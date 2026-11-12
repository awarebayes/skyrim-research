"""Tests for tools/unit_skeleton.py (skeleton.py, sheet.py), the lint's skeleton rule and the
missing-source message of tools/verifier/attempt. All inputs are synthetic."""
import contextlib
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
import check  # noqa: E402
import lint_reconstruction as lint  # noqa: E402
import sheet  # noqa: E402
import skeleton  # noqa: E402
import unit_skeleton as us  # noqa: E402

BUILD = json.loads((ROOT / 'builds/target.json').read_text())['build_id']
NG = 'CharmedBaryon/CommonLibSSE-NG@b93280e, MIT'
PO3 = 'powerof3/CommonLibSSE@654e55f, GPL-3.0'

# A shared header of the base class, as an accepted unit would provide it.
BASE_H = f"""// Widget base, build {BUILD}.
// Labels: v2
// Source exposure: mixed
// WidgetBase: COMMUNITY({NG})
#pragma once
class Cell;
class WidgetBase
{{
public:
    WidgetBase(Cell* a_cell, float a_life);
    virtual ~WidgetBase();
    void* unk08;
}};
"""
# Class material as the pack export writes it: base chain and image sizes.
CLASS_SKELETON = """// synthetic class material
class WidgetBase
{
};
static_assert(sizeof(WidgetBase) == 0x10);
class MidWidget : public ::WidgetBase
{
};
static_assert(sizeof(MidWidget) == 0x18);
class FancyWidget : public ::MidWidget
{
};
static_assert(sizeof(FancyWidget) == 0x28);
"""


def pack_readme(decl):
    conv = f'- Community declaration: `{decl}`.\n- Member function: `this` arrives in RCX.\n' if decl else ''
    return (f'# PRIVATE context pack\n\n## References leaving the function\n\n| +off | kind | target |\n|---|---|---|\n'
            f'| 0x4 | call CALL | 0x2000 |\n\n## Calling and return convention\n\n{conv}\n'
            '## Observed memory operands (non-stack)\n\n| displacement | base register | width | at |\n'
            '|---|---|---|---|\n| 0x18 | RCX | byte | +0x0 |\n')


def load_script(name):
    loader = SourceFileLoader(name, str(ROOT / 'tools' / 'verifier' / name))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class Fixture(unittest.TestCase):
    """A repository with one shared header, packs for three functions and a one-unit group."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        r = self.root
        (r / 'builds').mkdir()
        shutil.copyfile(ROOT / 'builds/target.json', r / 'builds/target.json')
        (r / 'findings').mkdir()
        (r / 'findings/batch.md').write_text('x\n')
        (r / 'reconstruction/recipes').mkdir(parents=True)
        (r / 'reconstruction/recipes/r.json').write_text('{}\n')
        (r / 'reconstruction/misc').mkdir()
        (r / 'reconstruction/misc/WidgetBase.h').write_text(BASE_H)
        packs = r / '.local/packs' / BUILD
        (packs / 'class/FancyWidget').mkdir(parents=True)
        (packs / 'class/FancyWidget/skeleton.h').write_text(CLASS_SKELETON)
        (packs / 'class/FancyWidget/class-excerpt.h').write_text(f'// CommonLibSSE-NG {"b" * 40} (MIT): x.h:1\n')
        fns = []
        specs = [(0x1000, 8, 'FancyWidget::GetFlag', 'CommonLibSSE-NG (MIT) slot',
                  '[[nodiscard]] bool GetFlag(Cell* a_cell, int a_mode = 0) const override;', None),
                 (0x1100, 50, 'FancyWidget::~FancyWidget', 'powerof3/CommonLibSSE (GPL-3.0) slot', None,
                  {'symbols': ['??_G'], 'kind': 'scalar deleting destructor'}),
                 (0x1200, 12, 'FancyWidget::Mystery', 'CommonLibSSE-NG (MIT) slot', None, None)]
        for rva, size, name, source, decl, dtor in specs:
            d = packs / f'0x{rva:x}'
            d.mkdir()
            (d / 'pack.json').write_text(json.dumps({'identity': {'name_source': source}, 'cautions': []}))
            (d / 'README.md').write_text(pack_readme(decl))
            (d / 'listing.txt').write_text(f'function at 0x{rva:x}   \n  +0x000  RET   \n')
            (d / 'decompiled.c').write_text('void f(void) { return; }\n')
            fn = {'rva': f'0x{rva:x}', 'size': size, 'symbol': f'unbound:{name}', 'community_name': name,
                  'pack': f'.local/packs/{BUILD}/0x{rva:x}'}
            if dtor:
                fn['destructor'] = dtor
            fns.append(fn)
        self.group = r / '.local/tasks/g1'
        self.unit = self.group / 'g1-fancywidget'
        self.unit.mkdir(parents=True)
        (self.unit / 'task.json').write_text(json.dumps({
            'task_id': 'g1-fancywidget', 'build_id': BUILD, 'compiled': 'reconstruction/misc/FancyWidget.cpp',
            'recipe': 'reconstruction/recipes/r.json', 'functions': fns, 'max_attempts': 4,
            'export': {'class_material': [f'.local/packs/{BUILD}/class/FancyWidget']}}))
        (self.unit / 'BRIEF.md').write_text(
            'Evidence: cite `findings/batch.md` in the .cpp header.\n\nShared headers (existing):\n'
            '- `WidgetBase`: `#include "../misc/WidgetBase.h"`\n\nCookbook rules these listings point to (x):\n'
            '- 14, 18: a slot-0 destructor is the deleting one.\n\n'
            '## Sibling source (fnv)\n\nCaution: text.\n\n- `0x1000`: `FancyWidget::GetFlag` `src/fancy.cpp:3` (/O2, 9 bytes); same name.\n')
        (r / '.local/sources/fnv_decomp/src').mkdir(parents=True)
        (r / '.local/sources/fnv_decomp/src/fancy.cpp').write_text(
            '// x\n\nbool FancyWidget::GetFlag()\n{\n    return flag;\n}\nint After() { return 1; }\n')
        (self.group / 'group.json').write_text(json.dumps({'group_id': 'g1', 'units': [
            {'dir': 'g1-fancywidget', 'compiled': 'reconstruction/misc/FancyWidget.cpp', 'functions': [],
             'max_attempts': 4}], 'functions': 3}))

    def tearDown(self):
        shutil.rmtree(self.root)

    def files(self):
        return us.skeleton_files(self.unit, repo=self.root)


class SkeletonText(Fixture):
    def test_header_fields_labels_and_stubs(self):
        h_rel, h, cpp_rel, cpp = self.files()
        self.assertEqual((h_rel, cpp_rel), ('reconstruction/misc/FancyWidget.h', 'reconstruction/misc/FancyWidget.cpp'))
        for text in (h, cpp):
            self.assertIn(BUILD, text)
            self.assertIn('Labels: v2', text)
            self.assertIn('Source exposure: mixed', text)
            self.assertIn('Task: g1-fancywidget', text)
            self.assertIn('GPL-3.0', text)  # a po3 label makes both files state the licence
        self.assertIn(f'// FancyWidget: COMMUNITY({NG}) EXE_RTTI', h)
        self.assertIn(f'// FancyWidget::GetFlag, FancyWidget::Mystery: COMMUNITY({NG})', h)
        self.assertIn(f'// FancyWidget::~FancyWidget: COMMUNITY({PO3})', h)
        self.assertIn('// MidWidget: STANDIN EXE_RTTI', h)
        self.assertNotIn('class Cell;', h.split('#pragma once')[1])  # the included header declares it
        self.assertIn('#include "../misc/WidgetBase.h"', h)
        # The intermediate base is a stand-in padded to its image size; it inherits the base's
        # constructor because the base has no default one.
        self.assertIn('class MidWidget : public WidgetBase', h)
        self.assertIn('using WidgetBase::WidgetBase;', h)
        self.assertIn('std::uint8_t unknown10[0x8];  // 10', h)
        self.assertIn('static_assert(sizeof(MidWidget) == 0x18, "MidWidget size");', h)
        self.assertIn('std::uint8_t unknown18[0x10];  // 18', h)
        # Signatures: community declaration cleaned of attributes, override and default arguments.
        self.assertIn('virtual bool GetFlag(Cell* a_cell, int a_mode = 0) const;  // compared: 0x1000', h)
        self.assertIn('bool FancyWidget::GetFlag(Cell* a_cell, int a_mode) const', cpp)
        self.assertIn('void Mystery();  // compared: 0x1200; TODO signature', h)
        self.assertIn('virtual ~FancyWidget();  // compared: 0x1100 (scalar deleting destructor)', h)
        self.assertIn('FancyWidget(Cell* a_cell, float a_life);', h)
        self.assertIn('FancyWidget::FancyWidget(Cell* a_cell, float a_life)\n    : MidWidget(a_cell, a_life)', cpp)
        # One unfilled stub per compared function, and the paperwork placeholders.
        self.assertEqual(cpp.count(f'    {us.BODY_MARKER};'), 3)
        self.assertIn(us.MODEL_MARKER, cpp)
        self.assertIn(us.ORIGIN_MARKER, cpp)
        for line in ('RVA 0x1000, 8 bytes: FancyWidget::GetFlag', 'RVA 0x1100, 50 bytes', 'RVA 0x1200, 12 bytes'):
            self.assertIn(line, cpp)
        self.assertIn('Evidence: findings/batch.md', cpp)
        self.assertIn('Recipe: reconstruction/recipes/r.json', cpp)

    def test_drafted_by_fills_the_model_line(self):
        _h, _ht, _c, cpp = us.skeleton_files(self.unit, drafted_by='test-model', repo=self.root)
        self.assertIn('Drafted by test-model', cpp)
        self.assertNotIn(us.MODEL_MARKER, cpp)

    def test_untouched_skeleton_lints_clean_except_the_placeholders(self):
        h_rel, cpp_rel = us.write_skeleton(self.unit, repo=self.root)
        names = [h_rel, cpp_rel]
        self.assertEqual(lint.lint_tree(self.root, names, skeleton_ok=names), [])
        strict = lint.lint_tree(self.root, names)
        self.assertTrue(strict)
        self.assertTrue(all('skeleton not filled' in p for p in strict), strict)
        self.assertEqual(len(strict), 3 + 2)  # three stub bodies, the model and origin placeholders

    def test_filled_skeleton_passes_strict_lint(self):
        h_rel, cpp_rel = us.write_skeleton(self.unit, drafted_by='test-model', repo=self.root)
        path = self.root / cpp_rel
        text = path.read_text().replace(f'    {us.BODY_MARKER};', '    return {};').replace(us.ORIGIN_MARKER, 'none')
        path.write_text(text)
        self.assertEqual(lint.lint_tree(self.root, [h_rel, cpp_rel]), [])

    def test_check_lint_tolerates_placeholders_only_in_files_it_is_told_are_untracked(self):
        h_rel, cpp_rel = us.write_skeleton(self.unit, repo=self.root)
        check.lint(self.root, [h_rel, cpp_rel], skeleton_ok={h_rel, cpp_rel})
        with self.assertRaisesRegex(ValueError, 'skeleton not filled'):
            check.lint(self.root, [h_rel, cpp_rel])

    def test_marker_in_any_spelling_is_refused(self):
        h_rel, cpp_rel = us.write_skeleton(self.unit, drafted_by='m', repo=self.root)
        path = self.root / cpp_rel
        text = path.read_text().replace(f'    {us.BODY_MARKER};', '    return {};').replace(us.ORIGIN_MARKER, 'none')
        path.write_text(text + '// SKELETON_TODO_LATER\n')
        self.assertTrue(any('SKELETON_TODO_LATER' in p for p in lint.lint_tree(self.root, [cpp_rel])))

    def test_refuses_to_overwrite(self):
        (self.root / 'reconstruction/misc/FancyWidget.cpp').write_text('// mine\n')
        with self.assertRaisesRegex(us.SkeletonError, 'already exist'):
            us.write_skeleton(self.unit, repo=self.root)
        self.assertEqual((self.root / 'reconstruction/misc/FancyWidget.cpp').read_text(), '// mine\n')
        self.assertFalse((self.root / 'reconstruction/misc/FancyWidget.h').exists())

    def test_cli_writes_every_unit_of_a_group_once(self):
        old = skeleton.REPO
        skeleton.REPO = self.root
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
                with unittest.mock.patch.object(us, 'REPO', self.root):
                    self.assertEqual(skeleton.main([str(self.group), '--sheets']), 0)
                    self.assertEqual(skeleton.main([str(self.group)]), 1)
            self.assertIn('already exist', err.getvalue())
        finally:
            skeleton.REPO = old
        self.assertTrue((self.root / 'reconstruction/misc/FancyWidget.cpp').is_file())
        self.assertTrue((self.unit / 'sheet.md').is_file())

    def test_declaration_parsing(self):
        self.assertEqual(us.split_declaration('[[nodiscard]] static RE::Foo* Get();'), ('Foo*', '', '', False, True))
        self.assertEqual(us.split_declaration('virtual void Set(int a_x) = 0;'), ('void', 'int a_x', '', True, False))
        self.assertEqual(us.split_declaration('bool IsEqual(NiObject* a_object) override;'),
                         ('bool', 'NiObject* a_object', '', True, False))
        self.assertIsNone(us.split_declaration('int value;'))
        self.assertEqual(us.without_defaults('int a = 0, float b = f(1, 2)'), 'int a, float b')

    def test_community_label_aliases(self):
        self.assertEqual(us.community_label('Community name, not verified: meh321 Address Library name list')[0],
                         'COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)')
        self.assertEqual(us.community_label('CommonLibSSE-NG (MIT) slot')[0], f'COMMUNITY({NG})')
        self.assertEqual(us.community_label('powerof3/CommonLibSSE (GPL-3.0)')[0], f'COMMUNITY({PO3})')
        self.assertEqual(us.community_label('nothing known'), (None, None))


class Sheets(Fixture):
    def test_function_sheet_has_the_facts_and_fits_the_cap(self):
        pages = us.sheet_pages(self.unit, '0x1000', repo=self.root)
        self.assertEqual(len(pages), 1)
        page = pages[0]
        self.assertLessEqual(len(page), us.SHEET_CAP)
        for needle in ('# 0x1000 FancyWidget::GetFlag (8 bytes)', 'Community declaration', '| 0x4 | call CALL',
                       '| 0x18 | RCX | byte', '14, 18:', 'src/fancy.cpp:3', '+0x000  RET\n', 'return;'):
            self.assertIn(needle, page)
        self.assertNotIn('RET   ', page)  # column padding dropped
        self.assertNotIn('return flag;', page)  # the sibling body only on request
        with_snippet = us.sheet_pages(self.unit, '0x1000', sibling=True, repo=self.root)[0]
        self.assertIn('return flag;', with_snippet)
        self.assertNotIn('After()', with_snippet)

    def test_destructor_kind_and_unknown_function(self):
        self.assertIn('Kind: scalar deleting destructor', us.sheet_pages(self.unit, '0x1100', repo=self.root)[0])
        with self.assertRaisesRegex(us.SkeletonError, 'not a function of this unit'):
            us.sheet_pages(self.unit, '0x9999', repo=self.root)

    def test_long_sheets_paginate_under_the_cap(self):
        listing = self.root / '.local/packs' / BUILD / '0x1000/listing.txt'
        listing.write_text(''.join(f'  +0x{i:03x}  MOV RAX,RBX\n' for i in range(900)) + 'x' * 9000 + '\n')
        pages = us.sheet_pages(self.unit, '0x1000', repo=self.root)
        self.assertGreater(len(pages), 3)
        self.assertTrue(all(len(p) <= us.SHEET_CAP - us.FOOTER_ROOM for p in pages))
        self.assertEqual(''.join(pages), us.function_sheet(us.load_unit(self.unit, self.root),
                                                           us.find_function(us.load_unit(self.unit, self.root),
                                                                            '0x1000'), repo=self.root))
        written = us.write_sheets(self.unit, repo=self.root)
        names = sorted(p.name for p in written)
        self.assertIn('sheet.md', names)
        self.assertIn('sheet-0x1000-p1.md', names)
        self.assertIn('sheet-0x1100.md', names)
        self.assertTrue(all(len(p.read_text()) <= us.SHEET_CAP for p in written))

    def test_cli_pages(self):
        with unittest.mock.patch.object(sheet, 'REPO', self.root), \
                unittest.mock.patch.object(us, 'REPO', self.root):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(sheet.main([str(self.unit)]), 0)
                self.assertEqual(sheet.main([str(self.unit), '--function', '0x1000']), 0)
            self.assertIn('| 0x1000 | 8 | FancyWidget::GetFlag | 1 |', out.getvalue())
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(sheet.main([str(self.unit), '--function', '0x1000', '--page', '2']), 2)
            self.assertIn('has 1 page', err.getvalue())


class AttemptMissingSource(unittest.TestCase):
    def setUp(self):
        self.attempt = load_script('attempt')
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.dir = self.tmp / '.local/tasks/u1'
        self.dir.mkdir(parents=True)
        self.task = {'dir': self.dir, 'task_id': 'u1', 'compiled': 'reconstruction/misc/Gadget.cpp',
                     'max_attempts': 3}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_message_names_the_file_and_the_skeleton_command(self):
        msg = self.attempt.missing_source_message(self.task, self.tmp)
        self.assertIn('reconstruction/misc/Gadget.cpp does not exist yet', msg)
        self.assertIn('nor does reconstruction/misc/Gadget.h', msg)
        self.assertIn('not counted', msg)
        self.assertIn('python3 tools/skeleton.py .local/tasks/u1', msg)
        self.assertNotIn('repository-relative regular file', msg)

    def test_no_message_once_the_source_exists(self):
        (self.tmp / 'reconstruction/misc').mkdir(parents=True)
        (self.tmp / 'reconstruction/misc/Gadget.cpp').write_text('// x\n')
        self.assertIsNone(self.attempt.missing_source_message(self.task, self.tmp))

    def test_attempt_exits_2_and_logs_nothing(self):
        p = self.attempt.pipeline
        with unittest.mock.patch.object(p, 'load_task', lambda d: self.task), \
                unittest.mock.patch.object(p, 'lock', lambda d: None), \
                unittest.mock.patch.object(p, 'REPO', self.tmp), \
                unittest.mock.patch.object(p, 'ensure_standing', side_effect=AssertionError('no machine')):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(self.attempt.attempt(self.dir), 2)
        self.assertIn('does not exist yet', err.getvalue())
        self.assertFalse((self.dir / 'attempts.jsonl').exists())
        self.assertFalse((self.dir / 'attempts').exists())


if __name__ == '__main__':
    unittest.main()
