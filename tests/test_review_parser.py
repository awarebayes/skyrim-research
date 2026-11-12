"""The review-block parser in tools/accept_function.py fails closed.

A finding written without its dash, a second `checks:` section, an unknown key, prose after the last
field or a block cut short must refuse the acceptance, not be read as an empty or first-wins value.
The end-to-end cases reuse the synthetic two-tier repository; nothing is game-derived.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import accept_function as af  # noqa: E402
import check  # noqa: E402
from check import naming_finding_problem, validate  # noqa: E402
from test_match_gate import REVIEW, GateFixture  # noqa: E402

REAL_LEGACY_ALLOWED = check.legacy_review_allowed
from test_two_tier import TwoTierFixture  # noqa: E402
from test_acceptance_flow import WHEN  # noqa: E402

GOOD = '''verdict: approve
escalation_category: none
source_paths: a.cpp a.h
source_digest: d
report_path: r.json
report_binding: agree, synthetic
checks:
  plausible_source: pass, synthetic
  provenance: pass, synthetic
  claim_scope: pass, synthetic
  publication_hygiene: pass, synthetic
blocking_findings: none
naming_findings: none
reasons: synthetic
'''


def parse(text):
    return af.fields(text.splitlines(), known=af.BLOCK_FIELDS, required=af.BLOCK_REQUIRED)


class FieldsUnitTests(unittest.TestCase):
    def assertProblem(self, text, pattern):
        block = parse(text)
        self.assertTrue(block['_problems'], text)
        self.assertRegex('; '.join(block['_problems']), pattern)
        return block

    def test_good_block_has_no_problems(self):
        block = parse(GOOD)
        self.assertEqual(block['_problems'], [])
        self.assertEqual((block['_blocking_findings'], block['_naming_findings']), ([], []))

    def test_empty_list_value_with_undashed_line_is_refused(self):
        # The fail-open shape: the indented prose line used to be dropped and the list read as empty.
        for key in ('blocking_findings', 'naming_findings'):
            with self.subTest(key=key):
                text = GOOD.replace(f'{key}: none\n', f'{key}:\n  the loop body is pasted decompiler output\n')
                block = self.assertProblem(text, f'not a field.*under {key}|{key} has an empty value')
                self.assertNotIn(f'_{key}', block)

    def test_empty_list_value_with_unindented_line_is_refused(self):
        text = GOOD.replace('naming_findings: none\n', 'naming_findings:\nunk020 is an NG name\n')
        block = self.assertProblem(text, 'naming_findings has an empty value')
        self.assertNotIn('_naming_findings', block)

    def test_empty_list_value_alone_is_refused(self):
        text = GOOD.replace('blocking_findings: none\n', 'blocking_findings:\n')
        self.assertNotIn('_blocking_findings', self.assertProblem(text, 'blocking_findings has an empty value'))

    def test_only_literal_none_is_empty(self):
        for value in ('None', 'NONE', 'n/a', '-', 'nothing', 'B1 a finding inline'):
            with self.subTest(value=value):
                self.assertProblem(GOOD.replace('blocking_findings: none', f'blocking_findings: {value}'),
                                   'is "none" or a list')

    def test_items_after_none_are_refused(self):
        self.assertProblem(GOOD.replace('blocking_findings: none\n', 'blocking_findings: none\n  - B1 real\n'),
                           'under blocking_findings')

    def test_items_and_continuations_parse(self):
        block = parse(GOOD.replace('naming_findings: none\n',
                                   'naming_findings:\n  - first part\n    continued\n  - second\n'))
        self.assertEqual(block['_problems'], [])
        self.assertEqual(block['_naming_findings'], ['first part continued', 'second'])

    def test_continuation_at_item_indent_is_refused(self):
        self.assertProblem(GOOD.replace('naming_findings: none\n', 'naming_findings:\n  - first\n  stray\n'),
                           'under naming_findings')

    def test_duplicate_keys_are_refused(self):
        self.assertProblem(GOOD + 'verdict: reject\n', "'verdict' given twice")
        self.assertProblem(GOOD.replace('blocking_findings: none\n', 'blocking_findings: none\nblocking_findings:\n  - B1\n'),
                           "'blocking_findings' given twice")

    def test_second_checks_section_is_refused(self):
        block = self.assertProblem(GOOD + 'checks:\n  provenance: fail, pasted\n', "'checks' given twice")
        # The second section's lines must not be read as part of the first either.
        self.assertEqual(block['_checks']['provenance'], 'pass, synthetic')
        self.assertProblem(GOOD.replace('  claim_scope: pass, synthetic\n',
                                        '  claim_scope: pass, synthetic\n  provenance: fail, x\n'),
                           "check 'provenance' given twice")

    def test_unknown_key_and_check_are_refused(self):
        self.assertProblem(GOOD.replace('reasons:', 'verdict_note: x\nreasons:'), "unknown field 'verdict_note'")
        self.assertProblem(GOOD.replace('checks:\n', 'checks:\n  record_binding: pass, x\n'), "unknown check")

    def test_text_after_last_field_is_refused(self):
        self.assertProblem(GOOD + '\nThe body is pasted decompiler output.\n', 'not a field')
        self.assertProblem(GOOD + '### Notes\n', 'not a field')
        self.assertProblem(GOOD + '  - a bullet under reasons\n', 'under reasons')

    def test_wrapped_reasons_continue(self):
        block = parse(GOOD.replace('reasons: synthetic\n', 'reasons: synthetic\n  and wrapped\n'))
        self.assertEqual((block['_problems'], block['reasons']), ([], 'synthetic and wrapped'))

    def test_block_cut_short_is_refused(self):
        cut = GOOD[:GOOD.index('blocking_findings')]
        self.assertProblem(cut, 'states no blocking_findings.*states no naming_findings.*states no reasons')

    def test_malformed_lines_are_refused(self):
        for line in ('verdict : approve', 'Verdict: approve', '  verdict: approve', 'verdict:approve',
                     'escalation_category:'):
            with self.subTest(line=line):
                text = GOOD.replace('verdict: approve\n', line + '\n')
                self.assertTrue(parse(text)['_problems'])

    def test_check_sub_line_outside_checks_is_refused(self):
        self.assertProblem(GOOD.replace('reasons:', 'reasons: x\n  provenance: pass, y\nzz:'), 'unknown field|under')


class NamingFilterTests(unittest.TestCase):
    def test_byte_and_disassembly_forms_are_refused(self):
        for bad in ('0x48 0x8b 0x05 0xc3 0x90 0x90', '0x48,0x8b,0x05', '48,8b,05,c3,90,90,cc,cc',
                    '48;8b;05;c3', '48:8b:05:c3', r'\x48\x8b\x05\xc3', r'see \x48 \x8b',
                    'mov rax, qword ptr [rcx+8]; call qword ptr [rax+0x18]', 'load from [rcx + 8]',
                    'read [R14D]', 'via dword ptr', 'ptr [x]', 'see ~/private/dump', 'see ~\\dump'):
            with self.subTest(bad=bad):
                self.assertIsNotNone(naming_finding_problem(bad))

    def test_ordinary_naming_prose_passes(self):
        for good in ('unk020 at offset 0x20 is an NG name without a label line',
                     'unk020 and unk028 are NG names (CharmedBaryon/CommonLibSSE-NG@b93280e)',
                     'members 0x10, 0x18 named from the community header', 'the pointer name is a guess',
                     'SIBLING label for value lacks the path note', 'fields a, b, c are guesses'):
            with self.subTest(good=good):
                self.assertIsNone(naming_finding_problem(good))


class HeaderTests(unittest.TestCase):
    def test_header_is_strict(self):
        head = '# Review t\n\nreviewer_model: m\nfresh_context: yes\ndrafted_or_triaged_any_reviewed_function: no\n'
        _, header, _ = af.review_blocks(head)
        self.assertEqual(header['_problems'], [])
        for extra in ('fresh_context: no\n', 'note: x\n', 'Some prose.\n'):
            with self.subTest(extra=extra):
                _, header, _ = af.review_blocks(head + extra)
                self.assertTrue(header['_problems'])

    def test_text_before_title_is_not_header(self):
        _, header, _ = af.review_blocks('chatter\n## x\n# Review t\n\nreviewer_model: m\n')
        self.assertEqual(header['_problems'], [])


class EndToEndTests(TwoTierFixture, unittest.TestCase):
    def edited(self, task, old, new):
        path = self.review_file(task, [self.block()])
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1))
        return str(path)

    def test_undashed_blocking_finding_is_not_accepted(self):
        path = self.edited('r-p1', 'blocking_findings: none\n',
                           'blocking_findings:\n  the loop body is pasted decompiler output\n')
        self.assertRefused('breaks the reviewer.md format', lambda: af.accept_many(self.root, path, when=WHEN))

    def test_undashed_naming_finding_is_not_dropped(self):
        path = self.edited('r-p2', 'naming_findings: none\n',
                           'naming_findings:\n  unk020 is an NG name with no label line\n')
        self.assertRefused('breaks the reviewer.md format', lambda: af.accept_many(self.root, path, when=WHEN))

    def test_second_checks_section_is_not_accepted(self):
        path = self.edited('r-p3', 'reasons: synthetic\n', 'checks:\n  provenance: fail, pasted\nreasons: synthetic\n')
        self.assertRefused("'checks' given twice", lambda: af.accept_many(self.root, path, when=WHEN))

    def test_malformed_block_of_another_function_refuses_the_review(self):
        path = self.review_file('r-two', [self.block(), dict(self.block(), rva=0x3000, size=8)])
        text = path.read_text()
        cut = text.rindex('reasons: synthetic\n')
        path.write_text(text[:cut] + 'reasons: synthetic\nprose the tool cannot place\n')
        self.assertRefused('0x3000 8.*breaks', lambda: af.accept_many(self.root, str(path), when=WHEN))

    def test_header_prose_is_refused(self):
        path = self.edited('r-head', 'sampling_second_pass: no\n', 'sampling_second_pass: no\nI read it twice.\n')
        self.assertRefused('header breaks', lambda: af.accept_many(self.root, path, when=WHEN))

    def test_clean_review_still_accepted(self):
        af.accept_many(self.root, str(self.review_file('r-ok', [self.block()])), when=WHEN)
        self.assertEqual(self.entry()['status'], 'matched')


class LegacyRecordTests(unittest.TestCase):
    """Records below schema 3 pass only if listed, unchanged, in tools/legacy_review_records.json."""

    def listed(self):
        return json.loads(check.LEGACY_REVIEW_RECORDS.read_text())['records']

    def test_list_matches_the_tracked_records(self):
        listed = self.listed()
        self.assertEqual(len(listed), 58)
        for name, digest in listed.items():
            path = ROOT / name
            if not path.is_file():
                continue  # revoked since; its absence is the inventory's concern
            record = json.loads(path.read_text())
            if record['review_record_schema'] < check.REVIEW_RECORD_SCHEMA:
                self.assertEqual(check.legacy_review_digest(record), digest, name)
                self.assertTrue(check.legacy_review_allowed(name, record), name)

    def test_edited_or_unlisted_legacy_record_is_refused(self):
        # A listed record still in the tree (no git history needed, so a shallow clone runs this).
        name, record = next((n, r) for n, r in ((n, json.loads((ROOT / n).read_text()))
                                                 for n in sorted(self.listed()) if (ROOT / n).is_file())
                            if r['review_record_schema'] < check.REVIEW_RECORD_SCHEMA)
        self.assertTrue(check.legacy_review_allowed(name, record))
        self.assertTrue(check.legacy_review_allowed(name, json.loads(json.dumps(record, indent=7))))
        for key, value in (('review_date', '2000-01-01'), ('reviewer_model', 'someone-else'),
                           ('review_sha256', 'b' * 64)):
            with self.subTest(key=key):
                self.assertFalse(check.legacy_review_allowed(name, dict(record, **{key: value})))
        self.assertFalse(check.legacy_review_allowed(name.replace('.review.json', '0.review.json'), record))


class LegacyRecordGateTests(GateFixture, unittest.TestCase):
    def test_hand_written_legacy_record_is_refused_by_the_gate(self):
        # The fixture allows its own records; the real list does not hold them.
        check.legacy_review_allowed = REAL_LEGACY_ALLOWED
        for schema in (1, 2):
            with self.subTest(schema=schema):
                review = dict(self.review, review_record_schema=schema)
                if schema == 2:
                    review.update(review_kind='full', previous_source_digest=None, previous_review_sha256=None,
                                  previous_code_section_sha256=None,
                                  code_section_sha256=self.record['runs'][0]['report']['candidate'].get(
                                      'code_section_sha256'))
                self.write(REVIEW, json.dumps(review))
                with self.assertRaisesRegex(ValueError, 'accepted only for the unchanged records'):
                    validate(self.data, self.target, root=self.root)


if __name__ == '__main__':
    unittest.main()
