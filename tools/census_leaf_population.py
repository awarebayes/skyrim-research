"""Generate a complete frozen census leaf cohort with per-entry reference bindings.

No match records, reviews or acceptance evidence are manufactured here. Generation
refuses existing source paths and accepted entries; confirm supplies match records.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/verifier'))
import bind
import disasm
import symbol_map
import census_leaf_population_template_v1 as template


def extract(rows, image_base, kind):
    instructions = [row[2] for row in rows]
    if kind == 'forward' and len(rows) == 1:
        match = re.fullmatch(r'jmp (0x[0-9a-f]+)(?: <[^>]*>)?', instructions[0])
    elif kind == 'address' and len(rows) == 2 and instructions[1] == 'ret':
        match = re.fullmatch(r'lea rax, \[rip[^\]]*\] # (0x[0-9a-f]+)(?: <[^>]*>)?', instructions[0])
    else:
        match = None
    if not match or int(match[1], 16) < image_base:
        raise ValueError('unsupported-reference-shape')
    return {'target-rva': int(match[1], 16) - image_base}


def write_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text() != content:
            raise ValueError('refusing to overwrite existing source')
    else:
        path.write_text(content)


def generate(ranking, kind, out):
    out = out.resolve()
    if not out.is_relative_to(ROOT / '.local'):
        raise ValueError('output must stay in repository .local')
    family = {'forward': 'tail-call-thunk', 'address': 'return-global-address'}[kind]
    groups = [g for g in ranking['groups'] if set(g['families']) == {family}]
    if len(groups) != 1:
        raise ValueError('ambiguous census cohort')
    rows = sorted(groups[0]['rows'], key=lambda r: int(r['rva'], 16))
    if len(rows) != groups[0]['members'] or len({r['rva'] for r in rows}) != len(rows):
        raise ValueError('incomplete or duplicate census population')
    config = json.loads((ROOT / '.local/verifier/config.json').read_text())
    image = Path(config['image'])
    if hashlib.sha256(image.read_bytes()).hexdigest() != json.loads((ROOT / 'builds/target.json').read_text())['image_sha256']:
        raise ValueError('image differs from pinned target')
    objdump = disasm.find_objdump(config.get('objdump'))
    if objdump is None:
        raise ValueError('objdump unavailable')
    image_base = disasm.image_base(image)
    progress_path = ROOT / 'data/progress.json'
    progress = json.loads(progress_path.read_text())
    existing = {f['rva']: f for f in progress['functions']}
    for row in rows:
        prior = existing.get(int(row['rva'], 16))
        if prior and (prior['status'] == 'matched' or prior['size'] != int(row['size'])):
            raise ValueError('population overlaps accepted entry or another inventory extent')
    out.mkdir(parents=True, exist_ok=True)

    def one(row):
        rva, size = int(row['rva'], 16), int(row['size'])
        owner, method, h, cpp, symbol, external = template.emit(kind, rva, size)
        refs = extract(disasm.target_rows(objdump, str(image), rva, size), image_base, kind)
        source = f'reconstruction/leaves/{owner}.cpp'
        write_new(ROOT / source, cpp)
        write_new((ROOT / source).with_suffix('.h'), h)
        entries = {symbol: dict(rva=rva, size=size), external: dict(rva=refs['target-rva'], size=None)}
        smap = dict(schema=1, build_id=template.BUILD, symbols=entries, folds=[],
                    _provenance=dict(note='Independent per-entry reference; all names and signatures are stand-ins.',
                                     entries=[dict(name=n, rva=hex(e['rva']), community_name=None,
                                                   note='Extracted from this pinned-image member.')
                                              for n, e in entries.items()]))
        digest = hashlib.sha256(symbol_map.serialize(smap)).hexdigest()
        map_path = f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(ROOT, map_path, smap)
        params = dict(rva=rva, size=size, kind=kind, **refs)
        metadata = dict(origin=template.origin(kind), family_parameters=params, name_source='GUESS(low)')
        directory = out / 'tasks' / f'p97-{kind}-{rva:x}'
        directory.mkdir(parents=True, exist_ok=True)
        task = dict(task_schema=1, task_id=directory.name, build_id=template.BUILD,
                    compiled=source, recipe=template.RECIPE, symbols=map_path,
                    functions=[dict(rva=rva, size=size, symbol=symbol, family_metadata=metadata)])
        (directory / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
        entry = dict(id=f'{template.BUILD}-0x{rva:x}', build_id=template.BUILD,
                     rva=rva, size=size, status='mapped', name=f'{owner}::{method}',
                     name_origin='GUESS', name_source='GUESS(low): ABI stand-in; original ownership and signature unknown.',
                     owner='awarebayes', evidence=template.EVIDENCE)
        return str(directory), entry

    with ThreadPoolExecutor(max_workers=4) as executor:
        generated = list(executor.map(one, rows))
    for _, entry in generated:
        if entry['rva'] not in existing:
            progress['functions'].append(entry)
    progress_path.write_text(json.dumps(progress, indent=2) + '\n')
    tasks = [task for task, _ in generated]
    bind.preflight(tasks, ROOT)
    (out / 'all.txt').write_text(''.join(task + '\n' for task in tasks))
    (out / 'population.json').write_text(json.dumps(dict(build_id=template.BUILD,
        members=[entry['rva'] for _, entry in generated]), indent=2) + '\n')
    print(f'prepared {len(tasks)} {kind} members; complete binding preflight passed', flush=True)


def records_to_spec(kind, out):
    """Validate every actual confirmation before linking reports and planning review."""
    import accept_function as af
    import family_review as fr
    progress, target = af.load(ROOT)
    by_rva = {f['rva']: f for f in progress['functions']}
    directories = (out / 'all.txt').read_text().splitlines()
    population = json.loads((out / 'population.json').read_text())
    expected = set(population['members'])
    if population['build_id'] != template.BUILD or len(expected) != len(population['members']):
        raise ValueError('invalid generated population')
    params, first, binding = [], [], None
    pending = []
    for directory in directories:
        task = json.loads((Path(directory) / 'task.json').read_text())
        member = task['functions'][0]
        fn = dict(by_rva[member['rva']])
        fn['report'] = f'reports/{template.BUILD}/0x{fn["rva"]:x}.json'
        record = af.validate_match(fn, target, ROOT)
        metadata = member['family_metadata']
        if (record.get('origin') != template.origin(kind)
                or record.get('family_parameters') != metadata['family_parameters']
                or record.get('name_source') != metadata['name_source']):
            raise ValueError('confirmed member differs from generated origin or parameter binding')
        current = fr.binding(fn, record)
        if binding is not None and current != binding:
            raise ValueError('population recipe/compiler/comparator bindings differ')
        binding = current
        params.append(record['family_parameters'])
        pending.append(fn)
    if (len(pending) < 20 or len({f['id'] for f in pending}) != len(pending)
            or {f['rva'] for f in pending} != expected):
        raise ValueError('incomplete or duplicate confirmed population')
    for fn in sorted(pending, key=lambda f: f['rva'])[:20]:
        first.append(fn['id'])
    source = lambda name: dict(path=name, sha256=hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
    spec = dict(origin=template.origin(kind), binding=binding,
                template_source=source('tools/census_leaf_population_template_v1.py'),
                parameter_source=source('tools/census_leaf_population.py'),
                parameter_ranges=fr.exact_ranges(params), first_members=first)
    # No inventory mutation until the complete cohort validates.
    for fn in pending:
        by_rva[fn['rva']]['report'] = fn['report']
    (ROOT / 'data/progress.json').write_text(json.dumps(progress, indent=2) + '\n')
    fr.write(ROOT, out / 'family-spec.json', spec)
    print(f'validated and linked {len(pending)} reproduced {kind} records; exact-row spec ready', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ranking', type=Path)
    parser.add_argument('--kind', required=True, choices=('forward', 'address'))
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--records-to-spec', action='store_true')
    args = parser.parse_args()
    if args.records_to_spec:
        records_to_spec(args.kind, args.out.resolve())
    elif args.ranking:
        generate(json.loads(args.ranking.read_text()), args.kind, args.out)
    else:
        parser.error('--ranking is required for generation')
