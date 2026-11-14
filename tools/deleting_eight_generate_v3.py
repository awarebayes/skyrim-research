"""Extract complete leaf shapes independently, then emit bounded destructor units.

Private selection JSON supplies root, out and members (rva, size).
Reference fields and allocation sizes are never transferred between members.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/verifier'))
import bind
import disasm
import symbol_map
import deleting_eight_template_v3 as template


def extract(rows, rva, image_base):
    offsets = [0, 2, 6, 13, 16, 19, 22, 24, 29, 34, 37, 41, 42]
    if [r[0] for r in rows] != offsets or sum(len(r[1].split()) for r in rows) != 43:
        raise ValueError('unsupported full instruction extent')
    instructions = [r[2] for r in rows]
    fixed = {0:'push rbx', 1:'sub rsp, 0x20', 3:'mov rbx, rcx',
             4:'mov qword ptr [rcx], rax', 5:'test dl, 0x1',
             9:'mov rax, rbx', 10:'add rsp, 0x20', 11:'pop rbx', 12:'ret'}
    if any(instructions[i] != text for i, text in fixed.items()):
        raise ValueError('unsupported deleting leaf shape')
    table = re.fullmatch(r'lea rax, \[rip[^\]]*\] # (0x[0-9a-f]+)(?: <[^>]*>)?', instructions[2])
    jump = re.fullmatch(r'je (0x[0-9a-f]+)(?: <[^>]*>)?', instructions[6])
    size = re.fullmatch(r'mov edx, (0x[0-9a-f]+)', instructions[7])
    call = re.fullmatch(r'call (0x[0-9a-f]+)(?: <[^>]*>)?', instructions[8])
    if not all((table,jump,size,call)) or int(jump[1],16) != image_base+rva+34:
        raise ValueError('unsupported deleting leaf references or branch')
    values = dict(zip(('table-rva','deallocator-rva'), (int(m[1],16)-image_base for m in (table,call))))
    if any(v < 0 for v in values.values()):
        raise ValueError('reference outside image')
    values.update({'entry-rva':rva, 'size':43, 'object-size':int(size[1],16)})
    template.emit(rva, values['object-size'])
    return values


def prepare(selection):
    root, out = (Path(selection[k]).resolve() for k in ('root','out'))
    if any('.local' not in p.parts for p in (root,out)):
        raise ValueError('private outputs required')
    config=json.loads((root/'.local/verifier/config.json').read_text())
    image=Path(config['image'])
    if hashlib.sha256(image.read_bytes()).hexdigest()!=json.loads((root/'builds/target.json').read_text())['image_sha256']:
        raise ValueError('image hash mismatch')
    objdump=disasm.find_objdump(config.get('objdump')); base=disasm.image_base(image)
    progress=json.loads((root/'data/progress.json').read_text()); existing={f['rva']:f for f in progress['functions']}
    def decode(m):
        if m['size']!=43 or existing.get(m['rva'],{}).get('status')=='matched':
            return m, None, 'accepted or conflicting extent'
        try:
            return m, extract(disasm.target_rows(objdump,str(image),m['rva'],43),m['rva'],base), None
        except ValueError as e:
            return m, None, str(e)
    with ThreadPoolExecutor(max_workers=6) as pool:
        decoded=list(pool.map(decode,selection['members']))
    tasks=[];excluded=[];rows=[]
    for m,params,reason in decoded:
        if reason:
            excluded.append(dict(rva=m['rva'],reason=reason));continue
        rva=m['rva'];e=template.emit(rva,params['object-size'])
        source=f'reconstruction/leaves/{e["cls"]}.cpp'
        for path,content in ((root/source,e['source']),((root/source).with_suffix('.h'),e['header'])):
            path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists() and path.read_text()!=content:raise ValueError('different existing source')
            path.write_text(content)
        entries={e['symbol']:dict(rva=rva,size=43),e['table']:dict(rva=params['table-rva'],size=None),e['deallocator']:dict(rva=params['deallocator-rva'],size=None)}
        smap=dict(schema=1,build_id=template.BUILD,symbols=entries,folds=[],_provenance=dict(entries=[dict(name=n,rva=hex(v['rva']),community_name=None,note='Independent member extraction; guessed ABI stand-in identity.') for n,v in entries.items()]))
        digest=hashlib.sha256(symbol_map.serialize(smap)).hexdigest();map_path=f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(root,map_path,smap)
        taskdir=out/'tasks'/f'p104-{rva:x}';taskdir.mkdir(parents=True,exist_ok=True)
        task=dict(task_schema=1,task_id=taskdir.name,build_id=template.BUILD,compiled=source,recipe=template.RECIPE,symbols=map_path,functions=[dict(rva=rva,size=43,symbol=e['symbol'],family_metadata=dict(origin=template.origin(),family_parameters=params,name_source='GUESS(low)'))])
        (taskdir/'task.json').write_text(json.dumps(task,indent=2)+'\n');tasks.append(str(taskdir));rows.append(params)
        if rva not in existing:
            progress['functions'].append(dict(id=f'{template.BUILD}-0x{rva:x}',build_id=template.BUILD,rva=rva,size=43,status='mapped',name=f'{e["cls"]}::~{e["cls"]}',name_origin='GUESS',name_source='GUESS(low): scalar deleting destructor ABI stand-in; original owner and layout unknown.',owner='awarebayes',evidence=template.EVIDENCE))
    (root/'data/progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    bind.preflight(tasks,root)
    (out/'all.txt').write_text(''.join(t+'\n' for t in tasks))
    (out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'excluded.json').write_text(json.dumps(excluded,indent=2)+'\n')
    print(f'prepared {len(tasks)}; excluded {len(excluded)}; whole-list binding preflight passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--selection',type=Path,required=True)
    prepare(json.loads(p.parse_args().selection.read_text()))
