"""Private draft checkouts and immutable, clean-attempt-backed unit harvests.

This is queue transport, not match evidence. Confirmation and acceptance keep their existing gates.
"""
import json
from collections import Counter
from pathlib import Path
import re
import shutil
import subprocess
import sys
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
    names = {'tasks', 'queue', 'verifier', 'packs', 'sources', 'analysis', 'material',
             'briefs', 'reviews', 'flow', 'toolchains'}
    names.update(p.name for p in (Path(root) / '.local').iterdir()
                 if p.is_dir() and p.name != 'worktrees')
    for name in names:
        dest = local / name
        if not dest.exists() and not dest.is_symlink():
            dest.symlink_to((Path(root) / '.local' / name).resolve(), target_is_directory=True)


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


def create(root, unit, tier, owner):
    root = Path(root).resolve()
    if not (root / '.git').exists():
        return None
    import work_queue as wq
    directory = task_dir(root, unit)
    directory.mkdir(parents=True, exist_ok=True)
    with wq.locked(directory / 'draft-lifecycle.lock'):
        return _create(root, unit, tier, owner)


def _create(root, unit, tier, owner):
    root = Path(root).resolve()
    directory = task_dir(root, unit)
    # Scratch queues used by offline tools are not repository-backed queues.
    if not (root / '.git').exists():
        return None
    state_path = directory / f'draft-{tier}.json'
    old = read(state_path)
    if old and old.get('ready') and Path(old['tree']).is_dir():
        link_private(root, Path(old['tree']))
        label(old['tree'], owner, unit['key'], 'draft', old['branch'])
        old['owner'] = owner
        save(state_path, old)
        return old
    tree = root / '.local/worktrees/draft' / f'{unit["key"]}-{tier}'
    branch = f'draft/{unit["key"]}-{tier}'
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
        # Never seed a new checkout from tracked source in the shared working tree.
        if not (tree / unit['sources'][-1]).exists():
            from unit_skeleton import write_skeleton
            write_skeleton(directory, repo=tree)
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


def audit_source(tree, sources, allowed, bind):
    """Also catch removed-from-task bodies that optimization left out of the object."""
    from check_origin import clean, functions
    names = bind.Names(bind.find_undname())
    counts = Counter()
    for symbol in allowed:
        name = names(symbol)
        special = re.match(r'\?\?(0|1|_G|_E)([A-Za-z_]\w*)@@', symbol)
        if special:
            kind, cls = special.groups()
            name = f'{cls}::{cls if kind == "0" else "~" + cls}'
        if name:
            counts[name] += 1
    bodies = Counter()
    for rel in sources:
        for fn in functions(clean((Path(tree) / rel).read_text())):
            name = (fn['class'] + '::' if fn['class'] else '') + fn['name']
            bodies[name] += 1
    if bodies - counts:
        raise ValueError('unit source contains bodies without passing attempts; remove failed additions: '
                         + ', '.join(sorted(bodies - counts)))


def harvest(qdir, unit, claim, records):
    """Snapshot only after a fresh all-pass compile and comparison of the retained unit.

    The full task is preserved for later tiers. The clean task selects passing additions and all
    existing regressions; an object-definition audit refuses leftover untested additions.
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
    raw = read(directory / 'task.json')
    queued = {int(r, 16) for r in unit['functions']}
    selected = [f for f in raw['functions'] if int(str(f['rva']), 0) in passing
                or int(str(f['rva']), 0) not in queued]
    data = read(tree / 'data/progress.json', {})
    for fn in data.get('functions', []):
        if fn.get('status') != 'matched':
            continue
        rec = read(tree / fn.get('report', 'missing'), {})
        if rec.get('source', {}).get('compiled') == raw['compiled'] and fn['rva'] not in {
                int(str(f['rva']), 0) for f in selected}:
            selected.append(dict(rec['runs'][0]['report']['function']))
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
    # Every pre-existing integrated function remains a regression, even if an old task omitted it.
    for fn in data.get('functions', []):
        if fn.get('status') != 'matched':
            continue
        rec = read(tree / fn.get('report', 'missing'), {})
        if fn.get('status') == 'matched' and rec.get('source', {}).get('compiled') == raw['compiled']:
            if fn['rva'] not in {int(str(f['rva']), 0) for f in final['functions']}:
                raise ValueError('integrated regression absent from clean task; no harvest')
    extra = defined - allowed
    if extra:
        raise ValueError('unit still defines functions without passing attempts; remove failed additions: '
                         + ', '.join(sorted(extra)))
    audit_source(tree, unit['sources'], allowed, bind)
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
    save(directory / f'harvest-{tier}.json', h)
    save(directory / 'harvest.json', h)
    return h


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
