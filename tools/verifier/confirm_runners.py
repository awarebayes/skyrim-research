"""`confirm` on runner hosts (tools/verifier/runners.py): the maintainer's own machines, no Boat.

Every unit is compiled on each confirm host from .local/verifier/runners.json (at least two, on
two different machines, with two different loaders: the pinned compiler natively on Windows and
under Wine on this Mac). Each host compares its own object against its own copy of the pinned
image; this Mac (the `local` host) also compares every other host's object against its image.
So a record has runs from at least two compile hosts and two compare hosts, as tools/check.py
requires, and each host is named by its host id, with its OS, loader and compiler hashes in a note.

docs/verification.md ("Runner hosts") admits these records as acceptance evidence
(RUNNER_RECORDS_ALLOWED); --out still writes them under DIR/<build id>/ for inspection. Writing
into reports/ needs a `local` host among the confirm hosts, because the rule requires the local
cross-compare of every other host's object. Every confirm run hashes each host's toolchain afresh
(no per-boot cache), and the hosts' own reports must show the loaders their config names, a
native compile on Windows and two operating systems (runners.independence_problem).
Record assembly, the build block and the Mac comparison are tools/verifier/confirm's own
functions, passed in as `base`.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import uuid

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
            + '; '.join(parts) + '. Each host hashed its compiler binaries during this confirm run and checked them '
            'against pinned.sha256, checked its own copy of the image against builds/target.json before compiling, '
            'and compared its own object; the local host '
            'also compared the other hosts\' objects. Host facts are self-reported by tools/verifier/unit_build.py.')


def reproduction(base, task, fn, closure, recipe):
    """The commands each compile host ran: the msvc-wine wrapper under Wine, cl.exe natively."""
    import check
    flags = ' '.join(recipe['flags'] + check.BUILD_ADDED_FLAGS)
    unset = ', '.join(check.BUILD_CLEARED_ENV)
    version = recipe['compiler']['version'].split(' ')[0]
    return (f'From the repository root, on each compile host, with cl {version} x64 unpacked at <msvc> (an MSVC '
            f'toolset and Windows SDK whose compiler binaries match tools/verifier/pinned.sha256; '
            f'tools/verifier/setup_boat_machine.sh shows one way to unpack them with msvc-wine) and {unset} removed '
            f'from the environment. Under Wine: <msvc>/bin/x64/cl {flags} /Fo<work>/candidate.obj {task["compiled"]} '
            f'(the msvc-wine wrapper sets INCLUDE to toolchain and SDK directories only). Natively on Windows: set '
            f'INCLUDE to the directories the wrapper uses, in its order, '
            f'<msvc>/VC/Tools/MSVC/<toolset>/atlmfc/include;<msvc>/VC/Tools/MSVC/<toolset>/include;'
            f'<msvc>/Windows Kits/10/Include/<sdk>/shared;.../ucrt;.../um;.../winrt;.../km '
            f'(tools/verifier/unit_build.py, MSVC_INCLUDE_DIRS), then run '
            f'<msvc>/VC/Tools/MSVC/<toolset>/bin/Hostx64/x64/cl.exe {flags} /Fo<work>/candidate.obj '
            f'{task["compiled"]}. On both, the verifier required the repository files /showIncludes lists to equal '
            f'--unit below ; ' + base.compare_steps(task, fn, ' '.join(closure)))


def facts_problem(hosts, facts):
    """Why the hosts' reported facts cannot go into a record, or None: the independence rule, and a
    toolchain hash measured in this run on every host."""
    problem = runners.independence_problem(hosts, facts)
    if problem:
        return problem
    for h in hosts:
        if (facts.get(h['host_id']) or {}).get('toolchain_check') != 'checked':
            return f'{h["host_id"]} did not report a toolchain check made in this run'
    return None


def runner_notes(base, task, recipe, hosts, facts, tree_state):
    notes = [n for n in base.notes(task, recipe) if not n.startswith(('Host independence', 'independence:'))]
    notes = [n.replace('under the msvc-wine wrapper', 'per loader').replace(
        'INCLUDE then set by the msvc-wine wrapper to toolchain and SDK directories only',
        'INCLUDE then set to toolchain and SDK directories only (by the msvc-wine wrapper under Wine, by '
        'tools/verifier/unit_build.py from the same directory list natively)') for n in notes]
    return notes[:1] + [independence_note(hosts, facts)] + notes[1:] + [base.source_note(*tree_state)]


def finish_unit(base, task, closure, hosts, outcome, out, tree_state):
    """(rows, lines, failed, written) for one unit once every host has its result.

    `outcome` is {host id: (exit code, unit directory, host facts)} or {host id: exception}. Every
    check of the single-unit path applies: each host built the unit, the reported facts meet the
    rule (toolchain hashed in this run on every host), every run passes, and match_record.py
    validates each record. `written` lists the record paths written."""
    recipe = json.loads((REPO / task['recipe']).read_text())
    out_root = task['dir'] / 'confirm'
    local = [h for h in hosts if h['backend'] == 'local']
    labels = [h['host_id'] for h in hosts]
    lines, rows, failed, written = [], {}, True, []
    try:
        for label in labels:
            value = outcome.get(label)
            if not isinstance(value, tuple):
                raise PipelineError(f'{label}: {value}')
            code, host_dir, _ = value
            if code not in (0, 1):
                raise PipelineError(f'{label}: the unit did not build or was refused (exit {code}); '
                                    f'run tools/verifier/attempt first, details in {host_dir}')
        facts = {label: outcome[label][2] for label in labels}
        problem = facts_problem(hosts, facts)
        if problem:
            raise PipelineError(f'compile hosts are not independent as reported: {problem}')
        runs = {fn['rva']: [] for fn in task['functions']}
        for fn in task['functions']:
            rows[fn['rva']] = {}
        for label in labels:
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
            build_path.write_text(json.dumps(base.build_block(task, {label: outcome[label][1] for label in labels}),
                                             indent=2) + '\n')
            more, failed = confirm_session.write_records(
                base, task, closure, recipe, runs, build_path, out,
                notes=runner_notes(base, task, recipe, hosts, facts, tree_state),
                reproduction=lambda *a: reproduction(base, *a))
            lines += more
            if not failed:
                written = [confirm_session.record_path(task, fn, out) for fn in task['functions']]
    except (PipelineError, runners.RunnerError) as exc:
        lines.append(f'  ERROR {exc}')
        failed = True
    return rows, lines, failed, written


# Files whose content can change what a runner confirm writes, beyond the unit's own inputs.
RUNNER_TOOLS = ('tools/verifier/confirm', 'tools/verifier/pipeline.py', 'tools/verifier/match_record.py',
                'tools/check.py', 'tools/verifier/confirm_runners.py', 'tools/verifier/confirm_session.py',
                'tools/verifier/runners.py', 'tools/verifier/host_agent.py')


def _sha256(path):
    return pipeline.sha256_file(path) if Path(path).is_file() else None


def input_key(task, files, hosts, out, tree_state):
    """The hash of everything a unit's records depend on except the hosts' toolchains, which a
    resumed run measures afresh: every file shipped to the hosts (sources, recipe, symbol map,
    comparator, host scripts, pins, manifest), the record-assembly tools and the validator, the
    base commit with the uncommitted inputs and the comparator source hash, the hosts and the
    output directory."""
    blob = {'task': {k: task.get(k) for k in ('task_id', 'build_id', 'compiled', 'recipe', 'symbols_repo',
                                              'functions', 'record_notes')},
            'files': {name: _sha256(path) for name, path in sorted(files.items())},
            'tools': {name: _sha256(REPO / name) for name in RUNNER_TOOLS},
            'tree_state': json.loads(json.dumps(list(tree_state), default=str)),
            'hosts': [{k: h.get(k) for k in ('host_id', 'machine', 'backend', 'loader')} for h in hosts],
            'out': str(out) if out else 'reports', 'records_allowed': RUNNER_RECORDS_ALLOWED}
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


class Journal:
    """One JSON line per unit whose records were written, appended and flushed as each unit
    finishes, so a stopped run leaves a trail --resume can use. Kept under .local/verifier/."""

    def __init__(self, out):
        name = 'reports' if out is None else 'out-' + hashlib.sha256(str(out).encode()).hexdigest()[:16]
        self.path = runners.starts.state_dir() / 'confirm-journal' / f'{name}.jsonl'
        self.lock = threading.Lock()

    def entries(self):
        found = {}
        try:
            text = self.path.read_text()
        except OSError:
            return found
        for line in text.splitlines():
            try:
                entry = json.loads(line)
                found[entry['task_id']] = entry
            except (ValueError, KeyError, TypeError):
                continue
        return found

    def add(self, entry):
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'a') as f:
                f.write(json.dumps(entry, sort_keys=True) + '\n')
                f.flush()
                os.fsync(f.fileno())


def reusable(entry, key, toolchains):
    """Why a journal entry cannot stand for this unit in this run, or None when it can: same input
    key, every host's compiler hashes as measured at the start of this run equal to those the
    journalled run reported, and every record it wrote still on disk unchanged."""
    if not entry:
        return 'not in the journal'
    if entry.get('key') != key:
        return 'inputs changed'
    recorded = entry.get('compiler_sha256') or {}
    if set(recorded) != set(toolchains):
        return 'different compile hosts'
    for host_id, measured in toolchains.items():
        if not measured or recorded.get(host_id) != measured:
            return f'{host_id} toolchain is not the one the journalled run measured'
    records = entry.get('records') or {}
    if not records:
        return 'no records'
    for path, digest in records.items():
        if _sha256(path) != digest:
            return f'record {Path(path).name} missing or changed'
    return None


def measure_toolchains(hosts, probe_fn, log):
    """{host id: compiler hashes} measured now on each host; None where the check did not pass."""
    found = {}
    for h in hosts:
        try:
            p = probe_fn(h)
        except (runners.RunnerError, OSError, subprocess.SubprocessError) as exc:
            log(f'resume: {h["host_id"]} probe failed ({exc}); no unit is skipped')
            found[h['host_id']] = None
            continue
        ok = p.get('toolchain') == 'ok' and p.get('image') == 'ok'
        found[h['host_id']] = p.get('compiler_sha256') if ok else None
        if not ok:
            log(f'resume: {h["host_id"]} toolchain {p.get("toolchain")}, image {p.get("image")}; no unit is skipped')
    return found


def open_log(log):
    """`log` that also appends each line, flushed, to a per-run file under .local/verifier/confirm-logs/."""
    directory = runners.starts.state_dir() / 'confirm-logs'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}-{uuid.uuid4().hex[:6]}.log'
    handle = open(path, 'a')
    lock = threading.Lock()

    def both(message):
        with lock:
            handle.write(message + '\n')
            handle.flush()
        log(message)
    return both, handle, path


def run_host(host, units, stage_root, deliver, log):
    """Every unit on one host, each with a toolchain check made in this run: one unit per slot
    (batch 1, the local host), or batches of host['batch'] units per upload (an ssh host)."""
    size = host.get('batch', 1)
    label = host['host_id']
    if size <= 1:
        def one(item):
            task, files = item
            worker = runners.AgentHost(host, task, log=log, fresh_prep=True)
            try:
                code, _ = worker.run(files, task['dir'] / '.confirm-stage' / label)
                dest = worker.fetch(task['dir'] / 'confirm' / label)
                deliver(task, label, (code, dest, worker.facts))
            except Exception as exc:  # reported with the unit
                deliver(task, label, exc)
        with ThreadPoolExecutor(max_workers=max(1, min(host['max_parallel'], len(units)))) as pool:
            list(pool.map(one, units))
        return
    worker = runners.BatchHost(host, log=log, fresh_prep=True)

    def batch(chunk):
        started = time.monotonic()
        try:
            results = worker.run(chunk, Path(stage_root) / label,
                                 {task['task_id']: task['dir'] / 'confirm' / label for task, _ in chunk})
        except Exception as exc:  # the whole batch failed; each of its units reports it
            results = {task['task_id']: exc for task, _ in chunk}
        for task, _ in chunk:
            deliver(task, label, results.get(task['task_id'], runners.RunnerError(f'{label}: no result')))
        log(f'{label}: batch of {len(chunk)} unit(s) in {time.monotonic() - started:.0f} s')

    # Two batches in flight: one transfers while the other compiles (BatchHost holds slots only then).
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(batch, [units[i:i + size] for i in range(0, len(units), size)]))


def run(base, task_dirs, replace=False, out=None, log=print, hosts=None, resume=False, probe_fn=None):
    started = time.monotonic()
    hosts = hosts if hosts is not None else runners.for_confirm()
    if not hosts:
        raise PipelineError('no runner confirm hosts in .local/verifier/runners.json ("confirm")')
    if out is None and not RUNNER_RECORDS_ALLOWED:
        raise PipelineError('records from runner hosts are not acceptance evidence until docs/verification.md admits '
                            'them; pass --out DIR to write inspection records outside reports/')
    if not any(h['backend'] == 'local' for h in hosts):
        if out is None:
            raise PipelineError('records in reports/ need a local host among the confirm hosts: docs/verification.md '
                                '("Runner hosts") requires it to compare every other host\'s object')
        log('confirm: no local host among the confirm hosts; each object is compared on its own host only '
            '(inspection records under --out only)')
    # With --resume the existing-record check moves to the units that actually run again.
    prepared = [confirm_session.prepare(base, d, replace or resume, out) for d in task_dirs]
    ids = [t['task_id'] for t, _, _ in prepared]
    if len(set(ids)) != len(ids):
        raise PipelineError('a task id is listed twice')
    log, handle, log_path = open_log(log)
    try:
        return _run(base, prepared, hosts, replace, out, log, log_path, resume, probe_fn, started)
    finally:
        handle.close()


def _run(base, prepared, hosts, replace, out, log, log_path, resume, probe_fn, started):
    journal = Journal(out)
    log(f'confirm: {len(prepared)} unit(s) on ' + ', '.join(
        f'{runners.describe(h)} [{h["max_parallel"]} slots, batch {h.get("batch", 1)}]' for h in hosts)
        + f'; log {log_path}; journal {journal.path}')
    toolchains = measure_toolchains(hosts, probe_fn or runners.probe, log) if resume else {}
    entries = journal.entries() if resume else {}
    states, skipped, pending = {}, [], []
    for task, files, closure in prepared:
        tid = task['task_id']
        states[tid] = base.source_state(task, closure)
        key = input_key(task, files, hosts, out, states[tid])
        why = reusable(entries.get(tid), key, toolchains) if resume else 'not resuming'
        if why is None:
            skipped.append(task)
            continue
        if resume and not replace:
            for fn in task['functions']:
                path = confirm_session.record_path(task, fn, out)
                if path.exists():
                    raise PipelineError(f'{path} exists and {tid} runs again ({why}); pass --replace to rewrite it')
        pending.append((task, files, closure, key))
    if resume:
        log(f'resume: {len(skipped)} unit(s) complete for the same inputs and toolchains, skipped: '
            + (', '.join(t['task_id'] for t in skipped) or 'none'))
    by_id = {task['task_id']: (task, files, closure, key) for task, files, closure, key in pending}
    labels = [h['host_id'] for h in hosts]
    results, done, lock = {}, [], threading.Lock()
    finisher = ThreadPoolExecutor(max_workers=4)
    unit_started = time.monotonic()

    def finish(tid):
        task, _, closure, key = by_id[tid]
        outcome = results[tid]
        rows, lines, failed, written = finish_unit(base, task, closure, hosts, outcome, out, states[tid])
        if not failed:
            journal.add({'task_id': tid, 'key': key,
                         'compiler_sha256': {label: outcome[label][2].get('compiler_sha256') for label in labels},
                         'records': {str(p): _sha256(p) for p in written},
                         'finished': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
        lines.append(f'  private: {task["dir"] / "confirm"}/  done at {time.monotonic() - unit_started:.0f} s')
        log(f'{tid} ({task["compiled"]}): ' + ('FAILED' if failed else 'records written'))
        for line in lines:
            log(line)
        with lock:
            done.append((task, rows, failed))

    def deliver(task, label, value):
        tid = task['task_id']
        with lock:
            results.setdefault(tid, {})[label] = value
            complete = len(results[tid]) == len(labels)
        if complete:
            finisher.submit(finish, tid)

    handles = [pipeline.lock(task['dir']) for task, _, _, _ in pending]
    stage_root = runners.starts.state_dir() / 'confirm-stage' / uuid.uuid4().hex[:12]
    try:
        units = [(task, files) for task, files, _, _ in pending]
        threads = [threading.Thread(target=run_host, args=(h, units, stage_root, deliver, log)) for h in hosts]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        finisher.shutdown(wait=True)
    finally:
        for h in handles:
            h.close()
        shutil.rmtree(stage_root, ignore_errors=True)
    table, any_failed = [], False
    finished = {task['task_id'] for task, _, _ in done}
    for tid in by_id:
        if tid not in finished:
            log(f'{tid}: FAILED (not every host returned a result)')
            any_failed = True
    for task, rows, failed in done:
        any_failed |= failed
        for rva, row in rows.items():
            ok = all(v[0] == 'pass' for v in row.values())
            shown = ' '.join(f'{k}={v[0]}' + ('' if v[0] == 'pass' else f':{v[1]}') for k, v in row.items())
            table.append(f'  {task["task_id"]:<28} 0x{rva:<9x} {"REPRODUCED" if ok else "NOT REPRODUCED":<15} {shown}')
    if not out and not any_failed:
        check = subprocess.run([sys.executable, str(REPO / 'tools/check.py')], cwd=REPO, capture_output=True, text=True)
        log('check.py: ' + (check.stdout or check.stderr).strip().splitlines()[-1][:160])
        any_failed |= check.returncode != 0
    log('summary:')
    for line in sorted(table):
        log(line)
    for task in skipped:
        log(f'  {task["task_id"]:<28} skipped: its records stand from the journalled run (--resume)')
    log(f'time {time.monotonic() - started:.0f} s; {len(pending)} unit(s) run, {len(skipped)} skipped; '
        'no Boat machine used')
    return 1 if any_failed else 0
