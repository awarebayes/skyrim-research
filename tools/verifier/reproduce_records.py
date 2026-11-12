#!/usr/bin/env python3
"""Recompile every unit that has a match record on one runner host and compare with the records.

    python3 tools/verifier/reproduce_records.py --host mac [--jobs N] [--unit reconstruction/...cpp]

For each translation unit with records under reports/<build id>/, the unit is compiled from this
checkout on the named host (tools/verifier/runners.py) with the record's recipe and the repository
symbol map, and each function is compared there against that host's pinned image. A function is
`equal` when the tree's tu-sha256-v1 digest is the record's, the comparator passes, and the
candidate code-section hash equals the one every run of the record reports. Anything else is
`different` with a reason; differences are findings, never adjusted.

This proves a host reproduces the committed evidence; it writes no record and accepts nothing.
Output is counts, RVAs, reason codes and hashes; private run files go to
.local/verifier/reproduce/<host id>/ (or --out); each run's summary is kept as
summaries/<UTC time>-<random>.json there, and summary.json is a copy of the latest. Exit 0 all equal, 1 some different, 2 error.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pipeline  # noqa: E402
import runners  # noqa: E402
from source_digest import tu_digest  # noqa: E402  (pipeline puts tools/ on the path)

REPO = pipeline.REPO


def records(repo=REPO):
    target = json.loads((Path(repo) / 'builds/target.json').read_text())
    out = []
    for path in sorted((Path(repo) / 'reports' / target['build_id']).glob('0x*.json')):
        if path.name.endswith('.review.json'):
            continue
        rec = json.loads(path.read_text())
        if 'match_record_schema' in rec:
            out.append(rec)
    return target, out


def task_id_for(compiled):
    stem = re.sub(r'[^a-z0-9]+', '-', compiled.lower().removeprefix('reconstruction/').removesuffix('.cpp')).strip('-')
    name = f'repro-{stem}'
    if len(name) > 43:
        name = name[:30].rstrip('-') + '-' + hashlib.sha256(compiled.encode()).hexdigest()[:12]
    return name


def units(recs, target, matched, root):
    """[(task, {rva: record})] grouped by compiled file, recipe and symbol map."""
    groups = {}
    for rec in recs:
        key = (rec['source']['compiled'], rec['recipe']['path'], rec['symbol_map']['path'])
        groups.setdefault(key, []).append(rec)
    out = []
    for (compiled, recipe, symbols), group in sorted(groups.items()):
        tid = task_id_for(compiled)
        functions, by_rva = [], {}
        for rec in group:
            fn = rec['runs'][0]['report']['function']
            functions.append({'rva': fn['rva'], 'size': fn['size'], 'symbol': fn['symbol']})
            by_rva[fn['rva']] = rec
        task = {'dir': Path(root) / tid, 'task_id': tid, 'build_id': target['build_id'], 'compiled': compiled,
                'recipe': recipe, 'symbols_local': REPO / symbols, 'symbols_repo': symbols,
                'functions': sorted(functions, key=lambda f: f['rva']), 'max_attempts': None, 'record_notes': []}
        out.append((task, by_rva))
    return out


def expected(rec):
    """(digest, {code-section hashes of every run}, every run passed)."""
    reports = [run['report'] for run in rec['runs']]
    return (rec['source']['digest'], {r['candidate']['code_section_sha256'] for r in reports},
            all(r.get('result') == 'pass' for r in reports))


def judge(rec, digest_now, report):
    """('equal', None) or ('different', why) for one function."""
    digest, hashes, passed = expected(rec)
    if not passed or len(hashes) != 1:
        return 'different', 'record-runs-disagree'
    if digest_now != digest:
        return 'different', 'tree-digest-differs-from-record'
    if report is None:
        return 'different', 'no-report'
    if report.get('result') != 'pass':
        return 'different', f'comparator-{report.get("result")}:{report.get("reason")}'
    if (report.get('candidate') or {}).get('code_section_sha256') not in hashes:
        return 'different', 'code-section-hash-differs'
    return 'equal', None


def reproduce_unit(host, task, by_rva, out_root, log):
    started = time.monotonic()
    files, closure = pipeline.unit_manifest(task)
    digest_now = tu_digest(REPO, closure)
    worker = runners.AgentHost(host, task, log=log)
    dest = Path(out_root) / task['task_id']
    stage = Path(out_root) / '.stage'
    stage.mkdir(parents=True, exist_ok=True)
    code, _ = worker.run(files, stage)
    try:
        worker.fetch(dest)
    except (runners.RunnerError, OSError):
        dest.mkdir(parents=True, exist_ok=True)
    rows = []
    for fn in task['functions']:
        try:
            report = json.loads((dest / f'0x{fn["rva"]:x}' / 'report.json').read_text())
        except (OSError, ValueError):
            report = None
        verdict, why = judge(by_rva[fn['rva']], digest_now, report)
        if report is None and code not in (0, 1):
            why = f'unit-exit-{code}'
        rows.append({'rva': fn['rva'], 'function_id': by_rva[fn['rva']]['function_id'], 'verdict': verdict,
                     'why': why, 'code_section_sha256': ((report or {}).get('candidate') or {}).get('code_section_sha256')})
    return {'unit': task['compiled'], 'exit': code, 'seconds': round(time.monotonic() - started, 1),
            'waited': round(worker.waited, 1), 'timings': {k: round(v, 1) for k, v in worker.timings.items()},
            'facts': worker.facts, 'functions': rows}


def save_summary(out_root, summary, now=None):
    """Write the summary to <out_root>/summaries/<UTC time>-<random>.json, never replacing an earlier
    one, and copy it to <out_root>/summary.json as the latest; returns the per-run path.

    A later run (even one of a single unit) must not overwrite the evidence of an earlier full one.
    """
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))
    folder = Path(out_root) / 'summaries'
    folder.mkdir(parents=True, exist_ok=True)
    text = json.dumps(summary, indent=1) + '\n'
    path = folder / f'{stamp}-{uuid.uuid4().hex[:8]}.json'
    with open(path, 'x') as f:
        f.write(text)
    (Path(out_root) / 'summary.json').write_text(text)
    return path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--host', required=True, help='host name in .local/verifier/runners.json')
    p.add_argument('--jobs', type=int, help='units in flight (default: the host\'s max_parallel)')
    p.add_argument('--unit', action='append', help='only this compiled file (repeatable)')
    p.add_argument('--out', type=Path, help='private output directory (default .local/verifier/reproduce/<host id>)')
    a = p.parse_args()
    try:
        config = runners.load()
        if config is None or a.host not in config['hosts'] or config['hosts'][a.host]['backend'] == 'boat':
            raise runners.RunnerError(f'{a.host} is not a local or ssh host in {runners.config_path()}')
        host = runners.with_image(config['hosts'][a.host])
        target, recs = records()
        progress = json.loads((REPO / 'data/progress.json').read_text())
        matched = {f['id'] for f in progress['functions'] if f.get('status') == 'matched'}
        out_root = a.out or (runners.main_root() / '.local' / 'verifier' / 'reproduce' / host['host_id'])
        pipeline.private_root(out_root)
        todo = units(recs, target, matched, out_root)
        if a.unit:
            todo = [t for t in todo if t[0]['compiled'] in a.unit]
        jobs = a.jobs or host['max_parallel']
        print(f'reproduce: {sum(len(b) for _, b in todo)} records in {len(todo)} units on {runners.describe(host)}; '
              f'{jobs} in flight')
        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            results = list(pool.map(lambda t: reproduce_unit(host, t[0], t[1], out_root, lambda m: None), todo))
    except (runners.RunnerError, pipeline.PipelineError) as exc:
        print(f'reproduce: {exc}', file=sys.stderr)
        return 2
    rows = [r for unit in results for r in unit['functions']]
    eq = sum(r['verdict'] == 'equal' for r in rows)
    m_rows = [r for r in rows if r['function_id'] in matched]
    m_eq = sum(r['verdict'] == 'equal' for r in m_rows)
    for unit in results:
        d = sum(r['verdict'] != 'equal' for r in unit['functions'])
        print(f'  {unit["unit"]}: {len(unit["functions"]) - d}/{len(unit["functions"])} equal, exit {unit["exit"]}, '
              f'{unit["seconds"]} s')
    for r in rows:
        if r['verdict'] != 'equal':
            print(f'  DIFFERENT 0x{r["rva"]:x} {r["why"]}')
    facts = {json.dumps(u['facts'], sort_keys=True) for u in results if u['facts']}
    seconds = sorted(u['seconds'] - u['waited'] for u in results)
    summary = {'host': host['host_id'], 'records': len(rows), 'equal': eq, 'different': len(rows) - eq,
               'matched': len(m_rows), 'matched_equal': m_eq, 'matched_different': len(m_rows) - m_eq,
               'units': len(results), 'jobs': jobs, 'wall_seconds': round(time.monotonic() - started, 1),
               'unit_seconds_median': seconds[len(seconds) // 2] if seconds else None,
               'host_facts': [json.loads(f) for f in sorted(facts)], 'results': results}
    saved = save_summary(out_root, summary)
    print(f'records: {eq}/{len(rows)} equal; matched (data/progress.json): {m_eq}/{len(m_rows)} equal, '
          f'{len(m_rows) - m_eq} different; {len(results)} units, wall {summary["wall_seconds"]} s, '
          f'median unit {summary["unit_seconds_median"]} s')
    for f in summary['host_facts']:
        print(f'host facts: {json.dumps(f, sort_keys=True)}')
    print(f'summary: {saved} (private; summary.json is a copy of the latest run)')
    return 0 if eq == len(rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
