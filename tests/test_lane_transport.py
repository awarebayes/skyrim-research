"""Original synthetic transport fixtures; acceptance predicates are unchanged."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import flow
import flow_lane as lane


class LaneTransport(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='lane-transport-')
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.source, self.tree = self.tmp / 'source', self.tmp / 'tree'
        for root in (self.source, self.tree):
            (root / '.local/reviews').mkdir(parents=True)

    def test_readonly_identical_review_is_not_rewritten_and_conflict_is_refused(self):
        source = self.source / '.local/reviews/nested/approved.md'
        source.parent.mkdir()
        source.write_text('Original synthetic approval\n')
        source.chmod(0o444)
        dest = lane.copy_private_review(self.source, self.tree, source)
        self.assertEqual(dest.read_bytes(), source.read_bytes())
        self.assertTrue(dest.stat().st_mode & 0o200, 'candidate copies must remain writable')
        dest.chmod(0o444)
        with patch.object(lane.shutil, 'copyfile', side_effect=AssertionError('must not rewrite')):
            self.assertEqual(lane.copy_private_review(self.source, self.tree, source), dest)
        other = self.source / '.local/reviews/different.md'
        other.write_text('Different synthetic approval\n')
        with self.assertRaisesRegex(flow.FlowError, 'conflicting saved review'):
            lane.copy_private_review(self.source, self.tree, other, 'nested/approved.md')
        self.assertEqual(dest.read_bytes(), source.read_bytes())

    def test_source_and_destination_containment_stay_strict(self):
        outside = self.tmp / 'outside.md'
        outside.write_text('Synthetic outside file\n')
        source = self.source / '.local/reviews/link.md'
        source.symlink_to(outside)
        with self.assertRaisesRegex(flow.FlowError, 'escapes private reviews'):
            lane.copy_private_review(self.source, self.tree, source)
        source.unlink()
        source.write_text('Inside\n')
        (self.tree / '.local/reviews/link.md').symlink_to(outside)
        with self.assertRaisesRegex(flow.FlowError, 'escapes private reviews'):
            lane.copy_private_review(self.source, self.tree, source)
        self.assertEqual(outside.read_text(), 'Synthetic outside file\n')

    def test_local_acceptance_review_record_is_carried_without_fabricating_one(self):
        report = 'reports/synthetic/0x1000.json'
        fn = dict(id='synthetic-0x1000', build_id='synthetic', rva=4096, status='matched', report=report)
        data = dict(functions=[fn])
        for root in (self.source, self.tree):
            (root / 'data').mkdir()
            (root / 'data/progress.json').write_text(json.dumps(data))
        record = self.source / report
        record.parent.mkdir(parents=True)
        record.write_text(json.dumps(dict(source=dict(compiled='reconstruction/x/A.cpp',
            translation_unit=['reconstruction/x/A.cpp'], digest='synthetic'))))
        cpp = self.source / 'reconstruction/x/A.cpp'
        cpp.parent.mkdir(parents=True)
        cpp.write_text('Original synthetic source\n')
        review = record.with_suffix('.review.json')
        review.write_text(json.dumps(dict(synthetic=True, verdict='approve')))
        files = flow.carry_into_tree(self.source, self.tree, ['0x1000'], {'0x1000': fn}, harvests={})
        self.assertIn('reports/synthetic/0x1000.review.json', files)
        self.assertEqual((self.tree / review.relative_to(self.source)).read_bytes(), review.read_bytes())
        review.unlink()
        (self.tree / review.relative_to(self.source)).unlink()
        flow.carry_into_tree(self.source, self.tree, ['0x1000'], {'0x1000': fn}, harvests={})
        self.assertFalse((self.tree / review.relative_to(self.source)).exists())

    def test_metadata_from_an_independent_input_is_fetched_before_merge(self):
        def git(root, *args):
            return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
        git(self.tree, 'init', '--quiet', '--initial-branch=main')
        for key, value in [('user.name', 'Synthetic'), ('user.email', 'synthetic@example.invalid')]:
            git(self.tree, 'config', key, value)
        (self.tree / 'base.txt').write_text('Synthetic base\n')
        git(self.tree, 'add', 'base.txt')
        git(self.tree, 'commit', '--quiet', '-m', 'base')
        clone = self.tmp / 'independent'
        git(self.tree, 'clone', '--quiet', '--no-local', '--branch', 'main', str(self.tree), str(clone))
        for key, value in [('user.name', 'Synthetic'), ('user.email', 'synthetic@example.invalid')]:
            git(clone, 'config', key, value)
        path = clone / 'reports/synthetic/family-batches/original.json'
        path.parent.mkdir(parents=True)
        path.write_text('{"synthetic": true}\n')
        git(clone, 'add', 'reports/synthetic/family-batches/original.json')
        git(clone, 'commit', '--quiet', '-m', 'private synthetic metadata')
        revision = git(clone, 'rev-parse', 'HEAD')
        self.assertNotEqual(subprocess.run(['git', '-C', str(self.tree), 'cat-file', '-e', revision],
                                           capture_output=True).returncode, 0)
        lane.merge_metadata(self.tree, clone, revision)
        self.assertEqual(git(self.tree, 'rev-parse', 'HEAD'), revision)
        self.assertEqual(git(clone, 'rev-parse', 'HEAD'), revision)
        self.assertEqual((self.tree / path.relative_to(clone)).read_bytes(), path.read_bytes())

    def test_zero_member_pushed_receipt_can_finish_without_an_event_count(self):
        fdir = self.tmp / 'flow'
        receipt = dict(id='synthetic', root=str(self.tree), branch='main', tree=str(self.tree),
                       state='running', items=[], accepted=[], integrated=dict(commit='a'*40, ci='green'))
        lane.save_run(fdir, receipt)
        with patch.object(flow, 'git', return_value=''), patch.object(flow, 'log_event') as events:
            result = lane.finish_run(self.tree, fdir, receipt, sys.executable, 0)
        self.assertEqual(result['state'], 'done')
        self.assertEqual(result['integrated']['accepted'], 0)
        self.assertEqual(events.call_args_list[0].kwargs['accepted'], 0)
