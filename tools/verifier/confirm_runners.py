"""`confirm` on runner hosts (tools/verifier/runners.py): the maintainer's own machines, no Boat.

Every unit is compiled on each confirm host from .local/verifier/runners.json (at least two, on
two different machines, with two different loaders: the pinned compiler natively on Windows and
under Wine on this Mac). Each host compares its own object against its own copy of the pinned
image; this Mac (the `local` host) also compares every other host's object against its image.
So a record has runs from at least two compile hosts and two compare hosts, as tools/check.py
requires, and each host is named by its host id, with its OS, loader and compiler hashes in a note.

docs/verification.md ("Runner hosts") admits these records as acceptance evidence
(RUNNER_RECORDS_ALLOWED); --out still writes them under DIR/<build id>/ for inspection.
Record assembly, the build block and the Mac comparison are tools/verifier/confirm's own
functions, passed in as `base`.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

import confirm_session
import pipeline
import runners
from pipeline import REPO, PipelineError

# docs/verification.md, "Runner hosts", admits records from these hosts.
RUNNER_RECORDS_ALLOWED = True


def independence_note(hosts, facts):
    parts = []
    for h in hosts:
        f = facts.get(h['host_id']) or {}
        hashes = ', '.join(f'{name} {digest}' for name, digest in sorted((f.get('compiler_sha256') or {}).items()))
        how = 'natively' if f.get('loader') == 'native' else 'under Wine'
        parts.append(f'{h["host_id"]} (machine {h["machine"]}; {f.get("os")} {f.get("machine")}; the pinned compiler '
                     f'run {how}; compiler binaries sha256: {hashes})')
    return ('independence: separate-machine, different-loader. The compile hosts are the maintainer\'s own '
            'machines, each with its own install of the pinned toolchain, reached by tools/verifier/runners.py: '
            + '; '.join(parts) + '. Each host checked its compiler binaries against pinned.sha256 and its own copy '
            'of the image against builds/target.json before compiling, and compared its own object; the local host '
            'also compared the other hosts\' objects. Host facts are self-reported by tools/verifier/unit_build.py.')


def runner_notes(base, task, recipe, hosts, facts, tree_state):
    notes = [n for n in base.notes(task, recipe) if not n.startswith(('Host independence', 'independence:'))]
    notes = [n.replace('under the msvc-wine wrapper', 'per loader').replace(
        'INCLUDE then set by the msvc-wine wrapper to toolchain and SDK directories only',
        'INCLUDE then set to toolchain and SDK directories only (by the msvc-wine wrapper under Wine, by '
        'tools/verifier/unit_build.py from the same directory list natively)') for n in notes]
    return notes[:1] + [independence_note(hosts, facts)] + notes[1:] + [base.source_note(*tree_state)]


def confirm_unit(base, task, files, closure, hosts, out, log):
    started = time.monotonic()
    handle = pipeline.lock(task['dir'])
    recipe = json.loads((REPO / task['recipe']).read_text())
    tree_state = base.source_state(task, closure)
    out_root = task['dir'] / 'confirm'
    stage = task['dir'] / '.confirm-stage'
    local = [h for h in hosts if h['backend'] == 'local']
    lines, rows, failed = [], {}, True
    workers = {h['host_id']: runners.AgentHost(h, task, log=log) for h in hosts}
    try:
        outcome = {}

        def work(label, host):
            try:
                code, _ = host.run(files, stage / label)
                outcome[label] = (code, host.fetch(out_root / label))
            except Exception as exc:  # reported below
                outcome[label] = (None, exc)

        threads = [threading.Thread(target=work, args=item) for item in workers.items()]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        for label, (code, value) in outcome.items():
            if code is None:
                raise PipelineError(f'{label}: {value}')
            if code not in (0, 1):
                raise PipelineError(f'{label}: the unit did not build or was refused (exit {code}); '
                                    f'run tools/verifier/attempt first, details in {value}')
        facts = {label: w.facts for label, w in workers.items()}
        problem = runners.independence_problem(hosts, facts)
        if problem:
            raise PipelineError(f'compile hosts are not independent as reported: {problem}')
        runs = {fn['rva']: [] for fn in task['functions']}
        for fn in task['functions']:
            rows[fn['rva']] = {}
        for label in workers:
            host_dir = outcome[label][1]
            for fn in task['functions']:
                report = host_dir / f'0x{fn["rva"]:x}' / 'report.json'
                rows[fn['rva']][label] = base.result_of(report)
                runs[fn['rva']].append((label, label, report))
                for compare in local:
                    if compare['host_id'] == label:
                        continue
                    _, mac_report = base.mac_compare(task, fn, host_dir,
                                                     out_root / 'mac' / label / f'0x{fn["rva"]:x}')
                    rows[fn['rva']][f'{compare["host_id"]}<-{label}'] = base.result_of(mac_report)
                    runs[fn['rva']].append((label, compare['host_id'], mac_report))
        failed = any(v[0] != 'pass' for row in rows.values() for v in row.values())
        if failed:
            lines.append('  no record written: every run must pass; a pass that fails to reproduce is escalated')
        else:
            build_path = out_root / 'build.json'
            build_path.write_text(json.dumps(base.build_block(task, {label: outcome[label][1] for label in workers}),
                                             indent=2) + '\n')
            more, failed = confirm_session.write_records(
                base, task, closure, recipe, runs, build_path, out,
                notes=runner_notes(base, task, recipe, hosts, facts, tree_state))
            lines += more
    except (PipelineError, runners.RunnerError) as exc:
        lines.append(f'  ERROR {exc}')
        failed = True
    finally:
        lines.append(f'  private: {out_root}/  time {time.monotonic() - started:.0f} s')
        handle.close()
    return rows, lines, failed


def run(base, task_dirs, replace=False, out=None, log=print, hosts=None):
    started = time.monotonic()
    hosts = hosts if hosts is not None else runners.for_confirm()
    if not hosts:
        raise PipelineError('no runner confirm hosts in .local/verifier/runners.json ("confirm")')
    if out is None and not RUNNER_RECORDS_ALLOWED:
        raise PipelineError('records from runner hosts are not acceptance evidence until docs/verification.md admits '
                            'them; pass --out DIR to write inspection records outside reports/')
    if not any(h['backend'] == 'local' for h in hosts):
        log('confirm: no local host among the confirm hosts; each object is compared on its own host only')
    prepared = [confirm_session.prepare(base, d, replace, out) for d in task_dirs]
    ids = [t['task_id'] for t, _, _ in prepared]
    if len(set(ids)) != len(ids):
        raise PipelineError('a task id is listed twice')
    parallel = max(1, min(h['max_parallel'] for h in hosts))
    log(f'confirm: {len(prepared)} unit(s) on ' + ', '.join(runners.describe(h) for h in hosts)
        + f'; up to {parallel} in parallel')
    with ThreadPoolExecutor(max_workers=min(parallel, len(prepared))) as pool:
        results = list(pool.map(lambda p: (p[0], confirm_unit(base, *p, hosts, out, log)), prepared))
    table, any_failed = [], False
    for task, (rows, lines, failed) in results:
        any_failed |= failed
        log(f'{task["task_id"]} ({task["compiled"]}): ' + ('FAILED' if failed else 'records written'))
        for line in lines:
            log(line)
        for rva, row in rows.items():
            ok = all(v[0] == 'pass' for v in row.values())
            shown = ' '.join(f'{k}={v[0]}' + ('' if v[0] == 'pass' else f':{v[1]}') for k, v in row.items())
            table.append(f'  {task["task_id"]:<28} 0x{rva:<9x} {"REPRODUCED" if ok else "NOT REPRODUCED":<15} {shown}')
    if not out and not any_failed:
        check = subprocess.run([sys.executable, str(REPO / 'tools/check.py')], cwd=REPO, capture_output=True, text=True)
        log('check.py: ' + (check.stdout or check.stderr).strip().splitlines()[-1][:160])
        any_failed |= check.returncode != 0
    log('summary:')
    for line in table:
        log(line)
    log(f'time {time.monotonic() - started:.0f} s; no Boat machine used')
    return 1 if any_failed else 0
