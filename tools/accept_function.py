"""Accept functions as `matched` after a Reviewer approve, re-accept label-only changes, or revoke.

    python3 tools/accept_function.py --build-id <build id> --rva 0x<rva> \
        --review .local/reviews/<task-id>.md --verdict approve
    python3 tools/accept_function.py --all-approved --review <file or -> [--functions ...] [--units ...]
    python3 tools/accept_function.py --family-batch reports/<build>/family-batches/<batch>.json
    python3 tools/accept_function.py --label-only [--functions ...] [--units ...]
    python3 tools/accept_function.py --refresh-named [--functions ...] [--units ...]
    python3 tools/accept_function.py --build-id <build id> --rva 0x<rva> --revoke --reason '<why>'

Accepting is the integration step of the acceptance rule in docs/verification.md (tier 1). Each
inventory entry must already name a match record that tools/check.py accepts. The review is the
Reviewer's output (.claude/agents/reviewer.md); its block for each function must say `approve`
with no escalation, name the reviewer model, give the translation-unit digest the match record
binds, `report_binding: agree`, `pass` for the four blocking checks, `blocking_findings: none` and
a `naming_findings` field. The header and every function block must keep to that format exactly
(`fields`, `refuse_malformed`; the grammar is written out in tests/test_review_mutations.py): an
unknown or repeated key, a stray line, a list value other than `none` or items, a closed-word value
in another spelling, a block cut short, a function heading other than exactly
`<build id> 0x<rva> <size>`, a second title or an unseen character refuses the whole review. `--all-approved` accepts every `approve` block of the review in one step
and lists the blocks it did not accept; `--functions` (inventory ids or 0x<rva>) and `--units`
(compiled file or <area>/<Class>) restrict it to those functions, each of which must then have an
approve block. Any refusal leaves everything unchanged. The tool writes the sanitized review
records (reports/<build id>/0x<rva>.review.json, schema 3, with the naming findings), sets those
entries to `matched`, sets tier 2 (`named`), refreshes `updated_at` and reconstruction/INDEX.md,
re-validates the whole inventory and prints the files to stage. Entries outside the selection
that were already stale before the run may stay stale; everything else must validate.

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
"Stale acceptances and delta reviews"). When that hash is unchanged, `--label-only` re-accepts
the entry with no Reviewer pass ("Label-only re-acceptance"), carrying the approval forward.

`--refresh-named` recomputes tier 2 for current `matched` entries: `named` is true when the
Reviewer record lists no open naming finding and tools/check_labels.py reports nothing for every
file of the unit, each declaring `Labels: v2`. The label check reads the private community
checkouts; without them it reports findings, which gives `false`.

Revoking sets the entry back to `mapped`, drops its `report` and `named`, and deletes its review
and match records; git history keeps both. The dated note in the function's finding is written by
hand: the tool prints what to add.

--family-batch accepts only unsampled in-range members of an active, approved family after the
committed draw, all sampled individual approvals and their sampling safeguards. Its schema 4
records name the saved family review rather than claiming an individual review. The ordinary
comparator and validator checks still apply.

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
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import (ROOT, LABEL_ONLY, MAX_NAMING_FINDINGS, REVIEW_RECORD_SCHEMA,  # noqa: E402
                   REVIEW_SCHEMA_FIELDS, STALE_REVIEW, STALE_UNIT, _json_or_none, acceptance_staleness,
                   is_hash, naming_finding_problem, record_code_section, review_record_path, validate,
                   validate_match, validate_review)
from build_index import INDEX, write_index  # noqa: E402
from lint_reconstruction import LABELS_VERSION, lint_tree  # noqa: E402
from source_digest import DIGEST_METHOD  # noqa: E402
import review_packet  # noqa: E402
import family_review as fr  # noqa: E402

PROGRESS = 'data/progress.json'
TARGET = 'builds/target.json'
REVIEWS = '.local/reviews'
TASK_ID = re.compile(r'[a-z0-9][a-z0-9-]*')
# The Reviewer's blocking grounds that have a check line (docs/verification.md, tier 1 item 3);
# record binding is `report_binding`. An approve must pass all of them.
BLOCKING_CHECKS = ('plausible_source', 'provenance', 'claim_scope', 'publication_hygiene')
LIST_FIELDS = ('naming_findings', 'blocking_findings')


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


HEADER_FIELDS = ('reviewer_model', 'fresh_context', 'drafted_or_triaged_any_reviewed_function', 'gates_in_force',
                 'source_revision', 'sampling_second_pass', 'decompiler_output_read')
BLOCK_FIELDS = ('verdict', 'escalation_category', 'review_kind', 'previous_source_digest', 'code_section_unchanged',
                'source_paths', 'source_digest', 'report_path', 'report_binding', 'checks', 'blocking_findings',
                'naming_findings', 'prior_review', 'reasons')
# A function block missing any of these is cut short or malformed; `reasons` is the format's last field.
BLOCK_REQUIRED = ('verdict', 'escalation_category', 'source_paths', 'source_digest', 'report_path',
                  'report_binding', 'checks', 'blocking_findings', 'naming_findings', 'reasons')
# Fields whose value is a closed word list (reviewer.md output format). A case change or a look-alike
# letter in a verdict word must refuse the review, not read as some other verdict.
YES_NO = ('yes', 'no')
VALUE_WORDS = {
    'fresh_context': YES_NO, 'drafted_or_triaged_any_reviewed_function': YES_NO,
    'sampling_second_pass': YES_NO, 'decompiler_output_read': YES_NO,
    'verdict': ('approve', 'reject', 'escalate'),
    'escalation_category': ('provenance', 'legal', 'systemic', 'other', 'none'),
    'review_kind': ('full', 'delta'), 'code_section_unchanged': YES_NO,
}
# These take one of their words, optionally followed by a comma and a one-line comment.
COMMENTED_WORDS = {'report_binding': ('agree', 'disagree', 'missing')}
CHECK_WORDS = ('pass', 'fail')
# A list item's text may not itself start with a bullet: `  - - x` is a duplicated dash, not a finding.
BULLET_START = re.compile(r'[-*+\u2010-\u2015\u2022\u2212\u00b7]')
TITLE = re.compile(r'# Review \S+\s*')


def commented(value, words):
    """True if `value` is one of `words`, alone or followed by a comma and a comment."""
    return value.split(',')[0].rstrip() in words and (value in words or re.fullmatch(r'\S+\s*,.*', value) is not None)


def fields(lines, known=None, required=()):
    """Parse `key: value` lines; `checks` sub-lines go to `_checks`, `- item` lines under a list
    field (LIST_FIELDS) to `_<field>`. Every deviation from the reviewer.md format is listed in
    `_problems`; the acceptance tool refuses a block or header that has any.

    The parser fails closed: only the literal `none` makes a list empty; a list written with an empty
    value must have items, so a finding written without its dash cannot vanish into an empty list.
    A line that is neither a field, a `checks` sub-line, a list item, a continuation of an item
    (indented at least to the item's text) or of `reasons`, nor blank, is a problem, as are unknown
    keys (when `known` is given), duplicate keys, sub-keys and items, a value outside its word list
    (VALUE_GRAMMAR), a continuation that reads as a field, and a missing required field. Packet tools
    that only display an old review read the same dict and ignore `_problems`.
    """
    out, checks, lists, problems = {}, {}, {}, []
    current = None       # field the following indented lines belong to
    item_indent = None   # indent of the last list item's dash, for continuations
    field_like = re.compile(r'([a-z][a-z_]*)\s*:')
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        # Keys start with a letter, so no review line can set the parsed `_` entries directly.
        match = re.fullmatch(r'([a-z][a-z_]*):(?:\s+(.*?))?\s*', line)
        if match:
            key, value = match.group(1), match.group(2) or ''
            current, item_indent = key, None
            if known is not None and key not in known:
                problems.append(f'line {number}: unknown field {key!r}')
            if key in out:
                problems.append(f'line {number}: field {key!r} given twice')
                current = None
                continue
            out[key] = value
            if key in LIST_FIELDS:
                if value == 'none':
                    lists[key] = []
                elif value:
                    problems.append(f'line {number}: {key} is "none" or a list of "  - <item>" lines, not {value!r}')
                else:
                    lists[key] = []
            elif key == 'checks':
                if value:
                    problems.append(f'line {number}: checks takes no value, only indented sub-lines')
            elif not value:
                problems.append(f'line {number}: field {key!r} is empty')
            elif key in VALUE_WORDS and value not in VALUE_WORDS[key]:
                problems.append(f'line {number}: {key} must be one of {", ".join(VALUE_WORDS[key])}, not {value!r}')
            elif key in COMMENTED_WORDS and not commented(value, COMMENTED_WORDS[key]):
                problems.append(f'line {number}: {key} must be one of {", ".join(COMMENTED_WORDS[key])}'
                                f' with an optional ", <comment>", not {value!r}')
            continue
        indent = len(line) - len(line.lstrip(' '))
        sub = re.fullmatch(r'\s+([a-z][a-z_]*):\s*(.*?)\s*', line)
        if current == 'checks' and sub:
            name = sub.group(1)
            if name not in BLOCKING_CHECKS:
                problems.append(f'line {number}: unknown check {name!r}')
            elif name in checks:
                problems.append(f'line {number}: check {name!r} given twice')
            elif not commented(sub.group(2), CHECK_WORDS):
                problems.append(f'line {number}: check {name!r} must be pass or fail, not {sub.group(2)!r}')
            else:
                checks[name] = sub.group(2)
            continue
        item = re.fullmatch(r'(\s*)- (.*?)\s*', line)
        if current in LIST_FIELDS and item and out.get(current) == '' and item.group(2).strip():
            text = item.group(2)
            if text != text.lstrip() or BULLET_START.match(text):
                problems.append(f'line {number}: a {current} item is "- " and its text, one space after the dash')
            elif text in lists[current]:
                problems.append(f'line {number}: {current} item given twice')
            elif item_indent is not None and len(item.group(1)) != item_indent:
                # A stray dash before a wrapped line would otherwise split one finding into two.
                problems.append(f'line {number}: {current} items must share one indent')
            lists[current].append(text.strip())
            item_indent = len(item.group(1))
            continue
        stripped = line.strip()
        continues = ((current in LIST_FIELDS and item_indent is not None and indent >= item_indent + 2)
                     or (current == 'reasons' and indent > 0))
        if continues and not stripped.startswith('- '):
            known_key = field_like.match(stripped)
            if known_key and known_key.group(1) in (known or ()) + BLOCKING_CHECKS:
                problems.append(f'line {number}: an indented {known_key.group(1)!r} line under {current} '
                                'reads as a field; write fields at column 0')
            if current == 'reasons':
                out['reasons'] += ' ' + stripped
            else:
                # A wrapped item continues the one before it.
                lists[current][-1] += ' ' + stripped
            continue
        problems.append(f'line {number}: not a field, check, list item or continuation'
                        + (f' (under {current})' if current else ''))
    for key in LIST_FIELDS:
        if out.get(key) == '' and not lists.get(key):
            problems.append(f'{key} has an empty value and no "  - <item>" lines; write none for no findings')
            lists.pop(key, None)
    for key in required:
        if key not in out:
            problems.append(f'states no {key}')
    if 'checks' in required and 'checks' in out:
        problems += [f'checks lacks {name} (each block gives checks {name}: pass or fail)'
                     for name in BLOCKING_CHECKS if name not in checks]
    out.update({f'_{k}': v for k, v in lists.items()})
    if checks:
        out['_checks'] = checks
    out['_problems'] = problems
    return out


def forbidden_characters(text):
    """Problems for characters a reader cannot see or that split lines unseen: control and format
    characters other than tab and CRLF line ends, line and paragraph separators, private-use and
    unassigned code points, and spaces other than U+0020 (a no-break space looks like a space but is
    not one to every pattern here)."""
    problems = []
    if '\r' in text.replace('\r\n', ''):
        problems.append('a carriage return outside a CRLF line end')
    seen = set()
    for ch in text:
        if ch in '\t\n\r' or ch in seen:
            continue
        category = unicodedata.category(ch)
        if category in ('Cc', 'Cf', 'Zl', 'Zp', 'Co', 'Cs', 'Cn') or (category == 'Zs' and ch != ' '):
            seen.add(ch)
            problems.append(f'character U+{ord(ch):04X} ({category})')
    return problems


def folded(text):
    """Compatibility-folded, case-folded text, to recognise a structural word written in another case
    or with a full-width look-alike."""
    return unicodedata.normalize('NFKC', text).casefold()


def review_blocks(text):
    """(title, header fields, [(heading words, block fields)]) of a review in reviewer.md format.

    Each block's fields carry `_heading` (the heading text after `## `) and `_verdict_line` (whether
    any line of the section, folded, starts with "verdict"). Document-level problems go to the
    header's `_problems`: text before the title, a second title, and unseen characters.
    """
    lines = text.splitlines()
    first = next((i for i, l in enumerate(lines) if TITLE.fullmatch(l)), None)
    title = None if first is None else lines[first].split()[2]
    document = []
    if first is not None and any(l.strip() for l in lines[:first]):
        document.append('text before the "# Review <task-id>" title')
    # The document starts at its title; anything before it is not part of the review.
    lines = lines[first + 1:] if first is not None else lines
    if any(re.match(r'\s*#\s*review\b', folded(l)) for l in lines):
        document.append('a second "# Review" title line')
    # On the raw text: splitlines would already have turned a lone CR or U+2028 into a line end.
    document += forbidden_characters(text)
    starts = [i for i, l in enumerate(lines) if l.startswith('## ')]
    header = fields(lines[:starts[0]] if starts else lines, known=HEADER_FIELDS)
    header['_problems'] = document + header['_problems']
    blocks = []
    for n, i in enumerate(starts):
        section = lines[i + 1:starts[n + 1] if n + 1 < len(starts) else len(lines)]
        body = fields(section, known=BLOCK_FIELDS, required=BLOCK_REQUIRED)
        body['_heading'] = lines[i][3:]
        body['_verdict_line'] = any(folded(l).strip().startswith('verdict') for l in section)
        blocks.append((lines[i][3:].split(), body))
    return title, header, blocks


def refuse_malformed(header, blocks, functions):
    """Refuse a review whose header or any function block breaks the format.

    A section is a function block if its heading's first word is an inventory build id in any case
    (or full-width form), or if any of its lines starts with "verdict". Its heading must then be
    exactly `<build id> 0x<lowercase hex RVA> <decimal size>` naming an inventory function with that
    size, and its body must parse without problems. Every block is checked, not only the accepted
    ones: a block the tool could not place might be a reject or escalate for a function it accepts.
    """
    refuse(not header['_problems'], 'review header breaks the reviewer.md format: ' + '; '.join(header['_problems']))
    sizes = {(fn['build_id'], fn['rva']): fn['size'] for fn in functions}
    builds = {folded(fn['build_id']) for fn in functions}
    for parts, body in blocks:
        heading = body['_heading']
        if not (parts and folded(parts[0]) in builds) and not body['_verdict_line']:
            continue  # commentary
        exact = re.fullmatch(r'(\S+) 0x([0-9a-f]+) ([0-9]+)', heading)
        key = exact and (exact.group(1), int(exact.group(2), 16))
        refuse(exact is not None and key in sizes and heading == f'{key[0]} 0x{key[1]:x} {sizes[key]}',
               f'review section "## {heading}" is a function block but its heading is not '
               '"<build id> 0x<lowercase hex RVA> <size>" for an inventory function and its size; '
               'commentary sections may not start a line with "verdict"')
        refuse(not body['_problems'], f'review block "## {heading}" breaks the reviewer.md format: '
               + '; '.join(body['_problems']))


def parse_review(text, build_id, rva, size):
    """Header fields and this function's block from a review in the reviewer.md output format.

    The block heading is exactly `## <build id> 0x<rva> <size>` (refuse_malformed has refused any
    other heading for a function block); the size must equal the inventory's, so a review of a
    differently sized range at the same address is not taken for this function.
    """
    title, header, all_blocks = review_blocks(text)
    blocks = [(parts[2:], body) for parts, body in all_blocks
              if len(parts) >= 2 and parts[0] == build_id and parts[1] == f'0x{rva:x}']
    refuse(len(blocks) == 1, f'review has {len(blocks)} blocks for {build_id} 0x{rva:x}; expected exactly 1')
    rest, block = blocks[0]
    refuse(len(rest) == 1 and rest[0] == str(size),
           f'review block for {build_id} 0x{rva:x} gives size {" ".join(rest) or "none"}, not the inventory size {size}')
    return title, header, block


def extract_review(text):
    """The review document from a transcript: from `# Review <id>` on, without an enclosing fence."""
    lines = text.splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if TITLE.fullmatch(l)), None)
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


def compiled_of(root, fn):
    record = _json_or_none(Path(root) / fn['report']) if isinstance(fn.get('report'), str) else None
    compiled = ((record or {}).get('source') or {}).get('compiled')
    return compiled if isinstance(compiled, str) else None


def resolve_selection(root, data, functions=None, units=None):
    """The inventory ids named by --functions (ids or 0x<rva>) and --units (compiled file or
    <area>/<Class>), or None when neither is given. Every name must select something."""
    if not functions and not units:
        return None
    picked = set()
    for name in functions or []:
        hits = [fn['id'] for fn in data['functions'] if name in (fn['id'], f'0x{fn["rva"]:x}')]
        refuse(len(hits) == 1, f'--functions {name}: {len(hits)} inventory entries; expected exactly 1')
        picked.update(hits)
    for name in units or []:
        path = name if name.startswith('reconstruction/') else f'reconstruction/{name.removesuffix(".cpp")}.cpp'
        hits = [fn['id'] for fn in data['functions'] if compiled_of(root, fn) == path]
        refuse(hits, f'--units {name}: no inventory entry names a match record compiled from {path}')
        picked.update(hits)
    return picked


def stale_ids(root, data):
    return {fn['id'] for fn in data['functions'] if fn['status'] == 'matched' and acceptance_staleness(fn, root)}


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


def label_findings(root, files):
    """tools/check_labels.py findings for the unit's files (a separate function so tests can stand in
    for the private community checkouts it reads)."""
    import check_labels
    return check_labels.check([Path(root) / name for name in files], root=Path(root))


def named_value(root, record, naming_findings):
    """Tier 2: no open naming finding, every unit file on `Labels: v2`, and no label-check finding.
    None (not assessed) when the approval recorded no naming findings at all (schema 1 or 2)."""
    if naming_findings is None:
        return None
    if naming_findings != []:
        return False
    unit = record['source']['translation_unit']
    for name in unit:
        if not LABELS_VERSION.search((Path(root) / name).read_text(encoding='utf-8')):
            return False
    try:
        return not label_findings(root, unit)
    except Exception:  # noqa: BLE001 - a label check that cannot run leaves the tier unset to false
        return False


def set_named(functions, index, value):
    """Set tier 2 on an entry, placed right after `status` so the two read together; None (not
    assessed) removes the field."""
    entry = {k: v for k, v in functions[index].items() if k != 'named'}
    out = {}
    for key, item in entry.items():
        out[key] = item
        if key == 'status' and value is not None:
            out['named'] = value
    functions[index] = out


def review_record(fn, record, header, title, blob, when, kind, naming, previous=None, old_section=None):
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
        'naming_findings': naming,
    }


def block_naming(block, where):
    """The approve block's naming findings, after the checks that make it a consistent approve."""
    refuse(block.get('report_binding', '').split(',')[0].strip() == 'agree',
           f'{where}: an approve needs report_binding: agree')
    checks = block.get('_checks') or {}
    for name in BLOCKING_CHECKS:
        refuse(checks.get(name, '').split(',')[0].strip() == 'pass',
               f'{where}: an approve needs checks {name}: pass (a blocking ground)')
    refuse('_blocking_findings' in block, f'{where}: review block states no blocking_findings (none for an approve)')
    refuse(block['_blocking_findings'] == [], f'{where}: an approve lists blocking findings; that is a reject')
    refuse('_naming_findings' in block, f'{where}: review block states no naming_findings (none, or a list)')
    naming = block['_naming_findings']
    refuse(len(naming) <= MAX_NAMING_FINDINGS, f'{where}: more than {MAX_NAMING_FINDINGS} naming findings')
    for item in naming:
        problem = naming_finding_problem(item)
        refuse(problem is None, f'{where}: {problem}; naming findings are published, rewrite it')
    return naming


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
    naming = block_naming(block, fn['id'])
    kind = block.get('review_kind') or 'full'
    refuse(kind in {'full', 'delta'}, f'review_kind {kind!r} is neither full nor delta')
    out = root / review_record_path(fn)
    previous = None
    if fn['status'] == 'matched':
        previous = _json_or_none(out)
        # Label-only and family records have no individual Reviewer pass on this digest; a full
        # review may replace them, which is how their naming findings get closed.
        relabelled = (previous is not None and previous.get('review_kind') in (LABEL_ONLY, 'family')
                      and previous.get('source_digest') == record['source']['digest'] and kind == 'full')
        refuse(previous is not None and (previous.get('source_digest') != record['source']['digest'] or relabelled),
               f'{fn["id"]} is already matched')
        # The superseded approval must be a real one for this function, or a delta would chain from nothing.
        refuse(previous.get('verdict') == 'approve' and previous.get('function_id') == fn['id'],
               f'{review_record_path(fn)} is not an approve for {fn["id"]}')
    else:
        refuse(not out.exists(), f'{review_record_path(fn)} already exists')
    if kind == 'full':
        # A full review stands on its own; it carries no link to the approval it replaces.
        return fn, record, review_record(fn, record, header, title, blob, when, 'full', naming)
    refuse(previous is None or previous.get('review_kind') != 'family', 'family approval needs a full individual review')
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
    return fn, record, review_record(fn, record, header, title, blob, when, 'delta', naming, previous, old)


def apply(root, data, new, target, prepared, tolerated, when):
    """Write the prepared review records and the new inventory, all or nothing; returns changed files.

    `prepared` is [(index, fn, record, review record or None)]. From the first write on, any failure,
    including an interrupt or a failed progress write, restores every file this touched.
    """
    new['updated_at'] = when.strftime('%Y-%m-%dT%H:%M:%SZ')
    unchanged_elsewhere(data, new, [i for i, *_ in prepared])
    written = [review_record_path(fn) for _, fn, _, review in prepared if review is not None]
    touched = [PROGRESS, INDEX] + written
    saved = {name: (root / name).read_bytes() if (root / name).is_file() else None for name in touched}
    try:
        for _, fn, _, review in prepared:
            if review is not None:
                (root / review_record_path(fn)).write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
        try:
            for index, _, record, _ in prepared:
                validate_review(new['functions'][index], record, root)
            validate(new, target, root, stale_ok=tolerated)
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
    changed = [PROGRESS] + written
    if saved[INDEX] != (root / INDEX).read_bytes():
        changed.append(INDEX)
    return changed


# Explicit model IDs and the Opus harness alias; unknown versions are not admitted.
OPUS_MODELS = frozenset(('opus', 'claude-opus-5-5'))
ADMITTING_PHRASES = {'gpt-6.1-terra': 'Terra class as the Reviewer'}
SOL_MODEL = 'gpt-6.1-sol'


def reviewer_admitted(root, model, profile):
    if model in OPUS_MODELS:
        return True
    if model == SOL_MODEL:
        return strong_reviewer_admitted(root, model, profile)
    phrase = ADMITTING_PHRASES.get(model)
    path = Path(root) / 'docs/verification.md'
    return bool(model == 'gpt-6.1-terra' and profile == 'claude-low' and phrase
                and path.is_file() and phrase in path.read_text())


def reviewer_matches(assigned, actual):
    return actual == assigned or (assigned in OPUS_MODELS and actual in OPUS_MODELS)


def strong_reviewer_admitted(root, model, profile):
    if model in OPUS_MODELS:
        return True
    path = Path(root) / 'docs/verification.md'
    return bool(model == SOL_MODEL and profile == 'claude-low' and path.is_file()
                and 'Sol class as the strong Reviewer' in path.read_text())


def active_flow_dir(root):
    import os
    import subprocess
    root = Path(root).resolve()
    result = subprocess.run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                            cwd=root, capture_output=True, text=True)
    shared = Path(result.stdout.strip()).parent if result.returncode == 0 else root
    expected = (shared / '.local/flow').resolve()
    override = os.environ.get('SKYRIM_FLOW_DIR')
    refuse(not override or Path(override).resolve() == expected,
           'SKYRIM_FLOW_DIR must resolve to the repository shared .local/flow')
    return expected


def active_profile(root, default=None):
    path = active_flow_dir(root) / 'events.jsonl'
    if path.is_file():
        for line in reversed(path.read_text().splitlines()):
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get('event') == 'session-start':
                import profiles
                return event.get('profile') or profiles.DEFAULT
    return default


def review_profile(root, task_id, requested):
    """A saved group's profile takes precedence over a later session; overrides must agree."""
    import profiles
    recorded = set()
    for path in (active_flow_dir(root) / 'groups').glob('*.json'):
        group = json.loads(path.read_text())
        if group.get('task_id') == task_id:
            recorded.add(group.get('profile') or profiles.DEFAULT)
    refuse(len(recorded) <= 1, 'review groups record conflicting profiles for this task')
    assigned = next(iter(recorded)) if recorded else active_profile(root, profiles.DEFAULT)
    refuse(not requested or not assigned or requested == assigned,
           '--profile does not match the recorded review group or active session profile')
    profile = assigned or requested or profiles.DEFAULT
    profiles.get(profile)
    return profile


def accept_many(root, review_source, targets=None, verdict='approve', when=None, select=None, profile=None):
    """Accept the approve blocks of one review: `targets` [(build id, rva)], or the approve blocks of
    the functions in `select` (inventory ids), or None for all of them.

    Returns (changed files, skipped block headings). All-or-nothing: every check runs before the
    first write, and any failure after it restores every file it touched.
    """
    root = Path(root)
    refuse(verdict == 'approve', f'verdict {verdict!r}: only approve is accepted; '
           'reject goes back to the Drafter or Engineer, escalate per docs/verification.md')
    data, target = load(root)
    # Stale acceptances are what a delta or re-review clears, so they may be present before; the
    # final validation below is strict except for entries outside this run that were stale already.
    validate(data, target, root, stale_ok=True)
    stale_before = stale_ids(root, data)
    review_file, blob = private_review(root, review_source)
    title, header, blocks = review_blocks(blob.decode('utf-8'))
    refuse(title is not None and TASK_ID.fullmatch(title),
           'review has no "# Review <task-id>" title with a lowercase task id')
    refuse_malformed(header, blocks, data['functions'])
    refuse(header.get('fresh_context') == 'yes', 'review does not state fresh_context: yes')
    refuse(header.get('drafted_or_triaged_any_reviewed_function') == 'no',
           'review does not state the Reviewer neither drafted nor triaged the function')
    model = header.get('reviewer_model')
    refuse(bool(model), 'review names no reviewer_model')
    profile = review_profile(root, title, profile)
    refuse(reviewer_admitted(root, model, profile),
           f'reviewer_model {model!r} is not admitted for this profile')
    skipped = []
    if targets is None:
        targets = []
        for parts, body in blocks:
            if body.get('verdict') != 'approve':
                skipped.append(f'{" ".join(parts)}: verdict {body.get("verdict")}')
                continue
            refuse(len(parts) >= 2 and re.fullmatch(r'0x[0-9a-fA-F]+', parts[1]),
                   f'review block heading "## {" ".join(parts)}" is not "<build id> 0x<rva> <size>"')
            if select is not None:
                hits = [fn for fn in data['functions'] if fn['build_id'] == parts[0] and fn['rva'] == int(parts[1], 16)]
                if not hits or hits[0]['id'] not in select:
                    skipped.append(f'{" ".join(parts)}: not selected')
                    continue
            targets.append((parts[0], int(parts[1], 16)))
        if select is not None:
            found = {data['functions'][entry_index(data, b, r)]['id'] for b, r in targets}
            missing = sorted(select - found)
            refuse(not missing, f'selected functions without an approve block in this review: {", ".join(missing)}')
        refuse(targets, 'review has no approve block')
    when = when or now_utc()
    prepared = []
    for build_id, rva in targets:
        index = entry_index(data, build_id, rva)
        refuse(index not in [i for i, *_ in prepared], f'{build_id} 0x{rva:x} is named twice')
        _, _, block = parse_review(blob.decode('utf-8'), build_id, rva, data['functions'][index]['size'])
        prepared.append((index, *prepare(root, data, target, index, title, header, block, blob, when)))
    new = copy.deepcopy(data)
    for index, _, record, review in prepared:
        new['functions'][index]['status'] = 'matched'
        set_named(new['functions'], index, named_value(root, record, review['naming_findings']))
    selected = {fn['id'] for _, fn, _, _ in prepared}
    return apply(root, data, new, target, prepared, stale_before - selected, when), skipped


def accept(root, build_id, rva, review_file, verdict, when=None, profile=None):
    """Accept one function from a review file; returns the changed files."""
    return accept_many(root, review_file, [(build_id, rva)], verdict, when, profile=profile)[0]


def accept_family_batch(root, batch_path, when=None, profile=None, fdir=None):
    """Accept unsampled members only after all required individual reviews and safeguards passed."""
    import flow
    root = Path(root)
    profile = profile or active_profile(root)
    data, target = load(root)
    validate(data, target, root, stale_ok=True)
    batch_path = fr.public_path(batch_path, f'reports/{target["build_id"]}/family-batches/')
    batch = fr.read(root, batch_path)
    family_path = fr.public_path(batch['family_path'], f'reports/{target["build_id"]}/families/')
    family = fr.read(root, family_path)
    fr.validate_family(family)
    fr.require(not family['paused'], 'family is paused: ' + family['pause_reason'])
    fr.private_approval(root, family, profile)
    fr.validate_batch(batch, family)
    fr.ordering(root, batch_path, batch)
    flow.family_group_hold(root, fdir or flow.flow_dir(root), batch['population'])
    by_id = {fn['id']: fn for fn in data['functions']}
    # Enrollment already checked the first 20 and their safeguards; their frozen row digests
    # are bound by the saved family review. Later batches review only their own required members.
    required = set(batch['sample'])
    for fid in batch['population']:
        fn = by_id[fid]
        rec = validate_match(fn, target, root)
        fr.check_member(family, fn, rec, ranges=False)
        fr.require(batch['members'][fid] == fr.member_digest(fn, rec), 'member differs from committed population')
        if fn['status'] == 'matched' or not fr.in_ranges(rec.get('family_parameters'), family['parameter_ranges']):
            required.add(fid)
    flow.family_reviewed_gate(root, fdir or flow.flow_dir(root), required, data, target)
    when = when or now_utc()
    prepared, new = [], copy.deepcopy(data)
    for fid in batch['population']:
        index = next(i for i, fn in enumerate(data['functions']) if fn['id'] == fid)
        fn = data['functions'][index]
        if fid in required:
            continue
        fr.require(fn['status'] != 'matched', 'unsampled member already accepted; use a new batch')
        rec = validate_match(fn, target, root)
        fr.check_member(family, fn, rec)
        fr.require(not (root / review_record_path(fn)).exists(), 'member already has an approval')
        rv = review_record(fn, rec, family['review'], family['review']['review_task_id'], b'', when,
                           'family', ['Family approval does not assess individual names.'])
        rv.update(review_record_schema=4, review_sha256=family['review']['review_sha256'],
                  family_evidence={'family_path': family_path, 'batch_path': batch_path,
                                   'batch_sha256': fr.digest(batch), 'member_sha256': fr.member_digest(fn, rec)})
        prepared.append((index, fn, rec, rv))
        new['functions'][index]['status'] = 'matched'
        set_named(new['functions'], index, False)
    if not prepared:
        return []
    selected = {fn['id'] for _, fn, _, _ in prepared}
    return apply(root, data, new, target, prepared, stale_ids(root, data) - selected, when)


def superseded_approval(fn, record, previous):
    """Refuse unless `previous` is a well-formed approve of this function for another digest."""
    where = review_record_path(fn)
    refuse(previous is not None, f'{where} is missing or not JSON')
    schema = previous.get('review_record_schema')
    refuse(schema in REVIEW_SCHEMA_FIELDS and set(previous) == REVIEW_SCHEMA_FIELDS[schema],
           f'{where} is not a Reviewer record of a known schema')
    refuse(previous['verdict'] == 'approve' and previous['escalation_category'] == 'none',
           f'{where} is not an approve without escalation')
    refuse((previous['function_id'], previous['build_id'], previous['rva'], previous['size'])
           == (fn['id'], fn['build_id'], fn['rva'], fn['size']), f'{where} approved another function')
    refuse(is_hash(previous['source_digest']) and previous['source_digest'] != record['source']['digest'],
           f'{where} does not bind an earlier digest')
    refuse(is_hash(previous['review_sha256']), f'{where} names no review hash')


def label_only(root, select=None, when=None):
    """Re-accept `review behind` entries whose compared code section is unchanged, without a
    Reviewer pass (docs/verification.md, "Label-only re-acceptance"). All selected entries, or all
    `review behind` entries when nothing is selected; any ineligible one refuses the whole run."""
    root = Path(root)
    data, target = load(root)
    validate(data, target, root, stale_ok=True)
    stale_before = stale_ids(root, data)
    candidates = [i for i, fn in enumerate(data['functions'])
                  if (select is None or fn['id'] in select)
                  and (select is not None or acceptance_staleness(fn, root) == STALE_REVIEW)]
    refuse(candidates, 'no matched entry has a re-confirmed record with its review behind' if select is None
           else 'nothing selected')
    when = when or now_utc()
    prepared = []
    new = copy.deepcopy(data)
    for index in candidates:
        fn = data['functions'][index]
        refuse(fn['status'] == 'matched', f'{fn["id"]} is {fn["status"]}; label-only re-acceptance is for matched entries')
        state = acceptance_staleness(fn, root)
        refuse(state != STALE_UNIT, f'{fn["id"]}: unit changed since its match record; re-confirm first')
        refuse(state == STALE_REVIEW, f'{fn["id"]}: its Reviewer record already binds the current record')
        record = validate_match(fn, target, root)
        current = record_code_section(record)
        refuse(current is not None, f'{fn["id"]}: the match record carries no code-section hash; a review is needed')
        previous = _json_or_none(root / review_record_path(fn))
        refuse(previous is None or previous.get('review_kind') != 'family',
               'family approval cannot be carried by label-only; use full review or a new family batch')
        superseded_approval(fn, record, previous)
        old, where = review_packet.previous_code_section(root, fn, previous['source_digest'])
        refuse(old is not None, f'{fn["id"]}: no code-section hash for the approved digest ({where}); a review is needed')
        refuse(old == current, f'{fn["id"]}: the compared code section changed since the approved digest; '
               'a full review is needed')
        problems = lint_tree(root, record['source']['translation_unit'])
        refuse(not problems, f'{fn["id"]}: reconstruction lint: {"; ".join(problems[:3])}')
        naming = previous.get('naming_findings') if previous['review_record_schema'] >= 3 else None
        review = {
            'review_record_schema': REVIEW_RECORD_SCHEMA,
            'function_id': fn['id'], 'build_id': fn['build_id'], 'rva': fn['rva'], 'size': fn['size'],
            'source_digest_method': DIGEST_METHOD, 'source_digest': record['source']['digest'],
            'reviewer_model': previous['reviewer_model'], 'review_task_id': previous['review_task_id'],
            'verdict': 'approve', 'escalation_category': 'none',
            'review_sha256': previous['review_sha256'], 'review_date': previous['review_date'],
            'review_kind': LABEL_ONLY,
            'previous_source_digest': previous['source_digest'],
            'previous_review_sha256': previous['review_sha256'],
            'previous_code_section_sha256': old, 'code_section_sha256': current,
            'naming_findings': naming,
        }
        set_named(new['functions'], index, named_value(root, record, naming))
        prepared.append((index, fn, record, review))
    selected = {fn['id'] for _, fn, _, _ in prepared}
    return apply(root, data, new, target, prepared, stale_before - selected, when)


def refresh_named(root, select=None, when=None):
    """Recompute tier 2 for current `matched` entries (all, or the selected ones)."""
    root = Path(root)
    data, target = load(root)
    validate(data, target, root, stale_ok=True)
    stale_before = stale_ids(root, data)
    new = copy.deepcopy(data)
    prepared = []
    for index, fn in enumerate(data['functions']):
        if select is not None and fn['id'] not in select:
            continue
        if select is not None:
            refuse(fn['status'] == 'matched' and fn['id'] not in stale_before,
                   f'{fn["id"]} is not a current matched entry')
        elif fn['status'] != 'matched' or fn['id'] in stale_before:
            continue
        record = validate_match(fn, target, root)
        review = validate_review(fn, record, root)
        naming = review.get('naming_findings') if review['review_record_schema'] >= 3 else None
        set_named(new['functions'], index, named_value(root, record, naming))
        if new['functions'][index] != fn:
            prepared.append((index, fn, record, None))
    if not prepared:
        return []
    return apply(root, data, new, target, prepared, stale_before, when or now_utc())


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
    entry.pop('named', None)
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
    p.add_argument('--family-flow-dir', type=Path, help=argparse.SUPPRESS)
    p.add_argument('--family-batch', help='Accept unsampled members of a precommitted family batch')
    p.add_argument('--all-approved', action='store_true', help='Accept every approve block of the review')
    p.add_argument('--label-only', action='store_true',
                   help='Re-accept review-behind entries whose compared code section is unchanged, without a review')
    p.add_argument('--refresh-named', action='store_true', help='Recompute tier 2 (named) for current matched entries')
    p.add_argument('--functions', nargs='+', metavar='ID_OR_RVA', help='Restrict to these inventory ids or 0x<rva>')
    p.add_argument('--units', nargs='+', metavar='UNIT', help='Restrict to functions compiled from these units')
    p.add_argument('--revoke', action='store_true', help='Revoke an accepted function')
    p.add_argument('--reason', help='Why the acceptance is revoked (with --revoke)')
    p.add_argument('--profile', choices=['cheap', 'full', 'claude-low'], help='Profile in use (defaults to active session)')
    p.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = p.parse_args(argv)
    skipped = []
    try:
        modes = sum(map(bool, (args.revoke, args.all_approved, args.label_only, args.refresh_named, args.family_batch)))
        refuse(modes <= 1, 'choose one of --revoke, --all-approved, --label-only, --refresh-named, --family-batch')
        selecting = bool(args.functions or args.units)
        refuse(not selecting or args.all_approved or args.label_only or args.refresh_named,
               '--functions and --units go with --all-approved, --label-only or --refresh-named')
        refuse(args.family_flow_dir is None or args.family_batch, '--family-flow-dir requires --family-batch')
        select = resolve_selection(args.root, load(args.root)[0], args.functions, args.units) if selecting else None
        if args.family_batch:
            refuse(not selecting and args.review is None and args.verdict is None
                   and args.build_id is None and args.rva is None, '--family-batch takes no function or review selection')
            changed = accept_family_batch(args.root, args.family_batch, profile=args.profile, fdir=args.family_flow_dir)
            print('accepted unsampled family members: status matched, family review recorded')
        elif args.revoke:
            refuse(args.review is None and args.verdict is None, '--revoke takes no --review or --verdict')
            refuse(args.build_id is not None and args.rva is not None, '--revoke needs --build-id and --rva')
            changed, finding, note = revoke(args.root, args.build_id, args.rva, args.reason)
            print(f'revoked {args.build_id} 0x{args.rva:x}: status mapped')
            print(f'add this dated note to {finding} by hand:\n{note}')
        elif args.all_approved:
            refuse(args.review is not None, '--all-approved needs --review')
            refuse(args.build_id is None and args.rva is None, '--all-approved takes no --build-id or --rva')
            refuse(args.verdict in (None, 'approve'), '--all-approved accepts approve blocks only')
            changed, skipped = accept_many(args.root, args.review, select=select, profile=args.profile)
            print(f'accepted {sum(n.endswith(".review.json") for n in changed)} function(s): status matched, Reviewer records written')
        elif args.label_only or args.refresh_named:
            refuse(args.review is None and args.verdict is None and args.build_id is None and args.rva is None,
                   '--label-only and --refresh-named take no --review, --verdict, --build-id or --rva')
            if args.label_only:
                changed = label_only(args.root, select)
                print(f're-accepted {sum(n.endswith(".review.json") for n in changed)} function(s) label-only: '
                      'code section unchanged, approval carried forward')
            else:
                changed = refresh_named(args.root, select)
                print(f'named recomputed; {"no change" if not changed else "inventory updated"}')
                if not changed:
                    return 0
        else:
            refuse(args.review is not None and args.verdict is not None, 'accepting needs --review and --verdict')
            refuse(args.build_id is not None and args.rva is not None, 'accepting one function needs --build-id and --rva')
            changed = accept(args.root, args.build_id, args.rva, args.review, args.verdict, profile=args.profile)
            print(f'accepted {args.build_id} 0x{args.rva:x}: status matched, Reviewer record written')
    except Refused as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'REFUSED: inconsistent inputs: {exc}', file=sys.stderr)
        return 1
    for line in skipped:
        print(f'not accepted: {line}')
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
