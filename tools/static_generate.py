"""Prepare static initializer candidates from a private census and pinned image.

All results are candidates: verifier confirmation and review are required. The census
and verifier settings are local inputs; source and maps stay uncommitted until review.
"""
import argparse
import csv
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
import compare_internal as internal
import static_template_v1 as template
import symbol_map
from pecoff import CoffObject, PeImage
from source_digest import include_closure, tu_digest


def extract(rows, image_base):
    """Require the complete reference shape; never fill absent bindings from another member."""
    direct = [int(m[1], 16) - image_base for row in rows
              if (m := re.match(r'(?:call|jmp) (0x[0-9a-f]+)', row[2]))]
    lea = [int(m[1], 16) - image_base for row in rows if row[2].startswith('lea ')
           and (m := re.search(r'# (0x[0-9a-f]+)', row[2]))]
    if len(direct) != 2 or len(lea) != 3 or any(x < 0 for x in direct + lea):
        raise ValueError('unsupported-reference-shape')
    return dict(zip(('descriptor-rva', 'object-rva', 'teardown-rva', 'construct-rva', 'atexit-rva'),
                    (lea[0], lea[1], lea[2], direct[0], direct[1])))


def prepare(census, out):
    out = Path(out).resolve()
    if '.local' not in out.parts:
        raise ValueError('output must be under .local')
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'all.txt').exists():
        raise ValueError('output already prepared')
    with Path(census).open(newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    seed = next(row for row in rows if int(row['rva'], 16) == 0x7bd0)
    selected = sorted((row for row in rows if row['masked'] == seed['masked']),
                      key=lambda row: int(row['rva'], 16))
    ids = [int(row['rva'], 16) for row in selected]
    if len(ids) != len(set(ids)) or len({r & ~15 for r in ids}) != len(ids):
        raise ValueError('duplicate member or static unit interval')
    progress_path = ROOT / 'data/progress.json'
    progress = json.loads(progress_path.read_text())
    spans = [(int(row['rva'], 16), int(row['rva'], 16) + int(row['size'])) for row in selected]
    existing = [(entry['rva'], entry['rva'] + entry['size']) for entry in progress['functions']]
    if any(a < old_end and old_start < b for a, b in spans for old_start, old_end in existing):
        raise ValueError('candidate overlaps inventory')
    if any(end > next_start for (_, end), (next_start, _) in zip(spans, spans[1:])):
        raise ValueError('candidate ranges overlap')
    config = json.loads((ROOT / '.local/verifier/config.json').read_text())
    image_path = Path(config['image'])
    if hashlib.sha256(image_path.read_bytes()).hexdigest() != json.loads((ROOT / 'builds/target.json').read_text())['image_sha256']:
        raise ValueError('image hash differs from pinned target')
    image = PeImage(image_path.read_bytes())
    objdump = disasm.find_objdump(config.get('objdump'))
    if not objdump:
        raise ValueError('objdump unavailable')
    host = next(h for h in runners.load()['hosts'].values() if h['backend'] == 'local' and h['loader'] == 'wine')
    flags = json.loads((ROOT / template.RECIPE).read_text())['flags']
    handler = json.loads((ROOT / 'reports' / template.BUILD / 'symbol-map.json').read_text())['symbols']['__CxxFrameHandler3']
    tasks, excluded = [], []
    def generate_one(row):
        rva, size = int(row['rva'], 16), int(row['size'])
        try:
            cls, header, cpp, origin, params = template.emit(rva, size)
            target = disasm.target_rows(objdump, str(image_path), rva, size)
            refs = extract(target, image.image_base)
        except ValueError as exc:
            excluded.append({'rva': rva, 'category': str(exc)})
            return
        params.update(refs)
        source = f'reconstruction/static/{cls}.cpp'
        for path, text in ((ROOT / source, cpp), ((ROOT / source).with_suffix('.h'), header)):
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_text() != text:
                raise ValueError('source destination already exists with different content')
            if not path.exists():
                path.write_text(text)
        taskdir = out / 'tasks' / f'p67-{rva:x}'
        taskdir.mkdir(parents=True, exist_ok=True)
        objpath = taskdir / 'probe.obj'
        with runners.slot(host['host_id'], host['max_parallel']):
            proc = subprocess.run([str(Path(host['msvc']) / 'bin/x64/cl'), *flags,
                                   '/Fo' + str(objpath), str(ROOT / source)],
                                  env=unit_build.clean_env(runners.LocalTransport(host).env()),
                                  capture_output=True, text=True)
        if proc.returncode:
            (taskdir / 'probe.log').write_text(proc.stdout + proc.stderr)
            raise ValueError(f'probe compilation failed at 0x{rva:x}')
        obj = CoffObject(objpath.read_bytes())
        name = '??__Eobject@@YAXXZ'
        symbols_by_name = {s.name: s for s in obj.symbols.values()}
        sym = symbols_by_name[name]
        context = {'source_revision': tu_digest(ROOT, include_closure(ROOT, source)), 'source_path': source}
        names = [name, '?descriptor@@3UDescriptor@@A', f'?object@@3U{cls}@@A',
                 f'?construct@@YAXPEAU{cls}@@PEBUDescriptor@@@Z', 'atexit', '??__Fobject@@YAXXZ']
        targets = [rva, refs['descriptor-rva'], refs['object-rva'], refs['construct-rva'],
                   refs['atexit-rva'], refs['teardown-rva']]
        entries = {}
        for n, address in zip(names, targets):
            key = internal.symbol_key(obj, symbols_by_name[n], context) if n in symbols_by_name else n
            entries[key] = {'rva': address, 'size': size if n == name else None}
        entries['__CxxFrameHandler3'] = handler
        provenance = [{'name': n, 'rva': hex(e['rva']), 'size_from': 'task' if e.get('size') else None,
                       'community_name': None, 'note': 'Per-unit target reference extracted from the pinned image; reconstruction names are guesses.'}
                      for n, e in entries.items()]
        smap = {'schema': 1, 'build_id': template.BUILD, 'symbols': entries, 'folds': [],
                '_provenance': {'entries': provenance, 'note': 'Per-unit initializer reference bindings'}}
        digest = hashlib.sha256(symbol_map.serialize(smap)).hexdigest()
        map_path = f'reports/{template.BUILD}/unit-symbols/{digest}.json'
        symbol_map.create(ROOT, map_path, smap)
        metadata = {'origin': origin, 'family_parameters': params, 'name_source': 'GUESS(low)'}
        task = {'task_schema': 2, 'task_id': f'p67-{rva:x}', 'build_id': template.BUILD,
                'compiled': source, 'recipe': template.RECIPE, 'symbols': map_path,
                'functions': [{'rva': rva, 'size': size, 'symbol': name,
                               'internal_selector': internal.selector(obj, sym), 'family_metadata': metadata}]}
        (taskdir / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
        progress['functions'].append({'id': f'{template.BUILD}-0x{rva:x}', 'build_id': template.BUILD,
            'rva': rva, 'size': size, 'status': 'mapped', 'name': f'{cls}::initializer', 'name_origin': 'GUESS',
            'name_source': 'GUESS(low): compiler-generated initializer; owning system unknown.',
            'owner': 'awarebayes', 'evidence': template.EVIDENCE})
        tasks.append(str(taskdir))
        if len(tasks) % 100 == 0:
            print(f'prepared {len(tasks)} members', flush=True)
    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(generate_one, selected))
    tasks.sort(key=lambda name: int(Path(name).name.split('-')[-1], 16))
    progress['functions'] = progress['functions'][:len(progress['functions']) - len(tasks)] + sorted(
        progress['functions'][-len(tasks):], key=lambda fn: fn['rva']) if tasks else progress['functions']
    bind.preflight(tasks, ROOT)
    (out / 'excluded.json').write_text(json.dumps(excluded, indent=2) + '\n')
    (out / 'all.txt').write_text(''.join(task + '\n' for task in tasks))
    (out / 'census.sha256').write_text(hashlib.sha256(Path(census).read_bytes()).hexdigest() + '\n')
    progress_path.write_text(json.dumps(progress, indent=2) + '\n')
    print(f'prepared {len(tasks)}; excluded {len(excluded)}; whole-list bind preflight passed', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--census', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    prepare(args.census, args.out)


if __name__ == '__main__':
    main()
