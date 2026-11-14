#!/usr/bin/env python3
"""Reuse only the successful Infrastructure run's site artifact for this exact commit."""
import argparse
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import time

import ci_status


def download(run, destination):
    subprocess.run(['gh', 'run', 'download', str(run), '--name', 'checked-site', '--dir', str(destination)],
                   check=True, capture_output=True, text=True)


def fetch(commit, destination, wait=1800, gh=ci_status.gh, fetch_artifact=download, sleep=time.sleep):
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('expected full commit SHA')
    deadline = time.monotonic() + wait
    while True:
        runs = gh('run', 'list', '--commit', commit, '--event', 'push', '--workflow', ci_status.CHECKS,
                  '--json', 'databaseId,headSha,status,conclusion')
        matching = [r for r in runs if r['headSha'] == commit]
        run = max(matching, key=lambda r: r['databaseId']) if matching else None
        if run and run['status'] == 'completed':
            if run['conclusion'] != 'success':
                raise ValueError(f'Infrastructure run {run["databaseId"]}: {run["conclusion"]}; no site reused')
            break
        if time.monotonic() >= deadline:
            raise ValueError('Infrastructure for exact SHA is still pending; no site reused')
        sleep(min(15, max(0, deadline-time.monotonic())))
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('site destination must be empty')
    with tempfile.TemporaryDirectory(prefix='checked-site-') as tmp:
        fetch_artifact(run['databaseId'], Path(tmp))
        with tarfile.open(Path(tmp) / 'artifact.tar') as archive:
            if any(not (m.isfile() or m.isdir()) for m in archive.getmembers()):
                raise ValueError('site artifact contains links or special files')
            destination.mkdir(parents=True, exist_ok=True)
            archive.extractall(destination, filter='data')
    if not (destination / 'index.html').is_file():
        raise ValueError('site artifact has no index.html')
    print(f'Checked site from Infrastructure run {run["databaseId"]}, commit {commit}')
    return run['databaseId']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--commit', required=True)
    p.add_argument('--out', type=Path, default=Path('dist'))
    p.add_argument('--wait', type=int, default=1800)
    a = p.parse_args()
    fetch(a.commit, a.out, a.wait)


if __name__ == '__main__':
    main()
