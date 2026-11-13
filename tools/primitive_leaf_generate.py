"""Extract and emit one explicitly selected private primitive-leaf population.

Selection JSON: root (private checkout), out (private output), family, members.
Each member carries rva, size and kind from the frozen census. A local image
hash and each complete decoded shape are checked before any inventory update.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/verifier'))
import bind
import compare_internal as internal
from pecoff import PeImage, CoffObject
import runners
import unit_build
import symbol_map
from source_digest import include_closure, tu_digest
import primitive_leaf_template_v1 as template


def extract(code, family):
    """Only complete bounded source shapes, with no padding or hidden targets."""
    if family == 'empty' and code == bytes((194, 0, 0)):
        return None
    if family == 'constant' and len(code) == 6 and code[0] == 184 and code[-1] == 195:
        return struct.unpack_from('<I', code, 1)[0]
    raise ValueError('unsupported-complete-primitive-shape')


def write_new(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text() != text:
            raise ValueError('refusing different existing source')
    else:
        path.write_text(text)


def family_parameters(emitted):
    """Translate the emitter's Python field names to the public family grammar."""
    row = emitted['parameters']
    result = {'entry-rva': row['entry_rva'], 'size': row['size'], 'kind': row['kind']}
    if 'value' in row:
        result['value'] = row['value']
    return result


def prepare(selection):
    root, out = (Path(selection[k]).resolve() for k in ('root', 'out'))
    if any('.local' not in p.parts for p in (root, out)):
        raise ValueError('source checkout and outputs must remain private')
    members, family = selection['members'], selection['family']
    if len({m['rva'] for m in members}) != len(members):
        raise ValueError('duplicate population member')
    config = json.loads((root/'.local/verifier/config.json').read_text())
    data = Path(config['image']).read_bytes()
    if hashlib.sha256(data).hexdigest() != json.loads((root/'builds/target.json').read_text())['image_sha256']:
        raise ValueError('pinned image mismatch')
    image = PeImage(data)
    progress = json.loads((root/'data/progress.json').read_text())
    existing = {f['rva']:f for f in progress['functions']}
    # Decode the complete population before writing any source or inventory.
    extracted = [(m, extract(image.read(m['rva'],m['size'],'primitive census member')[1],family)) for m in members]
    for m, _ in extracted:
        if m['rva'] in existing and (existing[m['rva']]['status']=='matched' or existing[m['rva']]['size']!=m['size']):
            raise ValueError('accepted or conflicting inventory member')
    out.mkdir(parents=True,exist_ok=True)
    host = next(h for h in runners.load()['hosts'].values() if h['backend']=='local' and h['loader']=='wine')
    flags = json.loads((root/template.RECIPE).read_text())['flags']
    tasks, rows = [], []
    for m, value in extracted:
        emitted = template.emit(m['rva'],m['size'],family,m['kind'],value)
        source = f'reconstruction/{emitted["area"]}/{emitted["cls"]}.cpp'
        write_new(root/source,emitted['source'])
        write_new((root/source).with_suffix('.h'),emitted['header'])
        taskdir = out/'tasks'/f'p93b-{family}-{m["rva"]:x}'
        taskdir.mkdir(parents=True,exist_ok=True)
        symbol = emitted['symbol']
        entry = dict(rva=m['rva'],size=m['size'],symbol=symbol)
        if m['kind']=='teardown':
            objpath=taskdir/'probe.obj'
            with runners.slot(host['host_id'],host['max_parallel']):
                p=subprocess.run([str(Path(host['msvc'])/'bin/x64/cl'),*flags,'/Fo'+str(objpath),str(root/source)],
                                 env=unit_build.clean_env(runners.LocalTransport(host).env()),capture_output=True,text=True,timeout=300)
            if p.returncode:
                (taskdir/'probe.log').write_text(p.stdout+p.stderr)
                raise ValueError('teardown identity probe refused')
            obj=CoffObject(objpath.read_bytes());sym=next(s for s in obj.symbols.values() if s.name==symbol)
            entry['internal_selector']=internal.selector(obj,sym)
            context=dict(source_revision=tu_digest(root,include_closure(root,source)),source_path=source)
            key=internal.symbol_key(obj,sym,context)
        else:
            key=symbol
        smap=dict(schema=1,build_id=template.BUILD,symbols={key:dict(rva=m['rva'],size=m['size'])},folds=[],
                  _provenance=dict(entries=[dict(name=key,rva=hex(m['rva']),community_name=None,
                                                note='Explicit pinned-image leaf entry; reconstruction identity is a guess.')]))
        digest=hashlib.sha256(symbol_map.serialize(smap)).hexdigest()
        map_path=f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(root,map_path,smap)
        parameters=family_parameters(emitted)
        entry['family_metadata']=dict(origin=emitted['origin'],family_parameters=parameters,name_source='GUESS(low)')
        task=dict(task_schema=2 if m['kind']=='teardown' else 1,task_id=taskdir.name,build_id=template.BUILD,
                  compiled=source,recipe=template.RECIPE,symbols=map_path,functions=[entry])
        (taskdir/'task.json').write_text(json.dumps(task,indent=2)+'\n');tasks.append(str(taskdir));rows.append(parameters)
        if m['rva'] not in existing:
            progress['functions'].append(dict(id=f'{template.BUILD}-0x{m["rva"]:x}',build_id=template.BUILD,
                rva=m['rva'],size=m['size'],status='mapped',name=f'{emitted["cls"]}::{emitted["method"]}',
                name_origin='GUESS',name_source='GUESS(low): trivial leaf stand-in; original signature and owner unknown.',
                owner='awarebayes',evidence=template.EVIDENCE))
    (root/'data/progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    bind.preflight(tasks,root)
    (out/'all.txt').write_text(''.join(t+'\n' for t in tasks))
    (out/'parameter-rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(f'prepared {len(tasks)} {family} entries, zero exclusions; whole-list bind preflight passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--selection',type=Path,required=True)
    prepare(json.loads(p.parse_args().selection.read_text()))
