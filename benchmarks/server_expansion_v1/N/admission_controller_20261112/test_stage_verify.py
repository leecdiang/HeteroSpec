"""Synthetic pure-file unit tests. No native/runtime/model imports or execution."""
import copy,hashlib,json,os,pathlib,struct,tempfile,unittest
from stage_verify import Invalid,RawChecker,StageVerifier,digest,parse_json,shape,validate_snapshot

H='a'*64
class Files(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='hs-staged-CPU-fixture-');self.root=pathlib.Path(self.tmp.name);self.r=RawChecker(self.root)
 def tearDown(self):self.tmp.cleanup()
 def json(self,name,value):
  b=(json.dumps(value,separators=(',',':'))+'\n').encode();(self.root/name).write_bytes(b);return {'file':name,'sha256':digest(b)}
 def tensor(self,name,dtype,shape_,axes,b=None):
  count=1
  for d in shape_:count*=d
  if b is None:b=b'\0'*(count*(2 if dtype=='F16LE' else 4))
  (self.root/name).write_bytes(b);return {'file':name,'dtype':dtype,'shape':shape_,'axes':axes,'bytes':len(b),'sha256':digest(b)}
 def snapshot(self,name,phase='TERMINAL',q=None,head=None,op='control/RESIDENT_R/example/0',event=1):
  q=[3] if q is None else q;head=len(q) if head is None else head;terminal=phase=='TERMINAL';reset=phase=='RESET';reconciled=phase=='POST_RECONCILE';m=q[:head];g=[151645] if terminal else [];pending={'id':151645,'position':head} if terminal else None;positions=[len(q)-1] if terminal else [] if reset or reconciled else [head-1];frontier=not reset and not reconciled
  if reset:q=[];m=[];head=0
  tensors={k:self.tensor(name+'-'+k+'.bin','F16LE',[36,8,head,128],['layer','kv_head','position','dimension']) for k in ('active_k','active_v')};tensors['vectors']=self.tensor(name+'-vectors.bin','F32LE',[len(positions),151936],['requested_row','vocabulary'])
  s={'schema':'hs.N1a.raw-state.v1','phase':phase,'path_kind':'RESIDENT','cohort':'SCRIPTED_CONTROL','execution_mode':'SCRIPTED_STATE_CONTROL','generation_cap':1,'run_id':'CPU_SYNTHETIC_NOT_NATIVE','operation_id':op,'context_id':'CPU_CONTEXT_LABEL_NOT_A_RUNTIME','identity':{k:H for k in ('contract_sha256','model_sha256','tokenizer_sha256','template_sha256','producer_sha256')},'provenance':{'executable_sha256':H,'capture_writer_sha256':H},'canonical_ids':q,'materialized_ids':m,'logical_ids':m+g,'generated_ids':g,'head':head,'pending':pending,'frontier':{'valid':frontier,'owned':frontier,'position':head-1 if frontier else None},'requested_vector_positions':positions,'owned_vector_ids':['CPU-SYNTHETIC-OWNED'] if positions else [],'event_ordinal':event,'tensors':tensors}
  if terminal:s['stop_reason']='EOG'
  d=self.json(name+'.json',s);d.update(run_id=s['run_id'],operation_id=op,phase=phase,executable_sha256=H);return s,d
 def test_duplicate_json_and_utf8_rejected(self):
  with self.assertRaises(Invalid):parse_json(b'{"shape":[],"shape":[1]}')
  with self.assertRaises(UnicodeError):parse_json(b'"\xff"')
 def test_exact_bits_signed_zero_rejected(self):
  a=self.tensor('a.bin','F32LE',[1],['scalar'],struct.pack('<I',0));b=self.tensor('b.bin','F32LE',[1],['scalar'],struct.pack('<I',0x80000000));x=self.r.tensor(a,b);self.assertEqual(x['status'],'NUMERIC_FAIL');self.assertEqual(x['bit_different_scalars'],1)
 def test_file_mutation_during_comparison_and_between_retained_hash_read_rejects(self):
  def touch(p):
   s=p.stat();os.utime(p,ns=(s.st_atime_ns,s.st_mtime_ns+1000000))
  class ChangingReader:
   def __init__(self,f,p):self.f=f;self.p=p;self.once=False
   def __enter__(self):return self
   def __exit__(self,*args):self.f.close()
   def fileno(self):return self.f.fileno()
   def read(self,n):
    b=self.f.read(n)
    if not self.once:touch(self.p);self.once=True
    return b
  class Changing(RawChecker):
   def open(inner,name):
    f=super(Changing,inner).open(name);return ChangingReader(f,inner.root/name) if name=='a.bin' else f
  a=self.tensor('a.bin','F16LE',[1],['scalar']);b=self.tensor('b.bin','F16LE',[1],['scalar'])
  with self.assertRaisesRegex(Invalid,'changed during raw comparison'):Changing(self.root).tensor(a,b)
  old=self.tensor('old.bin','F16LE',[36,8,2,128],['layer','kv_head','position','dimension']);new=self.tensor('new.bin','F16LE',[36,8,1,128],['layer','kv_head','position','dimension'])
  class Between(RawChecker):
   def hash_file(inner,name,*args,**kwargs):
    h=super(Between,inner).hash_file(name,*args,**kwargs)
    if name=='old.bin':touch(inner.root/name)
    return h
  with self.assertRaisesRegex(Invalid,'changed during transport read'):Between(self.root).retained_tensor(old,new,2,1)
 def test_equal_nonfinite_not_a_pass(self):
  a=self.tensor('a.bin','F16LE',[1],['scalar'],struct.pack('<H',0x7c00));b=self.tensor('b.bin','F16LE',[1],['scalar'],struct.pack('<H',0x7c00));x=self.r.tensor(a,b);self.assertEqual(x['status'],'NUMERIC_FAIL');self.assertIsNotNone(x['first_nonfinite'])
 def test_actual_digest_and_length_rechecked(self):
  a=self.tensor('a.bin','F16LE',[1],['scalar']);b=self.tensor('b.bin','F16LE',[1],['scalar']);(self.root/'b.bin').write_bytes(b'\x01\0')
  with self.assertRaises(Invalid):self.r.tensor(a,b)
 def test_snapshot_pending_eog_cap_and_full_vectors(self):
  s,_=self.snapshot('source');self.assertEqual(validate_snapshot(s),s)
  for key,value in [('pending',{'id':True,'position':1}),('generated_ids',[151645,3]),('generation_cap',True)]:
   bad=copy.deepcopy(s);bad[key]=value
   with self.assertRaises(Invalid):validate_snapshot(bad)
  bad=copy.deepcopy(s);bad['tensors']['vectors']['shape']=[1,1]
  with self.assertRaises(Invalid):validate_snapshot(bad)
 def test_aligned_reads_full_vector_bytes(self):
  a,ad=self.snapshot('a');b,bd=self.snapshot('b',op='control/REPEAT_RESIDENT_R/example/0');c={'left':ad,'right':bd};self.assertEqual(self.r.aligned(c)['status'],'PASS')
  t=b['tensors']['vectors'];raw=bytearray((self.root/t['file']).read_bytes());raw[-4:]=struct.pack('<f',1.0);(self.root/t['file']).write_bytes(raw);t['sha256']=digest(raw);d=self.json('b.json',b);bd['sha256']=d['sha256'];x=self.r.aligned(c);self.assertEqual(x['status'],'NUMERIC_FAIL');self.assertEqual(x['tensors']['vectors']['first_difference']['coordinate']['vocabulary'],151935)
 def test_cold_reconcile_compares_KV_without_equating_invalid_resident_frontier(self):
  a,ad=self.snapshot('resident',phase='POST_RECONCILE');b,bd=self.snapshot('cold',phase='POST_RECONCILE',op='control/COLD_CANONICAL_ORACLE/example/0')
  b.update(path_kind='COLD_ORACLE',execution_mode='SCRIPTED_CONTROL_ORACLE',frontier={'valid':True,'owned':True,'position':0},requested_vector_positions=[0],owned_vector_ids=['CPU_COLD_ROW'])
  b['tensors']['vectors']=self.tensor('cold-frontier.bin','F32LE',[1,151936],['requested_row','vocabulary']);bd['sha256']=self.json('cold.json',b)['sha256']
  result=self.r.aligned({'left':ad,'right':bd});self.assertEqual(result['status'],'PASS');self.assertEqual(set(result['tensors']),{'active_k','active_v'});self.assertIn('FRONTIER_NOT_COMPARED',result['scope'])
 def test_retained_prefix_uses_old_head_stride(self):
  oldhead,keep=3,1;a=bytearray(36*8*oldhead*256);b=bytearray(36*8*keep*256)
  for layer in range(36):
   for h in range(8):
    a[(layer*8+h)*oldhead*256:(layer*8+h)*oldhead*256+2]=b'\0\x3c';b[(layer*8+h)*keep*256:(layer*8+h)*keep*256+2]=b'\0\x3c'
  ta=self.tensor('old.bin','F16LE',[36,8,oldhead,128],['layer','kv_head','position','dimension'],a);tb=self.tensor('new.bin','F16LE',[36,8,keep,128],['layer','kv_head','position','dimension'],b);self.assertEqual(self.r.retained_tensor(ta,tb,oldhead,keep)['status'],'PASS')
  b[-2:]=b'\0\x3c';(self.root/'new.bin').write_bytes(b);tb['sha256']=digest(b);x=self.r.retained_tensor(ta,tb,oldhead,keep);self.assertEqual(x['status'],'NUMERIC_FAIL');self.assertEqual(x['first_difference']['coordinate'],{'layer':35,'kv_head':7,'position':0,'dimension':127})
 def test_prefix_receipt_pending_rule_and_forbidden_retry(self):
  old,od=self.snapshot('old',event=1);new,nd=self.snapshot('next',phase='POST_RECONCILE',q=[3,9],head=1,op='control/RESIDENT_R/example/1',event=6)
  rr={'schema':'hs.N1a.reconcile-receipt.v1','run_id':old['run_id'],'context_id':old['context_id'],'source_operation_id':old['operation_id'],'operation_id':new['operation_id'],'previous_snapshot_sha256':od['sha256'],'current_snapshot_sha256':nd['sha256'],'fallback_reason':None,'mode':'LCP_TRIM_REPLAY','actual_head_before':1,'actual_keep':1,'actual_model_rows_before_append':0,'old_frontier_invalidated':True,'old_pending_id':151645,'pending_disposition':'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX'}
  rd=self.json('reconcile.json',rr);c={'previous':od,'current':nd,'transition_receipt':rd};self.assertEqual(self.r.prefix(c)['status'],'PASS')
  rr['fallback_reason']='TRIM_CAPABILITY_UNSUPPORTED';c['transition_receipt']=self.json('reconcile.json',rr)
  with self.assertRaises(Invalid):self.r.prefix(c)
 def test_ownership_requires_actual_source_row_and_real_event_order(self):
  s,sd=self.snapshot('source');nextid='control/RESIDENT_R/example/1';origin={'snapshot':sd,'requested_row_index':0,'vector_position':0,'ownership_id':s['owned_vector_ids'][0],'next_operation_id':nextid};events=[];values=[]
  for name,phase,ordinal in [('before','BEFORE_NEXT_MUTATION',2),('after','AFTER_NEXT_MUTATION',5)]:
   e={'schema':'hs.N1a.owned-vector-event.v1','phase':phase,'run_id':s['run_id'],'context_id':s['context_id'],'source_operation_id':s['operation_id'],'next_operation_id':nextid,'source_snapshot_sha256':sd['sha256'],'source_requested_row_index':0,'source_vector_position':0,'ownership_id':origin['ownership_id'],'caller_owned':True,'capture_writer_sha256':H,'event_ordinal':ordinal,'tensor':self.tensor(name+'.bin','F32LE',[1,151936],['requested_row','vocabulary'])};events.append(self.json(name+'.json',e));values.append(e)
  m={'schema':'hs.N1a.mutation-receipt.v1','run_id':s['run_id'],'context_id':s['context_id'],'operation_id':nextid,'source_operation_id':s['operation_id'],'begin_event_ordinal':3,'end_event_ordinal':4,'actual_decode_calls':1,'actual_model_rows':1,'status':'COMPLETE'}
  c={'origin':origin,'before_event':events[0],'after_event':events[1],'mutation_receipt':self.json('mutation.json',m)};self.assertEqual(self.r.ownership(c)['status'],'PASS')
  for name,e,key in zip(('before','after'),values,('before_event','after_event')):
   data=bytearray((self.root/(name+'.bin')).read_bytes());data[-4:]=struct.pack('<f',1);(self.root/(name+'.bin')).write_bytes(data);e['tensor']['sha256']=digest(data);c[key]=self.json(name+'.json',e)
  result=self.r.ownership(c);self.assertEqual(result['status'],'NUMERIC_FAIL');self.assertIn('source row',result['reason'])
  m['begin_event_ordinal']=2;c['mutation_receipt']=self.json('mutation.json',m)
  with self.assertRaises(Invalid):self.r.ownership(c)
 def test_reset_checks_actual_empty_files(self):
  s,d=self.snapshot('reset',phase='RESET');self.assertEqual(self.r.reset({'capture':d})['status'],'PASS');(self.root/s['tensors']['active_v']['file']).write_bytes(b'\0\0')
  with self.assertRaises(Invalid):self.r.reset({'capture':d})
 def test_symlink_and_traversal_rejected(self):
  (self.root/'a.bin').write_bytes(b'\0');(self.root/'alias.bin').symlink_to('a.bin')
  for name in ('alias.bin','../a.bin','/a.bin','a\\b','a//b'):
   with self.assertRaises(Invalid):self.r.path(name)
 def test_tensor_bool_count_rejected(self):
  t=self.tensor('a.bin','F16LE',[0],['scalar']);t['bytes']=False
  with self.assertRaises(Invalid):shape(t)

class Stages(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.repo=pathlib.Path(__file__).resolve().parents[4]
 def test_frozen_graph_per_stage_exact_counts_and_absent_stays_not_run(self):
  with tempfile.TemporaryDirectory(prefix='hs-stage-CPU-only-') as d:
   v=StageVerifier(self.repo,pathlib.Path(d)/'ABSENT_CAPTURE_SET',{})
   allids=[]
   for stage,count in [('R',27),('REPEAT',81),('COLD',72),('STRONG',81)]:
    r=v.verify(stage);self.assertEqual(r['status'],'NOT_RUN');self.assertFalse(r['native_qualified']);self.assertEqual(len(r['exact_check_ids']),count);self.assertEqual({x['status'] for x in r['checks']},{'NOT_RUN'});allids+=r['exact_check_ids']
   self.assertEqual(len(set(allids)),261)
 def test_existing_incomplete_or_unbound_captures_fail_closed(self):
  with tempfile.TemporaryDirectory(prefix='hs-stage-CPU-only-') as d:
   v=StageVerifier(self.repo,d,{});r=v.verify('R');self.assertEqual(r['status'],'BLOCKED');self.assertFalse(r['native_qualified']);self.assertTrue(r['first_difference']);self.assertEqual(len(r['checks']),27)
 def test_constructor_manifest_is_copied_and_internal_mutation_blocks(self):
  with tempfile.TemporaryDirectory() as d:
   original={'run_id':'CPU_ORIGINAL','worker_bindings':{'example':{'identity':{'nested':['CPU_ONLY']}}}};v=StageVerifier(self.repo,pathlib.Path(d)/'ABSENT',original);original['worker_bindings']['example']['identity']['nested'].append('CHANGED_CALLER')
   self.assertEqual(v.manifest['worker_bindings']['example']['identity']['nested'],['CPU_ONLY']);self.assertEqual(v.verify('R')['status'],'NOT_RUN')
   v.manifest['worker_bindings']['example']['identity']['nested'].append('CHANGED_INTERNAL');self.assertEqual(v.verify('R')['status'],'BLOCKED');self.assertEqual(v.verify_sealed({'a.bin':H})['status'],'BLOCKED')
 def test_prior_file_seal_rechecks_bytes_and_allows_new_unsealed_stage_entries(self):
  with tempfile.TemporaryDirectory(prefix='hs-prior-CPU-files-') as d:
   root=pathlib.Path(d);(root/'before.bin').write_bytes(b'CPU synthetic bytes');v=StageVerifier(self.repo,d,{});seal={'before.bin':digest(b'CPU synthetic bytes')};r=v.verify_sealed(seal);self.assertEqual(r['status'],'PASS');self.assertFalse(r['native_qualified']);self.assertEqual(r['files_checked'],1)
   (root/'new-stage.bin').write_bytes(b'new CPU-only stage');self.assertEqual(v.verify_sealed(seal)['status'],'PASS')
   (root/'before.bin').write_bytes(b'altered');r=v.verify_sealed(seal);self.assertEqual(r['status'],'FAIL');self.assertEqual(r['first_difference']['file'],'before.bin')
   self.assertEqual(v.verify_sealed({})['status'],'BLOCKED');self.assertEqual(v.verify_sealed({'../escape':H})['status'],'BLOCKED')
 def test_unknown_stage_and_changed_frozen_input_reject(self):
  with tempfile.TemporaryDirectory() as d:
   v=StageVerifier(self.repo,d,{})
   with self.assertRaises(Invalid):v.verify('FAVORABLE_SUBSET')
   altered=pathlib.Path(d)/'CPU_FAKE_REPO/benchmarks/server_expansion_v1/N/n1a_lifecycle_20261112';altered.mkdir(parents=True)
   original=self.repo/'benchmarks/server_expansion_v1/N/n1a_lifecycle_20261112/N1A_PROPOSAL_NOT_ADMITTED.json';(altered/'N1A_PROPOSAL_NOT_ADMITTED.json').write_bytes(original.read_bytes()+b' ')
   with self.assertRaisesRegex(Invalid,'frozen proposal/graph changed'):StageVerifier(pathlib.Path(d)/'CPU_FAKE_REPO',d,{})
 def test_incremental_all_four_synthetic_stage_prefixes_and_all261_not_native(self):
  from cpu_stage_fixture import build_synthetic_prefix
  with tempfile.TemporaryDirectory(prefix='hs-incremental-SYNTHETIC-ONLY-') as d:
   root=pathlib.Path(d)/'SYNTHETIC_FILES_NOT_A_NATIVE_RUN';v=StageVerifier(self.repo,root,{});sealed={};allids=[]
   roles=['RESIDENT_R','REPEAT_RESIDENT_R','COLD_CANONICAL_ORACLE','STRONG_WHOLE_RECHUNK_LOOP4']
   for index,(role,count) in enumerate(zip(roles,[27,81,72,81])):
    manifest=build_synthetic_prefix(v,root,role,append=index>0);v=StageVerifier(self.repo,root,manifest)
    if sealed:self.assertEqual(v.verify_sealed(sealed)['status'],'PASS')
    r=v.verify(role);self.assertEqual(r['status'],'PASS',r.get('reason') or r.get('first_difference'));self.assertFalse(r['native_qualified']);self.assertFalse(r['admission_authorized']);self.assertEqual(len(r['checks']),count);self.assertEqual(r['inventory']['states'],63*(index+1));self.assertEqual(r['inventory']['events'],18*(index+1));self.assertEqual(r['scope'],'PROVISIONAL_PROVIDED_BYTES_ONLY');allids+=r['exact_check_ids'];sealed=r['capture_file_sha256']
    print(json.dumps({'schema':'hs.N1controller.synthetic-stage-unit.v1','stage':role,'checks':count,'status':r['status'],'scope':r['scope'],'native_qualified':False}))
    if not index:
     self.assertEqual(len(r['reference_inputs']),18);self.assertEqual(r['reference_inputs_scope'],'PROVIDED_R_SELF_NOT_COLD_EQUIVALENCE')
     for op,certificate in r['reference_inputs'].items():
      self.assertIn('/RESIDENT_R/',op);self.assertLess(certificate['retained_head'],len(certificate['canonical_ids']));self.assertLessEqual(len(certificate['canonical_ids'])+certificate['generation_cap']-1,4096);self.assertEqual(certificate['post_reconcile_snapshot']['phase'],'POST_RECONCILE');self.assertEqual(certificate['terminal_snapshot']['phase'],'TERMINAL');self.assertTrue(certificate['generated_ids']);self.assertIn(certificate['stop_reason'],('EOG','CAP'))
   self.assertEqual(len(allids),261);self.assertEqual(len(set(allids)),261);self.assertEqual(r['inventory']['producer_receipts'],24);self.assertEqual(r['inventory']['reconcile_receipts'],27);self.assertEqual(v.verify('R')['status'],'BLOCKED')
   # Removing a real commit file cannot be replaced by a JSON PASS flag.
   missing=sorted(root.glob('*-POST_APPEND'))[0]/'COMPLETE.json';missing.rename(missing.with_name('COMPLETE_REMOVED_FOR_CPU_TEST.json'));self.assertEqual(v.verify('STRONG')['status'],'BLOCKED');self.assertNotEqual(v.verify_sealed(sealed)['status'],'PASS')

if __name__=='__main__':unittest.main(verbosity=2)
