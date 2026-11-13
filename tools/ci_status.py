"""CI result of one pushed commit, read-only through GitHub CLI.

Exit status: 0 workflows passed or Pages was superseded, 1 at least one finished red,
2 runs are still pending or none exist yet, 3 `gh` is missing or could not answer, or
`--commit` names no commit of this repository. A short SHA or ref is expanded with `git rev-parse`.
A green result proves only what CI checks (publication hygiene, metadata, tests, site build),
never a byte match.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

GREEN, RED, PENDING, UNAVAILABLE = 0, 1, 2, 3
# Conclusions that do not make a run red: a skipped or neutral workflow did not fail anything.
OK_CONCLUSIONS = {'success', 'skipped', 'neutral'}
PAGES = 'Publish research report'
CHECKS = 'Infrastructure checks'
POLL_SECONDS = 15
REPO = Path(__file__).resolve().parents[1]
FULL_SHA = re.compile(r'[0-9a-f]{40}')


class GhError(Exception):
    pass


def gh(*args):
    """Run gh (CI_STATUS_GH overrides the executable, for tests) and parse its JSON output."""
    exe = os.environ.get('CI_STATUS_GH', 'gh')
    try:
        done = subprocess.run([exe, *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GhError(f'{exe}: {error}') from error
    if done.returncode != 0:
        raise GhError(f'{exe} {args[0]} {args[1]}: {done.stderr.strip() or "exit " + str(done.returncode)}')
    try:
        return json.loads(done.stdout)
    except ValueError as error:
        raise GhError(f'{exe} {args[0]} {args[1]}: output is not JSON') from error


def resolve_commit(ref='HEAD', cwd=REPO):
    """The full SHA of a commit-ish (short SHA, branch, HEAD).

    `gh run list --commit` and the runs' headSha both use the full SHA, so a short SHA would match
    no run and read as "no workflow runs yet" even after CI finished.
    """
    if FULL_SHA.fullmatch(ref.lower()):
        return ref.lower()
    done = subprocess.run(['git', 'rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}'],
                          capture_output=True, text=True, cwd=cwd)
    sha = done.stdout.strip()
    if done.returncode != 0 or not FULL_SHA.fullmatch(sha):
        raise GhError(f'git rev-parse: {ref!r} names no commit in {cwd}')
    return sha


def failed_steps(run_id):
    """'job / step' names whose conclusion is red, for a finished run."""
    jobs = gh('run', 'view', str(run_id), '--json', 'jobs').get('jobs', [])
    out = []
    for job in jobs:
        steps = [s['name'] for s in job.get('steps', []) if s.get('conclusion') not in OK_CONCLUSIONS | {None}]
        if steps:
            out += [f"{job['name']} / {s}" for s in steps]
        elif job.get('conclusion') not in OK_CONCLUSIONS:
            out.append(job['name'])
    return out


def superseding_pages(commit):
    """Find the newest main-branch push of a descendant, proven against current main."""
    runs = gh('run', 'list', '--workflow', 'pages.yml', '--branch', 'main', '--event', 'push',
              '--limit', '100', '--json', 'databaseId,workflowName,status,conclusion,headSha')
    main = gh('api', 'repos/{owner}/{repo}/commits/main').get('sha')
    if not isinstance(main, str) or not FULL_SHA.fullmatch(main):
        raise GhError('could not determine main head')
    for run in runs:
        sha = run.get('headSha', '')
        if not FULL_SHA.fullmatch(sha) or sha == commit or run.get('workflowName') != PAGES:
            continue
        relation = gh('api', f'repos/{{owner}}/{{repo}}/compare/{commit}...{sha}').get('status')
        if relation != 'ahead':
            continue
        if sha != main and gh('api', f'repos/{{owner}}/{{repo}}/compare/{sha}...{main}').get('status') != 'ahead':
            continue
        return run
    return None


def status(commit):
    """(exit code, run summaries) for the workflow runs of one commit."""
    runs = gh('run', 'list', '--commit', commit, '--limit', '50',
              '--json', 'databaseId,workflowName,status,conclusion,headSha')
    runs = [r for r in runs if r.get('headSha') == commit]
    summaries = []
    cancelled_pages = []
    for run in sorted(runs, key=lambda r: (r['workflowName'], r['databaseId'])):
        finished = run['status'] == 'completed'
        cancelled = finished and run.get('conclusion') == 'cancelled' and run['workflowName'] == PAGES
        red = finished and run.get('conclusion') not in OK_CONCLUSIONS and not cancelled
        summary = {'workflow': run['workflowName'], 'run_id': run['databaseId'],
                   'status': run['status'], 'conclusion': run.get('conclusion') or None,
                   'failed_steps': failed_steps(run['databaseId']) if red else []}
        summaries.append(summary)
        if cancelled:
            cancelled_pages.append(summary)
    if any(s['status'] == 'completed' and s['conclusion'] not in OK_CONCLUSIONS
           and s not in cancelled_pages for s in summaries):
        return RED, summaries
    if not summaries or any(s['status'] != 'completed' for s in summaries):
        return PENDING, summaries
    if cancelled_pages:
        # A skipped check, missing check, or skipped other workflow cannot establish success.
        others = [s for s in summaries if s not in cancelled_pages]
        if not any(s['workflow'] == CHECKS and s['conclusion'] == 'success' for s in others):
            return PENDING, summaries
        if any(s['conclusion'] != 'success' for s in others):
            return PENDING, summaries
        newer = superseding_pages(commit)
        if newer is None:
            return PENDING, summaries
        for summary in cancelled_pages:
            summary['superseded_by'] = newer['headSha']
            summary['superseding_status'] = newer['status']
            summary['superseding_conclusion'] = newer.get('conclusion') or None
            summary['superseding_run_id'] = newer['databaseId']
        if newer['status'] != 'completed' or newer.get('conclusion') == 'cancelled':
            return PENDING, summaries
        if newer.get('conclusion') != 'success':
            cancelled_pages[0]['failed_steps'] = failed_steps(newer['databaseId'])
            return RED, summaries
    return GREEN, summaries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--commit', help='commit SHA, short SHA or ref (default: HEAD)')
    parser.add_argument('--wait', type=float, default=0, metavar='SECONDS',
                        help='poll until no run is pending or this many seconds pass')
    parser.add_argument('--json', action='store_true', help='print a JSON record instead of text')
    args = parser.parse_args(argv)
    try:
        commit = resolve_commit(args.commit.strip() if args.commit else 'HEAD')
        deadline = time.monotonic() + args.wait
        code, summaries = status(commit)
        while code == PENDING and time.monotonic() < deadline:
            time.sleep(min(POLL_SECONDS, max(0.0, deadline - time.monotonic())))
            code, summaries = status(commit)
    except (GhError, subprocess.CalledProcessError) as error:
        print(f'UNAVAILABLE: {error}', file=sys.stderr)
        return UNAVAILABLE
    label = {GREEN: 'GREEN', RED: 'RED', PENDING: 'PENDING'}[code]
    if args.json:
        print(json.dumps({'commit': commit, 'result': label.lower(), 'runs': summaries}, indent=2))
    else:
        print(f'{label}: {commit}' + ('' if summaries else ' (no workflow runs yet)'))
        for s in summaries:
            print(f"  {s['workflow']} (run {s['run_id']}): {s['conclusion'] or s['status']}")
            if s.get('superseded_by'):
                sha = s['superseded_by'][:7]
                result = s['superseding_conclusion'] or s['superseding_status']
                print(f'    pages superseded by {sha}: {result}')
                if code == RED:
                    print(f'    newer Pages run {s["superseding_run_id"]} failed; older publish is unverified')
            for step in s['failed_steps']:
                print(f'    failed: {step}')
    return code


if __name__ == '__main__':
    sys.exit(main())
