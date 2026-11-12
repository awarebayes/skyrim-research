"""Probes for the combined rule: two-tier acceptance with the FNV sibling source.

Under the two-tier rule (docs/verification.md, "Acceptance rule") undeclared reuse of a sibling
body or a false origin or licence statement is a blocking provenance ground, while a missing or
imperfect `SIBLING` name label is a naming finding. These tests probe the places where the two
changes meet: the lint keeps the licence rule and the sibling rules together, a labelled unit
passes lint and the label check against a synthetic sibling clone, an approve whose only findings
are sibling-label ones is accepted, and a reject or an approve citing undeclared reuse is not. They
also cover the review packet's re-review options (`--prior-review`, `--prior-ref`, `--template`).

All inputs are synthetic: the "sibling" is a two-file git repository built here, never the real
clone, and the review files are written by the tests.
"""
import contextlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import accept_function as af  # noqa: E402
import check_labels  # noqa: E402
import lint_reconstruction  # noqa: E402
from lint_reconstruction import lint_file  # noqa: E402
import review_packet  # noqa: E402
from test_acceptance_flow import WHEN, git as flow_git  # noqa: E402
from test_match_gate import CPP, HDR  # noqa: E402
from test_two_tier import LINT_CPP, LINT_HDR, TwoTierFixture  # noqa: E402

PIN = '91e1b6e8'
LABEL = f'SIBLING(momusdigital/fnv_decomp@{PIN}, no-licence)'
SIBLING_FINDING = 'SyntheticSum::value comes from the sibling decompilation but is labelled GUESS, not SIBLING'
UNDECLARED = 'reuses the sibling body of SyntheticSum without a Sibling source header line'


def sibling_unit(rev=PIN):
    """Header and source of the synthetic unit, declaring one sibling name and one reused body."""
    hdr = LINT_HDR.replace('// SyntheticSum: GUESS\n',
                           f'// SyntheticSum SyntheticSum::value: SIBLING(momusdigital/fnv_decomp@{rev}, no-licence)\n')
    cpp = LINT_CPP.replace('// Labels: v2\n',
                           f'// Labels: v2\n// Sibling source: momusdigital/fnv_decomp@{rev} src/core/sum.cpp:3\n')
    return hdr, cpp


def run_git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid',
                           '-c', 'commit.gpgsign=false', *args],
                          capture_output=True, text=True, check=True).stdout.strip()


class SiblingFixture(TwoTierFixture):
    def make_clone(self):
        """A synthetic sibling decompilation declaring SyntheticSum::value, with one source file."""
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        fnv = Path(holder.name) / 'fnv_clone'
        (fnv / 'include').mkdir(parents=True)
        (fnv / 'build').mkdir()
        (fnv / 'src/core').mkdir(parents=True)
        (fnv / 'include/SyntheticSum.h').write_text('class SyntheticSum\n{\npublic:\n    int value;\n};\n')
        (fnv / 'src/core/sum.cpp').write_text('#include "SyntheticSum.h"\n\nint SyntheticSum::Get()\n{\n}\n')
        (fnv / 'build/units.json').write_text(json.dumps({'units': [{'source': 'src/core/sum.cpp', 'flags': ['/O2'],
            'functions': [{'symbol': '?Get@SyntheticSum@@QAEHXZ', 'address': '0x1', 'size': 3}]}]}))
        run_git(fnv, 'init', '-q')
        run_git(fnv, 'add', '.')
        run_git(fnv, 'commit', '-qm', 'fixture')
        return fnv, run_git(fnv, 'rev-parse', 'HEAD')[:8]


class LintAndLabelProbes(SiblingFixture, unittest.TestCase):
    def lint(self, *names):
        return [p for name in names for p in lint_file(self.root, name, None)]

    def test_labelled_unit_passes_lint_and_label_check_against_a_clone(self):
        fnv, rev = self.make_clone()
        hdr, cpp = sibling_unit(rev)
        self.write(HDR, hdr)
        self.write(CPP, cpp)
        # The synthetic clone cannot have the real pin, so the allowed-sibling table points at it.
        with mock.patch.dict(lint_reconstruction.SIBLING_SOURCES, {'momusdigital/fnv_decomp': (rev, 'no-licence')}):
            self.assertEqual(self.lint(CPP, HDR), [])
        self.write('findings/synthetic.md', '# synthetic, RVA 0x1010\n')
        flow_git(self.root, 'init', '-q')
        flow_git(self.root, 'add', '-A')
        flow_git(self.root, 'commit', '-q', '-m', 'unit')
        findings = check_labels.check([self.root / CPP, self.root / HDR], {}, root=self.root,
                                      siblings={'momusdigital/fnv_decomp': str(fnv)})
        self.assertEqual(findings, [])
        # The same unit citing a line the clone does not have is a label-check finding.
        self.write(CPP, cpp.replace('sum.cpp:3', 'sum.cpp:300'))
        findings = check_labels.check([self.root / CPP], {}, root=self.root,
                                      siblings={'momusdigital/fnv_decomp': str(fnv)})
        self.assertTrue(any('past the end of the file' in f for f in findings), findings)

    def test_real_pin_passes_lint_and_other_pins_do_not(self):
        hdr, cpp = sibling_unit()
        self.write(HDR, hdr)
        self.write(CPP, cpp)
        self.assertEqual(self.lint(CPP, HDR), [])
        hdr2, cpp2 = sibling_unit('abcdef12')
        self.write(HDR, hdr2)
        self.write(CPP, cpp2)
        problems = self.lint(CPP, HDR)
        self.assertEqual(len([p for p in problems if f'pinned at {PIN}' in p]), 2, problems)

    def test_wrong_licence_word_is_a_lint_problem(self):
        hdr, _ = sibling_unit()
        self.write(HDR, hdr.replace('no-licence', 'MIT'))
        self.assertTrue(any('licence word "no-licence"' in p for p in self.lint(HDR)))

    def test_sibling_source_outside_the_leading_comment_is_refused(self):
        _, cpp = sibling_unit()
        line = f'// Sibling source: momusdigital/fnv_decomp@{PIN} src/core/sum.cpp:3\n'
        self.write(CPP, cpp.replace(line, '') + line)
        self.assertTrue(any('belong in the leading comment' in p for p in self.lint(CPP)))

    def test_licence_rule_and_sibling_rules_apply_in_one_file(self):
        # Both branches' rules are live together: a GPL COMMUNITY label without GPL in the header
        # and a sibling citation at a wrong pin are reported side by side.
        hdr, _ = sibling_unit('abcdef12')
        # The GPL label sits below the leading comment, so the header does not mention GPL.
        hdr = hdr.replace('#pragma once\n', '#pragma once\n'
                          '// SyntheticSum::unk: COMMUNITY(powerof3/CommonLibSSE@b93280e, GPL-3.0)\n')
        self.write(HDR, hdr)
        problems = self.lint(HDR)
        self.assertTrue(any('GPL-licensed COMMUNITY label' in p for p in problems), problems)
        self.assertTrue(any(f'pinned at {PIN}' in p for p in problems), problems)
        # A justification-less noinline in the same file is still caught.
        self.write(HDR, hdr.replace('int SyntheticAddOne(int);', '__declspec(noinline) int SyntheticAddOne(int);'))
        self.assertTrue(any('noinline needs a justification' in p for p in self.lint(HDR)))


class AcceptanceProbes(SiblingFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        hdr, cpp = sibling_unit()
        self.write(HDR, hdr)
        self.write(CPP, cpp)
        self.regenerate()

    def test_approve_with_only_sibling_label_findings_is_accepted(self):
        self.accept(naming_findings=[SIBLING_FINDING, 'SyntheticSum label omits the sibling path note'])
        self.assertEqual(self.entry()['status'], 'matched')
        self.assertIs(self.entry()['named'], False)
        self.assertEqual(self.stored()['naming_findings'][0], SIBLING_FINDING)
        self.validate()

    def test_reject_on_undeclared_reuse_blocks(self):
        self.assertRefused('no approve block', lambda: self.accept(
            verdict='reject', checks={'provenance': 'fail'}, blocking_findings=[UNDECLARED]))
        self.assertEqual(self.entry()['status'], 'mapped')

    def test_approve_that_lists_undeclared_reuse_is_refused(self):
        self.assertRefused('lists blocking findings', lambda: self.accept(blocking_findings=[UNDECLARED]))
        self.assertRefused('checks provenance: pass', lambda: self.accept(task='r-prov', checks={'provenance': 'fail'}))

    def test_undeclared_reuse_filed_as_a_naming_finding_is_not_detectable(self):
        # Known limit: the tool cannot tell a misfiled blocking reason from a naming one; the
        # Reviewer checklist and the sampling second pass are what stop this.
        self.accept(naming_findings=[UNDECLARED])
        self.assertEqual(self.entry()['status'], 'matched')


OLD_BLOCK = '''
## synthetic-fixture 0x{rva:x} {size}

verdict: {verdict}
escalation_category: none
review_kind: full
source_paths: {cpp} {hdr}
source_digest: {digest}
report_path: reports/synthetic.json
reasons: the sibling label on value is missing; otherwise plausible.
'''


class PacketProbes(SiblingFixture, unittest.TestCase):
    def old_review(self, digest=None, verdict='reject'):
        text = ('# Review review-old\n\nreviewer_model: claude-opus-5-5\nfresh_context: yes\n'
                'drafted_or_triaged_any_reviewed_function: no\n'
                + OLD_BLOCK.format(rva=self.fn['rva'], size=self.fn['size'], cpp=CPP, hdr=HDR, verdict=verdict,
                                   digest=digest or self.record['source']['digest']))
        self.write('.local/reviews/review-old.md', text)
        return str(self.root / '.local/reviews/review-old.md')

    def packet(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = review_packet.main(['--root', str(self.root), '--no-notes', '--no-community', *args])
        return code, out.getvalue()

    def test_old_review_is_context_with_a_new_format_template(self):
        path = self.old_review()
        code, out = self.packet('--prior-review', path)
        self.assertEqual(code, 0)
        self.assertIn('earlier verdict: reject (full) on digest ' + self.record['source']['digest'], out)
        self.assertIn('earlier format: old (no report_binding, checks, blocking_findings, naming_findings)', out)
        self.assertIn('  | reasons: the sibling label on value is missing; otherwise plausible.', out)
        self.assertIn('unit since earlier review: unchanged (same digest)', out)
        self.assertIn('naming_findings: <none', out)
        self.assertRegex(out, r'prior_review: review-old [0-9a-f]{64}')

    def test_filled_template_is_accepted_by_the_tool(self):
        # The template is the format the acceptance tool reads: fill it in and accept it.
        _, out = self.packet('--prior-review', self.old_review())
        blocks = re.findall(r'```text\n(.*?)```', out, re.S)
        header, block = blocks[0], blocks[1]
        filled = header.replace('<task-id>', 'review-new').replace('<model id>', 'claude-opus-5-5')
        filled = filled.replace('<list>', 'G2').replace('<git commit>', '0000000').replace('<yes|no>', 'no')
        block = (block.replace('<approve|reject|escalate>', 'approve')
                 .replace('<provenance|legal|systemic|other|none>', 'none')
                 .replace('<tu-sha256-v1 digest you computed>', self.record['source']['digest'])
                 .replace('<agree|disagree|missing>, <one line>', 'agree, synthetic')
                 .replace('<pass|fail>, <one line>', 'pass, synthetic')
                 .replace('<none, or one "  - <item>" line each below>', 'none')
                 .replace('<none, or one "  - <item>" line each below; published>', '')
                 .replace('<short prose; no code, bytes or disassembly>', 'synthetic'))
        block = block.replace('naming_findings: \n', f'naming_findings:\n  - {SIBLING_FINDING}\n')
        self.assertNotIn('<', block)
        self.write('.local/reviews/review-new.md', filled + '\n' + block)
        af.accept_many(self.root, str(self.root / '.local/reviews/review-new.md'), when=WHEN)
        self.assertEqual(self.entry()['status'], 'matched')
        self.assertEqual(self.stored()['naming_findings'], [SIBLING_FINDING])
        self.validate()

    def test_old_review_alone_is_still_refused(self):
        # An old-format approve, even of the current digest, lacks the two-tier fields.
        self.assertRefused('report_binding|checks|naming_findings|blocking_findings',
                           lambda: af.accept_many(self.root, self.old_review(verdict='approve'), when=WHEN))

    def test_changed_unit_gets_a_verified_diff_or_none(self):
        flow_git(self.root, 'init', '-q')
        flow_git(self.root, 'add', '-A')
        flow_git(self.root, 'commit', '-q', '-m', 'reviewed')
        reviewed = self.record['source']['digest']
        base = run_git(self.root, 'rev-parse', 'HEAD')
        path = self.old_review(reviewed)
        self.grow_unit()
        _, out = self.packet('--prior-review', path)
        self.assertIn(f'diff from {base[:12]} (digest verified)', out)
        self.assertIn('+int SyntheticTwice', out)
        _, out = self.packet('--prior-review', path, '--prior-ref', base)
        self.assertIn('(digest verified)', out)
        # A ref whose digest is not the reviewed one gives no diff.
        flow_git(self.root, 'add', '-A')
        flow_git(self.root, 'commit', '-q', '-m', 'grown')
        _, out = self.packet('--prior-review', path, '--prior-ref', 'HEAD')
        self.assertIn('CHANGED, no verified base: --prior-ref HEAD has digest', out)
        self.assertNotIn('+int SyntheticTwice', out)

    def test_unknown_digest_gives_no_diff(self):
        _, out = self.packet('--prior-review', self.old_review('e' * 64))
        self.assertIn('CHANGED, no verified base: no commit found', out)

    def test_default_selection_skips_functions_accepted_at_the_current_digest(self):
        path = self.old_review()
        self.accept()
        code, _ = self.packet('--prior-review', path)
        self.assertEqual(code, 1)
        code, out = self.packet('--prior-review', path, f'0x{self.fn["rva"]:x}')
        self.assertEqual(code, 0)
        self.assertIn('earlier verdict: reject', out)

    def test_prior_ref_needs_prior_review_and_a_commit(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            review_packet.main(['--root', str(self.root), '--prior-ref', 'HEAD'])
        code, _ = self.packet('--prior-review', self.old_review(), '--prior-ref', 'no-such-ref')
        self.assertEqual(code, 1)

    def test_template_option_alone(self):
        _, out = self.packet('--template', f'0x{self.fn["rva"]:x}')
        self.assertIn('review block to fill', out)
        self.assertNotIn('earlier review', out)
        self.assertNotIn('prior_review:', out)


if __name__ == '__main__':
    unittest.main()
