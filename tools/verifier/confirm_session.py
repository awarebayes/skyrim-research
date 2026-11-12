"""`confirm` in session mode: compile on session machines A and B, compare on A, B and this Mac.

No machine is created, forked, resumed or stopped here; the session (tools/verifier/session)
owns the machines. Many task directories may be confirmed in one invocation: units run in
parallel up to the machines' CPU count, each unit on both machines at once, and one table is
printed at the end. Record assembly, notes, the build block and the Mac comparison are the
fork path's own functions from tools/verifier/confirm, passed in as `base`.

With `out` set, records are written under `<out>/<build id>/` instead of `reports/`: each is
assembled and validated by match_record.py under a temporary `reports/<build id>/.scratch-*/`
path (the validator accepts only record paths below reports/) and then moved out, so a scratch
run never leaves a record in the published tree.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import threading
import time
import uuid

import boatctl
import pipeline
import vsession
from pipeline import REPO, PipelineError

MAC_LABEL = 'macos-arm64-local'
SESSION_NOTE = (
    'independence: separate-machine. The two Boat compile hosts are separately installed machines: each was '
    'created from scratch and ran tools/verifier/setup_boat_machine.sh itself (neither is a disk fork of the '
    'other), so the pair also checks the toolchain install; both use the same pinned recipe, Ubuntu image and '
    'cloud provider. Each host checked its compiler binaries against pinned.sha256 and its image against '
    'builds/target.json before compiling. The macOS host only compared; it did not compile.')


def session_notes(base, task, recipe):
    notes = [n for n in base.notes(task, recipe) if not n.startswith(('Host independence', 'independence:'))]
    return notes[:1] + [SESSION_NOTE] + notes[1:]


def record_path(task, fn, out):
    name = f'0x{fn["rva"]:x}.json'
    return (Path(out) / task['build_id'] / name) if out else (REPO / 'reports' / task['build_id'] / name)


def prepare(base, task_dir, replace, out):
    task = pipeline.load_task(task_dir)
    files, closure = pipeline.unit_manifest(task)
    base.preflight(task, closure, True)
    for fn in task['functions']:
        path = record_path(task, fn, out)
        if path.exists() and not replace:
            raise PipelineError(f'{path} exists; pass --replace to rewrite it from new runs')
    return task, files, closure


def write_records(base, task, closure, recipe, runs, build_path, out, notes=None, reproduction=None):
    lines, failed = [], False
    reproduction = reproduction or base.reproduction
    scratch = None
    if out:
        scratch = REPO / 'reports' / task['build_id'] / f'.scratch-{uuid.uuid4().hex[:12]}'
    try:
        for fn in task['functions']:
            final = record_path(task, fn, out)
            target = (scratch / final.name) if scratch else final
            fid = f'{task["build_id"]}-0x{fn["rva"]:x}'
            cmd = [sys.executable, str(base.HERE / 'match_record.py'), '--function-id', fid, '--unit', *closure,
                   '--compiled', task['compiled'], '--recipe', task['recipe'], '--symbols', task['symbols_repo'],
                   '--reproduction', reproduction(task, fn, closure, recipe), '--build', str(build_path),
                   '--out', str(target.relative_to(REPO))]
            if fn.get('family_metadata'):
                cmd += ['--family-metadata', json.dumps(fn['family_metadata'], sort_keys=True)]
            for compiled_on, compared_on, report in runs[fn['rva']]:
                cmd += ['--run', compiled_on, compared_on, str(report)]
            for note in (notes if notes is not None else session_notes(base, task, recipe)):
                cmd += ['--note', note]
            proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
            ok = proc.returncode == 0
            if ok and scratch:
                final.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(final))
            shown = final.relative_to(REPO) if final.is_relative_to(REPO) else final
            lines.append(f'  record {shown}: ' + ('written' if ok else 'REFUSED '
                                                    + (proc.stderr or proc.stdout).strip()[-200:]))
            failed |= not ok
    finally:
        if scratch:
            shutil.rmtree(scratch, ignore_errors=True)
    return lines, failed


def confirm_unit(base, task, files, closure, hosts, replace, out):
    """(rows, lines, failed) for one unit; removes its task files from both machines afterwards."""
    started = time.monotonic()
    handle = pipeline.lock(task['dir'])  # held until the unit is done
    recipe = json.loads((REPO / task['recipe']).read_text())
    config = pipeline.load_config(task['dir'])
    out_root = task['dir'] / 'confirm'
    stage = task['dir'] / '.confirm-stage'
    remote_dir = f'{boatctl.REMOTE_HOME}/tasks/{task["task_id"]}-confirm'
    lines, rows, failed = [], {}, True
    workers = {label: pipeline.Host(machine, label, remote_dir, task, local_image=config.get('image'))
               for _, label, machine in hosts}
    try:
        outcome = {}

        def work(label, host):
            try:
                code, _ = host.run(files, stage / label, fresh=True)
                outcome[label] = (code, host.fetch(out_root / label))
            except Exception as exc:  # reported below; cleanup runs either way
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
        runs = {fn['rva']: [] for fn in task['functions']}
        for fn in task['functions']:
            rows[fn['rva']] = {}
        for label in workers:
            host_dir = outcome[label][1]
            for fn in task['functions']:
                remote_report = host_dir / f'0x{fn["rva"]:x}' / 'report.json'
                rows[fn['rva']][label] = base.result_of(remote_report)
                runs[fn['rva']].append((label, label, remote_report))
                _, mac_report = base.mac_compare(task, fn, host_dir, out_root / 'mac' / label / f'0x{fn["rva"]:x}')
                rows[fn['rva']][f'mac<-{label}'] = base.result_of(mac_report)
                runs[fn['rva']].append((label, MAC_LABEL, mac_report))
        failed = any(v[0] != 'pass' for row in rows.values() for v in row.values())
        if failed:
            lines.append('  no record written: every run must pass; a pass that fails to reproduce is escalated')
        else:
            build_path = out_root / 'build.json'
            build_path.write_text(json.dumps(base.build_block(task, {label: outcome[label][1] for label in workers}),
                                             indent=2) + '\n')
            more, failed = write_records(base, task, closure, recipe, runs, build_path, out)
            lines += more
    except (PipelineError, boatctl.BoatError) as exc:
        lines.append(f'  ERROR {exc}')
        failed = True
    finally:
        for label, host in workers.items():
            try:
                boatctl.execute(host.machine, f'rm -rf {shlex.quote(remote_dir)}', 60)
            except boatctl.BoatError:
                lines.append(f'  warning: could not remove {remote_dir} on {label}')
        wall = time.monotonic() - started
        # Both machines are busy for the unit's wall time; idle time is booked by `session down`.
        pipeline.record_cost(task, 'confirm', 2 * wall, wall)
        lines.append(f'  private: {out_root}/  time {wall:.0f} s')
        handle.close()
    return rows, lines, failed


def run(base, task_dirs, replace=False, out=None, log=print):
    started = time.monotonic()
    hosts = vsession.hosts()
    if hosts is None:
        raise PipelineError('no verifier session is up: an Engineer runs `tools/verifier/session up`, '
                            'or pass --fork for the old per-unit fork (one extra start per unit)')
    counters_before = vsession.starts.parse(json.loads(boatctl.cli('limits', '--json').stdout))
    session = vsession.active()
    cpus = [e.get('cpus') for e in session['machines'].values() if e.get('cpus')]
    parallel = max(1, min(cpus) if cpus else 4)
    prepared = []
    for d in task_dirs:
        prepared.append(prepare(base, d, replace, out))
    ids = [t['task_id'] for t, _, _ in prepared]
    if len(set(ids)) != len(ids):
        raise PipelineError('a task id is listed twice')
    log(f'confirm: {len(prepared)} unit(s) on session machines '
        + ', '.join(f'{k.upper()}={label}' for k, label, _ in hosts) + f'; up to {parallel} in parallel; no starts')
    with ThreadPoolExecutor(max_workers=min(parallel, len(prepared))) as pool:
        results = list(pool.map(lambda p: (p[0], confirm_unit(base, *p, hosts, replace, out)), prepared))
    table, any_failed = [], False
    for task, (rows, lines, failed) in results:
        any_failed |= failed
        log(f'{task["task_id"]} ({task["compiled"]}): ' + ('FAILED' if failed else 'records written'))
        for line in lines:
            log(line)
        for rva, row in rows.items():
            ok = all(v[0] == 'pass' for v in row.values())
            shown = ' '.join(f'{k.replace("boat-verifier-", "")}={v[0]}' + ('' if v[0] == 'pass' else f':{v[1]}')
                             for k, v in row.items())
            table.append(f'  {task["task_id"]:<28} 0x{rva:<9x} {"REPRODUCED" if ok else "NOT REPRODUCED":<15} {shown}')
    if not out and not any_failed:
        check = subprocess.run([sys.executable, str(REPO / 'tools/check.py')], cwd=REPO, capture_output=True, text=True)
        log('check.py: ' + (check.stdout or check.stderr).strip().splitlines()[-1][:160])
        any_failed |= check.returncode != 0
    counters_after = vsession.starts.parse(json.loads(boatctl.cli('limits', '--json').stdout))
    log('summary:')
    for line in table:
        log(line)
    log(f'starts: day used {counters_before["day"]["used"]} -> {counters_after["day"]["used"]} '
        '(this command makes none; other sessions may)')
    log(f'time {time.monotonic() - started:.0f} s; machines left running for the session')
    return 1 if any_failed else 0
