"""Host side of a local or ssh verifier runner (tools/verifier/runners.py). Standard library only.

Shipped inside every run directory next to the repository copy, so a host needs Python 3 and
the toolchain, never a checkout or an installed script:

    python <work>/<name>.py run   --run <work>/<name> --bundle <work>/<name>.tar --msvc <toolchain> \
        --image <exe> --loader wine|native --label <host id>
    python <work>/<name>.py probe --run <work>/<name> --bundle <work>/<name>.tar --msvc <toolchain> \
        --image <exe> --loader wine|native
    python <work>/<name>.py clean --run <work>/<name>

The caller uploads two files per run, <name>.tar (the repository copy and its spec) and <name>.py
(this script); `run` unpacks the archive into <work>/<name>/, compiles and compares with <dir>/repo/tools/verifier/unit_build.py (which checks the copy
against the spec, the compiler against pinned.sha256 and the image against builds/target.json)
and passes on its sanitized standard output and exit status, then packs work/<label>/ into
<name>.out.tar for the caller to fetch in one transfer; anything on unit_build's standard error goes
to a file in that directory, which only the caller's private fetch reads. `clean` removes all four. `probe` prints
KEY=value lines (toolchain and image state, compiler hashes, CPUs, OS, Python, runs in progress).
Runs older than a day are pruned, so a fetch that never happened leaves nothing behind.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time

RUN_NAME = re.compile(r'[a-z0-9][a-z0-9.-]{0,80}-[0-9a-f]{12}')
PRUNE_AFTER = 86400


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def bindir(msvc):
    found = sorted(p for p in (Path(msvc) / 'VC' / 'Tools' / 'MSVC').glob('*/bin/Hostx64/x64') if p.is_dir())
    return found[0] if len(found) == 1 else None


def run_paths(run):
    """(work root, name) of a run directory, refusing names the runner would not have made."""
    run = Path(run).resolve()
    if not RUN_NAME.fullmatch(run.name):
        raise SystemExit('agent-error bad run directory name')
    return run.parent, run.name


def leftovers(root, name):
    return [root / name, root / f'{name}.tar', root / f'{name}.out.tar', root / f'{name}.py']


def remove(paths):
    for path in paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                path.unlink()
            except OSError:
                pass


def prune(root, keep):
    now = time.time()
    for path in root.iterdir() if root.is_dir() else []:
        base = path.name
        for suffix in ('.out.tar', '.tar', '.py'):
            if base.endswith(suffix):
                base = base[:-len(suffix)]
                break
        if base == keep or not RUN_NAME.fullmatch(base):
            continue
        try:
            if now - path.stat().st_mtime > PRUNE_AFTER:
                remove([path])
        except OSError:
            pass


def unpack(bundle, dest):
    """Extract the uploaded archive with tarfile's `data` filter (no links out, no absolute paths)."""
    dest.mkdir(parents=True)
    with tarfile.open(bundle) as tar:
        if hasattr(tarfile, 'data_filter'):
            tar.extractall(dest, filter='data')
        else:
            for member in tar.getmembers():
                p = Path(member.name)
                if p.is_absolute() or '..' in p.parts or not (member.isfile() or member.isdir()):
                    raise SystemExit('agent-error unsafe archive member')
            tar.extractall(dest)
    Path(bundle).unlink()


def cmd_run(a):
    root, name = run_paths(a.run)
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,39}', a.label):
        print('agent-error bad label')
        return 2
    prune(root, name)
    run = root / name
    unpack(Path(a.bundle), run)
    work = run / 'work' / a.label
    marker = run / '.running'
    marker.write_text('running\n')
    try:
        proc = subprocess.run([sys.executable, '-I', str(run / 'repo' / 'tools' / 'verifier' / 'unit_build.py'),
                               '--repo', str(run / 'repo'), '--spec', str(run / 'repo' / '.unit' / 'spec.json'),
                               '--msvc', a.msvc, '--image', a.image, '--work', str(work), '--loader', a.loader],
                              capture_output=True, text=True, errors='replace')
    finally:
        marker.unlink()
    sys.stdout.write(proc.stdout)
    if proc.stderr.strip():
        work.mkdir(parents=True, exist_ok=True)
        (work / 'agent-stderr.txt').write_text(proc.stderr)
        print(f'agent: unit_build wrote {len(proc.stderr.splitlines())} line(s) to stderr (agent-stderr.txt)')
    if work.is_dir():
        with tarfile.open(root / f'{name}.out.tar', 'w', format=tarfile.PAX_FORMAT) as tar:
            for path in sorted(work.rglob('*')):
                tar.add(str(path), arcname=path.relative_to(work).as_posix(), recursive=False)
    return proc.returncode


def cmd_probe(a):
    root, name = run_paths(a.run)
    run = root / name
    unpack(Path(a.bundle), run)
    out = {'OS': {'darwin': 'macos', 'win32': 'windows'}.get(sys.platform, sys.platform), 'LOADER': a.loader,
           'PYTHON': '.'.join(map(str, sys.version_info[:3])), 'CPUS': str(os.cpu_count() or '')}
    pins = {}
    for line in (run / 'pinned.sha256').read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            pins[parts[1]] = parts[0]
    bins = bindir(a.msvc)
    hashes = {}
    if bins is None:
        out['TOOLCHAIN'] = 'missing'
    else:
        for name in pins:
            hashes[name] = sha256_file(bins / name) if (bins / name).is_file() else None
        out['TOOLCHAIN'] = 'ok' if hashes == pins else 'bad'
        if a.loader == 'wine' and not (Path(a.msvc) / 'bin' / 'x64' / 'cl').is_file():
            out['TOOLCHAIN'] = 'no-wrapper'
    out['COMPILER'] = json.dumps(hashes, sort_keys=True, separators=(',', ':'))
    target = json.loads((run / 'target.json').read_text())
    image = Path(a.image)
    if not image.is_file():
        out['IMAGE'] = 'missing'
    else:
        out['IMAGE'] = 'ok' if sha256_file(image) == target.get('image_sha256') else 'mismatch'
    out['RUNNING'] = str(sum(1 for p in root.glob('*/.running') if p.parent != run))
    for key in sorted(out):
        print(f'{key}={out[key]}')
    return 0


def cmd_clean(a):
    root, name = run_paths(a.run)
    paths = leftovers(root, name)
    remove(paths)
    return 0 if not any(p.exists() for p in paths[:3]) else 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True)
    for name in ('run', 'probe'):
        s = sub.add_parser(name)
        s.add_argument('--run', required=True)
        s.add_argument('--bundle', required=True)
        s.add_argument('--msvc', required=True)
        s.add_argument('--image', required=True)
        s.add_argument('--loader', choices=('wine', 'native'), required=True)
        if name == 'run':
            s.add_argument('--label', required=True)
    s = sub.add_parser('clean')
    s.add_argument('--run', required=True)
    a = p.parse_args()
    return {'run': cmd_run, 'probe': cmd_probe, 'clean': cmd_clean}[a.command](a)


if __name__ == '__main__':
    raise SystemExit(main())
