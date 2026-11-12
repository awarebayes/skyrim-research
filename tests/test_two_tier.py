"""Two-tier acceptance (docs/verification.md, "Acceptance rule"): tier 1 blocking grounds, naming
findings stored and filtered, tier 2 `named`, subset selection, and label-only re-acceptance.

Synthetic repository from test_acceptance_flow.FlowFixture, with the unit rewritten so that
tools/lint_reconstruction.py accepts it (label-only re-acceptance lints the unit). The label
check reads private community checkouts, so `accept_function.label_findings` is stood in for.
"""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import accept_function as af  # noqa: E402
import build_index  # noqa: E402
import build_site  # noqa: E402
from check import naming_finding_problem, validate  # noqa: E402
from lint_reconstruction import lint_file, lint_tree  # noqa: E402
from test_acceptance_flow import GROWN, OTHER_SECTION, WHEN, FlowFixture  # noqa: E402
from test_match_gate import CPP, HDR, REVIEW  # noqa: E402

LINT_HDR = '''// SyntheticSum: synthetic fixture for build synthetic-fixture.
// Source exposure: black-box
// Labels: v2
// SyntheticSum: GUESS
#pragma once
struct SyntheticSum { int value; };
int SyntheticAddOne(int);
'''
LINT_CPP = '''// SyntheticSum for build synthetic-fixture, RVA 0x1010, 9 bytes.
// Source exposure: black-box
// Evidence: findings/synthetic.md
// Drafted by test
// Recipe: reconstruction/recipes/synthetic.json
// Labels: v2
#include "SyntheticSum.h"
int SyntheticSum(int* p) { return SyntheticAddOne(*p); }
'''
FINDING = 'unk020 and unk028 are NG names (CharmedBaryon/CommonLibSSE-NG@b93280e) without a label line'


class TwoTierFixture(FlowFixture):
    def setUp(self):
        super().setUp()
        self.write(HDR, LINT_HDR)
        self.write(CPP, LINT_CPP)
        self.regenerate()
        self.assertEqual(lint_tree(self.root, [CPP, HDR]), [])
        self.labels = []
        original = af.label_findings
        af.label_findings = lambda root, files: list(self.labels)
        self.addCleanup(setattr, af, 'label_findings', original)

    def accept(self, task='review-one', select=None, **block):
        path = self.review_file(task, [self.block(**block)])
        return af.accept_many(self.root, str(path), when=WHEN, select=select)

    def stored(self):
        return json.loads((self.root / REVIEW).read_text())

    def entry(self):
        return self.progress()['functions'][0]

    def unchanged(self):
        return {p: (self.root / p).read_bytes() if (self.root / p).exists() else None
                for p in ('data/progress.json', REVIEW, build_index.INDEX)}

    def assertRefused(self, pattern, call):
        before = self.unchanged()
        with self.assertRaisesRegex((af.Refused, ValueError), pattern):
            call()
        self.assertEqual(self.unchanged(), before)


class BlockingGroundTests(TwoTierFixture, unittest.TestCase):
    def test_reject_still_blocks_whatever_its_reasons(self):
        # A reject is never accepted, even when the only findings are naming ones.
        self.assertRefused('no approve block', lambda: self.accept(verdict='reject', naming_findings=[FINDING]))
        self.assertRefused("verdict 'reject'", lambda: af.accept(
            self.root, 'synthetic-fixture', self.fn['rva'],
            self.review_file('review-r', [self.block(verdict='reject')]), 'approve', when=WHEN))

    def test_approve_listing_blocking_findings_refused(self):
        self.assertRefused('lists blocking findings', lambda: self.accept(blocking_findings=['pasted decompiler output']))

    def test_approve_with_failed_blocking_check_refused(self):
        for name in ('plausible_source', 'provenance', 'claim_scope', 'publication_hygiene'):
            with self.subTest(name):
                self.assertRefused(f'checks {name}: pass', lambda: self.accept(task=f'r-{name.replace("_", "-")}',
                                                                              checks={name: 'fail'}))

    def test_approve_without_a_blocking_check_refused(self):
        self.assertRefused('checks provenance: pass', lambda: self.accept(checks={'provenance': None}))

    def test_approve_with_binding_disagreement_refused(self):
        self.assertRefused('report_binding: agree', lambda: self.accept(binding='disagree, digest differs'))

    def test_approve_must_state_both_finding_lists(self):
        self.assertRefused('no naming_findings', lambda: self.accept(task='r-a', naming_findings=None))
        self.assertRefused('no blocking_findings', lambda: self.accept(task='r-b', blocking_findings=None))

    def test_unpublishable_naming_finding_refused(self):
        for bad in ('see /Users/someone/.local/dump.txt', 'bytes 48 8b 05 c3 here', 'write it as { return 1; }',
                    'digest e856137b470aa9369a5a98895cc57987'):
            with self.subTest(bad):
                self.assertRefused('naming finding holds', lambda: self.accept(task='r-bad', naming_findings=[bad]))
                (self.root / '.local/reviews/r-bad.md').unlink()


class NamingFindingsTests(TwoTierFixture, unittest.TestCase):
    def test_naming_findings_do_not_block_and_are_stored(self):
        self.accept(naming_findings=[FINDING, 'the header wording could cite NG more exactly'])
        record = self.stored()
        self.assertEqual(record['review_record_schema'], 3)
        self.assertEqual(record['naming_findings'], [FINDING, 'the header wording could cite NG more exactly'])
        self.assertEqual(self.entry()['status'], 'matched')
        self.assertIs(self.entry()['named'], False)
        self.assertEqual(list(self.entry()).index('named'), list(self.entry()).index('status') + 1)
        self.validate()
        self.assertIn('| matched | full | open |', (self.root / build_index.INDEX).read_text())

    def test_wrapped_finding_is_one_item(self):
        self.write('.local/reviews/r-wrap.md', self.review_file('r-wrap', [self.block()]).read_text().replace(
            'naming_findings: none\n', 'naming_findings:\n  - first part\n    continued\n  - second\n'))
        af.accept_many(self.root, str(self.root / '.local/reviews/r-wrap.md'), when=WHEN)
        self.assertEqual(self.stored()['naming_findings'], ['first part continued', 'second'])

    def test_no_findings_and_clean_labels_give_named(self):
        self.accept()
        self.assertEqual(self.stored()['naming_findings'], [])
        self.assertIs(self.entry()['named'], True)
        self.assertIn('| matched | full | checked |', (self.root / build_index.INDEX).read_text())
        self.validate()

    def test_label_check_findings_or_old_labels_leave_named_false(self):
        self.labels = ['a COMMUNITY name is not in the checkout']
        self.accept()
        self.assertIs(self.entry()['named'], False)

    def test_unit_without_labels_v2_is_not_named(self):
        self.write(HDR, LINT_HDR.replace('// Labels: v2\n', ''))
        self.regenerate()
        self.accept()
        self.assertIs(self.entry()['named'], False)

    def test_refresh_named_changes_only_the_tier(self):
        self.labels = ['finding']
        self.accept()
        before = self.progress()
        self.labels = []
        changed = af.refresh_named(self.root, when=WHEN)
        self.assertEqual(changed, ['data/progress.json', build_index.INDEX])
        after = self.progress()
        self.assertIs(after['functions'][0]['named'], True)
        after['functions'][0]['named'] = False
        self.assertEqual(after['functions'], before['functions'])
        self.assertEqual(af.refresh_named(self.root, when=WHEN), [])
        self.validate()

    def test_revoke_drops_named(self):
        self.accept()
        af.revoke(self.root, 'synthetic-fixture', self.fn['rva'], 'audit', when=WHEN)
        self.assertNotIn('named', self.entry())

    def test_site_and_packet_show_the_tier_apart(self):
        self.accept()
        html = build_site.render(self.progress(), 'test')
        self.assertIn('names and labels also checked for 1', html)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            af.review_packet.main(['--root', str(self.root), '--no-notes', '--no-community', f'0x{self.fn["rva"]:x}'])
        self.assertIn('naming findings: none; names: checked', out.getvalue())


class ForgedRecordTests(TwoTierFixture, unittest.TestCase):
    """Hand-edited records and inventory fields that the validator must refuse."""

    def setUp(self):
        super().setUp()
        self.accept()
        self.good = self.stored()

    def rejects(self, pattern, entry=None, **change):
        self.write(REVIEW, json.dumps(dict(self.good, **change)))
        if entry is not None:
            data = self.progress()
            data['functions'][0].update(entry)
            self.save_progress(data)
        with self.assertRaisesRegex(ValueError, pattern):
            self.validate()

    def save_progress(self, data):
        self.write('data/progress.json', json.dumps(data, indent=2) + '\n')

    def test_named_true_with_open_findings_rejected(self):
        self.rejects('named is true', naming_findings=[FINDING])

    def test_named_true_on_schema_2_record_rejected(self):
        record = {k: v for k, v in self.good.items() if k != 'naming_findings'}
        self.write(REVIEW, json.dumps(dict(record, review_record_schema=2)))
        with self.assertRaisesRegex(ValueError, 'named is true'):
            self.validate()

    def test_named_on_unmatched_entry_rejected(self):
        data = self.progress()
        data['functions'][1]['named'] = False
        self.save_progress(data)
        with self.assertRaisesRegex(ValueError, 'not matched'):
            self.validate()

    def test_named_must_be_boolean(self):
        self.rejects('true or false', entry={'named': 'yes'})

    def test_full_record_without_findings_list_rejected(self):
        self.rejects('naming_findings must be a list', naming_findings=None, entry={'named': False})

    def test_unpublishable_finding_in_record_rejected(self):
        self.rejects('private or absolute path', naming_findings=['C:\\dump\\x.txt'], entry={'named': False})
        self.rejects('at most 20', naming_findings=['n'] * 21, entry={'named': False})

    def test_schema_3_missing_field_rejected(self):
        record = {k: v for k, v in self.good.items() if k != 'naming_findings'}
        self.write(REVIEW, json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'fields must be exactly'):
            self.validate()

    def test_label_only_kind_needs_schema_3(self):
        record = {k: v for k, v in self.good.items() if k != 'naming_findings'}
        self.write(REVIEW, json.dumps(dict(record, review_record_schema=2, review_kind='label-only')))
        with self.assertRaisesRegex(ValueError, 'review_kind must be one of'):
            self.validate()

    def test_forged_label_only_records_rejected(self):
        old = self.grow_unit()
        af.label_only(self.root, when=WHEN)
        self.good = self.stored()
        self.validate()
        self.rejects('previous_review_sha256 equals review_sha256', previous_review_sha256='f' * 64)
        self.rejects('compared code section changed', previous_code_section_sha256=OTHER_SECTION)
        self.rejects('differs from the match record', code_section_sha256=OTHER_SECTION,
                     previous_code_section_sha256=OTHER_SECTION)
        self.rejects('previous_source_digest other than', previous_source_digest=self.good['source_digest'])
        self.assertNotEqual(old, self.good['source_digest'])


class LabelOnlyTests(TwoTierFixture, unittest.TestCase):
    def test_label_only_reaccepts_and_carries_the_approval(self):
        self.accept(naming_findings=[FINDING])
        first = self.stored()
        old = self.grow_unit()
        changed = af.label_only(self.root, when=WHEN)
        self.assertIn(REVIEW, changed)
        record = self.stored()
        self.assertEqual(record['review_kind'], 'label-only')
        self.assertEqual(record['previous_source_digest'], old)
        self.assertEqual(record['source_digest'], self.record_digest())
        for key in ('reviewer_model', 'review_task_id', 'review_sha256', 'review_date', 'naming_findings'):
            self.assertEqual(record[key], first[key], key)
        self.assertEqual(record['previous_review_sha256'], first['review_sha256'])
        self.assertEqual(record['previous_code_section_sha256'], self.real)
        self.assertEqual(record['code_section_sha256'], self.real)
        self.assertIs(self.entry()['named'], False)
        self.validate()
        self.assertIn('| matched | label-only | open |', (self.root / build_index.INDEX).read_text())

    def record_digest(self):
        return json.loads((self.root / self.fn['report']).read_text())['source']['digest']

    def test_label_only_chains(self):
        self.accept()
        first = self.stored()
        self.grow_unit()
        af.label_only(self.root, when=WHEN)
        self.write(CPP, (self.root / CPP).read_text() + '// SyntheticTwice: GUESS\n')
        self.regenerate()
        af.label_only(self.root, select={self.fn['id']}, when=WHEN)
        record = self.stored()
        self.assertEqual((record['review_sha256'], record['previous_review_sha256']),
                         (first['review_sha256'], first['review_sha256']))
        self.assertIs(self.entry()['named'], True)
        self.validate()

    def test_label_only_from_schema_2_approval_leaves_tier_2_unset(self):
        self.accept()
        legacy = {k: v for k, v in self.stored().items() if k != 'naming_findings'}
        self.write(REVIEW, json.dumps(dict(legacy, review_record_schema=2)))
        data = self.progress()
        del data['functions'][0]['named']
        self.save_data_raw(data)
        self.validate()
        self.assertEqual(af.refresh_named(self.root, when=WHEN), [])
        self.grow_unit()
        af.label_only(self.root, when=WHEN)
        self.assertIsNone(self.stored()['naming_findings'])
        self.assertNotIn('named', self.entry())
        self.validate()
        data = self.progress()
        data['functions'][0]['named'] = True
        self.save_data_raw(data)
        with self.assertRaisesRegex(ValueError, 'named is true'):
            self.validate()

    def save_data_raw(self, data):
        self.write('data/progress.json', json.dumps(data, indent=2) + '\n')

    def test_refused_when_code_section_differs(self):
        self.regenerate(OTHER_SECTION)
        self.accept()
        self.grow_unit()
        self.assertRefused('compared code section changed', lambda: af.label_only(self.root, when=WHEN))

    def test_refused_when_a_host_disagrees(self):
        self.accept()
        self.grow_unit()
        self.record['runs'][1]['report']['candidate']['code_section_sha256'] = OTHER_SECTION
        self.save_record()
        self.assertRefused('runs disagree', lambda: af.label_only(self.root, when=WHEN))

    def test_refused_when_record_lacks_code_section(self):
        self.accept()
        self.grow_unit(section=None)
        self.assertRefused('carries no code-section hash', lambda: af.label_only(self.root, when=WHEN))

    def test_refused_before_reconfirm(self):
        self.accept()
        self.write(CPP, (self.root / CPP).read_text() + GROWN)
        self.assertRefused('no matched entry has a re-confirmed record',
                           lambda: af.label_only(self.root, when=WHEN))
        self.assertRefused('re-confirm first', lambda: af.label_only(self.root, select={self.fn['id']}, when=WHEN))

    def test_refused_when_review_is_current(self):
        self.accept()
        self.assertRefused('already binds the current record',
                           lambda: af.label_only(self.root, select={self.fn['id']}, when=WHEN))

    def test_refused_for_unaccepted_entry(self):
        self.assertRefused('label-only re-acceptance is for matched entries',
                           lambda: af.label_only(self.root, select={self.fn['id']}, when=WHEN))

    def test_refused_when_lint_fails(self):
        self.accept()
        self.write(CPP, (self.root / CPP).read_text() + '__forceinline int Helper() { return 1; }\n')
        self.regenerate()
        self.assertRefused('reconstruction lint', lambda: af.label_only(self.root, when=WHEN))

    def test_refused_when_superseded_record_is_not_an_approve(self):
        self.accept()
        record = self.stored()
        self.grow_unit()
        self.write(REVIEW, json.dumps(dict(record, verdict='reject')))
        self.assertRefused('not an approve', lambda: af.label_only(self.root, when=WHEN))

    def test_full_review_closes_carried_findings(self):
        self.accept(naming_findings=[FINDING])
        self.grow_unit()
        af.label_only(self.root, when=WHEN)
        self.accept(task='review-names')
        record = self.stored()
        self.assertEqual((record['review_kind'], record['naming_findings']), ('full', []))
        self.assertIs(self.entry()['named'], True)
        self.validate()

    def test_delta_review_still_refused_from_label_only_digest(self):
        self.accept()
        self.grow_unit()
        af.label_only(self.root, when=WHEN)
        digest = self.stored()['source_digest']
        self.assertRefused('already matched', lambda: self.accept(
            task='review-d', review_kind='delta', previous_source_digest=digest, code_section_unchanged='yes'))

    def test_cli_label_only(self):
        self.accept()
        self.grow_unit()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            status = af.main(['--root', str(self.root), '--label-only', '--functions', f'0x{self.fn["rva"]:x}'])
        self.assertEqual(status, 0)
        self.assertIn('label-only', out.getvalue())
        self.validate()


class SelectionTests(TwoTierFixture, unittest.TestCase):
    def blocks(self):
        return [self.block(), {'rva': 0x3000, 'size': 8, 'digest': 'e' * 64}]

    def test_subset_of_a_review_is_accepted(self):
        path = self.review_file('review-batch', self.blocks())
        changed, skipped = af.accept_many(self.root, str(path), when=WHEN, select={self.fn['id']})
        self.assertIn(REVIEW, changed)
        self.assertEqual(skipped, ['synthetic-fixture 0x3000 8: not selected'])
        self.assertEqual([f['status'] for f in self.progress()['functions']], ['matched', 'reconstructed'])
        self.validate()

    def test_selected_function_without_approve_block_refused(self):
        path = self.review_file('review-batch', [self.block()])
        self.assertRefused('without an approve block', lambda: af.accept_many(
            self.root, str(path), when=WHEN, select={self.fn['id'], 'synthetic-fixture-0x3000'}))

    def test_selection_names_must_resolve(self):
        data = self.progress()
        with self.assertRaisesRegex(af.Refused, '0 inventory entries'):
            af.resolve_selection(self.root, data, ['0x9999'])
        with self.assertRaisesRegex(af.Refused, 'no inventory entry'):
            af.resolve_selection(self.root, data, units=['synthetic/Missing'])
        self.assertEqual(af.resolve_selection(self.root, data, units=['synthetic/SyntheticSum']), {self.fn['id']})
        self.assertEqual(af.resolve_selection(self.root, data, units=[CPP]), {self.fn['id']})

    def test_cli_selection(self):
        path = self.review_file('review-batch', self.blocks())
        with contextlib.redirect_stdout(io.StringIO()) as out:
            status = af.main(['--root', str(self.root), '--all-approved', '--review', str(path),
                              '--units', 'synthetic/SyntheticSum'])
        self.assertEqual(status, 0)
        self.assertIn('not accepted: synthetic-fixture 0x3000 8: not selected', out.getvalue())
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(af.main(['--root', str(self.root), '--functions', self.fn['id']]), 1)
        self.assertIn('go with --all-approved', err.getvalue())

    def test_only_entries_stale_before_and_outside_the_run_are_tolerated(self):
        self.accept()
        self.grow_unit()
        validate(self.progress(), self.target, root=self.root, stale_ok={self.fn['id']})
        for tolerated in (set(), {'synthetic-fixture-0x3000'}, False):
            with self.subTest(tolerated=tolerated), self.assertRaisesRegex(ValueError, 'Stale acceptance'):
                validate(self.progress(), self.target, root=self.root, stale_ok=tolerated)


class LintTests(unittest.TestCase):
    def lint(self, text, name='reconstruction/forms/Thing.h'):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / name).parent.mkdir(parents=True)
            (root / name).write_text(text)
            return lint_file(root, name, 'b')

    HEAD = '// Thing, build b. Source exposure: black-box. Names: GUESS.\n'

    def test_noinline_needs_justification(self):
        # A code line first, so the header comment is not the line before the attribute.
        body = 'struct Other;\nstruct Thing { __declspec(noinline) int Get(); };\n'
        self.assertTrue(any('noinline needs a justification' in p for p in self.lint(self.HEAD + body)))
        justified = body.replace('struct Thing', '// called by address from other units, kept out of line\nstruct Thing')
        self.assertEqual(self.lint(self.HEAD + justified), [])

    def test_gpl_label_needs_gpl_in_header(self):
        body = 'struct Thing {\n    // Get: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)\n    int Get();\n};\n'
        self.assertTrue(any('state the GPL licence' in p for p in self.lint(self.HEAD + body)))
        self.assertEqual(self.lint(self.HEAD + '// This file is GPL-3.0 (powerof3 names).\n' + body), [])
        # A known repository's label must carry its own licence word (test_review_parser covers more);
        # an unlisted repository's MIT label has no GPL obligation.
        self.assertTrue(any('licensed "GPL-3.0"' in p for p in self.lint(self.HEAD + body.replace('GPL-3.0', 'MIT'))))
        self.assertEqual(self.lint(self.HEAD + body.replace('GPL-3.0', 'MIT').replace('powerof3', 'someone')), [])


class FindingFilterTests(unittest.TestCase):
    def test_filter(self):
        self.assertIsNone(naming_finding_problem(FINDING))
        self.assertIsNone(naming_finding_problem('meh321 names 0x22b2c0 TESObjectREFR::GetInventoryChanges'))
        for bad in ('', 'x' * 301, 'line\nbreak', 'caf\u00e9', '```cpp', '/home/u/x', '01 02 03 04'):
            self.assertIsNotNone(naming_finding_problem(bad), bad)


if __name__ == '__main__':
    unittest.main()
