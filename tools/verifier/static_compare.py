"""Compare original synthetic internal functions in a two-TU MSVC build, then perturb bindings.

    python3 tools/verifier/static_compare.py <private-build-dir>

Run build_static.sh first. The DLL has no CRT entry point and is never executed; it tests bytes
and identity only, not startup or registration semantics. No object or DLL is published.
"""
import copy
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compare_internal as ci
from pecoff import CoffObject, PeImage
from source_digest import include_closure, tu_digest

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = 'tools/verifier/synthetic'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'


def cases(directory):
    directory = Path(directory)
    image = (directory / 'static.dll').read_bytes()
    base = PeImage(image).image_base
    rows = []
    for line in (directory / 'static.map').read_text().splitlines():
        match = re.match(r'\s+[0-9a-fA-F]{4}:[0-9a-fA-F]{8}\s+(\S+)\s+([0-9a-fA-F]{16})\s+(?:f\s+)?(\S+\.obj)\s*$', line)
        if match:
            rows.append((match[1], int(match[2], 16) - base, match[3]))
    externals = {name: {'rva': rva, 'size': None} for name, rva, obj in rows
                 if obj == 'static_identity_runtime.obj'}
    recipe = (ROOT / RECIPE).read_bytes()
    results = []
    for tu in ('static_identity_a', 'static_identity_b'):
        obj_bytes = (directory / f'{tu}.obj').read_bytes()
        obj = CoffObject(obj_bytes)
        source = f'{SOURCE_ROOT}/{tu}.cpp'
        revision = tu_digest(ROOT, include_closure(ROOT, source))
        context = {'source_revision': revision, 'source_path': source}
        symbols = copy.deepcopy(externals)
        for sym in obj.symbols.values():
            entries = [rva for name, rva, unit in rows if name == sym.name and unit == f'{tu}.obj']
            if sym.section > 0 and len(entries) == 1:
                symbols[ci.symbol_key(obj, sym, context)] = {
                    'rva': entries[0], 'size': len(obj.section(sym.section).data) if sym.is_function else None}
        for sym in obj.symbols.values():
            if sym.storage != 3 or not sym.is_function or sym.section <= 0:
                continue
            task = dict(context, task_schema=2, task_id=tu.replace('_', '-') + ('-init' if sym.name.startswith('??__E') else '-dtor'),
                        build_id='synthetic-static', target_image_sha256=ci.sha256(image),
                        rva=symbols[ci.symbol_key(obj, sym, context)]['rva'], size=len(obj.section(sym.section).data),
                        symbol=sym.name, recipe_sha256=ci.sha256(recipe))
            task['internal_identity'] = ci.make_identity(obj_bytes, sym.name, ci.selector(obj, sym), revision, source)
            args = {'task': task, 'manifest': {'status': 'pinned', 'build_id': task['build_id'],
                                               'image_sha256': task['target_image_sha256']},
                    'recipe_bytes': recipe, 'build_record': dict(context, source_path=source,
                        recipe_sha256=task['recipe_sha256'], object_sha256=ci.sha256(obj_bytes)),
                    'object_bytes': obj_bytes, 'image_bytes': image,
                    'symbol_map': {'schema': 1, 'build_id': task['build_id'], 'symbols': symbols, 'folds': []}}
            results.append((tu, sym.name, args))
    return results


def run(directory):
    result = []
    all_cases = cases(directory)
    for tu, symbol, args in all_cases:
        report = ci.compare(**args)
        result.append({'tu': tu, 'function': symbol, 'case': 'complete',
                       'result': report['result'], 'reason': report['reason']})
        if report['result'] != 'pass':
            raise AssertionError(report['detail'])
        for change in ('wrong-tu', 'wrong-guard', 'wrong-atexit', 'wrong-section', 'changed-source', 'short', 'long'):
            bad = copy.deepcopy(args)
            if change == 'wrong-tu':
                bad['symbol_map'] = copy.deepcopy(next(a['symbol_map'] for t, s, a in all_cases if t != tu and s == symbol))
            elif change in ('wrong-guard', 'wrong-atexit'):
                if change == 'wrong-atexit' and not symbol.startswith('??__E'):
                    continue
                obj = CoffObject(args['object_bytes'])
                sym = next(s for s in obj.symbols.values() if s.name.startswith('?object@@'))
                key = ci.symbol_key(obj, sym, args['task']) if change == 'wrong-guard' else 'atexit'
                bad['symbol_map']['symbols'][key]['rva'] += 1
            elif change == 'wrong-section':
                bad['task']['internal_identity']['section_number'] += 1
            elif change == 'changed-source':
                bad['task']['source_revision'] = ci.sha256(b'changed synthetic source')
                bad['build_record']['source_revision'] = bad['task']['source_revision']
            else:
                bad['task']['size'] += -1 if change == 'short' else 1
                key = bad['task']['internal_identity']['map_key']
                bad['symbol_map']['symbols'][key]['size'] = bad['task']['size']
            refused = ci.compare(**bad)
            result.append({'tu': tu, 'function': symbol, 'case': change,
                           'result': refused['result'], 'reason': refused['reason']})
            if refused['result'] != 'fail':
                raise AssertionError(f'{tu} {symbol}: {change} passed')
    return result


if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), indent=2))
