"""Generate checked-copy candidates with complete per-member reference validation.

The compiled template must match every non-reference byte and relocation field
before generation. The unchanged comparator still decides each actual match.
Inputs and rejected-member diagnostics remain private. No acceptance is done.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/verifier'))
import bind
import runners
import symbol_map
import unit_build
from pecoff import CoffObject, PeImage
from census_buffer_extract import extract, private_output
from census_leaf_generate import write_new
import checked_copy_template_v1 as template

# These hashes are part of the manifest-pinned parameter source. A helper edit
# requires a newly reviewed parameter-source revision, even if template code is unchanged.
EXTRACTION_DEPENDENCIES = {'tools/census_buffer_extract.py': '81450a6ac69a1a2afe3ce60ea6ad406a3c99f0a629289a39470036962518769d', 'tools/analysis/imagemodel.py': '40d948f70c939015e989dbc333b811ed53dc98f43c986f32ec37780acc432120', 'tools/analysis/x64.py': '11085bc7d8c33eabad00d7649312988426a6f21094f9ad8e99d62bc0c22d83d9', 'tools/pecoff.py': '2d617b4fc0bc619e70e4ef3c64c95a2b3565e9105ae283e281984d14665b3a38', 'tools/census_leaf_generate.py': '76e9ffdd812a10f8c558c316212c8d566bd250e5c12c7ca43d49ed98b1b28edd'}


def check_dependencies():
    for name, expected in EXTRACTION_DEPENDENCIES.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("pinned extraction dependency differs: " + name)


def bindings(image, rva, size, candidate, name):
    check_dependencies()
    symbols = [s for s in candidate.symbols.values() if s.name == name and s.is_function
               and s.storage == 2 and s.value == 0 and s.section > 0]
    if len(symbols) != 1:
        raise ValueError('template identity is not unique')
    section = candidate.section(symbols[0].section)
    if len(section.data) != size:
        raise ValueError('template extent differs')
    member = extract(image, rva, size)
    actual = {ref['offset']: ref for ref in member['references']}
    if len(actual) != len(member['references']) or len(actual) != len(section.relocs):
        raise ValueError('reference counts differ')
    target_code = bytearray(image.read(rva, size, 'private template enrollment')[1])
    candidate_code = bytearray(section.data)
    result, occupied = {}, set()
    for rel in section.relocs:
        ref = actual.get(rel.offset)
        if (rel.kind not in range(4, 10) or ref is None or ref['tail'] != rel.kind-4
                or ref['kind'] != 'REL32' or ref['width'] != 4):
            raise ValueError('reference field layout differs')
        span = set(range(rel.offset, rel.offset+4))
        if occupied & span:
            raise ValueError('overlapping references')
        occupied |= span
        if int.from_bytes(section.data[rel.offset:rel.offset+4], 'little', signed=True):
            raise ValueError('template reference has a nonzero addend')
        symbol = candidate.symbols[rel.symbol].name
        if symbol in result and result[symbol] != ref['target_rva']:
            raise ValueError('one template reference binds different targets')
        result[symbol] = ref['target_rva']
        candidate_code[rel.offset:rel.offset+4] = bytes(4)
        target_code[rel.offset:rel.offset+4] = bytes(4)
    if candidate_code != target_code:
        raise ValueError('complete non-reference instruction stream differs')
    return result


def generate(population, out, limit=None):
    check_dependencies()
    out = private_output(out)
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError('candidate limit must be positive')
    config = json.loads((ROOT / '.local/verifier/config.json').read_text())
    blob = Path(config['image']).read_bytes()
    target = json.loads((ROOT / 'builds/target.json').read_text())
    if target['status'] != 'pinned' or hashlib.sha256(blob).hexdigest() != target['image_sha256']:
        raise ValueError('image differs from pinned target')
    image = PeImage(blob)
    rows = sorted(population['rows'], key=lambda r: int(r['rva'], 16))
    if len(rows) != population['members'] or len({r['rva'] for r in rows}) != len(rows):
        raise ValueError('incomplete or duplicate population')
    progress = json.loads((ROOT / 'data/progress.json').read_text())
    existing = {f['rva']: f for f in progress['functions']}
    out.mkdir(parents=True, exist_ok=True)
    host = next(h for h in runners.load()['hosts'].values() if h['backend'] == 'local' and h['loader'] == 'wine')
    flags = json.loads((ROOT / template.RECIPE).read_text())['flags']
    accepted, rejected, tasks = [], [], []
    probe, probe_name = None, None
    for row in rows:
        rva, size = int(row['rva'], 16), int(row['size'])
        if size != population['size']:
            raise ValueError('population extent differs')
        prior = existing.get(rva)
        if prior and (prior['status'] == 'matched' or prior['size'] != size):
            rejected.append(dict(rva=rva, reason='already accepted or extent differs'))
            continue
        owner, name, header, source = template.emit(rva, size)
        directory = out / 'tasks' / f'p118-copy-{rva:x}'
        directory.mkdir(parents=True, exist_ok=True)
        compiled = f'reconstruction/buffers/{owner}.cpp'
        # A private probe avoids leaving rejected source units in the repository.
        write_new(directory / f'{owner}.h', header)
        write_new(directory / f'{owner}.cpp', source)
        if probe is None:
            objpath = directory / 'probe.obj'
            with runners.slot(host['host_id'], host['max_parallel']):
                proc = subprocess.run([str(Path(host['msvc']) / 'bin/x64/cl'), *flags,
                                       '/Fo'+str(objpath), str(directory / f'{owner}.cpp')],
                                      env=unit_build.clean_env(runners.LocalTransport(host).env()),
                                      capture_output=True, text=True, timeout=300)
            (directory / 'probe.log').write_text(proc.stdout + proc.stderr)
            if proc.returncode:
                raise ValueError('template compilation failed')
            probe, probe_name = CoffObject(objpath.read_bytes()), name
        try:
            refs = bindings(image, rva, size, probe, probe_name)
        except ValueError as error:
            rejected.append(dict(rva=rva, reason=str(error)))
            continue
        write_new(ROOT / compiled, source)
        write_new((ROOT / compiled).with_suffix('.h'), header)
        entries = {n: dict(rva=t, size=None) for n, t in refs.items()}
        entries[name] = dict(rva=rva, size=size)
        smap = dict(schema=1, build_id=template.BUILD, symbols=entries, folds=[],
                    _provenance=dict(note='Checked-copy ABI stand-in; each member reference independently decoded.',
                                     entries=[dict(name=n, rva=hex(e['rva']), community_name=None,
                                                   note='Independent member binding; names are guesses.')
                                              for n, e in entries.items()]))
        digest = hashlib.sha256(symbol_map.serialize(smap)).hexdigest()
        map_path = f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(ROOT, map_path, smap)
        params = dict(rva=rva, size=size)
        params.update({f'reference-{i}': refs[n] for i, n in enumerate(sorted(refs))})
        metadata = dict(origin=template.origin(), family_parameters=params, name_source='GUESS(low)')
        task = dict(task_schema=1, task_id=directory.name, build_id=template.BUILD,
                    compiled=compiled, recipe=template.RECIPE, symbols=map_path,
                    functions=[dict(rva=rva, size=size, symbol=name, family_metadata=metadata)])
        (directory / 'task.json').write_text(json.dumps(task, indent=2)+'\n')
        tasks.append(str(directory))
        accepted.append(dict(id=f'{template.BUILD}-0x{rva:x}', build_id=template.BUILD, rva=rva, size=size,
                             status='mapped', name=f'{owner}::Copy', name_origin='GUESS', owner='awarebayes',
                             name_source='GUESS(low): checked-copy ABI stand-in; ownership unknown.', evidence=template.EVIDENCE))
        if limit and len(accepted) >= limit:
            break
    for fn in accepted:
        if fn['rva'] not in existing:
            progress['functions'].append(fn)
    (ROOT / 'data/progress.json').write_text(json.dumps(progress, indent=2)+'\n')
    bind.preflight(tasks, ROOT)
    (out / 'all.txt').write_text(''.join(t+'\n' for t in tasks))
    (out / 'selection.json').write_text(json.dumps(dict(members=accepted, rejected=rejected), indent=2)+'\n')
    print(f'Prepared {len(tasks)} candidates; {len(rejected)} rejected; no match evidence created.', flush=True)


def records_to_spec(out):
    """Link only a complete, two-host-confirmed population and freeze exact rows."""
    import accept_function as af
    import family_review as fr
    out = private_output(out)
    progress, target = af.load(ROOT)
    by_rva = {f['rva']: f for f in progress['functions']}
    selected = json.loads((out / 'selection.json').read_text())['members']
    expected = {fn['rva'] for fn in selected}
    if len(expected) != len(selected) or len(selected) < 20:
        raise ValueError('need at least twenty unique selected members')
    pending, rows, binding = [], [], None
    for directory in (out / 'all.txt').read_text().splitlines():
        task = json.loads((Path(directory) / 'task.json').read_text())
        member = task['functions'][0]
        fn = dict(by_rva[member['rva']])
        fn['report'] = f'reports/{template.BUILD}/0x{fn["rva"]:x}.json'
        record = af.validate_match(fn, target, ROOT)
        metadata = member['family_metadata']
        if (record.get('origin') != template.origin()
                or record.get('family_parameters') != metadata['family_parameters']
                or record.get('name_source') != metadata['name_source']):
            raise ValueError('confirmation differs from generated member')
        current = fr.binding(fn, record)
        if binding is not None and binding != current:
            raise ValueError('population verifier bindings differ')
        binding = current
        rows.append(record['family_parameters'])
        pending.append(fn)
    if len(pending) != len(expected) or {fn['rva'] for fn in pending} != expected:
        raise ValueError('incomplete or duplicate confirmed population')
    source = lambda name: dict(path=name, sha256=hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
    spec = dict(origin=template.origin(), binding=binding, parameter_ranges=fr.exact_ranges(rows),
                template_source=source('tools/checked_copy_template_v1.py'),
                parameter_source=source('tools/census_checked_copy_generate.py'),
                first_members=[fn['id'] for fn in sorted(pending, key=lambda f:f['rva'])[:20]])
    for fn in pending:
        by_rva[fn['rva']]['report'] = fn['report']
    (ROOT / 'data/progress.json').write_text(json.dumps(progress, indent=2)+'\n')
    fr.write(ROOT, out / 'family-spec.json', spec)
    print(f'Validated {len(pending)} two-host records; exact-row family spec ready.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--population', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--records-to-spec', action='store_true')
    args = parser.parse_args()
    if args.records_to_spec:
        records_to_spec(args.out)
    elif args.population:
        generate(json.loads(args.population.read_text()), args.out, args.limit)
    else:
        parser.error('--population is required for generation')
