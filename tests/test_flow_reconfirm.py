"""Synthetic queue recovery and record transport use the unchanged match gate."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import flow
import flow_lane as lane
import flow_reconfirm as recovery
from test_match_gate import GateFixture, RECORD


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)

    def test_finished_collection_deduplicates_and_caches_inventory_without_consuming_live_run(self):
        source=self.root/'input'
        lane.write(source/'data/progress.json',dict(functions=[dict(id='synthetic-0x10',build_id='synthetic',rva=16,
                   report='reports/synthetic/0x10.json')]))
        lane.write(source/'reports/synthetic/0x10.json',dict(source=dict(compiled='reconstruction/synthetic/A.cpp')))
        for name,state,reason in [('a','done','stale-sibling: needs re-confirm'),
                                  ('b','failed','origin changed selected inventory entries/carried files'),
                                  ('c','running','stale-sibling: needs re-confirm')]:
            lane.write(self.root/'lane/runs'/f'{name}.json',dict(id=name,state=state,items=[dict(id='item',root=str(source))],
                       dropped=[dict(reason=reason,request=dict(item='item',functions=['0x10']))]))
        with patch.object(lane,'owner_alive',return_value=False),patch.object(flow,'inventory',wraps=flow.inventory) as reads:
            result=recovery.collect(self.root)
        self.assertEqual(len(result),1);self.assertEqual(result[0]['receipt'],'b');self.assertEqual(reads.call_count,1)

    def test_live_owner_not_consumed(self):
        lane.write(self.root/'lane/runs/a.json',dict(id='a',state='failed',owner={'pid':1},dropped=[]))
        with patch.object(lane,'owner_alive',return_value=True),patch.object(flow,'inventory') as reads:
            self.assertEqual(recovery.collect(self.root),[])
        reads.assert_not_called()

    def test_three_way_merge_preserves_both_sides_and_conflict_is_held(self):
        base=b'one\ntwo\nthree\nfour\nfive\n'
        self.assertEqual(recovery.merge_bytes(base.replace(b'one',b'main'),base,base.replace(b'five',b'candidate')),
                         b'main\ntwo\nthree\nfour\ncandidate\n')
        with self.assertRaisesRegex(flow.FlowError,'merge conflict'):
            recovery.merge_bytes(b'main\n',b'base\n',b'candidate\n')

    def test_symlink_containment(self):
        outside=self.root/'outside';outside.write_text('synthetic')
        path=self.root/'reconstruction/synthetic.cpp';path.parent.mkdir();path.symlink_to(outside)
        with self.assertRaisesRegex(flow.FlowError,'escaping'):
            recovery.source_path(self.root,'reconstruction/synthetic.cpp')

    def test_standard_wake_packet(self):
        raw=bytes.fromhex('020000000001')
        self.assertEqual(recovery.wake_packet('02:00:00:00:00:01'),b'\xff'*6+raw*16)
        with self.assertRaises(flow.FlowError):recovery.wake_packet('02:00')

    def test_mismatch_is_never_retried_on_resume(self):
        task=self.root/'task';lane.write(task/'confirm/native/0x10/report.json',dict(result='mismatch'))
        state=dict(view=str(self.root),units={'unit':dict(task=str(task),phase='prepared',function_ids=[])},
                   targets=[],build_id='synthetic')
        with patch.object(recovery,'runner_preflight'),patch.object(recovery.af,'load',return_value=({'functions':[]},{})), \
             patch.object(recovery,'rollback_failed_units'),patch.object(recovery.subprocess,'run') as run:
            recovery.confirm(state,self.root)
        run.assert_not_called();self.assertEqual(state['units']['unit']['phase'],'held')
        self.assertIn('never retry',state['units']['unit']['reason'])

    def test_long_command_does_not_hold_flow_state_lock(self):
        with patch.object(flow,'execute',return_value=0),patch.object(flow,'state_lock',side_effect=AssertionError('long lock')):
            self.assertEqual(flow.main(['reconfirm-dropped','--dry-run']),0)

    def test_resume_clean_rerun_precedes_enqueue(self):
        lane.write(self.root/'reconfirm/synthetic/state.json',dict(id='synthetic',phase='review_pending',view=str(self.root)))
        calls=[]
        with patch.object(recovery,'clean_reruns',side_effect=lambda *_:calls.append('rerun')), \
             patch.object(recovery,'enqueue',side_effect=lambda *_:calls.append('enqueue')):
            result=recovery.execute(self.root,self.root,resume='synthetic')
        self.assertEqual(calls,['rerun','enqueue']);self.assertEqual(result['phase'],'review_pending')


class CompanionRecords(GateFixture,unittest.TestCase):
    def setUp(self):
        super().setUp();self.write('builds/target.json',json.dumps(self.target));self.fn['status']='mapped'
        self.write('data/progress.json',json.dumps(self.data))

    def test_companion_uses_real_gate_and_keeps_unmatched_status(self):
        request=dict(functions=['0x1010'],record_refresh=[self.fn['id']]);by_rva={'0x1010':self.fn}
        self.assertEqual(lane.refreshed_records(self.root,request,by_rva),[RECORD]);self.assertEqual(self.fn['status'],'mapped')
        broken=copy.deepcopy(self.record);broken['runs']=broken['runs'][:1];self.write(RECORD,json.dumps(broken))
        with self.assertRaisesRegex(ValueError,'at least 2 runs'):lane.refreshed_records(self.root,request,by_rva)

    def test_matched_companion_needs_own_review(self):
        self.fn['status']='matched'
        with self.assertRaisesRegex(flow.FlowError,'own review selection'):
            lane.refreshed_records(self.root,dict(functions=['0x1010'],record_refresh=[self.fn['id']]),{'0x1010':self.fn})

    def test_unrelated_unit_record_not_carried(self):
        other=dict(self.fn,id='unrelated',rva=32,report='reports/synthetic-fixture/0x20.json')
        record=copy.deepcopy(self.record);record['source']['compiled']='reconstruction/synthetic/Other.cpp'
        self.write(other['report'],json.dumps(record))
        self.assertEqual(lane.refreshed_records(self.root,dict(functions=['0x1010'],record_refresh=['unrelated']),
                                               {'0x1010':self.fn,'0x20':other}),[])

    def test_preparation_builds_main_based_tasks_and_batches_progress_writes(self):
        import subprocess
        def git(*args):
            return subprocess.check_output(['git','-C',str(self.root),*args],text=True).strip()
        self.write('.gitignore','.local/\n')
        git('init','--quiet','--initial-branch=main')
        git('config','user.name','Synthetic');git('config','user.email','synthetic@example.invalid')
        git('add','data','builds','reports','reconstruction','findings','tools','.gitignore')
        git('commit','--quiet','-m','original synthetic fixture')
        git('remote','add','origin',str(self.root))
        fdir=self.root/'.local/flow';fdir.mkdir(parents=True)
        state=dict(id='synthetic',branch='main',drops=[dict(function_id=self.fn['id'],root=str(self.root),compiled=self.record['source']['compiled'])])
        with patch.object(recovery,'link_inputs'),patch.object(flow,'carry_into_tree',wraps=flow.carry_into_tree) as carry:
            recovery.prepare(self.root,fdir,state)
        self.assertEqual(carry.call_count,1)
        self.assertEqual(state['targets'],[self.fn['id']])
        unit=state['units'][self.record['source']['compiled']]
        task=lane.read(Path(unit['task'])/'task.json')
        self.assertEqual(task['functions'][0]['rva'],self.fn['rva'])
        view=Path(state['view'])
        self.assertEqual((view/RECORD).read_bytes(),(self.root/RECORD).read_bytes())
        self.assertEqual(lane.read(view/'data/progress.json')['functions'][0]['status'],'mapped')
        git('worktree','remove','--force',str(view))
