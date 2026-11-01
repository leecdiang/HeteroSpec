from __future__ import annotations
import copy,importlib.util,json,math,os,struct,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
import common as c
import plan,audit,tensors,native,operator_patch,run

def item(i):
    ids=[1,10+i,20+i]
    return {'id':f'x/{i}','prompt_ids':ids,'prompt_ids_sha256':c.prompt_hash(ids),'cap':128,'text_sha256':c.digest(str(i))}
def panel(n,start=0):return {'inputs':[item(i) for i in range(start,start+n)]}
def endpoint(ids=None):
    ids=ids or [1,2,3]
    return {'ids':ids,'eog':[False]*(len(ids)-1)+[True],'length':len(ids),'terminal_id':ids[-1],'stop_reason':'EOG'}
def policy():return {'prefill':'reference','rowwise_roles':0,'mechanism':'canonical producer state','revision':'dev1'}
def timing_records():
    records=[];p=panel(12)
    for s in range(4):
        for slot in plan.timing(p,policy(),s):
            records.append({'slot':slot,'input_id':slot['input_id'],'endpoint':endpoint(),'service_seconds':1.,'teacher_forced':False,'capture':False,'observer_mode':'off'})
    return records,{x['id']:endpoint() for x in p['inputs']}

class CommonTests(unittest.TestCase):
    def test_duplicate_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';p.write_text('{"x":1,"x":2}')
            with self.assertRaises(ValueError):c.read(p)
    def test_nan_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';p.write_text('{"x":NaN}')
            with self.assertRaises(ValueError):c.read(p)
    def test_exclusive_save(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';c.save(p,{},True)
            with self.assertRaises(FileExistsError):c.save(p,{},True)
    def test_path_traversal(self):
        with self.assertRaises(ValueError):c.confined('/tmp/test','../x')
    def test_empty_prompt(self):
        x=item(0);x['prompt_ids']=[]
        with self.assertRaises(ValueError):c.valid_input(x)
    def test_prompt_hash(self):
        x=item(0);x['prompt_ids'][0]=2
        with self.assertRaises(ValueError):c.valid_input(x)
    def test_endpoint_early_eog(self):
        e=endpoint();e['eog'][0]=True
        with self.assertRaises(ValueError):c.endpoint(e)
    def test_endpoint_truncated_cap(self):
        e=endpoint();e['eog']=[False]*3;e['stop_reason']='CAP'
        with self.assertRaises(ValueError):c.endpoint(e)
    def test_endpoint_valid(self):self.assertEqual(c.endpoint(endpoint()),endpoint())
    def test_geomean(self):self.assertAlmostEqual(c.gm([1.,4.]),2.)
    def test_geomean_nan(self):
        with self.assertRaises(ValueError):c.gm([1.,float('nan')])

class PlanTests(unittest.TestCase):
    def test_dev_count(self):self.assertEqual(len(plan.development(panel(4))),96)
    def test_dev_12_recipes(self):self.assertEqual(len(set(plan.DEVELOPMENT_RECIPES)),12)
    def test_heldout_count(self):self.assertEqual(len(plan.qualification(panel(12),policy())),120)
    def test_total_timing_count(self):self.assertEqual(sum(len(plan.timing(panel(12),policy(),s)) for s in range(4)),576)
    def test_slots_unique(self):
        ss=plan.development(panel(4));self.assertEqual(len(ss),len({s['slot_id'] for s in ss}))
    def test_reference_not_changed(self):
        for s in plan.qualification(panel(12),policy()):
            if s['arm']=='R':self.assertEqual(s['repair']['prefill'],'native');self.assertEqual(s['target_ub'],1)
    def test_formal_no_trace(self):
        for s in plan.timing(panel(12),policy(),0):self.assertEqual(s['observer'],'off');self.assertEqual(s['repair']['trace']['mode'],'off')
    def test_paired_warmup(self):
        ss=plan.timing(panel(12),policy(),0)
        for a,b in zip(ss[::2],ss[1::2]):
            self.assertEqual(a['experiment_arm'],b['experiment_arm']);self.assertEqual(a['source_index'],b['source_index']);self.assertEqual(a['category'],'warmup');self.assertEqual(b['category'],'measured')
    def test_order_balanced_aggregate(self):
        for s in range(4):
            ss=plan.timing(panel(12),policy(),s);counts={a:[0]*6 for a in plan.TIMING_ARMS}
            for i in range(12):
                arms=[x['experiment_arm'] for x in ss if x['source_index']==i and x['category']=='measured']
                for j,a in enumerate(arms):counts[a][j]+=1
            self.assertTrue(all(v==[2]*6 for v in counts.values()))
    def test_no_task_specific_policy(self):
        p=policy();p['special_task_ids']=['x/1']
        with self.assertRaises(ValueError):plan.policy_check(p)
    def test_reject_bool_roles(self):
        p=policy();p['rowwise_roles']=True
        with self.assertRaises(ValueError):plan.policy_check(p)
    def test_overlap_panels(self):
        with self.assertRaises(ValueError):plan.assert_distinct_panels(panel(4),panel(12))
    def test_disjoint_panels(self):plan.assert_distinct_panels(panel(4),panel(12,20))
    def test_probe_not_speculative(self):
        with self.assertRaises(ValueError):plan.trace_slot(panel(4),0,'C_QB','reference',[1,2,3],1)
    def test_probe_prefix(self):
        p=panel(4);s=plan.trace_slot(p,0,'M_QB','reference',[4,5,6],2)
        self.assertEqual(s['repair']['teacher_tokens'],[4,5]);self.assertEqual(s['category'],'diagnostic')

class TensorTests(unittest.TestCase):
    def meta(self,kind='f32'):return {'type':kind,'ne':[2,2,1,1],'nb':[4,12,24,24]}
    def data(self,pad=0.):return struct.pack('<6f',1,2,pad,3,4,pad)
    def test_strided_padding_ignored(self):
        r=tensors.compare(self.data(100),self.meta(),self.data(999),self.meta());self.assertTrue(r['bitwise_equal']);self.assertEqual(r['elements'],4)
    def test_logical_difference(self):
        b=bytearray(self.data());struct.pack_into('<f',b,12,7)
        r=tensors.compare(self.data(),self.meta(),bytes(b),self.meta());self.assertEqual(r['different_elements'],1);self.assertEqual(r['max_absolute_finite_difference'],4)
    def test_shape_requires_alignment(self):
        m=self.meta();m['ne'][1]=1;self.assertEqual(tensors.compare(self.data(),m,self.data(),self.meta())['status'],'NOT_COMPARABLE')
    def test_row_alignment(self):
        r=tensors.compare(self.data(),self.meta(),struct.pack('<2f',3,4),{'type':'f32','ne':[2,1,1,1],'nb':[4,8,8,8]},left_row=1)
        self.assertTrue(r['bitwise_equal'])
    def test_bounds(self):
        with self.assertRaises(ValueError):list(tensors.logical_values(b'\0',self.meta()))
    def test_bfloat(self):
        value=tensors.scalar(struct.pack('<H',0x3f80),'bf16',0)[1];self.assertEqual(value,1.)
    def test_nonfinite(self):
        m={'type':'f32','ne':[1]*4,'nb':[4]*4};b=struct.pack('<f',float('inf'))
        self.assertEqual(tensors.compare(b,m,b,m)['nonfinite_pairs'],1)
    def test_signed_zero_not_exact(self):
        m={'type':'f32','ne':[1]*4,'nb':[4]*4};self.assertFalse(tensors.compare(struct.pack('<f',0.),m,struct.pack('<f',-0.),m)['bitwise_equal'])

class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(HERE/'tests/fixtures/pr151_worker.cpp').read_bytes();cls.adapter=(HERE/'tests/fixtures/pr156_adapter.py.txt').read_bytes()
        cls.final=native.adapt(native.inherited_adapt(cls.raw.decode(),cls.adapter),(HERE/'repair_observer.inc').read_text())
    def test_authentic_worker(self):self.assertEqual(c.git_blob(self.raw),c.PINS['worker.cpp'])
    def test_authentic_adapter(self):self.assertEqual(c.git_blob(self.adapter),native.ADAPTER_BLOB)
    def test_anchor_fails_closed(self):
        with self.assertRaises(ValueError):native.once('x x','x','z')
    def test_scheduler_not_buffer_inference(self):
        self.assertIn('ggml_backend_sched_get_tensor_backend',self.final)
        self.assertNotIn('unexpected attention placement',self.final)
        self.assertIn('buffer_owner_device',self.final)
    def test_post_callback_returns_true(self):self.assertIn('return true; // false here would cancel',self.final)
    def test_reference_context_is_ub1(self):
        s=(HERE/'repair_boundary.hpp').read_text();self.assertIn('reference?1:4,true,!reference',s)
    def test_initial_logits_not_stale(self):self.assertIn('transferred_pending>=0?transferred_pending:target->sample',self.final)
    def test_no_acceptance_rewrite(self):
        a='        int seed=pending;';b='        base=keep;cycle++;'
        self.assertEqual(self.raw.decode().split(a)[1].split(b)[0],self.final.split(a)[1].split(b)[0])
    def test_probe_guard(self):self.assertIn('teacher probe cannot run acceptance loop',self.final)
    def test_state_cost_inside_timer(self):
        self.assertLess(self.final.index('produce_and_import'),self.final.index('r["service_seconds"]=since(start)'))
    def test_build_anchor(self):
        x='        code = Path(__file__).parent\n        for name in ("worker.cpp", "arm_spec.h"):'
        self.assertIn('repair_source_changes',native.patch_builder(x))
    def test_no_rowwise_patch_default(self):self.assertEqual(operator_patch.apply_rows('/missing','/missing',0)['mode'],'NO_ARITHMETIC_PATCH')
    def test_rowwise_patch_only_main_helper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'src').mkdir();p=root/'src/llama-graph.cpp'
            p.write_text('auto llm_graph_context::build_lora_mm(W w, T cur) { auto a = ggml_mul_mat(ctx0, w, cur); return a;}\nauto other(){return ggml_mul_mat(ctx0, w, cur);}')
            r=operator_patch.apply_rows(root,HERE,1);text=p.read_text();self.assertEqual(text.count('hs_repair_mm::mul_mat'),1);self.assertEqual(text.count('ggml_mul_mat(ctx0, w, cur)'),1)
    def test_new_reference_forbidden_in_policy(self):
        p=policy();p['reference']='candidate_output'
        with self.assertRaises(ValueError):plan.policy_check(p)

class CostTests(unittest.TestCase):
    def test_equal_not_gain(self):
        r,refs=timing_records();self.assertFalse(audit.performance(r,refs)['practical_layout_gain'])
    def test_gain(self):
        r,refs=timing_records()
        for x in r:
            if x['slot']['experiment_arm']=='C_QB':x['service_seconds']=.9
        self.assertTrue(audit.performance(r,refs)['practical_layout_gain'])
    def test_missing(self):
        r,refs=timing_records()
        with self.assertRaises(ValueError):audit.performance(r[:-1],refs)
    def test_duplicate(self):
        r,refs=timing_records();r[-1]=r[0]
        with self.assertRaises(ValueError):audit.performance(r,refs)
    def test_reference_failure(self):
        r,refs=timing_records();r[3]['endpoint']=endpoint([7,8,3])
        with self.assertRaises(ValueError):audit.performance(r,refs)
    def test_trace_in_timing(self):
        r,refs=timing_records();r[0]['observer_mode']='tensors'
        with self.assertRaises(ValueError):audit.performance(r,refs)
    def test_teacher_in_timing(self):
        r,refs=timing_records();r[0]['teacher_forced']=True
        with self.assertRaises(ValueError):audit.performance(r,refs)
    def test_reversed_session(self):
        r,refs=timing_records()
        for x in r:
            if x['slot']['experiment_arm']=='C_QB':x['service_seconds']=1.01 if x['slot']['session']==0 else .8
        self.assertFalse(audit.performance(r,refs)['practical_layout_gain'])
    def test_noise_guard(self):
        r,refs=timing_records()
        for x in r:
            if x['slot']['experiment_arm']=='C_PQ_A':x['service_seconds']=1.2
            if x['slot']['experiment_arm']=='C_QB':x['service_seconds']=1.
        self.assertFalse(audit.performance(r,refs)['practical_layout_gain'])
    def test_budget_keeps_failed_reservations(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'l';c.append(p,{'event':'START','reserved_requests':96});c.append(p,{'event':'END','seconds':2,'success':False})
            self.assertEqual(run.resource_totals(p),(96,2))
    def test_complete_vector_argmax(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';p.write_bytes(struct.pack('<4f',1,3,3,2));self.assertEqual(audit.full_vector(p,4)[0],1)
    def test_vector_wrong_size(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';p.write_bytes(struct.pack('<f',1))
            with self.assertRaises(ValueError):audit.full_vector(p,4)
    def test_vector_nan(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';p.write_bytes(struct.pack('<4f',1,2,float('nan'),4))
            with self.assertRaises(ValueError):audit.full_vector(p,4)


class CppPrimitiveTests(unittest.TestCase):
    def test_cpp_graph_and_stride_contract(self):
        import shutil,subprocess
        compiler=shutil.which('g++') or shutil.which('clang++')
        if not compiler:self.skipTest('C++ compiler unavailable; native host build still required')
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/('mock.exe' if os.name=='nt' else 'mock')
            subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror','-I'+str(HERE/'tests/stubs'),'-I'+str(HERE),str(HERE/'tests/rowwise_contract.cpp'),'-o',str(exe)],check=True,capture_output=True,text=True)
            r=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('CPP_GRAPH_ADDRESS_CONTRACT_PASS',r.stdout)

if __name__=='__main__':unittest.main(verbosity=2)
