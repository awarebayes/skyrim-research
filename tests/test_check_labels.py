"""tools/check_labels.py on original synthetic units and a synthetic community checkout."""
from importlib.machinery import SourceFileLoader
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
import check_labels  # noqa: E402

COMMUNITY_HEADER = '''#pragma once
namespace EX
{
    enum class FormType : std::uint8_t
    {
        None = 0,  // 00 NONE
        NPC = 0x2B,
        ActorCharacter = 0x3E,  // 3E Actor / Character
    };

    class Base
    {
    public:
        int baseValue;  // 00
    };

    class Widget : public Base
    {
    public:
        struct State1
        {
            std::uint32_t lifeState: 4;
            std::uint32_t meleeAttackState: 4;
        };

        enum class Sound
        {
            kCharge = 1,
            kReadyLoop,
            kCastLoop = 4,
        };

        bool IsReady() const;
        State1 actorState1;   // 08
        float  castingTimer;  // 0C
    };
}
'''
OFFSETS = 'namespace EX { constexpr int RTTI_Gadgets__Filter(1); }\n'


def git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), *args], capture_output=True, text=True, check=True).stdout.strip()


class LabelCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'repo'
        lib = Path(self.tmp.name) / 'lib'
        (lib / 'include/EX').mkdir(parents=True)
        (lib / 'include/EX/Widget.h').write_text(COMMUNITY_HEADER)
        (lib / 'include/EX/Offsets.h').write_text(OFFSETS)
        git(lib, 'init', '-q')
        git(lib, 'add', '.')
        git(lib, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-qm', 'fixture')
        self.rev = git(lib, 'rev-parse', 'HEAD')[:7]
        self.checkouts = {'Example/Lib': str(lib)}
        (self.root / 'reconstruction/area').mkdir(parents=True)
        (self.root / 'findings').mkdir()
        (self.root / 'findings/sel.md').write_text('selected `0x1000` and `0x2000`\n')

    def tearDown(self):
        self.tmp.cleanup()

    def label(self, rev=None):
        return f'COMMUNITY(Example/Lib@{rev or self.rev}, MIT)'

    def run_on(self, header, cpp=None, checkouts=None):
        h = self.root / 'reconstruction/area/Widget.h'
        h.write_text('// Labels: v2\n' + header)
        files = [h]
        if cpp is not None:
            c = self.root / 'reconstruction/area/Widget.cpp'
            c.write_text('// Labels: v2\n' + cpp)
            files.append(c)
        return check_labels.check(files, checkouts or self.checkouts, root=self.root)

    def test_community_names_that_exist_pass(self):
        header = f'''// Widget Widget::actorState1 Widget::State1::lifeState ::meleeAttackState: {self.label()}
// Widget::IsReady Widget::baseValue: {self.label()}; baseValue is a member of the base class
// FormType: {self.label()}
enum class FormType : std::uint8_t {{
    NPC            = 0x2B,
    ActorCharacter = 0x3E,
}};
'''
        self.assertEqual(self.run_on(header), [])

    def test_member_name_the_checkout_does_not_declare(self):
        findings = self.run_on(f'// Widget::flags1: {self.label()}\n')
        self.assertEqual(len(findings), 1)
        self.assertIn('Widget::flags1 is labelled COMMUNITY(Example/Lib)', findings[0])

    def test_unqualified_name_checked_in_the_class_around_it(self):
        header = f'''class Widget {{
public:
    // attackState: {self.label()}
    std::uint32_t attackState;
}};
'''
        findings = self.run_on(header)
        self.assertEqual(len(findings), 1)
        self.assertIn('declares no such name in Widget', findings[0])

    def test_enumerator_spelling_checked_when_the_enum_is_labelled(self):
        header = f'''// FormType: {self.label()}
enum class FormType : std::uint8_t {{
    kNone     = 0,
    Character = 0x3E,
}};
'''
        findings = self.run_on(header)
        self.assertEqual(sorted(f.split(': ', 1)[1] for f in findings),
                         ['FormType::Character is not an enumerator of Example/Lib FormType',
                          'FormType::kNone is not an enumerator of Example/Lib FormType'])

    def test_enumerator_value_checked_including_implicit_values(self):
        header = f'''// Sound::kReadyLoop Sound::kCastLoop: {self.label()}
enum class Sound {{
    kReadyLoop = 2,
    kCastLoop  = 3,
}};
'''
        findings = self.run_on(header)
        self.assertEqual(len(findings), 1)
        self.assertIn('Sound::kCastLoop = 3 here, but Example/Lib gives 4', findings[0])

    def test_guess_name_the_checkout_declares_in_that_class(self):
        findings = self.run_on('// Widget::castingTimer Widget::unk10: GUESS(low)\n')
        self.assertEqual(len(findings), 1)
        self.assertIn('Widget::castingTimer is labelled GUESS', findings[0])

    def test_guess_name_found_through_the_declaring_unit_class(self):
        header = '''// IsReady Unk_05: GUESS(high)
class Widget {
public:
    bool IsReady() const;
    void Unk_05();
};
'''
        findings = self.run_on(header)
        self.assertEqual(len(findings), 1)
        self.assertIn('IsReady is labelled GUESS but Example/Lib declares it in Widget', findings[0])

    def test_class_known_only_from_the_rtti_list(self):
        header = f'// Gadgets Gadgets::Filter: STANDIN EXE_RTTI {self.label()}\n'
        self.assertEqual(self.run_on(header), [])

    def test_checkout_at_another_revision(self):
        findings = self.run_on(f'// Widget: {self.label("0123abc")}\n')
        self.assertEqual(len(findings), 1)
        self.assertIn('the label pins 0123abc', findings[0])

    def test_missing_checkout_reported_once(self):
        header = f'// Widget: {self.label()}\n// Widget::IsReady: {self.label()}\n'
        findings = self.run_on(header, checkouts={'Example/Lib': str(Path(self.tmp.name) / 'absent')})
        self.assertEqual(len(findings), 1)
        self.assertIn('no local checkout of Example/Lib', findings[0])

    def test_evidence_must_mention_every_compared_rva(self):
        cpp = ('// RVA 0x1000, 12 bytes (A). RVA 0x3000, 8 bytes (B). The callee at RVA 0x9999 is named below.\n'
               '// Evidence: findings/sel.md.\n#include "Widget.h"\n')
        findings = self.run_on(f'// Widget: {self.label()}\n', cpp)
        self.assertEqual(len(findings), 1)
        self.assertIn('does not mention 0x3000', findings[0])

    def test_review_excerpts_quote_the_community_declaration(self):
        h = self.root / 'reconstruction/area/Widget.h'
        h.write_text(f'// Labels: v2\n// Widget::actorState1 Widget::baseValue: {self.label()}\n')
        lines = check_labels.community_excerpts([h], self.checkouts, root=self.root)
        self.assertEqual(len(lines), 2)
        self.assertIn('Widget::actorState1: Example/Lib include/EX/Widget.h:', lines[0])
        self.assertIn('State1 actorState1;', lines[0])
        self.assertIn('int baseValue;', lines[1])

    def test_files_without_v2_labels_are_skipped(self):
        h = self.root / 'reconstruction/area/Old.h'
        h.write_text(f'// Widget::flags1: {self.label()}\n')
        self.assertEqual(check_labels.check([h], self.checkouts, root=self.root), [])


class ConfirmNoteTests(unittest.TestCase):
    def setUp(self):
        loader = SourceFileLoader('confirm_script', str(TOOLS / 'verifier/confirm'))
        spec = importlib.util.spec_from_loader('confirm_script', loader)
        self.confirm = importlib.util.module_from_spec(spec)
        loader.exec_module(self.confirm)

    def test_note_names_uncommitted_tools_and_the_comparator_hash(self):
        note = self.confirm.source_note('b' * 40, ['tools/compare.py', 'reconstruction/a/B.cpp'], 'c' * 64)
        self.assertIn('uncommitted changes to tools/compare.py, reconstruction/a/B.cpp', note)
        self.assertIn('comparator source sha256 ' + 'c' * 64, note)

    def test_committed_note_still_binds_the_comparator_hash(self):
        note = self.confirm.source_note('b' * 40, [], 'c' * 64)
        self.assertIn('committed tree at base commit ' + 'b' * 40, note)
        self.assertIn('comparator source sha256 ' + 'c' * 64, note)

    def test_result_tools_include_the_comparator_and_verifier(self):
        for path in ('tools/compare.py', 'tools/pecoff.py', 'tools/verifier/verify_function.py',
                     'tools/verifier/confirm', 'tools/verifier/match_record.py'):
            self.assertIn(path, self.confirm.RESULT_TOOLS)


if __name__ == '__main__':
    unittest.main()
