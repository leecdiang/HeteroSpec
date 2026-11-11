from __future__ import annotations
import copy, io, json, math, struct, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiment as e
import gguf_inventory as g
import acquire

class Shared(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
        self.proof=self.root/'receipt.json';self.proof.write_text('{"synthetic": true}')
    def tearDown(self):self.t.cleanup()
    def spec(self):
        return dict(id='fixture',seed=7,panels={'p':dict(arms=['W4','WP','L4','LP'],roots=4,sessions=4,primers=2,scope='synthetic',contrasts=[['LP','WP'],['L4','W4']],interaction=['LP','W4','WP','L4'])})
    def panel(self):
        return e.schedule(self.spec(),'p',[{'root':str(i)} for i in range(4)])
    def records(self,p):
        values=dict(W4=4.,WP=2.,L4=2.,LP=1.)
        return [dict(s,status='COMPLETE',qualified=True,reference_id='R',gpu_uuid='GPU-A',service_s=values[s['arm']],evidence_path=str(self.proof),evidence_sha256=e.sha(self.proof)) for s in p['slots']]
    def test_require(self):
        with self.assertRaises(ValueError):e.require(False,'negative')
    def test_write_once(self):
        e.save(self.root/'r.json',{})
        with self.assertRaises(FileExistsError):e.save(self.root/'r.json',{})
    def test_duplicate_json(self):
        p=self.root/'bad';p.write_text('{"x":1,"x":2}')
        with self.assertRaises(ValueError):e.read(p)
    def test_nonfinite_json(self):
        p=self.root/'bad';p.write_text('{"x":NaN}')
        with self.assertRaises(ValueError):e.read(p)
    def test_plan_counts(self):
        p=self.panel();self.assertEqual(p['measurements'],64);self.assertEqual(p['primers'],32);self.assertEqual(len(p['workers']),16)
    def test_plan_stable(self):self.assertEqual(self.panel(),self.panel())
    def test_plan_cohort_duplicate(self):
        with self.assertRaises(ValueError):e.schedule(self.spec(),'p',[{'root':'x'}]*4)
    def test_contrast_valid(self):
        s=self.spec();s['panels']['p']['contrasts']=[['LP','not']]
        with self.assertRaises(ValueError):e.schedule(s,'p',[{'root':str(i)} for i in range(4)])
    def test_complete_known_ratio(self):
        p=self.panel();r=e.analyze(p,self.records(p),32)
        self.assertEqual(r['all_fixed_controls'][0]['total_ratio'],.5);self.assertEqual(r['all_fixed_controls'][0]['interval'],[.5,.5]);self.assertEqual(r['interaction']['ratio'],1.)
    def test_descriptive_has_no_population_interval(self):
        p=self.panel();p['inference']='descriptive';r=e.analyze(p,self.records(p),32)
        self.assertEqual(r['bootstrap_draws'],0);self.assertIsNone(r['all_fixed_controls'][0]['interval']);self.assertIsNone(r['interaction']['interval'])
    def test_bad_inference(self):
        p=self.panel();p['inference']='invented'
        with self.assertRaises(ValueError):e.analyze(p,self.records(p),32)
    def test_root_unit(self):
        p=self.panel();r=e.analyze(p,self.records(p),32);self.assertEqual(r['root_count'],4);self.assertEqual(r['adjusted_family_size'],3)
    def test_missing_slot(self):
        p=self.panel()
        with self.assertRaises(ValueError):e.analyze(p,self.records(p)[:-1],32)
    def test_duplicate_slot(self):
        p=self.panel();r=self.records(p)
        with self.assertRaises(ValueError):e.analyze(p,r+[r[0]],32)
    def test_failed_slot(self):
        p=self.panel();r=self.records(p);r[0]['status']='FAILED'
        with self.assertRaises(ValueError):e.analyze(p,r,32)
    def test_nonqualified(self):
        p=self.panel();r=self.records(p);r[0]['qualified']=False
        with self.assertRaises(ValueError):e.analyze(p,r,32)
    def test_wrong_gpu(self):
        p=self.panel();r=self.records(p);r[0]['gpu_uuid']='GPU-B'
        with self.assertRaises(ValueError):e.analyze(p,r,32)
    def test_mixed_reference(self):
        p=self.panel();r=self.records(p);r[0]['reference_id']='R2'
        with self.assertRaises(ValueError):e.analyze(p,r,32)
    def test_tampered_receipt(self):
        p=self.panel();r=self.records(p);self.proof.write_text('{}')
        with self.assertRaises(ValueError):e.analyze(p,r,32)
    def test_zero_clock(self):
        p=self.panel();r=self.records(p);r[0]['service_s']=0
        with self.assertRaises(ValueError):e.analyze(p,r,32)
    def test_nan_clock(self):
        p=self.panel();r=self.records(p);r[0]['service_s']=float('nan')
        with self.assertRaises(ValueError):e.analyze(p,r,32)
    def test_wrong_metric(self):
        p=self.panel();p['metric']='episode_s'
        with self.assertRaises(ValueError):e.analyze(p,self.records(p),32)
    def test_cost_partial(self):
        x=e.coverage([1.,None],3);self.assertIsNone(x['total_s']);self.assertEqual(x['observed_sum_s'],1.);self.assertEqual(x['unknown_or_absent'],2)
    def test_cost_real_zero(self):self.assertEqual(e.coverage([0.,0.],2)['total_s'],0.)
    def test_cost_negative(self):
        with self.assertRaises(ValueError):e.coverage([-1],1)
    def test_cost_extra(self):
        with self.assertRaises(ValueError):e.coverage([1,2],1)
    def test_quantile(self):self.assertEqual(e.quantile([0.,10.],.25),2.5)
    @staticmethod
    def string(x):
        x=x.encode();return struct.pack('<Q',len(x))+x
    def gguf(self,typ=8):
        vals={'general.architecture':'qwen3','qwen3.block_count':40,'qwen3.attention.head_count_kv':8,'qwen3.attention.head_count':40,'qwen3.embedding_length':5120}
        out=b'GGUF'+struct.pack('<IQQ',3,1,len(vals))
        for key,value in vals.items():
            out+=self.string(key)
            out+=struct.pack('<I',8)+self.string(value) if isinstance(value,str) else struct.pack('<II',4,value)
        out+=self.string('blk.0.attn_q.weight')+struct.pack('<IQIQ',1,32,typ,0)
        out+=b'\0'*((-len(out))%32)+b'\0'*64
        return out
    def test_gguf_actual_type(self):
        r=g.parse(io.BytesIO(self.gguf(12)));self.assertEqual(r['tensor_type_counts'],{'12':1});self.assertFalse(r['weight_data_read']);self.assertEqual(r['tensors'][0]['type_name'],'Q4_K')
    def test_gguf_shape(self):self.assertEqual(g.parse(io.BytesIO(self.gguf()))['tensors'][0]['shape'],[32])
    def test_gguf_no_magic(self):
        with self.assertRaises(ValueError):g.parse(io.BytesIO(b'BAD!'+self.gguf()[4:]))
    def test_gguf_version(self):
        x=bytearray(self.gguf());x[4:8]=struct.pack('<I',1)
        with self.assertRaises(ValueError):g.parse(io.BytesIO(x))
    def test_gguf_truncated(self):
        with self.assertRaises(ValueError):g.parse(io.BytesIO(self.gguf()[:48]))
    def test_gguf_oversized_count(self):
        x=bytearray(self.gguf());x[8:16]=struct.pack('<Q',100001)
        with self.assertRaises(ValueError):g.parse(io.BytesIO(x))
    def test_gguf_unknown_tensor_not_reinterpreted(self):self.assertEqual(g.parse(io.BytesIO(self.gguf(999)))['tensors'][0]['type_name'],'UNKNOWN_999')
    def test_kv_formula(self):
        r=g.parse(io.BytesIO(self.gguf()));self.assertEqual(g.kv_bytes(r['metadata'],4096),671088640)
    def test_kv_bad_context(self):
        r=g.parse(io.BytesIO(self.gguf()))
        with self.assertRaises(ValueError):g.kv_bytes(r['metadata'],0)
    def test_existing_model_no_network(self):
        p=self.root/'model';p.write_bytes(b'GGUFfixture');spec={'url':'https://huggingface.co/example/model','bytes':p.stat().st_size,'sha256':e.sha(p)}
        acquire.acquire(spec,p);self.assertEqual(p.read_bytes(),b'GGUFfixture')
    def test_existing_model_mismatch(self):
        p=self.root/'model';p.write_bytes(b'bad');spec={'url':'https://huggingface.co/example/model','bytes':3,'sha256':'a'*64}
        with self.assertRaises(ValueError):acquire.acquire(spec,p)
    def test_binding_no_self_certificate(self):
        b=dict(runtime_commit='a'*40,not_pr196_worktree=True,authorization_id='fixture',gpu_uuid='GPU-fixture',pr196_quiet_coordination=True,reference_id='R',deployment_id='D',numeric_qualification='PASS')
        for k in ('runtime_evidence','reference_evidence','model_manifest'):b[k]={'path':str(self.proof),'sha256':e.sha(self.proof)}
        with self.assertRaises(ValueError):e.binding_check(b)
    def test_binding_declarations_only(self):
        b=dict(runtime_commit='a'*40,not_pr196_worktree=True,authorization_id='fixture',gpu_uuid='GPU-fixture',pr196_quiet_coordination=True,reference_id='R',deployment_id='D',numeric_qualification='HOST_EVIDENCE_REQUIRED')
        for k in ('runtime_evidence','reference_evidence','model_manifest'):b[k]={'path':str(self.proof),'sha256':e.sha(self.proof)}
        self.assertTrue(e.binding_check(b))

if __name__=='__main__':unittest.main()
