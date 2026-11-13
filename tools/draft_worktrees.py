"""Private draft checkouts and immutable, clean-attempt-backed unit harvests.

This is queue transport, not match evidence. Confirmation and acceptance keep their existing gates.
"""
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

from source_digest import include_closure, tu_digest


def git(root, *args):
    proc = subprocess.run(['git', *args], cwd=root, capture_output=True)
    if proc.returncode:
        raise ValueError(proc.stderr.decode().strip())
    return proc.stdout


def read(path, default=None):
    return json.loads(path.read_text()) if path.is_file() else default


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)


def task_dir(root, unit):
    return Path(root) / unit['dir']


def label(tree, owner, task, kind, branch=None):
    save(Path(tree) / '.local/worktree-owner.json',
         {'owner': owner, 'task': task, 'kind': kind, 'branch': branch})


def link_private(root, tree):
    # Keep the worktree's own lifecycle metadata private to it; share kit inputs and task logs.
    local = Path(tree) / '.local'
    local.mkdir(exist_ok=True)
    names = {'tasks', 'queue', 'packs', 'sources', 'analysis', 'material',
             'briefs', 'reviews', 'flow', 'toolchains'}
    names.update(p.name for p in (Path(root) / '.local').iterdir()
                 if p.is_dir() and p.name not in {'worktrees', 'verifier'})
    for name in names:
        dest = local / name
        if not dest.exists() and not dest.is_symlink():
            dest.symlink_to((Path(root) / '.local' / name).resolve(), target_is_directory=True)
    # Diagnostics must resolve inside the checkout checked by verify_function. Host slots and
    # configuration remain shared, so changing the diagnostic location cannot bypass concurrency.
    verifier = local / 'verifier'
    if verifier.is_symlink():
        verifier.unlink()
    verifier.mkdir(exist_ok=True)
    shared = Path(root) / '.local/verifier'
    if shared.is_dir():
        for entry in shared.iterdir():
            dest = verifier / entry.name
            if entry.name != 'diagnostics' and not dest.exists() and not dest.is_symlink():
                dest.symlink_to(entry.resolve(), target_is_directory=entry.is_dir())


def current(root, unit):
    return read(task_dir(root, unit) / 'harvest.json')


def source_for(root, compiled, rva=None):
    """Latest harvested unit, if any. Legacy queues deliberately have no harvest metadata."""
    base = Path(root) / '.local/queue'
    import work_queue as wq
    for queue in sorted(base.glob('*/queue.tsv')):
        for unit in wq.read_queue(queue.parent):
            if compiled not in unit['sources']:
                continue
            h = current(root, unit)
            if h and (rva is None or int(rva) in h.get('compared', h['passing'])):
                return h
    return None


def copy_commit(root, commit, paths, tree):
    for rel in paths:
        dest = Path(tree) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(git(root, 'show', f'{commit}:{rel}'))


def carry_map_dependencies(root, tree, task):
    """Seed missing unit namespaces without changing maps already pinned by the base checkout."""
    from symbol_map import history_name
    paths = {task['symbols']} if task.get('symbols', '').startswith('reports/') else set()
    members = {int(str(fn['rva']), 0) for fn in task['functions']}
    for fn in read(tree / 'data/progress.json')['functions']:
        if fn['rva'] not in members or not fn.get('report'):
            continue
        record = read(tree / fn['report'], {})
        if record.get('source', {}).get('compiled') == task['compiled']:
            path = record.get('symbol_map', {}).get('path')
            if path:
                paths.add(path)
    for rel in sorted(paths):
        if not rel.startswith(f'reports/{task["build_id"]}/') or '..' in Path(rel).parts:
            raise ValueError(f'unit map is not a build-relative report dependency: {rel}')
        for name in (rel, history_name(rel)):
            dest, source = tree / name, root / name
            if dest.is_file():
                continue
            if not source.is_file():
                if name == rel:
                    raise ValueError(f'unit symbol-map dependency is missing: {rel}')
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)


def create(root, unit, tier, owner):
    root = Path(root).resolve()
    if not (root / '.git').exists():
        return None
    import work_queue as wq
    directory = task_dir(root, unit)
    directory.mkdir(parents=True, exist_ok=True)
    with wq.locked(directory / 'draft-lifecycle.lock'):
        return _create(root, unit, tier, owner)


def carry_legacy_passes(root, unit, tier, state):
    """Recover earlier in-place passes, merging around any work already done in this tier."""
    if tier == 'first' or state.get('carryover') or current(root, unit):
        return
    import work_queue as wq
    retained = set()
    for queue in (root / '.local/queue').glob('*/queue.tsv'):
        if any(u['dir'] == unit['dir'] for u in wq.read_queue(queue.parent)):
            retained.update(passing_before(queue.parent, unit, tier))
    data = json.loads(git(root, 'show', 'origin/main:data/progress.json'))
    integrated = {f['rva'] for f in data['functions'] if f['status'] == 'matched'}
    retained -= integrated
    if not retained:
        return
    tree = Path(state['tree'])
    merged = {}
    for rel in include_closure(root, read(task_dir(root, unit) / 'task.json')['compiled']):
        shared = (root / rel).read_bytes()
        dest = tree / rel
        try:
            base = git(root, 'show', f'{state["base"]}:{rel}')
        except ValueError:
            base = b''
        ours = dest.read_bytes() if dest.exists() else b''
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / name for name in ('ours', 'base', 'earlier')]
            for path, blob in zip(paths, (ours, base, shared)):
                path.write_bytes(blob)
            proc = subprocess.run(['git', 'merge-file', '-p', *map(str, paths)], capture_output=True)
        if proc.returncode:
            raise ValueError(f'earlier passing source conflicts in {rel}; preserve both tiers before retrying')
        merged[rel] = proc.stdout
    for rel, blob in merged.items():
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
    state['carryover'] = {'kind': 'legacy', 'passing': sorted(retained)}


def prepare_regressions(root, unit, tree):
    """Check integrated functions before spending a Drafter's attempt budget."""
    directory = task_dir(root, unit)
    task = read(directory / 'task.json')
    data = read(tree / 'data/progress.json')
    records = []
    members = {int(str(f['rva']), 0) for f in task['functions']}
    for fn in data['functions']:
        if fn['status'] != 'matched' or fn['rva'] not in members:
            continue
        rec = read(tree / fn['report'])
        if rec['source']['compiled'] != task['compiled']:
            continue
        records.append((fn, rec))
    if not records:
        return
    digest = hashlib.sha256((tree / task['recipe']).read_bytes()).hexdigest()
    selected = []
    for fn, rec in records:
        if rec['recipe']['sha256'] != digest:
            raise ValueError(f'unit preparation: accepted 0x{fn["rva"]:x} uses '
                             f'{rec["recipe"]["path"]}, not the task recipe {task["recipe"]}')
        selected.append(dict(rec['runs'][0]['report']['function']))
    probe = directory / 'preparation-checks' / uuid.uuid4().hex
    probe.mkdir(parents=True)
    for name in ('symbols.json', 'bind-hints.json', 'config.json'):
        if (directory / name).is_file():
            shutil.copyfile(directory / name, probe / name)
    if task.get('symbols', '').startswith('reports/'):
        shutil.copyfile(tree / task['symbols'], probe / 'symbols.json')
    save(probe / 'task.json', dict(task, functions=selected, max_attempts=None, symbols='symbols.json'))
    proc = subprocess.run([sys.executable, str(tree / 'tools/verifier/attempt'), str(probe)],
                          cwd=tree, capture_output=True, text=True)
    (probe / 'preparation.log').write_text(proc.stdout + proc.stderr)
    reports = [read(probe / f'attempts/001/0x{int(str(f["rva"]), 0):x}/report.json', {})
               for f in selected]
    if proc.returncode or any(r.get('result') != 'pass' for r in reports):
        raise ValueError(f'unit preparation: accepted regressions do not pass; see {probe / "preparation.log"}')
    save(directory / 'preparation.json', {'task': str(probe), 'recipe_sha256': digest,
                                        'passing': [int(str(f['rva']), 0) for f in selected]})


def install_prepared_skeleton(directory, tree, state):
    task = read(directory / 'task.json', {})
    if state.get('carryover') or read(directory / 'harvest.json') or task.get('export', {}).get(
            'unit_already_records') != [] or any(f.get('role') == 'regression' for f in task['functions']):
        return
    members = {int(str(fn['rva']), 0) for fn in task['functions']}
    for fn in read(tree / 'data/progress.json')['functions']:
        if fn['rva'] in members and fn['status'] == 'matched' and fn.get('report'):
            if read(tree / fn['report'], {}).get('source', {}).get('compiled') == task['compiled']:
                return
    sources = state['sources']
    cached = [directory / 'skeleton' / Path(rel).name for rel in sources]
    if all(p.is_file() for p in cached):
        blobs = {rel: p.read_bytes() for rel, p in zip(sources, cached)}
    else:
        from unit_skeleton import skeleton_files
        header, htext, cpp, ctext = skeleton_files(directory, repo=tree)
        blobs = {header: htext.encode(), cpp: ctext.encode()}
    if set(blobs) != set(sources):
        raise ValueError('prepared skeleton does not name exactly the claimed unit files')
    for rel, blob in blobs.items():
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
    state['prepared_skeleton'] = True


def _create(root, unit, tier, owner):
    root = Path(root).resolve()
    directory = task_dir(root, unit)
    # Scratch queues used by offline tools are not repository-backed queues.
    if not (root / '.git').exists():
        return None
    state_path = directory / f'draft-{tier}.json'
    old = read(state_path)
    if old and old.get('ready') and Path(old['tree']).is_dir():
        carry_map_dependencies(root, Path(old['tree']), read(directory / 'task.json'))
        carry_legacy_passes(root, unit, tier, old)
        # Resume a checkout initialized from a base stub only while it is still untouched.
        # Never replace a Drafter's edits when recovering an older setup state.
        if not old.get('prepared_skeleton') and old.get('base'):
            try:
                untouched = all((Path(old['tree']) / rel).read_bytes() == git(
                    root, 'show', f'{old["base"]}:{rel}') for rel in unit['sources'])
            except (OSError, ValueError):
                untouched = False
            if untouched:
                install_prepared_skeleton(directory, Path(old['tree']), old)
        link_private(root, Path(old['tree']))
        label(old['tree'], owner, unit['key'], 'draft', old['branch'])
        old['owner'] = owner
        save(state_path, old)
        return old
    tree = root / '.local/worktrees/draft' / f'{unit["key"]}-{tier}'
    branch = f'draft/{unit["key"]}-{tier}'
    if old and old.get('ready') and old.get('tree') == str(tree) and old.get('branch') == branch and not tree.exists():
        git(root, 'worktree', 'add', '--quiet', str(tree), branch)
        link_private(root, tree)
        label(tree, owner, unit['key'], 'draft', branch)
        old['owner'] = owner
        save(state_path, old)
        return old
    if old and not old.get('ready'):
        # A process may have stopped between worktree creation and completion of setup.
        if tree.exists():
            git(root, 'worktree', 'remove', '--force', str(tree))
        if git(root, 'branch', '--list', branch).strip():
            git(root, 'branch', '-D', branch)
        state_path.unlink(missing_ok=True)
    if tree.exists():
        raise ValueError(f'draft checkout already exists without state: {tree}')
    if git(root, 'branch', '--list', branch).strip():
        raise ValueError(f'draft branch already exists without state: {branch}')
    state = {'tree': str(tree), 'branch': branch, 'tier': tier, 'owner': owner,
             'base': git(root, 'rev-parse', 'origin/main').decode().strip(), 'sources': unit['sources'],
             'ready': False}
    inputs = {name: (directory / name).read_bytes() if (directory / name).exists() else None
              for name in ('task.json', 'symbols.json', 'bind-hints.json')}
    save(state_path, state)
    try:
        git(root, 'worktree', 'add', '--quiet', '-b', branch, str(tree), 'origin/main')
        link_private(root, tree)
        label(tree, owner, unit['key'], 'draft', branch)
        carry_map_dependencies(root, tree, read(directory / 'task.json'))
        prior = current(root, unit)
        if prior and not prior.get('integrated'):
            copy_commit(root, prior['commit'], prior['sources'], tree)
            frozen = read(Path(prior['task']) / 'task.json')
            task = read(directory / 'task.json')
            bound = {int(str(f['rva']), 0): f for f in frozen['functions']}
            task['functions'] = [dict(f, symbol=bound[int(str(f['rva']), 0)]['symbol'])
                                 if int(str(f['rva']), 0) in bound else f for f in task['functions']]
            shutil.copyfile(Path(prior['task']) / 'symbols.json', directory / 'symbols.json')
            task['symbols'] = 'symbols.json'
            save(directory / 'task.json', task)
        else:
            task = read(directory / 'task.json')
            if task and task.get('symbols', '').startswith('reports/'):
                shutil.copyfile(tree / task['symbols'], directory / 'symbols.json')
                task['symbols'] = 'symbols.json'
                save(directory / 'task.json', task)
        carry_legacy_passes(root, unit, tier, state)
        install_prepared_skeleton(directory, tree, state)
        if not (tree / unit['sources'][-1]).exists():
            from unit_skeleton import write_skeleton
            write_skeleton(directory, repo=tree)
        prepare_regressions(root, unit, tree)
        state['ready'] = True
        save(state_path, state)
        save(directory / 'draft-managed.json', {'unit': unit['key']})
    except Exception as exc:
        if tree.exists():
            git(root, 'worktree', 'remove', '--force', str(tree))
        if git(root, 'branch', '--list', branch).strip():
            git(root, 'branch', '-D', branch)
        for name, blob in inputs.items():
            if blob is None:
                (directory / name).unlink(missing_ok=True)
            else:
                (directory / name).write_bytes(blob)
        state_path.unlink(missing_ok=True)
        raise ValueError(f'draft setup failed and was rolled back: {exc}') from exc
    return state


def route_attempt(task, repo):
    """Refuse accidental attempts against the shared checkout for a new-style claim."""
    states = [read(p) for p in state_paths(task)]
    active = [s for s in states if s and Path(s['tree']).is_dir()]
    if (active or (Path(task) / 'draft-managed.json').exists()) and Path(repo).resolve() not in [
            Path(s['tree']).resolve() for s in active]:
        raise ValueError('run attempt in the claimed draft checkout: '
                         + (active[-1]['tree'] if active else 'no live checkout; claim the unit first'))


def harvest_for_confirmation(directory):
    directory = Path(directory)
    h = read(directory / 'harvest.json')
    if not h and ((directory / 'draft-managed.json').exists() or state_paths(directory)):
        raise ValueError('draft unit needs a clean harvested snapshot before confirmation')
    return h


def state_paths(directory):
    return [p for tier in ('first', 'fallback', 'strong')
            if (p := Path(directory) / f'draft-{tier}.json').is_file()]


def passing_before(qdir, unit, tier):
    import work_queue as wq
    return {int(r, 16) for r in unit['functions']} - {
        int(r, 16) for r in wq.unpassed(qdir, unit, tier)} if tier != 'first' else set()


def target_symbols(tree, directory, task, final, data):
    """Names bound to task or inventory function targets, rather than incidental helpers."""
    inventory = [f for f in data.get('functions', []) if f['build_id'] == task['build_id']]
    targets = {int(str(f['rva']), 0) for f in task['functions']} | {f['rva'] for f in inventory}
    symbols = {f['symbol'] for f in task['functions'] + final['functions']}
    for path in {directory / 'symbols.json',
                 (tree / task['symbols']) if task.get('symbols', '').startswith('reports/')
                 else directory / task.get('symbols', 'symbols.json')}:
        for name, entry in read(path, {}).get('symbols', {}).items():
            if 'rva' in entry and int(str(entry['rva']), 0) in targets:
                symbols.add(name)
    hints = read(directory / 'bind-hints.json', {})
    for name, value in hints.items():
        if not str(value).startswith('tls:') and int(str(value), 0) in targets:
            symbols.add(name)
    for fn in inventory:
        if not fn.get('report'):
            continue
        record = read(tree / fn['report'], {})
        for run in record.get('runs', []):
            symbol = run.get('report', {}).get('function', {}).get('symbol')
            if symbol:
                symbols.add(symbol)
    return symbols


def audit_source(tree, sources, allowed, targets, bind):
    """Catch known failed target bodies even when optimization omitted their symbols."""
    from check_origin import clean, functions
    names = bind.Names(bind.find_undname())
    symbols = sorted(targets | allowed)
    for start in range(0, len(symbols), 64):
        names.load(symbols[start:start + 64])

    def qualified(symbol):
        name = symbol if re.fullmatch(r'(?:[A-Za-z_]\w*::)*~?[A-Za-z_]\w*', symbol) else names(symbol)
        special = re.match(r'\?\?(0|1|_G|_E)([A-Za-z_]\w*)@@', symbol)
        if special:
            kind, cls = special.groups()
            name = f'{cls}::{cls if kind == "0" else "~" + cls}'
        return name
    # A source name shared with a passing overload does not establish another binding.
    # Emitted definitions are checked by their exact symbol, independently of this scan.
    failed_names = {qualified(s) for s in targets - allowed} - {qualified(s) for s in allowed} - {None}
    failed = set()
    for rel in sources:
        for fn in functions(clean((Path(tree) / rel).read_text())):
            name = (fn['class'] + '::' if fn['class'] else '') + fn['name']
            if name in failed_names:
                failed.add(name)
    if failed:
        raise ValueError('unit source contains target bodies without passing attempts; remove failed additions: '
                         + ', '.join(sorted(failed)))


def existing_header_emissions(tree, base, closure, symbols, task_targets, bind, explicit_only=False):
    """Untouched stand-ins can emit incidental functions, just as in an ordinary attempt."""
    from check_origin import brace_pairs, clean, functions
    existing_classes, existing_bodies, changed_bodies = set(), set(), set()

    def bodies(text):
        out = {}
        for fn in functions(text, with_heads=explicit_only):
            name = (fn['class'] + '::' if fn['class'] else '') + fn['name']
            signature = re.sub(r'\s+', ' ', fn['head']).strip() if explicit_only else json.dumps(fn['params'])
            out.setdefault(name, set()).add((signature, fn['body']))
        return out

    def classes(text):
        pairs = brace_pairs(text)
        declarations = set()
        for match in re.finditer(r'\b(?:class|struct)\s+([A-Za-z_]\w*)\b[^;{}]*\{', text):
            end = pairs.get(match.end() - 1)
            if end is None:
                continue
            definition = text[match.start():end + 1]
            # A nested enum declaration emits no destructor code. Keep enum-valued members:
            # only a closing brace followed directly by a semicolon is declaration-only.
            nested = brace_pairs(definition)
            enums = []
            for enum in re.finditer(r'\benum\s+(?:class\s+)?[A-Za-z_]\w*[^;{}]*\{', definition):
                close = nested.get(enum.end() - 1)
                if close is not None and re.match(r'\s*;', definition[close + 1:]):
                    tail = re.match(r'\s*;', definition[close + 1:]).end()
                    enums.append((enum.start(), close + 1 + tail))
            for start, stop in reversed(enums):
                definition = definition[:start] + definition[stop:]
            declarations.add((match.group(1), re.sub(r'\s+', ' ', definition)))
        return declarations

    def defaults(text):
        return {f'{owner}::{member}' for owner, member in re.findall(
            r'\b([A-Za-z_]\w*)::(~?[A-Za-z_]\w*)\s*\([^;{}]*\)[^;{}=]*=\s*default\s*;', text)}

    for rel in closure:
        blob = (tree / rel).read_bytes()
        try:
            before = git(tree, 'show', f'{base}:{rel}')
        except ValueError:
            before = b''
        text = clean(blob.decode())
        original = clean(before.decode())
        old_bodies = bodies(original)
        for name, definitions in bodies(text).items():
            if definitions <= old_bodies.get(name, set()):
                existing_bodies.add(name)
            else:
                changed_bodies.add(name)
        changed_bodies.update(defaults(text) - defaults(original))
        if Path(rel).suffix in ('.h', '.hpp'):
            existing_classes.update(name for name, definition in classes(text) & classes(original))
    names = bind.Names(bind.find_undname())
    names.load(sorted(symbols))
    exempt = set()
    for symbol in symbols - task_targets:
        name = names(symbol) or symbol
        special = re.match(r'\?\?(0|1|_G|_E)([A-Za-z_]\w*)@@', symbol)
        if special:
            kind, owner = special.groups()
            name = f'{owner}::{owner if kind == "0" else "~" + owner}'
        if name in changed_bodies:
            continue
        owner = name.rsplit('::', 1)[0] if '::' in name else None
        if name in existing_bodies or (not explicit_only and owner in existing_classes):
            exempt.add(symbol)
    return exempt


def accepted_baseline_emissions(tree, base, closure, symbols, final, bind):
    """Keep unchanged definitions supporting an integrated, freshly passing regression.

    This does not pass those definitions as targets. The accepted record must bind the exact
    baseline unit, and only explicit bodies unchanged from that baseline can be incidental.
    """
    if not symbols:
        return set()
    from review_packet import digest_at
    data = json.loads(git(tree, 'show', f'{base}:data/progress.json'))
    compared = {int(str(fn['rva']), 0) for fn in final['functions']}
    for fn in data.get('functions', []):
        if (fn.get('status') != 'matched' or fn['build_id'] != final['build_id']
                or fn['rva'] not in compared or not fn.get('report')):
            continue
        record = json.loads(git(tree, 'show', f'{base}:{fn["report"]}'))
        source = record.get('source', {})
        files = source.get('translation_unit', [])
        if (source.get('compiled') == final['compiled'] and files
                and digest_at(tree, base, files) == source.get('digest')):
            return existing_header_emissions(tree, base, closure, symbols, set(), bind,
                                             explicit_only=True)
    return set()


def harvest(qdir, unit, claim, records):
    """Snapshot only after a fresh all-pass compile and comparison of the retained unit.

    The full task is preserved for later tiers. The clean task selects passing additions and all
    existing regressions; a target-binding audit refuses leftover untested candidates.
    """
    import work_queue as wq
    root = wq.queue_repo(qdir)
    directory = task_dir(root, unit)
    tier = claim.get('tier', 'first')
    state = claim['draft']
    tree = Path(state['tree'])
    passing = passing_before(qdir, unit, tier) | {
        int(r['rva'], 16) for r in records if r.get('result') == 'pass' and 'rva' in r}
    if not passing:
        return None
    original = read(directory / 'task.json')
    raw = dict(original)
    queued = {int(r, 16) for r in unit['functions']}
    selected = [f for f in raw['functions'] if int(str(f['rva']), 0) in passing
                or int(str(f['rva']), 0) not in queued]
    data = read(tree / 'data/progress.json', {})
    if not passing <= {int(str(f['rva']), 0) for f in selected}:
        raise ValueError('passing function missing from task.json')
    clean = directory / 'harvest-checks' / uuid.uuid4().hex
    clean.mkdir(parents=True)
    for name in ('symbols.json', 'bind-hints.json', 'config.json'):
        if (directory / name).is_file():
            shutil.copyfile(directory / name, clean / name)
    if raw.get('symbols', '').startswith('reports/'):
        shutil.copyfile(tree / raw['symbols'], clean / 'symbols.json')
    raw.update(functions=selected, max_attempts=None, symbols='symbols.json')
    save(clean / 'task.json', raw)
    # All comparisons run afresh in an empty attempt directory, outside the tier retry budget.
    command = [sys.executable, str(tree / 'tools/verifier/attempt'), str(clean)]
    proc = subprocess.run(command, cwd=tree, capture_output=True, text=True)
    (clean / 'harvest.log').write_text(proc.stdout + proc.stderr)
    if proc.returncode:
        raise ValueError(f'clean harvest attempt failed; no harvest: {clean / "harvest.log"}')
    final = read(clean / 'task.json')
    dest = clean / 'attempts/001'
    closure = include_closure(tree, raw['compiled'])
    digest = tu_digest(tree, closure)
    result = read(dest / 'result.json', {})
    if result.get('source_revision') != digest:
        raise ValueError('clean attempt does not bind current unit; no harvest')
    for fn in final['functions']:
        report = read(dest / f'0x{int(str(fn["rva"]), 0):x}/report.json', {})
        if report.get('result') != 'pass':
            raise ValueError('clean attempt missing a passing comparison; no harvest')
    sys.path.insert(0, str(Path(__file__).parent / 'verifier'))
    import bind
    from pecoff import CoffObject
    defined = set(bind.defined_functions(CoffObject((dest / 'candidate.obj').read_bytes())))
    allowed = {f['symbol'] for f in final['functions']}
    # Membership comes from the prepared task, including its explicit regressions. Other
    # producers may publish a stub with the same compiled path; integration still validates
    # every accepted record against the complete source closure before anything can land.
    targets = target_symbols(tree, directory, original, final, data)
    # The clean binder may have learned additional target bindings during this attempt.
    targets.update(target_symbols(tree, clean, final, final, data))
    names = bind.Names(bind.find_undname())
    names.load(sorted(defined))
    targets.update(symbol for symbol in defined if names(symbol) in targets)
    extra = (defined & targets) - allowed
    task_targets = target_symbols(tree, directory, original, final, {'functions': []})
    extra -= existing_header_emissions(tree, state['base'], closure, extra, task_targets, bind)
    candidates = {f['symbol'] for f in original['functions'] + final['functions']}
    baseline = accepted_baseline_emissions(tree, state['base'], closure,
                                           extra | (candidates - allowed), final, bind)
    extra -= baseline
    if extra:
        raise ValueError('unit still defines target functions without passing attempts; remove failed additions: '
                         + ', '.join(sorted(extra)))
    # Only the task names identify source candidates; unrelated inventory overloads do not
    # establish a source binding by name alone. Emitted inventory bindings were checked above.
    audit_source(tree, unit['sources'], allowed | baseline, candidates, bind)
    import lint_reconstruction
    findings = lint_reconstruction.lint_tree(tree, closure)
    if findings:
        raise ValueError('harvest lint failed; no harvest: ' + '; '.join(findings))
    changed = git(tree, 'diff', '--name-only', 'HEAD').decode().splitlines()
    if set(changed) - set(unit['sources']):
        raise ValueError('draft changed files outside its unit; no harvest')
    git(tree, 'add', '--', *unit['sources'])
    staged = git(tree, 'diff', '--cached', '--name-only').decode().splitlines()
    if set(staged) - set(unit['sources']):
        raise ValueError('draft index contains files outside its unit; no harvest')
    git(tree, 'commit', '--quiet', '--allow-empty', '-m', f'Harvest draft {unit["key"]} ({tier})')
    commit = git(tree, 'rev-parse', 'HEAD').decode().strip()
    from review_packet import digest_at
    if digest_at(root, commit, closure) != digest:
        raise ValueError('harvest commit differs from clean attempt; no harvest')
    # Harvest refs outlive their draft branches, including final-tier exhaustion.
    git(root, 'update-ref', f'refs/harvests/{unit["key"]}/{tier}', commit)
    h = {'commit': commit, 'branch': state['branch'], 'tree': str(tree), 'tier': tier,
         'sources': closure, 'unit_sources': unit['sources'], 'compiled': raw['compiled'],
         'digest': digest, 'passing': sorted(passing), 'task': str(clean), 'build_id': raw['build_id'],
         'compared': [int(str(f['rva']), 0) for f in final['functions']],
         'attempt': str(dest), 'queue': str(Path(qdir).resolve()), 'unit': unit['dir']}
    if baseline:
        h.update(baseline_commit=state['base'], baseline_definitions=sorted(baseline))
    save(directory / f'harvest-{tier}.json', h)
    save(directory / 'harvest.json', h)
    return h


def remove_clean_checkout(root, unit, state):
    """Remove a labelled, clean checkout without changing its branch or harvest refs."""
    tree = Path(state['tree'])
    if not tree.exists():
        return
    try:
        expected = Path(root).resolve() / '.local/worktrees/draft' / f"{unit['key']}-{state['tier']}"
        owner = read(tree / '.local/worktree-owner.json', {})
        if tree != expected or owner.get('task') != unit['key'] or owner.get('kind') != 'draft':
            print(f'leaving draft checkout {tree}: owner unavailable')
            return
        status = git(tree, 'status', '--porcelain=v1', '--untracked-files=all')
        if status:
            print(f'leaving dirty draft checkout {tree}')
            return
        git(root, 'worktree', 'remove', str(tree))
    except (OSError, ValueError, KeyError, AttributeError) as exc:
        print(f'leaving draft checkout {tree}: {exc}')


def cleanup(root, unit):
    """Remove only this unit's labelled draft worktrees and branches; retain task diagnostics."""
    for path in state_paths(task_dir(root, unit)):
        state = read(path)
        tree = Path(state['tree'])
        if tree.exists():
            owner = read(tree / '.local/worktree-owner.json', {})
            if owner.get('task') != unit['key'] or owner.get('kind') != 'draft':
                raise ValueError(f'unlabelled draft checkout: {tree}')
            git(root, 'worktree', 'remove', '--force', str(tree))
        git(root, 'branch', '-D', state['branch'])
        path.unlink()


def cleanup_integrated(root):
    import work_queue as wq
    origin = json.loads(git(root, 'show', 'origin/main:data/progress.json'))
    matched = {(f['build_id'], f['rva']) for f in origin['functions'] if f.get('status') == 'matched'}
    for queue in (Path(root) / '.local/queue').glob('*/queue.tsv'):
        for unit in wq.read_queue(queue.parent):
            directory = task_dir(root, unit)
            if not (directory / 'harvest.json').is_file():
                continue
            with wq.locked(directory / 'draft-lifecycle.lock'):
                h = current(root, unit)
                if h and {(h['build_id'], r) for r in h['passing']} <= matched:
                    # An earlier tier may integrate while a later tier is drafting this unit.
                    # Claim setup takes this lock too, closing the check/remove race.
                    if any((wq.tier_dir(queue.parent, 'claims', tier) / f'{unit["key"]}.lock').exists()
                           for tier in ('first', 'fallback', 'strong')):
                        continue
                    from review_packet import digest_at
                    if digest_at(root, 'origin/main', h['sources']) == h['digest']:
                        cleanup(root, unit)
                        h['integrated'] = True
                        save(directory / 'harvest.json', h)


def confirm_one(root, directory, args):
    """Confirm from a detached harvest commit, publish only resulting records and unit maps."""
    h = harvest_for_confirmation(directory)
    if not h:
        return None
    from review_packet import digest_at
    if digest_at(root, h['commit'], h['sources']) != h['digest']:
        raise ValueError('harvest commit does not bind recorded digest')
    tree = Path(root) / '.local/worktrees/confirm' / uuid.uuid4().hex
    git(root, 'worktree', 'add', '--quiet', '--detach', str(tree), h['commit'])
    try:
        link_private(root, tree)
        label(tree, 'confirm', Path(directory).name, 'confirm')
        # Enrollment can land after the source harvest. Carry only the selected identities;
        # their source still comes exclusively from the immutable harvest commit.
        task = read(Path(h['task']) / 'task.json')
        data = read(tree / 'data/progress.json')
        known = {f['id']: f for f in data['functions']}
        enrolled = {f['id']: f for f in read(Path(root) / 'data/progress.json')['functions']}
        for fn in task['functions']:
            ident = f'{task["build_id"]}-0x{int(str(fn["rva"]), 0):x}'
            row = enrolled.get(ident)
            if row is None or row['size'] != fn['size']:
                raise ValueError(f'{ident} must be enrolled before confirmation')
            if ident not in known:
                data['functions'].append(row)
                evidence = row.get('evidence')
                if evidence and (Path(root) / evidence).is_file():
                    dest = tree / evidence
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(Path(root) / evidence, dest)
        save(tree / 'data/progress.json', data)
        binding_list = tree / '.local/harvest-bind.txt'
        binding_list.write_text(h['task'] + '\n')
        command = [sys.executable, str(tree / 'tools/verifier/bind.py'), '--list', str(binding_list), '--unit-maps']
        proc = subprocess.run(command, cwd=tree)
        if proc.returncode:
            return proc.returncode
        command = [sys.executable, str(tree / 'tools/verifier/confirm'), h['task'], *args]
        task = read(Path(h['task']) / 'task.json')
        paths = [f'reports/{task["build_id"]}/0x{int(str(fn["rva"]), 0):x}.json'
                 for fn in task['functions']]
        before = {rel: (tree / rel).stat().st_mtime_ns if (tree / rel).exists() else None for rel in paths}
        proc = subprocess.run(command, cwd=tree)
        # As in the in-place path, validated records survive a later whole-tree check refusal
        # (for example a regression whose acceptance now needs re-review). Preserve the exit code.
        if '--out' not in args:
            for rel in paths:
                if not (tree / rel).exists() or (tree / rel).stat().st_mtime_ns == before[rel]:
                    continue
                record = read(tree / rel)
                if record['source']['digest'] != h['digest']:
                    raise ValueError('confirmation record differs from harvest')
                dependencies = [rel, record['symbol_map']['path']]
                from symbol_map import history_name
                dependencies += [history_name(record['symbol_map']['path'])]
                for name in dependencies:
                    if (tree / name).is_file():
                        dest = Path(root) / name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(tree / name, dest)
        return proc.returncode
    finally:
        git(root, 'worktree', 'remove', '--force', str(tree))
