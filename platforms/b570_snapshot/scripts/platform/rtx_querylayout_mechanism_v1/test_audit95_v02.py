"""Synthetic falsification of independent scientific endpoints; CPU only."""
import copy,itertools,json,unittest
import audit95_v02 as a

def row(t,arm,s,j):
    ids=[1]*128;o=dict(ids=ids,eog_flags=[False]*128,length=128,terminal_id=1,stop_reason='CAP',cached_tokens=0,truncated=False)
    w=dict(unsupported_replay=False,output_ids_count=128,prompt_ids_count=2,proposal_generated=0,proposal_verified=0,accepted_committed=0,first_mismatch_rejected=0,unexamined_after_mismatch=0,terminal_discarded=0,unverified_before_verify=0,initial_target_committed=1,bonus_committed=0,correction_committed=0,fallback_committed=127,accepted_prefix_hist={},cycle_progress_hist={},verification_caller_width_hist={},verify_cycles=0,verification_seed_rows=0,draft_continuation_calls=0,draft_continuation_rows=0,draft_proposal_rows=0,draft_catchup_rows=0,target_caller_width_hist={'1':127},target_continuation_rows=127,target_continuation_calls=127,target_physical_width_hist={'1':129},draft_physical_width_hist={},physical_micrograph_calls=129,physical_micrograph_rows=129,target_continuation_physical_width_hist={'1':127},target_prefill_physical_calls=2)
    c=dict(mask=0 if arm=='R' else 3,prefill_ub=1 if arm=='R' else 4,layout=arm.split('_')[-1])
    ms=2.0 if arm in ['M_PQ','C_PQ','M_GS','C_GS'] else 1.0
    obs=dict(mode='counts',phase_timers=False,heavy_capture=False,etw=False,added_sync=False,workload=w,feature_units={},scope_mask=c['mask'],target_ub=c['prefill_ub'],context=1024,effective_batch=1024)
    return dict(family='F',task=t,condition=arm,session=s,round=j,status='COMPLETED',warmup=False,phase='formal',measurement_mode='counts',observation={k:False for k in ['phase_timers','heavy_capture','etw','added_sync']},wall_ms=ms,request_start_ns=0,request_end_ns=int(ms*1e6),actual_condition=c,output=o,response=dict(tokens=ids,tokens_predicted=128,stop_type='limit',timings=dict(cache_n=0),hs_closeout=obs),workload=w,workload_error=None,feature_units={})
class Tests(unittest.TestCase):
    def setUp(self):
        self.tasks=[d+'/'+str(i) for d in ['MBPP','GSM8K'] for i in range(6)]
        self.plan=dict(families=['F'],P2_panel={'F':[dict(id=t) for t in self.tasks]})
        self.rows=[row(t,arm,s,j) for t,arm,s,j in itertools.product(self.tasks,a.ARMS,range(2),range(4))]
    def run_pairs(self,rr=None):return a.paired(self.rows if rr is None else rr,self.plan,{'F':{99}})['F']
    def test_complete_known_cost(self):
        r=self.run_pairs();self.assertTrue(all(q['qualified'] for q in r['qualification'].values()));self.assertEqual(r['comparisons'][0]['cost_ratio'],2.0)
    def test_missing_no_subset_estimate(self):
        r=self.run_pairs(self.rows[1:]);self.assertIsNone(r['comparisons'][0]['cost_ratio'])
    def test_duplicate_rejected(self):
        with self.assertRaises(AssertionError):self.run_pairs(self.rows+[self.rows[0]])
    def test_truncated_rejected(self):
        self.rows[0]['output']['truncated']=True
        with self.assertRaises(AssertionError):self.run_pairs()
    def test_false_eog_rejected(self):
        self.rows[0]['output']['eog_flags'][-1]=True
        with self.assertRaises(AssertionError):self.run_pairs()
    def test_observer_pollution_rejected(self):
        self.rows[0]['observation']['added_sync']=True
        with self.assertRaises(AssertionError):self.run_pairs()
    def test_full_native_mismatch_no_cost(self):
        r=next(x for x in self.rows if x['condition']=='M_PQ');r['output']['ids'][0]=2
        result=self.run_pairs();self.assertIsNone(result['comparisons'][0]['cost_ratio']);self.assertTrue(result['qualification']['M_PQ']['mismatches'])
    def test_unstable_reference_no_cost(self):
        self.rows[0]['output']['ids'][0]=2
        result=self.run_pairs();self.assertFalse(any(q['qualified'] for q in result['qualification'].values()))
    def test_counter_corruption_rejected(self):
        self.rows[0]['workload']['physical_micrograph_rows']+=1
        with self.assertRaises(AssertionError):self.run_pairs()
    def test_timer_scope_corruption_rejected(self):
        self.rows[0]['wall_ms']+=1
        with self.assertRaises(AssertionError):self.run_pairs()
    def test_unregistered_task_rejected(self):
        self.rows[0]['task']='MBPP/new'
        with self.assertRaises(AssertionError):self.run_pairs()
    def test_known_float_difference(self):
        import struct
        x=struct.pack('<ff',1.0,2.0);y=struct.pack('<II',0x3f800001,0x40000000)
        m=a.float_metrics(x,y);self.assertEqual(m['max_ULP'],1);self.assertEqual(m['equal_elements'],1);self.assertFalse(m['bitwise_equal'])
    def test_nonfinite_not_silently_equal(self):
        import struct
        m=a.float_metrics(struct.pack('<f',float('nan')),struct.pack('<f',1));self.assertEqual(m['nonfinite_pairs'],1);self.assertFalse(m['bitwise_equal'])
    def test_drop_slow_task_rejected(self):
        result=self.run_pairs([r for r in self.rows if r['task']!=self.tasks[-1]]);self.assertFalse(any(q['qualified'] for q in result['qualification'].values()))
if __name__=='__main__':unittest.main()
