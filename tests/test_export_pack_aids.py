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


if __name__ == '__main__':
    unittest.main()
