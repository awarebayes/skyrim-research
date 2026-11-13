"""Generate a bounded private pilot from explicit per-member selection metadata.

The selection JSON names a private destination checkout, output directory and
members (rva, size, owner, area, kind, virtual, owner_is_rtti). No full-population
enrollment, family planning, acceptance or review is performed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/verifier'))
import bind
import disasm
import runners
import unit_build
from pecoff import CoffObject
import symbol_map
import census_leaf_template_v1 as template


def extract(rows, image_base, kind):
    """Check the whole narrow shape and extract only this member's reference."""
    instructions = [row[2] for row in rows]
    if kind == 'empty' and len(rows) == 1 and re.fullmatch(r'ret(?: 0x0)?', instructions[0]):
        return {}
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


def prepare(selection):
    root, out = (Path(selection[key]).resolve() for key in ('root', 'out'))
    if any('.local' not in path.parts for path in (root, out)):
        raise ValueError('pilot checkout and output must be private')
    members = selection['members']
    if not members or len(members) > 40:
        raise ValueError('pilot requires one through forty members')
    if len({m['rva'] for m in members}) != len(members) or len({m['owner'] for m in members}) != len(members):
        raise ValueError('duplicate pilot identity or unit')
    config = json.loads((root / '.local/verifier/config.json').read_text())
    image = Path(config['image'])
    if hashlib.sha256(image.read_bytes()).hexdigest() != json.loads((root / 'builds/target.json').read_text())['image_sha256']:
        raise ValueError('image differs from pinned target')
    objdump = disasm.find_objdump(config.get('objdump'))
    if objdump is None:
        raise ValueError('objdump unavailable')
    image_base = disasm.image_base(image)
    host = next(h for h in runners.load()['hosts'].values()
                if h['backend'] == 'local' and h['loader'] == 'wine')
    flags = json.loads((root / template.RECIPE).read_text())['flags']
    progress_path = root / 'data/progress.json'
    progress = json.loads(progress_path.read_text())
    existing = {f['rva']: f for f in progress['functions']}
    for member in members:
        prior = existing.get(member['rva'])
        if prior and (prior['status'] == 'matched' or prior['size'] != member['size']):
            raise ValueError('pilot overlaps an accepted function or another inventory extent')
    out.mkdir(parents=True, exist_ok=True)

    def one(member):
        rva, size, owner, kind = (member[k] for k in ('rva', 'size', 'owner', 'kind'))
        if type(rva) is not int or type(size) is not int or rva < 0 or size <= 0:
            raise ValueError('invalid member range')
        area = member['area']
        if not re.fullmatch(r'[a-z]+', area):
            raise ValueError('invalid area')
        method, h, cpp = template.emit(owner, kind, member['virtual'])
        prefix = template.header(owner, method, kind, rva=rva, size=size,
                                 owner_is_rtti=member['owner_is_rtti'])
        source = f'reconstruction/{area}/{owner}.cpp'
        write_new(root / source, prefix + cpp)
        write_new((root / source).with_suffix('.h'), prefix + h)
        refs = extract(disasm.target_rows(objdump, str(image), rva, size), image_base, kind)
        directory = out / 'tasks' / f'p93-{kind}-{rva:x}'
        directory.mkdir(parents=True, exist_ok=True)
        objpath = directory / 'probe.obj'
        with runners.slot(host['host_id'], host['max_parallel']):
            proc = subprocess.run([str(Path(host['msvc']) / 'bin/x64/cl'), *flags,
                                   '/Fo' + str(objpath), str(root / source)],
                                  env=unit_build.clean_env(runners.LocalTransport(host).env()),
                                  capture_output=True, text=True, timeout=300)
        if proc.returncode:
            (directory / 'probe.log').write_text(proc.stdout + proc.stderr)
            raise ValueError('probe compilation failed')
        obj = CoffObject(objpath.read_bytes())
        candidates = [s for s in obj.symbols.values() if s.name.startswith(f'?{method}@{owner}@@')
                      and s.section > 0]
        if len(candidates) != 1:
            raise ValueError('ambiguous compiled method identity')
        name = candidates[0].name
        entries = {name: dict(rva=rva, size=size)}
        if kind != 'empty':
            external = 'census_target' if kind == 'forward' else '?census_global@@3EA'
            if external not in {s.name for s in obj.symbols.values()}:
                raise ValueError('compiled reference identity missing')
            entries[external] = dict(rva=refs['target-rva'], size=None)
        smap = dict(schema=1, build_id=template.BUILD, symbols=entries, folds=[],
                    _provenance=dict(note='Explicit per-member pilot references; names and signatures are guesses.',
                                     entries=[dict(name=n, rva=hex(e['rva']), community_name=None,
                                                   note='Extracted independently from this pinned-image member.')
                                              for n, e in entries.items()]))
        digest = hashlib.sha256(symbol_map.serialize(smap)).hexdigest()
        map_path = f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(root, map_path, smap)
        parameters = {key: value for key, value in member.items() if key != 'owner_source'}
        parameters.update(refs)
        metadata = dict(origin=template.origin(kind), family_parameters=parameters, name_source='GUESS(low)')
        task = dict(task_schema=1, task_id=directory.name, build_id=template.BUILD,
                    compiled=source, recipe=template.RECIPE, symbols=map_path,
                    functions=[dict(rva=rva, size=size, symbol=name, family_metadata=metadata)])
        (directory / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
        return str(directory), dict(id=f'{template.BUILD}-0x{rva:x}', build_id=template.BUILD,
                                    rva=rva, size=size, status='mapped', name=f'{owner}::{method}',
                                    name_origin='GUESS', name_source='GUESS(low): census pilot method; signature unknown.',
                                    owner='awarebayes', evidence=template.EVIDENCE)

    with ThreadPoolExecutor(max_workers=4) as executor:
        generated = list(executor.map(one, members))
    for _, entry in generated:
        if entry['rva'] in existing:
            if existing[entry['rva']]['size'] != entry['size']:
                raise ValueError('existing inventory has another extent')
        else:
            progress['functions'].append(entry)
    tasks = [task for task, _ in generated]
    progress_path.write_text(json.dumps(progress, indent=2) + '\n')
    bind.preflight(tasks, root)
    (out / 'all.txt').write_text(''.join(task + '\n' for task in tasks))
    print(f'prepared {len(tasks)} pilot members; binding preflight passed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    args = parser.parse_args()
    prepare(json.loads(args.selection.read_text()))
