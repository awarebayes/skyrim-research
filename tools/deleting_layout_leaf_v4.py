"""Represented-layout scalar deleting destructors, with independent per-member RTTI bindings."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools/verifier'), str(ROOT/'tools/ghidra')]
from analysis import stamp
import bind
import disasm
import export_pack
import symbol_map
import deleting_layout_bindings_v1 as independent_bindings

BUILD = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
CATALOG = 'tools/deleting_layout_catalog_v4.json'
CATALOG_SHA256 = '0d98e3426c037d9b121294fb2736476b34a5ed44f14420ed35b36e4da4cd6b2f'


BINDING_AUDIT_SHA256 = 'dde9d76f7f575b87a00294f5bf106ea15ee410cff6852e99771f9cc62a818eee'

def origin():
    return dict(family='scalar-deleting-leaf', version='4',
                template_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def extract(rows, rva, image_base):
    offsets = [0, 2, 6, 13, 16, 19, 22, 24, 29, 34, 37, 41, 42]
    if [r[0] for r in rows] != offsets or sum(len(r[1].split()) for r in rows) != 43:
        raise ValueError('unsupported full instruction extent')
    ins = [r[2] for r in rows]
    fixed = {0:'push rbx', 1:'sub rsp, 0x20', 3:'mov rbx, rcx',
             4:'mov qword ptr [rcx], rax', 5:'test dl, 0x1',
             9:'mov rax, rbx', 10:'add rsp, 0x20', 11:'pop rbx', 12:'ret'}
    if any(ins[i] != value for i,value in fixed.items()):
        raise ValueError('unsupported deleting leaf shape')
    table = re.fullmatch(r'lea rax, \[rip[^\]]*\] # (0x[0-9a-f]+)(?: <[^>]*>)?',ins[2])
    jump = re.fullmatch(r'je (0x[0-9a-f]+)(?: <[^>]*>)?',ins[6])
    size = re.fullmatch(r'mov edx, (0x[0-9a-f]+)',ins[7])
    call = re.fullmatch(r'call (0x[0-9a-f]+)(?: <[^>]*>)?',ins[8])
    if not all((table,jump,size,call)) or int(jump[1],16) != image_base+rva+34:
        raise ValueError('unsupported references or branch')
    return {'entry-rva':rva,'size':43,'object-size':int(size[1],16),
            'table-rva':int(table[1],16)-image_base,'deallocator-rva':int(call[1],16)-image_base}


def table_identity(image, rva):
    base=image.pe.image_base
    col=struct.unpack('<Q',image.read(rva-8,8))[0]-base
    td=struct.unpack('<I',image.read(col+12,4))[0]
    offset=struct.unpack('<I',image.read(col+4,4))[0]
    return image._cstr(td+16),offset


def source(root, header, members):
    text=(root/header).read_text()
    notice=''
    if '// MIT License' in text:
        notice=text[text.index('// MIT License'):text.index('// SOFTWARE.')+len('// SOFTWARE.')]+'\n'
    declarations='\n'.join(s for s in text.splitlines() if s.startswith('// Declaration source:') or s.startswith('// Declarations derived from') or s.startswith('// Interface declarations adapt'))
    definitions=list(dict.fromkeys(d for m in members for d in m['definitions']))
    types=list(dict.fromkeys(m['type'] for m in members))
    labels=', '.join(dict.fromkeys(re.findall(r'\b([A-Za-z_]\w*)::~', '\n'.join(definitions))))
    prefix=f'''// Build: {BUILD}; RVA 0x{members[0]["rva"]:x}; 43 bytes
// Evidence: findings/ghidra-import.md
// Recipe: {RECIPE}
// Source exposure: mixed (represented community declarations and local binary analysis).
// Drafted by tools/deleting_layout_leaf_v4.py (GPT-6.1 Sol).
// Labels: v2
// {labels}: GUESS(medium) STANDIN; represented layout type names.
// object: GUESS(low)
// Empty destructor bodies are inferred stand-ins for the compared leaf code only.
// Fields and inheritance come from the included represented layout, never an allocation-size array.
// No original field ownership or omitted methods are claimed; only scalar deleting code is compared.
// Shared structural template specializations do not recover original template arguments.
// The static objects request normal compiler emission; initialization and other methods are unassessed.
// Origin: {json.dumps(origin(),sort_keys=True)}
'''+declarations+'\n'+notice
    assertions='\n'.join(f'static_assert(sizeof({m["type"]}) == {m["object_size"]}, "independently observed allocation size");' for m in members)
    return prefix+'void operator delete(void*, unsigned __int64) noexcept;\n'+f'#include "{Path(header).name}"\nnamespace ResearchLayouts {{\n'+'\n'.join(definitions)+'\n}\n'+assertions+'\n'+'\n'.join(f'static {typ} object;' if len(types)==1 else f'static {typ} object{i};' for i,typ in enumerate(types))+'\n'


def prepare(selection):
    root=Path(selection['root']).resolve();out=Path(selection['out']).resolve()
    if any('.local' not in p.parts for p in (root,out)):
        raise ValueError('private generation root and outputs required')
    raw=(root/CATALOG).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CATALOG_SHA256:raise ValueError('catalog differs from pinned template')
    catalog=json.loads(raw);cfg=json.loads((root/'.local/verifier/config.json').read_text())
    image=export_pack.ImageFacts(cfg['image']);target=json.loads((root/'builds/target.json').read_text())
    if image.sha256!=catalog['image_sha256'] or image.sha256!=target['image_sha256']:raise ValueError('image hash mismatch')
    if hashlib.sha256((root/'tools/deleting_layout_bindings_v1.py').read_bytes()).hexdigest()!=BINDING_AUDIT_SHA256:raise ValueError('binding auditor changed')
    witnesses={row['rva']:row for row in independent_bindings.audit(independent_bindings.Image(cfg['image']),catalog)}
    for rel,digest in catalog['headers'].items():
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest:raise ValueError('represented header changed: '+rel)
    progress=json.loads((root/'data/progress.json').read_text());by={f['rva']:f for f in progress['functions']}
    objdump=disasm.find_objdump(cfg.get('objdump'));entries=catalog['members'];tasks=[];excluded=[]
    def decode(pair):
        index,m=pair
        try:
            if by[m['rva']]['status']=='matched':raise ValueError('already accepted')
            owner,off=table_identity(image,m['owner_table'])
            if (owner,off)!=(m['owner_rtti'],0) or struct.unpack('<Q',image.read(m['owner_table']+8*m['owner_slot'],8))[0]!=image.pe.image_base+m['rva']:
                raise ValueError('primary RTTI owner/slot binding changed')
            params=extract(disasm.target_rows(objdump,cfg['image'],m['rva'],43),m['rva'],image.pe.image_base)
            stored,off=table_identity(image,params['table-rva'])
            if stamp.parse_type_descriptor(stored).qualified!=m['stored_rtti'] or off or params['table-rva']!=m['stored_table'] or params['object-size']!=m['object_size']:
                raise ValueError('represented class, allocation or stored table binding differs')
            witness=witnesses[m['rva']]
            if (params['table-rva'],params['object-size'],params['deallocator-rva']) != (witness['stored_table'],witness['object_size'],witness['deallocator_rva']):raise ValueError('independent operand audit disagrees')
            params['layout-index']=index
            return m,params,None
        except (ValueError,KeyError) as e:return m,None,str(e)
    with ThreadPoolExecutor(max_workers=6) as pool:decoded=list(pool.map(decode,enumerate(entries)))
    # One class/header pair may serve independently bound duplicate structural instantiations.
    grouped={}
    for m,params,reason in decoded:
        if reason:excluded.append(dict(rva=m['rva'],reason=reason));continue
        grouped.setdefault(m['header'],[]).append(m)
    for header,members in grouped.items():
        cpp=(root/header).with_suffix('.cpp')
        if cpp.exists() and cpp.read_text()!=source(root,header,members):raise ValueError('different existing source: '+str(cpp.relative_to(root)))
        cpp.write_text(source(root,header,members))
    for m,params,reason in decoded:
        if reason:continue
        rva=m['rva'];compiled=str(Path(m['header']).with_suffix('.cpp'));symbols={m['symbol']:dict(rva=rva,size=43),'??3@YAXPEAX_K@Z':dict(rva=params['deallocator-rva'],size=None)}
        symbols.update({t['symbol']:dict(rva=t['rva'],size=None) for t in m['tables']})
        smap=dict(schema=1,build_id=BUILD,symbols=symbols,folds=[],_provenance=dict(entries=[dict(name=n,rva=hex(v['rva']),community_name=None,note='Independent leaf extraction and primary RTTI/represented-base identity; source aliases are stand-ins.') for n,v in symbols.items()]))
        digest=hashlib.sha256(symbol_map.serialize(smap)).hexdigest();map_path=f'reports/{BUILD}/unit-symbols/{digest}.json';symbol_map.create(root,map_path,smap)
        taskdir=out/'tasks'/f'p104b-{rva:x}';taskdir.mkdir(parents=True,exist_ok=True)
        task=dict(task_schema=1,task_id=taskdir.name,build_id=BUILD,compiled=compiled,recipe=RECIPE,symbols=map_path,functions=[dict(rva=rva,size=43,symbol=m['symbol'],family_metadata=dict(origin=origin(),family_parameters=params,name_source='GUESS(medium)'))])
        (taskdir/'task.json').write_text(json.dumps(task,indent=2)+'\n');tasks.append(str(taskdir))
    bind.preflight(tasks,root)
    out.mkdir(parents=True,exist_ok=True);(out/'all.txt').write_text(''.join(t+'\n' for t in tasks));(out/'excluded.json').write_text(json.dumps(excluded,indent=2)+'\n')
    print(f'prepared {len(tasks)} represented-layout tasks; excluded {len(excluded)}; binding preflight passed',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--selection',type=Path,required=True)
    prepare(json.loads(parser.parse_args().selection.read_text()))
