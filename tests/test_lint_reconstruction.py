"""Tests for tools/lint_reconstruction.py: each rule rejects its construct, the accepted unit passes."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import lint_reconstruction as lint  # noqa: E402

BUILD = json.loads((ROOT / 'builds/target.json').read_text())['build_id']
HEADER = f"""// Types for Widget, build {BUILD}.
// Source exposure: binary-analysis. Names are GUESS.
#pragma once

class Widget {{
public:
    int Get() const;
    int value;
}};
"""
SOURCE = f"""// Widget::Get, build {BUILD}, RVA 0x1000, 8 bytes.
// Evidence: findings/TEMPLATE.md
// Source exposure: binary-analysis. Drafted by a synthetic test.
// Recipe: reconstruction/recipes/r.json
#include "Widget.h"

int Widget::Get() const {{ return value; }}
"""


class LintTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / 'builds').mkdir()
        shutil.copyfile(ROOT / 'builds/target.json', self.root / 'builds/target.json')
        (self.root / 'findings').mkdir()
        (self.root / 'findings/TEMPLATE.md').write_text('x\n')
        (self.root / 'reconstruction/recipes').mkdir(parents=True)
        (self.root / 'reconstruction/recipes/r.json').write_text('{}\n')
        (self.root / 'reconstruction/misc').mkdir()
        self.write(HEADER, SOURCE)

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, header=None, source=None):
        if header is not None:
            (self.root / 'reconstruction/misc/Widget.h').write_text(header)
        if source is not None:
            (self.root / 'reconstruction/misc/Widget.cpp').write_text(source)

    def problems(self):
        return lint.lint_tree(self.root)

    def assert_problem(self, needle, header=None, source=None):
        self.write(header, source)
        found = self.problems()
        self.assertTrue(any(needle in p for p in found), f'{needle!r} not in {found}')

    def test_good_unit_and_repository_sources_pass(self):
        self.assertEqual(self.problems(), [])
        self.assertEqual(lint.lint_tree(ROOT), [])

    def test_banned_constructs(self):
        body = SOURCE.replace('{ return value; }', '{{ {} return value; }}')
        cases = {
            'inline assembly': '__asm { nop }',
            '__emit': '__emit 0x90;',
            'pragma operator': '__pragma(optimize("", off))',
            'codegen-only __declspec': '} __declspec(naked) void f() {',
            'byte escapes': 'const char* s = "\\x48\\x89\\x5c\\x24";',
            'braced list of 8+': 'static const unsigned char b[] = {0x48, 0x89, 0x5c, 0x24, 8, 0x57, 0x48, 0x83};',
        }
        for needle, snippet in cases.items():
            with self.subTest(needle):
                self.assert_problem(needle, source=body.replace('{}', snippet))

    def test_banned_words_in_comments_are_refused_too(self):
        # No comment state is kept, so a lexing disagreement cannot hide code; prose pays for it.
        self.assert_problem('inline assembly', source=SOURCE + '// no __asm here\n')

    def test_reviewer_bypasses(self):
        body = SOURCE.replace('{ return value; }', '{{ {} return value; }}')
        cases = {
            # Backslash-newline inside a directive or a __declspec argument list.
            '#pragma optimize': '\n#pra\\\ngma optimize("", off)\n',
            '#pragma /*': '\n#pragma /**/ optimize("", off)\n',
            'codegen-only __declspec': '} __declspec(na\\\nked) void f() {',
            # The old lexer took a digit separator for a character literal and stopped seeing code.
            "digit separator": "int n = 1'000; __declspec(naked) int m;",
            # A banned argument that is not the first one.
            'codegen-only __declspec ': '} __declspec(noinline, naked) void f() {',
            # The keyword reached through an identity macro, or separated from its parenthesis.
            'codegen-only __declspec word': '}\n#define ID(x) x\nID(__declspec)(safebuffers) void f() {',
            'codegen-only __declspec word ': '} __declspec/**/(naked) void f() {',
            'codegen-only __declspec  ': '} __declspec(align(16) safebuffers) void f() {',
            'token pasting': '\n#define P(a, b) a##b\n',
            '#define naming __declspec': '\n#define NAKED __declspec(naked)\n',
            '#define naming __declspec ': '\n#define WORD naked\n',
            '#define naming __declspec  ': '\n#define EMIT __emit\n',
            'inline assembly': '__asm__("nop");',
            'byte-sized integer or character literals': "static const char b[] = {'\\x48', '\\x89', 'H', 1, 2, 3, 4, 5};",
        }
        for needle, snippet in cases.items():
            with self.subTest(needle):
                self.assert_problem(needle.strip(), source=body.replace('{}', snippet))

    def test_digit_separator_free_literals_pass(self):
        self.write(source=SOURCE.replace('return value;', "return value + 1000 + u8'a' + L'b' + '1';"))
        self.assertEqual(self.problems(), [])

    def test_codegen_pragmas(self):
        self.assert_problem('#pragma optimize', source=SOURCE + '#pragma optimize("", off)\n')
        self.write(source=SOURCE)
        self.write(header=HEADER.replace('#pragma once', '#pragma once\n#pragma pack(push, 4)\n#pragma pack(pop)'))
        self.assertEqual(self.problems(), [])

    def test_header_fields(self):
        self.assert_problem('build id', source=SOURCE.replace(BUILD, 'other'))
        self.assert_problem('Source exposure', source=SOURCE.replace('binary-analysis', 'leaked'))
        self.assert_problem('RVA 0x', source=SOURCE.replace('RVA 0x1000', 'RVA ?'))
        self.assert_problem('Drafted by', source=SOURCE.replace('Drafted by', 'Written by'))
        self.assert_problem('evidence', source=SOURCE.replace('findings/TEMPLATE.md', 'findings/none.md'))
        self.assert_problem('Recipe:', source=SOURCE.replace('recipes/r.json', 'recipes/none.json'))
        self.write(source=SOURCE)
        self.assert_problem('name origin', header=HEADER.replace('GUESS', 'guessed'))

    def test_layout(self):
        self.assert_problem('must include its own header', source=SOURCE.replace('#include "Widget.h"', ''))
        self.write(source=SOURCE)
        self.assert_problem('declare class Widget', header=HEADER.replace('class Widget {', 'class Gadget {'))
        self.write(header=HEADER)
        (self.root / 'reconstruction/Engine').mkdir()
        (self.root / 'reconstruction/Engine/widget.cpp').write_text(SOURCE)
        self.assertTrue(any('reconstruction/<area>/<Class>' in p for p in self.problems()))

    def test_include_style(self):
        self.assert_problem('must be included as "misc/Widget.h"', source=SOURCE.replace('"Widget.h"', '<misc/Widget.h>'))
        self.assert_problem('block comment', source=SOURCE + '/*\n#include "Widget.h"\n*/\n')
        self.assert_problem('conditional block', source=SOURCE + '#if 0\n#include "Widget.h"\n#endif\n')
        self.assert_problem('not exactly #include', source=SOURCE + '// see #include order\n')
        guarded = HEADER.replace('#pragma once', '#ifndef WIDGET_H\n#define WIDGET_H\n#include <cstdint>') + '#endif\n'
        self.write(header=guarded, source=SOURCE)
        self.assertEqual(self.problems(), [])


if __name__ == '__main__':
    unittest.main()
