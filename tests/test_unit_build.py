"""Tests for tools/verifier/unit_build.py: build environment, /showIncludes cross-check, sync and prep.

A fake msvc-wine layout stands in for the toolchain: its `cl` prints `/showIncludes` notes and
writes an original synthetic COFF object (tests/synthetic_pecoff.py), so the whole host-side path
runs here without a compiler, Wine or game input.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
import synthetic_pecoff as sp  # noqa: E402
import unit_build as ub  # noqa: E402

COPY = ('tools/compare_runtime.py', 'tools/compare_internal.py', 'tools/compare.py', 'tools/pecoff.py', 'tools/source_digest.py', 'tools/verifier/verify_function.py',
        'tools/verifier/unit_build.py')
FAKE_CL = r'''#!/usr/bin/env bash
# Fake cl for tests: report what it saw, print include notes, write the synthetic object.
set -u
env > "$FAKE_LOG/env.txt"
out=; src=
for a in "$@"; do case $a in /Fo*) out=${a#/Fo};; /*) ;; *) src=$a;; esac; done
here=$(pwd -P)
echo "$(basename "$src")"
case "${FAKE_MODE:-ok}" in
  ok)       echo "Note: including file: $here/reconstruction/synth/Synth.h";;
  extra)    echo "Note: including file: $here/reconstruction/synth/Synth.h"
            echo "Note: including file:  $here/reconstruction/synth/Other.h";;
  outside)  echo "Note: including file: $here/reconstruction/synth/Synth.h"
            echo "Note: including file: /usr/include/stdio.h";;
  fail)     echo "$src(3): error C2065: 'x': undeclared identifier"; exit 2;;
esac
echo "Note: including file:  $FAKE_TOOLCHAIN/include/cstdint"
cp "$FAKE_OBJECT" "$out"
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Pure(unittest.TestCase):
    def test_clean_env_removes_search_and_flag_variables(self):
        env = ub.clean_env({'PATH': '/bin', 'INCLUDE': 'x', 'CL': '/Ox', '_CL_': '/FIx.h', 'LIB': 'y',
                            'LIBPATH': 'z', 'EXTERNAL_INCLUDE': 'w', 'HOME': '/h'})
        self.assertEqual(env, {'PATH': '/bin', 'HOME': '/h'})

    def test_include_must_stay_under_toolchain_root(self):
        base = 'z:\\home\\user\\msvc'
        self.assertIsNone(ub.include_problem(f'{base}\\vc\\include;{base}\\kits\\10\\include\\um', base))
        self.assertIn('outside', ub.include_problem(f'{base}\\vc\\include;z:\\home\\user\\repo', base))
        self.assertIn('outside', ub.include_problem(f'{base}\\..\\evil', base))
        self.assertIn('outside', ub.include_problem(f'{base}2\\include', base))
        self.assertEqual(ub.include_problem('', base), 'INCLUDE is empty')

    def test_parse_show_includes_keeps_other_lines(self):
        opened, rest = ub.parse_show_includes('A.cpp\nNote: including file: /r/a.h\n'
                                              'Note: including file:   /m/x\nwarning C4100: y\n')
        self.assertEqual(opened, ['/r/a.h', '/m/x'])
        self.assertEqual(rest, ['A.cpp', 'warning C4100: y'])

    def test_classify_includes(self):
        repo, tool, out = ub.classify_includes(
            ['/w/repo/reconstruction/a/B.h', 'z:\\m\\include\\cstdint', '/m/include/x', '/w/repo/../evil.h',
             'c:\\windows\\x.h', 'relative.h', '/w/repository/x.h'], '/w/repo', '/m')
        self.assertEqual(repo, ['reconstruction/a/B.h'])
        self.assertEqual(tool, 2)
        self.assertEqual(out, ['/w/repo/../evil.h', 'c:\\windows\\x.h', 'relative.h', '/w/repository/x.h'])

    def test_closure_difference_both_directions(self):
        closure = ['reconstruction/a/B.cpp', 'reconstruction/a/B.h']
        self.assertIsNone(ub.closure_difference(['reconstruction/a/B.h'], 'reconstruction/a/B.cpp', closure))
        self.assertIn('lacks: reconstruction/a/C.h', ub.closure_difference(
            ['reconstruction/a/B.h', 'reconstruction/a/C.h'], 'reconstruction/a/B.cpp', closure))
        self.assertIn('did not open', ub.closure_difference([], 'reconstruction/a/B.cpp', closure))

    def test_mismatch_offset(self):
        self.assertEqual(ub.mismatch_offset('code differs at +0x4c'), '+0x4c')
        self.assertEqual(ub.mismatch_offset('candidate function is 3 bytes'), '-')


class HostRun(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.repo, self.msvc, self.work = self.tmp / 'repo', self.tmp / 'msvc', self.tmp / 'work'
        self.log = self.tmp / 'log'
        self.log.mkdir()
        inputs = sp.inputs()
        self.image = self.tmp / 'image.pe'
        self.image.write_bytes(inputs['image_bytes'])
        self.object = self.tmp / 'synthetic.obj'
        self.object.write_bytes(inputs['object_bytes'])
        for name in COPY:
            (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, self.repo / name)
        bindir = self.msvc / 'bin/x64'
        bindir.mkdir(parents=True)
        (bindir / 'cl.exe').write_bytes(b'fake compiler binary')
        (self.repo / 'tools/verifier/pinned.sha256').write_text(f'{sha(bindir / "cl.exe")}  cl.exe\n')
        base = 'z:' + str(self.msvc).replace('/', '\\')
        self.include = f'{base}\\vc\\include;{base}\\kits\\include'
        (bindir / 'msvcenv.sh').write_text(f"BASE='{base}'\nBINDIR='{bindir}'\nDEFAULT_INCLUDE='{self.include}'\n"
                                           'export INCLUDE="${FAKE_INCLUDE:-$DEFAULT_INCLUDE}"\n')
        (bindir / 'cl').write_text(FAKE_CL)
        (bindir / 'cl').chmod(0o755)
        (self.repo / 'builds').mkdir()
        (self.repo / 'builds/target.json').write_text(json.dumps(inputs['manifest']))
        (self.repo / 'reconstruction/synth').mkdir(parents=True)
        (self.repo / 'reconstruction/synth/Synth.h').write_text('#pragma once\nint SyntheticSum(int* p);\n')
        (self.repo / 'reconstruction/synth/Synth.cpp').write_text('#include "Synth.h"\n')
        (self.repo / 'reconstruction/recipes').mkdir()
        (self.repo / 'reconstruction/recipes/r.json').write_bytes(sp.recipe())
        (self.repo / 'task').mkdir()
        (self.repo / 'task/symbols.json').write_text(json.dumps(inputs['symbol_map']))
        self.task = inputs['task']

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def spec(self, **overrides):
        files = {}
        for path in sorted(self.repo.rglob('*')):
            rel = path.relative_to(self.repo).as_posix()
            if path.is_file() and not rel.startswith(('.unit', '.local')) and '__pycache__' not in rel:
                files[rel] = sha(path)
        spec = {'unit_spec_schema': 1, 'task_id': 'synthetic', 'host': 'test-host', 'build_id': 'synthetic-fixture',
                'compiled': 'reconstruction/synth/Synth.cpp', 'recipe': 'reconstruction/recipes/r.json',
                'symbols': 'task/symbols.json',
                'functions': [{'rva': self.task['rva'], 'size': self.task['size'], 'symbol': self.task['symbol']}],
                'files': files}
        spec.update(overrides)
        path = self.tmp / 'spec.json'
        path.write_text(json.dumps(spec))
        return path

    def run_build(self, mode='ok', spec=None, image=None, extra_env=None):
        env = dict(os.environ, FAKE_MODE=mode, FAKE_LOG=str(self.log), FAKE_OBJECT=str(self.object),
                   FAKE_TOOLCHAIN=str(self.msvc), SR_PREP_MARKER_DIR=str(self.tmp),
                   CL='/DINJECTED', _CL_='/FIinjected.h', INCLUDE='/somewhere/else', **(extra_env or {}))
        proc = subprocess.run([sys.executable, str(self.repo / 'tools/verifier/unit_build.py'), '--repo', str(self.repo),
                               '--spec', str(spec or self.spec()), '--msvc', str(self.msvc),
                               '--image', str(image or self.image), '--work', str(self.work)],
                              capture_output=True, text=True, env=env)
        return proc.returncode, proc.stdout

    def error(self):
        return json.loads((self.work / 'error.json').read_text())['status']

    def test_pass_records_environment_and_clears_flag_variables(self):
        code, out = self.run_build()
        self.assertEqual(code, 0, out)
        fdir = self.work / f'0x{self.task["rva"]:x}'
        report = json.loads((fdir / 'report.json').read_text())
        self.assertEqual((report['result'], report['reason']), ('pass', 'all-checks-passed'))
        env = json.loads((fdir / 'build-record.json').read_text())['environment']
        self.assertEqual((env['CL'], env['_CL_'], env['INCLUDE']), (None, None, self.include))
        self.assertEqual(env['show_includes']['repository_files'],
                         ['reconstruction/synth/Synth.cpp', 'reconstruction/synth/Synth.h'])
        seen = dict(line.split('=', 1) for line in (self.log / 'env.txt').read_text().splitlines() if '=' in line)
        self.assertNotIn('CL', seen)
        self.assertNotIn('_CL_', seen)
        self.assertEqual(seen.get('INCLUDE'), None)  # the fake cl does not source msvcenv.sh itself
        self.assertIn('/showIncludes', json.loads((self.work / 'compile-command.json').read_text()))
        self.assertNotIn(str(self.repo), out)
        # The second run in the same boot reuses the prep check.
        code, out = self.run_build()
        self.assertEqual(code, 0)
        self.assertIn('prep cached', out)

    def test_compiler_opening_a_file_outside_the_closure_fails(self):
        (self.repo / 'reconstruction/synth/Other.h').write_text('#pragma once\n')
        code, out = self.run_build('extra')
        self.assertEqual(code, 4)
        self.assertEqual(self.error(), 'include-closure-mismatch')
        self.assertIn('Other.h', out)

    def test_closure_include_the_compiler_never_opened_fails(self):
        (self.repo / 'reconstruction/synth/Other.h').write_text('#pragma once\n')
        (self.repo / 'reconstruction/synth/Synth.cpp').write_text('#include "Synth.h"\n/*\n#include "Other.h"\n*/\n')
        code, out = self.run_build('ok')
        self.assertEqual(code, 4)
        self.assertIn('did not open', out)

    def test_include_outside_repository_and_toolchain_fails(self):
        code, _ = self.run_build('outside')
        self.assertEqual(code, 4)
        self.assertEqual(self.error(), 'include-outside')

    def test_wrapper_include_outside_toolchain_fails(self):
        code, _ = self.run_build(extra_env={'FAKE_INCLUDE': 'z:\\home\\user\\repo'})
        self.assertEqual(code, 4)
        self.assertEqual(self.error(), 'include-env')

    def test_compile_failure_keeps_messages_off_stdout(self):
        code, out = self.run_build('fail')
        self.assertEqual(code, 3)
        self.assertNotIn('undeclared', out)
        self.assertIn('undeclared', (self.work / 'compile.log').read_text())

    def test_copy_must_match_spec(self):
        spec = self.spec()
        (self.repo / 'reconstruction/synth/Synth.h').write_text('#pragma once\nint changed;\n')
        code, _ = self.run_build(spec=spec)
        self.assertEqual(code, ub.EXIT_SYNC)

    def test_stale_files_are_removed_from_the_copy(self):
        spec = self.spec()
        (self.repo / 'reconstruction/synth/Stale.h').write_text('#pragma once\n')
        code, _ = self.run_build(spec=spec)
        self.assertEqual(code, 0)
        self.assertFalse((self.repo / 'reconstruction/synth/Stale.h').exists())

    def test_toolchain_and_image_checks(self):
        (self.msvc / 'bin/x64/cl.exe').write_bytes(b'another compiler')
        code, _ = self.run_build()
        self.assertEqual(code, ub.EXIT_TOOLCHAIN)
        (self.msvc / 'bin/x64/cl.exe').write_bytes(b'fake compiler binary')
        code, _ = self.run_build(image=self.tmp / 'private/missing.exe')
        self.assertEqual(code, ub.EXIT_IMAGE)
        self.assertTrue((self.tmp / 'private').is_dir())
        other = self.tmp / 'other.pe'
        other.write_bytes(b'not the image')
        code, _ = self.run_build(image=other)
        self.assertEqual(code, ub.EXIT_IMAGE)


if __name__ == '__main__':
    unittest.main()
