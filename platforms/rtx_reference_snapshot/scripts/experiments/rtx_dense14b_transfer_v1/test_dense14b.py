"""CPU tests only. Synthetic fixtures are never native experimental evidence."""
from __future__ import annotations
import copy, hashlib, importlib.util, json, math, struct, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import common as c
import design as d
import model_inspect as mi
import native


def item(i,domain='code',stratum='short',n=128):
    ids=[100+i]*n
    return {'id':f'fixture/{i}','domain':domain,'stratum':stratum,'prompt_ids':ids,
            'prompt_ids_sha256':c.prompt_hash(ids),'cap':128,'text_sha256':c.digest(['text',i]),
            'source_revision':'synthetic-no-dataset','tokenization_receipt_sha256':c.digest(['render',i])}

def candidates():
    return [item(j*10+i,domain,st,128 if st=='short' else 512)
            for j,(domain,st) in enumerate(d.STRATA) for i in range(6)]

def exposure():return {'coverage_review_complete':True,'input_ids':[],'text_sha256':[],'prompt_ids_sha256':[]}

def panel():return d.select_panel(candidates(),exposure())

def timing():
    out=[]
    for s in range(4):
        for slot in d.slots(panel(),'formal',s):
            a=slot['experiment_arm'];t={'R':1.2,'M_PQ':.8,'M_QB':.7,'C_PQ_A':1.,'C_PQ_B':1.,'C_QB':.9}[a]
            out.append({'slot':slot,'service_seconds':t,'synthetic_fixture':True})
    return out

class Primitives(unittest.TestCase):
    def test_duplicate_json(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x';p.write_text('{"x":1,"x":2}')
            with self.assertRaises(ValueError):c.read(p)
    def test_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x';p.write_text('{"x":NaN}')
            with self.assertRaises(ValueError):c.read(p)
    def test_exclusive_save(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x';c.save(p,{},True)
            with self.assertRaises(FileExistsError):c.save(p,{},True)
    def test_atomic_save(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x';c.save(p,{'a':1});c.save(p,{'a':2});self.assertEqual(c.read(p),{'a':2})
    def test_traversal(self):
        with self.assertRaises(ValueError):c.confined('/tmp/root','../escape')
    def test_prompt_native_hash(self):
        self.assertEqual(c.prompt_hash([1,2]),hashlib.sha256(b'[1,2]').hexdigest())
    def test_bool_not_integer(self):
        with self.assertRaises(ValueError):c.exact_int(True,0,40,'integer')
    def test_geomean(self):self.assertAlmostEqual(c.geomean([2,.5]),1.)
    def test_geomean_nan(self):
        with self.assertRaises(ValueError):c.geomean([float('nan')])
    def test_empty_mean(self):
        with self.assertRaises(ValueError):c.geomean([])
    def test_git_blob(self):self.assertEqual(c.git_blob(b''),'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')

class PanelTests(unittest.TestCase):
    def test_balanced(self):
        p=panel();self.assertEqual(len(p['inputs']),12)
        for k in d.STRATA:self.assertEqual(sum((x['domain'],x['stratum'])==k for x in p['inputs']),3)
    def test_order_invariance(self):self.assertEqual(panel(),d.select_panel(list(reversed(candidates())),exposure()))
    def test_exposure_ids(self):
        e=exposure();e['input_ids']=[panel()['inputs'][0]['id']]
        self.assertNotIn(e['input_ids'][0],[x['id'] for x in d.select_panel(candidates(),e)['inputs']])
    def test_exposure_text(self):
        e=exposure();e['text_sha256']=[panel()['inputs'][0]['text_sha256']]
        self.assertNotIn(e['text_sha256'][0],[x['text_sha256'] for x in d.select_panel(candidates(),e)['inputs']])
    def test_exposure_tokens(self):
        e=exposure();e['prompt_ids_sha256']=[panel()['inputs'][0]['prompt_ids_sha256']]
        self.assertNotIn(e['prompt_ids_sha256'][0],[x['prompt_ids_sha256'] for x in d.select_panel(candidates(),e)['inputs']])
    def test_incomplete_exposure(self):
        e=exposure();e['coverage_review_complete']=False
        with self.assertRaises(ValueError):d.select_panel(candidates(),e)
    def test_shortage(self):
        with self.assertRaises(ValueError):d.select_panel(candidates()[:3],exposure())
    def test_wrong_length(self):
        x=candidates();x[0]['stratum']='long'
        with self.assertRaises(ValueError):d.select_panel(x,exposure())
    def test_duplicates_not_new_tasks(self):
        self.assertEqual(panel(),d.select_panel(candidates()+candidates(),exposure()))
    def test_hash_mutation(self):
        x=item(1);x['prompt_ids'][0]+=1
        with self.assertRaises(ValueError):d.input_check(x)
    def test_cap_mutation(self):
        x=item(1);x['cap']=64
        with self.assertRaises(ValueError):d.input_check(x)
    def test_input_overflow(self):
        with self.assertRaises(ValueError):d.input_check(item(1,n=900))

class ScheduleTests(unittest.TestCase):
    def test_pilot40(self):self.assertEqual(len(d.slots({'inputs':candidates()[:4]},'pilot')),40)
    def test_qualification120(self):self.assertEqual(len(d.slots(panel(),'qualification')),120)
    def test_formal576(self):self.assertEqual(len(timing()),576)
    def test_total736(self):self.assertEqual(40+120+len(timing()),736)
    def test_unique(self):
        rows=timing();self.assertEqual(len({r['slot']['slot_id'] for r in rows}),576)
    def test_warmup_pairing(self):
        r=d.slots(panel(),'formal',0)
        for a,b in zip(r[::2],r[1::2]):
            self.assertEqual((a['source_index'],a['experiment_arm']),(b['source_index'],b['experiment_arm']))
            self.assertEqual((a['category'],b['category']),('warmup','measured'))
    def test_aggregate_position_balance(self):
        rows=d.slots(panel(),'formal',0);positions={a:[0]*6 for a in c.ARMS}
        for i in range(12):
            arms=[r['experiment_arm'] for r in rows if r['source_index']==i and r['category']=='measured']
            for j,a in enumerate(arms):positions[a][j]+=1
        self.assertTrue(all(v==[2]*6 for v in positions.values()))
    def test_alias_preserves_native_arm(self):self.assertEqual(d.spec('C_PQ_A')['arm'],d.spec('C_PQ_B')['arm'])
    def test_R_selector(self):self.assertEqual(d.spec('R')['layout_selector'],1)
    def test_contexts(self):
        self.assertEqual(d.spec('R')['target_ub'],1)
        self.assertTrue(all(d.spec(a)['target_ub']==4 for a in c.ARMS if a!='R'))
    def test_no_draft_in_M(self):self.assertFalse(d.spec('M_QB')['draft_enabled'])
    def test_k3(self):self.assertEqual(d.spec('C_QB')['k'],3)

class AnalysisTests(unittest.TestCase):
    def test_known_means(self):
        x=d.analyze(timing());self.assertAlmostEqual(x['primary_ratio'],.9)
        self.assertAlmostEqual(x['means']['D_QB'],.7/.9);self.assertTrue(x['practical_screen_pass'])
    def test_duplicate(self):
        r=timing();r[-1]=r[0]
        with self.assertRaises(ValueError):d.analyze(r)
    def test_missing(self):
        with self.assertRaises(ValueError):d.analyze(timing()[:-1])
    def test_nan(self):
        r=timing();r[5]['service_seconds']=float('nan')
        with self.assertRaises(ValueError):d.analyze(r)
    def test_wrong_session(self):
        r=timing();r[0]['slot']['session']=4
        with self.assertRaises(ValueError):d.analyze(r)
    def test_noise_screen(self):
        r=timing()
        for x in r:
            if x['slot']['experiment_arm']=='C_PQ_A':x['service_seconds']=1.4
        self.assertFalse(d.analyze(r)['practical_screen_pass'])
    def test_session_reversal(self):
        r=timing()
        for x in r:
            if x['slot']['session']==0 and x['slot']['experiment_arm']=='C_QB':x['service_seconds']=1.01
        self.assertFalse(d.analyze(r)['practical_screen_pass'])
    def test_small_effect(self):
        r=timing()
        for x in r:
            if x['slot']['experiment_arm']=='C_QB':x['service_seconds']=.99
        self.assertFalse(d.analyze(r)['practical_screen_pass'])
    def test_warmups_not_in_estimate(self):
        r=timing()
        for x in r:
            if x['slot']['category']=='warmup':x['service_seconds']=999.
        self.assertAlmostEqual(d.analyze(r)['primary_ratio'],.9)
    def test_no_population_CI(self):self.assertIsNone(d.analyze(timing())['confidence_interval'])

class EndpointTests(unittest.TestCase):
    def good(self):return {'ids':[7,151645],'eog':[False,True],'length':2,'terminal_id':151645,'stop_reason':'EOG'}
    def test_endpoint(self):self.assertEqual(c.endpoint(self.good()),self.good())
    def test_truncation(self):
        x=self.good();x['eog']=[False,False];x['stop_reason']='CAP'
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_terminal(self):
        x=self.good();x['terminal_id']=8
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_early_eog(self):
        x=self.good();x['eog']=[True,True]
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_boolean_length(self):
        x={'ids':[151645],'eog':[True],'length':True,'terminal_id':151645,'stop_reason':'EOG'}
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_boolean_terminal(self):
        x={'ids':[1],'eog':[True],'length':1,'terminal_id':True,'stop_reason':'EOG'}
        with self.assertRaises(ValueError):c.endpoint(x)
    def test_bool_id(self):
        x=self.good();x['ids'][0]=True
        with self.assertRaises(ValueError):c.endpoint(x)

class GeometryTests(unittest.TestCase):
    def fixture(self,scope='QB',ngl=24):
        return {'observed_scope':scope,'cycles':[{}],'geometry':[
            {'name':f'kq-{i}','op':'MUL_MAT','phase':phase,'device':'RTX 5070 Ti' if i>=41-ngl else 'CPU',
             'device_type':1 if i>=41-ngl else 0,
             'sources':[{'ne':[128,512,8,1]},{'ne':[128,1,40,4 if scope=='QB' else 1]}]}
            for phase in ('PREFILL','VERIFY') for i in range(40)]}
    def test_all40(self):self.assertEqual(len(d.phases_map(self.fixture(),24)['VERIFY']),40)
    def test_output_layer_counts_toward_offload(self):
        for ngl,first in ((24,17),(20,21),(16,25)):
            observed=d.phases_map(self.fixture(ngl=ngl),ngl)['VERIFY']
            self.assertEqual([i for i,v in observed.items() if v=='GPU'],list(range(first,40)))
    def test_reject_old_off_by_one(self):
        x=self.fixture();x['geometry'][16]['device']='RTX 5070 Ti';x['geometry'][16]['device_type']=1
        with self.assertRaises(ValueError):d.phases_map(x,24)
    def test_wrong_heads(self):
        x=self.fixture();x['geometry'][0]['sources'][1]['ne'][2]=32
        with self.assertRaises(ValueError):d.phases_map(x,24)
    def test_missing_layer(self):
        x=self.fixture();x['geometry']=x['geometry'][:-1]
        with self.assertRaises(ValueError):d.phases_map(x,24)
    def test_wrong_device(self):
        x=self.fixture();x['geometry'][0]['device']='RTX 5070 Ti';x['geometry'][0]['device_type']=1
        with self.assertRaises(ValueError):d.phases_map(x,24)
    def test_unallocated(self):
        x=self.fixture();x['geometry'][0]['device']='UNALLOCATED'
        with self.assertRaises(ValueError):d.phases_map(x,24)
    def test_PQ(self):self.assertEqual(len(d.phases_map(self.fixture('PQ'),24)['VERIFY']),40)
    def test_bad_QB(self):
        x=self.fixture();x['geometry'][0]['sources'][1]['ne']=[128,4,40,1]
        with self.assertRaises(ValueError):d.phases_map(x,24)

class NativePatchTests(unittest.TestCase):
    def test_missing_anchor(self):
        with self.assertRaises(ValueError):native.replace_once('a','b','c')
    def test_duplicate_anchor(self):
        with self.assertRaises(ValueError):native.replace_once('aa','a','b')
    def test_simple_patch(self):self.assertEqual(native.replace_once('abc','b','x'),'axc')
    def test_upstream_drift(self):
        with patch('subprocess.check_output',return_value=b'wrong bytes'):
            with self.assertRaises(ValueError):c.upstream_bytes(Path('.'),'worker.cpp')
    def test_unknown_upstream(self):
        with self.assertRaises(ValueError):c.upstream_bytes(Path('.'),'unknown.cpp')
    def test_source_pins(self):self.assertEqual(len(c.PINS),4)

class GgufTests(unittest.TestCase):
    def test_wrong_magic(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x';p.write_bytes(b'XXXX')
            with self.assertRaises(ValueError):mi.inspect(p)
    def test_bad_version(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x';p.write_bytes(b'GGUF'+struct.pack('<I',99))
            with self.assertRaises(ValueError):mi.inspect(p)
    def test_truncated(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x';p.write_bytes(b'GGUF'+struct.pack('<I',3))
            with self.assertRaises(ValueError):mi.inspect(p)
    def test_wrong_target(self):
        with self.assertRaises(ValueError):mi.target_contract({'metadata':{'general.architecture':'llama'}})


class ArchiveTests(unittest.TestCase):
    def test_reopened_members(self):
        import archive
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'raw';root.mkdir();(root/'a.json').write_text('{}');(root/'b.f32').write_bytes(b'1234')
            r=archive.pack(root,Path(td)/'zip',limit=3)
            self.assertEqual(len(r['files']),2);self.assertEqual(len(r['parts']),2)
            self.assertFalse(r['remote_uploaded'])
    def test_forbid_weights(self):
        import archive
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'raw';root.mkdir();(root/'m.gguf').write_bytes(b'data')
            with self.assertRaises(ValueError):archive.pack(root,Path(td)/'zip')
    def test_private_paths_excluded(self):
        import archive
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'raw';root.mkdir();(root/'a.json').write_text('{}');(root/'LOCAL_PATHS.json').write_text('{}')
            r=archive.pack(root,Path(td)/'zip');self.assertEqual(len(r['files']),1)

class FullArtifactTests(unittest.TestCase):
    """Exercises the artifact reader with full-size synthetic vocabulary vectors."""
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.panel={'inputs':candidates()[:4]};cls.slots=d.slots(cls.panel,'pilot')
        cls.binding={'is_synthetic':True,'families':{'Qwen':{'fixture':True}},'dense14b':{'target_gpu_layers':24}}
        cls.vector_cache={}
        def vec(token):
            if token not in cls.vector_cache:
                b=bytearray(151936*4);struct.pack_into('<f',b,token*4,1.);cls.vector_cache[token]=bytes(b)
            return cls.vector_cache[token]
        for s in cls.slots:
            x=cls.panel['inputs'][s['source_index']];base=len(x['prompt_ids']);end=EndpointTests().good();C=s['draft_enabled']
            cyc={'cycle':0,'base':base,'seed':7,'proposals':[11,12,13],'decisions':[151645,66,77,88],
                 'accepted':0,'rejected':True,'commit_kind':'correction','output_length':2,'pending_after':None,
                 'done':True,'keep':base+1,'target_before':{'min':0,'max':base-1},'draft_before':{'min':0,'max':base-1},
                 'target_after':{'min':0,'max':base},'draft_after':{'min':0,'max':base},'caller_rows':4}
            r={'slot':s,'identity':cls.binding['families']['Qwen'],'prompt_ids':x['prompt_ids'],
               'prompt_ids_sha256':x['prompt_ids_sha256'],'capture':s['observer']=='heavy','arm':s['arm'],
               'k':s['k'],'draft_enabled':C,'observed_scope':s['scope'],'lifecycle':'resident','endpoint':end,**end,
               'vocabulary_eog':[151645],'cycles':[cyc] if C else [],'target_final_kv':{'min':0,'max':base},
               'draft_final_kv':{'min':0,'max':base} if C else None,'target_calls':2,'draft_calls':5 if C else 0,
               'service_seconds':1.,'synthetic_fixture':True}
            g=GeometryTests().fixture('QB' if s['scope']=='QB' else 'PQ')['geometry']
            r['geometry']=[a for a in g if a['phase']=='PREFILL' or C]
            folder=cls.root/s['slot_id']
            if r['capture']:
                target=folder/'target';target.mkdir(parents=True)
                (target/'initial.f32').write_bytes(vec(7))
                if C:
                    draft=folder/'draft';draft.mkdir()
                    for j,token in enumerate(cyc['proposals']):(draft/f'proposal-0-{j}.f32').write_bytes(vec(token))
                    for j,token in enumerate(cyc['decisions']):(target/f'verify-0-{j}.f32').write_bytes(vec(token))
                else:(target/'ordinary-1.f32').write_bytes(vec(151645))
                for role in ('target','draft') if C else ('target',):
                    p=folder/(role+'_final.state');p.write_bytes((role+':fixture-state').encode())
                    r[role+'_state']={'bytes':p.stat().st_size,'sha256':c.file_hash(p)}
            c.save(cls.root/(s['slot_id']+'.json'),r)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def audit(self):
        # This simple stub does not replace the pinned native-transaction auditor.
        def stub(r,x,m):
            if r['draft_enabled']:
                self.assertEqual(r['cycles'][0]['caller_rows'],4)
        return d.qualification(self.root,self.panel,self.slots,self.binding,stub)
    def test_complete_raw_matrix(self):
        x=self.audit();self.assertEqual(x['status'],'PASS');self.assertEqual(x['records'],40)
        self.assertTrue(all(p['full_logits_equal'] for p in x['paired_diagnostics']))
    def test_common_reference_failure(self):
        slot=next(s for s in self.slots if s['arm']=='M_QB' and s['observer']=='off')
        p=self.root/(slot['slot_id']+'.json');old=p.read_bytes();r=c.read(p)
        r['endpoint']['ids'][0]=8;r['ids'][0]=8;c.save(p,r)
        try:self.assertEqual(self.audit()['status'],'UNQUALIFIED')
        finally:p.write_bytes(old)
    def test_missing_raw_vector(self):
        slot=next(s for s in self.slots if s['arm']=='C_PQ' and s['observer']=='heavy')
        p=self.root/slot['slot_id']/'target'/'verify-0-3.f32';old=p.read_bytes();p.unlink()
        try:self.assertEqual(self.audit()['status'],'UNQUALIFIED')
        finally:p.write_bytes(old)
    def test_internal_difference_not_false_endpoint_failure(self):
        slot=next(s for s in self.slots if s['arm']=='M_QB' and s['observer']=='heavy')
        p=self.root/slot['slot_id']/'target'/'initial.f32';old=p.read_bytes();b=bytearray(old);struct.pack_into('<f',b,40,.01);p.write_bytes(b)
        try:
            r=self.audit();self.assertEqual(r['status'],'PASS')
            self.assertTrue(any(not x['full_logits_equal'] for x in r['paired_diagnostics']))
        finally:p.write_bytes(old)

if __name__=='__main__':unittest.main(verbosity=2)
