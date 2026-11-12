"""The review grammar tools/accept_function.py accepts, and a mutation test that holds it to it.

Grammar (a saved review, after extract_review has cut a transcript at the title)
------------------------------------------------------------------------------
Characters: no control or format characters other than tab and CRLF/LF line ends, no line or
paragraph separators, no private-use or unassigned code points, and no space other than U+0020.
A carriage return is allowed only as part of CRLF.

    review      = title header section*
    title       = "# Review " task-id EOL            ; first non-blank line; task-id [a-z0-9][a-z0-9-]*
    header      = { blank | field }                  ; keys from HEADER_FIELDS, each at most once
    section     = "## " heading-text EOL body        ; a line starting "## " (exactly) starts a section
    body        = { blank | field | check | item | continuation }

No line after the title may read, case-folded and NFKC-folded, as "#" + optional spaces + "review"
(a second title). A section is a *function block* if the first word of its heading, folded, is an
inventory build id, or if any of its lines, folded and stripped, starts with "verdict". Every other
section is commentary and is not parsed.

    function-heading = build-id " 0x" hex " " size   ; exactly: build id as in the inventory, hex
                                                     ; lower case without leading zeros, size decimal
                                                     ; and equal to the inventory size of that RVA;
                                                     ; single spaces, nothing else on the line
    field       = key ":" [ spaces value ] EOL       ; key [a-z][a-z_]* at column 0; known key; once
    value       = text without leading/trailing space
    check       = indent check-name ":" spaces word [ "," comment ] EOL   ; only under "checks:"
    item        = indent "- " text EOL               ; only under a list field with an empty value
    continuation = indent text EOL                   ; under "reasons" (any indent > 0), or under a
                                                     ; list item, indented to at least its text
                                                     ; column (dash indent + 2)

Field rules for a function block (BLOCK_FIELDS, BLOCK_REQUIRED) and the header (HEADER_FIELDS):
- `checks` takes no value; its sub-lines are the four BLOCKING_CHECKS, each at most once, valued
  `pass` or `fail`, optionally followed by `, <comment>`.
- `blocking_findings` and `naming_findings` are the literal `none`, or empty with one or more items.
  Item text is stripped, may not start with another bullet, and may not repeat an earlier item.
- Words: verdict approve|reject|escalate; escalation_category provenance|legal|systemic|other|none;
  review_kind full|delta; code_section_unchanged, fresh_context,
  drafted_or_triaged_any_reviewed_function, sampling_second_pass, decompiler_output_read yes|no;
  report_binding agree|disagree|missing, optionally followed by `, <comment>`.
- Any other field value must be non-empty.
- A continuation whose text starts with a known key or check name and a colon is refused (an
  indented field would otherwise be swallowed).
- Required in every function block: verdict, escalation_category, source_paths, source_digest,
  report_path, report_binding, checks, blocking_findings, naming_findings, reasons.
Anything else in the header or a function block (prose, sub-headings, a stray line) refuses the
whole review, as does a malformed function heading, so a block the tool cannot place can never hide
a reject.

Mutation test
-------------
`MutationTests` builds a valid review: header, an approve block for the fixture function with two
naming findings (one wrapped) and a wrapped `reasons`, a reject block for the second inventory
function with one blocking finding, and a commentary section. It is accepted. Each mutant changes one
structural token of it: title, heading and commentary heading words, `#`/`##`, `0x`, the RVA and
size, keys, check names, `:`, verdict/category/binding/check words, `none`, `-` bullets,
indentation, separating spaces and blank lines. Operators per token: delete, duplicate, upper/lower/
title/swap case, look-alike replacement (full-width forms, Cyrillic letters, Unicode dashes and
colons, no-break, em and ideographic spaces, zero-width space, tab, newline), punctuation inserted
before or after (`: , . ; h - # 0`), whitespace inserted before or after, a key replaced by every
other key of its kind; per line: duplicate, insert a blank line before. Deleting a whole item or
continuation line, or editing the text of a finding, is a different review, not a malformed one, and
is not generated. Every mutant runs through `accept_many` in --all-approved mode and through the
single-function `accept`; it must be refused, or accepted with exactly the original verdicts,
categories, check words, binding word and findings for both functions and an identical published
record.
"""
import difflib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import accept_function as af  # noqa: E402
import build_index  # noqa: E402
from test_acceptance_flow import WHEN  # noqa: E402
from test_match_gate import CPP, HDR, RECORD, REVIEW  # noqa: E402
from test_two_tier import TwoTierFixture  # noqa: E402

FINDING_A = 'unk020 is an NG name without a label line'
FINDING_B = 'the pointer name is a guess'
TASK = 'r-mut'

CYRILLIC = {'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р', 'c': 'с', 'x': 'х', 'i': 'і', 'y': 'у', 's': 'ѕ',
            'R': 'Р', 'E': 'Е', 'N': 'Ν'}
LOOKALIKES = {
    '#': ['＃', '♯', '﹟'], '##': ['＃＃', '#＃', '♯♯', '# #', '###', '#'],
    '-': ['‐', '‑', '–', '—', '−', '*', '•', '+', '－'],
    ':': ['：', '꞉', '∶', ';', '=', ' :'],
    '0x': ['0X', '0х', 'Ox', '0×', 'x', '0'],
}
SPACES = ['', '  ', '\t', '\xa0', ' ', '　', '​', '\n']
PUNCT = [':', ',', '.', ';', 'h', '-', '#', '0']
INSERT_SPACES = [' ', '\t', '\xa0', '​', '\n']


def review(fn, digest):
    return f'''# Review {TASK}

reviewer_model: claude-opus-5-5
fresh_context: yes
drafted_or_triaged_any_reviewed_function: no
gates_in_force: G2
source_revision: 0000000
sampling_second_pass: no
decompiler_output_read: no

## synthetic-fixture 0x{fn['rva']:x} {fn['size']}

verdict: approve
escalation_category: none
source_paths: {CPP} {HDR}
source_digest: {digest}
report_path: {RECORD}
report_binding: agree, synthetic
checks:
  plausible_source: pass, synthetic
  provenance: pass, synthetic
  claim_scope: pass, synthetic
  publication_hygiene: pass, synthetic
blocking_findings: none
naming_findings:
  - {FINDING_A}
    wrapped here
  - {FINDING_B}
reasons: synthetic
  and wrapped

## synthetic-fixture 0x3000 8

verdict: reject
escalation_category: none
source_paths: {CPP}
source_digest: {'e' * 64}
report_path: reports/synthetic-fixture/0x3000.json
report_binding: missing, no record
checks:
  plausible_source: pass, synthetic
  provenance: fail, synthetic
  claim_scope: pass, synthetic
  publication_hygiene: pass, synthetic
blocking_findings:
  - B1 the second function reuses an undeclared body
naming_findings: none
reasons: synthetic

## Notes

Free commentary the tool does not parse.
'''


def tokens(line):
    """(start, end, kind) spans of the structural tokens of one review line."""
    import re
    out = []
    if line.startswith('# Review '):
        # The task id is an identifier the Reviewer chooses, not a structural token.
        return [(0, 1, '#'), (1, 2, ' '), (2, 8, 'word'), (8, 9, ' ')]
    if line.startswith('## '):
        out = [(0, 2, '##'), (2, 3, ' ')]
        for m in re.finditer(r'\S+|\s+', line[3:]):
            s, e = m.start() + 3, m.end() + 3
            text = m.group()
            if text.isspace():
                out.append((s, e, ' '))
            elif text.startswith('0x'):
                out += [(s, s + 2, '0x'), (s + 2, e, 'word')]
            else:
                out.append((s, e, 'word'))
        return out
    m = re.fullmatch(r'( *)- (.*)', line)
    if m:
        d = len(m.group(1))
        return ([(0, d, 'indent')] if d else []) + [(d, d + 1, '-'), (d + 1, d + 2, ' ')]
    m = re.fullmatch(r'( *)([a-z_]+):( ?)(.*)', line)
    if m:
        ind, key, sp, value = m.groups()
        k0 = len(ind)
        out = ([(0, k0, 'indent')] if ind else []) + [(k0, k0 + len(key), 'key:' + ('check' if ind else key)),
                                                      (k0 + len(key), k0 + len(key) + 1, ':')]
        v0 = k0 + len(key) + 1
        if sp:
            out.append((v0, v0 + 1, ' '))
            v0 += 1
        word = re.match(r'[a-z]+', value)
        structural = key in af.VALUE_WORDS or key in af.COMMENTED_WORDS or ind or value == 'none'
        if word and structural:
            out.append((v0, v0 + word.end(), 'word'))
            if value[word.end():word.end() + 1] == ',':
                out.append((v0 + word.end(), v0 + word.end() + 1, ','))
        return out
    m = re.fullmatch(r'( +)\S.*', line)
    if m:
        return [(0, len(m.group(1)), 'indent')]
    return []


def replacements(text, kind):
    out = {''}                                      # delete
    out.add(text + text)                            # duplicate
    if kind in ('#', '##', '-', ':', '0x'):
        out.update(LOOKALIKES[kind])
    if kind in (' ', 'indent'):
        out.update(SPACES)
        out.update(text + s for s in (' ', '\t'))
        if kind == 'indent':
            out.update(' ' * n for n in range(0, 7))
    if any(c.isalpha() for c in text):
        out.update({text.upper(), text.lower(), text.title(), text.swapcase(), text.capitalize()})
        for i, c in enumerate(text):
            if c in CYRILLIC:
                out.add(text[:i] + CYRILLIC[c] + text[i + 1:])
        out.add(''.join(chr(ord(c) + 0xFEE0) if '!' <= c <= '~' else c for c in text))   # full-width
    if kind.startswith('key:'):
        key = kind[4:]
        pool = af.BLOCKING_CHECKS if key == 'check' else af.BLOCK_FIELDS + af.HEADER_FIELDS
        out.update(k for k in pool if k != text)
    if text == 'none':
        out.update({'n/a', 'nothing', 'no', '-', 'None.', 'none,'})
    # Punctuation next to a separating space would land in the text that follows it (a finding, a
    # value), which is an edit of content, not of structure; spaces get space operations only.
    for p in (INSERT_SPACES if kind in (' ', 'indent') else PUNCT + INSERT_SPACES):
        out.add(text + p)
        out.add(p + text)
    out.discard(text)
    return out


def mutants(original):
    lines = original.split('\n')
    seen = set()
    for n, line in enumerate(lines):
        variants = set()
        for start, end, kind in tokens(line):
            for new in replacements(line[start:end], kind):
                variants.add(line[:start] + new + line[end:])
        for v in variants:
            seen.add('\n'.join(lines[:n] + [v] + lines[n + 1:]))
        if line.strip():
            continuation = line.startswith(' ') and not line.lstrip().startswith('- ') and ':' not in line
            if not continuation:
                seen.add('\n'.join(lines[:n + 1] + [line] + lines[n + 1:]))  # duplicate the line
            if not continuation and not line.lstrip().startswith('- '):
                seen.add('\n'.join(lines[:n] + lines[n + 1:]))             # delete a structural line
        seen.add('\n'.join(lines[:n] + [''] + lines[n:]))                    # blank line before
    seen.discard(original)
    return sorted(seen)


def summary(text, functions):
    """What the review says about each inventory function, from the parser."""
    _, header, blocks = af.review_blocks(text)
    sizes = {(fn['build_id'], fn['rva']): fn['size'] for fn in functions}
    out = {'header': (header.get('fresh_context'), header.get('drafted_or_triaged_any_reviewed_function'),
                      header.get('reviewer_model'))}
    for parts, body in blocks:
        if len(parts) == 3 and parts[1].startswith('0x'):
            try:
                key = (parts[0], int(parts[1], 16))
            except ValueError:
                continue
            if key in sizes:
                out.setdefault(body['_heading'], []).append((
                    body.get('verdict'), body.get('escalation_category'),
                    body.get('report_binding', '').split(',')[0].strip(),
                    tuple(sorted((k, v.split(',')[0].strip()) for k, v in (body.get('_checks') or {}).items())),
                    tuple(body.get('_blocking_findings', ('<missing>',))),
                    tuple(body.get('_naming_findings', ('<missing>',)))))
    return out


class ReviewFixture(TwoTierFixture):
    def setUp(self):
        super().setUp()
        (self.root / '.local/reviews').mkdir(parents=True, exist_ok=True)


class MutationTests(ReviewFixture, unittest.TestCase):
    def snapshot(self):
        names = ('data/progress.json', REVIEW, build_index.INDEX)
        return {p: (self.root / p).read_bytes() if (self.root / p).exists() else None for p in names}

    def restore(self, state):
        for name, blob in state.items():
            if blob is None:
                (self.root / name).unlink(missing_ok=True)
            else:
                (self.root / name).write_bytes(blob)

    def run_mode(self, path, mode):
        if mode == 'all':
            af.accept_many(self.root, str(path), when=WHEN)
        else:
            af.accept(self.root, 'synthetic-fixture', self.fn['rva'], str(path), 'approve', when=WHEN)
        return json.loads((self.root / REVIEW).read_text())

    def published(self, record):
        return {k: v for k, v in record.items() if k != 'review_sha256'}

    def test_every_single_token_mutant_is_refused_or_identical(self):
        original = review(self.fn, self.record['source']['digest'])
        functions = self.progress()['functions']
        path = self.root / f'.local/reviews/{TASK}.md'
        clean = self.snapshot()
        path.write_text(original)
        expected = {}
        for mode in ('all', 'one'):
            self.restore(clean)
            expected[mode] = self.published(self.run_mode(path, mode))
        self.restore(clean)
        self.assertEqual(expected['all']['naming_findings'], [FINDING_A + ' wrapped here', FINDING_B])
        want = summary(original, functions)
        self.assertEqual(len(want), 3)   # header and both function blocks
        counts = {'mutants': 0, 'refused': 0, 'accepted_identical': 0, 'accepted_different': 0}
        different = []
        for text in mutants(original):
            counts['mutants'] += 1
            path.write_text(text)
            outcomes = []
            for mode in ('all', 'one'):
                try:
                    record = self.run_mode(path, mode)
                except (af.Refused, ValueError):
                    outcomes.append(None)
                    self.assertEqual(self.snapshot(), clean)
                    continue
                self.restore(clean)
                outcomes.append(self.published(record) == expected[mode] and summary(text, functions) == want)
            if all(o is None for o in outcomes):
                counts['refused'] += 1
            elif all(o is True for o in outcomes):
                counts['accepted_identical'] += 1
            else:
                counts['accepted_different'] += 1
                different.append(text)
        if os.environ.get('REVIEW_MUTANTS_REPORT'):
            print(f'\nreview mutants: {counts}', file=sys.stderr)
        changed = ['\n'.join(line for line in difflib.unified_diff(original.split('\n'), text.split('\n'),
                                                                    lineterm='', n=0) if line[:1] in '+-')
                   for text in different]
        self.assertEqual(changed, [], 'accepted mutants that change a verdict, check, binding or finding')
        self.assertGreater(counts['mutants'], 1000)
        self.assertGreater(counts['refused'], counts['mutants'] // 2)


class HeadingTests(ReviewFixture, unittest.TestCase):
    """B2: a reject block the tool cannot place must refuse the review, not be dropped."""

    def reject_after_approve(self, heading):
        text = review(self.fn, self.record['source']['digest'])
        approve = text.index('## synthetic-fixture 0x1010')
        reject_start = text.index('## synthetic-fixture 0x3000 8')
        block = text[approve:reject_start].replace('verdict: approve', 'verdict: reject').replace(
            'blocking_findings: none', 'blocking_findings:\n  - B1 conflicting').replace(
            f'## synthetic-fixture 0x{self.fn["rva"]:x} {self.fn["size"]}', '## ' + heading)
        path = self.root / '.local/reviews/r-head.md'
        path.write_text(text[:reject_start] + block + text[reject_start:])
        return str(path)

    def test_malformed_heading_of_a_conflicting_reject_refuses(self):
        rva, size = f'0x{self.fn["rva"]:x}', self.fn['size']
        for heading in (f'synthetic-fixture {rva}: {size}', f'synthetic-fixture {rva}, {size}',
                        f'synthetic-fixture {rva}h {size}', f'SYNTHETIC-FIXTURE {rva} {size}',
                        f'Synthetic-Fixture {rva} {size}', f'synthetic-fixture {rva.upper()} {size}',
                        f'synthetic-fixture 0x0{rva[2:]} {size}', f'synthetic-fixture {rva} 0{size}',
                        f'synthetic-fixture {rva} {size} ', f'synthetic-fixture  {rva} {size}',
                        f'synthetic-fixture {rva} {size + 1}', f'synthetic-fixture {rva}',
                        f'ｓynthetic-fixture {rva} {size}', f'synthetic‐fixture {rva} {size}',
                        f'notes on {rva}', 'Notes'):
            with self.subTest(heading=heading):
                self.assertRefused('function block but its heading|breaks', lambda: af.accept_many(
                    self.root, self.reject_after_approve(heading), when=WHEN))
                self.assertRefused('function block but its heading|breaks', lambda: af.accept(
                    self.root, 'synthetic-fixture', self.fn['rva'], self.reject_after_approve(heading),
                    'approve', when=WHEN))

    def test_well_formed_conflicting_reject_refuses(self):
        rva = f'0x{self.fn["rva"]:x}'
        self.assertRefused('2 blocks', lambda: af.accept_many(
            self.root, self.reject_after_approve(f'synthetic-fixture {rva} {self.fn["size"]}'), when=WHEN))

    def test_unknown_function_heading_refuses(self):
        text = review(self.fn, self.record['source']['digest']).replace('0x3000 8', '0x3001 8')
        path = self.root / '.local/reviews/r-unknown.md'
        path.write_text(text)
        self.assertRefused('function block but its heading', lambda: af.accept_many(self.root, str(path), when=WHEN))

    def test_valid_review_is_accepted(self):
        path = self.root / '.local/reviews/r-valid.md'
        path.write_text(review(self.fn, self.record['source']['digest']))
        changed, skipped = af.accept_many(self.root, str(path), when=WHEN)
        self.assertEqual(skipped, ['synthetic-fixture 0x3000 8: verdict reject', 'Notes: verdict None'])
        self.assertEqual(self.entry()['status'], 'matched')


class TitleTests(ReviewFixture, unittest.TestCase):
    """N8: a second title, in any section and any case, refuses the review."""

    def test_second_title_refuses(self):
        text = review(self.fn, self.record['source']['digest'])
        for second in ('# Review r-other', '# review r-other', '#  Review r-other', '＃ Review r-other',
                       '  # Review r-other'):
            with self.subTest(second=second):
                path = self.root / '.local/reviews/r-twice.md'
                path.write_text(text + f'\n{second}\n\nfresh_context: no\n')
                self.assertRefused('second "# Review" title', lambda: af.accept_many(self.root, str(path), when=WHEN))


if __name__ == '__main__':
    unittest.main()
