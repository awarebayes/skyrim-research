"""Accept one function as `matched` after a Reviewer approve, or revoke an acceptance.

    python3 tools/accept_function.py --build-id <build id> --rva 0x<rva> \
        --review .local/reviews/<task-id>.md --verdict approve
    python3 tools/accept_function.py --build-id <build id> --rva 0x<rva> --revoke --reason '<why>'

Accepting is the integration step of the acceptance rule in docs/verification.md. The inventory
entry must already name a match record that tools/check.py accepts. The private review file is the
Reviewer's verbatim output (.claude/agents/reviewer.md); its block for this function must say
`approve` with no escalation, name the reviewer model, and give the translation-unit digest the
match record binds. The tool then writes the sanitized review record
(reports/<build id>/0x<rva>.review.json), sets that one entry to `matched`, updates `updated_at`,
and re-validates the whole inventory. It refuses on any inconsistency and changes nothing then.

Revoking sets the entry back to `mapped`, drops its `report`, and deletes its review and match
records; git history keeps both. The dated note in the function's finding is written by hand: the
tool prints what to add.

Neither mode commits. Stage the printed files by name and commit them with the evidence.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import (ROOT, REVIEW_RECORD_SCHEMA, review_record_path, validate,  # noqa: E402
                   validate_match, validate_review)
from source_digest import DIGEST_METHOD  # noqa: E402

PROGRESS = 'data/progress.json'
TARGET = 'builds/target.json'
REVIEWS = '.local/reviews'


class Refused(Exception):
    pass


def refuse(condition, message):
    if not condition:
        raise Refused(message)


def parse_rva(text):
    try:
        value = int(text, 16) if text.lower().startswith('0x') else int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f'not an RVA: {text}') from None
    if value < 0:
        raise argparse.ArgumentTypeError(f'not an RVA: {text}')
    return value


def fields(lines):
    out = {}
    for line in lines:
        match = re.fullmatch(r'([a-z_]+):\s*(.*?)\s*', line)
        if match and match.group(1) not in out:
            out[match.group(1)] = match.group(2)
    return out


def parse_review(text, build_id, rva):
    """Header fields and this function's block from a review in the reviewer.md output format."""
    lines = text.splitlines()
    title = next((m.group(1) for m in (re.fullmatch(r'# Review (\S+)\s*', l) for l in lines) if m), None)
    starts = [i for i, l in enumerate(lines) if l.startswith('## ')]
    header = fields(lines[:starts[0]] if starts else lines)
    blocks = []
    for n, i in enumerate(starts):
        parts = lines[i][3:].split()
        if len(parts) >= 2 and parts[0] == build_id:
            try:
                if int(parts[1], 16) == rva:
                    blocks.append(fields(lines[i + 1:starts[n + 1] if n + 1 < len(starts) else len(lines)]))
            except ValueError:
                continue
    refuse(len(blocks) == 1, f'review has {len(blocks)} blocks for {build_id} 0x{rva:x}; expected exactly 1')
    return title, header, blocks[0]


def load(root):
    return json.loads((root / PROGRESS).read_text()), json.loads((root / TARGET).read_text())


def entry_index(data, build_id, rva):
    hits = [i for i, fn in enumerate(data['functions']) if fn['build_id'] == build_id and fn['rva'] == rva]
    refuse(len(hits) == 1, f'{len(hits)} inventory entries for {build_id} 0x{rva:x}; expected exactly 1')
    return hits[0]


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def write_progress(root, data):
    (root / PROGRESS).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def unchanged_elsewhere(before, after, index):
    """The tool may touch one entry and updated_at; anything else changing is a bug, so refuse."""
    a, b = copy.deepcopy(before), copy.deepcopy(after)
    for d in (a, b):
        d.pop('updated_at')
        d['functions'].pop(index)
    refuse(a == b, 'internal error: other inventory data would change')


def accept(root, build_id, rva, review_file, verdict, when=None):
    root = Path(root)
    refuse(verdict == 'approve', f'verdict {verdict!r}: only approve is accepted; '
           'reject goes back to the Drafter or Engineer, escalate per docs/verification.md')
    data, target = load(root)
    validate(data, target, root)
    index = entry_index(data, build_id, rva)
    fn = data['functions'][index]
    refuse(fn['status'] != 'matched', f'{fn["id"]} is already matched')
    refuse(fn.get('report') is not None, f'{fn["id"]} names no match record (report)')
    record = validate_match(dict(fn, status='matched'), target, root)

    review_file = Path(review_file).resolve()
    private = (root / REVIEWS).resolve()
    # The full review may quote source; it must stay in the private reviews directory.
    refuse(private in review_file.parents, f'review file must be under {REVIEWS}/')
    refuse(review_file.is_file(), f'review file {review_file} does not exist')
    blob = review_file.read_bytes()
    title, header, block = parse_review(blob.decode('utf-8'), build_id, rva)
    refuse(title is not None and re.fullmatch(r'[a-z0-9][a-z0-9-]*', title),
           'review has no "# Review <task-id>" title with a lowercase task id')
    refuse(block.get('verdict') == verdict, f'review says verdict {block.get("verdict")!r}, not {verdict!r}')
    refuse(block.get('escalation_category') == 'none',
           f'review escalation_category is {block.get("escalation_category")!r}, not none')
    refuse(header.get('fresh_context') == 'yes', 'review does not state fresh_context: yes')
    refuse(header.get('drafted_or_triaged_any_reviewed_function') == 'no',
           'review does not state the Reviewer neither drafted nor triaged the function')
    refuse(bool(header.get('reviewer_model')), 'review names no reviewer_model')
    refuse(block.get('source_digest') == record['source']['digest'],
           'review source_digest differs from the match record: it reviewed other source')

    when = when or now_utc()
    review = {
        'review_record_schema': REVIEW_RECORD_SCHEMA,
        'function_id': fn['id'], 'build_id': fn['build_id'], 'rva': fn['rva'], 'size': fn['size'],
        'source_digest_method': DIGEST_METHOD, 'source_digest': record['source']['digest'],
        'reviewer_model': header['reviewer_model'], 'review_task_id': title,
        'verdict': verdict, 'escalation_category': 'none',
        'review_sha256': hashlib.sha256(blob).hexdigest(), 'review_date': when.date().isoformat(),
    }
    out = root / review_record_path(fn)
    refuse(not out.exists(), f'{review_record_path(fn)} already exists')
    new = copy.deepcopy(data)
    new['functions'][index]['status'] = 'matched'
    new['updated_at'] = when.strftime('%Y-%m-%dT%H:%M:%SZ')
    unchanged_elsewhere(data, new, index)
    out.write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
    try:
        validate_review(new['functions'][index], record, root)
        validate(new, target, root)
    except (ValueError, KeyError, TypeError) as exc:
        out.unlink()
        raise Refused(f'validator rejects the result: {exc}') from None
    write_progress(root, new)
    return [PROGRESS, review_record_path(fn)]


def revoke(root, build_id, rva, reason, when=None):
    root = Path(root)
    refuse(bool(reason and reason.strip()), 'revocation needs --reason')
    data, target = load(root)
    index = entry_index(data, build_id, rva)
    fn = data['functions'][index]
    refuse(fn['status'] == 'matched', f'{fn["id"]} is {fn["status"]}, not matched')
    when = when or now_utc()
    new = copy.deepcopy(data)
    entry = new['functions'][index]
    entry['status'] = 'mapped'
    record_path = entry.pop('report', None)
    new['updated_at'] = when.strftime('%Y-%m-%dT%H:%M:%SZ')
    unchanged_elsewhere(data, new, index)
    removed = [p for p in (review_record_path(fn), record_path) if p and (root / p).is_file()]
    saved = {name: (root / name).read_bytes() for name in removed}
    for name in removed:
        (root / name).unlink()
    try:
        validate(new, target, root)
    except (ValueError, KeyError, TypeError) as exc:
        for name, blob in saved.items():
            (root / name).write_bytes(blob)
        raise Refused(f'validator rejects the result: {exc}') from None
    write_progress(root, new)
    note = (f'- {when.date().isoformat()}: acceptance revoked; status back to `mapped`. Reason: {reason.strip()} '
            f'The earlier match record ({record_path}) stays in git history and is not current evidence.')
    return [PROGRESS] + removed, fn['evidence'], note


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--build-id', required=True)
    p.add_argument('--rva', required=True, type=parse_rva, help='RVA, hex with 0x or decimal')
    p.add_argument('--review', type=Path, help=f'Private review file under {REVIEWS}/')
    p.add_argument('--verdict', choices=['approve', 'reject', 'escalate'], help='Verdict parsed from the review')
    p.add_argument('--revoke', action='store_true', help='Revoke an accepted function')
    p.add_argument('--reason', help='Why the acceptance is revoked (with --revoke)')
    p.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = p.parse_args(argv)
    try:
        if args.revoke:
            refuse(args.review is None and args.verdict is None, '--revoke takes no --review or --verdict')
            changed, finding, note = revoke(args.root, args.build_id, args.rva, args.reason)
            print(f'revoked {args.build_id} 0x{args.rva:x}: status mapped')
            print(f'add this dated note to {finding} by hand:\n{note}')
            print('also update the contents tables in reports/README.md and reconstruction/README.md if they cite it')
        else:
            refuse(args.review is not None and args.verdict is not None, 'accepting needs --review and --verdict')
            changed = accept(args.root, args.build_id, args.rva, args.review, args.verdict)
            print(f'accepted {args.build_id} 0x{args.rva:x}: status matched, Reviewer record written')
    except Refused as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'REFUSED: inconsistent inputs: {exc}', file=sys.stderr)
        return 1
    print('changed files (stage these by name; nothing was committed):')
    for name in changed:
        gone = not (args.root / name).exists()
        # tools/check.py fails on a tracked file missing from disk until its deletion is staged.
        print(f'  {name}' + ('  (deleted: stage with git rm)' if gone else ''))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
