"""Public CI self-test: synthetic objects only, no compiler or game input."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import ci_hash_check as ci
import compare
import synthetic_pecoff as fx


class PublicHashTest(unittest.TestCase):
    def test_hash_is_exactly_the_public_comparator_hash(self):
        inputs = fx.inputs()
        report = compare.compare(**inputs)
        ref = dict(symbol=fx.FUNCTION, size=len(fx.CODE))
        self.assertEqual(ci.candidate_hash(inputs['object_bytes'], ref),
                         report['candidate']['code_section_sha256'])
        # Object timestamps do not enter this hash; function bytes do.
        stamp = bytearray(inputs['object_bytes'])
        struct.pack_into('<I', stamp, 4, 123456)
        self.assertEqual(ci.candidate_hash(stamp, ref), ci.candidate_hash(inputs['object_bytes'], ref))
        self.assertNotEqual(ci.candidate_hash(fx.coff_object(code=fx.CODE[:-1] + b'\x90'), ref),
                            ci.candidate_hash(inputs['object_bytes'], ref))
        with self.assertRaisesRegex(ValueError, 'size'):
            ci.candidate_hash(inputs['object_bytes'], dict(ref, size=len(fx.CODE) + 1))

    def test_all_three_current_public_references_bind_and_use_distinct_units(self):
        refs = [ci.reference(ROOT, rva) for rva in ci.SELF_TEST_RVAS]
        self.assertEqual(len({ref['unit'] for ref in refs}), 3)
        self.assertIn(ci.contrib.SELF_TEST_RVA, ci.SELF_TEST_RVAS)

    def test_version_banner_is_insufficient_when_one_binary_differs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pins = root / 'tools/verifier/pinned.sha256'
            pins.parent.mkdir(parents=True)
            bindir = root / 'bin'
            bindir.mkdir()
            names = ('cl.exe', 'c1xx.dll', 'c2.dll', 'link.exe')
            for name in names:
                (bindir / name).write_bytes(name.encode())
            pins.write_text(''.join(f'{hashlib.sha256(n.encode()).hexdigest()}  {n}\n' for n in names))
            proc = ci.subprocess.CompletedProcess([], 2, '', 'Compiler Version 19.16.27054 for x64')
            with patch.object(ci.subprocess, 'run', return_value=proc):
                self.assertEqual(ci.probe(root, bindir)['toolset'], 'MATCH')
                (bindir / 'c2.dll').write_bytes(b'different')
                self.assertEqual(ci.probe(root, bindir)['toolset'], 'MISMATCH')

    def test_no_diagnostics_or_local_paths_in_failure_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'report.json'
            with patch.object(ci, 'probe', side_effect=OSError('private diagnostic')), patch('builtins.print'):
                self.assertEqual(ci.main(['probe', '--bin', tmp, '--out', str(out)]), 1)
            report = out.read_text()
            self.assertNotIn('private diagnostic', report)
            self.assertNotIn(tmp, report)
            self.assertEqual(json.loads(report)['acceptance'], 'not-evaluated')


if __name__ == '__main__':
    unittest.main()
