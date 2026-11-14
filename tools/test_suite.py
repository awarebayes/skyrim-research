#!/usr/bin/env python3
"""Run the complete unittest discovery inventory in isolated module processes, with no exclusions."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def inventory(root):
    tests = root / 'tests'
    loader = unittest.TestLoader()
    suite = loader.discover(str(tests), top_level_dir=str(tests))
    if loader.errors:
        raise ValueError('\n'.join(loader.errors))
    modules = {}
    for test in flatten(suite):
        modules.setdefault(test.__class__.__module__, []).append(test.id())
    return modules


def execute(root, ids, result):
    proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--root', root,
                           '--worker', '--result', result], input=json.dumps(ids),
                          capture_output=True, text=True, cwd=root)
    path = Path(result)
    report = json.loads(path.read_text()) if path.is_file() else None
    return proc.returncode, proc.stdout + proc.stderr, report


def shard_modules(modules, index, count):
    """Partition whole modules so their fixtures and test order remain unchanged."""
    if count < 1 or not 0 <= index < count:
        raise ValueError('require --shard-count > 0 and 0 <= --shard-index < --shard-count')
    return {name: modules[name] for offset, name in enumerate(sorted(modules)) if offset % count == index}


def run(root, jobs, listing=False, shard_index=0, shard_count=1):
    modules = inventory(root)
    discovered = sum(map(len, modules.values()))
    modules = shard_modules(modules, shard_index, shard_count)
    if listing:
        print(json.dumps(modules, indent=2))
        return 0
    expected = sum(map(len, modules.values()))
    started, total, skipped, failed = time.monotonic(), 0, 0, False
    # Module fixtures, class fixtures and their ordering stay inside one normal unittest run.
    with tempfile.TemporaryDirectory(prefix='test-suite-') as tmp, ProcessPoolExecutor(max_workers=jobs) as pool:
        tasks = {pool.submit(execute, str(root), ids, str(Path(tmp) / (module + '.json'))): (module, ids)
                 for module, ids in modules.items()}
        for future in as_completed(tasks):
            module, ids = tasks[future]
            code, output, report = future.result()
            print(output, end='', flush=True)
            if report is None or code or report['run'] != len(ids):
                failed = True
                print(f'FAIL: {module}: worker exit {code}, expected {len(ids)} tests, report {report}', flush=True)
            if report:
                total += report['run']
                skipped += report['skipped']
    failed |= total != expected
    seconds = time.monotonic()-started
    report = root / ('.local/test-suite-results.json' if shard_count == 1 else
                     f'.local/test-suite-results-{shard_index}-of-{shard_count}.json')
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(dict(discovered=discovered, selected=expected, executed=total,
                                      shard_index=shard_index, shard_count=shard_count,
                                      skipped=skipped, failed=failed,
                                      jobs=jobs, seconds=seconds, python=sys.version.split()[0]), indent=2)+'\n')
    print(f'\nRan {total} tests in {time.monotonic()-started:.3f}s; discovered {discovered}; '
          f'selected {expected}; shard {shard_index}/{shard_count}; module processes {jobs}')
    print('FAILED' if failed else f'OK (skipped={skipped}; existing unittest decorators only)')
    return int(failed)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path.cwd())
    p.add_argument('--jobs', type=int, default=min(4, os.cpu_count() or 1))
    p.add_argument('--list', action='store_true')
    p.add_argument('--shard-index', type=int, default=0, help='zero-based CI shard (whole modules)')
    p.add_argument('--shard-count', type=int, default=1)
    p.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--result', type=Path, help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.jobs < 1:
        p.error('--jobs must be positive')
    if a.shard_count < 1 or not 0 <= a.shard_index < a.shard_count:
        p.error('require --shard-count > 0 and 0 <= --shard-index < --shard-count')
    root = a.root.resolve()
    os.chdir(root)
    sys.path.insert(0, str(root / 'tests'))
    if a.worker:
        ids = json.load(sys.stdin)
        # unittest discovery imports every module before running any test. Preserve that
        # import environment (including legacy path setup) in each isolated worker.
        inventory(root)
        suite = unittest.defaultTestLoader.loadTestsFromNames(ids)
        result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
        a.result.write_text(json.dumps(dict(run=result.testsRun, skipped=len(result.skipped))))
        return 0 if result.wasSuccessful() else 1
    return run(root, a.jobs, a.list, a.shard_index, a.shard_count)


if __name__ == '__main__':
    raise SystemExit(main())
