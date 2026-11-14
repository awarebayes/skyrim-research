"""Extract complete wrapper shapes independently, then emit bounded destructor units.

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
import deleting_wrapper_template_v1 as template


def extract(rows, rva, image_base):
    offsets = [0, 5, 6, 10, 12, 15, 20, 23, 25, 30, 33, 38, 43, 46, 50, 51]
    if [r[0] for r in rows] != offsets or sum(len(r[1].split()) for r in rows) != 52:
        raise ValueError('unsupported full instruction extent')
    instructions = [r[2] for r in rows]
    fixed = {0:'mov qword ptr [rsp + 0x8], rbx', 1:'push rdi', 2:'sub rsp, 0x20',
             3:'mov ebx, edx', 4:'mov rdi, rcx', 6:'test bl, 0x1', 9:'mov rcx, rdi',
             11:'mov rbx, qword ptr [rsp + 0x30]', 12:'mov rax, rdi',
             13:'add rsp, 0x20', 14:'pop rdi', 15:'ret'}
    if any(instructions[i] != text for i, text in fixed.items()):
        raise ValueError('unsupported deleting wrapper shape')
    call_pattern = r'call (0x[0-9a-f]+)(?: <[^>]*>)?'
    destructor = re.fullmatch(call_pattern, instructions[5])
    deallocator = re.fullmatch(call_pattern, instructions[10])
    jump = re.fullmatch(r'je (0x[0-9a-f]+)(?: <[^>]*>)?', instructions[7])
    size = re.fullmatch(r'mov edx, (0x[0-9a-f]+)', instructions[8])
    if not all((destructor, deallocator, jump, size)) or int(jump[1], 16) != image_base+rva+38:
        raise ValueError('unsupported deleting wrapper references or branch')
    values = dict(zip(('destructor-rva','deallocator-rva'),
                     (int(m[1],16)-image_base for m in (destructor,deallocator))))
    if any(v < 0 for v in values.values()):
        raise ValueError('reference outside image')
    values.update({'entry-rva':rva, 'size':52, 'object-size':int(size[1],16)})
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
        if m['size']!=52 or existing.get(m['rva'],{}).get('status')=='matched':
            return m, None, 'accepted or conflicting extent'
        try:
            return m, extract(disasm.target_rows(objdump,str(image),m['rva'],52),m['rva'],base), None
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
        entries={e['symbol']:dict(rva=rva,size=52),e['destructor']:dict(rva=params['destructor-rva'],size=None),e['deallocator']:dict(rva=params['deallocator-rva'],size=None)}
        smap=dict(schema=1,build_id=template.BUILD,symbols=entries,folds=[],_provenance=dict(entries=[dict(name=n,rva=hex(v['rva']),community_name=None,note='Independent member extraction; guessed ABI stand-in identity.') for n,v in entries.items()]))
        digest=hashlib.sha256(symbol_map.serialize(smap)).hexdigest();map_path=f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(root,map_path,smap)
        taskdir=out/'tasks'/f'p106-{rva:x}';taskdir.mkdir(parents=True,exist_ok=True)
        task=dict(task_schema=1,task_id=taskdir.name,build_id=template.BUILD,compiled=source,recipe=template.RECIPE,symbols=map_path,functions=[dict(rva=rva,size=52,symbol=e['symbol'],family_metadata=dict(origin=template.origin(),family_parameters=params,name_source='GUESS(low)'))])
        (taskdir/'task.json').write_text(json.dumps(task,indent=2)+'\n');tasks.append(str(taskdir));rows.append(params)
        if rva not in existing:
            progress['functions'].append(dict(id=f'{template.BUILD}-0x{rva:x}',build_id=template.BUILD,rva=rva,size=52,status='mapped',name=f'{e["cls"]}::~{e["cls"]}',name_origin='GUESS',name_source='GUESS(low): scalar deleting destructor ABI stand-in; original owner and additional slots unknown.',owner='awarebayes',evidence=template.EVIDENCE))
    (root/'data/progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    bind.preflight(tasks,root)
    (out/'all.txt').write_text(''.join(t+'\n' for t in tasks))
    (out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'excluded.json').write_text(json.dumps(excluded,indent=2)+'\n')
    print(f'prepared {len(tasks)}; excluded {len(excluded)}; whole-list binding preflight passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--selection',type=Path,required=True)
    prepare(json.loads(p.parse_args().selection.read_text()))
