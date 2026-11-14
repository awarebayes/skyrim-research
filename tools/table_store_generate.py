"""Decode each complete table store and independently bind its RTTI locator.

The selection names a private checkout, output directory and explicit RVA/size
members. All image reads and raw analysis stay private; emitted maps contain
identities only. No template address is transferred between members.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools/verifier'), str(ROOT/'tools/ghidra')]
import bind
import disasm
import export_pack as ep
from build_function_table import Rtti
from pecoff import Reject
import symbol_map
import table_store_template_v1 as template


def extract(rows, rva, image_base):
    if ([r[0] for r in rows] != [0, 7, 10]
            or sum(len(r[1].split()) for r in rows) != 11):
        raise ValueError('different complete instruction extent')
    table = re.fullmatch(r'lea rax, \[rip[^\]]*\] # (0x[0-9a-f]+)(?: <[^>]*>)?', rows[0][2])
    if not table or rows[1][2] != 'mov qword ptr [rcx], rax' or rows[2][2] != 'ret':
        raise ValueError('different primary table store shape')
    target = int(table[1], 16) - image_base
    if target < 8:
        raise ValueError('table reference outside image')
    return {'entry-rva': rva, 'size': 11, 'table-rva': target}


def bind_rtti(img, rtti, params):
    table = params['table-rva']
    try:
        col = struct.unpack('<Q', img.read(table-8, 8))[0] - rtti.base
        if not 0 < col < img.size_of_image:
            raise ValueError('no in-image complete object locator')
        sig, offset, cdoff, td, chd, selfr = struct.unpack('<6I', img.read(col, 24))
        if sig != 1 or selfr != col or table-8 not in rtti.reloc:
            raise ValueError('invalid complete object locator')
        if rtti.vftables.get(table) != (offset, td, chd):
            raise ValueError('RTTI binding disagreement')
        if offset != 0 or cdoff != 0:
            raise ValueError('non-primary or construction table')
        name = rtti.td_name(td)
        if not re.fullmatch(r'\.\?A[VU].+@@', name):
            raise ValueError('invalid class type descriptor')
        _, bases = rtti.chain(chd)
        if not bases or bases[0] != name:
            raise ValueError('hierarchy does not bind class descriptor')
        first = struct.unpack('<Q', img.read(table, 8))[0] - rtti.base
        section = img.section(first)
        if section is None or not section.flags & ep.EXEC:
            raise ValueError('table has no executable first slot')
    except (Reject, struct.error, IndexError) as error:
        raise ValueError('unreadable table RTTI') from error
    return dict(params, **{'locator-rva': col, 'type-descriptor-rva': td,
                          'hierarchy-rva': chd, 'subobject-offset': offset,
                          'construction-displacement': cdoff})


def write_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and (path.is_symlink() or path.read_text() != content):
        raise ValueError('refusing different existing source')
    path.write_text(content)


def prepare(selection):
    root, out = (Path(selection[k]).resolve() for k in ('root', 'out'))
    if any('.local' not in p.parts for p in (root, out)):
        raise ValueError('private outputs required')
    members = selection['members']
    if len({m['rva'] for m in members}) != len(members):
        raise ValueError('duplicate member')
    config = json.loads((root/'.local/verifier/config.json').read_text())
    image = Path(config['image'])
    target = json.loads((root/'builds/target.json').read_text())
    img = ep.ImageFacts(image)
    if img.sha256 != target['image_sha256']:
        raise ValueError('image hash mismatch')
    rtti = Rtti(img, lambda r: True)
    objdump = disasm.find_objdump(config.get('objdump'))
    if objdump is None:
        raise ValueError('objdump unavailable')
    progress = json.loads((root/'data/progress.json').read_text())
    existing = {f['rva']: f for f in progress['functions']}
    for m in members:
        old = existing.get(m['rva'], {})
        if (type(m['rva']) is not int or m['rva'] < 0 or m['size'] != 11
                or old.get('status') == 'matched' or old.get('size', 11) != 11):
            raise ValueError('accepted member or conflicting identity/extent')
    def decode(m):
        params = extract(disasm.target_rows(objdump, str(image), m['rva'], 11), m['rva'], rtti.base)
        return bind_rtti(img, rtti, params)
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(decode, members))
    tasks = []
    for params in rows:
        rva = params['entry-rva']
        e = template.emit(rva)
        source = f'reconstruction/leaves/{e["cls"]}.cpp'
        write_new(root/source, e['source'])
        write_new((root/source).with_suffix('.h'), e['header'])
        entries = {e['symbol']: dict(rva=rva, size=11),
                   e['table']: dict(rva=params['table-rva'], size=None)}
        smap = dict(schema=1, build_id=template.BUILD, symbols=entries, folds=[],
                    _provenance=dict(entries=[dict(name=n, rva=hex(v['rva']), community_name=None,
                    note='Independent whole-member reference and primary RTTI binding; guessed source identity.')
                    for n, v in entries.items()]))
        digest = hashlib.sha256(symbol_map.serialize(smap)).hexdigest()
        map_path = f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(root, map_path, smap)
        taskdir = out/'tasks'/f'p107-{rva:x}'
        taskdir.mkdir(parents=True, exist_ok=True)
        task = dict(task_schema=1, task_id=taskdir.name, build_id=template.BUILD,
                    compiled=source, recipe=template.RECIPE, symbols=map_path,
                    functions=[dict(rva=rva, size=11, symbol=e['symbol'], family_metadata=dict(
                    origin=template.origin(), family_parameters=params, name_source='GUESS(low)'))])
        write_new(taskdir/'task.json', json.dumps(task, indent=2)+'\n')
        tasks.append(str(taskdir))
        if rva not in existing:
            progress['functions'].append(dict(id=f'{template.BUILD}-0x{rva:x}', build_id=template.BUILD,
                rva=rva, size=11, status='mapped', name=f'{e["cls"]}::~{e["cls"]}', name_origin='GUESS',
                name_source='GUESS(low): primary table store represented as a polymorphic destructor; RTTI binds the table, not the original method role or full layout.',
                owner='awarebayes', evidence=template.EVIDENCE))
    (root/'data/progress.json').write_text(json.dumps(progress, indent=2)+'\n')
    bind.preflight(tasks, root)
    (out/'all.txt').write_text(''.join(t+'\n' for t in tasks))
    (out/'rows.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(f'prepared {len(tasks)} primary RTTI-bound stores; whole-list binding preflight passed', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--selection', type=Path, required=True)
    prepare(json.loads(p.parse_args().selection.read_text()))
