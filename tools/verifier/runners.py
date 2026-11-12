#!/usr/bin/env python3
"""Verifier runners: where `attempt` and `confirm` compile and compare, chosen by a private config.

    python3 tools/verifier/runners.py status          # each configured host: toolchain, image, CPUs
    python3 tools/verifier/runners.py check-config    # parse and validate the config only

Three backends:

- `boat`: the Boat machines of tools/verifier/session (pipeline.Host); unchanged behaviour.
- `local`: this machine. The pinned toolchain under Wine (or natively on Windows), no network.
- `ssh`: a named host reached over key-based SSH with its own ssh_config; first use the
  maintainer's Windows PC with the pinned compiler run natively.

Local and ssh hosts keep no repository and need nothing installed but Python 3 (stdlib only), the
unpacked toolchain and, for comparing, the pinned image. Every run uploads a fresh minimal copy:
the unit's include closure, the comparator and the host scripts, a spec file and
`host_agent.py`; the command line carries only paths and fixed options (candidate source never
travels in a command), the host compiles and compares with tools/verifier/unit_build.py, the
caller fetches `work/<host id>/` and the run directory is removed.

The config is `.local/verifier/runners.json` of the main checkout (SR_RUNNERS_CONFIG overrides);
tools/verifier/runners.example.json is the tracked example. Without it, or with `"attempt":
"boat"`, everything behaves as before. A host is named in records only by its `host_id`, with
the OS, loader and compiler hashes it reports; private paths, user names and addresses stay in
the config.

Concurrency: each local or ssh host has `max_parallel` slots (file locks under
.local/verifier/runner-slots/); a run waits for a free slot, so Drafters queue instead of
overloading the host.
"""
import argparse
from contextlib import contextmanager
import fcntl
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import starts  # noqa: E402

SCHEMA = 1
BACKENDS = ('boat', 'local', 'ssh')
LOADERS = ('wine', 'native')
HOST_ID = re.compile(r'[a-z0-9][a-z0-9-]{1,39}')
# Everything on an ssh command line must survive PowerShell, cmd and POSIX shells unquoted.
SAFE_TOKEN = re.compile(r'[A-Za-z0-9_:/\\.+=@-]+')
RUN_NAME = re.compile(r'[a-z0-9][a-z0-9.-]{0,80}-[0-9a-f]{12}')
AGENT = HERE / 'host_agent.py'
DEFAULT_SLOT_WAIT = 3600
DEFAULT_TIMEOUT = 900


class RunnerError(Exception):
    pass


def config_path():
    configured = os.environ.get('SR_RUNNERS_CONFIG')
    return Path(configured) if configured else starts.state_dir() / 'runners.json'


def main_root():
    """The main checkout: relative local paths in the config are relative to it."""
    return starts.state_dir().parent.parent


def _local_path(value, root):
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(root) / path


def validate(raw, root=None):
    """The parsed config with defaults applied; raises RunnerError naming the first problem."""
    root = Path(root) if root else main_root()
    if not isinstance(raw, dict) or raw.get('runners_schema') != SCHEMA:
        raise RunnerError(f'runners config: runners_schema must be {SCHEMA}')
    hosts = raw.get('hosts')
    if not isinstance(hosts, dict) or not hosts:
        raise RunnerError('runners config: hosts must name at least one host')
    out, ids = {}, set()
    for name, h in hosts.items():
        where = f'runners config: hosts.{name}'
        if not isinstance(h, dict) or h.get('backend') not in BACKENDS:
            raise RunnerError(f'{where}.backend must be one of {", ".join(BACKENDS)}')
        backend = h['backend']
        host = dict(h, name=name)
        if backend == 'boat':
            out[name] = host
            continue
        hid = h.get('host_id')
        if not isinstance(hid, str) or not HOST_ID.fullmatch(hid):
            raise RunnerError(f'{where}.host_id must match {HOST_ID.pattern} (it appears in records)')
        if hid in ids:
            raise RunnerError(f'{where}.host_id {hid} is used twice')
        ids.add(hid)
        machine = h.get('machine')
        if not isinstance(machine, str) or not HOST_ID.fullmatch(machine):
            raise RunnerError(f'{where}.machine must name the physical machine ({HOST_ID.pattern}); two hosts on '
                              'one machine share it, and confirm needs two different machines')
        if h.get('loader') not in LOADERS:
            raise RunnerError(f'{where}.loader must be one of {", ".join(LOADERS)}')
        for key in ('msvc', 'work'):
            if not isinstance(h.get(key), str) or not h[key]:
                raise RunnerError(f'{where}.{key} is required')
        limit = h.get('max_parallel', 1)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 64:
            raise RunnerError(f'{where}.max_parallel must be an integer from 1 to 64')
        host['max_parallel'] = limit
        # Units per upload in a runner confirm: an ssh host pays several seconds of session setup per
        # transfer and command, so it gets units in batches; a local host gains nothing from batching.
        batch = h.get('batch', 2 * limit if backend == 'ssh' else 1)
        if not isinstance(batch, int) or isinstance(batch, bool) or not 1 <= batch <= 256:
            raise RunnerError(f'{where}.batch must be an integer from 1 to 256')
        host['batch'] = batch
        if backend == 'local':
            for key in ('msvc', 'work', 'wine_bin', 'wineprefix', 'image'):
                if h.get(key):
                    host[key] = str(_local_path(h[key], root))
            if h['loader'] == 'wine' and not host.get('wine_bin') and sys.platform == 'darwin':
                raise RunnerError(f'{where}.wine_bin is required for Wine on macOS')
        else:
            for key in ('ssh_host', 'ssh_config', 'image'):
                if not isinstance(h.get(key), str) or not h[key]:
                    raise RunnerError(f'{where}.{key} is required')
            host['ssh_config'] = str(_local_path(h['ssh_config'], root))
            python = h.get('python', ['python3'])
            if isinstance(python, str):
                python = [python]
            host['python'] = python
            for token in [h['ssh_host'], h['msvc'], h['image'], h['work'], *python]:
                if not isinstance(token, str) or not SAFE_TOKEN.fullmatch(token):
                    raise RunnerError(f'{where}: {token!r} needs quoting on the remote shell; use a path without '
                                      'spaces or shell characters (forward slashes work on Windows)')
        out[name] = host
    attempt = raw.get('attempt', 'boat')
    if attempt not in out:
        raise RunnerError(f'runners config: attempt names {attempt!r}, which is not a host')
    confirm = raw.get('confirm', [])
    if not isinstance(confirm, list) or any(c not in out for c in confirm):
        raise RunnerError('runners config: confirm must list configured hosts')
    if any(out[c]['backend'] == 'boat' for c in confirm):
        raise RunnerError('runners config: confirm lists runner hosts only; Boat confirms through the session')
    return {'attempt': attempt, 'confirm': confirm, 'hosts': out}


def load(path=None, root=None):
    """The validated config, or None when there is no config file (Boat behaviour)."""
    path = Path(path) if path else config_path()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text())
    except ValueError as exc:
        raise RunnerError(f'{path}: not JSON ({exc})') from None
    return validate(raw, root)


def legacy_image(root=None):
    """The image from .local/verifier/config.json, the setting the comparisons on this Mac use."""
    path = Path(root or main_root()) / '.local' / 'verifier' / 'config.json'
    try:
        return json.loads(path.read_text()).get('image')
    except (OSError, ValueError):
        return None


# ------------------------------------------------------------------ slots


def slot_dir():
    return starts.state_dir() / 'runner-slots'


@contextmanager
def slot(host_id, limit, wait=DEFAULT_SLOT_WAIT, log=None, directory=None, poll=0.5):
    """Hold one of `limit` slots of a host for the duration of the block; wait for one if all are taken.

    The locks are flock()ed files, released by the kernel if the holder dies, so a crashed
    attempt never blocks a host. Yields the seconds spent waiting.
    """
    directory = Path(directory) if directory else slot_dir()
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    said = False
    while True:
        for i in range(limit):
            handle = open(directory / f'{host_id}.{i}.lock', 'w')
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                handle.close()
                continue
            try:
                yield time.monotonic() - started
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
                handle.close()
            return
        if time.monotonic() - started > wait:
            raise RunnerError(f'{host_id}: all {limit} slots stayed busy for {wait} s')
        if not said and log:
            log(f'{host_id}: all {limit} slots busy; waiting for one')
            said = True
        time.sleep(poll)


@contextmanager
def slots(host_id, limit, want, wait=DEFAULT_SLOT_WAIT, log=None, directory=None, poll=0.5):
    """Hold one slot (waiting for it like `slot`) plus up to want-1 more that are free right now.

    Yields how many are held. Extra slots are taken only without waiting, so two callers that
    each want several can never hold part of a set and wait on each other.
    """
    directory = Path(directory) if directory else slot_dir()
    with slot(host_id, limit, wait=wait, log=log, directory=directory, poll=poll):
        extra = []
        try:
            for i in range(limit):
                if len(extra) >= want - 1:
                    break
                handle = open(directory / f'{host_id}.{i}.lock', 'w')
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    handle.close()
                    continue
                extra.append(handle)
            yield 1 + len(extra)
        finally:
            for handle in extra:
                fcntl.flock(handle, fcntl.LOCK_UN)
                handle.close()


def slots_busy(host_id, limit, directory=None):
    """How many of a host's slots are held right now."""
    directory = Path(directory) if directory else slot_dir()
    busy = 0
    for i in range(limit):
        path = directory / f'{host_id}.{i}.lock'
        if not path.exists():
            continue
        with open(path, 'w') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(handle, fcntl.LOCK_UN)
            except OSError:
                busy += 1
    return busy


# ------------------------------------------------------------------ transports


class LocalTransport:
    """This machine: copies and subprocesses, with the host's Wine settings in the environment."""

    def __init__(self, host):
        self.host = host

    def env(self):
        env = dict(os.environ)
        if self.host.get('wine_bin'):
            env['PATH'] = self.host['wine_bin'] + os.pathsep + env.get('PATH', '')
        if self.host.get('wineprefix'):
            env['WINEPREFIX'] = self.host['wineprefix']
        env.setdefault('WINEDEBUG', '-all')
        # Prep markers live with the host's work, so a cached toolchain check is per host and boot.
        env['SR_PREP_MARKER_DIR'] = str(Path(self.host['work']) / '.prep')
        return env

    def prepare(self):
        Path(self.host['work']).mkdir(parents=True, exist_ok=True, mode=0o700)
        (Path(self.host['work']) / '.prep').mkdir(exist_ok=True)

    def put(self, paths, remote_dir):
        for path in paths:
            shutil.copyfile(path, Path(remote_dir) / Path(path).name)

    def get(self, remote_file, local_file):
        shutil.copyfile(remote_file, local_file)

    def run(self, argv, timeout):
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, env=self.env(), timeout=timeout)
        except subprocess.TimeoutExpired:
            return 124, '', 'timeout'
        return proc.returncode, proc.stdout, proc.stderr

    def join(self, *parts):
        return str(Path(*parts))


class SshTransport:
    """A host reached with `ssh -F <config> <host>`; files go by scp, never in a command line."""

    def __init__(self, host):
        self.host = host
        # One multiplexed connection: a fresh session to Windows OpenSSH costs seconds, and a run
        # makes five. The socket path stays short (sockets are limited to about 100 bytes); ssh
        # creates it owner-only.
        self.base = ['-F', host['ssh_config'], '-o', 'BatchMode=yes', '-o', 'ControlMaster=auto',
                     '-o', f'ControlPath={host.get("control_dir", "/tmp")}/sr-cm-%C', '-o', 'ControlPersist=120']
        self.prepared = False
        self._lock = threading.Lock()

    def prepare(self):
        """Create the work root once (scp needs the parent of a run directory to exist).

        `mkdir <path>` with backslashes means the same in PowerShell, cmd and (as one odd name)
        nowhere else that matters; an existing directory makes it fail harmlessly.
        """
        with self._lock:
            if self.prepared:
                return
            self.run(['mkdir', self.host['work'].replace('/', '\\') if ':' in self.host['work']
                      else self.host['work']], 60)
            self.prepared = True

    def _scp(self, *args, timeout=900):
        proc = subprocess.run(['scp', *self.base, '-q', *args], capture_output=True, text=True,
                              timeout=timeout, env=dict(os.environ, COPYFILE_DISABLE='1'))
        if proc.returncode != 0:
            raise RunnerError(f'{self.host["host_id"]}: scp failed (exit {proc.returncode}): '
                              f'{(proc.stderr or "").strip()[-200:]}')

    def put(self, paths, remote_dir):
        """One scp for all files: per-file round trips dominate on Windows OpenSSH."""
        self._scp(*[str(p) for p in paths], f'{self.host["ssh_host"]}:{remote_dir}/')

    def get(self, remote_file, local_file):
        self._scp(f'{self.host["ssh_host"]}:{remote_file}', str(local_file))

    def run(self, argv, timeout):
        for token in argv:
            if not SAFE_TOKEN.fullmatch(token):
                raise RunnerError(f'refusing to send {token!r} on an ssh command line')
        try:
            proc = subprocess.run(['ssh', *self.base, self.host['ssh_host'], ' '.join(argv)],
                                  capture_output=True, text=True, timeout=timeout + 30)
        except subprocess.TimeoutExpired:
            return 124, '', 'timeout'
        return proc.returncode, proc.stdout, proc.stderr

    def join(self, *parts):
        return '/'.join(p.rstrip('/') for p in parts)


def transport_for(host):
    return LocalTransport(host) if host['backend'] == 'local' else SshTransport(host)


# ------------------------------------------------------------------ hosts


def describe(host):
    """One line naming a host the way records may: id, machine, backend and loader, no paths."""
    return f'{host["host_id"]} (machine {host["machine"]}, {host["backend"]}, {host["loader"]})'


class AgentHost:
    """pipeline.Host's interface (run, fetch) for a local or ssh host, one fresh copy per run."""

    def __init__(self, host, task, label=None, transport=None, log=None, timeout=DEFAULT_TIMEOUT, fresh_prep=False):
        self.host, self.task = host, task
        # A run whose host facts go into a record hashes the toolchain itself instead of trusting
        # the per-boot marker, so the hashes the record names were measured during that run.
        self.fresh_prep = fresh_prep
        self.label = label or host['host_id']
        self.machine = host['host_id']
        self.transport = transport or transport_for(host)
        self.log = log or (lambda msg: None)
        self.timeout = timeout
        self.timings = {}
        self.waited = 0.0
        self.facts = None
        self._run = None

    def _python(self):
        return list(self.host['python']) if self.host['backend'] == 'ssh' else [sys.executable]

    def _bundle(self, files, stage_root, name):
        """(tar, agent copy) to upload: the repository copy with its spec, and host_agent.py."""
        import pipeline
        stage = Path(stage_root)
        stage.mkdir(parents=True, exist_ok=True)
        spec = pipeline.unit_spec(self.task, files, self.label)
        if self.fresh_prep:
            spec['fresh_prep'] = True
        return make_bundle(stage, name, {f'repo/{rel}': src for rel, src in files.items()},
                           {'repo/.unit/spec.json': json.dumps(spec, sort_keys=True).encode()})

    def run(self, files, stage_root, fresh=True, timeout=None):
        """(exit code, sanitized stdout) of unit_build.py on this host; always a fresh copy."""
        timeout = timeout or self.timeout
        name = f'{self.task["task_id"]}-{uuid.uuid4().hex[:12]}'
        start = time.monotonic()
        paths = self._bundle(files, stage_root, name)
        code = 2
        try:
            with slot(self.host['host_id'], self.host['max_parallel'], log=self.log) as waited:
                self.waited += waited
                self.transport.prepare()
                self.transport.put(paths, self.host['work'])
                self._run = name
                self.timings['upload'] = self.timings.get('upload', 0) + time.monotonic() - start - waited
                t0 = time.monotonic()
                code, out, err = self.transport.run(self._agent(name, 'run', '--bundle', self._remote(name + '.tar'),
                                                                '--msvc', self.host['msvc'], '--image',
                                                                self.host['image'], '--loader', self.host['loader'],
                                                                '--label', self.label), timeout)
                self.timings['run'] = self.timings.get('run', 0) + time.monotonic() - t0
        finally:
            for path in paths:
                Path(path).unlink(missing_ok=True)
        if code == 124:
            self.clean()
            raise RunnerError(f'{self.label}: run timed out after {timeout}s')
        return code, out

    def _remote(self, *parts):
        return self.transport.join(self.host['work'], *parts)

    def _agent(self, name, command, *args):
        # -I: the agent runs from the work directory, where an uploaded or left-over module named
        # like a standard one must not be imported in its place.
        return self._python() + ['-I', self._remote(name + '.py'), command, '--run', self._remote(name), *args]

    def fetch(self, dest):
        """Unpack work/<label> of the last run into `dest` (replaced), then remove the run on the host."""
        if self._run is None:
            raise RunnerError(f'{self.label}: nothing to fetch')
        start = time.monotonic()
        dest = Path(dest)
        part = dest.with_name(dest.name + '.part')
        shutil.rmtree(part, ignore_errors=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        archive = dest.with_name(dest.name + '.out.tar')
        try:
            self.transport.get(self._remote(self._run + '.out.tar'), archive)
            unpack(archive, part)
        except (OSError, RunnerError, tarfile.TarError):
            shutil.rmtree(part, ignore_errors=True)
            self.clean()
            raise RunnerError(f'{self.label}: no results to fetch (the run wrote no output archive)') from None
        finally:
            archive.unlink(missing_ok=True)
        shutil.rmtree(dest, ignore_errors=True)
        part.rename(dest)
        self.timings['fetch'] = time.monotonic() - start
        try:
            self.facts = json.loads((dest / 'result.json').read_text()).get('host_facts')
        except (OSError, ValueError):
            self.facts = None
        self.clean()
        return dest

    def clean(self):
        """Remove the last run's files on the host; a failure leaves them to the agent's pruning."""
        if self._run is None:
            return
        try:
            self.transport.run(self._agent(self._run, 'clean'), 120)
        except (RunnerError, OSError, subprocess.SubprocessError):
            pass
        self._run = None


class BatchHost:
    """Several units on one local or ssh host in one upload, one agent command and one fetch.

    Each unit is still a fresh copy checked against its own spec and compiled and compared by
    unit_build.py on its own, with the same host facts per unit as AgentHost gives; only the
    transport is shared, which on an ssh host saves four sessions per unit.
    """

    def __init__(self, host, transport=None, log=None, timeout=DEFAULT_TIMEOUT, fresh_prep=False):
        self.host = host
        self.fresh_prep = fresh_prep
        self.label = host['host_id']
        self.transport = transport or transport_for(host)
        self.log = log or (lambda msg: None)
        self.timeout = timeout
        self.timings = {}

    def _remote(self, *parts):
        return self.transport.join(self.host['work'], *parts)

    def _python(self):
        return list(self.host['python']) if self.host['backend'] == 'ssh' else [sys.executable]

    def run(self, units, stage_root, dests):
        """{task id: (exit code, unit directory, host facts) or RunnerError} for `units`, a list of
        (task, files); unit results are unpacked into dests[task id] (replaced)."""
        import pipeline
        ids = [task['task_id'] for task, _ in units]
        if len(set(ids)) != len(ids):
            raise RunnerError(f'{self.label}: a unit is listed twice in one batch')
        name = f'batch-{uuid.uuid4().hex[:12]}'
        stage = Path(stage_root)
        stage.mkdir(parents=True, exist_ok=True)
        files, blobs = {}, {'units.json': json.dumps(ids).encode()}
        for task, unit_files in units:
            spec = pipeline.unit_spec(task, unit_files, self.label)
            if self.fresh_prep:
                spec['fresh_prep'] = True
            files.update({f'{task["task_id"]}/repo/{rel}': src for rel, src in unit_files.items()})
            blobs[f'{task["task_id"]}/repo/.unit/spec.json'] = json.dumps(spec, sort_keys=True).encode()
        start = time.monotonic()
        paths = make_bundle(stage, name, files, blobs)
        launched = False
        try:
            self.transport.prepare()
            launched = True
            self.transport.put(paths, self.host['work'])
            self.timings['upload'] = self.timings.get('upload', 0) + time.monotonic() - start
            # Slots cover only the compile and compare, so another batch's transfer overlaps them.
            with slots(self.host['host_id'], self.host['max_parallel'], self.host['max_parallel'],
                       log=self.log) as jobs:
                t0 = time.monotonic()
                # A batch runs ceil(units / jobs) units one after another per job.
                timeout = self.timeout * -(-len(units) // jobs)
                code, out, err = self.transport.run(
                    self._python() + ['-I', self._remote(name + '.py'), 'batch', '--run', self._remote(name),
                                      '--bundle', self._remote(name + '.tar'), '--msvc', self.host['msvc'],
                                      '--image', self.host['image'], '--loader', self.host['loader'],
                                      '--label', self.label, '--jobs', str(jobs)], timeout)
                self.timings['run'] = self.timings.get('run', 0) + time.monotonic() - t0
            if code != 0:
                raise RunnerError(f'{self.label}: batch agent exit {code}' + (' (timeout)' if code == 124 else '')
                                  + f' {(out or "").strip()[-200:]}')
            t0 = time.monotonic()
            archive = stage / f'{name}.out.tar'
            part = stage / f'{name}.out'
            try:
                self.transport.get(self._remote(name + '.out.tar'), archive)
                unpack(archive, part)
            except (OSError, RunnerError, tarfile.TarError):
                shutil.rmtree(part, ignore_errors=True)
                raise RunnerError(f'{self.label}: no batch results to fetch') from None
            finally:
                archive.unlink(missing_ok=True)
            self.timings['fetch'] = self.timings.get('fetch', 0) + time.monotonic() - t0
            results = {}
            for tid in ids:
                try:
                    agent = json.loads((part / f'{tid}.agent.json').read_text())
                except (OSError, ValueError):
                    results[tid] = RunnerError(f'{self.label}: no result for {tid} in the batch')
                    continue
                dest = Path(dests[tid])
                shutil.rmtree(dest, ignore_errors=True)
                dest.parent.mkdir(parents=True, exist_ok=True)
                src = part / tid
                if src.is_dir():
                    src.rename(dest)
                else:
                    dest.mkdir()
                try:
                    facts = json.loads((dest / 'result.json').read_text()).get('host_facts')
                except (OSError, ValueError):
                    facts = None
                results[tid] = (agent.get('exit'), dest, facts)
            shutil.rmtree(part, ignore_errors=True)
            return results
        finally:
            for path in paths:
                Path(path).unlink(missing_ok=True)
            if launched:
                try:
                    self.transport.run(self._python() + ['-I', self._remote(name + '.py'), 'clean', '--run',
                                                         self._remote(name)], 120)
                except (RunnerError, OSError, subprocess.SubprocessError):
                    pass


def make_bundle(stage, name, files, blobs=None):
    """Write <stage>/<name>.tar (files {archive name: local path} and blobs {archive name: bytes})
    and <stage>/<name>.py (the agent); returns both paths.

    xz-compressed (readers detect it): every unit of a batch carries the same tools and symbol map,
    which xz's large window stores once, and over a slow link to an ssh host the transfer, not the
    compile, is the largest cost of a run."""
    archive = Path(stage) / f'{name}.tar'
    with tarfile.open(archive, 'w:xz', format=tarfile.PAX_FORMAT) as tar:
        for arc, src in sorted(files.items()):
            tar.add(str(src), arcname=arc, recursive=False)
        for arc, data in sorted((blobs or {}).items()):
            info = tarfile.TarInfo(arc)
            info.size, info.mode, info.mtime = len(data), 0o644, int(time.time())
            tar.addfile(info, io.BytesIO(data))
    agent = Path(stage) / f'{name}.py'
    shutil.copyfile(AGENT, agent)
    return [archive, agent]


def unpack(archive, dest):
    """Extract a results archive with tarfile's `data` filter: no links out, no absolute paths."""
    Path(dest).mkdir(parents=True)
    with tarfile.open(archive) as tar:
        tar.extractall(dest, filter='data')


def probe(host, transport=None, timeout=300):
    """{'toolchain', 'image', 'cpus', 'os', 'loader', 'python', 'running'} as the host reports it."""
    transport = transport or transport_for(host)
    name = f'probe-{uuid.uuid4().hex[:12]}'
    python = list(host['python']) if host['backend'] == 'ssh' else [sys.executable]
    remote = transport.join(host['work'], name)
    with tempfile.TemporaryDirectory() as tmp:
        paths = make_bundle(tmp, name, {'pinned.sha256': HERE / 'pinned.sha256',
                                        'target.json': REPO / 'builds' / 'target.json'})
        transport.prepare()
        transport.put(paths, host['work'])
    agent = [*python, '-I', remote + '.py']
    try:
        code, out, err = transport.run(agent + ['probe', '--run', remote, '--bundle', remote + '.tar', '--msvc',
                                                host['msvc'], '--image', host['image'], '--loader', host['loader']],
                                       timeout)
    finally:
        transport.run(agent + ['clean', '--run', remote], 120)
    fields = dict(line.split('=', 1) for line in out.splitlines() if '=' in line)
    if code != 0 or 'TOOLCHAIN' not in fields:
        raise RunnerError(f'{host["host_id"]}: probe gave no result (exit {code}) {(err or "").strip()[-200:]}')
    return {'toolchain': fields['TOOLCHAIN'], 'image': fields.get('IMAGE'),
            'cpus': int(fields['CPUS']) if fields.get('CPUS', '').isdigit() else None,
            'os': fields.get('OS'), 'loader': fields.get('LOADER'), 'python': fields.get('PYTHON'),
            'running': int(fields['RUNNING']) if fields.get('RUNNING', '').isdigit() else None,
            'compiler_sha256': json.loads(fields['COMPILER']) if fields.get('COMPILER') else {}}


# ------------------------------------------------------------------ selection


def for_attempt(config=None):
    """The host dict attempts run on, or None for the Boat path (no config, or attempt = a boat host)."""
    config = config if config is not None else load()
    if config is None:
        return None
    host = config['hosts'][config['attempt']]
    if host['backend'] == 'boat':
        return None
    return with_image(host)


def with_image(host):
    if host['backend'] == 'local' and not host.get('image'):
        image = legacy_image()
        if not image:
            raise RunnerError(f'{host["host_id"]}: no image (runners.json "image" or .local/verifier/config.json)')
        host = dict(host, image=image)
    if not host.get('image'):
        raise RunnerError(f'{host["host_id"]}: no image configured')
    return host


def for_confirm(config=None):
    """The confirm hosts (at least two), checked for independence; None when no runner confirm is set."""
    config = config if config is not None else load()
    if config is None or not config['confirm']:
        return None
    hosts = [with_image(config['hosts'][name]) for name in config['confirm']]
    problem = independence_problem(hosts)
    if problem:
        raise RunnerError(f'runners config: confirm hosts are not independent: {problem}')
    return hosts


def independence_problem(hosts, facts=None):
    """Why these compile hosts do not meet the independence requirement, or None.

    Two compile hosts at least, on two different machines, with two different loaders (one runs
    the pinned compiler natively, one under Wine). `facts` ({host id: host_facts}) are what the
    hosts reported after compiling; when given, their loaders and operating systems are what is
    checked: each host must report the loader its config names, a `native` host must report
    Windows, and the hosts must report at least two operating systems, so a second Wine host
    relabelled `native`, or two hosts on one OS, do not pass on the config's word alone.
    """
    if len(hosts) < 2:
        return 'needs at least two compile hosts'
    if len({h['machine'] for h in hosts}) < 2:
        return 'all compile hosts are on one machine'
    if facts is not None:
        loaders = {(facts.get(h['host_id']) or {}).get('loader') for h in hosts}
    else:
        loaders = {h['loader'] for h in hosts}
    if len(loaders) < 2 or None in loaders:
        return 'the compile hosts do not use two different loaders (native and wine)'
    if facts is not None:
        for h in hosts:
            f = facts.get(h['host_id']) or {}
            if f.get('loader') != h['loader']:
                return f'{h["host_id"]} reported loader {f.get("loader")!r}, its config names {h["loader"]!r}'
            if f.get('loader') == 'native' and f.get('os') != 'windows':
                return f'{h["host_id"]} reported a native compile on {f.get("os")!r}, not windows'
        systems = {(facts.get(h['host_id']) or {}).get('os') for h in hosts}
        if len(systems) < 2 or None in systems:
            return 'the compile hosts do not report two different operating systems'
    return None


# ------------------------------------------------------------------ command line


def status(config=None, log=print, probe_fn=probe):
    config = config if config is not None else load()
    if config is None:
        log(f'runners: no config at {config_path()}; attempt and confirm use Boat')
        return 0
    log(f'runners: attempt on {config["attempt"]}; confirm on {", ".join(config["confirm"]) or "(Boat session)"}')
    bad = 0
    for name, host in config['hosts'].items():
        if host['backend'] == 'boat':
            log(f'  {name}: boat (tools/verifier/session status)')
            continue
        busy = slots_busy(host['host_id'], host['max_parallel'])
        try:
            p = probe_fn(with_image(host))
        except (RunnerError, OSError, subprocess.SubprocessError) as exc:
            log(f'  {name}: {describe(host)}: unreachable or broken: {exc}')
            bad += 1
            continue
        ok = p['toolchain'] == 'ok' and p['image'] == 'ok' and p['loader'] == host['loader']
        bad += not ok
        log(f'  {name}: {describe(host)}: toolchain {p["toolchain"]} (pinned.sha256), image {p["image"]} '
            f'(builds/target.json), {p["os"]}, python {p["python"]}, {p["cpus"]} CPUs, slots {busy}/'
            f'{host["max_parallel"]} busy, runs on host {p["running"]}')
    return 1 if bad else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('command', choices=('status', 'check-config'))
    a = p.parse_args()
    try:
        if a.command == 'check-config':
            config = load()
            if config is None:
                print(f'no config at {config_path()} (Boat behaviour)')
                return 0
            print(f'ok: attempt on {config["attempt"]}; confirm on {", ".join(config["confirm"]) or "(Boat session)"}; '
                  + '; '.join(describe(h) if h['backend'] != 'boat' else f'{n} boat'
                              for n, h in config['hosts'].items()))
            return 0
        return status()
    except RunnerError as exc:
        print(f'runners: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
