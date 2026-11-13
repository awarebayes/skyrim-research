"""Batch claims use synthetic public metadata and a fake gh; no network or game inputs."""
import contextlib
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import claims
import contrib
import work_queue as wq

BUILD = 'synthetic-build'
NOW = datetime.now(timezone.utc).isoformat()
PUBLIC = {'target_build_id': BUILD, 'functions': [
    {'build_id': BUILD, 'rva': r, 'size': 8, 'name': n, 'status': 'mapped'}
    for r, n in [(0x1000, 'Alpha::One'), (0x1020, 'Alpha::Two'), (0x2000, 'Beta::One')]]}


def raw(number=1, entries=((0x1000, 0x1001),), me='other', old=False, managed=False):
    text = claims.body(BUILD, entries, PUBLIC, me, managed=managed)
    return {'number': number, 'title': f'claim: {BUILD} Alpha (1 functions)', 'body': text,
            'user': {'login': 'creator'}, 'assignees': [{'login': me}], 'html_url': f'https://example/issues/{number}',
            'updated_at': (datetime.now(timezone.utc) - timedelta(days=15)).isoformat() if old else NOW}


class FakeGh:
    def __init__(self, rows=()):
        self.rows, self.writes, self.closed, self.calls = list(rows), [], [], []
        self.client = claims.GitHub(runner=self.run)

    def run(self, command, **kw):
        self.calls.append(command)
        args = command[1:]
        result = ''
        if args[:2] == ['api', 'user']:
            result = json.dumps({'login': 'project'})
        elif args[0] == 'api':
            result = json.dumps([] if '/timeline?' in args[1] else self.rows)
        elif args[:2] == ['issue', 'create']:
            number = max([i['number'] for i in self.rows] + [7]) + 1
            self.rows.append(dict(raw(number, me='project'), title=args[args.index('--title') + 1], body=kw['input']))
            self.writes.append(('create', number))
            result = f'https://example/issues/{number}'
        elif args[:2] == ['issue', 'edit']:
            number = int(args[2])
            issue = next(i for i in self.rows if i['number'] == number)
            issue['body'] = kw['input']
            issue['title'] = args[args.index('--title') + 1]
            issue['updated_at'] = datetime.now(timezone.utc).isoformat()
            self.writes.append(('edit', number))
        elif args[:2] == ['issue', 'comment']:
            number = int(args[2])
            next(i for i in self.rows if i['number'] == number)['updated_at'] = datetime.now(timezone.utc).isoformat()
            self.writes.append(('comment', number))
        elif args[:2] == ['issue', 'close']:
            number = int(args[2]); self.closed.append(number)
            self.rows = [i for i in self.rows if i['number'] != number]
        elif args[:2] != ['label', 'create']:
            raise AssertionError(command)
        return subprocess.CompletedProcess(command, 0, result, '')


class ClaimsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_old_title_and_new_block_share_parser(self):
        old = claims.parse_issue(dict(raw(), title=f'claim: {BUILD} 0x1020 Alpha::Two', body=''))
        new = claims.parse_issue(raw(entries=((0x1000, 0x1001), (0x2000, 0x2100))))
        index = claims.ClaimIndex([old, new], BUILD)
        self.assertEqual(len(index.get(0x1020)), 1)
        self.assertEqual(index.get(0x20ff)[0]['author'], 'other')
        self.assertFalse(index.get(0x2100))
        self.assertEqual(index.get(0x1000)[0]['number'], 1)
        self.assertFalse(claims.ClaimIndex([new], 'other-build').get(0x1000))

    def test_block_is_authoritative_over_title_and_names(self):
        issue = raw(entries=((0x2000, 0x2100),))
        issue['title'] += ' 0x9999'
        self.assertEqual(claims.parse_issue(issue)['entries'], [(0x2000, 0x2100)])

    def test_assignee_over_author_lapse_and_overlap(self):
        index = claims.ClaimIndex([claims.parse_issue(raw()), claims.parse_issue(raw(2, old=True))])
        self.assertEqual([i['number'] for i in claims.claimed(index, 0x1000)], [1])
        self.assertFalse(index.overlaps([(0x1000, 0x1002)], 'other'))
        self.assertEqual(len(index.overlaps([(0x0fff, 0x1001)], 'project')), 1)
        self.assertFalse(index.overlaps([(0x1001, 0x1002)], 'project'))

    def test_lapse_boundary_and_body_rule(self):
        now = datetime.now(timezone.utc)
        issue = claims.parse_issue(raw())
        issue['updated_at'] = (now - timedelta(hours=23)).isoformat()
        self.assertTrue(claims.live(issue, now))
        issue['updated_at'] = (now - timedelta(hours=24)).isoformat()
        self.assertFalse(claims.live(issue, now))
        self.assertIn('This claim lapses after 24 hours without activity (a comment, an update or a linked pull request); anyone may then take it over.', issue['body'])

    def test_publish_and_sync_keep_alive_only_active_and_only_once(self):
        for command in ('publish', 'sync'):
            with self.subTest(command=command):
                issues = [raw(8, me='project', managed=True), raw(9, entries=((0x1020, 0x1021),), me='project', managed=True),
                          raw(10, entries=((0x2000, 0x2001),), me='project', managed=True)]
                for issue in issues:
                    issue['updated_at'] = (datetime.now(timezone.utc) - timedelta(hours=13)).isoformat()
                issues[2]['updated_at'] = (datetime.now(timezone.utc) - timedelta(hours=11)).isoformat()
                fake = FakeGh(issues)
                groups = (BUILD, [([(0x1000, 0x1001)], {}), ([(0x1020, 0x1021)], {}), ([(0x2000, 0x2001)], {})])
                # Match the title generated by publish, avoiding a separate content update.
                for issue in issues:
                    entries = claims.parse_issue(issue)['entries']
                    issue['title'] = claims.parts(BUILD, entries, PUBLIC, 'project', True)[0][0]
                with patch.object(claims, 'collect', return_value=groups), \
                     patch.object(claims, 'active_entries', return_value=[(0x1000, 0x1001), (0x2000, 0x2001)]), \
                     patch.object(claims, 'git_json', return_value=PUBLIC), contextlib.redirect_stdout(io.StringIO()):
                    for _ in range(2):
                        if command == 'publish':
                            claims.publish(self.root, fake.client, PUBLIC)
                        else:
                            claims.sync(self.root, fake.client)
                self.assertEqual(fake.writes, [('comment', 8)])

    def test_active_entries_use_pipeline_and_planned_families(self):
        import flow
        (self.root / 'data').mkdir()
        (self.root / 'data/progress.json').write_text(json.dumps(PUBLIC))
        family = self.root / 'reports' / BUILD / 'families'
        family.mkdir(parents=True)
        (family / 'plan.json').write_text('{}')
        states = {'0x1000': {'state': 'queued'}, '0x1020': {'state': 'rejected'},
                  '0x2000': {'state': 'review-pending'}, '0x3000': {'state': 'pushed'}}
        with patch.object(claims, 'planned_family', return_value={0x4000}), \
                patch.object(flow, 'function_states', return_value=states):
            entries = claims.active_entries(self.root, PUBLIC)
        self.assertEqual(set(entries), {(0x1000, 0x1001), (0x2000, 0x2001), (0x4000, 0x4001)})

    def test_comment_and_linked_pr_extend_lapse(self):
        issue = raw(old=True)
        def api(_):
            return [{'event': 'cross-referenced', 'created_at': issue['updated_at'],
                     'source': {'issue': {'pull_request': {}, 'updated_at': NOW}}}]
        # The presence of pull_request identifies a PR even when its payload is empty.
        issue['updated_at'] = claims.activity(api, 'x/y', issue)
        self.assertTrue(claims.live(claims.parse_issue(issue)))

    def test_split_under_limit_round_trips_all_entries(self):
        entries = [(r, r + 1) for r in range(10000, 23000)]
        parts = claims.parts(BUILD, entries, PUBLIC, 'project')
        self.assertGreater(len(parts), 1)
        result = []
        for title, text, chunk in parts:
            self.assertLess(len(text), 60000)
            self.assertIn('part ', title)
            result += claims.parse_issue(dict(raw(), title=title, body=text))['entries']
        self.assertEqual(result, entries)
        with self.assertRaises(ValueError):
            claims.GitHub(runner=lambda *_a, **_kw: self.fail('must refuse before gh')).create('t', 'a' * 60000, 'project')

    def test_body_whitelist_ignores_private_fields_and_untracked_names(self):
        private = dict(PUBLIC['functions'][0], name='private decompiler name', disassembly='private assembly',
                       host='/private/machine', source='private source', targets=['private target'])
        text = claims.body(BUILD, [(private['rva'], private['rva'] + 1)], PUBLIC, 'project')
        self.assertIn('Alpha::One', text)
        for value in ['private decompiler name', 'private assembly', '/private/machine', 'private source', 'private target']:
            self.assertNotIn(value, text)
        private['name'] = 'Alpha::One\n```\nprivate source'
        text = claims.body(BUILD, [(0x1000, 0x1001)], dict(PUBLIC, functions=[private]), 'project')
        self.assertNotIn('private source', text)
        self.assertEqual(text.count('```'), 2)

    def test_cache_ttl_force_and_offline_fallback(self):
        fake = FakeGh([raw()])
        index, login = claims.cached(self.root, gh=fake.client)
        self.assertEqual(login, 'project')
        before = len(fake.calls)
        self.assertTrue(claims.cached(self.root, gh=fake.client)[0].get(0x1000))
        self.assertEqual(len(fake.calls), before)
        claims.cached(self.root, True, fake.client)
        self.assertGreater(len(fake.calls), before)
        for failure in (FileNotFoundError('gh'), RuntimeError('offline')):
            with patch.object(fake.client, 'user', side_effect=failure), contextlib.redirect_stderr(io.StringIO()) as err:
                index, login = claims.cached(self.root, True, fake.client)
            self.assertTrue(index.get(0x1000))
            self.assertIn('stale', err.getvalue())

    def test_publish_is_idempotent_and_dry_run_does_not_write(self):
        fake = FakeGh()
        groups = (BUILD, [([(0x1000, 0x1001), (0x2000, 0x2001)], {})])
        with patch.object(claims, 'collect', return_value=groups), contextlib.redirect_stdout(io.StringIO()):
            claims.publish(self.root, fake.client, PUBLIC, dry_run=True)
            self.assertFalse(fake.writes)
            claims.publish(self.root, fake.client, PUBLIC)
            claims.publish(self.root, fake.client, PUBLIC)
        self.assertEqual(fake.writes, [('create', 8)])
        create = next(c for c in fake.calls if c[1:3] == ['issue', 'create'])
        self.assertEqual(create[create.index('--assignee') + 1], 'project')
        self.assertIn('--label', create)

    def test_publish_skips_external_partial_overlap(self):
        fake = FakeGh([raw(entries=((0x1000, 0x1100),))])
        with patch.object(claims, 'collect', return_value=(BUILD, [([(0x1020, 0x1021), (0x2000, 0x2001)], {})])), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            claims.publish(self.root, fake.client, PUBLIC)
        self.assertIn('#1', err.getvalue())
        created = claims.parse_issue(fake.rows[-1])
        self.assertEqual(created['entries'], [(0x2000, 0x2001)])

    def test_sync_marks_done_then_closes_only_on_origin(self):
        fake = FakeGh([raw(8, me='project', managed=True)])
        public = json.loads(json.dumps(PUBLIC))
        public['functions'][0]['status'] = 'matched'
        with patch.object(claims, 'git_json', return_value=public) as read, contextlib.redirect_stdout(io.StringIO()):
            claims.sync(self.root, fake.client)
        read.assert_called_once_with(self.root, 'origin/main')
        self.assertEqual(fake.closed, [8])
        self.assertEqual(fake.writes, [('edit', 8)])

    def test_range_sync_never_closes_with_unknown_members(self):
        issue = raw(8, entries=((0x1000, 0x1100),), me='project', managed=True)
        issue['body'] = claims.body(BUILD, [(0x1000, 0x1100)], PUBLIC, 'project', total=3, managed=True)
        fake = FakeGh([issue])
        public = json.loads(json.dumps(PUBLIC))
        for fn in public['functions']:
            fn['status'] = 'matched'
        with patch.object(claims, 'git_json', return_value=public), contextlib.redirect_stdout(io.StringIO()):
            claims.sync(self.root, fake.client)
        self.assertFalse(fake.closed)
        self.assertIn('2 / 3', fake.rows[0]['body'])

    def test_sync_failure_is_nonfatal(self):
        with patch.object(claims, 'sync', side_effect=RuntimeError('offline')), contextlib.redirect_stderr(io.StringIO()) as err:
            claims.sync_safe(self.root)
        self.assertIn('integration remains successful', err.getvalue())

    def test_queue_add_and_next_skip_ranges_and_allow_project(self):
        q = self.root / '.local/queue/small'
        q.mkdir(parents=True)
        (q / 'queue.tsv').write_text('a\ta.cpp\t0x1000\t3\nb\tb.cpp\t0x2000\t3\n')
        external = claims.ClaimIndex([claims.parse_issue(raw(entries=((0x1000, 0x1100),)))])
        with patch.object(claims, 'project_claims', return_value=(external, 'project')), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(wq.claim(q, 'worker')['dir'], 'b')
            task = self.root / 'task';task.mkdir()
            (task / 'task.json').write_text(json.dumps({'compiled': 'a.cpp', 'max_attempts': 3, 'functions': [{'rva': '0x1000'}]}))
            self.assertFalse(wq.add(q, ['task'], self.root))
        self.assertIn('#1', err.getvalue())
        with patch.object(claims, 'project_claims', return_value=(external, 'other')):
            self.assertEqual(wq.claim(q, 'other-worker')['dir'], 'a')

    def test_contributor_refuses_partial_range_overlap_with_exit_six(self):
        index = claims.ClaimIndex([claims.parse_issue(raw(entries=((0x1010, 0x1030),)))])
        fake = FakeGh()
        # Contributor adapter uses the same parser/index and retains its existing exit codes.
        class Adapter:
            def open_items(self, refresh=False): return index
            def user(self): return 'project'
        ctx = contrib.Ctx(repo=self.root, private=self.root / '.local/contrib', github=Adapter(), as_json=True, interactive=False)
        with patch.object(contrib, 'inventory', return_value=PUBLIC), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(contrib.Stop) as error:
                contrib.cmd_claim(ctx, contrib.parser().parse_args(['claim', '--range', '0x1000-0x1040']))
        self.assertEqual(error.exception.code, 6)
        self.assertIn('#1', error.exception.message)

    def test_selection_combines_rvas_classes_lists_and_merged_ranges(self):
        file = self.root / 'functions.txt'
        file.write_text('# only metadata\n0x2000 ignored name\n')
        args = contrib.parser().parse_args(['claim', '0x1000', '--class', 'Alpha', '--list', str(file),
                                           '--range', '0x1000-0x1020', '--range', '0x1010-0x1030'])
        rows, entries = contrib.claim_selection(None, args, PUBLIC)
        self.assertEqual([f['rva'] for f in rows], [0x1000, 0x1020, 0x2000])
        self.assertEqual(entries, [(0x1000, 0x1030), (0x2000, 0x2001)])

    def test_range_total_includes_previously_accepted_members(self):
        public = json.loads(json.dumps(PUBLIC))
        public['functions'][0]['status'] = 'matched'
        plans = claims.parts(BUILD, [(0x1000, 0x1100)], public, 'project', counts={(0x1000, 0x1100): 2})
        self.assertIn('(2 functions)', plans[0][0])
        self.assertIn('Accepted on origin/main: 1 / 2', plans[0][1])

    def test_project_login_override_stays_local(self):
        (self.root / 'data').mkdir()
        (self.root / 'data/progress.json').write_text(json.dumps(PUBLIC))
        (self.root / '.local').mkdir()
        (self.root / '.local/claims-config.json').write_text(json.dumps({'project_login': 'override'}))
        with patch.object(claims, 'cached', return_value=(claims.ClaimIndex(), 'authenticated')):
            self.assertEqual(claims.project_claims(self.root)[1], 'override')

    def test_collect_queues_flow_families_and_static_ranges(self):
        q = self.root / '.local/queue/one'; q.mkdir(parents=True)
        (q / 'queue.tsv').write_text('a\ta.cpp\t0x1000,0x1020\t3\n')
        families = self.root / 'reports' / BUILD / 'families'; families.mkdir(parents=True)
        (families / 'one.json').write_text(json.dumps({'members': ['0x1020']}))
        clusters = self.root / 'clusters.json'
        clusters.write_text(json.dumps({'build_id': BUILD, 'clusters': [{'members': ['0x3000', '0x3010'],
                            'ranges': [{'start': '0x3000', 'end': '0x3020'}]}]}))
        import flow
        with patch.object(flow, 'function_states', return_value={'0x2000': {'state': 'confirmed'}}):
            build, groups = claims.collect(self.root, PUBLIC, cluster_lists=[clusters])
        self.assertEqual(build, BUILD)
        self.assertEqual(len(groups), 4)
        self.assertEqual(groups[1], ([(0x3000, 0x3020)], {(0x3000, 0x3020): 2}))
        all_entries = [e for entries, _counts in groups for e in entries]
        self.assertEqual(all_entries.count((0x1020, 0x1021)), 1)

    def test_takeover_comment_releases_only_its_overlapping_scope(self):
        issue = raw(entries=((0x1000, 0x1100),))
        event = {'created_at': NOW, 'body': 'Taking over.\n<!-- skyrim-claim-takeover-v1 0x1020-0x1040 -->'}
        claims.activity(lambda _path: [event], 'x/y', issue)
        index = claims.ClaimIndex([claims.parse_issue(issue)])
        self.assertTrue(index.get(0x101f))
        self.assertFalse(index.get(0x1020))
        self.assertFalse(index.get(0x103f))
        self.assertTrue(index.get(0x1040))

    def test_disjoint_takeover_does_not_remove_claim(self):
        issue = raw(entries=((0x1000, 0x1100),))
        issue['claim_takeovers'] = [(0x2000, 0x2100)]
        self.assertEqual(claims.parse_issue(issue)['entries'], [(0x1000, 0x1100)])


if __name__ == '__main__':
    unittest.main()
