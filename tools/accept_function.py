"""Accept functions as `matched` after a Reviewer approve, re-approve stale ones, or revoke.

    python3 tools/accept_function.py --build-id <build id> --rva 0x<rva> \
        --review .local/reviews/<task-id>.md --verdict approve
    python3 tools/accept_function.py --all-approved --review <file or ->
    python3 tools/accept_function.py --build-id <build id> --rva 0x<rva> --revoke --reason '<why>'

Accepting is the integration step of the acceptance rule in docs/verification.md. Each inventory
entry must already name a match record that tools/check.py accepts. The review is the Reviewer's
output (.claude/agents/reviewer.md); its block for each function must say `approve` with no
escalation, name the reviewer model, and give the translation-unit digest the match record binds.
`--all-approved` accepts every `approve` block of the review in one step and lists the blocks it
did not accept; any refusal leaves everything unchanged. The tool writes the sanitized review
records (reports/<build id>/0x<rva>.review.json, schema 2), sets those entries to `matched`,
refreshes `updated_at` and reconstruction/INDEX.md, re-validates the whole inventory and prints
the files to stage. It refuses on any inconsistency and changes nothing then.

The review is read from a file under .local/reviews/, from another file outside the repository
(a saved transcript) or from stdin (`--review -`). Text before the `# Review <task-id>` line, and
a code fence around it, is dropped; the rest is saved verbatim to .local/reviews/<task-id>.md,
the private file the record's hash binds. A file inside the repository but outside .local/ is
refused, since it could be published.

A `matched` entry whose Reviewer record binds an earlier digest (stale, "review behind") is
re-approved by a full review, or by a delta review: a block with `review_kind: delta`,
`previous_source_digest: <the approved digest>` and `code_section_unchanged: yes`. A delta is
accepted only if the superseded record approved exactly that digest and the compared code
section hash is the same in the approved and the current match record (docs/verification.md,
"Stale acceptances and delta reviews").

Revoking sets the entry back to `mapped`, drops its `report`, and deletes its review and match
records; git history keeps both. The dated note in the function's finding is written by hand: the
tool prints what to add.

No mode commits. Stage the printed files by name and commit them with the evidence.
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
from check import (ROOT, REVIEW_RECORD_SCHEMA, _json_or_none, record_code_section,  # noqa: E402
                   review_record_path, validate, validate_match, validate_review)
from build_index import INDEX, write_index  # noqa: E402
from source_digest import DIGEST_METHOD  # noqa: E402
import review_packet  # noqa: E402

PROGRESS = 'data/progress.json'
TARGET = 'builds/target.json'
REVIEWS = '.local/reviews'
TASK_ID = re.compile(r'[a-z0-9][a-z0-9-]*')


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


def review_blocks(text):
    """(title, header fields, [(heading words, block fields)]) of a review in reviewer.md format."""
    lines = text.splitlines()
    title = next((m.group(1) for m in (re.fullmatch(r'# Review (\S+)\s*', l) for l in lines) if m), None)
    starts = [i for i, l in enumerate(lines) if l.startswith('## ')]
    header = fields(lines[:starts[0]] if starts else lines)
    blocks = []
    for n, i in enumerate(starts):
        body = fields(lines[i + 1:starts[n + 1] if n + 1 < len(starts) else len(lines)])
        blocks.append((lines[i][3:].split(), body))
    return title, header, blocks


def parse_review(text, build_id, rva, size):
    """Header fields and this function's block from a review in the reviewer.md output format.

    The block heading is `## <build id> 0x<rva> <size>`; the size must equal the inventory's, so a
    review of a differently sized range at the same address is not taken for this function.
    """
    title, header, all_blocks = review_blocks(text)
    blocks = []
    for parts, body in all_blocks:
        if len(parts) >= 2 and parts[0] == build_id:
            try:
                if int(parts[1], 16) == rva:
                    blocks.append((parts[2:], body))
            except ValueError:
                continue
    refuse(len(blocks) == 1, f'review has {len(blocks)} blocks for {build_id} 0x{rva:x}; expected exactly 1')
    rest, block = blocks[0]
    refuse(len(rest) == 1 and rest[0] == str(size),
           f'review block for {build_id} 0x{rva:x} gives size {" ".join(rest) or "none"}, not the inventory size {size}')
    return title, header, block


def extract_review(text):
    """The review document from a transcript: from `# Review <id>` on, without an enclosing fence."""
    lines = text.splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if re.fullmatch(r'# Review \S+\s*', l)), None)
    refuse(start is not None, 'review has no "# Review <task-id>" title')
    fenced = start > 0 and lines[start - 1].lstrip().startswith('```')
    body = lines[start:]
    if fenced:
        end = next((i for i, l in enumerate(body) if l.strip().startswith('```')), len(body))
        body = body[:end]
    return ''.join(body).rstrip('\n') + '\n'


def private_review(root, source):
    """Path and bytes of the private review file, saving stdin or an outside file under REVIEWS/."""
    private = (root / REVIEWS).resolve()
    if source != '-':
        path = Path(source).resolve()
        if private in path.parents:
            refuse(path.is_file(), f'review file {path} does not exist')
            return path, path.read_bytes()
        # The full review may quote source; a copy inside the repository could be committed.
        refuse(root.resolve() not in path.parents or (root / '.local').resolve() in path.parents,
               f'review file must be under {REVIEWS}/ or outside the repository')
        refuse(path.is_file(), f'review file {path} does not exist')
        raw = path.read_text(encoding='utf-8')
    else:
        raw = sys.stdin.read()
    blob = extract_review(raw).encode('utf-8')
    title = re.match(r'# Review (\S+)', blob.decode()).group(1)
    refuse(bool(TASK_ID.fullmatch(title)), 'review has no "# Review <task-id>" title with a lowercase task id')
    out = private / f'{title}.md'
    refuse(not out.exists() or out.read_bytes() == blob,
           f'{REVIEWS}/{title}.md already exists with other content; use a new review task id')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    return out, blob


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


def unchanged_elsewhere(before, after, indices):
    """The tool may touch the named entries and updated_at; anything else changing is a bug, so refuse."""
    a, b = copy.deepcopy(before), copy.deepcopy(after)
    for d in (a, b):
        d.pop('updated_at')
        d['functions'] = [fn for i, fn in enumerate(d['functions']) if i not in set(indices)]
    refuse(a == b, 'internal error: other inventory data would change')


def review_record(fn, record, header, title, blob, when, kind, previous=None, old_section=None):
    section = record_code_section(record)
    return {
        'review_record_schema': REVIEW_RECORD_SCHEMA,
        'function_id': fn['id'], 'build_id': fn['build_id'], 'rva': fn['rva'], 'size': fn['size'],
        'source_digest_method': DIGEST_METHOD, 'source_digest': record['source']['digest'],
        'reviewer_model': header['reviewer_model'], 'review_task_id': title,
        'verdict': 'approve', 'escalation_category': 'none',
        'review_sha256': hashlib.sha256(blob).hexdigest(), 'review_date': when.date().isoformat(),
        'review_kind': kind,
        'previous_source_digest': previous['source_digest'] if previous else None,
        'previous_review_sha256': previous['review_sha256'] if previous else None,
        'previous_code_section_sha256': old_section,
        'code_section_sha256': section,
    }


def prepare(root, data, target, index, title, header, block, blob, when):
    """The review record to write for one function, after every check that needs no write."""
    fn = data['functions'][index]
    refuse(fn.get('report') is not None, f'{fn["id"]} names no match record (report)')
    record = validate_match(dict(fn, status='matched'), target, root)
    refuse(block.get('verdict') == 'approve', f'review says verdict {block.get("verdict")!r}, not \'approve\'')
    refuse(block.get('escalation_category') == 'none',
           f'review escalation_category is {block.get("escalation_category")!r}, not none')
    refuse(block.get('source_digest') == record['source']['digest'],
           'review source_digest differs from the match record: it reviewed other source')
    kind = block.get('review_kind') or 'full'
    refuse(kind in {'full', 'delta'}, f'review_kind {kind!r} is neither full nor delta')
    out = root / review_record_path(fn)
    previous = None
    if fn['status'] == 'matched':
        previous = _json_or_none(out)
        refuse(previous is not None and previous.get('source_digest') != record['source']['digest'],
               f'{fn["id"]} is already matched')
        # The superseded approval must be a real one for this function, or a delta would chain from nothing.
        refuse(previous.get('verdict') == 'approve' and previous.get('function_id') == fn['id'],
               f'{review_record_path(fn)} is not an approve for {fn["id"]}')
    else:
        refuse(not out.exists(), f'{review_record_path(fn)} already exists')
    if kind == 'full':
        # A full review stands on its own; it carries no link to the approval it replaces.
        return fn, record, review_record(fn, record, header, title, blob, when, 'full')
    refuse(previous is not None, f'{fn["id"]} has no earlier approval; a delta review needs one, do a full review')
    refuse(block.get('previous_source_digest') == previous['source_digest'],
           'delta review previous_source_digest is not the digest the superseded Reviewer record approved')
    refuse(block.get('code_section_unchanged') == 'yes', 'delta review does not state code_section_unchanged: yes')
    current = record_code_section(record)
    refuse(current is not None, 'the match record carries no code-section hash (candidate.code_section_sha256); '
           'a delta review needs one, do a full review')
    old, where = review_packet.previous_code_section(root, fn, previous['source_digest'])
    refuse(old is not None, f'no code-section hash for the approved digest ({where}); do a full review')
    refuse(old == current, 'the compared code section changed since the approved digest; do a full review')
    return fn, record, review_record(fn, record, header, title, blob, when, 'delta', previous, old)


def accept_many(root, review_source, targets=None, verdict='approve', when=None):
    """Accept the approve blocks of one review: `targets` [(build id, rva)] or None for all of them.

    Returns (changed files, skipped block headings). All-or-nothing: every check runs before the
    first write, and any failure after it restores every file it touched.
    """
    root = Path(root)
    refuse(verdict == 'approve', f'verdict {verdict!r}: only approve is accepted; '
           'reject goes back to the Drafter or Engineer, escalate per docs/verification.md')
    data, target = load(root)
    # Stale acceptances are what a delta or re-review clears, so they may be present before; the
    # final validation below is strict.
    validate(data, target, root, stale_ok=True)
    review_file, blob = private_review(root, review_source)
    title, header, blocks = review_blocks(blob.decode('utf-8'))
    refuse(title is not None and TASK_ID.fullmatch(title),
           'review has no "# Review <task-id>" title with a lowercase task id')
    refuse(header.get('fresh_context') == 'yes', 'review does not state fresh_context: yes')
    refuse(header.get('drafted_or_triaged_any_reviewed_function') == 'no',
           'review does not state the Reviewer neither drafted nor triaged the function')
    refuse(bool(header.get('reviewer_model')), 'review names no reviewer_model')
    skipped = []
    if targets is None:
        targets = []
        for parts, body in blocks:
            if body.get('verdict') != 'approve':
                skipped.append(f'{" ".join(parts)}: verdict {body.get("verdict")}')
                continue
            refuse(len(parts) >= 2 and re.fullmatch(r'0x[0-9a-fA-F]+', parts[1]),
                   f'review block heading "## {" ".join(parts)}" is not "<build id> 0x<rva> <size>"')
            targets.append((parts[0], int(parts[1], 16)))
        refuse(targets, 'review has no approve block')
    when = when or now_utc()
    prepared = []
    for build_id, rva in targets:
        index = entry_index(data, build_id, rva)
        refuse(index not in [i for i, *_ in prepared], f'{build_id} 0x{rva:x} is named twice')
        _, _, block = parse_review(blob.decode('utf-8'), build_id, rva, data['functions'][index]['size'])
        prepared.append((index, *prepare(root, data, target, index, title, header, block, blob, when)))
    new = copy.deepcopy(data)
    for index, *_ in prepared:
        new['functions'][index]['status'] = 'matched'
    new['updated_at'] = when.strftime('%Y-%m-%dT%H:%M:%SZ')
    unchanged_elsewhere(data, new, [i for i, *_ in prepared])
    touched = [PROGRESS, INDEX] + [review_record_path(fn) for _, fn, _, _ in prepared]
    saved = {name: (root / name).read_bytes() if (root / name).is_file() else None for name in touched}
    # From the first write on, any failure, including an interrupt or a failed progress write, must
    # leave neither a review record nor a half-updated inventory behind.
    try:
        for _, fn, _, review in prepared:
            (root / review_record_path(fn)).write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
        try:
            for index, _, record, _ in prepared:
                validate_review(new['functions'][index], record, root)
            validate(new, target, root)
        except (ValueError, KeyError, TypeError) as exc:
            raise Refused(f'validator rejects the result: {exc}') from None
        write_progress(root, new)
        write_index(new, root)
    except BaseException:
        for name, blob_before in saved.items():
            if blob_before is None:
                (root / name).unlink(missing_ok=True)
            else:
                (root / name).write_bytes(blob_before)
        raise
    changed = [PROGRESS] + [review_record_path(fn) for _, fn, _, _ in prepared]
    if saved[INDEX] != (root / INDEX).read_bytes():
        changed.append(INDEX)
    return changed, skipped


def accept(root, build_id, rva, review_file, verdict, when=None):
    """Accept one function from a review file; returns the changed files."""
    return accept_many(root, review_file, [(build_id, rva)], verdict, when)[0]


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
    unchanged_elsewhere(data, new, [index])
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
    write_index(new, root)
    note = (f'- {when.date().isoformat()}: acceptance revoked; status back to `mapped`. Reason: {reason.strip()} '
            f'The earlier match record ({record_path}) stays in git history and is not current evidence.')
    return [PROGRESS, INDEX] + removed, fn['evidence'], note


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--build-id')
    p.add_argument('--rva', type=parse_rva, help='RVA, hex with 0x or decimal')
    p.add_argument('--review', help=f'Review file under {REVIEWS}/ or outside the repository, or - for stdin')
    p.add_argument('--verdict', choices=['approve', 'reject', 'escalate'], help='Verdict parsed from the review')
    p.add_argument('--all-approved', action='store_true', help='Accept every approve block of the review')
    p.add_argument('--revoke', action='store_true', help='Revoke an accepted function')
    p.add_argument('--reason', help='Why the acceptance is revoked (with --revoke)')
    p.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = p.parse_args(argv)
    skipped = []
    try:
        if args.revoke:
            refuse(args.review is None and args.verdict is None and not args.all_approved,
                   '--revoke takes no --review, --verdict or --all-approved')
            refuse(args.build_id is not None and args.rva is not None, '--revoke needs --build-id and --rva')
            changed, finding, note = revoke(args.root, args.build_id, args.rva, args.reason)
            print(f'revoked {args.build_id} 0x{args.rva:x}: status mapped')
            print(f'add this dated note to {finding} by hand:\n{note}')
        elif args.all_approved:
            refuse(args.review is not None, '--all-approved needs --review')
            refuse(args.build_id is None and args.rva is None, '--all-approved takes no --build-id or --rva')
            refuse(args.verdict in (None, 'approve'), '--all-approved accepts approve blocks only')
            changed, skipped = accept_many(args.root, args.review)
            print(f'accepted {sum(n.endswith(".review.json") for n in changed)} function(s): status matched, Reviewer records written')
        else:
            refuse(args.review is not None and args.verdict is not None, 'accepting needs --review and --verdict')
            refuse(args.build_id is not None and args.rva is not None, 'accepting one function needs --build-id and --rva')
            changed = accept(args.root, args.build_id, args.rva, args.review, args.verdict)
            print(f'accepted {args.build_id} 0x{args.rva:x}: status matched, Reviewer record written')
    except Refused as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'REFUSED: inconsistent inputs: {exc}', file=sys.stderr)
        return 1
    for line in skipped:
        print(f'not accepted (not approve): {line}')
    print('changed files (stage these by name; nothing was committed):')
    for name in changed:
        gone = not (args.root / name).exists()
        # tools/check.py fails on a tracked file missing from disk until its deletion is staged.
        print(f'  {name}' + ('  (deleted: stage with git rm)' if gone else ''))
    print('stage with: git add -- ' + ' '.join(n for n in changed if (args.root / n).exists())
          + ''.join(f'; git rm --cached -- {n}' for n in changed if not (args.root / n).exists()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
