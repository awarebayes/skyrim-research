"""Generate private storage candidates using an explicit private extraction contract.

Instruction predicates, target membership, and all extracted rows stay in .local.
This tool never embeds a target opcode sequence. The natural source template is
separate from the instruction contract; neither a shape nor a compile is a pass.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/verifier'))
import bind
import disasm
import runners
import symbol_map
import unit_build
from pecoff import CoffObject, PeImage
from census_leaf_generate import write_new
from storage_row_extract import extract_eh, extract_instructions
import storage_init_template_v2 as template
import storage_init_template_v1 as prior_template

# Pins the generic extraction implementation as part of this parameter source.
EXTRACTOR_SHA256 = 'bef60ec00d5199f4bc7923025c3eeed141ed45a3068856789b18d848b899afc5'

# Factual artifact digest only; the private instruction contract is never published.
CONTRACT_SHA256 = 'c3e2632952e50d5ad8d548b322b58fe1d659c286c7aa0147fae98d795cd1df8d'


def load_contract(path):
    blob = Path(path).read_bytes()
    if hashlib.sha256(blob).hexdigest() != CONTRACT_SHA256:
        raise ValueError('private extraction contract differs from pinned digest')
    return json.loads(blob)


def replacement_allowed(existing, member):
    return (len(existing) == 1 and existing[0]['rva'] == member['rva']
            and existing[0]['size'] == member['size'] and existing[0]['status'] == 'mapped'
            and existing[0]['name'] == f'StorageInit{member["rva"]:x}::initialize')


def extract_member(image, objdump, image_path, member, contract, procedures, handler):
    rva, size = member['rva'], member['size']
    primary = disasm.target_rows(objdump, str(image_path), rva, size)
    parameters = extract_instructions(primary, image.image_base, contract['primary'])
    eh = extract_eh(image, rva, procedures, handler)
    if any(eh[k] != v for k, v in contract['eh'].items()):
        raise ValueError('EH metadata differs from private contract')
    if len(eh['actions']) != 1 or not eh['actions'][0][1]:
        raise ValueError('template requires one nonnull cleanup')
    state, action = eh.pop('actions')[0]
    cleanup = disasm.target_rows(objdump, str(image_path), action, contract['cleanup_size'])
    parameters.update(extract_instructions(cleanup, image.image_base, contract['cleanup']))
    parameters.update(eh)
    parameters.update({'entry-rva': rva, 'size': size, 'cleanup-action-rva': action, 'cleanup-to-state': state})
    return parameters


def prepare(config):
    root, out, contract_path = (Path(config[k]).resolve() for k in ('root', 'out', 'contract'))
    if any('.local' not in p.parts for p in (root, out, contract_path)):
        raise ValueError('candidate root, output and contract must be private')
    if hashlib.sha256((ROOT / 'tools/storage_row_extract.py').read_bytes()).hexdigest() != EXTRACTOR_SHA256:
        raise ValueError('generic extractor differs from pinned parameter source')
    members = config['members']
    if not members or len({m['rva'] for m in members}) != len(members):
        raise ValueError('empty or duplicate population')
    contract = load_contract(contract_path)
    settings = json.loads((root / '.local/verifier/config.json').read_text())
    image_path = Path(settings['image'])
    blob = image_path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != json.loads((root / 'builds/target.json').read_text())['image_sha256']:
        raise ValueError('image differs from pinned target')
    image = PeImage(blob)
    procedures = {}
    for begin, _, unwind in image.runtime_functions():
        procedures.setdefault(begin, []).append(unwind)
    objdump = disasm.find_objdump(settings.get('objdump'))
    if not objdump:
        raise ValueError('objdump unavailable')
    host = next(h for h in runners.load()['hosts'].values() if h['backend'] == 'local' and h['loader'] == 'wine')
    flags = json.loads((root / template.RECIPE).read_text())['flags']
    handler = json.loads((root / f'reports/{template.BUILD}/symbol-map.json').read_text())['symbols']['__CxxFrameHandler3']
    progress_path = root / 'data/progress.json'
    progress = json.loads(progress_path.read_text())
    for m in members:
        overlaps = [f for f in progress['functions'] if m['rva'] < f['rva'] + f['size'] and f['rva'] < m['rva'] + m['size']]
        if overlaps and not replacement_allowed(overlaps, m):
            raise ValueError('member overlaps an unowned or accepted inventory entry')
    extracted = [extract_member(image, objdump, image_path, m, contract, procedures, handler['rva']) for m in members]
    out.mkdir(parents=True, exist_ok=True)
    (out / 'rows.json').write_text(json.dumps(extracted, indent=2) + '\n')

    def one(parameters):
        rva, size = parameters['entry-rva'], parameters['size']
        cls, header, cpp, origin = template.emit(rva, size, parameters)
        source = f'reconstruction/storage/{cls}.cpp'
        _, old_header, old_cpp, _ = prior_template.emit(rva, size, parameters)
        for path, text, old in ((root/source, cpp, old_cpp), ((root/source).with_suffix('.h'), header, old_header)):
            if path.exists():
                if path.is_symlink() or path.read_text() not in (old, text):
                    raise ValueError('source is not the frozen prior version')
                path.write_text(text)
            else:
                write_new(path, text)
        directory = out / 'tasks' / f'p111-v2-storage-{rva:x}'
        directory.mkdir(parents=True, exist_ok=True)
        objpath = directory / 'probe.obj'
        with runners.slot(host['host_id'], host['max_parallel']):
            proc = subprocess.run([str(Path(host['msvc']) / 'bin/x64/cl'), *flags, '/Fo'+str(objpath), str(root / source)],
                                  env=unit_build.clean_env(runners.LocalTransport(host).env()), capture_output=True, text=True, timeout=300)
        if proc.returncode:
            (directory / 'probe.log').write_text(proc.stdout + proc.stderr)
            raise ValueError('probe compilation failed')
        obj = CoffObject(objpath.read_bytes())
        name = f'?initialize@{cls}@@SAIPEAX@Z'
        entries = {name: dict(rva=rva, size=size),
                   '??_7Adapter@@6B@': dict(rva=parameters['table-rva'], size=None),
                   '?storage_helper@@YAIPEAIPEAUAdapterBase@@II@Z': dict(rva=parameters['helper-rva'], size=None),
                   '??1Adapter@@UEAA@XZ': dict(rva=parameters['cleanup-rva'], size=None),
                   '__CxxFrameHandler3': handler}
        names = {s.name for s in obj.symbols.values()}
        if not set(entries) <= names:
            raise ValueError('compiled reference identity missing')
        smap = dict(schema=1, build_id=template.BUILD, symbols=entries, folds=[],
                    _provenance=dict(note='Per-member storage and EH bindings; all reconstruction names are guesses.',
                                     entries=[dict(name=n, rva=hex(e['rva']), community_name=None,
                                                   note='Independently extracted from the pinned-image member.') for n,e in entries.items()]))
        digest = hashlib.sha256(symbol_map.serialize(smap)).hexdigest()
        map_path = f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(root, map_path, smap)
        metadata = dict(origin=origin, family_parameters=parameters, name_source='GUESS(low)')
        task = dict(task_schema=1, task_id=directory.name, build_id=template.BUILD,
                    compiled=source, recipe=template.RECIPE, symbols=map_path,
                    functions=[dict(rva=rva, size=size, symbol=name, family_metadata=metadata)])
        (directory / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
        entry = dict(id=f'{template.BUILD}-0x{rva:x}', build_id=template.BUILD, rva=rva, size=size,
                     status='mapped', name=f'{cls}::initialize', name_origin='GUESS',
                     name_source='GUESS(low): storage adapter helper; owning type and original signature unknown.',
                     owner='awarebayes', evidence=template.EVIDENCE)
        return str(directory), entry

    with ThreadPoolExecutor(max_workers=4) as executor:
        generated = list(executor.map(one, extracted))
    existing = {f['rva'] for f in progress['functions']}
    progress['functions'].extend(entry for _, entry in generated if entry['rva'] not in existing)
    progress_path.write_text(json.dumps(progress, indent=2) + '\n')
    tasks = [task for task, _ in generated]
    bind.preflight(tasks, root)
    (out / 'all.txt').write_text(''.join(task+'\n' for task in tasks))
    print(f'prepared {len(tasks)} members; binding preflight passed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    args = parser.parse_args()
    prepare(json.loads(args.selection.read_text()))
