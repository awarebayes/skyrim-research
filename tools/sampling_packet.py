"""Compare a sampling safeguard's from-scratch re-run with the committed match records, and build
the label-only part of the sampling packet.

    python3 tools/sampling_packet.py --sample S.json --rerun DIR [--compare-out F] [--packet-out F]

`S.json` holds the drawn sample, `{"seed": ..., "reviewed": {unit: [rva, ...]}, "label_only":
{unit: [rva, ...]}}`; `DIR` holds the re-run records as `<build id>/<rva>.json` (written by
`tools/verifier/confirm` into a scratch directory). A function AGREEs when the re-run has the
committed record's source digest and result set, one code-section hash equal to the committed
one, and compiles on two hosts. The label-only packet gives, per unit, the approved digest the
carried-forward approval binds, the commit where the unit had it (recomputed from the committed
blobs), the full diff to HEAD, and the re-run verdict per sampled function.

`--compare FILE` reads the verdicts from an earlier comparison file instead of recomputing them.
Its rows end in AGREE or DISAGREE; they are read without their line endings, so a row's verdict
is not lost to a trailing newline (an ad hoc builder once printed DISAGREE for every function
that way).

Nothing here decides a sampling outcome: the Reviewer reads the packet; disagreements pause the
batch under `docs/verification.md`. The packet holds reconstructed source diffs (G2).
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_packet import digest_at  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BUILD = 'sse-steam-1-7-104'
COMMENT = re.compile(r'^[+-]\s*(//|/\*|\*)')


def summary(record):
    runs = record.get('runs') or []
    return (record['source']['digest'],
            {((r.get('report') or {}).get('result'), (r.get('report') or {}).get('reason')) for r in runs},
            {((r.get('report') or {}).get('candidate') or {}).get('code_section_sha256') for r in runs},
            sorted({r.get('compiled_on') for r in runs}), len(runs))


def compare(committed, rerun):
    """(agree, row text) for one function's committed and re-run records."""
    a_digest, a_results, a_hashes, _, a_runs = summary(committed)
    b_digest, b_results, b_hashes, b_hosts, b_runs = summary(rerun)
    ok = (a_digest == b_digest and a_results == b_results and a_hashes == b_hashes
          and len(b_hashes) == 1 and len(b_hosts) == 2)
    return ok, (f'runs {a_runs}/{b_runs} digest_same {a_digest == b_digest} hash_same {a_hashes == b_hashes} '
                f'n_hash {len(b_hashes)} result {sorted(map(str, b_results))} compile_hosts {b_hosts} '
                + ('AGREE' if ok else 'DISAGREE'))


def parse_rows(lines):
    """{rva: 'AGREE' | 'DISAGREE'} from comparison rows `<group> <unit> <rva> ... <verdict>`."""
    out = {}
    for line in lines:
        parts = line.rstrip('\r\n').split()
        if len(parts) >= 4 and parts[-1] in ('AGREE', 'DISAGREE') and parts[2].startswith('0x'):
            out[parts[2]] = parts[-1]
    return out


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def comment_only(diff):
    """Changed lines of a unified diff that are neither comments nor blank."""
    changed = [l for l in diff.splitlines() if l[:1] in '+-' and not l.startswith(('+++', '---'))]
    return [l for l in changed if not COMMENT.match(l) and l[1:].strip()]


def label_packet(root, sample, verdicts, build=BUILD):
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    out = ['# Sampling packet: label-only re-acceptances', '',
           f'Seed "{sample.get("seed")}". For each unit: the approved digest the carried-forward approval binds,',
           'the commit where the unit had that digest (tu-sha256-v1 recomputed from the committed blobs),',
           f'and the full diff to {head[:12]}. Question for the Reviewer: is every changed line a comment',
           'or label line, with no token of code changed? The from-scratch re-run is summarised per function.', '']
    problems = []
    for unit, rvas in sample.get('label_only', {}).items():
        reviews = [json.loads((root / f'reports/{build}/{r}.review.json').read_text()) for r in rvas]
        record = json.loads((root / f'reports/{build}/{rvas[0]}.json').read_text())
        files = record['source']['translation_unit']
        previous = {r.get('previous_source_digest') for r in reviews}
        current = {r.get('source_digest') for r in reviews}
        if len(previous) != 1 or len(current) != 1:
            problems.append(f'{unit}: sampled reviews disagree on their digests')
            continue
        previous, current = previous.pop(), current.pop()
        base = next((c for c in git(root, 'log', '--format=%H', head, '--', *files).decode().split()
                     if digest_at(root, c, files) == previous), None)
        out += [f'## Unit {unit}', '', f'translation unit: {", ".join(files)}', f'approved digest: {previous}',
                f'base commit with that digest: {base or "NOT FOUND"}', f'accepted digest: {current}', '',
                'sampled functions:']
        for rva, review in zip(rvas, reviews):
            verdict = verdicts.get(rva, 'MISSING')
            out.append(f'- {rva} size {review.get("size")}: code section {review.get("code_section_sha256")} '
                       f'(approved record {review.get("previous_code_section_sha256")}); re-run '
                       + ('AGREE, pass on both machines' if verdict == 'AGREE' else verdict))
            if verdict != 'AGREE':
                problems.append(f'{unit} {rva}: re-run {verdict}')
        out.append('')
        if base is None:
            problems.append(f'{unit}: no commit with the approved digest')
            continue
        diff = git(root, 'diff', '--no-color', '-U3', base, head, '--', *files).decode()
        if comment_only(diff):
            problems.append(f'{unit}: non-comment lines changed')
        out += ['```diff', diff.rstrip('\n'), '```', '']
    return out, problems


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('--sample', type=Path, required=True)
    p.add_argument('--rerun', type=Path, help='directory with <build>/<rva>.json re-run records')
    p.add_argument('--compare', type=Path, help='read verdicts from an earlier comparison file instead')
    p.add_argument('--compare-out', type=Path)
    p.add_argument('--packet-out', type=Path)
    p.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = p.parse_args(argv)
    root, sample = args.root, json.loads(args.sample.read_text())
    if args.compare:
        verdicts = parse_rows(args.compare.read_text().splitlines(keepends=True))
    elif args.rerun:
        rows, verdicts = [], {}
        for group in ('reviewed', 'label_only'):
            for unit, rvas in sample.get(group, {}).items():
                for rva in rvas:
                    committed = json.loads((root / f'reports/{BUILD}/{rva}.json').read_text())
                    rerun = json.loads((args.rerun / BUILD / f'{rva}.json').read_text())
                    ok, row = compare(committed, rerun)
                    verdicts[rva] = 'AGREE' if ok else 'DISAGREE'
                    rows.append(f'{group:10} {unit:30} {rva:10} {row}')
        text = '\n'.join(rows) + '\n'
        if args.compare_out:
            args.compare_out.write_text(text)
        print(text, end='')
        print(f'agree {sum(v == "AGREE" for v in verdicts.values())} of {len(verdicts)}')
    else:
        p.error('give --rerun or --compare')
    if args.packet_out:
        out, problems = label_packet(root, sample, verdicts)
        args.packet_out.write_text('\n'.join(out) + '\n')
        print(f'packet: {args.packet_out}; problems: {len(problems)}')
        for line in problems:
            print(f'  {line}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
