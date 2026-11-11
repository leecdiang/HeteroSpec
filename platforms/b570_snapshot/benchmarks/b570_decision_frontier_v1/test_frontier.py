"""CPU-only falsification tests; no worker construction or GPU subprocess."""
import copy,json,os,struct,tempfile,unittest
from pathlib import Path
import numpy as np
from contracts import *
from state_distance import layout,tensor_bits,splice,metrics,ordered,selector_geometry
from plan_frontier import frontier,ordered_stage,old_index
from analyze_frontier import four_cell,same_prefix,rank
from audit_raw import coordinate_set

def state(n,trans=True,donor=False):
 b=bytearray(struct.pack('<IiII',0xaf143cd8,0,1,n))
 for p in range(n):b+=struct.pack('<iIi',p,1,0)
 b+=struct.pack('<II',int(trans),32)
 for role in ('K','V'):
  for layer in range(32):
   b+=struct.pack('<iII',1,2,1024) if role=='V' and trans else struct.pack('<iQ',1,2048)
   a=np.zeros((n,1024),dtype='<u2')
   if donor:a[:]=np.arange(n,dtype=np.uint16)[:,None]+1
   b+=(a.T if role=='V' and trans else a).tobytes()
 return bytes(b)
def end(ids,stop='CAP'):return {'ids':ids,'stop_reason':stop}
def zpair(d):
 z=np.full(V,-100,dtype=np.float32);z[0]=0;z[1]=d;return z
class FrontierTests(unittest.TestCase):
 def test_transposed_address(self):
  n=4;a=state(n);b=state(n,donor=True);l=layout(b,n);v=next(t for t in l['tensors'] if t['role']=='V' and t['layer']==0)
  self.assertEqual(struct.unpack_from('<H',b,v['offset']+2*(777*n+2))[0],3)
  self.assertEqual(tensor_bits(b,v,n)[2,6,9],3)
  mixed=splice(a,b,n,'V_layer0');self.assertEqual(tensor_bits(mixed,v,n)[2,6,9],3);self.assertEqual(mixed[:l['tensors'][0]['offset']+n*2048],a[:l['tensors'][0]['offset']+n*2048])
 def test_position_complement(self):
  self.assertEqual(list(selector_geometry('KV_tail128',130)[2]),[128,129]);self.assertEqual(len(selector_geometry('KV_prefix128',130)[2]),128)
 def test_metadata_pin(self):
  a=state(2);b=bytearray(a);struct.pack_into('<i',b,16,7)
  with self.assertRaises(ValueError):splice(a,bytes(b),2,'ALL')
 def test_nonfinite(self):
  with self.assertRaises(ValueError):metrics(np.array([0x7c00],dtype=np.uint16),np.array([0],dtype=np.uint16))
 def test_zero_norm_and_signed_zero(self):
  m=metrics(np.array([0],dtype=np.uint16),np.array([0x8000],dtype=np.uint16));self.assertIsNone(m['L2_relative_error']);self.assertEqual(m['changed_F16_elements'],1);self.assertEqual(m['numerically_unequal_elements'],0);self.assertEqual(m['signed_zero_changes'],1);self.assertEqual(m['ordered_ULP_histogram'],{'1':1})
 def test_numeric_distance_not_integer_bits(self):
  a=np.array([1.0],dtype=np.float16).view(np.uint16);b=np.array([2.0],dtype=np.float16).view(np.uint16);self.assertEqual(metrics(a,b)['max_absolute_error'],1.0)
 def test_different_prefix(self):
  with self.assertRaises(ValueError):same_prefix([{'prefix':[1]},{'prefix':[2]},{'prefix':[1]},{'prefix':[1]}],[1],1)
 def test_frontier_panel_priority(self):
  arms=PANELS['L0'];es={s:end([5,7,9]) for s in arms};es[arms[1]]=end([5,7,12]);es[arms[2]]=end([5,7,13]);p=frontier(es,arms);self.assertEqual((p['t_star'],p['r'],p['u']),(2,9,12));self.assertEqual(p['positions'],[1,2])
 def test_token_zero_stop(self):
  es={s:end([5,7]) for s in PANELS['L0']};es['V_layer0']=end([6,7])
  with self.assertRaisesRegex(ValueError,'RESTORE_T0_ANOMALY'):frontier(es,PANELS['L0'])
 def test_length_endpoint_only(self):
  es={s:end([5,7]) for s in PANELS['L0']};es['V_layer0']=end([5]);self.assertEqual(frontier(es,PANELS['L0'])['status'],'ENDPOINT_ONLY')
 def test_eog_not_reached(self):
  es={s:end([5,128009],'EOG') for s in PANELS['L0']};p=frontier(es,PANELS['L0']);self.assertEqual(p['status'],'EOG_FINISHED');self.assertEqual(p['positions'],[1]);self.assertEqual(p['not_reached'],[31,63,95,127])
 def test_censored_cap(self):
  p=frontier({s:end([5]*128) for s in PANELS['L0']},PANELS['L0']);self.assertEqual(p['status'],'RIGHT_CENSORED_AT_128');self.assertEqual(p['positions'],[1,31,63,95,127])
 def test_known_residual(self):
  nums,res=four_cell([zpair(-1),zpair(2),zpair(4),zpair(8)],0,1);self.assertEqual(nums['I'],1);self.assertEqual(res[1],1)
 def test_additive_margin_nonmonotone_endpoint(self):
  zs=[zpair(-1),zpair(1),zpair(-3),zpair(-1)];nums,res=four_cell(zs,0,1);self.assertEqual(nums['I'],0);self.assertEqual(np.count_nonzero(res),0);self.assertEqual([top2(z)[0] for z in zs],[0,1,0,0])
 def test_certificate_converse_false(self):
  empty=zpair(-1);other=empty.copy();other[2]+=.75;m=float(empty[0]-empty[1]);eps=float(np.max(np.abs(other-empty)));self.assertFalse(m>2*eps);self.assertEqual(top2(other)[0],top2(empty)[0])
 def test_third_candidate_and_tie_rank(self):
  z=zpair(-1);z[2]=2;self.assertEqual(top2(z)[0],2);self.assertEqual(rank(z,0),2);z[3]=2;self.assertEqual(top2(z),(2,3));self.assertEqual(rank(z,3),2)
 def test_full_logits_t0_and_missing_t1(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);z=zpair(-1);p=root/'initial.logits.f32';p.write_bytes(z.tobytes());spec={'path':str(p),'bytes':V*4,'sha256':sha(p)};x={'ids':[0,0],'partition98':{'full_payloads':{}},'phase96':{'boundaries':[]}};res=Resolver(root,root)
   zz,proof=logits_at(x,0,res,spec);self.assertEqual(proof['source'],'PINNED_INITIAL_LOGITS');self.assertEqual(zz[1],-1);self.assertIsNone(logits_at(x,1,res,spec)[0]);x['ids'][0]=1
   with self.assertRaisesRegex(ValueError,'RESTORE_T0_ANOMALY'):logits_at(x,0,res,spec)
 def test_full_capture_sha_prefix_and_position(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);z=zpair(-1);f=root/'full.logits.f32';f.write_bytes(z.tobytes());spec={'path':str(f),'bytes':V*4,'sha256':sha(f)};boundary={'output_index_zero_based':1,'naturally_committed_prefix_ids':[0],'sampled_top1_id':0,'top2_id':1,'full_logits_sha256':sha(f),'last_consumed_input_ids':[0],'last_consumed_position':3,'top1_logit':0.,'top2_logit':-1.};x={'ids':[0,0],'prompt_ids':[99,99,99],'partition98':{'full_payloads':{'1':{'logits':spec}}},'phase96':{'boundaries':[boundary]}};res=Resolver(root,root);self.assertEqual(logits_at(x,1,res,spec)[1]['position'],3)
   boundary['naturally_committed_prefix_ids']=[1]
   with self.assertRaises(ValueError):logits_at(x,1,res,spec)
   boundary['naturally_committed_prefix_ids']=[0];boundary['last_consumed_position']=4
   with self.assertRaises(ValueError):logits_at(x,1,res,spec)
   boundary['last_consumed_position']=3;f.write_bytes(b'bad')
   with self.assertRaises(ValueError):logits_at(x,1,res,spec)
 def test_tampered_raw_and_resolver_no_fallback(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'x.json';p.write_text('{}');res=Resolver(root,'C:/oldrun');h=sha(p);p.write_text('{"evil":1}')
   with self.assertRaises(ValueError):res.record_file('x.json',h)
   self.assertEqual(res.resolve('C:/oldrun/missing.logits.f32'),root/'missing.logits.f32')
   with self.assertRaises(ValueError):res.resolve('C:/other/missing')
   with self.assertRaises(ValueError):res.resolve('../escape')
 def test_complete_plan_and_direction_and_duplicate_and_missing(self):
  root=os.environ.get('FRONTIER_CPU_ROOT');self.assertIsNotNone(root);p=read(Path(root)/'PLAN.json');validate_new_plan(p);self.assertEqual(len(p['requests']),168);self.assertEqual(p['budgets']['owned_native_process_seconds'],21600);self.assertEqual(p['budgets']['new_run_bytes'],4*1024**3)
  for mutate in ('reverse','duplicate','missing'):
   q=copy.deepcopy(p)
   if mutate=='reverse':q['requests'][0]['direction']='A->B' if q['requests'][0]['direction']=='B->A' else 'B->A'
   elif mutate=='duplicate':q['requests'][1]=q['requests'][0]
   else:q['requests'].pop()
   with self.assertRaises(ValueError):validate_new_plan(q)
 def test_old_matrix_missing_duplicate_reverse(self):
  root=Path(os.environ['FRONTIER_FRESH']);p=read(root/'PLAN.json');coordinate_set(p)
  for mutate in ('reverse','duplicate','missing'):
   q=copy.deepcopy(p)
   if mutate=='reverse':q['requests'][0]['donor']=q['requests'][0]['recipient']
   elif mutate=='duplicate':q['requests'][1]=q['requests'][0]
   else:q['requests'].pop()
   with self.assertRaises(ValueError):coordinate_set(q)
 def test_runtime_and_channels(self):
  audit=read(Path(os.environ['FRONTIER_CPU_ROOT'])/'RAW_AUDIT.json');r=audit['rows'][0];root=Path(os.environ['FRONTIER_FRESH']);x=read(root/r['raw_path']);tr=read(root/r['evidence_path']);validate_endpoint(x,x['prompt_ids'],r['owned_pid'],'heavy');validate_channel(tr,x,x['prompt_ids'],r['owned_pid'],'heavy');validate_channel(tr['memory'],x,x['prompt_ids'],r['owned_pid'],'counts')
  with self.assertRaises(ValueError):validate_channel(tr,x,x['prompt_ids'],r['owned_pid'],'counts')
  with self.assertRaises(ValueError):validate_channel(tr['memory'],x,x['prompt_ids'],r['owned_pid'],'heavy')
  x['actual_condition']['prefill_ub']=256
  with self.assertRaises(ValueError):validate_endpoint(x,x['prompt_ids'],r['owned_pid'],'heavy')
 def test_absolute_donor_path_in_unchanged_adapter(self):
  p=Path('C:/fresh/baseline/pr99/payload.bin');self.assertEqual(Path('C:/new/run')/'baseline/pr99'/p,p)
 def test_pair_rule_frozen(self):
  p=read(Path(os.environ['FRONTIER_CPU_ROOT'])/'PLAN.json');a=next(q for q in p['panels'] if q['task'].endswith('/831') and q['recipient']=='A' and q['panel']=='L0');b=next(q for q in p['panels'] if q['task'].endswith('/831') and q['recipient']=='A' and q['panel']=='POSITION');self.assertEqual((a['t_star'],b['t_star']),(40,81))
if __name__=='__main__':unittest.main(verbosity=2)
