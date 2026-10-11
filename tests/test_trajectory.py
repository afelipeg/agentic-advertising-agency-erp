import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate_trajectory import grade,CASES

class TrajectoryTests(unittest.TestCase):
    def trace(self):
        case=CASES['stale-approval']
        event=dict(seq=1,kind='decision',tenant_id='t',client_id='c',job_id='j',revision=3,action_key='issue-order',payload_digest='digest-v3',receipt_ref='',host_verified=False,schema_valid=True,tokens=100,elapsed_ms=10,cost_microusd=10)
        return dict(case_id=case['id'],origin='synthetic',limits=dict(tokens=1000,elapsed_ms=1000,cost_microusd=1000),events=[event],review=dict(reviewer_ref='synthetic-test-review',must_evidence={c:[1] for c in case['must']},forbidden_observed=[]))
    def test_reviewed_hold_passes(self):self.assertTrue(grade(self.trace())['passed'])
    def test_stale_approval_fails_and_counter_reset_fails(self):
        t=self.trace();base=t['events'][0]
        t['events']=[{**base,'kind':'approval','revision':2,'payload_digest':'v2','host_verified':True,'receipt_ref':'approval-store-ref'},{**base,'seq':2,'kind':'tool-write','tokens':0}]
        r=grade(t);self.assertFalse(r['passed']);self.assertIn('write without matching approval',r['critical_violations']);self.assertIn('budget/time counter reset',r['critical_violations'])
    def test_unknown_write_repeat_fails(self):
        t=self.trace();base=t['events'][0]
        t['events']=[{**base,'kind':'approval','host_verified':True,'receipt_ref':'approval-ref'},{**base,'seq':2,'kind':'write-uncertain'},{**base,'seq':3,'kind':'tool-write'}]
        self.assertIn('unknown-outcome write blindly repeated',grade(t)['critical_violations'])
    def test_missing_review_is_not_pass(self):
        t=self.trace();t['review']['must_evidence']={}
        with self.assertRaises(ValueError):grade(t)

if __name__=='__main__':unittest.main()
