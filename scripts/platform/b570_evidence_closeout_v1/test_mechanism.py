"""Synthetic CPU guards for leakage, timing closure and missing model evidence."""
import copy, hashlib, unittest
import closeout, mechanism
from test_closeout import D, PLATFORM, fixture

def calibration():
    rows=[]
    for family in D['families']:
        for arm in D['mechanism']['profile_arms']:
            spec=arm==D['mechanism']['candidate_arm']
            for task in D['mechanism']['calibration_task_ids']:
                units={n:0 for n in mechanism.features(D)}
                units.update(target_prefill_ids=10,reconcile_output_ids=4,request_channel=1)
                if spec:
                    units.update(draft_prefill_ids=10,draft_continuation_rows=4,rollback_calls=1)
                    units['target_continuation_calls_w'+str(4 if PLATFORM=='rtx' else 2)]=1
                else:units['target_continuation_calls_w1']=3
                spans={n:float(z)*2 for n,z in units.items()}
                rows.append({'slot':family+'/'+arm+'|'+task,'family':family,'condition':arm,'task':task,
                    'phase':'exposed_profile','profile_mode':'lite','actual_no_added_sync':True,
                    'completed_wall_partition':True,'on_off_raw_equal':True,
                    'source_identity_sha256':hashlib.sha256(family.encode()).hexdigest(),
                    'raw_evidence_sha256':'b'*64,'feature_units':units,'component_ms':spans,'wall_ms':sum(spans.values())})
    return {'rows':rows}

def prediction_record():
    family=D['families'][0];arm=D['mechanism']['candidate_arm'];w=4 if PLATFORM=='rtx' else 2
    # One generated/accepted proposal plus a terminal-discarded proposal: not all P-A rejected.
    work={'prompt_ids_count':10,'output_ids_count':3,'proposal_generated':w-1,'proposal_verified':w-1,
          'accepted_committed':1,'first_mismatch_rejected':0,'unexamined_after_mismatch':0,
          'terminal_discarded':w-2,'unverified_before_verify':0,'initial_target_committed':1,
          'bonus_committed':1,'correction_committed':0,'fallback_committed':0,'verify_cycles':1,
          'verification_seed_rows':1,'draft_continuation_calls':3,'draft_continuation_rows':3,
          'rollback_calls':1,'counter_semantics_sha256':'c'*64,'accepted_prefix_hist':{'1':1},
          'cycle_progress_hist':{'2':1},'verification_caller_width_hist':{str(w):1}}
    units={n:0 for n in mechanism.features(D)}
    units.update(target_prefill_ids=10,draft_prefill_ids=10,draft_continuation_rows=3,
                 reconcile_output_ids=3,rollback_calls=1,request_channel=1)
    units['target_continuation_calls_w'+str(w)]=1
    return {'family':family,'condition':arm,'output':{'length':3},'workload':work,'feature_units':units,
            'source_identity_sha256':hashlib.sha256(family.encode()).hexdigest()}

class MechanismGuards(unittest.TestCase):
    def test_complete_frozen_model_is_checked_on_full_task_session_panel(self):
        i,p,f,rr=fixture();m=mechanism.calibrate(D,calibration())
        f.update(model_sha256=closeout.digest(m),model_frozen_before_first_formal=True)
        width=4 if PLATFORM=='rtx' else 2
        for row in rr:
            spec=row['condition']==D['mechanism']['candidate_arm']
            cycles=32 if width==4 else 64
            accepted=95 if width==4 else 63
            work={'prompt_ids_count':2,'output_ids_count':128,'proposal_generated':cycles*(width-1) if spec else 0,
                'proposal_verified':cycles*(width-1) if spec else 0,'accepted_committed':accepted if spec else 0,
                'first_mismatch_rejected':0,'unexamined_after_mismatch':0,'terminal_discarded':1 if spec else 0,
                'unverified_before_verify':0,'initial_target_committed':1,'bonus_committed':cycles if spec else 0,
                'correction_committed':0,'fallback_committed':0 if spec else 127,
                'verify_cycles':cycles if spec else 0,'verification_seed_rows':cycles if spec else 0,
                'draft_continuation_calls':128 if spec else 0,'draft_continuation_rows':128 if spec else 0,
                'rollback_calls':cycles if spec else 0,'counter_semantics_sha256':'c'*64,
                'accepted_prefix_hist':{str(width-1):cycles-1,str(width-2):1} if spec else {},
                'cycle_progress_hist':{str(width):cycles-1,str(width-1):1} if spec else {},
                'verification_caller_width_hist':{str(width):cycles} if spec else {}}
            units={n:0 for n in mechanism.features(D)}
            units.update(target_prefill_ids=2,draft_prefill_ids=2 if spec else 0,
                draft_continuation_rows=128 if spec else 0,reconcile_output_ids=128,
                rollback_calls=cycles if spec else 0,request_channel=1)
            units['target_continuation_calls_w'+str(width if spec else 1)]=cycles if spec else 127
            row.update(workload=work,feature_units=units,
                       source_identity_sha256=hashlib.sha256(row['family'].encode()).hexdigest())
            if row['condition'] in D['mechanism']['profile_arms']:
                row['wall_ms']=mechanism.predict(D,m,row)['predicted_wall_ms']
        out=mechanism.analyse(D,p,i,rr,f,m)
        for panel in out['model_validation']:
            self.assertEqual(panel['expected'],96);self.assertEqual(panel['covered'],96)
            self.assertEqual(panel['MAPE'],0)
            self.assertTrue(all(d['direction_accuracy']==1.0 for d in panel['directions']))
            self.assertEqual(panel['status'],'PASS' if PLATFORM=='rtx' else 'EVIDENCE_NOT_QUALIFIED')
        row=next(r for r in rr if r['condition']==D['mechanism']['candidate_arm'])
        del row['feature_units']
        out=mechanism.analyse(D,p,i,rr,f,m)
        panel=next(x for x in out['model_validation'] if x['family']==row['family'] and x['domain']==row['task'].split('/')[0])
        self.assertEqual(panel['status'],'INCOMPLETE');self.assertIsNone(panel['MAPE'])

    def test_fresh_confirmation_task_cannot_fit(self):
        c=calibration();c['rows'][0]['task']='MBPP/fresh'
        with self.assertRaises(AssertionError):mechanism.calibrate(D,c)

    def test_formal_cost_cannot_fit(self):
        c=calibration();c['rows'][0]['phase']='formal'
        with self.assertRaises(AssertionError):mechanism.calibrate(D,c)

    def test_heavy_sync_cost_cannot_fit(self):
        c=calibration();c['rows'][0]['profile_mode']='heavy'
        with self.assertRaises(AssertionError):mechanism.calibrate(D,c)

    def test_new_sync_or_nonclosing_wall_is_rejected(self):
        for key,val in (('actual_no_added_sync',False),('wall_ms',1.0)):
            c=calibration();c['rows'][0][key]=val
            with self.assertRaises(AssertionError):mechanism.calibrate(D,c)

    def test_duplicate_calibration_cannot_hide_missing_task(self):
        c=calibration();c['rows'][1]=copy.deepcopy(c['rows'][0])
        with self.assertRaises(AssertionError):mechanism.calibrate(D,c)

    def test_negative_component_or_zero_work_cost_is_rejected(self):
        c=calibration();c['rows'][0]['component_ms']['request_channel']=-1
        with self.assertRaises(AssertionError):mechanism.calibrate(D,c)
        c=calibration();r=c['rows'][0];r['component_ms']['draft_prefill_ids']=1;r['wall_ms']+=1
        with self.assertRaises(AssertionError):mechanism.calibrate(D,c)

    def test_unseen_width_is_not_zero_cost(self):
        m=mechanism.calibrate(D,calibration());r=prediction_record()
        k='target_continuation_calls_w'+str(4 if PLATFORM=='rtx' else 2)
        m['coefficients_ms_per_unit'][r['family']][r['condition']][k]=None
        p=mechanism.predict(D,m,r)
        self.assertEqual(p['status'],'UNSUPPORTED_SHAPE');self.assertIsNone(p['predicted_wall_ms'])

    def test_unused_proposals_are_not_all_rejected(self):
        r=prediction_record();r['workload'].update(proposal_generated=2,proposal_verified=1,
            terminal_discarded=1,verification_caller_width_hist={'2':1})
        v=mechanism.workload_metrics(r['workload'],3)
        self.assertEqual(v['acceptance_per_generated'],0.5)
        self.assertEqual(v['acceptance_per_verified'],1.0)
        self.assertEqual(r['workload']['first_mismatch_rejected'],0)

    def test_raw_output_and_proposal_conservation_are_checked(self):
        r=prediction_record()
        with self.assertRaises(AssertionError):mechanism.workload_metrics(r['workload'],4)
        r['workload']['proposal_generated']+=1
        with self.assertRaises(AssertionError):mechanism.workload_metrics(r['workload'],3)

    def test_runtime_identity_drift_is_not_model_success(self):
        c=calibration();c['rows'][1]['source_identity_sha256']='d'*64
        with self.assertRaises(AssertionError):mechanism.calibrate(D,c)
        m=mechanism.calibrate(D,calibration());r=prediction_record();r['source_identity_sha256']='d'*64
        self.assertEqual(mechanism.predict(D,m,r)['status'],'IDENTITY_MISMATCH')

    def test_confirmation_refit_or_negative_coefficient_is_rejected(self):
        m=mechanism.calibrate(D,calibration());m['fit_on_confirmation']=True
        with self.assertRaises(AssertionError):mechanism.validate_model(D,m)
        m=mechanism.calibrate(D,calibration());f=D['families'][0];a=D['mechanism']['profile_arms'][0]
        m['coefficients_ms_per_unit'][f][a]['request_channel']=-1
        with self.assertRaises(AssertionError):mechanism.validate_model(D,m)

    def test_missing_workload_does_not_erase_primary_cost(self):
        i,p,f,rr=fixture();m=mechanism.calibrate(D,calibration())
        f.update(model_sha256=closeout.digest(m),model_frozen_before_first_formal=True)
        out=mechanism.analyse(D,p,i,rr,f,m)
        self.assertTrue(all(z['status']=='INCOMPLETE' for z in out['model_validation']))
        self.assertTrue(out['primary_cost_and_output']['families'][D['families'][0]]['qualification'][D['mechanism']['candidate_arm']]['native_qualified'])
        if PLATFORM=='rtx':
            self.assertTrue(out['primary_cost_and_output']['families'][D['families'][0]]['qualification']['C3']['qualified'])
        else:
            self.assertFalse(out['primary_cost_and_output']['physical_residency_gate'])

    def test_late_or_changed_model_seal_is_rejected(self):
        i,p,f,rr=fixture();m=mechanism.calibrate(D,calibration())
        for model_hash,early in (('f'*64,True),(closeout.digest(m),False)):
            ff=dict(f,model_sha256=model_hash,model_frozen_before_first_formal=early)
            with self.assertRaises(AssertionError):mechanism.analyse(D,p,i,rr,ff,m)

if __name__=='__main__':unittest.main()
