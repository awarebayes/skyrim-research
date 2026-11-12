"""Conservative primitives for script-produced reconstruction candidates.

The generate and attempt commands use a private JSON config with paths named main,
worktree, census, families, functions, progress, image and runners. Output and the
separate checkout must be inside the main checkout private directory. Local passes
are preliminary evidence only; they do not confer match status.
"""
import re
import json
import hashlib
import inspect
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_digest import include_closure, tu_digest


IDENT = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z')
GENERATOR_VERSION = '2'
BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/generator-leaves-selection.md'


class UnsafeCandidate(ValueError):
    """The candidate cannot be emitted safely by this generator."""


def task_digest(worktree, task_dir):
    task = json.loads((Path(task_dir) / 'task.json').read_text())
    paths = include_closure(worktree, task['compiled'])
    return tu_digest(worktree, paths)


def input_digest(worktree, task_dir):
    """Bind the task identity, symbol map, recipe, image pin and toolchain pin for resume."""
    root, directory = Path(worktree), Path(task_dir)
    task = json.loads((directory / 'task.json').read_text())
    symbols = Path(task['symbols'])
    symbols = root / symbols if task['symbols'].startswith('reports/') else directory / symbols
    blobs = [(directory / 'task.json').read_bytes(), symbols.read_bytes()]
    blobs += [(root / path).read_bytes() for path in
              (task['recipe'], 'builds/target.json', 'tools/verifier/pinned.sha256')]
    return hashlib.sha256(b''.join(len(b).to_bytes(8, 'big') + b for b in blobs)).hexdigest()


def check_resume(records, worktree):
    for record in records:
        if not record.get('source_digest') or record['source_digest'] != task_digest(worktree, record['task']):
            raise ValueError('resume record missing source digest or source changed; use a new output directory')
        if record.get('input_digest') and record['input_digest'] != input_digest(worktree, record['task']):
            raise ValueError('resume inputs changed; use a new output directory')


def validate_identity(owner, method, *, existing_classes, names, name_rva, rva):
    """Reject identities whose class or function conflicts with existing inputs.

    ``names`` maps a qualified public name to all RVAs carrying that name.  The
    caller must populate it from the whole inventory, not just selected candidates.
    """
    if '<' in owner or '>' in owner or '__' in owner:
        raise UnsafeCandidate('template-owned')
    parts = owner.split('::')
    if not all(IDENT.fullmatch(part) for part in parts) or not IDENT.fullmatch(method):
        raise UnsafeCandidate('unsupported-name')
    if owner in existing_classes or parts[-1] in existing_classes:
        raise UnsafeCandidate('existing-unit')
    qualified = f'{owner}::{method}'
    if name_rva != rva or set(names.get(qualified, ())) != {rva}:
        raise UnsafeCandidate('name-clash')
    return qualified


def validate_bindings(reference_fields, bindings):
    """Require one exact target binding per reference field, with no extras.

    Values are RVAs from the member's own independently decoded reference map.
    The comparator remains responsible for verifying the compiled reference.
    """
    if set(reference_fields) != set(bindings):
        raise UnsafeCandidate('reference-fields')
    if any(bindings[field] != target for field, target in reference_fields.items()):
        raise UnsafeCandidate('wrong-target')


def emit_leaf(owner, method, *, family, width, value, virtual, name_label):
    """Return a self-contained header/source pair for a narrow leaf candidate.

    ``value`` is the immediate for a constant, or the member byte offset for a
    member and member-address.  This emitter deliberately does not decode an
    executable or decide whether an identity is safe.
    """
    if family not in ('constant', 'member', 'member-address'):
        raise UnsafeCandidate('unsupported-family')
    if width not in (1, 4, 8) or (family == 'constant' and width == 8):
        raise UnsafeCandidate('unsupported-width')
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise UnsafeCandidate('invalid-parameter')
    if family == 'constant' and value >= 1 << (width * 8):
        raise UnsafeCandidate('invalid-parameter')
    parts = owner.split('::')
    if not all(IDENT.fullmatch(p) for p in parts) or not IDENT.fullmatch(method):
        raise UnsafeCandidate('unsupported-name')
    if name_label != 'GUESS(low)' and not re.fullmatch(r'COMMUNITY\([^()\r\n]+\)', name_label):
        raise UnsafeCandidate('name-origin')
    if family != 'constant' and value < (8 if virtual else 0):
        raise UnsafeCandidate('invalid-offset')
    types = {1: 'std::uint8_t', 4: 'std::uint32_t', 8: 'void*'}
    member_type = types[width]
    result_type = member_type + ' const*' if family == 'member-address' else member_type
    pad = value - (8 if virtual else 0)
    if family != 'constant' and (value % width or pad > 0x100000):
        raise UnsafeCandidate('invalid-offset')
    label = f'// {method}: {name_label}'
    if name_label == 'GUESS(low)':
        label += '; method name inferred from vtable owner and slot'
    h = ['#pragma once', '#include <cstdint>', label]
    for ns in parts[:-1]:
        h.append(f'namespace {ns} {{')
    h.extend([f'class {parts[-1]}', '{', 'public:',
              f'    {"virtual " if virtual else ""}{result_type} {method}() const;'])
    if family != 'constant':
        if pad:
            h.append(f'    std::uint8_t padding[0x{pad:x}];')
        h.append(f'    {member_type} member;')
    h.append('};')
    h.extend('}' for _ in parts[:-1])
    expression = (f'0x{value:x}' if family == 'constant' else
                  ('&member' if family == 'member-address' else 'member'))
    cpp = [f'#include "{parts[-1]}.h"', label, f'{result_type} {owner}::{method}() const', '{',
           f'    return {expression};', '}']
    return '\n'.join(h) + '\n', '\n'.join(cpp) + '\n'


def publication_header(owner, method, *, rva, size, origin, name_label, class_label, notice=''):
    """Common leading comment for both files; no licence grant for reconstruction."""
    lines = [f'// {owner}::{method}, build {BUILD}, RVA 0x{rva:x}, {size} bytes.',
             '// Labels: v2', '// Source exposure: mixed (local binary analysis and public names).',
             f'// Evidence: {EVIDENCE}', f'// Recipe: {RECIPE}',
             '// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).',
             '// Origin: ' + json.dumps(origin, sort_keys=True, separators=(',', ':')),
             '// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.',
             '// Adapted bodies: none. Body synthesized from the bounded leaf template.',
             '// A comparator pass verifies code under the recipe, not names or original source form.',
             '// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.',
             f'// {owner}: {class_label}', f'// {method}: {name_label}',
             '// member, padding: GUESS(low); storage names invented for the measured member offset']
    if name_label == 'GUESS(low)':
        lines += ['// Method name is a guess built from the vtable owner and slot, not a public symbol.']
    if notice:
        lines += ['// Public naming source notice:'] + ['// ' + s if s else '//' for s in notice.splitlines()]
    return '\n'.join(lines) + '\n'


def template_digest(family):
    text = '\n'.join((GENERATOR_VERSION, family, inspect.getsource(emit_leaf),
                      inspect.getsource(publication_header)))
    return hashlib.sha256(text.encode()).hexdigest()


def resolve_area(owner, classes, unit_areas):
    """Use an evidenced unit or the nearest primary base under the documented area rule."""
    from ghidra.export_pack import area_for
    if unit_areas.get(owner):
        return unit_areas[owner], 'owner-unit', owner
    if area_for(owner):
        return area_for(owner), 'prefix', owner
    seen = {owner}
    parent = classes.get(owner, {}).get('parent')
    while parent and parent not in seen:
        seen.add(parent)
        if unit_areas.get(parent):
            return unit_areas[parent], 'base-unit', parent
        if area_for(parent):
            return area_for(parent), 'base-prefix', parent
        parent = classes.get(parent, {}).get('parent')
    return None, 'no-area-rule', None


def write_new(path, content):
    """Repeat identical generation safely, refusing a different existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text() != content:
            raise ValueError('generated source already exists with different contents')
    else:
        with path.open('x') as f:
            f.write(content)


def decode_leaf(data):
    """Decode only the leaf forms selected by the census shape."""
    import struct
    if len(data) >= 6 and data[0] == 0xb8 and data[5] == 0xc3:
        return 'constant', 4, struct.unpack_from('<I', data, 1)[0]
    if len(data) >= 3 and data[0] == 0xb0 and data[2] == 0xc3:
        return 'constant', 1, data[1]
    for prefix, width, disp in ((b'\x48\x8b\x41', 8, 1), (b'\x8b\x41', 4, 1),
                                (b'\x0f\xb6\x41', 1, 1), (b'\x48\x8b\x81', 8, 4),
                                (b'\x8b\x81', 4, 4)):
        end = len(prefix) + disp
        if len(data) > end and data.startswith(prefix) and data[end] == 0xc3:
            return 'member', width, int.from_bytes(data[len(prefix):end], 'little', signed=True)
    return None


def generate(args):
    import collections
    import csv
    import json
    import struct
    from pathlib import Path
    cfg = json.loads(Path(args.config).read_text())
    out = Path(args.out).resolve()
    wt = Path(cfg['worktree']).resolve()
    private = (Path(cfg['main']) / '.local').resolve()
    if not out.is_relative_to(private) or not wt.is_relative_to(private):
        raise ValueError('output and worktree must be inside the main checkout private directory')
    if not (wt / '.local').is_dir() or not (wt / 'tools/verifier/attempt').is_file():
        raise ValueError('private worktree with linked .local required')
    ranks = [11, 22] if args.family == 'const-return' else [18, 56]
    families = json.loads(Path(cfg['families']).read_text())
    shapes = {f['shape'] for f in families if f['rank'] in ranks}
    solved = {int(str(f['rva']), 0) for f in json.loads(Path(cfg['progress']).read_text())['functions'] if f.get('status') == 'matched'}
    data = Path(cfg['image']).read_bytes()
    target = json.loads((wt / 'builds/target.json').read_text())
    if target.get('build_id') != BUILD or hashlib.sha256(data).hexdigest() != target.get('image_sha256'):
        raise ValueError('generator image differs from pinned target')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    sections = []
    for i in range(struct.unpack_from('<H', data, pe + 6)[0]):
        off = pe + 24 + struct.unpack_from('<H', data, pe + 20)[0] + 40 * i
        vs, va, rs, ro = struct.unpack_from('<IIII', data, off + 8)
        sections.append((va, min(vs, rs), ro))
    inventory = {}
    names = collections.defaultdict(set)
    for line in Path(cfg['functions']).read_text().splitlines():
        d = json.loads(line); inventory[d['rva']] = d
        for n in d['names']:
            names[n['name']].add(d['rva'])
    existing = {p.stem for p in (wt / 'reconstruction').rglob('*.h')}
    # Include the shared checkout's active work without modifying it.
    existing |= {p.stem for p in (Path(cfg['main']) / 'reconstruction').rglob('*.h')}
    classes = {c['class']: c for c in map(json.loads, Path(cfg.get('classes',
               str(Path(cfg['main']) / '.local/analysis/classes.jsonl'))).read_text().splitlines())}
    unit_areas = {}
    for root in (wt, Path(cfg['main'])):
        for path in (root / 'reconstruction').glob('*/*.h'):
            area = path.parent.name
            if path.stem in unit_areas and unit_areas[path.stem] != area:
                raise ValueError('class has conflicting existing unit areas')
            unit_areas[path.stem] = area
    out.mkdir(parents=True, exist_ok=True)
    for pin in (RECIPE, 'builds/target.json', 'tools/verifier/pinned.sha256'):
        write_new(out / pin, (wt / pin).read_text())
    index = out / (args.family + '.jsonl')
    prior = [json.loads(x) for x in index.read_text().splitlines()] if args.resume and index.exists() else []
    check_resume(prior, wt)
    for entry in prior:
        if entry['source_digest'] != task_digest(out, entry['task']):
            raise ValueError('staged source changed; use a new output directory')
    if index.exists() and not args.resume:
        raise ValueError('index exists; use --resume or a new output directory')
    selected = {x['rva'] for x in prior}
    seen = {x['owner'] for x in prior}
    for other in out.glob('*-return.jsonl'):
        if other != index:
            seen.update(json.loads(line)['owner'] for line in other.read_text().splitlines())
    counts = collections.Counter()
    areas = collections.Counter()
    rows = csv.DictReader(Path(cfg['census']).read_text().splitlines(), delimiter='\t')
    emitted = 0
    for row in rows:
        if row['shape'] not in shapes or not row['tier']:
            continue
        r = int(row['rva'], 16)
        if r in solved or r in selected:
            continue
        d = inventory.get(r)
        if not d:
            counts['undecodable'] += 1; continue
        owner_info = d.get('owner') or {}
        owner = owner_info.get('class', '')
        if '<' in owner or '>' in owner:
            counts['template-owned'] += 1; continue
        name = next((n for n in d['names'] if n.get('how') != 'placeholder' and
                     re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*::[A-Za-z_][A-Za-z_0-9]*', n['name'])
                     and n.get('source') in ('meh321', 'ng-id', 'ng-slot')), None)
        if name:
            cls, method = name['name'].split('::')
            if names[name['name']] != {r}:
                counts['name-clash'] += 1; continue
            label = ('COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)' if name['source'] == 'meh321'
                     else 'COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)')
        elif IDENT.fullmatch(owner) and isinstance(owner_info.get('slot'), int):
            cls, method, label = owner, 'Slot' + str(owner_info['slot']), 'GUESS(low)'
        else:
            counts['undecodable'] += 1; continue
        if not re.fullmatch(r'[A-Z][A-Za-z0-9_]*', cls):
            counts['unsupported-class-layout'] += 1; continue
        if cls in existing or cls in seen:
            counts['existing-unit'] += 1; continue
        area, area_how, area_owner = resolve_area(cls, classes, unit_areas)
        if not area:
            counts['no-area-rule'] += 1; continue
        code = next((data[ro + r - va:ro + r - va + 16] for va, size, ro in sections if va <= r < va + size), b'')
        decoded = decode_leaf(code)
        if not decoded or decoded[0] != ('constant' if args.family == 'const-return' else 'member'):
            counts['undecodable'] += 1; continue
        kind, width, value = decoded
        try:
            h, cpp = emit_leaf(cls, method, family=kind, width=width, value=value,
                               virtual=bool(owner_info), name_label=label)
        except UnsafeCandidate:
            counts['undecodable'] += 1; continue
        unit = f'stamp-{r:x}'
        name_source = (dict(kind='public', source=name['source'],
                           repository=('meh321/AddressLibraryDatabase' if name['source'] == 'meh321'
                                       else 'CharmedBaryon/CommonLibSSE-NG'),
                           revision=('0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91' if name['source'] == 'meh321'
                                     else 'b93280e832f263dbef44e44cbe2936622a02f91a'),
                           confidence='medium')
                       if name else dict(kind='guess', confidence='low',
                                         owner=owner, slot=owner_info['slot'],
                                         rationale='vtable owner and slot; method spelling invented'))
        origin = dict(generator_family=args.family, generator_version=GENERATOR_VERSION,
                      template_digest=template_digest(args.family), name_source=name_source)
        notice = ''
        if 'CommonLibSSE-NG@' in label:
            import subprocess
            from unit_skeleton import COMMUNITY_SOURCES
            clone, revision, _ = COMMUNITY_SOURCES['CharmedBaryon/CommonLibSSE-NG']
            notice = subprocess.check_output(['git', '-C', str(Path(cfg['main']) / clone),
                                             'show', f'{revision}:LICENSE'], text=True)
        prefix = publication_header(cls, method, rva=r, size=int(row['size']), origin=origin,
                                    name_label=label,
                                    class_label='EXE_RTTI' if cls == owner else label, notice=notice)
        compiled = f'reconstruction/{area}/{cls}.cpp'
        for root in (out, wt):
            write_new(root / compiled, prefix + cpp)
            write_new((root / compiled).with_suffix('.h'), prefix + h)
        task_dir = out / 'tasks' / unit
        task_dir.mkdir(parents=True, exist_ok=True)
        mangling = {1: "E", 4: "I", 8: "PEAX"}[width]
        symbol = f'?{method}@{cls}@@{"U" if owner_info else "Q"}EBA{mangling}XZ'
        fn = dict(rva=hex(r), size=int(row['size']), symbol=symbol,
                  function_id=f'sse-steam-1-7-104-{hex(r)}', community_name=f'{cls}::{method}',
                  name_origin='GUESS' if label == 'GUESS(low)' else 'COMMUNITY', verdict='generated', pack=None)
        task = dict(task_id=unit.lower().replace('_', '-'), build_id='sse-steam-1-7-104',
                    compiled=compiled,
                    recipe=RECIPE, symbols='symbols.json',
                    functions=[fn], max_attempts=2,
                    export=dict(generator='tools/stamp.py', task_schema=1, unit_already_records=[]))
        (task_dir / 'task.json').write_text(json.dumps(task, indent=2))
        (task_dir / 'symbols.json').write_text(json.dumps(dict(schema=1, build_id=task['build_id'],
                                                     symbols={symbol: dict(rva=r, size=fn['size'])}), indent=2))
        with index.open('a') as f:
            f.write(json.dumps(dict(rva=r, size=fn['size'], build_id=BUILD, name=fn['community_name'],
                                    owner=cls, task=str(task_dir), family=args.family, compiled=compiled,
                                    name_source=name_source, origin=origin,
                                    area=dict(area=area, how=area_how, owner=area_owner),
                                    parameters=dict(family=kind, width=width, value=value, virtual=bool(owner_info)),
                                    input_digest=input_digest(wt, task_dir),
                                    source_digest=task_digest(wt, task_dir))) + '\n')
        seen.add(cls); emitted += 1; areas[area_how] += 1
        if args.limit and emitted >= args.limit:
            break
    summary = dict(emitted=emitted, skipped=counts, areas=areas)
    (out / (args.family + '.summary.json')).write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


def install(args):
    """Install digest-bound local passes from a staging tree without replacing files."""
    import os
    import shutil
    from pathlib import PurePosixPath

    staging = Path(args.source).resolve()
    dest = Path(args.dest).resolve()
    if not (dest / 'reconstruction').is_dir():
        raise ValueError('destination must be a checkout with reconstruction/')
    index = [json.loads(line) for line in (staging / (args.family + '.jsonl')).read_text().splitlines()]
    results = [json.loads(line) for line in (staging / 'results.jsonl').read_text().splitlines()]
    by_task = {}
    for result in results:
        if result['task'] in by_task:
            raise ValueError('duplicate result for task')
        by_task[result['task']] = result
    files = []
    for entry in index:
        result = by_task.get(entry['task'])
        if not result or result.get('result') != 'pass' or result.get('exit') != 0:
            continue
        if entry.get('family') != args.family:
            raise ValueError('index family mismatch')
        task_dir = Path(entry['task']).resolve()
        if not task_dir.is_relative_to(staging):
            raise ValueError('task must be inside staging')
        task = json.loads((task_dir / 'task.json').read_text())
        rel = PurePosixPath(task['compiled'])
        if (len(rel.parts) != 3 or rel.parts[0] != 'reconstruction' or
                not re.fullmatch(r'[a-z][a-z0-9_]*', rel.parts[1]) or
                not re.fullmatch(r'[A-Z][A-Za-z0-9_]*\.cpp', rel.parts[2])):
            raise ValueError('invalid compiled unit path')
        expected = {str(rel), str(rel.with_suffix('.h'))}
        if set(include_closure(staging, str(rel))) != expected:
            raise ValueError('unit must contain exactly its source and header')
        digest = task_digest(staging, task_dir)
        if not digest or entry.get('source_digest') != digest or result.get('source_digest') != digest:
            raise ValueError('source digest mismatch')
        if result.get('family') != args.family or result.get('rva') != entry.get('rva'):
            raise ValueError('result identity mismatch')
        if 'build_id' in entry:
            functions = task.get('functions') or []
            if (task.get('build_id') != entry['build_id'] or len(functions) != 1 or
                    int(str(functions[0]['rva']), 0) != entry['rva'] or
                    functions[0]['size'] != entry['size'] or task['compiled'] != entry['compiled']):
                raise ValueError('task identity mismatch')
            if not entry.get('input_digest') or result.get('input_digest') != entry['input_digest']:
                raise ValueError('result input digest mismatch')
            if input_digest(staging, task_dir) != entry['input_digest']:
                raise ValueError('staged input digest mismatch')
        for path in (Path(str(rel)), Path(str(rel)).with_suffix('.h')):
            source = staging / path
            if source.is_symlink() or not source.resolve().is_relative_to(staging) or not source.is_file():
                raise ValueError('invalid staged source')
            files.append(path)
    if len(files) != len(set(files)):
        raise ValueError('duplicate unit path')
    for path in files:
        if not (dest / path).resolve().is_relative_to(dest / 'reconstruction'):
            raise ValueError('destination escapes reconstruction')
    clashes = [str(path) for path in files if os.path.lexists(dest / path)]
    if clashes:
        raise ValueError('destination clashes: ' + ', '.join(clashes))
    for path in files:
        target = dest / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with (staging / path).open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
    print(json.dumps(dict(installed=len(files) // 2)))


def require_local_wine(raw):
    host = raw['hosts'][raw['attempt']]
    if (host.get('backend'), host.get('loader'), host.get('host_id')) != ('local', 'wine', 'mac-wine'):
        raise ValueError('attempt runner must be local mac-wine')
    return host


def attempt_all(args):
    import concurrent.futures
    import json
    import os
    import subprocess
    import time
    from pathlib import Path
    cfg = json.loads(Path(args.config).read_text())
    runner_path = Path(cfg['runners'])
    raw = json.loads(runner_path.read_text())
    host = require_local_wine(raw)
    out = Path(args.out).resolve(); wt = Path(cfg['worktree']).resolve()
    private = (Path(cfg['main']) / '.local').resolve()
    if not out.is_relative_to(private) or not wt.is_relative_to(private):
        raise ValueError('output and worktree must be inside the main checkout private directory')
    # Freeze the checked configuration so each child uses exactly this local host.
    snapshot = out / 'runner.json'
    snapshot.write_text(json.dumps(dict(runners_schema=raw['runners_schema'], attempt=raw['attempt'],
                                        hosts={raw['attempt']: host}, confirm=[])))
    env = dict(os.environ, SR_RUNNERS_CONFIG=str(snapshot))
    tasks = [json.loads(line) for p in sorted(out.glob('*-return.jsonl')) for line in p.read_text().splitlines()]
    if any(not task.get('input_digest') for task in tasks):
        raise ValueError('index missing input digest; use a new output directory')
    check_resume(tasks, wt)
    for task in tasks:
        if task['source_digest'] != task_digest(out, task['task']):
            raise ValueError('staged source changed; use a new output directory')
    log = out / 'results.jsonl'
    records = list(map(json.loads, log.read_text().splitlines())) if args.resume and log.exists() else []
    if any(not record.get('input_digest') for record in records):
        raise ValueError('resume result missing input digest; use a new output directory')
    check_resume(records, wt)
    runner_digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    if any(record.get('runner_digest') != runner_digest for record in records):
        raise ValueError('resume runner configuration changed; use a new output directory')
    if len({x['task'] for x in records}) != len(records):
        raise ValueError('duplicate resume result')
    done = {x['task'] for x in records}
    if log.exists() and not args.resume:
        raise ValueError('result log exists; use --resume')
    def run(task):
        digest = task_digest(wt, task['task'])
        inputs = input_digest(wt, task['task'])
        t = time.monotonic()
        proc = subprocess.run([str(wt / 'tools/verifier/attempt'), task['task']], cwd=wt, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        text = proc.stdout
        m = re.search(r'\b(PASS|FAIL) ([a-z0-9-]+)', text)
        result = m.group(1).lower() if m else 'error'
        reason = m.group(2) if m else ('compile-failed' if 'COMPILE FAILED' in text else 'infrastructure')
        Path(task['task'], 'output.txt').write_text(text)
        if task_digest(wt, task['task']) != digest or input_digest(wt, task['task']) != inputs:
            result, reason = 'error', 'inputs-changed-during-attempt'
        return dict(task=task['task'], rva=task['rva'], family=task['family'], source_digest=digest,
                    input_digest=inputs, runner_digest=runner_digest, result=result,
                    reason=reason, exit=proc.returncode, seconds=round(time.monotonic()-t, 2))
    pending = [t for t in tasks if t['task'] not in done]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool, log.open('a') as f:
        for result in pool.map(run, pending):
            f.write(json.dumps(result) + '\n'); f.flush()
            print(json.dumps(result), flush=True)


def main():
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('generate', 'attempt'):
        q = sub.add_parser(command)
        q.add_argument('--out', required=True)
        q.add_argument('--config', default='.local/stamp/config.json')
        q.add_argument('--resume', action='store_true')
        if command == 'generate':
            q.add_argument('--family', choices=('const-return', 'member-return'), required=True)
            q.add_argument('--limit', type=int)
        else:
            q.add_argument('--jobs', type=int, default=1)
    q = sub.add_parser('install')
    q.add_argument('--family', choices=('const-return', 'member-return'), required=True)
    q.add_argument('--from', dest='source', required=True)
    q.add_argument('--dest', required=True)
    args = p.parse_args()
    if (getattr(args, 'limit', None) is not None and args.limit < 1) or getattr(args, 'jobs', 1) < 1:
        p.error('limit and jobs must be positive')
    try:
        {'generate': generate, 'attempt': attempt_all, 'install': install}[args.command](args)
    except (ValueError, OSError, KeyError) as exc:
        p.exit(2, f'stamp: {exc}\n')


if __name__ == '__main__':
    main()
