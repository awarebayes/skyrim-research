"""tools/ci_status.py against a stubbed gh: exit codes, failed-step names, waiting and JSON output."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import ci_status  # noqa: E402

SHA = 'a' * 40
OTHER = 'b' * 40
# The stub answers `gh run list` from list.json and `gh run view <id>` from view-<id>.json in the
# directory named by CI_STUB_DIR; a file named `broken` makes it fail like an unauthenticated gh.
STUB = '''import json, os, pathlib, sys
d = pathlib.Path(os.environ['CI_STUB_DIR'])
if (d / 'broken').exists():
    sys.exit('gh: not logged in')
calls = d / 'calls'
n = int(calls.read_text()) if calls.exists() else 0
calls.write_text(str(n + 1))
args = sys.argv[1:]
if args[:2] == ['run', 'list']:
    lists = sorted(d.glob('list*.json'))
    print(lists[min(n, len(lists) - 1)].read_text())
elif args[:2] == ['run', 'view']:
    print((d / f'view-{args[2]}.json').read_text())
else:
    sys.exit('unexpected gh call ' + ' '.join(args))
'''


def run(rid, workflow, status='completed', conclusion='success', sha=SHA):
    return {'databaseId': rid, 'workflowName': workflow, 'status': status,
            'conclusion': conclusion if status == 'completed' else '', 'headSha': sha}


class CiStatusTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        exe = self.dir / 'gh'
        exe.write_text(f'#!{sys.executable}\n{STUB}')
        exe.chmod(0o755)
        env = mock.patch.dict(os.environ, {'CI_STATUS_GH': str(exe), 'CI_STUB_DIR': str(self.dir)})
        env.start()
        self.addCleanup(env.stop)

    def runs(self, *runs, name='list.json'):
        (self.dir / name).write_text(json.dumps(list(runs)))

    def jobs(self, rid, *jobs):
        (self.dir / f'view-{rid}.json').write_text(json.dumps({'jobs': list(jobs)}))

    def main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ci_status.main(['--commit', SHA, *argv])
        return code, out.getvalue(), err.getvalue()

    def test_all_green(self):
        self.runs(run(1, 'Infrastructure checks'), run(2, 'Publish research report'))
        code, out, _ = self.main()
        self.assertEqual(code, ci_status.GREEN)
        self.assertTrue(out.startswith('GREEN'))

    def test_red_names_the_failed_step(self):
        self.runs(run(1, 'Infrastructure checks', conclusion='failure'), run(2, 'Publish research report'))
        self.jobs(1, {'name': 'check', 'conclusion': 'failure', 'steps': [
            {'name': 'Run python3 tools/check.py', 'conclusion': 'success'},
            {'name': 'Run python3 -m unittest discover -s tests -v', 'conclusion': 'failure'},
            {'name': 'Run python3 tools/build_site.py', 'conclusion': 'skipped'}]})
        code, out, _ = self.main()
        self.assertEqual(code, ci_status.RED)
        self.assertIn('failed: check / Run python3 -m unittest discover -s tests -v', out)
        self.assertNotIn('build_site', out)

    def test_red_wins_over_pending(self):
        self.runs(run(1, 'A', conclusion='cancelled'), run(2, 'B', status='in_progress'))
        self.jobs(1, {'name': 'job', 'conclusion': 'cancelled', 'steps': []})
        code, out, _ = self.main()
        self.assertEqual(code, ci_status.RED)
        self.assertIn('failed: job', out)

    def test_pending_and_no_runs(self):
        self.runs(run(1, 'A'), run(2, 'B', status='queued'))
        self.assertEqual(self.main()[0], ci_status.PENDING)
        self.runs(run(3, 'A', sha=OTHER))  # runs of another commit do not count
        code, out, _ = self.main()
        self.assertEqual(code, ci_status.PENDING)
        self.assertIn('no workflow runs yet', out)

    def test_wait_polls_until_finished(self):
        self.runs(run(1, 'A', status='in_progress'), name='list0.json')
        self.runs(run(1, 'A'), name='list1.json')
        with mock.patch.object(ci_status.time, 'sleep') as sleep:
            code, _, _ = self.main('--wait', '600')
        self.assertEqual(code, ci_status.GREEN)
        self.assertEqual(sleep.call_count, 1)

    def test_no_wait_reports_pending_once(self):
        self.runs(run(1, 'A', status='in_progress'))
        with mock.patch.object(ci_status.time, 'sleep') as sleep:
            self.assertEqual(self.main()[0], ci_status.PENDING)
        sleep.assert_not_called()

    def test_json_output(self):
        self.runs(run(1, 'A'))
        code, out, _ = self.main('--json')
        self.assertEqual(code, ci_status.GREEN)
        record = json.loads(out)
        self.assertEqual(record['result'], 'green')
        self.assertEqual(record['runs'][0]['run_id'], 1)

    def test_gh_failing_or_missing_is_unavailable(self):
        (self.dir / 'broken').write_text('')
        code, out, err = self.main()
        self.assertEqual(code, ci_status.UNAVAILABLE)
        self.assertIn('not logged in', err)
        self.assertEqual(out, '')
        with mock.patch.dict(os.environ, {'CI_STATUS_GH': str(self.dir / 'absent')}):
            self.assertEqual(self.main()[0], ci_status.UNAVAILABLE)


if __name__ == '__main__':
    unittest.main()
