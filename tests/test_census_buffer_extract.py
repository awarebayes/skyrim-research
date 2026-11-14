"""Original synthetic operand fixtures, independent of any game input."""
from pathlib import Path
import struct
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import census_buffer_extract as extract


class BufferExtractionTests(unittest.TestCase):
    def image(self, code, rva=4096):
        return NS(image_base=0, read=lambda *args: (NS(flags=0x20000000), code),
                  section_for=lambda r: NS())

    def test_complete_operands_and_indirect_slot(self):
        # synthetic: add rax, 40; call [rip+disp32]; ret
        code = bytes.fromhex('48 83 c0 28 ff 15') + struct.pack('<i', 8192-4096-10) + b'\xc3'
        member = extract.extract(self.image(code), 4096, len(code))
        self.assertEqual(member['instructions'][0]['immediate']['unsigned'], 40)
        self.assertEqual(member['references'][0]['target_rva'], 8192)
        self.assertEqual(member['callback_slots'][0]['slot_kind'], 'rip')
        self.assertEqual(''.join(r['encoding'] for r in member['instructions']), code.hex())

    def test_references_are_per_member_not_transferred(self):
        rows = []
        for target in [8192, 12288]:
            code = b'\xe8' + struct.pack('<i', target-4101) + b'\xc3'
            rows.append(extract.extract(self.image(code), 4096, len(code)))
        self.assertEqual([r['references'][0]['target_rva'] for r in rows], [8192, 12288])
        self.assertEqual(extract.columns(rows)['0:references']['distinct'], 2)

    def test_object_callback_displacement(self):
        code = bytes.fromhex('ff 50 28 c3')
        row = extract.extract(self.image(code), 4096, len(code))['callback_slots'][0]
        self.assertEqual(row['slot_kind'], 'register-or-object')
        self.assertEqual(row['displacement']['signed'], 40)

    def test_local_branch_boundary(self):
        code = bytes.fromhex('eb 01 48 89 c0 c3')
        with self.assertRaisesRegex(ValueError, 'instruction boundary'):
            extract.extract(self.image(code), 4096, len(code))

    def test_truncated_and_external_short_branch_refused(self):
        for code in [b'\xe8', bytes.fromhex('eb 7f c3')]:
            with self.assertRaises(ValueError):
                extract.extract(self.image(code), 4096, len(code))

    def test_wrong_reference_decoder_is_refused(self):
        code = b'\xe8' + struct.pack('<i', 8192-4101) + b'\xc3'
        original = extract.imagemodel.field_records
        def wrong(*args):
            fields, insns, flags, end = original(*args)
            fields[0] = (*fields[0][:-1], 9000)
            return fields, insns, flags, end
        with patch.object(extract.imagemodel, 'field_records', side_effect=wrong):
            with self.assertRaisesRegex(ValueError, 'target disagrees'):
                extract.extract(self.image(code), 4096, len(code))

    def test_roles_keep_inferences_separate_and_bind_opcode(self):
        code = bytes.fromhex('48 83 c0 28 c3')
        row = extract.extract(self.image(code), 4096, len(code))
        roles = dict(measured={'stride': dict(instruction=0, opcode=[0x83], field='immediate')},
                     inferred={'policy': dict(description='advance records', instructions=[0], confidence='low')})
        result = extract.annotate(row, roles)
        self.assertEqual(result['measured']['stride']['operand']['unsigned'], 40)
        self.assertEqual(result['inferred']['policy']['status'], 'inferred-unverified')
        roles['measured']['stride']['opcode'] = [0x90]
        with self.assertRaisesRegex(ValueError, 'opcode differs'):
            extract.annotate(row, roles)

    def test_missing_semantic_operand_or_evidence_refused(self):
        row = extract.extract(self.image(b'\xc3'), 4096, 1)
        for roles in [dict(measured={'stride': dict(instruction=0, opcode=[0xc3], field='immediate')}),
                      dict(inferred={'policy': dict(instructions=[1])})]:
            with self.assertRaises(ValueError):
                extract.annotate(row, roles)

    def test_output_cannot_escape_private_directory_through_symlink(self):
        import tempfile
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / '.local').mkdir()
            (root / '.local' / 'escape').symlink_to(root, target_is_directory=True)
            self.assertEqual(extract.private_output(root / '.local' / 'result.json'), (root / '.local/result.json').resolve())
            with self.assertRaises(ValueError):
                extract.private_output(root / '.local' / 'escape' / 'result.json')


if __name__ == '__main__':
    unittest.main()
