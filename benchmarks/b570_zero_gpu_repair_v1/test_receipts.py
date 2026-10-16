"""Synthetic contract counterexamples. Never use these fixtures as host results."""
import copy
import unittest
from check_receipts import CASES, BASE_CHECKS, EXTRA_CHECKS, confirmation_order, judge, validate, load_json


def receipt(name='frozen_input', round_id=0):
    spec = CASES[name]
    checks = BASE_CHECKS | EXTRA_CHECKS.get(name, set())
    negative = spec['kind'] == 'negative'
    if negative:
        checks |= {'trigger_side_effect', 'detector_object_match'}
    keys = {'fixture', 'lifecycle', 'cleanup', 'watch', 'coverage'} | checks
    if negative:
        keys |= {'injection', 'detector'}
    result = dict(case_id=name, round=round_id, freeze_sha256='a'*64,
                  fixture_ready=True, control_point_reached=True, trigger_observed=negative,
                  early_failure=False, cleanup_complete=True, closed_ns=200,
                  planned_target_id='registered-object-1', no_work_after_detection=True,
                  detector=dict(code=spec['detector'],at_ns=150,fault_id=f'{round_id}:{name}',target_id='registered-object-1'),
                  verified={k:True for k in checks},
                  evidence={k:dict(path='raw/'+k+'.json',sha256='b'*64) for k in keys})
    if negative:
        result['trigger'] = dict(code=spec['trigger'],begin_ns=100,end_ns=160,fault_id=f'{round_id}:{name}',target_id='registered-object-1')
    return result


def panel():
    return dict(freeze_sha256='a'*64,receipts=[receipt(n,r) for r in range(3) for n in confirmation_order(r)])


class Counterexamples(unittest.TestCase):
    def test_complete_contract(self):
        p=panel();self.assertEqual(len(p['receipts']),57)
        self.assertEqual(validate(p)['status'],'RECEIPT_CONTRACT_PASS')
    def test_rejected_before_child_or_fault_is_not_pass(self):
        r=receipt();r['trigger_observed']=False
        self.assertEqual(judge(r)[0],'NOT_REACHED')
    def test_wrong_prior_sealed_slot_does_not_pass(self):
        r=receipt();r['detector']['target_id']='previous-slot'
        self.assertEqual(judge(r)[0],'WRONG_FAILURE')
    def test_generic_failed_does_not_pass(self):
        r=receipt();r['detector']['code']='FAILED'
        self.assertEqual(judge(r)[0],'WRONG_FAILURE')
    def test_earlier_unrelated_failure_not_overwritten(self):
        r=receipt();r['early_failure']=True
        self.assertEqual(judge(r)[0],'WRONG_FAILURE')
    def test_control_point_must_be_reached(self):
        r=receipt();r['control_point_reached']=False
        self.assertEqual(judge(r)[0],'NOT_REACHED')
    def test_receipt_order_is_not_operation_order(self):
        r=receipt();self.assertLess(r['detector']['at_ns'],r['trigger']['end_ns'])
        self.assertEqual(judge(r)[0],'PASS')
    def test_detector_cannot_precede_operation(self):
        r=receipt();r['detector']['at_ns']=99
        self.assertEqual(judge(r)[0],'WRONG_FAILURE')
    def test_wrong_fault_id(self):
        r=receipt();r['detector']['fault_id']='0:inactive_output'
        self.assertEqual(judge(r)[0],'WRONG_FAILURE')
    def test_wrong_injection(self):
        r=receipt();r['trigger']['code']='OTHER'
        self.assertEqual(judge(r)[0],'WRONG_FAILURE')
    def test_overflow_needs_all_acked_frames(self):
        r=receipt('log_overflow');r['verified']['all_ack_frames_retained']=False
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_overflow_needs_nonempty_ack(self):
        r=receipt('log_overflow');r['verified']['ack_nonempty']=False
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_watchdog_requires_independent_evidence(self):
        r=receipt('watcher_stall');del r['evidence']['independent_watchdog']
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_pending_close_needs_completion(self):
        r=receipt('terminal_pending_completion');r['verified']['pending_completion_observed']=False
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_transition_cannot_drop_sealed_guard(self):
        r=receipt('normal_transition');r['verified']['sealed_guard_continuous']=False
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_missing_raw_hash(self):
        r=receipt();r['evidence']['injection']['sha256']=''
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_path_traversal(self):
        r=receipt();r['evidence']['injection']['path']='../other.json'
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_timestamp_nan_or_bool(self):
        for value in [float('nan'),True,-1,1.5]:
            r=receipt();r['trigger']['begin_ns']=value
            self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_cleanup_required(self):
        r=receipt();r['cleanup_complete']=False
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_no_go_after_detection(self):
        r=receipt();r['no_work_after_detection']=False
        self.assertEqual(judge(r)[0],'WRONG_FAILURE')
    def test_missing_case(self):
        p=panel();p['receipts'].pop()
        self.assertEqual(validate(p)['status'],'RECEIPT_CONTRACT_FAIL')
    def test_duplicate_cannot_replace_failure(self):
        p=panel();p['receipts'][1]=copy.deepcopy(p['receipts'][0])
        self.assertEqual(validate(p)['status'],'RECEIPT_CONTRACT_FAIL')
    def test_retry_cannot_append(self):
        p=panel();p['receipts'].append(copy.deepcopy(p['receipts'][0]))
        self.assertEqual(validate(p)['status'],'RECEIPT_CONTRACT_FAIL')
    def test_outcome_selected_order(self):
        p=panel();p['receipts'][0],p['receipts'][1]=p['receipts'][1],p['receipts'][0]
        self.assertEqual(validate(p)['status'],'RECEIPT_CONTRACT_FAIL')
    def test_changed_freeze(self):
        p=panel();p['receipts'][-1]['freeze_sha256']='c'*64
        self.assertEqual(validate(p)['status'],'RECEIPT_CONTRACT_FAIL')
    def test_no_freeze(self):
        p=panel();p['freeze_sha256']=''
        self.assertEqual(validate(p)['status'],'RECEIPT_CONTRACT_FAIL')
    def test_missing_auxiliary_ledger(self):
        r=receipt();r['verified']['process_ledger']=False
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_fixture_not_raw_attestation(self):
        self.assertIn('no raw/Windows/ENGINEERING_READY',validate(panel())['scope'])
    def test_duplicate_json_keys_cannot_hide_failure(self):
        with self.assertRaises(ValueError):
            load_json('{"trigger_observed":false,"trigger_observed":true}')
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):
            load_json('{"at_ns":NaN}')
    def test_injection_cannot_outlive_closure(self):
        r=receipt();r['trigger']['end_ns']=201
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')
    def test_malformed_case_is_evidence_missing(self):
        r=receipt();r['case_id']=[]
        self.assertEqual(judge(r)[0],'EVIDENCE_MISSING')


if __name__=='__main__':
    unittest.main()
