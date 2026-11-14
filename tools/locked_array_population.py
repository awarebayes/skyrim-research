"""Extract and regenerate the frozen locked-array mutation census.

Private input: a census JSON with groups F063/F068; source image and runner paths
come only from local configuration. Every member is independently disassembled,
including its own EH cleanup. Full normalized shapes must agree with the pilot.
No acceptance or review evidence is manufactured by generation.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools/verifier'),str(ROOT/'tools/ghidra')]
import disasm
import export_pack as ep
import bind
import symbol_map
import locked_array_template_v1 as template
SHAPES={'F063':'9c3aae0f5a123db5cc9626872125fe9c17e630daf1eb3f40d21d469fa59cc374','F068':'24c2b10e5327cf016af716bcd20bb7ed1d7202f863270007fa9b3bd806d89130'}
def extract(pair, cfg, img):
 base=img.pe.image_base
 family,row=pair;rva=int(row['rva'],16);size=int(row['size']);rows=disasm.target_rows(cfg['objdump'],cfg['image'],rva,size)
 assert rows and rows[-1][0]+len(rows[-1][1].split())==size,(family,hex(rva),'extent')
 calls=[int(m[1],16)-base for x in rows if (m:=re.match(r'call (0x[0-9a-f]+)',x[2]))]
 assert len(calls)==(4 if family=='F068' else 3),(family,hex(rva),'call count')
 iats=[int(m[1],16)-base for x in rows if x[2].startswith('call qword ptr [rip') and (m:=re.search(r'# (0x[0-9a-f]+)',x[2]))]
 assert len(iats)==1,(family,hex(rva),'thread import')
 eh=ep.eh_facts(img,{'by_rva':{}},[],rva,img.pdata_intersecting(rva,rva+size))
 assert not eh['reasons'] and len(eh['funclets'])==1 and len(eh['handlers'])==1
 frva=next(iter(eh['funclets']));frows=disasm.target_rows(cfg['objdump'],cfg['image'],frva,12)
 assert len(frows)==2 and frows[0][2].startswith('lea rcx, [rdx + ')
 cleanup=int(re.fullmatch(r'jmp (0x[0-9a-f]+).*',frows[1][2])[1],16)-base
 frame_offset=int(re.fullmatch(r'lea rcx, \[rdx \+ (0x[0-9a-f]+)\]',frows[0][2])[1],16)
 def normal(x):
  ins=x[2]
  if ins.startswith('call 0x'):return 'call DIRECT'
  if ins.startswith('call qword ptr [rip'):return 'call IAT'
  m=re.match(r'(j[a-z]+) (0x[0-9a-f]+)',ins)
  if m:return m[1]+' OFFSET '+str(int(m[2],16)-base-rva)
  return ins
 normalized='\n'.join(normal(x) for x in rows)
 refs=dict(guard_constructor=calls[0],append=calls[1],move=calls[-1],thread_id_iat=iats[0],guard_destructor=cleanup,handler=next(iter(eh['handlers'].values())))
 if family=='F068':refs['erase']=calls[2]
 return dict(family=family,rva=rva,size=size,references=refs,funclet_rva=frva,guard_frame_offset=frame_offset,normalized_shape_sha256=hashlib.sha256(normalized.encode()).hexdigest())


def generate(census, out):
    out=out.resolve()
    if not out.is_relative_to(ROOT/'.local'):
        raise ValueError('output must be private')
    cfg=json.loads((ROOT/'.local/verifier/config.json').read_text())
    target=json.loads((ROOT/'builds/target.json').read_text())
    img=ep.ImageFacts(cfg['image'])
    if img.sha256!=target['image_sha256'] or target['build_id']!=template.BUILD:
        raise ValueError('target differs from pin')
    global_map=json.loads((ROOT/f'reports/{template.BUILD}/symbol-map.json').read_text())
    img.handler_names={v['rva']:k for k,v in global_map['symbols'].items() if k in ep.EH_HANDLERS}
    pairs=[]
    for kind,count in [('F063',95),('F068',86)]:
        rows=census[kind]['rows']
        if len(rows)!=count or len({r['rva'] for r in rows})!=count:
            raise ValueError('incomplete or duplicate census variant')
        pairs += [(kind,row) for row in rows]
    with ThreadPoolExecutor(max_workers=4) as ex:
        extracted=list(ex.map(lambda pair:extract(pair,cfg,img),pairs))
    progress=json.loads((ROOT/'data/progress.json').read_text())
    existing={f['rva']:f for f in progress['functions']}
    tasks={kind:[] for kind in SHAPES}
    for row in extracted:
        kind,rva,size=row['family'],row['rva'],row['size']
        if row['normalized_shape_sha256']!=SHAPES[kind] or row['guard_frame_offset']!=0x60:
            raise ValueError('member outside validated caller/EH shape')
        if rva in existing and (existing[rva]['status']=='matched' or existing[rva]['size']!=size):
            raise ValueError('overlaps accepted member or another extent')
        owner,array,method,ah,h,cpp=template.emit(kind,rva,size)
        namespace=f'p117_{rva:x}'
        folder='reconstruction/bsengine/'
        for name,content in [(array+'.h',ah),(owner+'.h',h),(owner+'.cpp',cpp)]:
            path=ROOT/folder/name
            if path.exists() and (path.is_symlink() or path.read_text()!=content):
                raise ValueError('refusing source overwrite')
            path.write_text(content)
        refs=row['references']
        names={f'?{method}@{owner}@{namespace}@@QEAAXPEAUSink@2@@Z':dict(rva=rva,size=size),
               f'??0Guard@{namespace}@@QEAA@AEAULock@1@@Z':dict(rva=refs['guard_constructor'],size=None),
               f'??1Guard@{namespace}@@QEAA@XZ':dict(rva=refs['guard_destructor'],size=None),
               f'?Push@?${array}@PEAUSink@{namespace}@@@{namespace}@@QEAAXAEBQEAUSink@2@@Z':dict(rva=refs['append'],size=None),
               f'?Move@ArrayBase@{namespace}@@QEAAXPEAXIIII@Z':dict(rva=refs['move'],size=None),
               '__imp_GetCurrentThreadId':dict(rva=refs['thread_id_iat'],size=None),
               '__CxxFrameHandler3':dict(rva=refs['handler'],size=None)}
        if kind=='F068':
            names[f'?EraseExternal@?${array}@PEAUSink@{namespace}@@@{namespace}@@QEAAXII@Z']=dict(rva=refs['erase'],size=None)
        smap=dict(schema=1,build_id=template.BUILD,symbols=names,folds=[],_provenance=dict(note='Per-member caller and EH extraction; all ownership and helper signatures are guesses.',entries=[dict(name=n,rva=hex(v['rva']),community_name=None,note='Independently extracted from this parent or its EH cleanup.') for n,v in names.items()]))
        digest=hashlib.sha256(symbol_map.serialize(smap)).hexdigest()
        map_path=f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(ROOT,map_path,smap)
        params={'rva':rva,'size':size,'variant':kind,'shape':kind.lower()+'-caller-v1','guard-frame':row['guard_frame_offset'],**{k.replace('_','-'):v for k,v in refs.items()}}
        symbol=next(iter(names))
        metadata=dict(origin=template.origin(kind),family_parameters=params,name_source='GUESS(low)')
        task=dict(task_schema=1,task_id=f'p117-{kind.lower()}-{rva:x}',build_id=template.BUILD,compiled=folder+owner+'.cpp',recipe=template.RECIPE,symbols=map_path,functions=[dict(rva=rva,size=size,symbol=symbol,family_metadata=metadata)])
        directory=out/'tasks'/task['task_id'];directory.mkdir(parents=True,exist_ok=True)
        (directory/'task.json').write_text(json.dumps(task,indent=2)+'\n')
        tasks[kind].append(str(directory))
        entry=dict(id=f'{template.BUILD}-0x{rva:x}',build_id=template.BUILD,rva=rva,size=size,status='mapped',name=f'{namespace}::{owner}::{method}',name_origin='GUESS',name_source='GUESS(low): inferred mutation and ABI stand-in; specialization unknown.',owner='awarebayes',evidence=template.EVIDENCE)
        if rva in existing: existing[rva].update(entry)
        else: progress['functions'].append(entry)
    for kind,paths in tasks.items():
        (out/(kind+'.txt')).write_text(''.join(p+'\n' for p in paths))
    (out/'all.txt').write_text(''.join(p+'\n' for paths in tasks.values() for p in paths))
    (out/'population.json').write_text(json.dumps(extracted,indent=2)+'\n')
    (ROOT/'data/progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    bind.preflight([p for paths in tasks.values() for p in paths],ROOT)
    print('generated and bound 95 F063 and 86 F068 members',flush=True)


def records_to_spec(out):
    """Link only authentic reproduced records and freeze exact correlated rows."""
    import accept_function as af
    import family_review as fr
    progress,target=af.load(ROOT)
    by_rva={fn['rva']:fn for fn in progress['functions']}
    source=lambda name:dict(path=name,sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
    for kind in SHAPES:
        rows=[]
        binding=None
        members=[]
        for directory in (out/(kind+'.txt')).read_text().splitlines():
            task=json.loads((Path(directory)/'task.json').read_text())
            member=task['functions'][0]
            fn=dict(by_rva[member['rva']])
            fn['report']=f'reports/{template.BUILD}/0x{fn["rva"]:x}.json'
            record=af.validate_match(fn,target,ROOT)
            metadata=member['family_metadata']
            if any(record.get(key)!=value for key,value in metadata.items()):
                raise ValueError('confirmed origin or parameters differ from generation')
            current=fr.binding(fn,record)
            if binding is not None and binding!=current:
                raise ValueError('population bindings differ')
            binding=current
            rows.append(record['family_parameters'])
            members.append(fn)
        expected=95 if kind=='F063' else 86
        if len(members)!=expected or len({fn['id'] for fn in members})!=expected:
            raise ValueError('incomplete reproduced variant')
        spec=dict(origin=template.origin(kind),binding=binding,
                  template_source=source('tools/locked_array_template_v1.py'),
                  parameter_source=source('tools/locked_array_population.py'),
                  parameter_ranges=fr.exact_ranges(rows),
                  first_members=[fn['id'] for fn in sorted(members,key=lambda fn:fn['rva'])[:20]])
        for fn in members:
            by_rva[fn['rva']]['report']=fn['report']
        fr.write(ROOT,out/(kind+'-spec.json'),spec)
    (ROOT/'data/progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    print('validated both reproduced populations; exact-row specs ready',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--census',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--records-to-spec',action='store_true')
    args=parser.parse_args()
    if args.records_to_spec:
        records_to_spec(args.out.resolve())
    elif args.census:
        generate(json.loads(args.census.read_text()),args.out)
    else:
        parser.error('--census is required for generation')
