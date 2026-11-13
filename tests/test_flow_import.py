"""State import against real synthetic comparator evidence and process locking."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'tools'), str(Path(__file__).resolve().parent)]
import flow
import flow_import
from flow_state import atomic_write, state_lock
import test_family_review as family_fixture


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = family_fixture.FamilyReviewTests('test_acceptance_preserves_comparator_and_names_family_review')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.addCleanup(self.fixture.tearDown)
        self.root = self.fixture.root
        self.source_root = self.root / '.local/source-tree'
        self.fixture.git('worktree', 'add', '--quiet', '--detach', str(self.source_root), 'HEAD')
        self.addCleanup(lambda: self.fixture.git('worktree', 'remove', '--force', str(self.source_root)))
        self.source = self.source_root / '.local/flow'
        self.dest = self.root / '.local/flow'
        self.reviews = self.source_root / '.local/reviews'
        shutil.copytree(self.root / '.local/reviews', self.reviews)
        initial = flow.load_group(self.dest, 'initial')
        second = flow.load_group(self.dest, 'initial-s')
        for group, name, pair in ((initial, 'g001', 'g001-s'), (second, 'g001-s', 'g001')):
            old_task = group['task_id']
            group.update(name=name, pair=pair, task_id='review-flow-' + name, integrated=None,
                         source_revision=self.fixture.git('rev-parse', 'HEAD'), dispatched=None)
            text = (self.reviews / (old_task + '.md')).read_text().replace('# Review ' + old_task, '# Review ' + group['task_id'])
            (self.reviews / (group['task_id'] + '.md')).write_text(text)
            if group['kind'] == 'review':
                compare = self.source_root / '.local/flow/rerun/g001/compare.txt'
                compare.parent.mkdir(parents=True)
                compare.write_text(''.join(r + ' AGREE\n' for r in group['sampled']))
                selection = {self.fixture.records[self.fixture.first[0]]['source']['compiled']: group['sampled']}
                (compare.parent / 'sample.json').write_text(json.dumps({'reviewed': selection, 'label_only': {}}))
                group['rerun']['file'] = '.local/flow/rerun/g001/compare.txt'
            else:
                group['rerun'] = None
            flow.save_group(self.source, group)
        (self.source / 'events.jsonl').write_text('{"event":"session-start","profile":"cheap"}\n')

    def run_import(self):
        with state_lock(self.dest):
            return flow_import.import_state(self.root, self.dest, self.source, self.reviews)

    def test_happy_path_collision_and_bytes_preserved(self):
        flow.save_group(self.dest, dict(name='g001', task_id='other-task', profile='cheap'))
        before = (self.dest / 'groups/g001.json').read_bytes()
        receipt = self.run_import()
        self.assertEqual(receipt['groups'], {'g001': 'g002', 'g001-s': 'g002-s'})
        self.assertEqual(before, (self.dest / 'groups/g001.json').read_bytes())
        g = flow.load_group(self.dest, 'g002')
        self.assertEqual(g['pair'], 'g002-s')
        self.assertEqual(g['task_id'], 'review-flow-g001')
        saved = flow.review_path(self.root, g)
        self.assertEqual(saved.name, 'review-flow-g002.md')
        self.assertEqual(saved.read_bytes(), (self.reviews / 'review-flow-g001.md').read_bytes())
        self.assertEqual(flow.read_review(self.root, g, self.fixture.data['functions'])[0], 'ok')
        self.assertTrue(flow.sampling_gate(self.root, self.dest, g, self.fixture.data)[0])
        self.assertEqual((self.dest / 'rerun/g002/sample.json').read_bytes(), (self.source / 'rerun/g001/sample.json').read_bytes())
        self.assertEqual(self.fixture.family['review']['review_sha256'],
                         hashlib.sha256((self.root / self.fixture.family_review_path).read_bytes()).hexdigest())

    def test_idempotent_even_after_normal_group_progress(self):
        receipt = self.run_import()
        group = flow.load_group(self.dest, receipt['groups']['g001'])
        group['integrated'] = {'commit': 'synthetic-progress'}
        flow.save_group(self.dest, group)
        self.assertEqual(receipt, self.run_import())
        self.assertEqual(flow.load_group(self.dest, group['name'])['integrated'], group['integrated'])

    def test_unit_digest_mismatch_refuses_before_any_write(self):
        record = next(iter(self.fixture.records.values()))
        source_file = self.source_root / record['source']['compiled']
        source_file.write_text(source_file.read_text() + '\n// changed\n')
        before = {p.name: p.read_bytes() for p in (self.dest / 'groups').glob('*')}
        with self.assertRaisesRegex(ValueError, 'digest|revision'):
            self.run_import()
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.dest / 'groups').glob('*')})
        self.assertFalse((self.dest / 'imports').exists())

    def test_template_digest_mismatch(self):
        (self.source_root / 'tools/synthetic_template.py').write_text('changed\n')
        with self.assertRaisesRegex(ValueError, 'template or extraction digest mismatch'):
            self.run_import()

    def test_manifest_digest_mismatch(self):
        path = self.source_root / self.fixture.family_path
        family = json.loads(path.read_text())
        family['first_members'][self.fixture.first[0]] = 'a' * 64
        path.write_text(json.dumps(family))
        with self.assertRaisesRegex(ValueError, 'member digest mismatch|spec digest mismatch'):
            self.run_import()

    def test_different_existing_review_is_not_overwritten(self):
        (self.root / '.local/reviews/review-flow-g001.md').write_text('different existing review')
        with self.assertRaisesRegex(ValueError, 'overwrite different'):
            self.run_import()
        self.assertEqual((self.root / '.local/reviews/review-flow-g001.md').read_text(), 'different existing review')

    def test_changed_source_after_import_refused(self):
        self.run_import()
        (self.source / 'events.jsonl').write_text('{"event":"changed"}\n')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            self.run_import()

    def test_interrupted_import_reuses_allocation(self):
        real = flow_import.atomic_write
        def fail(path, blob):
            if Path(path).parent.name == 'groups':
                raise OSError('interrupted')
            return real(path, blob)
        with patch('flow_import.atomic_write', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'interrupted'):
                self.run_import()
        receipt = self.run_import()
        self.assertEqual(receipt['groups']['g001'], 'g001')
        self.assertTrue(receipt['complete'])

    def test_unsent_briefs_are_shared_and_source_files_are_untouched(self):
        for file in self.reviews.glob('review-flow-*.md'):
            file.unlink()
        g = flow.load_group(self.source, 'g001')
        g['rerun'] = None
        flow.save_group(self.source, g)
        source_brief = self.source_root / '.local/briefs/review-flow-g001.md'
        source_brief.parent.mkdir(parents=True, exist_ok=True)
        source_brief.write_text('existing source brief')
        receipt = self.run_import()
        imported = flow.load_group(self.dest, receipt['groups']['g001'])
        self.assertTrue(Path(imported['brief']).is_file())
        self.assertTrue(Path(imported['brief']).is_relative_to((self.root / '.local/briefs').resolve()))
        self.assertEqual(source_brief.read_text(), 'existing source brief')
        self.assertTrue((self.dest / 'rerun/g001/sample.json').is_file())

    def test_attached_family_keeps_combined_instructions(self):
        g = flow.load_group(self.source, 'g001')
        (self.reviews / (g['task_id'] + '.md')).unlink()
        g['family_review_path'] = self.fixture.family_path
        flow.save_group(self.source, g)
        receipt = self.run_import()
        imported = flow.load_group(self.dest, receipt['groups']['g001'])
        self.assertIn('ordinary full-review blocks', Path(imported['brief']).read_text())
        self.assertTrue(Path(imported['member_brief']).is_file())

    def test_consecutive_ids_sampling_and_retry_names_remap_once(self):
        for name in ('g001', 'g001-s'):
            g = flow.load_group(self.source, name)
            new = name.replace('g001', 'g002')
            task = 'review-flow-' + new + '-r2'
            text = (self.reviews / (g['task_id'] + '.md')).read_text()
            text = text.replace('# Review ' + g['task_id'], '# Review ' + task)
            (self.reviews / (task + '.md')).write_text(text)
            g.update(name=new, pair=g['pair'].replace('g001', 'g002'), task_id=task)
            flow.save_group(self.source, g)
        flow.save_group(self.dest, dict(name='g001', task_id='unrelated', profile='cheap'))
        receipt = self.run_import()
        self.assertEqual(receipt['review_files']['review-flow-g001.md'], 'review-flow-g002.md')
        self.assertEqual(receipt['review_files']['review-flow-g002-r2.md'], 'review-flow-g003-r2.md')
        self.assertEqual(receipt['review_files']['review-flow-g002-s-r2.md'], 'review-flow-g003-s-r2.md')

    def test_conflicting_shared_brief_refused_without_overwrite(self):
        brief = self.root / '.local/briefs/import-g001.md'
        brief.parent.mkdir(parents=True, exist_ok=True)
        brief.write_text('existing different brief')
        with self.assertRaisesRegex(ValueError, 'overwrite different'):
            self.run_import()
        self.assertEqual(brief.read_text(), 'existing different brief')
        self.assertFalse((self.dest / 'imports').exists())

    def test_interruption_after_group_write_blocks_other_consumers(self):
        real = flow_import.atomic_write
        written = []
        def fail(path, blob):
            if Path(path).parent.name == 'groups':
                if written:
                    raise OSError('interrupted after group')
                written.append(path)
            return real(path, blob)
        with patch('flow_import.atomic_write', side_effect=fail):
            with self.assertRaises(OSError):
                self.run_import()
        with self.assertRaisesRegex(ValueError, 'incomplete state import'):
            flow.groups(self.dest)
        import accept_function
        with self.assertRaisesRegex(ValueError, 'incomplete state import'):
            accept_function.review_profile(self.root, 'review-flow-g001', None)
        self.assertEqual(accept_function.main(['--root', str(self.root), '--label-only']), 1)
        self.assertEqual(flow.main(['--root', str(self.root), '--offline', 'status']), 1)
        self.assertTrue(self.run_import()['complete'])

    def test_shared_destination_required(self):
        with self.assertRaisesRegex(ValueError, 'destination must be shared'):
            flow_import.import_state(self.root, self.root / '.local/other', self.source, self.reviews)


class LockTests(unittest.TestCase):
    def test_lock_serializes_read_modify_write_and_process_exit_releases_it(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            counter = base / 'count'
            counter.write_text('0')
            code = ('import sys,time;from pathlib import Path;from flow_state import state_lock,atomic_write;'
                    'p=Path(sys.argv[1]);\n'
                    'for _ in range(15):\n'
                    ' with state_lock(p):\n'
                    '  n=int((p/"count").read_text());time.sleep(.002);atomic_write(p/"count",str(n+1).encode())\n')
            env = dict(os.environ, PYTHONPATH=str(Path(flow.__file__).parent))
            children = [subprocess.Popen([sys.executable, '-c', code, str(base)], env=env) for _ in range(3)]
            for child in children:
                self.assertEqual(child.wait(timeout=15), 0)
            self.assertEqual(counter.read_text(), '45')
            crash = subprocess.run([sys.executable, '-c',
                'import os,sys;from flow_state import state_lock\nwith state_lock(sys.argv[1]):os._exit(7)', str(base)], env=env)
            self.assertEqual(crash.returncode, 7)
            with state_lock(base):
                self.assertTrue((base / '.state.lock').is_file())

    def test_integrate_child_can_share_parent_lock(self):
        import tempfile
        from flow_state import inherited_lock
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            with state_lock(base):
                fd = inherited_lock()
                env = dict(os.environ, PYTHONPATH=str(Path(flow.__file__).parent), SKYRIM_FLOW_LOCK_FD=str(fd))
                child = subprocess.run([sys.executable, '-c',
                    'import sys;from flow_state import state_lock\nwith state_lock(sys.argv[1]):print("locked")', str(base)],
                    pass_fds=(fd,), env=env, timeout=5, capture_output=True, text=True)
                self.assertEqual(child.returncode, 0, child.stderr)
                self.assertEqual(child.stdout.strip(), 'locked')
                self.assertEqual(inherited_lock(), fd)

    def test_atomic_write_failure_keeps_original(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'state.json'
            path.write_bytes(b'original')
            with patch('flow_state.os.replace', side_effect=OSError('unavailable')):
                with self.assertRaises(OSError):
                    atomic_write(path, b'new')
            self.assertEqual(path.read_bytes(), b'original')
            self.assertEqual(list(path.parent.iterdir()), [path])
