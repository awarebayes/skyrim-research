"""Pure helpers behind the Drafter aids in tools/ghidra/export_pack.py, on original synthetic text."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'ghidra'))
import export_pack as ep  # noqa: E402

LISTING = """function X at rva 0x1000
  +0x000  PUSH RBX
  +0x002  SUB RSP,0x20
  +0x006  TEST dword ptr [RDX + 0x28],0x3ff
  +0x00e  MOV RAX,qword ptr [RCX]
  +0x011  MOV qword ptr [RSP + 0x30],RBX
  +0x016  MOV EAX,dword ptr [0x14219e55c]   [READ 0x219e55c DAT]
"""


class AidTests(unittest.TestCase):
    def test_observed_offsets_skip_stack_and_absolute(self):
        self.assertEqual(ep.observed_offsets(LISTING), [(0x28, 'RDX', 'dword', 6), (0, 'RCX', 'qword', 0xe)])

    def test_trim_keeps_head_virtuals_method_and_touched_members(self):
        body = ['class Widget :', '\tpublic Base  // 00', '{', 'public:']
        body += [f'\tstd::uint32_t filler{i};  // {0x100 + 4 * i:03X}' for i in range(300)]
        body += ['\tvirtual void Tick();  // 05', '\tbool Get(int a_x);', '\tstd::uint32_t flags;  // 4B8', '};']
        text, trimmed = ep.trim_excerpt('\n'.join(body), {0x4b8, 0x104}, ['Get'], full_limit=100)
        self.assertTrue(trimmed)
        for wanted in ('class Widget :', 'virtual void Tick', 'bool Get(int a_x)', 'flags;  // 4B8', 'filler1;'):
            self.assertIn(wanted, text)
        self.assertNotIn('filler200;', text)
        self.assertIn('lines omitted', text)

    def test_convention_notes(self):
        notes = '\n'.join(ep.convention_notes(
            'static BSPointerHandle<T> GetHandle(T* a_ptr);', 'BSPointerHandleManagerInterface'))
        self.assertIn('result address in RCX', notes)
        self.assertNotIn('`this`', notes)
        notes = '\n'.join(ep.convention_notes('void SetGlobalTimeMultiplier(float a_mult, bool a_arg2);', 'BSTimer'))
        self.assertIn('`this` arrives in RCX', notes)
        self.assertIn('`float a_mult` arrives in XMM1', notes)
        self.assertIn('`bool a_arg2` arrives in R8', notes)

    def test_fp_equality_without_parity(self):
        fast = '  +0x000  UCOMISS XMM1,XMM2\n  +0x003  JZ 0x10\n  +0x005  RET\n'
        precise = '  +0x000  UCOMISS XMM1,XMM2\n  +0x003  JP 0x10\n  +0x005  JZ 0x12\n'
        ordered = '  +0x000  COMISS XMM1,XMM2\n  +0x003  JBE 0x10\n'
        reset = '  +0x000  UCOMISS XMM1,XMM2\n  +0x003  JA 0x8\n  +0x005  TEST EAX,EAX\n  +0x007  JZ 0x10\n'
        self.assertEqual(ep.fp_equality_without_parity(fast), [0])
        self.assertEqual(ep.fp_equality_without_parity(precise), [])
        self.assertEqual(ep.fp_equality_without_parity(ordered), [])
        self.assertEqual(ep.fp_equality_without_parity(reset), [])

    def test_fp_sensitive_ignores_moves_and_zeroing(self):
        self.assertFalse(ep.fp_sensitive('  +0x000  MOVSS XMM0,dword ptr [RCX + 0x8]\n  +0x005  XORPS XMM2,XMM2\n'))
        self.assertTrue(ep.fp_sensitive('  +0x000  MULSS XMM1,XMM0\n'))
        self.assertTrue(ep.fp_sensitive('  +0x000  CVTSI2SS XMM0,EAX\n'))

    def test_pick_functions_mixes_large_and_small_within_budget(self):
        fns = [{'rva': i, 'size': s} for i, s in enumerate([10, 20, 30, 40, 150, 120, 400, 101])]
        picked = [f['size'] for f in ep.pick_functions(fns, 5, 2, 100, 1200)]
        self.assertEqual(picked, [10, 20, 30, 101, 120])
        self.assertEqual([f['size'] for f in ep.pick_functions(fns, 5, 2, 100, 200)], [10, 20, 30, 101])

    def test_class_kind(self):
        self.assertEqual(ep.class_kind('TESObjectREFR', 'forms', False, ['TESObjectREFR', 'TESForm']), 'form')
        self.assertEqual(ep.class_kind('TESFile', 'forms', False, []), 'other')
        self.assertEqual(ep.class_kind('BSDirectInputManager', 'bsengine', True), 'manager-singleton')
        self.assertEqual(ep.class_kind('ExtraCount', None, False), 'extra-data')
        self.assertEqual(ep.class_kind('PlayerCharacter', 'actors', True), 'actor')

    def test_member_offsets_own_body_only(self):
        body = 'class W\n{\npublic:\n\tvirtual void F();  // 01\n\tint a;  // 08\n\tstruct N\n\t{\n\t\tint b;  // 10\n' \
               '\t};\n\tfloat c;  // 0C\n};'
        self.assertEqual(ep.member_offsets(body), {8: 'int a;', 0xc: 'float c;'})


if __name__ == '__main__':
    unittest.main()
