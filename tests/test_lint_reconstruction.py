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


V2_HEADER = f"""// Types for Widget, build {BUILD}.
// Source exposure: community-headers. Labels: v2
// Widget, Widget::Get: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT)
// Widget::value: GUESS(low); the only member the function reads
// Gadget: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

class Widget {{
public:
    int Get() const;
    int value;
}};
"""


class ReviewerFollowUpTests(LintTests):
    def test_universal_character_names_refused_anywhere(self):
        for snippet in ('int caf\\u00e9 = 0;', 'const char* s = "\\U0001F600";', '// see \\u0041'):
            with self.subTest(snippet):
                self.assert_problem('universal character name', source=SOURCE + snippet + '\n')

    def test_codegen_constructs_need_a_justification(self):
        cases = {
            '__forceinline': '__forceinline int Twice(int x) { return x * 2; }',
            '[[msvc::': '[[msvc::forceinline]] int Twice(int x) { return x * 2; }',
            'codegen intrinsic': 'unsigned long Low(unsigned long m) { unsigned long i; _BitScanForward(&i, m); return i; }',
        }
        for needle, line in cases.items():
            with self.subTest(needle):
                self.assert_problem(needle, source=SOURCE + line + '\n')
                self.write(source=SOURCE + '// the engine forces this accessor inline everywhere\n' + line + '\n')
                self.assertEqual(self.problems(), [])
                self.write(source=SOURCE + line + '  // inlined by the original engine\n')
                self.assertEqual(self.problems(), [])
                self.assert_problem(needle, source=SOURCE + '// to match\n' + line + '\n')

    def test_labels_v2_grammar_accepted(self):
        self.write(header=V2_HEADER)
        self.assertEqual(self.problems(), [])

    def test_labels_v2_grammar_refusals(self):
        cases = {
            'Names are COMMUNITY and unverified.': 'label outside the v2 grammar',
            'Widget: COMMUNITY (CommonLibSSE-NG b93280e, MIT)': 'label outside the v2 grammar',
            'Widget: COMMUNITY(CharmedBaryon/CommonLibSSE-NG, MIT)': 'label outside the v2 grammar',
            'Widget: GUESS names': 'label outside the v2 grammar',
            'Widget: GUESSED': 'label outside the v2 grammar',
            'Widget: EXE-RTTI': 'label outside the v2 grammar',
            'Widget: GUESS; agrees with EXE_RTTI': 'label outside the v2 grammar',
            'Gadget: STANDIN': 'STANDIN also needs the origin',
        }
        for line, needle in cases.items():
            with self.subTest(line):
                self.assert_problem(needle, header=V2_HEADER.replace('#pragma once', f'// {line}\n#pragma once'))

    def test_labels_v2_header_needs_a_label_line(self):
        header = '\n'.join(l for l in V2_HEADER.splitlines() if ': ' not in l or 'Labels' in l or 'exposure' in l) + '\n'
        self.assert_problem('needs at least one', header=header)

    def test_unknown_labels_version_refused(self):
        self.assert_problem('unknown "Labels: v3"', header=V2_HEADER.replace('Labels: v2', 'Labels: v3'))

    def test_free_form_labels_still_pass_without_v2(self):
        self.write(header=HEADER.replace('Names are GUESS.', 'Names are GUESS names; COMMUNITY (NG b93280e, MIT).'))
        self.assertEqual(self.problems(), [])


if __name__ == '__main__':
    unittest.main()
