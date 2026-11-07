"""CPU-only integration/negative tests. All raw fixtures and mock lifetimes are synthetic."""
import copy,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import host_request as h
import run_p1 as runner
import raw_audit
from protocol import read_json,digest,validate_plan
ROOT=Path(__file__).resolve().parent
class HostAdmission(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.plan=read_json(ROOT/'p0/PLAN_P1.json');cls.runtime=read_json(ROOT/'p0/RUNTIME.json');cls.cases={c['id']:c for c in cls.plan['panel']}
 def admission(self,s=None,runtime=None):
  s=s or self.plan['slots'][0];return h.admit(s,self.cases[s['task']],runtime or self.runtime)
 def candidate(self,name='C_R_QB',mode='counts'):return next(s for s in self.plan['slots'] if s['arm']==name and s['mode']==mode)
 def test_01_all_80_real_serializers(self):
  validate_plan(self.plan)
  for s in self.plan['slots']:
   a=self.admission(s);self.assertEqual(json.loads(a.wire)['prompt_ids'],s['request']['prompt_ids']);self.assertEqual(a.native_arg_k,1)
 def test_02_no_second_lookup_or_mutable_request(self):
  s=copy.deepcopy(self.candidate());r=copy.deepcopy(self.runtime);a=self.admission(s,r);wire=a.wire;s['request']['cap']=1;r['roles'].clear();buf=io.BytesIO();a.send(buf);self.assertEqual(buf.getvalue(),wire)
 def test_03_wire_matches_disk_admission(self):
  self.assertEqual([h.readback(self.admission(s)) for s in self.plan['slots']],read_json(ROOT/'p0/WIRES_P1.json'))
 def test_04_slot_recipe_drift_rejected(self):
  for key,value in [('target_output_capacity',1),('continuation_ubatch',1),('target_prefill_attention','QB'),('draft_prefill_policy','target_global_schedule')]:
   s=copy.deepcopy(self.candidate());s['request'][key]=value;s['request_sha256']=digest(s['request'])
   with self.subTest(key=key),self.assertRaises(ValueError):self.admission(s)
 def test_05_correct_hash_wrong_arm_rejected(self):
  s=copy.deepcopy(self.candidate());other=self.candidate('C_B_PQ');s['request']=copy.deepcopy(other['request']);s['request_sha256']=digest(s['request'])
  with self.assertRaises(ValueError):self.admission(s)
 def test_06_old_new_binary_swap_rejected(self):
  r=copy.deepcopy(self.runtime);r['roles']['new']['binary']=r['roles']['old']['binary'];r['roles']['new']['sha256']=r['roles']['old']['sha256']
  with self.assertRaises(ValueError):self.admission(self.candidate(),r)
 def test_07_wrong_runtime_kind(self):
  r=copy.deepcopy(self.runtime);r['roles']['new']['kind']='ORIGINAL_PR92'
  with self.assertRaises(ValueError):self.admission(self.candidate(),r)
 def test_08_target_draft_swap_rejected(self):
  r=copy.deepcopy(self.runtime);r['models']['target'],r['models']['draft']=r['models']['draft'],r['models']['target']
  with self.assertRaises(ValueError):self.admission(self.candidate(),r)
 def test_09_effective_k_vs_cli(self):
  for name in ('R','R_SHADOW','M_B_QB','M_R_QB'):
   s=next(s for s in self.plan['slots'] if s['arm']==name);a=self.admission(s);self.assertEqual((a.effective_k,a.argv[6]),(0,'1'));self.assertEqual(a.argv[3],'NONE')
 def test_10_draft_plan_is_independent(self):
  for name in ('C_B_QB','C_R_QB'):
   a=self.admission(self.candidate(name));self.assertEqual(a.request['normalized108']['draft_prefill_policy'],'independent_ref128');self.assertEqual(a.request['normalized108']['draft_continuation_ubatch'],1)
 def test_11_counts_no_diagnostic(self):
  for s in self.plan['slots']:
   if s['mode']=='counts':self.assertFalse(self.admission(s).request['capture'])
 def test_12_diagnostic_only_finite_capture(self):
  a=self.admission(self.candidate(mode='diagnostic'));self.assertTrue(a.request['capture']);self.assertFalse(a.request['phase96_diagnostic']);self.assertFalse(a.request['own_bind_sham']);self.assertEqual(a.request['boundary_cuts'],[])
 def test_13_absent_authorization_rejected(self):
  with self.assertRaises((ValueError,KeyError)):runner.authorize({'status':'CANDIDATE'}, {}, {})
 def test_14_wrong_F0_hash_rejected(self):
  f=dict(status='P0_COMPLETE_PENDING_AUTHOR_CONFIRMATION',budget={'request_starts':80});a=dict(author_confirmed=True,phase='P1',F0_sha256='a'*64,budget=f['budget'],authorization_source='SYNTHETIC_TEST_ONLY')
  with self.assertRaises(ValueError):runner.authorize(f,a,{})
 def test_15_reference_precedence(self):
  with self.assertRaises(ValueError):runner.stage_gate(self.plan,8,{})
 def test_16_reference_disagreement_stops(self):
  rec={s['slot']:{'endpoint':{'ids':[int(s['session'])]}} for s in self.plan['slots'][:8]}
  with self.assertRaises(ValueError):runner.stage_gate(self.plan,8,rec)
 def test_17_valid_candidate_mismatch_does_not_stop(self):
  rec={s['slot']:{'endpoint':{'ids':[1]}} for s in self.plan['slots'][:16]}
  runner.stage_gate(self.plan,16,rec)
 def test_18_shadow_mismatch_stops(self):
  rec={s['slot']:{'endpoint':{'ids':[1]}} for s in self.plan['slots'][:12]};rec[self.plan['slots'][8]['slot']]['endpoint']={'ids':[2]}
  with self.assertRaises(ValueError):runner.stage_gate(self.plan,12,rec)
 def test_19_failed_Popen_is_charged_before_creation(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(runner,'RUN',Path(tmp)):
   a=self.admission();w=runner.Worker(a,self.runtime)
   def no_spawn(*args,**kwargs):
    self.assertEqual(runner.ledger()[0]['event'],'PROCESS_ATTEMPT');raise OSError('SYNTHETIC_LOAD_FAILURE_NO_PROCESS')
   with patch.object(runner.subprocess,'Popen',side_effect=no_spawn),self.assertRaises(OSError):w.start()
   rows=runner.ledger();self.assertEqual(sum(r['event']=='PROCESS_ATTEMPT' for r in rows),1);self.assertEqual(sum(r['event']=='REQUEST_START' for r in rows),0);self.assertEqual(rows[-1]['event'],'PROCESS_CLOSED')
 def test_20_duplicate_attempt_rejected_without_launch(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(runner,'RUN',Path(tmp)):
   a=self.admission();runner.journal(dict(event='PROCESS_ATTEMPT',slot=a.slot));w=runner.Worker(a,self.runtime)
   with patch.object(runner.subprocess,'Popen') as p,self.assertRaises(ValueError):w.start()
   p.assert_not_called()
 def test_21_raw_duplicate_keys_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'raw.json';p.write_text('{"ids":[1],"ids":[2]}')
   with self.assertRaises(ValueError):raw_audit.load(p)
 def test_22_native_sources_have_counts_independent_phase_guard(self):
  source=(ROOT/'native/worker.cpp').read_text(encoding='utf-8');i=source.index('int phase108=');j=source.index('int rc=llama_decode(ctx,b);');self.assertLess(i,j);self.assertNotIn('if(counted())',source[i:j]);self.assertIn('phase108==0||role=="DRAFT"?0:consumer108',source)
 def test_23_graph_cache_invalidation_even_same_ub(self):
  source=(ROOT/'_host/source/llama-context.cpp').read_text(encoding='utf-8');t=source[source.index('void llama_context::b570_geometry_bind'):];self.assertIn('gf_res_prev->reset()',t);self.assertIn('std::to_string(capacity)',t);self.assertIn('b570_active_layout=layout;',t)
 def test_24_VERIFY_all_outputs_preserved(self):
  source=(ROOT/'native/worker.cpp').read_text(encoding='utf-8');self.assertIn('tgt.decode(batch,base,true,"VERIFY")',source);self.assertIn('requested_logit_positions',source);self.assertIn('b.logits[i]=all||i==b.n_tokens-1',source)
 def test_25_no_native_import_or_P0_auto_run(self):
  with patch.object(runner.subprocess,'Popen',side_effect=AssertionError('NO_NATIVE_ALLOWED')):
   for s in self.plan['slots']:self.admission(s)
class IndependentRaw(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='SYNTHETIC_RAW_TEST_');self.addCleanup(self.tmp.cleanup);self.d=Path(self.tmp.name);self.runtime=read_json(ROOT/'p0/RUNTIME.json');plan=read_json(ROOT/'p0/PLAN_P1.json');self.s=next(s for s in plan['slots'] if s['arm']=='R' and s['task']=='GSM8K/test/1248');c=next(c for c in plan['panel'] if c['id']==self.s['task']);a=h.admit(self.s,c,self.runtime);base=ROOT/'_host/pr97/baseline/pr92_restore';records=read_json(base/'FORMAL_RECORDS.json');old=next(r for r in records if r['condition']=='R_stock' and r['task']==self.s['task']);self.r=read_json(base/old['raw_path']);self.r['request_id']=self.s['slot'];pid=self.r['pid'];self.weights=[dict(event='WEIGHT_MAP',pid=pid,all_weights_Vulkan0=True,tensors=[dict(backend_device='Vulkan0',gpu_backend_buffer=True)])]
  self.put('LAUNCH.json',h.readback(a));self.put('REQUEST.json',a.request);(self.d/'REQUEST.wire').write_bytes(a.wire);self.put('IDENTITY.json',dict(pid=pid,argv=list(a.argv),modules=self.runtime['roles']['old']['modules'],weights=self.weights,all_target_weights_offloaded=True,no_draft_offload_violation=True));self.put('LIFECYCLE.json',dict(pid=pid,returncode=0,closed=True,lifecycle_id='SYNTHETIC_ONLY'));self.mem=read_json(base/old['memory_path']);self.put(self.s['slot']+'.memory.json',self.mem);self.persist()
 def put(self,name,value):(self.d/name).write_text(json.dumps(value),encoding='utf-8')
 def persist(self):self.put('RESULT.json',self.r);(self.d/'stdout.jsonl').write_text('\n'.join(json.dumps(x) for x in self.weights+[self.r])+'\n',encoding='utf-8')
 def audit(self):return raw_audit.audit(self.d,self.s,self.runtime)
 def test_01_synthetic_raw_reconstruction(self):self.assertEqual(self.audit()['endpoint']['ids'],self.r['ids'])
 def test_02_executor_result_without_native_stdout_rejected(self):
  self.r['ids'][0]+=1;self.put('RESULT.json',self.r)
  with self.assertRaises(ValueError):self.audit()
 def test_03_endpoint_truncation_rejected(self):
  self.r['ids'].pop();self.persist()
  with self.assertRaises(ValueError):self.audit()
 def test_04_forged_terminal_rejected(self):
  self.r['terminal_id']=123;self.persist()
  with self.assertRaises(ValueError):self.audit()
 def test_05_correct_source_hash_wrong_capacity_rejected(self):
  self.r['actual_condition']['output_capacity']=4;self.persist()
  with self.assertRaises(ValueError):self.audit()
 def test_06_graph_conservation_rejected(self):
  self.r['workload']['target_micrographs']+=1;self.persist()
  with self.assertRaises(ValueError):self.audit()
 def test_07_counts_heavy_rejected(self):
  self.r['observation']['added_sync']=True;self.persist()
  with self.assertRaises(ValueError):self.audit()
 def test_08_wrong_memory_PID_rejected(self):
  self.mem['samples'][0]['pid']+=1;self.put(self.s['slot']+'.memory.json',self.mem)
  with self.assertRaises(ValueError):self.audit()
 def test_09_wire_mutation_rejected(self):
  (self.d/'REQUEST.wire').write_bytes(b'{}\n')
  with self.assertRaises(ValueError):self.audit()
if __name__=='__main__':unittest.main(verbosity=2)
