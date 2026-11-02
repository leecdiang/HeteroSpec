from __future__ import annotations
import array, collections, copy, importlib.util, itertools, json, math, pathlib, shutil, struct, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import lr_common as c
import history, schedule, panel, lr_audit as audit, host, native_stage

def item(i,domain='code',n=128):
    ids=[i+10]*n
    return {'id':f'new/{i}','prompt_ids':ids,'prompt_ids_sha256':c.prompt_hash(ids),'cap':128,
      'text_sha256':c.sha(f'text{i}'.encode()),'domain':domain,'source_revision':'a'*40,'tokenizer_sha256':'b'*64}
def endpoint(ids=None):
    ids=ids or [10]*127+[2]
    return {'ids':ids,'eog':[False]*(len(ids)-1)+[True],'length':len(ids),'terminal_id':ids[-1],'stop_reason':'EOG'}
def record(s,seconds=10.):
    e=endpoint();return dict(e,endpoint=e,slot=s,input_id=s['input_id'],capture=False,teacher_forced=False,
      observer_mode='off',llama_diagnostic={'mode':'off'},service_seconds=seconds)
def measured(n=12):
    p={'inputs':[item(i) for i in range(n)]};records=[];refs={x['id']:endpoint() for x in p['inputs']}
    values={'R':30,'M_PQ':15,'M_QB':14,'C_PQ_A':10,'C_PQ_B':10,'C_QB':9}
    for s in range(6):
        for slot in schedule.timing(p,{'prefill':'native'},s):records.append(record(slot,float(values[slot['experiment_arm']])))
    return records,refs

class EndpointTests(unittest.TestCase):
    def test_valid(self):self.assertEqual(c.endpoint(endpoint())['length'],128)
    def test_short_eog(self):self.assertEqual(c.endpoint(endpoint([1,2]))['length'],2)
    def test_wrong_vocab(self):
        x=endpoint();x['ids'][0]=128256
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_early_eog(self):
        x=endpoint();x['eog'][1]=True
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_bad_terminal(self):
        x=endpoint();x['terminal_id']=42
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_missing_stop(self):
        x=endpoint();del x['stop_reason']
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_bool_token(self):
        x=endpoint();x['ids'][0]=True
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_bad_prompt_hash(self):
        x=item(0);x['prompt_ids'][0]+=1
        with self.assertRaises(ValueError):c.input_check(x)
    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):c.confined(d,'../outside')
    def test_duplicate_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'x';p.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):c.read(p)

class HistoryTests(unittest.TestCase):
    def sample(self):
        return {'ids':[10,11,12,20,21,30], 'draft_enabled':True,'cycles':[
          {'cycle':0,'seed':10,'base':100,'proposals':[11,12,13],'decisions':[11,12,20,99],'output_length':4},
          {'cycle':1,'seed':20,'base':103,'proposals':[21,22,23],'decisions':[21,30,40,99],'output_length':6}]}
    def test_partial_accept_mapping(self):
        m=history.decision_rows(self.sample());self.assertEqual((m[3]['cycle'],m[3]['row']),(0,2));self.assertEqual((m[5]['cycle'],m[5]['row']),(1,1))
    def test_not_index_div_k(self):self.assertEqual(history.decision_rows(self.sample())[4]['cycle'],1)
    def test_absolute_input_position(self):self.assertEqual(history.decision_rows(self.sample())[5]['input_position'],104)
    def test_initial_special(self):self.assertIsNone(history.decision_rows(self.sample())[0]['cycle'])
    def test_bad_seed(self):
        x=self.sample();x['cycles'][1]['seed']=7
        with self.assertRaises(ValueError):history.decision_rows(x)
    def test_bad_decision(self):
        x=self.sample();x['cycles'][0]['decisions'][1]=100
        with self.assertRaises(ValueError):history.decision_rows(x)
    def test_bonus(self):
        x={'ids':[10,11,12,13,14],'draft_enabled':True,'cycles':[{'cycle':0,'seed':10,'base':20,'proposals':[11,12,13],'decisions':[11,12,13,14],'output_length':5}]}
        self.assertEqual(history.decision_rows(x)[4]['row'],3)
    def test_ordinary(self):self.assertEqual(history.decision_rows({'ids':[1,2],'draft_enabled':False})[1]['file'],'target/ordinary-1.f32')
    def test_length_difference(self):self.assertEqual(history.first_difference([1],[1,2]),1)
    def test_equal(self):self.assertIsNone(history.first_difference([1,2],[1,2]))

class VectorTests(unittest.TestCase):
    def write(self,d,vals):
        p=pathlib.Path(d)/'v.f32';v=array.array('f',vals)
        if sys.byteorder!='little':v.byteswap()
        p.write_bytes(v.tobytes());return p
    def test_complete_128256_first_argmax(self):
        with tempfile.TemporaryDirectory() as d:
            a=[0.]*c.VOCAB;a[7]=a[8]=3.;p=self.write(d,a);self.assertEqual(audit.full_vector(p)[0],7)
    def test_short_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):audit.full_vector(self.write(d,[0.]*100))
    def test_nan_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a=[0.]*c.VOCAB;a[-1]=float('nan')
            with self.assertRaises(ValueError):audit.full_vector(self.write(d,a))
    def test_wrong_family_vocab(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):audit.full_vector(self.write(d,[0.]*151936))

class PlanTests(unittest.TestCase):
    def setUp(self):self.p={'inputs':[item(i) for i in range(12)]};self.policy={'prefill':'native'}
    def test_development36(self):self.assertEqual(len(schedule.development({'inputs':self.p['inputs'][:3]})),36)
    def test_oracle_pinned_schema(self):self.assertTrue(all(s['study_id']=='rtx_scope_transfer_v1' and s['arm']=='R' for s in schedule.original_references(self.p)))
    def test_qualification120(self):self.assertEqual(len(schedule.qualification(self.p,self.policy)),120)
    def test_all_timing864(self):self.assertEqual(sum(len(schedule.timing(self.p,self.policy,s)) for s in range(6)),864)
    def test_24_inputs1728(self):self.assertEqual(sum(len(schedule.timing({'inputs':[item(i) for i in range(24)]},self.policy,s)) for s in range(6)),1728)
    def test_all_slot_unique(self):
        ids=[s['slot_id'] for j in range(6) for s in schedule.timing(self.p,self.policy,j)];self.assertEqual(len(ids),len(set(ids)))
    def test_input_level_williams_position_balance(self):
        pos=collections.Counter()
        for s in range(6):
            rows=[x for x in schedule.timing(self.p,self.policy,s) if x['category']=='measured' and x['source_index']==0]
            for j,x in enumerate(rows):pos[x['experiment_arm'],j]+=1
        self.assertEqual(set(pos.values()),{1});self.assertEqual(len(pos),36)
    def test_input_level_first_order_balance(self):
        pairs=collections.Counter()
        for s in range(6):
            row=[x['experiment_arm'] for x in schedule.timing(self.p,self.policy,s) if x['category']=='measured' and x['source_index']==0]
            pairs.update(zip(row,row[1:]))
        self.assertEqual(len(pairs),30);self.assertEqual(set(pairs.values()),{1})
    def test_AA_order_balance(self):
        count=0
        for s in range(6):
            row=[x['experiment_arm'] for x in schedule.timing(self.p,self.policy,s) if x['category']=='measured' and x['source_index']==0]
            count+=row.index('C_PQ_A')<row.index('C_PQ_B')
        self.assertEqual(count,3)
    def test_paired_warmups(self):
        row=schedule.timing(self.p,self.policy,0)
        for a,b in zip(row[::2],row[1::2]):self.assertEqual((a['source_index'],a['experiment_arm']),(b['source_index'],b['experiment_arm']));self.assertEqual((a['category'],b['category']),('warmup','measured'))
    def test_probe_is_diagnostic(self):
        p=schedule.probe(self.p,0,'C_QB',17);self.assertEqual(p['category'],'diagnostic');self.assertEqual(p['llama_diag']['cycle'],17)
    def test_probe_wrong_arm(self):
        with self.assertRaises(ValueError):schedule.probe(self.p,0,'R',2)
    def test_bad_session(self):
        with self.assertRaises(ValueError):schedule.timing(self.p,self.policy,6)

class CostTests(unittest.TestCase):
    def test_recompute_means(self):
        rows,refs=measured();r=audit.performance(rows,refs,12);self.assertAlmostEqual(r['means']['layout'],.9);self.assertAlmostEqual(r['means']['CQB_R'],.3);self.assertTrue(r['practical_layout_gain'])
    def test_missing(self):
        rows,refs=measured()
        with self.assertRaises(ValueError):audit.performance(rows[:-1],refs,12)
    def test_duplicate(self):
        rows,refs=measured();rows[-1]=rows[0]
        with self.assertRaises(ValueError):audit.performance(rows,refs,12)
    def test_warmup_not_sample(self):
        rows,refs=measured()
        for r in rows:
            if r['slot']['category']=='warmup':r['service_seconds']=10000.
        self.assertAlmostEqual(audit.performance(rows,refs,12)['means']['layout'],.9)
    def test_diagnostic_timing(self):
        rows,refs=measured();rows[0]['llama_diagnostic']['mode']='pair'
        with self.assertRaises(ValueError):audit.performance(rows,refs,12)
    def test_reference_failure(self):
        rows,refs=measured();rows[0]['endpoint']['ids'][0]=11
        with self.assertRaises(ValueError):audit.performance(rows,refs,12)
    def test_nonfinite(self):
        rows,refs=measured();rows[0]['service_seconds']=float('inf')
        with self.assertRaises(ValueError):audit.performance(rows,refs,12)
    def test_zero(self):
        rows,refs=measured();rows[0]['service_seconds']=0.
        with self.assertRaises(ValueError):audit.performance(rows,refs,12)
    def test_session_reversal(self):
        rows,refs=measured()
        for r in rows:
            if r['slot']['session']==0 and r['slot']['experiment_arm']=='C_QB':r['service_seconds']=11.
        self.assertFalse(audit.performance(rows,refs,12)['practical_layout_gain'])
    def test_AA_guard(self):
        rows,refs=measured()
        for r in rows:
            if r['slot']['experiment_arm']=='C_PQ_A':r['service_seconds']=12.
        self.assertFalse(audit.performance(rows,refs,12)['practical_layout_gain'])

class PanelTests(unittest.TestCase):
    def pool(self):return [item(i,domain,n) for i,(domain,n,j) in enumerate(itertools.product(('code','math'),(200,600),range(10)))]
    def test_crossed_selection(self):
        p=panel.select(self.pool(),[],24);count=collections.Counter((x['domain'],x['stratum']) for x in p['inputs']);self.assertEqual(set(count.values()),{6})
    def test_deterministic(self):self.assertEqual(panel.select(self.pool(),[],12),panel.select(list(reversed(self.pool())),[],12)|{'source_pool_sha256':c.digest(self.pool())})
    def test_exclusion(self):
        pool=self.pool();p=panel.select(pool,[pool[0]],12);self.assertNotIn(pool[0]['id'],[x['id'] for x in p['inputs']])
    def test_insufficient(self):
        with self.assertRaises(ValueError):panel.select(self.pool()[:2],[],12)
    def test_missing_source(self):
        pool=self.pool();del pool[0]['source_revision']
        with self.assertRaises(ValueError):panel.select(pool,[],12)
    def test_invalid_count(self):
        with self.assertRaises(ValueError):panel.select(self.pool(),[],13)

class ResourceTests(unittest.TestCase):
    def limits(self):return dict(request_credits=8192,development_credits=6144,total_native_seconds=172800,worker_timeout_seconds=10800)
    def test_budget_extend_without_reset(self):
        with tempfile.TemporaryDirectory() as d:
            host.amend_budget(d,self.limits(),'initial');v=self.limits();v['request_credits']=16384;host.amend_budget(d,v,'new mechanism tranche')
            self.assertEqual(host.budget_current(d)['request_credits'],16384);self.assertEqual(len((pathlib.Path(d)/'RESOURCE_POLICY.jsonl').read_text().splitlines()),2)
    def test_reason_required(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):host.amend_budget(d,self.limits(),'')
    def test_bad_chain(self):
        with tempfile.TemporaryDirectory() as d:
            host.amend_budget(d,self.limits(),'initial');p=pathlib.Path(d)/'RESOURCE_POLICY.jsonl';x=json.loads(p.read_text());x['previous']='changed';p.write_text(json.dumps(x)+'\n')
            with self.assertRaises(ValueError):host.budget_current(d)
    def test_diagnostic_credits(self):
        p={'inputs':[item(0)]};self.assertEqual(host.reserve_cost([schedule.probe(p,0,'C_QB',1)]),6)
    def test_admission_not_model_request(self):self.assertEqual(host.reserve_cost([],True),0)
    def test_finite_budget(self):
        with tempfile.TemporaryDirectory() as d:
            x=self.limits();x['total_native_seconds']=float('inf')
            with self.assertRaises(ValueError):host.amend_budget(d,x,'bad')

class NativeContractTests(unittest.TestCase):
    def test_compile_real_pure_helper(self):
        compiler=shutil.which('g++') or shutil.which('clang++')
        if not compiler:self.skipTest('C++ compiler unavailable; pure helper compile not claimed')
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d);code='''#include "cycle_contract.hpp"\n#include <cassert>\nint main(){using namespace hs_llama_contract;assert(output_index(81,0,4)==81);assert(output_index(81,3,4)==84);preverify_bound(817,818);assert(probe_allowed(true,true,true,0));assert(!probe_allowed(false,true,true,0));bool bad=false;try{preverify_bound(818,818);}catch(...){bad=true;}assert(bad);bad=false;try{output_index(81,4,4);}catch(...){bad=true;}assert(bad);}\n'''
            (p/'t.cpp').write_text(code);subprocess.run([compiler,'-std=c++17','-I',str(ROOT),str(p/'t.cpp'),'-o',str(p/'t')],check=True,capture_output=True);subprocess.run([str(p/'t')],check=True)
    def test_no_default_Qwen_patch(self):self.assertIn('native.stage(repo,out,roles,False)',(ROOT/'native_stage.py').read_text())
    def test_diagnostic_not_reference(self):self.assertIn('"source_is_canonical_R",false',(ROOT/'llama_probe.hpp').read_text())
    def test_no_task_specific_native_branch(self):
        s=(ROOT/'llama_probe.hpp').read_text();self.assertNotIn('CodeContests',s);self.assertNotIn('108',s);self.assertNotIn('737',s)
    def test_actual_state_before_shadow(self):self.assertIn('state(natural)==bytes',(ROOT/'llama_probe.hpp').read_text())
    def test_own_path_required(self):self.assertIn('need(own,"q4 own-path replay differs',(ROOT/'llama_probe.hpp').read_text())
    def test_fresh_capture_is_retained(self):self.assertIn('worker=fresh_fix(worker)',(ROOT/'native_stage.py').read_text())
    def test_shape_axis_not_guessed(self):self.assertIn('q/k/attention nodes need separately reviewed axis maps',(ROOT/'triage.py').read_text())


class DriverAdapterTests(unittest.TestCase):
    def module(self,d,drift=False):
        text="""def run_unit(bundle,name,panel,schedule,original=False,admit=False):
    c={};used=dev_used=native_count=0
    argv=['Qwen',str(bundle/'BINDING.json')]
    need(used+(0 if admit else len(schedule))<=1200,'new-study 1200-request budget exhausted; old 40 remain separately accounted')
    need(dev_used+(0 if admit else len(schedule))<=480,'development budget exhausted')
    row={'reserved_requests':0 if admit else len(schedule)}
    need(native_count==(0 if admit else len(schedule)),'incomplete result')
    return row
"""
        if drift:text=text.replace('<=480','<=481')
        p=pathlib.Path(d)/'driver_fixture.py';p.write_text(text)
        spec=importlib.util.spec_from_file_location('driver_fixture',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    def test_credits_do_not_change_native_completed_count(self):
        with tempfile.TemporaryDirectory() as d:
            fn,old,new=host.derive_driver(self.module(d),None,{'families':{'Llama':{}}})
            self.assertIn('native_count==(0 if admit else len(schedule))',new)
            self.assertNotIn('native_count==reserve_cost',new)
    def test_exact_three_budget_sites(self):
        with tempfile.TemporaryDirectory() as d:
            _,_,new=host.derive_driver(self.module(d),None,{'families':{'Llama':{}}})
            self.assertEqual(new.count('reserve_cost(schedule,admit)'),3)
            self.assertIn("'Llama',str(bundle/",new)
    def test_changed_parent_budget_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):host.derive_driver(self.module(d,True),None,{'families':{'Llama':{}}})

if __name__=='__main__':unittest.main(verbosity=2)
