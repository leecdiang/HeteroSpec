import copy,hashlib,json,math,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import analyze,costs,design,stage_costs,stage_resident_core

# Minimal synthetic anchor fixtures, NOT a native build or an old-R snapshot.
OBSERVER='''void reset(const pj &req){path=req.at("output");}
void begin(llama_context * ctx,llama_batch b) { x(); }
void end(llama_context * ctx,int code) { y(); }
void move(){
auto before=state(src);auto p=positions(src);
auto * clone=common_sampler_clone(sampler);
auto * dst=llama_init_from_model(model,cp);
size_t consumed=llama_state_set_data(dst,before.data(),before.size());
auto restored=state(dst),after=state(src);
        transfer={{"before",p},{"kv_equal",before==restored}};
if(before!=restored)throw std::runtime_error("Transfer gate failed");
sampler=clone;return dst;
}'''
NATIVE='"service_ms"; if(ctx_tgt!=source_target)llama_free(ctx_tgt); result_file.close();'
TARGET='"service_ms"; if(ctx!=source_target){common_sampler_free(sampler);llama_free(ctx);} metrics_file.close();'

class TestCosts(unittest.TestCase):
 def sidecar(self):
  phases={k:dict(calls=0,inclusive_s=0.,exclusive_s=0.) for k in costs.TARGET+costs.DRAFT}
  phases['target_verify']=dict(calls=1,inclusive_s=1.,exclusive_s=1.)
  phases['draft_prefill']=dict(calls=1,inclusive_s=2.,exclusive_s=2.)
  phases['transition']=dict(calls=1,inclusive_s=3.,exclusive_s=1.)
  phases['export_source']=dict(calls=1,inclusive_s=2.,exclusive_s=2.)
  return dict(schema='b570-cost-v1',mode=1,valid=True,phases=phases)
 def test_nested_no_double_count(self):
  d=costs.decompose(7,self.sidecar());self.assertEqual(d['exclusive_accounted_s'],6);self.assertEqual(d['other_s'],4)
 def test_unknown_is_null(self):self.assertIsNone(costs.decompose(3,None)['draft_s'])
 def test_invalid(self):
  for t in (float('nan'),-1,True):
   with self.assertRaises(ValueError):costs.decompose(t,None)
 def test_overlap_rejected(self):
  with self.assertRaises(ValueError):costs.decompose(5,self.sidecar())
 def test_identity(self):
  a=costs.decompose(8,self.sidecar());b=costs.decompose(7,self.sidecar())
  self.assertEqual(costs.economic_identity(a,b)['full_service_saving_s'],1)
 def test_modes_not_mixed(self):
  a=costs.decompose(7,self.sidecar());sc=self.sidecar();sc['mode']=2;b=costs.decompose(7,sc)
  with self.assertRaises(ValueError):costs.economic_identity(a,b)
 def test_invalid_trace(self):
  s=self.sidecar();s['valid']=False
  with self.assertRaises(ValueError):costs.decompose(7,s)
 def test_missing_phase(self):
  s=self.sidecar();del s['phases']['target_prefill']
  with self.assertRaises(ValueError):costs.decompose(7,s)

class TestStages(unittest.TestCase):
 def fixture(self,root):
  source=root/'source';source.mkdir()
  files={'observer.h':OBSERVER,'native.cpp':NATIVE,'target.cpp':TARGET,'CMakeLists.txt':'project(test)\n'}
  for k,v in files.items():(source/k).write_text(v)
  pins=root/'pins.json';pins.write_text(json.dumps({'receipt':'synthetic','files':{k:hashlib.sha256((source/k).read_bytes()).hexdigest() for k in files}}))
  return source,pins
 def test_stage_all_modes(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);src,pins=self.fixture(root);original=(src/'observer.h').read_bytes()
   for mode in (0,1,2):
    out=root/f'm{mode}';r=stage_costs.stage(src,pins,out,mode)
    self.assertFalse(r['removed_transfer_checks']);self.assertEqual((src/'observer.h').read_bytes(),original)
    text=(out/'observer.h').read_text();self.assertIn('Transfer gate failed',text);self.assertIn('begin_decode',text)
    self.assertIn('before==restored',text);self.assertIn('B570_COST_MODE='+str(mode),(out/'CMakeLists.txt').read_text())
 def test_anchor_drift(self):
  with self.assertRaises(ValueError):stage_costs.observer(OBSERVER.replace('state(src)','changed(src)'))
 def test_duplicate_anchor(self):
  with self.assertRaises(ValueError):stage_costs.observer(OBSERVER+OBSERVER)
 def test_bad_pin(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s,p=self.fixture(r);(s/'observer.h').write_text('different')
   with self.assertRaises(ValueError):stage_costs.stage(s,p,r/'out',1)
   self.assertFalse((r/'out').exists())
 def test_no_legacy_timer_relabel(self):
  with self.assertRaises(ValueError):stage_costs.frontend(NATIVE.replace('service_ms','generation_ms'))
 def test_resident_overlay(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);src=r/'original';(src/'src').mkdir(parents=True)
   files={'src/llama-context.h':'struct C {\n    void sched_reserve();\n};\n','src/llama-context.cpp':'// frozen original\n'}
   for k,v in files.items():(src/k).write_text(v)
   pins=r/'pins.json';pins.write_text(json.dumps({'files':{k:hashlib.sha256((src/k).read_bytes()).hexdigest() for k in files}}))
   x=stage_resident_core.stage(src,pins,r/'overlay',(1,128));self.assertFalse(x['output_reserve_modified'])
   self.assertEqual((src/'src/llama-context.cpp').read_text(),'// frozen original\n')
   self.assertIn('sched_need_reserve = true',(r/'overlay/src/llama-context.cpp').read_text())

class TestDesign(unittest.TestCase):
 def test_schedule_balance(self):
  p=design.schedule(['r0','r1'])
  self.assertEqual(len(p['slots']),144)
  for root in p['roots']:
   for arm in p['arms']:
    rs=[r for r in p['slots'] if r['root_id']==root and r['arm']==arm and r['kind']=='measure']
    self.assertEqual(sorted(x['period'] for x in rs),list(range(6)))
 def test_target_plan(self):self.assertEqual(len(design.schedule(['r0']*1,'target')['slots']),8)
 def test_no_root_dup(self):
  with self.assertRaises(ValueError):design.schedule(['r','r'])
 def test_selection(self):
  r=design.choose_roots(['a','b','c'],['b'],2,'fixed');self.assertEqual(set(r),{'a','c'})
  with self.assertRaises(ValueError):design.choose_roots(['a'],[],2,'fixed')
 def test_gate_numerical_failure(self):self.assertEqual(design.gate(False,[],{})['action'],'REPAIR_OR_SCOPE_CLOSE')
 def test_gate_joint(self):self.assertEqual(design.gate(True,[1.1,1.2],{},1.15)['action'],'FREEZE_JOINT_CONFIRMATION')
 def test_no_estimator_switch(self):self.assertEqual(design.gate(True,[1.1,1.2],{},.99)['action'],'CLOSE_SPECULATION_AND_REPORT')
 def test_independent_target_path(self):self.assertEqual(design.gate(True,[.5,.4],{},.45,True)['action'],'FREEZE_TARGET_ONLY_CONFIRMATION')

class TestAnalysis(unittest.TestCase):
 def fixture(self):
  p=design.schedule(['a','b','c','d'],'target');rs=[]
  for x in p['slots']:rs.append(dict(x,status='COMPLETE',qualified=True,timing_mode=0,reference_family='one',service_s=2 if x['arm']=='S_M' else 1))
  return p,rs
 def test_exact_effect(self):
  p,rs=self.fixture();a=analyze.analyze(p,rs,1000);c=a['contrasts'][0]
  self.assertEqual(c['total_ratio'],2);self.assertEqual(c['total_family95'],[2,2]);self.assertEqual(a['independent_roots'],4)
 def test_missing_slot(self):
  p,rs=self.fixture()
  with self.assertRaises(ValueError):analyze.analyze(p,rs[:-1],1000)
 def test_diagnostic_not_clean(self):
  p,rs=self.fixture();rs[0]['timing_mode']=1
  with self.assertRaises(ValueError):analyze.analyze(p,rs,1000)
 def test_bad_reference_pool(self):
  p,rs=self.fixture();rs[0]['reference_family']='two'
  with self.assertRaises(ValueError):analyze.analyze(p,rs,1000)
 def test_duplicate_plan(self):
  p,rs=self.fixture();p['slots'].append(p['slots'][0])
  with self.assertRaises(ValueError):analyze.analyze(p,rs,1000)

if __name__=='__main__':unittest.main()
