"""Artificial byte-fixture tests only; not neural model/GPU qualification."""
import copy,hashlib,json,struct,tempfile,unittest
from pathlib import Path
import replay_audit as A

ID={'reference_deployment_sha256':hashlib.sha256(b'artificial-reference').hexdigest(),'candidate_deployment_sha256':hashlib.sha256(b'artificial-candidate').hexdigest(),
 'target_model_sha256':hashlib.sha256(b'artificial-model').hexdigest(),'tokenizer_sha256':hashlib.sha256(b'artificial-tokenizer').hexdigest(),'vocab':16,'n_ctx':128,
 'candidate_target_ubatch':1,'candidate_prefill_recipe':'whole_prompt_last_only','reference_recipe':'tokenwise_all','binding_complete':True,'eog_ids':[],'kv_bytes_per_token':4,'state_format':'synthetic-token-state-v1','scope':'CPU_SYNTHETIC_BYTE_FIXTURE_ONLY'}
def vec(p):
    best=int(hashlib.sha256(bytes(p)).hexdigest(),16)%16
    return [float(100+len(p)) if i==best else float(-i-len(p)) for i in range(16)]
def pick(p):return A.argmax(vec(p))
def case(rej=3,cap=9,stop=0):
    prompt=[1,2,3];h=prompt.copy();out=[pick(h)];pending=out[0];rows=[]
    def done():return len(out)==cap or (stop>0 and len(out)==stop)
    while not done():
        base=len(h);seed=pending;v=[seed];props=[]
        for j in range(3):
            token=pick(h+v)
            if j==rej:token=(token+1)%16
            props.append(token);v.append(token)
        dec=[pick(h+v[:i+1]) for i in range(4)];acc=0;last=None
        for j in range(3):
            if done():break
            if props[j]==dec[j]:acc+=1;out.append(props[j]);last='accepted'
            else:pending=dec[j];out.append(pending);last='correction';break
        if acc==3 and not done():pending=dec[3];out.append(pending);last='bonus'
        h+=v[:1+acc]
        rows.append({'base':base,'seed':seed,'proposals':props,'decisions':dec,'accepted':acc,'last':last,'keep':len(h),'pending':None if done() else pending})
    return {'ids':out,'cycles':rows,'cap':cap,'target_ubatch':1,'forced_reject_index':rej,'stop_after_output_index':stop,'stop_is_synthetic_eog_predicate':True}
def put(root,b):
    h=hashlib.sha256(b).hexdigest();p=root/(h+'.bin');p.write_bytes(b)
    return {'path':p.name,'sha256':h,'bytes':len(b)}
def lv(root,p):return put(root,struct.pack('<16f',*vec(p)))
def kv(root,p):return put(root,struct.pack('<'+'i'*len(p),*p))
def bundle(root,c=None):
    c=c or case();plan=A.make_plan(c,[1,2,3],ID);qs={q['query_id']:q for q in plan['queries']}
    e={'candidate_identity':ID['candidate_deployment_sha256'],'reference_identity':ID['reference_deployment_sha256'],
       'state_format':ID['state_format'],'reference_jobs':{},'candidate_rows':{},'reference_queries':{},'candidate_commits':{}}
    for q in qs.values():
        p=q['tokens'];e['reference_queries'][q['query_id']]={'mode':'forced_prefix','fresh_context':True,'start_empty':True,
          'decoded_tokens':p,'positions':list(range(len(p))),'sequence_id':0,'caller_widths':[1]*len(p),'physical_ubatches':[1]*len(p),'logits_masks':[[True]]*len(p),'logits':lv(root,p),'kv':kv(root,p)}
        for name in q['capture_uses']:e['candidate_rows'][name]={'query_id':q['query_id'],'producer':copy.deepcopy(next(u['producer'] for u in plan['uses'] if u['use_id']==name)),'logits':lv(root,p)}
    for job in plan['fresh_replay_jobs']:
        e['reference_jobs'][job['job_id']]={'start_empty':True,'status':'COMPLETED','tokens':job['tokens'],'execution':A.reference_metadata(job['tokens'],3,ID),
          'observations':{qid:copy.deepcopy(e['reference_queries'][qid]) for qid in job['query_ids']}}
    for s in plan['commits']:
        d=copy.deepcopy(s);d['kv']=kv(root,s['tokens']);d['frontier_logits']=e['candidate_rows'][s['frontier_logits_use']]['logits'];e['candidate_commits'][s['commit_id']]=d
    prefixes=[[1,2,3]+c['ids'][:i] for i in range(len(c['ids']))]
    e['free_scalar_run']={'mode':'autonomous_scalar','forced_tokens_used':False,'fresh_context':True,'start_empty':True,'sequence_id':0,'decoded_tokens':[1,2,3]+c['ids'][:-1],'positions':list(range(3+len(c['ids'])-1)),'caller_widths':[1]*(3+len(c['ids'])-1),'physical_ubatches':[1]*(3+len(c['ids'])-1),'logits_masks':[[True]]*(3+len(c['ids'])-1),'prompt_ids':[1,2,3],
      'cap':c['cap'],'stop_contract':{'cap':c['cap'],'eog_ids':[],'synthetic_stop_after':c.get('stop_after_output_index',0)},'stop_reason':'CAP' if len(c['ids'])==c['cap'] else 'SYNTHETIC_STOP','prefixes':prefixes,'output':c['ids'],'eog_flags':[False]*len(c['ids']),'logits':[lv(root,p) for p in prefixes]}
    return plan,e
class Tests(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.p,self.e=bundle(self.root)
    def tearDown(self):self.t.cleanup()
    def reject(self,needle):
        with self.assertRaisesRegex(A.EvidenceError,needle):A.audit(self.p,self.e,self.root,ID)
    def test_complete_byte_fixture(self):self.assertEqual(A.audit(self.p,self.e,self.root,ID)['status'],'RECORDED_EVIDENCE_MATCH')
    def test_all_termination_branch_plans(self):
        for r in [0,1,2,3]:
            for cap in [1,2,5,9]:
                p,e=bundle(self.root,case(r,cap));A.audit(p,e,self.root,ID)
        for stop in [1,2,3,4,5]:
            p,e=bundle(self.root,case(3,9,stop));A.audit(p,e,self.root,ID)
    def test_terminal_pending_is_not_next_loop_pending(self):
        for r,cap,want in [(3,1,1),(0,2,1),(3,5,1),(3,2,0)]:
            p=A.make_plan(case(r,cap),[1,2,3],ID);s=p['commits'][-1]
            self.assertIsNone(s['pending_for_next_loop']);self.assertEqual(len(s['unmaterialized_output']),want)
    def test_accepted_stop_frontier_is_not_row3(self):
        p=A.make_plan(case(3,2),[1,2,3],ID);self.assertEqual(p['commits'][-1]['frontier_logits_use'],'cycle-0-row-1')
    def test_missing_unexamined_row(self):
        del self.e['candidate_rows']['cycle-0-row-3'];self.reject('missing/extra candidate rows')
    def test_one_bit_non_argmax_difference(self):
        row=self.e['candidate_rows']['initial'];b=bytearray((self.root/row['logits']['path']).read_bytes());b[0]^=1;row['logits']=put(self.root,b);self.reject('vector bytes differ')
    def test_wrong_prefix_identity(self):
        self.e['candidate_rows']['initial']['query_id']='bad';self.reject('wrong row/prefix')
    def test_terminal_unmaterialized_token_erasure(self):
        self.e['candidate_commits'][self.p['commits'][-1]['commit_id']]['unmaterialized_output']=[];self.reject('semantic metadata mismatch')
    def test_wrong_state_format_is_unproven(self):
        self.e['state_format']='different-serializer';self.reject('UNPROVEN')
    def test_lost_state_even_if_claimed_hash_updated(self):
        d=self.e['candidate_commits']['cycle-0'];n=d['kv']['bytes'];d['kv']=put(self.root,bytes(n));self.reject('active KV bytes differ')
    def test_stale_frontier_logits(self):
        p,e=bundle(self.root,case(0,2));self.p,self.e=p,e
        e['candidate_commits']['cycle-0']['frontier_logits']=e['candidate_rows']['cycle-0-row-3']['logits'];self.reject('wrong saved frontier')
    def test_reference_is_not_fresh(self):
        next(iter(self.e['reference_queries'].values()))['fresh_context']=False;self.reject('reference execution metadata differs')
    def test_reference_scalar_width_violation(self):
        next(iter(self.e['reference_queries'].values()))['caller_widths'][0]=2;self.reject('reference execution metadata differs')
    def test_reference_identity_swapped(self):
        self.e['reference_identity']='x'*64;self.reject('reference identity')
    def test_free_run_is_forced(self):
        self.e['free_scalar_run']['forced_tokens_used']=True;self.reject('teacher-forced')
    def test_free_run_prefix_wrong(self):
        self.e['free_scalar_run']['prefixes'][0]=[1];self.reject('free-run prefixes')
    def test_free_run_non_argmax_mutation(self):
        b=bytearray((self.root/self.e['free_scalar_run']['logits'][0]['path']).read_bytes());b[0]^=1
        self.e['free_scalar_run']['logits'][0]=put(self.root,b);self.reject('free and forced scalar R vectors differ')
    def test_free_run_stop_contract_mutation(self):
        self.e['free_scalar_run']['stop_contract']['cap']=99;self.reject('stop contract differs')
    def test_zero_kv_contract_is_unproven(self):
        bad=copy.deepcopy(ID);bad['kv_bytes_per_token']=0
        with self.assertRaisesRegex(A.EvidenceError,'zero or invalid KV'):A.audit(self.p,self.e,self.root,bad)
    def test_free_run_not_start_empty(self):
        self.e['free_scalar_run']['start_empty']=False;self.reject('initial/sequence state differs')
    def test_free_run_width_not_scalar(self):
        self.e['free_scalar_run']['caller_widths'][0]=4;self.reject('free-run producer recipe differs')
    def test_prompt_boundary_changes_query_identity(self):
        self.assertNotEqual(A.query_id([1,2,3,4],ID,2),A.query_id([1,2,3,4],ID,3))
    def test_historical_prompt_recipe_not_silently_replaced(self):
        historical=copy.deepcopy(ID);historical['reference_recipe']='historical_prefill_then_scalar'
        self.assertEqual(A.reference_widths(5,3,historical),[3,1,1])
        self.assertNotEqual(A.query_id([1,2,3,4],ID,3),A.query_id([1,2,3,4],historical,3))
    def test_maximal_paths_cover_without_candidate_state_restore(self):
        p=A.make_plan(case(3,9),[1,2,3],ID)
        self.assertEqual(len(p['fresh_replay_jobs']),1)
        self.assertEqual(set(p['fresh_replay_jobs'][0]['query_ids']),{q['query_id'] for q in p['queries']})
    def test_reject_paths_capture_each_query_once_by_default(self):
        p=A.make_plan(case(0,9),[1,2,3],ID)
        assigned=[k for j in p['fresh_replay_jobs'] for k in j['query_ids']]
        self.assertEqual(len(assigned),len(set(assigned)))
        self.assertEqual(set(assigned),{q['query_id'] for q in p['queries']})
        self.assertLess(len(assigned),sum(len(j['available_query_ids']) for j in p['fresh_replay_jobs']))
    def test_optional_duplicate_reference_is_checked(self):
        p,e=bundle(self.root,case(0,5));self.p,self.e=p,e
        j=next(j for j in p['fresh_replay_jobs'] if len(j['query_ids'])<len(j['available_query_ids']))
        qid=next(k for k in j['available_query_ids'] if k not in j['query_ids'])
        obs=copy.deepcopy(e['reference_queries'][qid]);b=bytearray((self.root/obs['logits']['path']).read_bytes());b[0]^=1;obs['logits']=put(self.root,b)
        e['reference_jobs'][j['job_id']]['observations'][qid]=obs;self.reject('duplicate fresh-R prefix observations disagree')
    def test_missing_reference_job_is_incomplete(self):
        self.e['reference_jobs'].pop(next(iter(self.e['reference_jobs'])));self.reject('job inventory')
    def test_duplicate_reference_prefix_disagreement(self):
        job=next(iter(self.e['reference_jobs'].values()));obs=next(iter(job['observations'].values()))
        b=bytearray((self.root/obs['logits']['path']).read_bytes());b[0]^=1;obs['logits']=put(self.root,b);self.reject('duplicate fresh-R prefix observations disagree')
    def test_job_observation_metadata_not_ignored(self):
        obs=next(iter(next(iter(self.e['reference_jobs'].values()))['observations'].values()))
        obs['decoded_tokens']=[15];self.reject('observation metadata differs')
    def test_reference_mask_not_ignored(self):
        next(iter(self.e['reference_queries'].values()))['logits_masks']=[[False]]*3;self.reject('reference execution metadata differs')
    def test_candidate_row_mask_not_ignored(self):
        self.e['candidate_rows']['initial']['producer']['logits_mask']=[False]*3;self.reject('candidate producer metadata differs')
    def test_free_run_mask_not_ignored(self):
        self.e['free_scalar_run']['logits_masks']=[[False]]*len(self.e['free_scalar_run']['decoded_tokens']);self.reject('free-run output mask differs')
    def test_float_cap_rejected(self):
        c=case();c['cap']=9.0
        with self.assertRaisesRegex(A.EvidenceError,'integer output cap'):A.make_plan(c,[1,2,3],ID)
    def test_boolean_ubatch_rejected(self):
        c=case();c['target_ubatch']=True
        with self.assertRaisesRegex(A.EvidenceError,'target ubatch differs'):A.make_plan(c,[1,2,3],ID)
    def test_float_position_metadata_rejected(self):
        self.e['candidate_rows']['initial']['producer']['positions']=[0.0,1.0,2.0];self.reject('candidate producer metadata differs')
    def test_float_accepted_count_rejected(self):
        c=case();c['cycles'][0]['accepted']=3.0
        with self.assertRaisesRegex(A.EvidenceError,'noninteger cycle field'):A.make_plan(c,[1,2,3],ID)
    def test_integer_done_rejected(self):
        self.e['candidate_commits'][self.p['commits'][-1]['commit_id']]['done']=1;self.reject('semantic metadata mismatch')
    def test_float_committed_positions_rejected(self):
        self.e['candidate_commits']['initial']['positions']=[0.,1.,2.];self.reject('semantic metadata mismatch')
    def test_boolean_free_physical_width_rejected(self):
        self.e['free_scalar_run']['physical_ubatches']=[True]*len(self.e['free_scalar_run']['decoded_tokens']);self.reject('typed metadata differs')
    def test_float_plan_position_rejected(self):
        self.p['queries'][0]['positions']=[0.,1.,2.];self.reject('plan/identity differs')
    def test_payload_counter_covers_all_reads(self):
        from unittest.mock import patch
        original=A.blob;counts=[0,0]
        def counted(*args):
            b=original(*args);counts[0]+=len(b);counts[1]+=1;return b
        with patch.object(A,'blob',counted):report=A.audit(self.p,self.e,self.root,ID)
        self.assertEqual(counts,[report['payload_bytes_read'],report['payload_read_calls']])
    def test_path_escape_rejected(self):
        self.e['candidate_rows']['initial']['logits']['path']='../escape';self.reject('escapes bundle')
    def test_premature_endpoint_mutation(self):
        c=case();c['ids']=c['ids'][:1];c['cycles']=[]
        with self.assertRaisesRegex(A.EvidenceError,'incomplete request'):A.make_plan(c,[1,2,3],ID)
    def test_nan_rejected_even_if_both_sides_match(self):
        ref=put(self.root,struct.pack('<16f',float('nan'),*([0.]*15)))
        k=self.p['uses'][0]['query_id'];self.e['reference_queries'][k]['logits']=ref;self.e['candidate_rows']['initial']['logits']=ref;self.reject('nonfinite')
if __name__=='__main__':unittest.main(verbosity=2)
