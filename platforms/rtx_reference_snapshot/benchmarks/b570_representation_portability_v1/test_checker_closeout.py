"""Input/schema and support-field regressions. No attention/model execution."""
import copy, io, json, pathlib, subprocess, sys, tempfile, time, unittest
from common import ROOT, load, modules, save, sha
from conditions import BACKEND, MAX_INT, INTEGER_FIELDS, TEXT_FIELDS, VECTOR_FIELDS
from conditions import evaluate, example, q_rows_overlap
from fixtures import fixtures

class CheckerCloseout(unittest.TestCase):
    def reject(self,x):
        r=evaluate(x)
        self.assertTrue(r['errors'])
        for rep in r['representations'].values():
            self.assertFalse(rep['static_legal'])
            self.assertIsNone(rep['vulkan_mul_mat_batch3_equal'])
            self.assertIsNone(rep['vulkan_mul_mat_support'])
            self.assertEqual(rep['vulkan_evidence_level'],'UNKNOWN')
        json.dumps(r,allow_nan=False)

    def test_non_object_roots(self):
        for x in (None,False,True,0,2.0,'input',[],[example()]):
            with self.subTest(type=type(x).__name__):self.reject(x)

    def test_missing_fields(self):
        for field in example():
            x=example();del x[field]
            with self.subTest(field=field):self.reject(x)

    def test_integer_types_and_range(self):
        for field in INTEGER_FIELDS:
            for value in (None,True,False,2.0,'2',[],{},float('nan'),float('inf'),-1,MAX_INT+1):
                x=example();x[field]=value
                with self.subTest(field=field,type=type(value).__name__):self.reject(x)

    def test_vector_types_and_elements(self):
        for field in VECTOR_FIELDS:
            for value in (None,False,'1234',{},[],[1,2,3],[1,2,3,4,5],(1,2,3,4),
                          [1,True,3,4],[1,2.0,3,4],[1,-1,3,4],[1,MAX_INT+1,3,4],[1,None,3,4]):
                x=example();x[field]=value
                with self.subTest(field=field,type=type(value).__name__):self.reject(x)

    def test_text_and_boolean_types(self):
        for field in TEXT_FIELDS:
            for value in (None,True,5,[],{},'', '   '):
                x=example();x[field]=value
                with self.subTest(field=field,type=type(value).__name__):self.reject(x)
        for value in (0,1,'true',None,[],False):
            x=example();x['mask_nonempty']=value;self.reject(x)

    def test_semantic_rejections(self):
        for field,value in [('q',0),('q',3),('k',0),('h',0),('hk',0),('hk',7),
                            ('q_offset',33),('q_offset',36),('q_buffer_bytes',0),
                            ('mask_ne',[128,1,1,1]),('mask_nb',[4,516,0,0]),
                            ('k_ne',[128,128,8,2]),('v_ne',[128,128,8,2]),
                            ('k_nb',[2,256,32768,0]),('v_nb',[2,256,32768,0]),
                            ('k_buffer_bytes',0),('v_buffer_bytes',0),('mask_buffer_bytes',0),
                            ('kv_dtype','F32'),('mask_type','F16'),('phase','UNKNOWN'),
                            ('role','UNKNOWN'),('version','other')]:
            x=example();x[field]=value
            with self.subTest(field=field,value=value):self.reject(x)

    def test_support_is_not_a_positive_certificate(self):
        for q in (1,2):
            r=evaluate(example(q));self.assertFalse(r['errors']);self.assertEqual(r['schema_version'],2)
            for name,rep in r['representations'].items():
                mismatch=name=='QB' and q==2
                self.assertEqual(rep['vulkan_mul_mat_batch3_equal'],not mismatch)
                self.assertIs(rep['vulkan_mul_mat_support'],False if mismatch else None)
                self.assertEqual(rep['vulkan_support_scope'],'BATCH3_NECESSARY_CONDITION_ONLY')
                self.assertEqual(rep['vulkan_evidence_level'],'SOURCE_PROVEN_PROPERTY' if mismatch else 'UNKNOWN')
                self.assertEqual(rep['actual_backend_observation'],'UNKNOWN')
                self.assertFalse(rep['full_request_qualification'])
                self.assertEqual(rep['cost_eligibility'],'UNKNOWN')

    def test_unbound_backend_does_not_reject_qb_from_other_version(self):
        x=example();x['backend_dll_sha256']='different-version';r=evaluate(x)
        self.assertFalse(r['errors'])
        for rep in r['representations'].values():
            self.assertIsNone(rep['vulkan_mul_mat_batch3_equal'])
            self.assertIsNone(rep['vulkan_mul_mat_support'])
            self.assertEqual(rep['vulkan_batch3_evidence_level'],'UNKNOWN')
            self.assertEqual(rep['reason'],'BACKEND_VERSION_UNBOUND')

    def test_role_phase_binding(self):
        for role in ('target','draft'):
            for phase in ('PREFILL','VERIFY'):
                x=example(1);x.update(role=role,phase=phase);r=evaluate(x)
                for name in ('PQ','QB'):
                    rep=r['representations'][name]
                    self.assertEqual(rep['static_legal'],role=='target' and phase!='PREFILL')
                    self.assertIsNone(rep['vulkan_mul_mat_support'])
                    if not rep['static_legal']:
                        self.assertIsNone(rep['vulkan_mul_mat_batch3_equal'])
                        self.assertEqual(rep['reason'],'ROLE_PHASE_BINDING_NOT_ADMITTED')

    def test_overlap_formula_against_integer_addresses(self):
        for q in (1,2):
            for h in (1,2,3,5):
                for a in (0,4,508,512,516,1024,1536,2560):
                    for b in (0,4,508,512,516,1024):
                        addresses=[j*a+head*b+d*4 for j in range(q) for head in range(h) for d in range(128)]
                        expected=len(addresses)!=len(set(addresses))
                        self.assertEqual(q_rows_overlap(q,h,a,b),expected,(q,h,a,b))

    def test_huge_declared_heads_without_enumeration(self):
        x=example();x['h']=1<<40
        x['q_nb']=[4,512*x['h'],512,1024*x['h']]
        x['q_buffer_bytes']=32+1024*x['h']
        self.assertFalse(evaluate(x)['errors'])
        x['h']=MAX_INT;x['q_buffer_bytes']=MAX_INT
        self.reject(x)

    def test_all_72_geometry_descriptors_without_attention(self):
        seen=set()
        for group in ('dev','holdout'):
            for f in fixtures(group):
                key=tuple(f[n] for n in ('q','k','h','hk','storage'))
                if key in seen:continue
                seen.add(key);q,k,h,hk,s=key;x=example(q)
                x.update(k=k,h=h,hk=hk,q_nb=[4,512*h if s else 512,512 if s else 512*q,512*h*q],
                         q_offset=32 if s else 0,q_buffer_bytes=512*h*q+(32 if s else 0),
                         k_ne=[128,k,hk,1],v_ne=[k,128,hk,1],k_nb=[2,256,256*k,256*k*hk],
                         v_nb=[2,2*k,256*k,256*k*hk],k_buffer_bytes=256*k*hk,v_buffer_bytes=256*k*hk,
                         mask_ne=[k,32,1,1],mask_nb=[4,4*k,128*k,128*k],mask_buffer_bytes=128*k)
                self.assertFalse(evaluate(x)['errors'],key)
        self.assertEqual(len(seen),72)

    def test_cli_bad_json_and_schema(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'_host') as d:
            p=pathlib.Path(d)/'input.json'
            for text in ('{broken','null','[]','{"q": true}',json.dumps(dict(example(),q=2.0))):
                p.write_text(text,encoding='utf-8')
                r=subprocess.run([sys.executable,str(ROOT/'conditions.py'),str(p)],capture_output=True,text=True)
                self.assertEqual(r.returncode,2)
                self.assertTrue(json.loads(r.stdout)['errors'])
                self.assertEqual(r.stderr,'')

if __name__=='__main__':
    before=modules();started=time.monotonic();stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CheckerCloseout))
    receipt=dict(tests=result.testsRun,success=result.wasSuccessful(),failures=len(result.failures),errors=len(result.errors),
                 log=stream.getvalue(),elapsed_s=time.monotonic()-started,checker_sha256=sha(ROOT/'conditions.py'),
                 test_source_sha256=sha(__file__),modules_before=before,modules_after=modules(),
                 CPU_geometry_descriptors=72,new_attention_fixtures=0,new_model_processes=0,new_model_requests=0,
                 new_GPU_forwards=0,new_GPU_operators=0,probes=0,warmups=0,
                 scope='User-authorized final input validation/support semantics correction. Historical 432-fixture results and NO-GO remain unchanged.')
    save(ROOT/'CHECKER_CLOSEOUT_TESTS.json',receipt)
    print(stream.getvalue());raise SystemExit(0 if result.wasSuccessful() else 1)
