"""Compile one reconstruction unit with the pinned recipe and compare each of its functions.

Runs on a verifier host, inside a minimal copy of the repository that `tools/verifier/attempt` and
`tools/verifier/confirm` keep in sync:

    python3 tools/verifier/unit_build.py --repo <copy> --spec <spec.json> --msvc ~/msvc \
        --image ~/private/<build id>/SkyrimSE.exe --work <dir> [--loader wine|native]

`--loader wine` (default) runs the msvc-wine wrapper `<msvc>/bin/x64/cl` (a Boat machine, or this
Mac under Wine); `--loader native` runs `<msvc>/VC/Tools/MSVC/<ver>/bin/Hostx64/x64/cl.exe` directly
on Windows with INCLUDE built the way the msvc-wine wrapper builds it, from the same unpacked
toolset and SDK. Either way the compiler binaries are checked against pinned.sha256 and their
hashes are written to result.json, so a record can name what each host actually ran.

The spec (JSON) names the task id, host label, compiled file, recipe, symbol map, the functions
to compare and the SHA-256 of every file the copy must hold. Steps, each failing closed:

1. The copy holds exactly the listed files with the listed hashes (other files are removed), so
   a half-finished upload cannot be compiled.
2. Once per boot (every run when the spec sets `fresh_prep`, as confirm on runner hosts does):
   the compiler binaries the wrapper runs match tools/verifier/pinned.sha256, and the image
   matches builds/target.json. Exit 42 if the image is missing or wrong (the caller
   uploads it and retries), 44 if the toolchain differs.
3. The unit is the include closure of the compiled file (tools/source_digest.py) and the recipe
   names no include path but the closure's roots.
4. The compile runs with INCLUDE, LIB, LIBPATH, CL, _CL_ and EXTERNAL_INCLUDE removed from the
   environment. The msvc-wine wrapper then sets INCLUDE to toolchain and SDK directories only;
   that value is checked and written to the build record. CL and _CL_ would add flags the recipe
   does not name, so they must stay unset. `/showIncludes` is added to the recipe flags: it
   prints the files the compiler opened and changes no section but the object-path record.
5. Every file the compiler opened is either under the toolchain root or a repository file of
   the closure, and the closure's repository files are exactly those the compiler opened.
6. Each function is compared with tools/verifier/verify_function.py (the comparator decides).

Standard output carries only sanitized lines (counts, reason codes, offsets, hashes), because
Boat keeps exec output. Compiler output, reports and diagnostics go to files under --work.
Exit status: 0 every function passed, 1 a comparison failed, 2 comparator error, 3 compile
failed, 4 unit or include problem, 42/43/44 as above (43: copy does not match the spec).
"""
import argparse
import hashlib
import json
import ntpath
import os
from pathlib import Path, PurePosixPath
import platform
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from source_digest import include_closure, recipe_flag_problem, tu_digest  # noqa: E402

SPEC_SCHEMA = 1
# Variables that change include search or add compiler flags; the wrapper sets INCLUDE itself.
CLEARED_ENV = ('INCLUDE', 'LIB', 'LIBPATH', 'CL', '_CL_', 'EXTERNAL_INCLUDE')
SHOW_INCLUDES = '/showIncludes'
NOTE_PREFIX = 'Note: including file:'
KEEP_IN_COPY = {'.unit', '.local'}
EXIT_IMAGE, EXIT_SYNC, EXIT_TOOLCHAIN = 42, 43, 44
LOADERS = ('wine', 'native')
COMPILE_TIMEOUT = 180
# The include directories the msvc-wine wrapper (msvcenv.sh) puts in INCLUDE, in its order; a native
# compile uses the same list so both loaders search the same unpacked toolset and SDK.
MSVC_INCLUDE_DIRS = (('msvc', 'atlmfc\\include'), ('msvc', 'include'), ('sdk', 'shared'), ('sdk', 'ucrt'),
                     ('sdk', 'um'), ('sdk', 'winrt'), ('sdk', 'km'))


class UnitError(Exception):
    def __init__(self, code, status, detail):
        super().__init__(detail)
        self.code, self.status, self.detail = code, status, detail


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def clean_env(environ):
    """The compile environment: everything but the variables that steer include search or flags."""
    return {k: v for k, v in environ.items() if k not in CLEARED_ENV}


def windows_compile_job():
    """Put this dedicated supervisor in a non-breakaway, kill-on-close Windows job.

    No compiler starts until assignment succeeds; only the supervisor owns the job handle.
    API/layout reference: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
    """
    import ctypes as c
    class Basic(c.Structure):
        _fields_ = [('PerProcessUserTimeLimit', c.c_int64), ('PerJobUserTimeLimit', c.c_int64),
                    ('LimitFlags', c.c_uint32), ('MinimumWorkingSetSize', c.c_size_t),
                    ('MaximumWorkingSetSize', c.c_size_t), ('ActiveProcessLimit', c.c_uint32),
                    ('Affinity', c.c_size_t), ('PriorityClass', c.c_uint32), ('SchedulingClass', c.c_uint32)]
    class IO(c.Structure):
        _fields_ = [(name, c.c_uint64) for name in ('ReadOperationCount', 'WriteOperationCount',
                    'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]
    class Limits(c.Structure):
        _fields_ = [('BasicLimitInformation', Basic), ('IoInfo', IO), ('ProcessMemoryLimit', c.c_size_t),
                    ('JobMemoryLimit', c.c_size_t), ('PeakProcessMemoryUsed', c.c_size_t),
                    ('PeakJobMemoryUsed', c.c_size_t)]
    api = c.WinDLL('kernel32', use_last_error=True)
    api.CreateJobObjectW.argtypes, api.CreateJobObjectW.restype = [c.c_void_p, c.c_wchar_p], c.c_void_p
    api.SetInformationJobObject.argtypes = [c.c_void_p, c.c_int, c.c_void_p, c.c_uint32]
    api.SetInformationJobObject.restype = c.c_int
    api.AssignProcessToJobObject.argtypes = [c.c_void_p, c.c_void_p]
    api.AssignProcessToJobObject.restype = c.c_int
    api.GetCurrentProcess.argtypes, api.GetCurrentProcess.restype = [], c.c_void_p
    api.TerminateJobObject.argtypes, api.TerminateJobObject.restype = [c.c_void_p, c.c_uint32], c.c_int
    api.CloseHandle.argtypes, api.CloseHandle.restype = [c.c_void_p], c.c_int
    handle = api.CreateJobObjectW(None, None)  # non-inheritable handle, no shared job name
    if not handle:
        raise c.WinError(c.get_last_error())
    limits = Limits()
    limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if (not api.SetInformationJobObject(handle, 9, c.byref(limits), c.sizeof(limits))
            or not api.AssignProcessToJobObject(handle, api.GetCurrentProcess())):
        error = c.get_last_error()
        api.CloseHandle(handle)
        raise c.WinError(error)
    return api, handle


def compile_supervisor(command, timeout, result_path):
    """Dedicated child owns the deadline even if unit_build/SSH dies.

    The compiler inherits this supervisor's POSIX process group or Windows job. On *every*
    outcome, kill the whole owned tree, including a child retaining stdout after cl exits.
    Result metadata is private and flushed before cleanup kills the supervisor itself.
    """
    job = None
    result = dict(returncode=None, timeout=False, supervisor_error=False)
    try:
        if sys.platform == 'win32':
            job = windows_compile_job()
        elif os.getpgrp() != os.getpid():
            raise OSError('compile supervisor needs its own process group')
        try:
            result['returncode'] = subprocess.run(command, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            result['timeout'] = True
    except (OSError, subprocess.SubprocessError):
        result['supervisor_error'] = True
    finally:
        try:
            with open(result_path, 'w', encoding='utf-8') as output:
                json.dump(result, output)
                output.flush()
                os.fsync(output.fileno())
        finally:
            if job is not None:
                api, handle = job
                api.TerminateJobObject(handle, 0)
                # If termination failed, process exit closes the sole handle and kills the job.
                os._exit(125)
            if sys.platform != 'win32' and os.getpgrp() == os.getpid():
                os.killpg(os.getpid(), signal.SIGKILL)
    return 125


def compile_bounded(cmd, repo, env, timeout=COMPILE_TIMEOUT):
    private = Path(repo) / '.local'
    private.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='compile-supervisor-', dir=private) as directory:
        result_path = Path(directory) / 'result.json'
        argv = [sys.executable, '-I', str(Path(__file__).resolve()), '--compile-child',
                str(timeout), str(result_path), json.dumps(cmd)]
        windows = sys.platform == 'win32'
        proc = subprocess.Popen(argv, cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, errors='replace', **({} if windows else {'start_new_session': True}))
        def kill_owned():
            if windows:
                # Killing the supervisor closes its non-inheritable job handle, killing children.
                proc.kill()
            else:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        expired = False
        try:
            try:
                stdout, stderr = proc.communicate(timeout=timeout + 15)
            except subprocess.TimeoutExpired:
                expired = True
                kill_owned()
                try:
                    stdout, stderr = proc.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    # A failed cleanup must itself be bounded; never enter Popen.__exit__.wait().
                    proc.stdout.close()
                    proc.stderr.close()
                    proc.wait(timeout=15)
                    stdout, stderr = '', ''
            if expired:
                raise UnitError(3, 'compile-timeout', f'compiler exceeded {timeout} seconds')
            try:
                result = json.loads(result_path.read_text())
            except (OSError, ValueError):
                raise UnitError(4, 'compile-supervisor', 'compile supervisor produced no complete result') from None
            if result.get('timeout'):
                raise UnitError(3, 'compile-timeout', f'compiler exceeded {timeout} seconds')
            if result.get('supervisor_error') or type(result.get('returncode')) is not int:
                raise UnitError(4, 'compile-supervisor', 'compile supervisor could not contain the compiler')
            return subprocess.CompletedProcess(cmd, result['returncode'], stdout, stderr)
        finally:
            if proc.poll() is None:
                kill_owned()
                proc.wait(timeout=15)
            proc.stdout.close()
            proc.stderr.close()


def wrapper_settings(msvc, env):
    """INCLUDE, BASE and BINDIR exactly as the msvc-wine wrapper computes them for the compile."""
    script = ('. "$1/bin/x64/msvcenv.sh" >/dev/null 2>&1 || exit 9; '
              'printf "%s\\n%s\\n%s\\n" "$INCLUDE" "$BASE" "$BINDIR"')
    out = subprocess.run(['bash', '-c', script, 'msvcenv', str(msvc)], env=env,
                         capture_output=True, text=True)
    lines = out.stdout.split('\n')
    if out.returncode != 0 or len(lines) < 3:
        raise UnitError(EXIT_TOOLCHAIN, 'toolchain-wrapper', 'cannot read the wrapper environment')
    return {'INCLUDE': lines[0], 'BASE': lines[1], 'BINDIR': lines[2]}


def native_settings(msvc):
    """INCLUDE, BASE and BINDIR for a native Windows compile from an unpacked toolset at `msvc`.

    Exactly one toolset version and one SDK include version must be present: picking one of several
    silently would let a host compile with a compiler or headers the pins do not describe.
    """
    msvc = Path(msvc)
    toolsets = sorted(p for p in (msvc / 'VC' / 'Tools' / 'MSVC').glob('*') if p.is_dir())
    sdks = sorted(p for p in (msvc / 'Windows Kits' / '10' / 'Include').glob('10.*') if p.is_dir())
    if len(toolsets) != 1 or len(sdks) != 1:
        raise UnitError(EXIT_TOOLCHAIN, 'toolchain-layout',
                        f'expected one MSVC toolset and one SDK include version, found {len(toolsets)} and {len(sdks)}')
    base = ntpath.normpath(str(msvc).replace('/', '\\'))
    roots = {'msvc': ntpath.join(base, 'VC', 'Tools', 'MSVC', toolsets[0].name),
             'sdk': ntpath.join(base, 'Windows Kits', '10', 'Include', sdks[0].name)}
    include = ';'.join(ntpath.join(roots[kind], sub) for kind, sub in MSVC_INCLUDE_DIRS)
    return {'INCLUDE': include, 'BASE': base, 'BINDIR': str(toolsets[0] / 'bin' / 'Hostx64' / 'x64')}


def include_problem(include, base):
    """Why the INCLUDE value is not toolchain/SDK directories only, or None."""
    entries = [e for e in include.split(';') if e]
    if not entries:
        return 'INCLUDE is empty'
    root = base.rstrip('\\').lower() + '\\'
    for entry in entries:
        norm = entry.replace('/', '\\').lower()
        if not norm.startswith(root) or '\\..' in norm:
            return f'INCLUDE entry outside the toolchain root: {entry}'
    return None


def parse_show_includes(text):
    """(opened paths in order, remaining output lines) from cl output with /showIncludes."""
    opened, rest = [], []
    for line in text.splitlines():
        if line.startswith(NOTE_PREFIX):
            opened.append(line[len(NOTE_PREFIX):].strip())
        else:
            rest.append(line)
    return opened, rest


def _norm(path):
    """A wrapper-printed path as a POSIX absolute path; the wrapper strips `z:` and flips slashes."""
    path = path.replace('\\', '/')
    if re.match(r'^[A-Za-z]:/', path):
        if path[0].lower() != 'z':
            return None
        path = path[2:]
    return os.path.normpath(path) if path.startswith('/') else None


def classify_includes(opened, repo, toolchain):
    """Split opened files into repository-relative paths, a toolchain count and anything else."""
    repo, toolchain = os.path.normpath(str(repo)), os.path.normpath(str(toolchain))
    repo_files, outside, tool_count = set(), [], 0
    for raw in opened:
        path = _norm(raw)
        if path is None:
            outside.append(raw)
        elif path.startswith(toolchain + '/'):
            tool_count += 1
        elif path.startswith(repo + '/'):
            repo_files.add(PurePosixPath(os.path.relpath(path, repo)).as_posix())
        else:
            outside.append(raw)
    return sorted(repo_files), tool_count, outside


def classify_includes_windows(opened, repo, toolchain):
    """classify_includes for a native Windows compile: drive-letter paths, case-insensitive roots,
    repository paths kept in the spelling the compiler printed."""
    def norm(p):
        return ntpath.normpath(str(p).replace('/', '\\'))
    repo_n = norm(repo).rstrip('\\')
    tool_n = norm(toolchain).rstrip('\\').lower() + '\\'
    repo_files, outside, tool_count = set(), [], 0
    for raw in opened:
        p = norm(raw)
        low = p.lower()
        if low.startswith(tool_n):
            tool_count += 1
        elif low.startswith(repo_n.lower() + '\\') and '\\..\\' not in low + '\\':
            repo_files.add(p[len(repo_n) + 1:].replace('\\', '/'))
        else:
            outside.append(raw)
    return sorted(repo_files), tool_count, outside


def fold_case_includes(outside, repo, closure, repo_files):
    """Entries of `outside` that are closure files spelled in another case, moved into repo_files.

    macOS volumes are usually case-insensitive and Wine there may print an opened header in lower
    case, so it no longer starts with the repository path as spelled. Only an exact
    case-insensitive match to a file of the derived closure is accepted; anything else stays
    outside and still fails the build.
    """
    prefix = os.path.normpath(str(repo)).lower() + '/'
    by_lower = {c.lower(): c for c in closure}
    files, rest = set(repo_files), []
    for raw in outside:
        path = _norm(raw)
        hit = None
        if path is not None and path.lower().startswith(prefix):
            hit = by_lower.get(path.lower()[len(prefix):])
        if hit:
            files.add(hit)
        else:
            rest.append(raw)
    return sorted(files), rest


def closure_difference(compiler_files, compiled, closure):
    """Problem text if the compiler's repository files differ from the derived closure, else None.

    The compiled file itself is not listed by /showIncludes, so it is added before comparing.
    A file only in the closure is usually an include inside a comment or a dead `#if` branch:
    the closure counts it (over-including is its safe direction) but the compiler never opened it.
    """
    seen = set(compiler_files) | {compiled}
    only_compiler = sorted(seen - set(closure))
    only_closure = sorted(set(closure) - seen)
    if not only_compiler and not only_closure:
        return None
    parts = []
    if only_compiler:
        parts.append('compiler opened files the closure lacks: ' + ', '.join(only_compiler))
    if only_closure:
        parts.append('closure lists files the compiler did not open (commented-out or conditional include?): '
                     + ', '.join(only_closure))
    return '; '.join(parts)


def sync_copy(repo, files):
    """Require the copy to hold exactly `files` ({path: sha256}); remove anything else."""
    bad = []
    for name, digest in files.items():
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or p.parts[0] in KEEP_IN_COPY:
            raise UnitError(EXIT_SYNC, 'sync-mismatch', f'invalid path in spec: {name}')
        path = repo / name
        if not path.is_file() or path.is_symlink() or sha256_file(path) != digest:
            bad.append(name)
    if bad:
        raise UnitError(EXIT_SYNC, 'sync-mismatch', f'{len(bad)} file(s) missing or different')
    wanted = set(files)
    for dirpath, dirnames, filenames in os.walk(repo, topdown=True):
        rel_dir = os.path.relpath(dirpath, repo)
        if rel_dir == '.':
            dirnames[:] = [d for d in dirnames if d not in KEEP_IN_COPY]
        for fn in filenames:
            # as_posix() of a native relative path: on Windows a normpath'd string keeps backslashes and
            # would never equal a spec name, so every file would look unwanted.
            rel = Path(dirpath, fn).relative_to(repo).as_posix()
            if rel not in wanted:
                os.unlink(os.path.join(dirpath, fn))


def boot_id():
    """An identifier that changes at every boot, or None where none is known (then nothing is cached)."""
    try:
        return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    except OSError:
        pass
    if sys.platform == 'darwin':
        out = subprocess.run(['sysctl', '-n', 'kern.boottime'], capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return 'darwin ' + out.stdout.strip()
    return None


def prepare_host(repo, msvc, image, wrapper, expected_image, marker_dir=None, use_cache=True):
    """Toolchain and image checks, once per boot (a resume or a fork is a new boot), or on every
    call when `use_cache` is False.

    Returns (state, {binary name: sha256}): the hashes of the compiler binaries this host runs,
    which equal the pins whenever the check passed.
    """
    marker_dir = marker_dir or os.environ.get('SR_PREP_MARKER_DIR', '/dev/shm')
    pins = (repo / 'tools/verifier/pinned.sha256').read_text()
    boot = boot_id()
    key = hashlib.sha256(f'{boot}\n{pins}\n{wrapper["BINDIR"]}\n{image}\n{expected_image}'.encode()).hexdigest()
    marker = Path(marker_dir) / f'sr-verifier-prep-{key[:16]}'
    if use_cache and boot is not None and marker.is_file():
        try:
            return 'cached', json.loads(marker.read_text())
        except ValueError:
            pass
    hashes = {}
    for line in pins.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        digest, name = parts
        binary = Path(wrapper['BINDIR']) / name
        hashes[name] = sha256_file(binary) if binary.is_file() else None
        if hashes[name] != digest:
            raise UnitError(EXIT_TOOLCHAIN, 'toolchain-mismatch', f'{name} does not match pinned.sha256')
    image = Path(image)
    if not image.is_file():
        image.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        raise UnitError(EXIT_IMAGE, 'image-missing', 'target image is not on this host')
    if sha256_file(image) != expected_image:
        raise UnitError(EXIT_IMAGE, 'image-mismatch', 'target image hash differs from builds/target.json')
    if boot is not None:
        try:
            marker.write_text(json.dumps(hashes, sort_keys=True) + '\n')
        except OSError:
            pass
    return 'checked', hashes


def host_facts(loader, compiler_hashes, toolchain_check=None):
    """What a record may say about the host: OS, CPU architecture, loader, compiler hashes and
    whether those hashes were measured in this run (`checked`) or read from the per-boot marker
    (`cached`). Never a path, user name or address."""
    system = {'darwin': 'macos', 'win32': 'windows'}.get(sys.platform, sys.platform)
    facts = {'os': system, 'machine': platform.machine().lower(), 'loader': loader,
             'compiler_sha256': dict(sorted(compiler_hashes.items()))}
    if toolchain_check is not None:
        facts['toolchain_check'] = toolchain_check
    return facts


def make_task(spec, fn, digest, recipe_sha, object_bytes=None):
    task = {'task_id': fn.get('task_id') or f'{spec["build_id"]}-0x{fn["rva"]:x}', 'build_id': spec['build_id'],
            'target_image_sha256': spec['image_sha256'], 'rva': fn['rva'], 'size': fn['size'],
            'symbol': fn['symbol'], 'source_revision': digest, 'source_path': spec['compiled'],
            'recipe_sha256': recipe_sha}
    if 'internal_selector' in fn:
        from compare_internal import make_identity
        task['task_schema'] = 2
        task['internal_identity'] = make_identity(object_bytes, fn['symbol'], fn['internal_selector'],
                                                 digest, spec['compiled'])
    return task


def mismatch_offset(detail):
    m = re.search(r'at \+0x([0-9a-f]+)', detail or '')
    return f'+0x{m.group(1)}' if m else '-'


def run(args):
    clock = time.monotonic()
    timings = {}

    def lap(phase):
        nonlocal clock
        now = time.monotonic()
        timings[phase] = round(timings.get(phase, 0) + now - clock, 3)
        clock = now

    spec = json.loads(Path(args.spec).read_text())
    if spec.get('unit_spec_schema') not in (SPEC_SCHEMA, 2):
        raise UnitError(4, 'invalid-spec', f'unit spec needs unit_spec_schema {SPEC_SCHEMA}')
    internal = any('internal_selector' in fn for fn in spec.get('functions', []))
    if (spec['unit_spec_schema'] == 2) != internal:
        raise UnitError(4, 'invalid-spec', 'internal selectors need unit_spec_schema 2; external tasks need schema 1')
    repo, work, msvc = Path(args.repo).resolve(), Path(args.work).resolve(), Path(args.msvc).resolve()
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    sync_copy(repo, spec['files'])
    lap('sync')
    env = clean_env(os.environ)
    # English /showIncludes notes whatever the host's language; it changes messages, not objects.
    env['VSLANG'] = '1033'
    loader = getattr(args, 'loader', None) or 'wine'
    if loader == 'native':
        wrapper = native_settings(msvc)
        env['INCLUDE'] = wrapper['INCLUDE']
    else:
        wrapper = wrapper_settings(msvc, env)
    problem = include_problem(wrapper['INCLUDE'], wrapper['BASE'])
    if problem:
        raise UnitError(4, 'include-env', problem)
    target = json.loads((repo / 'builds/target.json').read_text())
    if target.get('build_id') != spec['build_id']:
        raise UnitError(4, 'invalid-spec', 'spec build id differs from builds/target.json')
    spec['image_sha256'] = target['image_sha256']
    prep, compiler_hashes = prepare_host(repo, msvc, args.image, wrapper, target['image_sha256'],
                                         use_cache=not spec.get('fresh_prep'))
    lap('prep')
    host = host_facts(loader, compiler_hashes, prep)
    print(f'host {spec["host"]} prep {prep} {host["os"]} {loader}')

    compiled = spec['compiled']
    try:
        closure = include_closure(repo, compiled)
    except (ValueError, OSError) as exc:
        raise UnitError(4, 'unit-invalid', str(exc))
    recipe_path = repo / spec['recipe']
    recipe = json.loads(recipe_path.read_text())
    problem = recipe_flag_problem(recipe.get('flags'))
    if problem:
        raise UnitError(4, 'recipe-flags', problem)
    digest = tu_digest(repo, closure)
    recipe_sha = sha256_file(recipe_path)

    lap('closure')
    obj = work / 'candidate.obj'
    cl = str(Path(wrapper['BINDIR']) / 'cl.exe') if loader == 'native' else str(msvc / 'bin/x64/cl')
    cmd = [cl] + recipe['flags'] + [SHOW_INCLUDES, f'/Fo{obj}', compiled]
    proc = compile_bounded(cmd, repo, env)
    (work / 'compile-command.json').write_text(json.dumps(cmd[1:], indent=1) + '\n')
    opened, rest = parse_show_includes(proc.stdout)
    (work / 'compile.log').write_text('\n'.join(rest) + '\n' + proc.stderr)
    (work / 'includes.txt').write_text('\n'.join(opened) + '\n')
    errors = sum(1 for line in rest if re.search(r'\berror [A-Z]+\d+', line))
    if proc.returncode != 0 or not obj.is_file():
        print(f'compile failed exit {proc.returncode} errors {errors}')
        return 3
    if loader == 'native':
        repo_files, tool_count, outside = classify_includes_windows(opened, repo, wrapper['BASE'])
    else:
        repo_files, tool_count, outside = classify_includes(opened, repo, Path(wrapper['BASE'][2:].replace('\\', '/')))
        if outside and sys.platform == 'darwin':
            repo_files, outside = fold_case_includes(outside, repo, closure, repo_files)
    if outside:
        raise UnitError(4, 'include-outside', f'{len(outside)} included file(s) outside the repository and toolchain')
    diff = closure_difference(repo_files, compiled, closure)
    if diff:
        (work / 'include-check.txt').write_text(diff + '\n')
        raise UnitError(4, 'include-closure-mismatch', diff)
    environment = {'INCLUDE': wrapper['INCLUDE'], 'CL': None, '_CL_': None,
                   'cleared': list(CLEARED_ENV), 'added_flags': [SHOW_INCLUDES],
                   'show_includes': {'repository_files': sorted(set(repo_files) | {compiled}),
                                     'toolchain_files': tool_count, 'equals_closure': True}}
    obj_sha = sha256_file(obj)
    lap('compile')
    print(f'compile ok object {obj_sha[:16]} includes repo {len(closure)} toolchain {tool_count} closure-equal')

    worst = 0
    results = []
    for fn in spec['functions']:
        d = work / f'0x{fn["rva"]:x}'
        d.mkdir()
        task = make_task(spec, fn, digest, recipe_sha, obj.read_bytes() if 'internal_selector' in fn else None)
        task_file = {'verify_task_schema': 2 if 'internal_identity' in task else 1, 'task': task,
                     'recipe': os.path.relpath(recipe_path, d),
                     'symbols': os.path.relpath(repo / spec['symbols'], d),
                     'manifest': os.path.relpath(repo / 'builds/target.json', d)}
        build_record = {'build_record_schema': 1, 'source_revision': digest, 'source_path': compiled,
                        'recipe_sha256': recipe_sha, 'object_sha256': obj_sha, 'environment': environment}
        (d / 'task-file.json').write_text(json.dumps(task_file, indent=2) + '\n')
        (d / 'build-record.json').write_text(json.dumps(build_record, indent=2) + '\n')
        diagnostics = repo / '.local/verifier/diagnostics' / f'{spec["host"]}-0x{fn["rva"]:x}.json'
        proc = subprocess.run([sys.executable, str(repo / 'tools/verifier/verify_function.py'),
                               '--task-file', str(d / 'task-file.json'), '--object', str(obj),
                               '--build-record', str(d / 'build-record.json'), '--image', str(args.image),
                               '--report', str(d / 'report.json'), '--diagnostics', str(diagnostics)],
                              capture_output=True, text=True)
        (d / 'summary.txt').write_text(proc.stdout + proc.stderr)
        if diagnostics.exists():
            shutil.move(str(diagnostics), d / 'diagnostics.json')
        flat = diagnostics.with_name(diagnostics.stem + '.task.json')
        if flat.exists():
            flat.unlink()
        try:
            report = json.loads((d / 'report.json').read_text())
        except (OSError, ValueError):
            report = {'result': 'error', 'reason': 'no-report'}
        status = {0: 0, 1: 1}.get(proc.returncode, 2)
        worst = max(worst, status)
        results.append({'rva': fn['rva'], 'result': report.get('result'), 'reason': report.get('reason')})
        lap('compare')
        print(f'0x{fn["rva"]:x} {report.get("result")} {report.get("reason")} {mismatch_offset(report.get("detail"))}')
    (work / 'result.json').write_text(json.dumps({'host': spec['host'], 'host_facts': host, 'object_sha256': obj_sha,
                                                  'source_revision': digest, 'functions': results,
                                                  'timings': timings}, indent=2) + '\n')
    return worst


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--repo', required=True)
    p.add_argument('--spec', required=True)
    p.add_argument('--msvc', required=True)
    p.add_argument('--image', required=True)
    p.add_argument('--work', required=True)
    p.add_argument('--loader', choices=LOADERS, default='wine',
                   help='wine: the msvc-wine wrapper; native: cl.exe directly on Windows')
    args = p.parse_args()
    try:
        return run(args)
    except UnitError as exc:
        work = Path(args.work)
        if work.is_dir():
            (work / 'error.json').write_text(json.dumps({'status': exc.status, 'detail': exc.detail}) + '\n')
        # The detail names repository paths and counts only, never source text or bytes.
        print(f'unit-error {exc.status}: {exc.detail}')
        return exc.code


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--compile-child':
        raise SystemExit(compile_supervisor(json.loads(sys.argv[4]), float(sys.argv[2]), sys.argv[3]))
    raise SystemExit(main())
