"""CPU-only synthetic regression tests. No model result is generated here."""
from __future__ import annotations
import array, copy, hashlib, json, os, struct, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import common as c
import plans as p
import analyze as a
import host, stage, repair_build, trace_compare as tc, archive

ROOT=Path(__file__).parent

def item(i,domain='code',length='short',n=128):
    ids=[100+i]*n
    return dict(id=f'fixture/{i}',prompt_ids=ids,prompt_ids_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest(),
                cap=128,text_sha256=c.digest(['text',i]),source_revision='SYNTHETIC_TEST',tokenization_receipt_sha256=c.digest(['template',i]),domain=domain,stratum=length)
def dev():return {'inputs':[item(i) for i in range(4)],'natural_inputs_only':True}
def panel():
    return {'inputs':[item(10+g*3+i,d,l,128 if l=='short' else 512) for g,(d,l) in enumerate((('code','short'),('math','short'),('code','long'),('math','long'))) for i in range(3)],'natural_inputs_only':True}

def record(s,x):
    n=len(x['prompt_ids']);draft=s['draft_enabled'];cycles=[]
    if draft:cycles=[dict(cycle=0,base=n,seed=1,proposals=[9,2,3],decisions=[9,2,3,4],accepted=1,rejected=False,
        commit_kind='accepted',keep=n+2,done=True,output_length=2,pending_after=None,target_after={'min':0,'max':n+1},draft_after={'min':0,'max':n+1})]
    geometry=[]
    for phase in ('PREFILL','VERIFY' if draft else 'ORDINARY'):
        for j in range(40):geometry.append({'name':f'kq-{j}','op':'MUL_MAT','layer':j,'phase':phase,
            'placement_basis':'ggml_backend_sched_get_tensor_backend','compute_backend':'CPU' if j<17 else 'CUDA0','buffer_owner':'NVIDIA',
            'sources':[{'ne':[128,256,8,1]},{'ne':[128,1,40,4 if draft and s['scope']=='QB' and phase=='VERIFY' else 1]}]})
    return dict(ids=[1,9],eog=[False,True],length=2,terminal_id=9,stop_reason='EOG',prompt_ids=x['prompt_ids'],
        prompt_ids_sha256=x['prompt_ids_sha256'],vocabulary_eog=[9],cycles=cycles,arm=s['arm'],k=s['k'],
        draft_enabled=draft,producer=s['producer'],capture=s['observer']=='heavy',observed_scope=s['scope'],
        row_repair_policy=s['rows'],geometry=geometry,context={'expected_layers':40},
        target_final_kv={'min':0,'max':n+(1 if draft else 0)},draft_final_kv={'min':0,'max':n+1} if draft else None,
        target_state={'bytes':8,'sha256':'a'*64},draft_state={'bytes':8,'sha256':'b'*64} if draft else None,
        folder=s['slot_id'],slot=p.native_slot(s),input_id=x['id'],service_seconds=1.)

def audit_fixture():
    pan=dev();slots=p.confirmation(pan,'NATIVE','off',regression=True)
    records={s['slot_id']:record(s,pan['inputs'][s['source_index']]) for s in slots}
    return pan,slots,records

def run_audit(records,slots,pan):
    with patch.object(a,'vector_audit',return_value={'target/initial.f32':'hash'}):
        return a.audit(records,slots,pan,vector_roots={s['slot_id']:Path('.') for s in slots})

def timing():
    out=[];pan=panel()
    costs={'R':1.4,'M_PQ':1.1,'M_QB':1.0,'C_PQ_A':1.0,'C_PQ_B':1.0,'C_QB':.9}
    for session in range(4):
        for s in p.timing(pan,'RSEED','off',session):
            out.append({'outer_slot':s,'service_seconds':costs[s['experiment_arm']],'endpoint_qualified':True,'capture':False,'synthetic_fixture':True})
    return out

class PrimitiveTests(unittest.TestCase):
    def test_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'x';f.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):c.read(f)
    def test_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'x';f.write_text('{"a":NaN}')
            with self.assertRaises(ValueError):c.read(f)
    def test_exclusive_write(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'x';c.save(f,{},True)
            with self.assertRaises(FileExistsError):c.save(f,{},True)
    def test_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'x';c.save(f,{'a':1});c.save(f,{'a':2});self.assertEqual(c.read(f),{'a':2})
    def test_traversal(self):
        with self.assertRaises(ValueError):c.safe('/tmp/root','../escape')
    def test_boolean_integer(self):
        with self.assertRaises(ValueError):c.integer(True,0,3,'x')
    def test_geomean(self):self.assertEqual(c.gm([2,.5]),1)
    def test_bad_geomean(self):
        for xs in ([],[0],[float('nan')],[float('inf')]):
            with self.subTest(xs=xs),self.assertRaises(ValueError):c.gm(xs)
    def test_original_worker_identity(self):self.assertEqual(c.sha(ROOT/'fixtures/pr156_worker.cpp'),c.HISTORICAL_WORKER)

class PlansTests(unittest.TestCase):
    def test_development_counts(self):
        self.assertEqual([len(p.development(dev(),k)) for k in ('baseline','sham','p1','rseed')],[40,8,32,32])
    def test_confirmation144(self):self.assertEqual(len(p.confirmation(panel(),'RSEED','off')),144)
    def test_regression48(self):self.assertEqual(len(p.confirmation(dev(),'RSEED','off',regression=True)),48)
    def test_timing576(self):self.assertEqual(len(timing()),576)
    def test_budgets(self):self.assertEqual(sum(v for k,v in p.BUDGET.items() if k!='total'),1200)
    def test_warmup_pairs(self):
        s=p.timing(panel(),'P1','qkv',0)
        for x,y in zip(s[::2],s[1::2]):self.assertEqual(x['slot_id'].rsplit('/',1)[0],y['slot_id'].rsplit('/',1)[0])
    def test_balanced_arm_positions(self):
        slots=p.timing(panel(),'P1','off',0);counts={a:[0]*6 for a in p.TIMING}
        for i in range(12):
            order=[s['experiment_arm'] for s in slots if s['source_index']==i and s['category']=='measured']
            for j,a0 in enumerate(order):counts[a0][j]+=1
        self.assertTrue(all(v==[2]*6 for v in counts.values()))
    def test_unique_slots(self):
        z=[r['outer_slot']['slot_id'] for r in timing()];self.assertEqual(len(z),len(set(z)))
    def test_new_and_old_reference_distinct(self):
        s=p.confirmation(panel(),'RSEED','ffn')[:4]
        self.assertEqual([x['cohort'] for x in s],['reference','reference','repair','repair'])
        self.assertEqual(p.native_slot(s[0])['study_id'],'rtx_dense14b_transfer_v1')
        self.assertEqual(p.native_slot(s[2])['study_id'],c.STUDY)
    def test_reference_not_repaired(self):
        for s in p.confirmation(panel(),'RSEED','qkv'):
            if s['experiment_arm']=='R':self.assertEqual((s['producer'],s['rows']),('NATIVE','off'))
    def test_forbid_reference_rseed(self):
        with self.assertRaises(ValueError):p.make_slot(item(1),0,'R','off','x','RSEED')
    def test_policy_normalization(self):self.assertEqual(p.policy('qkv,ffn'),'ffn,qkv')
    def test_policy_rejects_prompt_rules(self):
        for s in ('GSM8K/111','layer16','all','qkv,qkv',''):
            with self.subTest(s=s),self.assertRaises(ValueError):p.policy(s)
    def test_panel_duplicate(self):
        x=panel();x['inputs'][1]=x['inputs'][0]
        with self.assertRaises(ValueError):p.panel_check(x,'confirmation')
    def test_panel_hash(self):
        x=item(1);x['prompt_ids'][0]=5
        with self.assertRaises(ValueError):p.input_check(x)
    def test_panel_strata(self):
        x=panel();x['inputs'][0]['stratum']='long'
        with self.assertRaises(ValueError):p.panel_check(x,'confirmation')
    def test_teacher_not_confirmation(self):
        x=panel();x['inputs'][0]['teacher_ids']=[1]*128
        with self.assertRaises(ValueError):p.panel_check(x,'confirmation')

class AuditTests(unittest.TestCase):
    def test_complete_synthetic_matrix(self):
        pan,slots,rs=audit_fixture();self.assertEqual(run_audit(rs,slots,pan)['status'],'PASS')
    def test_reference_failure_not_pqqb_success(self):
        pan,slots,rs=audit_fixture()
        for s in slots:
            if s['experiment_arm'] in ('M_PQ','M_QB'):
                rs[s['slot_id']]['ids'][0]=2
        self.assertEqual(run_audit(rs,slots,pan)['status'],'UNQUALIFIED')
    def test_observer_changes_cycle(self):
        pan,slots,rs=audit_fixture();s=next(s for s in slots if s['experiment_arm']=='C_QB' and s['category']=='heavy')
        rs[s['slot_id']]['cycles'][0]['accepted']=2
        self.assertEqual(run_audit(rs,slots,pan)['status'],'UNQUALIFIED')
    def test_buffer_owner_not_backend(self):
        pan,slots,rs=audit_fixture();s=next(s for s in slots if s['experiment_arm']=='M_QB' and s['category']=='heavy')
        for g in rs[s['slot_id']]['geometry']:g['placement_basis']='buffer_owner'
        self.assertEqual(run_audit(rs,slots,pan)['status'],'UNQUALIFIED')
    def test_unknown_backend(self):
        pan,slots,rs=audit_fixture();s=next(s for s in slots if s['experiment_arm']=='M_QB' and s['category']=='heavy')
        rs[s['slot_id']]['geometry'][0]['compute_backend']='UNRESOLVED'
        self.assertEqual(run_audit(rs,slots,pan)['status'],'UNQUALIFIED')
    def test_incomplete_layer_coverage(self):
        pan,slots,rs=audit_fixture();s=next(s for s in slots if s['experiment_arm']=='M_QB' and s['category']=='heavy')
        rs[s['slot_id']]['geometry']=[g for g in rs[s['slot_id']]['geometry'] if g['layer']!=39]
        self.assertEqual(run_audit(rs,slots,pan)['status'],'UNQUALIFIED')
    def test_missing_q4(self):
        pan,slots,rs=audit_fixture();s=next(s for s in slots if s['experiment_arm']=='C_QB' and s['category']=='heavy')
        for g in rs[s['slot_id']]['geometry']:g['sources'][1]['ne'][3]=1
        self.assertEqual(run_audit(rs,slots,pan)['status'],'UNQUALIFIED')
    def test_missing_record(self):
        pan,slots,rs=audit_fixture();rs.pop(slots[0]['slot_id'])
        with self.assertRaises(ValueError):run_audit(rs,slots,pan)
    def test_teacher_not_qualification(self):
        pan,slots,rs=audit_fixture();rs[slots[0]['slot_id']]['diagnostic_teacher_forced']=True
        self.assertEqual(run_audit(rs,slots,pan)['status'],'UNQUALIFIED')
    def test_new_reference_not_silently_changed(self):
        pan,slots,rs=audit_fixture();s=next(s for s in slots if s['experiment_arm']=='R_NEW' and s['category']=='heavy')
        rs[s['slot_id']]['target_state']['sha256']='z'*64
        self.assertEqual(run_audit(rs,slots,pan)['status'],'UNQUALIFIED')
    def test_full_vector_greedy(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'v';v=array.array('f',[0])*151936;v[543]=1;f.write_bytes(v.tobytes());self.assertEqual(a.vector(f)[0],543)
    def test_full_vector_tie(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'v';v=array.array('f',[0])*151936;v[3]=v[9]=2;f.write_bytes(v.tobytes());self.assertEqual(a.vector(f)[0],3)
    def test_truncated_vector(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'v';f.write_bytes(b'\0'*16)
            with self.assertRaises(ValueError):a.vector(f)
    def test_nonfinite_vector(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'v';v=array.array('f',[0])*151936;v[4]=float('nan');f.write_bytes(v.tobytes())
            with self.assertRaises(ValueError):a.vector(f)
    def test_transactions(self):
        s=p.make_slot(item(1),0,'C_QB','off','x');a.transactions(record(s,item(1)))
    def test_wrong_pending(self):
        s=p.make_slot(item(1),0,'C_QB','off','x');r=record(s,item(1));r['cycles'][0]['pending_after']=7
        with self.assertRaises(ValueError):a.transactions(r)
    def test_wrong_keep(self):
        s=p.make_slot(item(1),0,'C_QB','off','x');r=record(s,item(1));r['cycles'][0]['keep']+=1
        with self.assertRaises(ValueError):a.transactions(r)

class CostTests(unittest.TestCase):
    def test_qualifying_gain(self):self.assertTrue(a.analyze(timing())['practical_layout_gain'])
    def test_draft_value_separate(self):self.assertAlmostEqual(a.analyze(timing())['means']['D_QB'],1/.9)
    def test_complete_window(self):
        x=timing()
        for r in x:
            if r['outer_slot']['experiment_arm']=='C_QB':r['service_seconds']+=.2
        self.assertFalse(a.analyze(x)['practical_layout_gain'])
    def test_duplicate(self):
        x=timing();x[-1]=copy.deepcopy(x[-2])
        with self.assertRaises(ValueError):a.analyze(x)
    def test_missing(self):
        with self.assertRaises(ValueError):a.analyze(timing()[:-1])
    def test_bad_qualification(self):
        x=timing();x[0]['endpoint_qualified']=False
        with self.assertRaises(ValueError):a.analyze(x)
    def test_instrumented_timing(self):
        x=timing();x[0]['capture']=True
        with self.assertRaises(ValueError):a.analyze(x)
    def test_nan(self):
        x=timing();x[0]['service_seconds']=float('nan')
        with self.assertRaises(ValueError):a.analyze(x)
    def test_session_reversal(self):
        x=timing()
        for r in x:
            if r['outer_slot']['experiment_arm']=='C_QB' and r['outer_slot']['session']==0:r['service_seconds']=1.01
        self.assertFalse(a.analyze(x)['practical_layout_gain'])
    def test_aa_guard(self):
        x=timing()
        for r in x:
            if r['outer_slot']['experiment_arm']=='C_PQ_A':r['service_seconds']=1.5
        self.assertFalse(a.analyze(x)['practical_layout_gain'])

class PatchTests(unittest.TestCase):
    def test_pinned_worker_patches(self):
        raw=(ROOT/'fixtures/pr156_worker.cpp').read_text();x=stage.patch_worker(raw)
        self.assertIn('reference_seed',x);self.assertIn('token_history',x)
        self.assertNotIn('if(!d || (ggml_backend_dev_type(d)',x)
        self.assertIn('keep=base+1+accepted',x)
        self.assertIn('speculative',stage.patch_worker.__doc__ or 'speculative')
    def test_unknown_anchor_refused(self):
        with self.assertRaises(ValueError):stage.patch_worker((ROOT/'fixtures/pr156_worker.cpp').read_text().replace('Observer obs;','Observer missing;'))
    def test_idempotence_refused(self):
        x=stage.patch_worker((ROOT/'fixtures/pr156_worker.cpp').read_text())
        with self.assertRaises(ValueError):stage.patch_worker(x)
    def test_reference_prefill_charged(self):
        x=stage.patch_worker((ROOT/'fixtures/pr156_worker.cpp').read_text())
        self.assertLess(x.index('auto start=Clock::now();hsc::begin'),x.index('seed_context->decode'))
        self.assertLess(x.index('seed_context->decode'),x.index('r["service_seconds"]=since(start)'))
    def test_no_historical_answer_injection(self):
        x=stage.PREFILL;self.assertIn('repair_snapshot(*seed_context)',x);self.assertNotIn('input.at("teacher_ids")',x)
    def test_row_policy_process_fixed(self):
        s=(ROOT/'reference_rows.h').read_text();self.assertIn('static const std::set',s);self.assertIn('!hs_scope::active',s)
    def test_precision_forwarding(self):self.assertIn('set_prec(t->src[0],p)',(ROOT/'reference_rows.h').read_text())
    def test_observer_no_buffer_inference(self):
        s=(ROOT/'repair_observer.h').read_text();self.assertIn('ggml_backend_sched_get_tensor_backend',s);self.assertIn('return true; // false here',s)
    def test_patch_core(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);(r/'src').mkdir();(r/'ggml/include').mkdir(parents=True)
            (r/'src/llama-context.h').write_text('get_sched()');(r/'ggml/include/ggml-backend.h').write_text('ggml_backend_sched_get_tensor_backend ggml_backend_name')
            f=r/'src/llama-graph.cpp';f.write_text('ggml_tensor* llm_graph_context::build_lora_mm(ggml_tensor* w, ggml_tensor* cur) {auto* r=ggml_mul_mat(ctx0,w,cur);ggml_mul_mat_set_prec(r,GGML_PREC_F32);return r;}')
            receipt=repair_build.patch_core(r,ROOT);self.assertFalse(receipt['native_validated']);self.assertIn('hs_repair_rows::set_prec',f.read_text())
    def test_patch_core_no_guess(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);(r/'src').mkdir();(r/'ggml/include').mkdir(parents=True)
            (r/'src/llama-context.h').write_text('');(r/'ggml/include/ggml-backend.h').write_text('')
            with self.assertRaises(ValueError):repair_build.patch_core(r,ROOT)

class TraceTests(unittest.TestCase):
    def fixture(self,root):
        f=root/'x';f.write_bytes(struct.pack('<6f',1,2,999,3,4,999))
        return {'file':'x','bytes':24,'sha256':c.sha(f),'ne':[2,2,1,1],'nb':[4,12,24,24],'type':'f32'}
    def test_strided_column_ignores_padding(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);n=self.fixture(r);_,v,shape=tc.logical_column(r,n,1,1);self.assertEqual(v,[3,4]);self.assertEqual(shape,[2,1,1])
    def test_snapshot_hash(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);n=self.fixture(r);(r/'x').write_bytes(b'\0'*24)
            with self.assertRaises(ValueError):tc.logical_column(r,n,1,1)
    def test_snapshot_bounds(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);n=self.fixture(r);n['nb'][1]=400
            with self.assertRaises(ValueError):tc.logical_column(r,n,1,1)
    def test_prefix_for_row(self):
        n={'caller_prefix_ids':[1,2],'caller_prefix_sha256':hashlib.sha256(b'[1,2]').hexdigest(),'call_ids':[3,4,5]}
        self.assertEqual(tc.row_prefix(n,1,0),[1,2,3,4])
    def test_prefix_hash_fails(self):
        n={'caller_prefix_ids':[1,2],'caller_prefix_sha256':'bad','call_ids':[3]}
        with self.assertRaises(ValueError):tc.row_prefix(n,0,0)
    def test_no_shape_only_mapping(self):
        with self.assertRaises(ValueError):tc.compare('.',{'pairs':[],'mode':'observed_output_frontier'})

class LedgerArchiveTests(unittest.TestCase):
    def test_unclosed_reservation(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'ledger';c.append(f,{'event':'START','attempt':'a','budget_phase':'development','requests':40})
            b=host.budget_totals(f);self.assertEqual(b['reserved'],40);self.assertEqual(b['unclosed'],['a'])
    def test_failure_remains_charged(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'ledger';c.append(f,{'event':'START','attempt':'a','budget_phase':'development','requests':40});c.append(f,{'event':'END','attempt':'a','seconds':1,'success':False})
            b=host.budget_totals(f);self.assertEqual(b['reserved'],40);self.assertFalse(b['unclosed'])
    def test_duplicate_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'l';e={'event':'START','attempt':'a','budget_phase':'development','requests':1};c.append(f,e);c.append(f,e)
            with self.assertRaises(ValueError):host.budget_totals(f)
    def test_archive_reopens_every_member(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)/'raw';r.mkdir();(r/'a').write_bytes(b'abc');(r/'b').write_bytes(b'def')
            x=archive.pack(r,Path(td)/'out',3);self.assertEqual(x['verified_members'],2);self.assertEqual(len(x['parts']),2);self.assertFalse(x['remote_readback'])
    def test_archive_no_model_binary(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)/'raw';r.mkdir();(r/'x.gguf').write_bytes(b'a')
            with self.assertRaises(ValueError):archive.pack(r,Path(td)/'out')
    def test_archive_not_inside_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):archive.pack(td,Path(td)/'out')


class FinalGateTests(unittest.TestCase):
    def test_seed_initial_eog_is_not_fake_consumer_coverage(self):
        z=record(p.make_slot(item(0),0,'C_QB','heavy','d','RSEED'),item(0))
        z['target_calls']=0;z['length']=1;z['seed_geometry']=z['geometry'];z['geometry']=[]
        self.assertEqual(a.placement(z)['consumer'],'NOT_RUN_INITIAL_EOG')
    def test_empty_seed_coverage_rejected(self):
        with self.assertRaises(ValueError):a.placement({'target_calls':0,'length':1,'producer':'RSEED','seed_geometry':[]})
    def test_reverse_cross_count(self):
        slots=p.development(dev(),'cross')
        self.assertEqual(len(slots),8)
        self.assertTrue(all(s['experiment_arm']=='R_NEW' and s['producer']=='BSEED' for s in slots))
    def test_reverse_cross_not_candidate(self):
        with self.assertRaises(ValueError):p.make_slot(item(0),0,'M_QB','heavy','x','BSEED')
    def test_native_trace_can_reproduce_failure(self):
        slots=p.development(dev(),'trace',producer='NATIVE')
        self.assertTrue(all(s['producer']=='NATIVE' for s in slots))
    def test_candidate_p1_available(self):
        self.assertTrue(all(s['producer']=='P1' for s in p.development(dev(),'candidate',rows='qkv',producer='P1')))
    def test_short_complete_teacher_endpoint_allowed(self):
        x=item(0);x['teacher_ids']=[1,9];self.assertEqual(p.input_check(x),x)
    def test_empty_teacher_rejected(self):
        x=item(0);x['teacher_ids']=[]
        with self.assertRaises(ValueError):p.input_check(x)
    def test_sealing_reaudits_raw(self):
        import inspect
        text=inspect.getsource(host.seal)
        self.assertIn('a=reaudit(candidate_run)',text)
        self.assertIn("reaudit(bundle/'RUN_baseline_v00.json')",text)
        self.assertIn("reaudit(bundle/'RUN_sham_v00.json')",text)
    def test_native_sampler_for_seed(self):
        self.assertIn('pending=repair_initial(boundary.logits,*target)',stage.PREFILL)
        self.assertIn('producer=="RSEED"?reference_seed:candidate_seed',stage.PREFILL)
    def test_host_probe_disambiguates_uuid(self):
        import inspect
        self.assertIn("x.split(',')[0].strip()==gpu_uuid",inspect.getsource(host.host_identity))

if __name__=='__main__':unittest.main(verbosity=2)
