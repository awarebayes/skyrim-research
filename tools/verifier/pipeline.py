"""Shared logic of `tools/verifier/attempt` and `tools/verifier/confirm`.

A task directory is private (inside a `.local/` directory) and holds `task.json`:

    {"task_id": "first-function",                       # default: the directory name
     "build_id": "sse-steam-1-7-104",                   # must equal builds/target.json
     "compiled": "reconstruction/<area>/<Class>.cpp",   # the rest of the unit is derived
     "recipe": "reconstruction/recipes/<recipe>.json",  # or "recipe_name": "<recipe>"
     "symbols": "symbols.json",                         # relative to the task dir; a path starting
                                                        # with reports/ is a repository file
     "functions": [{"rva": "0x73ad90", "size": 84, "symbol": "?Name@Class@@..."}],
     "max_attempts": 12,                                # optional budget, enforced by attempt
     "record_notes": ["..."]}                           # optional, confirm adds them to records

Sources are read from the checkout the command runs from, never from the
task directory. Only these files go to a verifier host: the comparator and its helpers, the
toolchain pin, the target manifest, the unit's include closure, the recipe and the symbol map.
"""
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from source_digest import include_closure, recipe_flag_problem  # noqa: E402
import boatctl  # noqa: E402
import disasm  # noqa: E402
import vsession  # noqa: E402
try:
    import cost_hooks  # noqa: E402  (optional: the cost ledger may not be installed)
except ImportError:
    cost_hooks = None

TOOL_FILES = ('tools/compare.py', 'tools/pecoff.py', 'tools/source_digest.py', 'tools/verifier/verify_function.py',
              'tools/verifier/unit_build.py', 'tools/verifier/pinned.sha256', 'builds/target.json')
TASK_ID = re.compile(r'[a-z0-9][a-z0-9.-]{0,55}')
PRIVATE_SYMBOLS = 'task/symbols.json'
DEFAULT_TTL = int(os.environ.get('SR_VERIFIER_TTL', '3600'))
# Extend the deadline when less than this remains, so an attempt never races the auto-stop.
MIN_LEFT = 900
EXIT_IMAGE, EXIT_SYNC = 42, 43


class PipelineError(Exception):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def private_root(path):
    """The `.local` directory that contains `path`; private outputs may only go below one."""
    path = Path(path).resolve()
    for parent in [path, *path.parents]:
        if parent.name == '.local':
            return parent
    raise PipelineError(f'{path} is not inside a .local/ directory; task directories are private')


def load_config(task_dir, repo=REPO):
    """Private per-host settings: {"image": "<local SkyrimSE.exe>", "objdump": "<llvm-objdump>"}."""
    for root in (private_root(task_dir), Path(repo) / '.local'):
        path = root / 'verifier' / 'config.json'
        if path.is_file():
            return json.loads(path.read_text())
    return {}


def cost_targets(task):
    """Functions a verifier run spends compute on, as '<build id>:0x<rva>' for the cost ledger."""
    return [f'{task["build_id"]}:0x{fn["rva"]:x}' for fn in task['functions']]


def record_cost(task, stage, seconds, wall):
    """Queue Boat usage for the cost ledger when its hook module is installed; never fails a run."""
    if cost_hooks is None or seconds is None:
        return
    try:
        cost_hooks.record_boat(task['task_id'], stage, seconds, wall, cost_targets(task))
    except Exception:  # cost bookkeeping must never change a verifier result
        pass
    # Session overhead booked by `session down` excludes what was attributed here.
    vsession.note_attributed(seconds, task['task_id'], stage)


def parse_int(value, what):
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]+|[0-9]+', value):
        return int(value, 0)
    raise PipelineError(f'task.json: {what} must be an integer or 0x-hex string')


def main_checkout(repo=REPO):
    """The primary checkout of this repository; a git worktree has no `.local/` of its own."""
    out = subprocess.run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'], cwd=repo,
                         capture_output=True, text=True)
    return Path(out.stdout.strip()).parent if out.returncode == 0 and out.stdout.strip() else Path(repo)


def resolve_task_dir(arg, repo=REPO):
    """`arg` as given, else relative to the main checkout, so `.local/tasks/<id>` works from a worktree."""
    path = Path(arg)
    if path.is_dir() or path.is_absolute():
        return path.resolve()
    return (main_checkout(repo) / path).resolve()


def load_task(task_dir, repo=REPO):
    task_dir = resolve_task_dir(task_dir, repo)
    private_root(task_dir)
    try:
        raw = json.loads((task_dir / 'task.json').read_text())
    except (OSError, ValueError) as exc:
        raise PipelineError(f'cannot read {task_dir / "task.json"}: {exc}') from None
    target = json.loads((Path(repo) / 'builds/target.json').read_text())
    task_id = raw.get('task_id', task_dir.name)
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise PipelineError('task.json: task_id must match [a-z0-9][a-z0-9.-]* (no underscores)')
    if raw.get('build_id') != target.get('build_id'):
        raise PipelineError(f'task.json: build_id {raw.get("build_id")!r} is not the pinned target '
                            f'{target.get("build_id")!r}')
    compiled = raw.get('compiled')
    if not isinstance(compiled, str) or not compiled.startswith('reconstruction/') or not compiled.endswith('.cpp'):
        raise PipelineError('task.json: compiled must be reconstruction/<area>/<Class>.cpp')
    recipe = raw.get('recipe') or (f'reconstruction/recipes/{raw["recipe_name"]}.json' if raw.get('recipe_name') else None)
    if not isinstance(recipe, str) or not recipe.startswith('reconstruction/recipes/'):
        raise PipelineError('task.json: recipe must be reconstruction/recipes/<name>.json')
    symbols = raw.get('symbols', 'symbols.json')
    if not isinstance(symbols, str):
        raise PipelineError('task.json: symbols must be a path')
    public_symbols = symbols.startswith('reports/')
    symbols_path = (Path(repo) / symbols) if public_symbols else (task_dir / symbols)
    if not symbols_path.is_file():
        raise PipelineError(f'symbol map not found: {symbols_path}')
    functions = []
    for i, fn in enumerate(raw.get('functions') or []):
        if not isinstance(fn, dict) or not isinstance(fn.get('symbol'), str) or not fn['symbol']:
            raise PipelineError(f'task.json: functions[{i}] needs rva, size and symbol')
        functions.append({'rva': parse_int(fn.get('rva'), f'functions[{i}].rva'),
                          'size': parse_int(fn.get('size'), f'functions[{i}].size'), 'symbol': fn['symbol']})
    if not functions:
        raise PipelineError('task.json: functions must list at least one function')
    if len({f['rva'] for f in functions}) != len(functions):
        raise PipelineError('task.json: a function is listed twice')
    notes = raw.get('record_notes') or []
    if not isinstance(notes, list) or not all(isinstance(n, str) and n.strip() for n in notes):
        raise PipelineError('task.json: record_notes must be a list of strings')
    max_attempts = raw.get('max_attempts')
    if max_attempts is not None:
        max_attempts = parse_int(max_attempts, 'max_attempts')
    return {'dir': task_dir, 'task_id': task_id, 'build_id': raw['build_id'], 'compiled': compiled,
            'recipe': recipe, 'symbols_local': symbols_path,
            'symbols_repo': symbols if public_symbols else None, 'functions': functions,
            'max_attempts': max_attempts, 'record_notes': notes}


def unit_manifest(task, repo=REPO):
    """({copy path: local path}, closure) for everything a verifier host needs for this unit."""
    repo = Path(repo)
    try:
        closure = include_closure(repo, task['compiled'])
    except (ValueError, OSError) as exc:
        raise PipelineError(f'translation unit of {task["compiled"]}: {exc}') from None
    recipe = repo / task['recipe']
    if not recipe.is_file():
        raise PipelineError(f'recipe not found: {task["recipe"]}')
    problem = recipe_flag_problem(json.loads(recipe.read_text()).get('flags'))
    if problem:
        raise PipelineError(f'recipe flags: {problem}')
    files = {name: repo / name for name in TOOL_FILES}
    files.update({name: repo / name for name in closure})
    files[task['recipe']] = recipe
    files[task['symbols_repo'] or PRIVATE_SYMBOLS] = task['symbols_local']
    return files, closure


def unit_spec(task, files, host):
    return {'unit_spec_schema': 1, 'task_id': task['task_id'], 'host': host, 'build_id': task['build_id'],
            'compiled': task['compiled'], 'recipe': task['recipe'],
            'symbols': task['symbols_repo'] or PRIVATE_SYMBOLS,
            'functions': [{'rva': f['rva'], 'size': f['size'], 'symbol': f['symbol']} for f in task['functions']],
            'files': {name: sha256_file(path) for name, path in sorted(files.items())}}


def changed_files(spec_files, state, machine, remote_dir):
    """Files whose hash differs from what this host last received for this task."""
    if not state or state.get('machine') != machine or state.get('remote_dir') != remote_dir:
        return sorted(spec_files)
    known = state.get('files') or {}
    return sorted(name for name, digest in spec_files.items() if known.get(name) != digest)


def remote_script(remote_dir, spec, label, image, fresh=False):
    """The one shell line run per host: merge uploads, write the spec, build and compare."""
    blob = base64.b64encode(json.dumps(spec, sort_keys=True).encode()).decode()
    t = shlex.quote(remote_dir)
    lines = [
        'shopt -s nullglob', f'T={t}', 'mkdir -p "$T"', 'cd "$T"',
        'rm -rf repo work' if fresh else ':',
        'mkdir -p repo/.unit work',
        'for d in incoming-*; do cp -r "$d"/. repo/ && rm -rf "$d"; done',
        f'printf %s {blob} | base64 -d > repo/.unit/spec.json',
        'touch .running',
        f'python3 -I repo/tools/verifier/unit_build.py --repo repo --spec repo/.unit/spec.json '
        f'--msvc {boatctl.REMOTE_HOME}/msvc --image {shlex.quote(image)} --work work/{shlex.quote(label)}',
        'rc=$?', 'rm -f .running', 'exit $rc',
    ]
    return 'bash -c ' + shlex.quote('\n'.join(lines))


def remote_image(build_id):
    """Fixed private location of the pinned image on a verifier host, outside every task directory."""
    return f'{boatctl.REMOTE_HOME}/private/{build_id}/SkyrimSE.exe'


class Host:
    """One verifier machine running one unit: sync, build and compare, fetch the results."""

    def __init__(self, machine, label, remote_dir, task, state_path=None, local_image=None, log=None):
        self.machine, self.label, self.remote_dir, self.task = machine, label, remote_dir, task
        self.state_path, self.local_image = state_path, local_image
        self.log = log or (lambda msg: None)
        self.timings = {}

    def _state(self):
        if self.state_path and self.state_path.is_file():
            try:
                return json.loads(self.state_path.read_text())
            except ValueError:
                return None
        return None

    def _save_state(self, files):
        if self.state_path:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps({'machine': self.machine, 'remote_dir': self.remote_dir,
                                                   'files': files}, indent=1) + '\n')

    def _upload(self, files, names, stage_root):
        stage = stage_root / f'incoming-{uuid.uuid4().hex[:12]}'
        if stage.exists():
            shutil.rmtree(stage)
        for name in names:
            dest = stage / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(files[name], dest)
        try:
            boatctl.upload(self.machine, stage, f'{self.remote_dir}/{stage.name}')
        finally:
            shutil.rmtree(stage, ignore_errors=True)

    def _upload_image(self):
        if not self.local_image or not Path(self.local_image).is_file():
            raise PipelineError('the verifier host has no target image and no local image is configured '
                                '(.local/verifier/config.json "image")')
        dest = remote_image(self.task['build_id'])
        self.log(f'uploading the target image to {self.label} (once per machine)')
        code, out, _ = boatctl.execute(self.machine, f'mkdir -p -m 700 {shlex.quote(str(PurePosixPath(dest).parent))} '
                                       f'&& rm -f {shlex.quote(dest)}.part', 60)
        if code != 0:
            raise PipelineError(f'cannot prepare the image directory on {self.label}')
        boatctl.upload(self.machine, self.local_image, dest + '.part')
        code, _, _ = boatctl.execute(self.machine, f'chmod 600 {shlex.quote(dest)}.part && '
                                     f'mv {shlex.quote(dest)}.part {shlex.quote(dest)}', 60)
        if code != 0:
            raise PipelineError(f'cannot place the image on {self.label}')

    def run(self, files, stage_root, fresh=False, timeout=600):
        """Returns (exit code, sanitized stdout) of unit_build.py on this host."""
        spec = unit_spec(self.task, files, self.label)
        retried_sync = retried_image = False
        while True:
            start = time.monotonic()
            state = None if fresh else self._state()
            names = changed_files(spec['files'], state, self.machine, self.remote_dir)
            if state is None or state.get('machine') != self.machine:
                # scp needs the parent directory; only the first sync to a host pays for this call.
                code, _, _ = boatctl.execute(self.machine, f'mkdir -p {shlex.quote(self.remote_dir)}', 60)
                if code != 0:
                    raise PipelineError(f'cannot create the task directory on {self.label}')
            if names:
                self._upload(files, names, stage_root)
            self.timings['upload'] = self.timings.get('upload', 0) + time.monotonic() - start
            start = time.monotonic()
            script = remote_script(self.remote_dir, spec, self.label, remote_image(self.task['build_id']), fresh)
            code, out, err = boatctl.execute(self.machine, script, timeout)
            self.timings['run'] = self.timings.get('run', 0) + time.monotonic() - start
            if code == EXIT_SYNC and not retried_sync:
                retried_sync, fresh = True, True
                continue
            if code == EXIT_IMAGE and not retried_image:
                retried_image = True
                self._upload_image()
                continue
            if code not in (EXIT_SYNC,):
                self._save_state(spec['files'])
            if code == 124:
                raise PipelineError(f'{self.label}: remote run timed out after {timeout}s')
            return code, out

    def fetch(self, dest):
        """Copy work/<label> from the host to `dest` (replaced)."""
        start = time.monotonic()
        dest = Path(dest)
        part = dest.with_name(dest.name + '.part')
        shutil.rmtree(part, ignore_errors=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        boatctl.download(self.machine, f'{self.remote_dir}/work/{self.label}', part)
        shutil.rmtree(dest, ignore_errors=True)
        part.rename(dest)
        self.timings['fetch'] = time.monotonic() - start
        return dest


def wait_state(machine, wanted, limit=180):
    end = time.monotonic() + limit
    while time.monotonic() < end:
        state = boatctl.info(machine)['state']
        if state in wanted:
            return state
        time.sleep(2)
    raise PipelineError(f'machine {machine} did not reach {"/".join(sorted(wanted))} in {limit}s')


def ensure_standing(ttl=DEFAULT_TTL, log=print):
    """Bring the standing verifier up (resume or reuse) with an auto-stop deadline; returns (id, how)."""
    in_session = vsession.machine_for_attempt(ttl)
    if in_session is not None:
        return in_session
    machine, state = boatctl.lookup()
    if machine is None:
        raise PipelineError(f'no machine named {boatctl.STANDING}; it is rebuilt only by an Engineer '
                            '(docs/boat-agent-guidelines.md, lifecycle rule 3)')
    if state == 'stopping':
        state = wait_state(machine, {'stopped'})
    if state in {'provisioning', 'provisioned', 'starting', 'cloning'}:
        state = wait_state(machine, boatctl.RUNNING)
    if state in boatctl.RUNNING:
        left = boatctl.seconds_left(boatctl.info(machine))
        if left is not None and left < MIN_LEFT:
            boatctl.extend(machine, ttl)
            return machine, f'warm, deadline extended to {ttl // 60} min'
        return machine, 'warm' + (f', auto-stop in {left // 60} min' if left is not None else '')
    if state in {'stopped', 'error'}:
        boatctl.resume(machine, ttl, reason='ensure_standing (no session)')
        return machine, f'resumed, auto-stop in {ttl // 60} min'
    raise PipelineError(f'{boatctl.STANDING} is in state {state}')


def candidate_size(obj, symbol):
    """Length of the candidate function's own section, or None (read locally with tools/pecoff.py)."""
    try:
        from pecoff import CoffObject
        co = CoffObject(Path(obj).read_bytes())
        for sym in co.symbols.values():
            if sym.name == symbol and sym.section > 0:
                return len(co.section(sym.section).data or b'')
    except Exception:  # a reading aid only; the comparator's report is what counts
        return None
    return None


def function_line(fn, fdir, obj):
    try:
        report = json.loads((fdir / 'report.json').read_text())
    except (OSError, ValueError):
        return f'0x{fn["rva"]:x} ERROR  comparator wrote no report (see {fdir / "summary.txt"})', 'error'
    result, reason = report.get('result', 'error'), report.get('reason') or report.get('verify_function')
    detail = report.get('detail') or ''
    m = re.search(r'at \+0x([0-9a-f]+)', detail)
    size = candidate_size(obj, fn['symbol'])
    parts = [f'0x{fn["rva"]:x} {str(result).upper():<4} {reason}']
    if m:
        parts.append(f'first mismatch +0x{m.group(1)}')
    parts.append(f'size {size if size is not None else "?"}/{fn["size"]}')
    cov = report.get('coverage') or {}
    if result == 'pass' or cov.get('unwind') not in (None, 'not-checked'):
        parts.append(f'unwind {cov.get("unwind")}')
    if reason == 'function-symbol-missing':
        parts.append(f'(object does not define {fn["symbol"]})')
    elif reason == 'unresolved-symbol':
        # The comparator's detail names the symbol only; it holds no bytes.
        parts.append(f'({detail})')
    return '  '.join(parts), result


def compile_errors(log_path, limit=5):
    try:
        lines = Path(log_path).read_text(errors='replace').splitlines()
    except OSError:
        return []
    errs = [line for line in lines if re.search(r'\b(error|fatal error) [A-Z]+\d+', line)]
    out = []
    for line in errs[:limit]:
        out.append('    ' + re.sub(r'^.*?/repo/', '', line)[:160])
    if len(errs) > limit:
        out.append(f'    ... {len(errs) - limit} more in compile.log')
    return out


def lock(task_dir):
    path = Path(task_dir) / '.attempt' / 'lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, 'w')
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise PipelineError('another attempt or confirm is running for this task') from None
    return handle


def git_dirty(paths, repo=REPO):
    out = subprocess.run(['git', 'status', '--porcelain', '--', *paths], cwd=repo, capture_output=True, text=True)
    if out.returncode != 0:
        raise PipelineError('git status failed; run from a git checkout')
    return [line[3:] for line in out.stdout.splitlines()]
