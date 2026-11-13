"""Negative cases that protect publication boundaries and prevent invented match claims."""
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check import ROOT, check_git, index_blob, inspect_payload, validate
from fingerprint import fingerprint
from build_site import render


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'data/progress.json').read_text())
        self.target = json.loads((ROOT / 'builds/target.json').read_text())

    def pin(self):
        self.target.update(status='pinned', build_id='synthetic-test', store='synthetic', version='synthetic',
                           architecture='x86-64', image_sha256='a' * 64)
        self.data['target_build_id'] = 'synthetic-test'
        self.data['functions'] = [dict(id='test', build_id='synthetic-test', rva=4096, size=8, status='mapped',
                                      name='Synthetic', owner='test', name_origin='GUESS', evidence='findings/TEMPLATE.md')]

    def test_bootstrap_is_valid_without_claiming_scope(self):
        validate(self.data, self.target)
        page = render(self.data, 'synthetic-revision')
        self.assertIn('Not measured', page)
        self.assertNotIn('100%', page)

    def test_page_states_gate_from_data(self):
        # The live inventory may already hold accepted functions; the empty-state wording needs none.
        for function in self.data['functions']:
            function['status'] = 'mapped'
        page = render(self.data, 'synthetic-revision')
        self.assertNotIn('not implemented', page)
        self.assertNotIn('disabled during bootstrap', page)
        self.assertIn('Matching gate implemented; no function accepted yet', page)
        self.assertIn('Scope remains unknown; no completion percentage', page)
        self.pin()
        self.data['functions'][0]['status'] = 'matched'
        page = render(self.data, 'synthetic-revision')
        self.assertIn('<strong>1</strong><small>Each: comparator pass on 2+ hosts and a Reviewer approve', page)
        self.assertNotIn('%', page.split('Scope note')[0].split('metrics')[-1])

    def test_phase_blurb_follows_the_data(self):
        page = render(self.data, 'synthetic-revision')
        self.assertNotIn('Target selection and the matching toolchain come next', page)
        self.pin()
        self.data['work_items'] = [dict(id='a', title='Planned thing', status='planned', owner='o', acceptance='x',
                                        issue_url=None),
                                   dict(id='b', title='Active thing', status='active', owner='o', acceptance='x',
                                        issue_url=None)]
        page = render(self.data, 'synthetic-revision')
        self.assertIn('Target synthetic-test is pinned. 1 function inventoried, 0 accepted byte matches. '
                      '2 open work items; in progress: Active thing.', page)
        for item in self.data['work_items']:
            item['status'] = 'done'
        self.assertIn('All 2 work items done', render(self.data, 'synthetic-revision'))
        self.data['target_build_id'] = None
        self.assertIn('No target build is pinned yet', render(self.data, 'synthetic-revision'))

    def test_fake_scope_rejected(self):
        self.data['scope'].update(functions=100, bytes=1000)
        with self.assertRaisesRegex(ValueError, 'inventory'):
            validate(self.data, self.target)

    def test_matched_needs_a_match_record_even_for_pinned_target(self):
        # tests/test_match_gate.py covers the record itself; a bare status flip must still fail.
        self.pin()
        self.data['functions'][0]['status'] = 'matched'
        with self.assertRaisesRegex(ValueError, 'missing report path'):
            validate(self.data, self.target)

    def test_cross_build_function_rejected(self):
        self.pin()
        self.data['functions'][0]['build_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'another build'):
            validate(self.data, self.target)

    def test_aliases_cannot_double_count(self):
        self.pin()
        fn = copy.deepcopy(self.data['functions'][0])
        fn['id'] = 'different-id'
        self.data['functions'].append(fn)
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            validate(self.data, self.target)

    def test_private_evidence_cannot_be_published(self):
        self.pin()
        self.data['functions'][0]['evidence'] = '.local/notes.txt'
        with self.assertRaisesRegex(ValueError, 'public findings'):
            validate(self.data, self.target)

    def test_site_escapes_contributor_text(self):
        self.data['work_items'][0]['title'] = '<script>unsafe</script>'
        page = render(self.data, 'test')
        self.assertNotIn('<script>unsafe', page)
        self.assertIn('&lt;script&gt;unsafe', page)

    def test_publication_guard_rejects_artifacts(self):
        for name, payload in [('image.EXE', b'text'), ('notes.txt', b'MZ\0payload'),
                              ('.local/input.txt', b'private'), ('archive.txt', b'\xff\xfe'),
                              ('large.txt', b'x' * (1024 * 1024 + 1)),
                              ('pointer.txt', b'version https://git-lfs.github.com/spec/v1\n')]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                inspect_payload(name, payload)

    def test_large_inventory_size_exceptions_keep_other_guards(self):
        allowed = ('data/progress.json', 'reconstruction/INDEX.md',
                   'reports/build-1/symbol-map.json', 'reports/build-1/symbol-map.history.json',
                   'reports/build-1/families/family.json')
        large_text = b' ' * (1024 * 1024 + 1)
        for name in allowed:
            with self.subTest(name=name):
                valid = (b'{"schema":1,"build_id":"build-1","symbols":{}}' + large_text
                         if name.endswith('/symbol-map.json') else b'{}' + large_text
                         if name.endswith('.json') else large_text)
                inspect_payload(name, valid)
                if name.endswith('.json'):
                    with self.assertRaises(ValueError):
                        inspect_payload(name, b'not json' + large_text)
                with self.assertRaisesRegex(ValueError, 'exceeds 32 MiB'):
                    inspect_payload(name, b' ' * (32 * 1024 * 1024 + 1))
                with self.assertRaisesRegex(ValueError, 'binary content'):
                    inspect_payload(name, large_text + b'\0')
                with self.assertRaisesRegex(ValueError, 'LFS prohibited'):
                    inspect_payload(name, b'version https://git-lfs.github.com/spec/v1' + large_text)
        for name in ('data/other.json', 'reports/build-1/families/nested/family.json',
                     'reports/build-1/symbol-map.extra.json', 'reports/BUILD/symbol-map.json'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'exceeds 1 MiB'):
                inspect_payload(name, large_text)

    def test_staged_binary_detected_after_worktree_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            path = root / 'notes.txt'
            path.write_bytes(b'private\0binary')
            subprocess.run(['git', 'add', 'notes.txt'], cwd=root, check=True)
            path.write_text('innocent replacement')
            with self.assertRaisesRegex(ValueError, 'binary content'):
                check_git(root, staged=True)
            with self.assertRaisesRegex(ValueError, 'binary content'):
                check_git(root, staged=False)

    def test_batch_blob_framing_refuses_wrong_missing_or_truncated_objects(self):
        sha = 'a' * 40
        for response in (b'', f'{sha} missing\n'.encode(), b'b' * 40 + b' blob 1\nx\n',
                         f'{sha} tree 1\nx\n'.encode(), f'{sha} blob -1\n'.encode(),
                         f'{sha} blob 3\nx\n'.encode(), f'{sha} blob 1\nx!'.encode(),
                         f'{sha} blob {32 * 1024 * 1024 + 1}\n'.encode()):
            with self.subTest(response=response), self.assertRaises(ValueError):
                index_blob(SimpleNamespace(stdin=io.BytesIO(), stdout=io.BytesIO(response)), sha, 'notes.txt')
        objects = SimpleNamespace(stdin=io.BytesIO(), stdout=io.BytesIO(
            f'{sha} blob 3\n'.encode() + b'a\nb\n' + f'{sha} blob 0\n\n'.encode()))
        self.assertEqual(index_blob(objects, sha, 'first.txt'), b'a\nb')
        self.assertEqual(index_blob(objects, sha, 'empty.txt'), b'')
        self.assertEqual(objects.stdin.getvalue(), (sha + '\n' + sha + '\n').encode())

    def test_one_git_batch_checks_every_index_blob_and_working_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            for name in ('notes.txt', 'same text.txt', 'unicode-λ.txt', 'line\nbreak.txt'):
                (root / name).write_text('safe text\n')
            subprocess.run(['git', 'add', '--all'], cwd=root, check=True)
            real_popen = subprocess.Popen
            with patch('check.subprocess.Popen', wraps=real_popen) as calls:
                self.assertEqual(check_git(root), 4)
                self.assertEqual(sum(c.args[0] == ['git', 'cat-file', '--batch'] for c in calls.call_args_list), 1)
            path = root / 'notes.txt'
            path.write_bytes(b'working\0binary')
            self.assertEqual(check_git(root, staged=True), 4)
            with self.assertRaisesRegex(ValueError, 'binary content'):
                check_git(root)
            path.unlink()
            self.assertEqual(check_git(root, staged=True), 4)
            with self.assertRaisesRegex(ValueError, 'missing file/symlink'):
                check_git(root)
            path.symlink_to('same text.txt')
            with self.assertRaisesRegex(ValueError, 'missing file/symlink'):
                check_git(root)

    def test_batch_git_still_refuses_unresolved_index_stages(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            sha = subprocess.check_output(['git', 'hash-object', '-w', '--stdin'], cwd=root,
                                          input=b'safe text\n').decode().strip()
            subprocess.run(['git', 'update-index', '--index-info'], cwd=root, check=True,
                           input=f'100644 {sha} 1\tconflict.txt\n'.encode())
            with self.assertRaisesRegex(ValueError, 'unresolved conflict'):
                check_git(root, staged=True)

    def test_fingerprint_is_read_only_and_checks_architecture(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'synthetic.exe'
            payload = bytearray(70)
            payload[:2] = b'MZ'
            struct.pack_into('<I', payload, 60, 64)
            payload[64:68] = b'PE\0\0'
            struct.pack_into('<H', payload, 68, 0x8664)
            path.write_bytes(payload)
            self.assertEqual(fingerprint(path), hashlib.sha256(payload).hexdigest())
            self.assertEqual(path.read_bytes(), payload)
            struct.pack_into('<H', payload, 68, 0x14c)
            path.write_bytes(payload)
            with self.assertRaisesRegex(ValueError, 'x86-64'):
                fingerprint(path)


if __name__ == '__main__':
    unittest.main()
