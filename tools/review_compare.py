#!/usr/bin/env python3
"""Compare the per-function verdicts of sets of saved reviews (for example Sonnet and Terra
Reviewers' blind re-reviews against the Opus reviews of the same functions at the same revision).

    python3 tools/review_compare.py --set opus R1.md [R2.md ...] --set sonnet S1.md ... [--set terra T1.md ...] [--json]
    python3 tools/review_compare.py --reference R1.md ... --candidate C1.md ...

The first set is the reference; every later set is compared with it separately.

Blocks are matched by their heading (`<build id> 0x<rva> <size>`). For each function present in
either set it prints both verdicts, whether they agree, whether both reviewed the same source digest,
which blocking checks each failed and how many blocking findings each listed. The summary counts
agreements and the two kinds of disagreement that matter for calibration:

- missed: the reference rejected or escalated, the candidate approved (the dangerous kind);
- stricter: the reference approved, the candidate did not.

Reviews are read with the acceptance tool's block parser; a review it would refuse is reported as
such (and its blocks still compared, marked `malformed`), since calibration measures judgement, not
format. Exit status 0 when every shared function agrees, 1 otherwise, 2 on unreadable input. It
prints verdict words, check names and counts only, never review prose.
"""
import argparse
import json
from pathlib import Path
import re
import sys

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import accept_function as af  # noqa: E402


def blocks_of(paths):
    """({heading: summary}, [problems]) over several review files."""
    out, problems = {}, []
    for path in paths:
        text = Path(path).read_text(encoding='utf-8')
        title, header, blocks = af.review_blocks(text)
        bad = list(header.get('_problems') or [])
        for parts, body in blocks:
            heading = ' '.join(parts)
            if not (len(parts) == 3 and re.fullmatch(r'0x[0-9a-f]+', parts[1])):
                continue
            if body.get('_problems'):
                bad.append(f'{heading}: {"; ".join(body["_problems"])}')
            if heading in out:
                problems.append(f'{heading} appears in more than one review of the same set ({out[heading]["file"]}, {path})')
            out[heading] = {'file': str(path), 'verdict': body.get('verdict'), 'digest': body.get('source_digest'),
                            'category': body.get('escalation_category'),
                            'failed_checks': sorted(k for k, v in (body.get('_checks') or {}).items() if v.startswith('fail')),
                            'blocking_findings': len(body.get('_blocking_findings') or []),
                            'naming_findings': len(body.get('_naming_findings') or []),
                            'malformed': bool(body.get('_problems'))}
        if bad:
            problems.append(f'{path}: the acceptance tool would refuse it: {bad[0]}' + (f' (+{len(bad) - 1} more)' if len(bad) > 1 else ''))
    return out, problems


def compare(reference, candidate):
    rows = []
    for heading in sorted(set(reference) | set(candidate), key=lambda h: (h.split()[0], int(h.split()[1], 16))):
        a, b = reference.get(heading), candidate.get(heading)
        row = {'function': heading, 'reference': a and a['verdict'], 'candidate': b and b['verdict'],
               'same_digest': bool(a and b and a['digest'] == b['digest']),
               'reference_failed': a and a['failed_checks'], 'candidate_failed': b and b['failed_checks'],
               'reference_blocking': a and a['blocking_findings'], 'candidate_blocking': b and b['blocking_findings']}
        if a is None or b is None:
            row['outcome'] = 'only-reference' if b is None else 'only-candidate'
        elif a['verdict'] == b['verdict']:
            row['outcome'] = 'agree'
        elif a['verdict'] != 'approve' and b['verdict'] == 'approve':
            row['outcome'] = 'missed'
        elif a['verdict'] == 'approve':
            row['outcome'] = 'stricter'
        else:
            row['outcome'] = 'differ'
        rows.append(row)
    counts = {}
    for r in rows:
        counts[r['outcome']] = counts.get(r['outcome'], 0) + 1
    shared = [r for r in rows if r['outcome'] not in ('only-reference', 'only-candidate')]
    return rows, {'functions': len(rows), 'shared': len(shared), **counts,
                  'agreement': round(counts.get('agree', 0) / len(shared), 3) if shared else None,
                  'reference_non_approve': sum(1 for r in shared if r['reference'] != 'approve'),
                  'caught': sum(1 for r in shared if r['reference'] != 'approve' and r['candidate'] != 'approve')}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--set', nargs='+', action='append', default=[], metavar=('LABEL', 'FILE'),
                   help='a label and its review files; the first set is the reference, each later one a candidate')
    p.add_argument('--reference', nargs='+', help='same as a first --set labelled "reference"')
    p.add_argument('--candidate', nargs='+', help='same as a later --set labelled "candidate"')
    p.add_argument('--json', action='store_true')
    a = p.parse_args(argv)
    sets = ([['reference', *a.reference]] if a.reference else []) + a.set + ([['candidate', *a.candidate]] if a.candidate else [])
    if len(sets) < 2 or any(len(s) < 2 for s in sets):
        p.error('give at least two sets, each a label and one or more review files')
    try:
        parsed = [(s[0], *blocks_of(s[1:])) for s in sets]
    except (OSError, UnicodeDecodeError) as exc:
        print(f'review_compare: {exc}', file=sys.stderr)
        return 2
    ref_label, ref, ref_problems = parsed[0]
    result, worst = [], 0
    for label, cand, problems in parsed[1:]:
        rows, summary = compare(ref, cand)
        summary['problems'] = ref_problems + problems
        result.append({'reference': ref_label, 'candidate': label, 'summary': summary, 'rows': rows})
        if any(r['outcome'] not in ('agree', 'only-reference', 'only-candidate') for r in rows):
            worst = 1
    if a.json:
        print(json.dumps(result if len(result) > 1 else result[0], indent=2))
        return worst
    for res in result:
        print(f'## {res["candidate"]} against {res["reference"]}\n')
        print(f'| function | {res["reference"]} | {res["candidate"]} | outcome | same digest | '
              f'{res["reference"]} failed | {res["candidate"]} failed |')
        print('|---|---|---|---|---|---|---|')
        for r in res['rows']:
            print(f'| {r["function"]} | {r["reference"]} | {r["candidate"]} | {r["outcome"]} | '
                  f'{"yes" if r["same_digest"] else "NO"} | {",".join(r["reference_failed"] or []) or "-"} | '
                  f'{",".join(r["candidate_failed"] or []) or "-"} |')
        print()
        print(json.dumps({k: v for k, v in res['summary'].items() if k != 'problems'}))
        for line in res['summary']['problems']:
            print(f'note: {line}')
        print()
    return worst


if __name__ == '__main__':
    raise SystemExit(main())
