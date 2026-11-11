"""CPU regression and negative controls. Every original/future native launch is forbidden."""
import copy,io,os,random,tempfile,types,unittest,subprocess
import numpy as np
from pathlib import Path
from unittest.mock import patch
from pinned_sources import *
from registry import *
from admission import *
PLAN=read(Path(REFS['old_run'])/'PLAN.json');AUDIT=read(Path(REFS['v1_benchmark'])/'evidence/RAW_AUDIT.json');REG=build_registry(PLAN['cells']);RUN=REFS['candidate_run']
class Sender:
 CPU_only=True
 def __init__(self):self.sent=[];self.completions=0;self.runtime_identity=identity_expected()
 def send(self,obj):self.sent.append(obj)
 def wait(self,n):require(n=='CHECK_OK','completion forbidden')

class V2Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.reader=PayloadReader();cls.proof=validate_registry_against_plan(PLAN,REG,AUDIT,cls.reader);cls.actual=[capture_real_request(s,REG,RUN) for s in PLAN['requests']]
 def test_old_collision_exact_28_before_launch(self):
  old=read(Path(REFS['old_run'])/'DONORS.json');bad=registry_mismatches(PLAN,old);self.assertEqual(len(bad),28);self.assertEqual({r['recipient'] for r in bad},{'A'})
  with patch.object(subprocess,'Popen',forbidden_launch),self.assertRaises(ValueError):validate_registry_against_plan(PLAN,old,AUDIT)
 def test_order_invariance_22_orders(self):
  ref=encoded(REG);cells=PLAN['cells'];self.assertEqual(encoded(build_registry(sorted(cells,key=lambda c:c['recipient']))),ref);self.assertEqual(encoded(build_registry(sorted(cells,key=lambda c:c['recipient'],reverse=True))),ref)
  for seed in range(20):cs=copy.deepcopy(cells);random.Random(10500+seed).shuffle(cs);self.assertEqual(encoded(build_registry(cs)),ref)
 def test_logical_cells_not_deduplicated_by_CAS(self):
  self.assertEqual(len(REG['entries']),64);self.assertEqual(sum('KV' in e for e in REG['entries'].values()),56);self.assertLess(len({e['KV']['sha256'] for e in REG['entries'].values() if 'KV' in e}),56)
 def test_duplicate_logical_insert_rejected(self):
  with self.assertRaises(ValueError):build_registry(PLAN['cells']+[PLAN['cells'][0]])
  with self.assertRaises(ValueError):insert({'x':1},'x',2)
 def test_duplicate_JSON_keys_rejected(self):
  with self.assertRaises(ValueError):loads('{"entries":{"x":1,"x":2}}')
 def test_full_registry_and_requests_disk_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);write(p/'registry.json',REG);write(p/'plan.json',PLAN);rr=read(p/'registry.json');pp=read(p/'plan.json');validate_registry_against_plan(pp,rr,AUDIT,self.reader)
   for s,(req,proof) in zip(pp['requests'],self.actual):write(p/'request.json',req);q=read(p/'request.json');validate_actual_request(q,s,rr,RUN,self.reader);self.assertEqual(q,req);self.assertEqual(proof['registry_reads'],1);self.assertEqual(proof['native_launches'],0);self.assertEqual(proof['completion_sent'],0)
 def test_EMPTY_ALL_both_directions_recipient_logits(self):
  for c in PLAN['cells']:
   if c['state'] not in ('EMPTY','ALL'):continue
   req,_=capture_real_request(next(s for s in PLAN['requests'] if key(s)==key(c)),REG,RUN);self.assertTrue(spec_equal(req['restore100']['KV'],c['mixture_spec']));self.assertTrue(spec_equal(req['restore100']['logits'],c['initial_logits_spec']))
 def test_valid_hash_wrong_cell_no_send(self):
  s=PLAN['requests'][0];req=copy.deepcopy(self.actual[0][0]);wrong=next(c for c in PLAN['cells'] if c['task']==s['task'] and c['recipient']!=s['recipient'] and c['state']==s['state']);self.reader(wrong['mixture_spec']);req['restore100']['KV']=wrong['mixture_spec'];sender=Sender()
  with self.assertRaises(ValueError):a=admit(req,s,PLAN,REG,RUN,self.reader);send_preverified(a,sender,sender.runtime_identity)
  self.assertEqual(sender.sent,[]);self.assertEqual(sender.completions,0)
 def test_swapped_logits_no_send(self):
  s=PLAN['requests'][0];req=copy.deepcopy(self.actual[0][0]);wrong=next(c for c in PLAN['cells'] if c['task']==s['task'] and c['recipient']!=s['recipient']);req['restore100']['logits']=wrong['initial_logits_spec'];sender=Sender()
  with self.assertRaises(ValueError):a=admit(req,s,PLAN,REG,RUN,self.reader);send_preverified(a,sender,sender.runtime_identity)
  self.assertFalse(sender.sent)
 def test_missing_extra_logical_keys(self):
  for change in ('missing','extra'):
   r=copy.deepcopy(REG)
   if change=='missing':r['entries'].pop(next(iter(r['entries'])))
   else:r['entries']['EXTRA']=copy.deepcopy(next(iter(r['entries'].values())))
   with self.assertRaises(ValueError):validate_registry_against_plan(PLAN,r,AUDIT,self.reader)
 def test_wrong_direction_stale_plan(self):
  for change in ('direction','stage','repeat','prompt','missing_slot','duplicate_slot'):
   p=copy.deepcopy(PLAN)
   if change=='direction':p['requests'][0]['direction']='A->B'
   elif change=='stage':p['requests'][0]['stage']='subset_counts'
   elif change=='repeat':p['requests'][0]['repeat']=1
   elif change=='prompt':p['requests'][0]['prompt_ids'][0]=1
   elif change=='missing_slot':p['requests'].pop()
   else:p['requests'][1]=copy.deepcopy(p['requests'][0])
   with self.assertRaises(ValueError):validate_registry_against_plan(p,REG,AUDIT,self.reader)
 def test_stale_registry_and_legal_wrong_source(self):
  r=copy.deepcopy(REG);c=PLAN['cells'][0];other=next(x for x in PLAN['cells'] if x['task']==c['task'] and x['recipient']!=c['recipient'] and x['state']==c['state']);r['entries'][kvkey(c)]['KV']=other['mixture_spec']
  with self.assertRaises(ValueError):validate_registry_against_plan(PLAN,r,AUDIT,self.reader)
 def test_payload_tamper_before_send(self):
  s=copy.deepcopy(PLAN['requests'][0]);req=copy.deepcopy(self.actual[0][0]);r=copy.deepcopy(REG)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'payload';spec=copy.deepcopy(s['mixture_spec']);p.write_bytes(Path(spec['path']).read_bytes());spec['path']=str(p);s['mixture_spec']=spec;req['restore100']['KV']=spec;r['entries'][kvkey(s)]['KV']=spec;a=admit(req,s,PLAN,r,RUN,PayloadReader());p.write_bytes(b'tampered');sender=Sender()
   with self.assertRaises(ValueError):send_preverified(a,sender,sender.runtime_identity)
   self.assertEqual(sender.sent,[])
 def test_single_admitted_object_no_second_registry_lookup(self):
  s=PLAN['requests'][0];req=copy.deepcopy(self.actual[0][0]);a=admit(req,s,PLAN,REG,RUN,self.reader);sender=Sender();m=load('controller100')
  with patch.object(m,'load',lambda *a:(_ for _ in ()).throw(AssertionError('SECOND_LOOKUP_FORBIDDEN'))),patch.object(subprocess,'Popen',forbidden_launch):send_preverified(a,sender,sender.runtime_identity)
  self.assertEqual(sender.sent[0],{'op':'CHECK'});self.assertIs(sender.sent[1],a.request);self.assertEqual(sender.completions,0)
 def test_mutated_admitted_object_and_runtime_rejected(self):
  for which in ('runtime','request'):
   s=PLAN['requests'][0];req=copy.deepcopy(self.actual[0][0]);a=admit(req,s,PLAN,REG,RUN,self.reader);sender=Sender();ident=copy.deepcopy(sender.runtime_identity)
   if which=='runtime':ident['recipe']['prefill_ub']=256
   else:a.request['boundary_cuts']=[1]
   with self.assertRaises(ValueError):send_preverified(a,sender,ident)
   self.assertFalse(sender.sent)
 def test_identity_drift_during_CHECK_prevents_forward(self):
  s=PLAN['requests'][0];a=admit(copy.deepcopy(self.actual[0][0]),s,PLAN,REG,RUN,self.reader);sender=Sender()
  def wait(n):sender.runtime_identity=copy.deepcopy(sender.runtime_identity);sender.runtime_identity['driver_identity']['DriverVersion']='wrong'
  sender.wait=wait
  with self.assertRaises(ValueError):send_preverified(a,sender,identity_expected())
  self.assertEqual(sender.sent,[{'op':'CHECK'}])
 def test_counts_memory_heavy_trace_and_independent_native_gate(self):
  row=AUDIT['rows'][0];root=Path(REFS['pr103_fresh']);x=read(root/row['raw_path']);trace=read(root/row['evidence_path']);C.validate_channel(trace,x,x['prompt_ids'],row['owned_pid'],'heavy');C.validate_channel(trace['memory'],x,x['prompt_ids'],row['owned_pid'],'counts')
  legacy_req=read(root/row['raw_path'].replace('.RESULT.json','.REQUEST.json'));cell=next(c for c in PLAN['cells'] if c['task']==row['task'] and c['recipient']==row['recipient'] and c['state']==row['selector']);self.assertTrue(validate_native_result(legacy_req,cell,x,trace,row['owned_pid'],'heavy',C.Resolver(root,AUDIT['resolver_original_prefix'])))
  with self.assertRaises(ValueError):C.validate_channel(trace,x,x['prompt_ids'],row['owned_pid'],'counts')
  with self.assertRaises(ValueError):C.validate_channel(trace['memory'],x,x['prompt_ids'],row['owned_pid'],'heavy')
  records=list((Path(REFS['old_run'])/'records').glob('*.json'));rec=read(records[0]);bad=read(Path(REFS['old_run'])/rec['raw_path']);ev=read(Path(REFS['old_run'])/rec['evidence_path'])
  with self.assertRaises(ValueError):validate_native_result(self.actual[0][0],PLAN['requests'][0],bad,ev,rec['owned_pid'],'counts',None)
 def test_loaded_identity_adapter_old_failure_not_a_sample(self):
  base=Path(REFS['old_run']);rec=read(next((base/'records').glob('*.json')));directory=base/Path(rec['identity_path']).parent;identity=read(directory/'IDENTITY.json');command=read(directory/'COMMAND.json');ready=next(loads(line) for line in (directory/'stdout.jsonl').read_text().splitlines() if loads(line)['event']=='READY');loaded=read(directory/'MODULES.stdout');self.assertEqual(identity_from_native_evidence(identity,command,ready,loaded,identity_expected()['driver_identity']),identity_expected());bad=copy.deepcopy(ready);bad['forward_calls']=1
  with self.assertRaises(ValueError):identity_from_native_evidence(identity,command,bad,loaded,identity_expected()['driver_identity'])
 def test_original_constructor_forbidden(self):
  with patch.object(subprocess,'Popen',forbidden_launch):
   with self.assertRaises(AssertionError):subprocess.Popen(['b570-boundary-worker.exe'])
 def test_no_default_native_authorization(self):
  sender=Sender();sender.CPU_only=False;s=PLAN['requests'][0];a=admit(copy.deepcopy(self.actual[0][0]),s,PLAN,REG,RUN,self.reader)
  with self.assertRaisesRegex(ValueError,'SEPARATE_AUTHOR'):send_preverified(a,sender,sender.runtime_identity)
  self.assertFalse(sender.sent)
 def test_wrong_model_worker_DLL_driver_rejected(self):
  for field in ('model','worker','DLL','driver'):
   s=PLAN['requests'][0];a=admit(copy.deepcopy(self.actual[0][0]),s,PLAN,REG,RUN,self.reader);sender=Sender();identity=copy.deepcopy(sender.runtime_identity)
   if field=='model':identity['model']['sha256']='0'*64
   elif field=='worker':identity['modules'][0]['sha256']='0'*64
   elif field=='DLL':identity['modules'][1]['sha256']='0'*64
   else:identity['driver_identity']['DriverVersion']='wrong'
   with self.assertRaises(ValueError):send_preverified(a,sender,identity)
   self.assertFalse(sender.sent)
 def test_POSITION_NOT_COMPARABLE_and_L0_guard(self):
  from canonical_position import position_checks
  A={'panel':'POSITION','prefix_ids':[1],'canonical_pair':[2,3],'actual_condition':{},'natural_first_ids':[1],'sampler_contracts':['native greedy']};B=copy.deepcopy(A);states=[b'AA',b'BA',b'AB',b'BB'];z=[np.array([i],dtype=np.float32) for i in range(4)]
  self.assertTrue(all(position_checks(A,B,states,states[::-1],z,z[::-1],b'I',b'I').values()))
  for field,val in [('prefix_ids',[9]),('canonical_pair',[2,4]),('actual_condition',{'FA':True})]:
   bad=copy.deepcopy(B);bad[field]=val;self.assertFalse(all(position_checks(A,bad,states,states[::-1],z,z[::-1],b'I',b'I').values()))
  badstates=states[::-1];badstates[0]=b'wrong';self.assertFalse(all(position_checks(A,B,states,badstates,z,z[::-1],b'I',b'I').values()));bad=copy.deepcopy(A);bad['panel']='L0'
  with self.assertRaises(ValueError):position_checks(bad,B,states,states[::-1],z,z[::-1],b'I',b'I')
 def test_no_difference_pair_is_per_observed_t(self):
  from canonical_position import no_difference_pair
  a=np.full(C.V,-1,dtype=np.float32);a[1]=2;a[2]=1;b=np.full(C.V,-1,dtype=np.float32);b[3]=2;b[4]=1;self.assertEqual(no_difference_pair(a),(1,2));self.assertEqual(no_difference_pair(b),(3,4))
 def test_original_numerical_prefix_residual_suite(self):
  os.environ['FRONTIER_CPU_ROOT']=str(Path(REFS['v1_benchmark'])/'evidence');os.environ['FRONTIER_FRESH']=REFS['pr103_fresh'];mod=load('test_frontier');suite=unittest.defaultTestLoader.loadTestsFromModule(mod);buf=io.StringIO();result=unittest.TextTestRunner(stream=buf).run(suite);self.assertTrue(result.wasSuccessful(),buf.getvalue());self.assertEqual(result.testsRun,24)
if __name__=='__main__':
 import sys
 with patch.object(subprocess,'Popen',forbidden_launch):
  suite=unittest.defaultTestLoader.loadTestsFromTestCase(V2Tests);r=unittest.TextTestRunner(stream=sys.stdout,verbosity=2).run(suite)
  write(ROOT/'TEST_RECEIPT.json',{'status':'PASS' if r.wasSuccessful() else 'FAIL','v2_test_methods':r.testsRun,'nested_frozen_v1_test_methods':24,'tests_are_not_native_admission':True,'new_native_processes':0,'new_native_requests':0,'original_request_and_send_dry_runs':168,'native_constructor_called':False,'Popen_policy':'all attempted launches rejected during suite','traversal_orders':22,'failures':[str(e) for _,e in r.failures+r.errors]})
  sys.exit(0 if r.wasSuccessful() else 1)
