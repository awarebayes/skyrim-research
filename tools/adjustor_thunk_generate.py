"""Reconcile independent member-local tailcalls and image-relative MSVC RTTI.

Selection JSON is private runtime input, never a target byte signature. LLVM
decodes arithmetic and direct-transfer operands. RTTI fields follow the MSVC
image-relative locator/base-descriptor format; no captured table is embedded.
The COFF reference is bound to the observed target transfer, not to a guessed name.
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
import disasm
from export_pack import ImageFacts
import bind
import symbol_map
import adjustor_thunk_template_v2 as template


def extract(rows, rva, size, image_base):
    position, adjustment, target = 0, 0, None
    for row in rows:
        offset, encoding, text = row[:3]
        if offset != position:
            raise ValueError('instruction extent gap')
        position += len(encoding.split())
        arithmetic = re.fullmatch(r'(add|sub) rcx, (-?0x[0-9a-f]+|-?[0-9]+)', text)
        transfer = re.fullmatch(r'jmp (0x[0-9a-f]+)(?: <[^>]*>)?', text)
        if arithmetic and target is None:
            value = int(arithmetic[2], 0)
            adjustment += value if arithmetic[1] == 'add' else -value
        elif transfer and target is None and position == size:
            target = int(transfer[1], 16)-image_base
        else:
            raise ValueError('outside this-only arithmetic/direct-tailcall semantics')
    if position != size or target is None or adjustment >= 0 or target < 0:
        raise ValueError('incomplete or unsupported secondary adjustment')
    return dict(adjustment=adjustment, callee_rva=target)


def rtti(image, table):
    base = image.pe.image_base
    col = struct.unpack('<Q', image.read(table-8,8))[0]-base
    signature, offset, cd, td, chd, self_rva = struct.unpack('<IIIIII',image.read(col,24))
    if signature != 1 or self_rva != col or cd:
        raise ValueError('inconsistent or construction RTTI locator')
    count, array = struct.unpack('<II', image.read(chd+8,8))
    if not 1 <= count <= 4096:
        raise ValueError('invalid hierarchy count')
    bases=[]
    for index in range(count):
        bcd=struct.unpack('<I', image.read(array+4*index,4))[0]
        btd, contained, mdisp, pdisp, vdisp, attributes=struct.unpack('<IIiiiI',image.read(bcd,24))
        bases.append(dict(type=image._cstr(btd+16),contained=contained,mdisp=mdisp,pdisp=pdisp,vdisp=vdisp))
    return dict(type=image._cstr(td+16),offset=offset,bases=bases)


def reconcile(image, member, decoded):
    primary=rtti(image,member['primary_table'])
    secondary=rtti(image,member['secondary_table'])
    read_slot=lambda table,slot:struct.unpack('<Q',image.read(table+8*slot,8))[0]-image.pe.image_base
    if primary['type']!=member['rtti_type'] or secondary['type']!=primary['type'] or primary['offset']:
        raise ValueError('owner RTTI identity mismatch')
    if read_slot(member['secondary_table'],member['slot'])!=member['rva']:
        raise ValueError('secondary slot does not bind the selected entry')
    if read_slot(member['primary_table'],member['primary_slot'])!=decoded['callee_rva']:
        raise ValueError('decoded tailcall does not bind the primary callee')
    if secondary['offset']!=-decoded['adjustment'] or not any(b['pdisp']==-1 and b['mdisp']==secondary['offset'] for b in secondary['bases'][1:]):
        raise ValueError('this adjustment does not bind a nonvirtual RTTI base')
    expected=member['direct_bases'];actual=[];index=1
    while index<len(primary['bases']):
        b=primary['bases'][index];actual.append(b);index+=b['contained']+1
    if [(b['type'],b['mdisp'],b['pdisp']) for b in actual]!=[(b['type'],b['offset'],-1) for b in expected]:
        raise ValueError('represented direct-base identities or offsets disagree')
    return {'entry-rva':member['rva'],'size':member['size'],'this-offset':secondary['offset'],
            'callee-rva':decoded['callee_rva'],'primary-table-rva':member['primary_table'],
            'secondary-table-rva':member['secondary_table'],'slot':member['slot'],
            'layout-size':member['layout_size']}


def prepare(selection):
    root,out=(Path(selection[k]).resolve() for k in ('root','out'))
    if any('.local' not in p.parts for p in (root,out)):
        raise ValueError('private preparation roots required')
    config=json.loads((root/'.local/verifier/config.json').read_text());image=ImageFacts(config['image'])
    if image.sha256!=json.loads((root/'builds/target.json').read_text())['image_sha256']:
        raise ValueError('image hash mismatch')
    objdump=disasm.find_objdump(config.get('objdump'))
    progress=json.loads((root/'data/progress.json').read_text());existing={f['rva']:f for f in progress['functions']}
    def decode(m):
        return m,reconcile(image,m,extract(disasm.target_rows(objdump,config['image'],m['rva'],m['size']),m['rva'],m['size'],image.pe.image_base))
    with ThreadPoolExecutor(max_workers=6) as pool:
        decoded=list(pool.map(decode,selection['members']))
    tasks=[];params=[]
    for member,row in decoded:
        rva=member['rva']
        if existing.get(rva,{}).get('status')=='matched':
            raise ValueError('selected entry is already accepted')
        emitted=template.emit(rva,member['size'],row['this-offset'],member['layout'],member['layout_size'])
        source=f'reconstruction/bsengine/{emitted["cls"]}.cpp'
        for path,content in ((root/source,emitted['source']),((root/source).with_suffix('.h'),emitted['header'])):
            if path.exists() and path.read_text()!=content:
                raise ValueError('different source already exists')
            path.write_text(content)
        entries={emitted['symbol']:dict(rva=rva,size=member['size']),emitted['callee']:dict(rva=row['callee-rva'],size=None)}
        smap=dict(schema=1,build_id=template.BUILD,symbols=entries,folds=[],_provenance=dict(entries=[dict(name=n,rva=hex(v['rva']),community_name=None,note='Member-local decoded tailcall and RTTI slot binding; compiler ABI spelling is a guessed stand-in.') for n,v in entries.items()]))
        digest=hashlib.sha256(symbol_map.serialize(smap)).hexdigest();map_path=f'reports/{template.BUILD}/unit-symbols/{digest}.json';symbol_map.create(root,map_path,smap)
        taskdir=out/'tasks'/f'p110-{rva:x}';taskdir.mkdir(parents=True,exist_ok=True)
        task=dict(task_schema=1,task_id=taskdir.name,build_id=template.BUILD,compiled=source,recipe=template.RECIPE,symbols=map_path,functions=[dict(rva=rva,size=member['size'],symbol=emitted['symbol'],family_metadata=dict(origin=template.origin(),family_parameters=row,name_source='GUESS(low)'))])
        (taskdir/'task.json').write_text(json.dumps(task,indent=2)+'\n');tasks.append(str(taskdir));params.append(row)
        if rva not in existing:
            progress['functions'].append(dict(id=f'{template.BUILD}-0x{rva:x}',build_id=template.BUILD,rva=rva,size=member['size'],status='mapped',name=f'{emitted["cls"]} secondary destructor adjustor',name_origin='GUESS',name_source='GUESS(low): compiler-emitted override over represented RTTI bases; names do not establish target identity.',owner='awarebayes',evidence=template.EVIDENCE))
    (root/'data/progress.json').write_text(json.dumps(progress,indent=2)+'\n');bind.preflight(tasks,root)
    (out/'all.txt').write_text(''.join(t+'\n' for t in tasks));(out/'rows.json').write_text(json.dumps(params,indent=2)+'\n')
    print(f'prepared {len(tasks)}; independent RTTI/transfer reconciliation and whole-list preflight passed')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--selection',type=Path,required=True)
    prepare(json.loads(parser.parse_args().selection.read_text()))
