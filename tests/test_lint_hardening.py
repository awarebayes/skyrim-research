"""Licence, sibling-citation and label-parser hardening in tools/lint_reconstruction.py and
tools/check_labels.py. All headers, checkouts and clones here are synthetic.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_labels  # noqa: E402
from lint_reconstruction import lint_file  # noqa: E402

HEAD = '// Thing, build b. Source exposure: black-box. Names: GUESS.\n'
PIN = '91e1b6e8'
NG = 'CharmedBaryon/CommonLibSSE-NG@b93280e'
PO3 = 'powerof3/CommonLibSSE@654e55f'


def git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid',
                           '-c', 'commit.gpgsign=false', *args],
                          capture_output=True, text=True, check=True).stdout.strip()


class LintLicenceTests(unittest.TestCase):
    def lint(self, text, name='reconstruction/forms/Thing.h'):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / name).parent.mkdir(parents=True)
            (root / name).write_text(text)
            return lint_file(root, name, 'b')

    def body(self, label):
        return f'struct Thing {{\n    // Get: {label}\n    int Get();\n}};\n'

    def test_gpl_word_matched_in_any_case(self):
        for word in ('gpl-3.0', 'Gpl-3.0', 'lgpl-2.1', 'agpl-3.0'):
            with self.subTest(word=word):
                problems = self.lint(HEAD + self.body(f'COMMUNITY(someone/lib@1234567, {word})'))
                self.assertTrue(any('state the GPL licence' in p for p in problems), problems)
        # A header that states the licence in lower case satisfies the rule.
        stated = HEAD + '// This file is gpl-3.0 (someone names).\n'
        self.assertEqual(self.lint(stated + self.body('COMMUNITY(someone/lib@1234567, gpl-3.0)')), [])

    def test_known_repository_must_carry_its_licence(self):
        for label, expected in ((f'COMMUNITY({PO3}, MIT)', 'GPL-3.0'), (f'COMMUNITY({PO3}, gpl-3.0)', 'GPL-3.0'),
                                (f'COMMUNITY({NG}, GPL-3.0)', 'MIT'), (f'COMMUNITY({NG}, Apache-2.0)', 'MIT'),
                                ('COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, MIT)', 'permission')):
            with self.subTest(label=label):
                problems = self.lint(HEAD + '// GPL-3.0 stated here.\n' + self.body(label))
                self.assertTrue(any(f'licensed "{expected}"' in p for p in problems), problems)

    def test_known_repositories_with_their_licence_pass(self):
        for label in (f'COMMUNITY({NG}, MIT)', 'COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)'):
            with self.subTest(label=label):
                self.assertEqual(self.lint(HEAD + self.body(label)), [])
        self.assertEqual(self.lint(HEAD + '// GPL-3.0 stated here.\n' + self.body(f'COMMUNITY({PO3}, GPL-3.0)')), [])

    def test_licence_table_applies_without_labels_v2(self):
        # HEAD declares no `Labels: v2`; the free-form label still states a provenance.
        self.assertNotIn('Labels: v2', HEAD)
        problems = self.lint(HEAD + f'// names from COMMUNITY({NG}, GPL-3.0) here\nstruct Thing {{}};\n')
        self.assertTrue(any('licensed "MIT"' in p for p in problems), problems)

    def test_malformed_community_labels_are_refused_in_every_file(self):
        # None of these fits the label grammar, so the table could not see them; each is refused
        # without `Labels: v2` (HEAD) as well as with it.
        for label in ('COMMUNITY(powerof3/CommonLibSSE@main, MIT)', 'COMMUNITY(powerof3/CommonLibSSE@654E55F, MIT)',
                      'COMMUNITY(powerof3/CommonLibSSE, MIT)', 'COMMUNITY(powerof3/CommonLibSSE@654e55f, MIT licence)',
                      'COMMUNITY(powerof3/CommonLibSSE@654e55f,MIT)', 'community(someone/lib@1234567, MIT)',
                      'Community(powerof3/CommonLibSSE@654e55f, GPL-3.0)', 'COMMUNITY(unverified)'):
            for head in (HEAD, HEAD + '// Labels: v2\n'):
                with self.subTest(label=label, v2='Labels' in head):
                    problems = self.lint(head + '// GPL-3.0 stated here.\n' + self.body(label))
                    self.assertTrue(any('is not "COMMUNITY(<owner>/<repo>@<rev>, <licence>)"' in p for p in problems),
                                    problems)

    def test_known_repository_matched_without_case(self):
        for label, want in (('COMMUNITY(POWEROF3/CommonLibSSE@654e55f, MIT)', 'licensed "GPL-3.0"'),
                            ('COMMUNITY(powerof3/commonlibsse@654e55f, GPL-3.0)', 'write the repository as'),
                            ('COMMUNITY(charmedbaryon/commonlibsse-ng@b93280e, GPL-3.0)', 'licensed "MIT"')):
            with self.subTest(label=label):
                problems = self.lint(HEAD + '// GPL-3.0 stated here.\n' + self.body(label))
                self.assertTrue(any(want in p for p in problems), problems)
        # A different repository that merely shares a prefix is not a known one.
        self.assertEqual(self.lint(HEAD + self.body('COMMUNITY(powerof3/CommonLibSSE-fork@654e55f, MIT)')), [])

    def test_spaced_legacy_prose_is_not_a_label(self):
        # Older units describe origins in prose as "COMMUNITY (NG b93280e, MIT)"; that is not the
        # label token and stays outside this rule.
        self.assertEqual(self.lint(HEAD + '// Get: COMMUNITY (CommonLibSSE-NG b93280e, MIT)\nstruct Thing {};\n'), [])


class LintSiblingTests(unittest.TestCase):
    lint = LintLicenceTests.lint

    def test_sibling_label_checked_in_files_without_labels_v2(self):
        for label, want in ((f'SIBLING(momusdigital/fnv_decomp@abcdef12, no-licence)', f'pinned at {PIN}'),
                            (f'SIBLING(momusdigital/fnv_decomp@{PIN}, MIT)', 'licence word "no-licence"'),
                            (f'SIBLING(other/decomp@{PIN}, no-licence)', 'not an allowed sibling source'),
                            ('SIBLING(momusdigital/fnv_decomp, no-licence)', 'is not "SIBLING(')):
            with self.subTest(label=label):
                problems = self.lint(HEAD + f'struct Thing {{\n    // Get: {label}\n    int Get();\n}};\n')
                self.assertTrue(any(want in p for p in problems), problems)
        ok = f'struct Thing {{\n    // Get: SIBLING(momusdigital/fnv_decomp@{PIN}, no-licence)\n    int Get();\n}};\n'
        self.assertEqual(self.lint(HEAD + ok), [])

    def test_sibling_label_reported_once_in_a_v2_file(self):
        head = HEAD + '// Labels: v2\n// Thing: GUESS\n'
        problems = self.lint(head + 'struct Thing {\n    // Get: SIBLING(momusdigital/fnv_decomp@abcdef12, no-licence)\n'
                             '    int Get();\n};\n')
        self.assertEqual(len([p for p in problems if 'pinned at' in p]), 1, problems)

    def test_dotdot_in_sibling_source_path_is_refused(self):
        for path in ('src/../../outside.txt', 'include/a/../../b.h', 'src/..'):
            with self.subTest(path=path):
                problems = self.lint(f'// Sibling source: momusdigital/fnv_decomp@{PIN} {path}\n' + HEAD
                                     + 'struct Thing {};\n')
                self.assertTrue(any('".." components' in p for p in problems), problems)
        ok = f'// Sibling source: momusdigital/fnv_decomp@{PIN} src/core/a..b.cpp\n'
        self.assertFalse(any('".."' in p for p in self.lint(ok + HEAD + 'struct Thing {};\n')))


class LabelCheckPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / 'repo'
        (self.root / 'reconstruction/area').mkdir(parents=True)
        fnv = base / 'fnv'
        (fnv / 'include').mkdir(parents=True)
        (fnv / 'src').mkdir()
        (fnv / 'include/Widget.h').write_text('class Widget\n{\npublic:\n    int count;\n};\n')
        (fnv / 'src/w.cpp').write_text('int a;\n')
        (fnv / 'build').mkdir()
        (fnv / 'build/units.json').write_text(json.dumps({'units': []}))
        (base / 'outside.txt').write_text('private\n' * 50)
        (fnv / 'src/link.txt').symlink_to(base / 'outside.txt')
        git(fnv, 'init', '-q')
        git(fnv, 'add', '.')
        git(fnv, 'commit', '-qm', 'fixture')
        self.siblings = {'momusdigital/fnv_decomp': str(fnv)}
        self.rev = git(fnv, 'rev-parse', 'HEAD')[:8]

    def run_on(self, path):
        c = self.root / 'reconstruction/area/Widget.cpp'
        c.write_text(f'// Sibling source: momusdigital/fnv_decomp@{self.rev} {path}\nint x;\n')
        return check_labels.check([c], {}, root=self.root, siblings=self.siblings)

    def test_path_inside_the_clone_is_read(self):
        self.assertEqual(self.run_on('src/w.cpp:1'), [])

    def test_path_leading_outside_the_clone_is_not_read(self):
        for path in ('src/../../outside.txt:3', 'src/link.txt:3'):
            with self.subTest(path=path):
                findings = self.run_on(path)
                self.assertTrue(any('leads outside' in f for f in findings), findings)
                self.assertFalse(any('past the end' in f or 'does not exist' in f for f in findings), findings)


TEMPLATE_HEADER = '''#pragma once
namespace EX
{
    template <class Hash, class KeyEqual, class Traits,
        template <std::size_t, std::size_t> class Allocator>
    class ScatterTable
    {
    public:
        std::uint32_t _capacity;  // 0C
        const void*   _sentinel;  // 18
    };

    template <class T>
    struct Box : public Base<T>
    {
        T value;
    };

    struct HeapAllocator
    {
        void* _entries;
    };

    struct Holder : public Base<struct Tag>
    {
        int held;
    };

    template <class K, class V = Pair<K, struct Tag>>
    class Map : public Base<std::pair<K, V>>
    {
        V* _root;
    };
}
'''


class TemplateScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / 'repo'
        (self.root / 'reconstruction/area').mkdir(parents=True)
        lib = base / 'lib'
        (lib / 'include/EX').mkdir(parents=True)
        (lib / 'include/EX/Table.h').write_text(TEMPLATE_HEADER)
        git(lib, 'init', '-q')
        git(lib, 'add', '.')
        git(lib, 'commit', '-qm', 'fixture')
        self.checkouts = {'Example/Lib': str(lib)}
        self.label = f'COMMUNITY(Example/Lib@{git(lib, "rev-parse", "HEAD")[:7]}, MIT)'

    def run_on(self, line):
        h = self.root / 'reconstruction/area/Widget.h'
        h.write_text('// Labels: v2\n' + line + '\n')
        return check_labels.check([h], self.checkouts, root=self.root)

    def test_template_template_parameter_does_not_take_the_class_body(self):
        names = ('ScatterTable::_capacity, ScatterTable::_sentinel, Box::value, HeapAllocator::_entries, '
                 'Holder::held, Map::_root')
        self.assertEqual(self.run_on(f'// {names}: {self.label}'), [])

    def test_names_the_class_lacks_are_still_found(self):
        findings = self.run_on(f'// ScatterTable::_free: {self.label}')
        self.assertEqual(len(findings), 1, findings)
        self.assertIn('ScatterTable::_free', findings[0])

    def test_scope_parser_names(self):
        names = [s[3] for s in check_labels.unit_scopes(TEMPLATE_HEADER)]
        self.assertEqual(names, ['EX', 'ScatterTable', 'Box', 'HeapAllocator', 'Holder', 'Map'])


if __name__ == '__main__':
    unittest.main()
