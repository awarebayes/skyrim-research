"""Negative cases that protect publication boundaries and prevent invented match claims."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check import ROOT, check_git, inspect_payload, validate
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
