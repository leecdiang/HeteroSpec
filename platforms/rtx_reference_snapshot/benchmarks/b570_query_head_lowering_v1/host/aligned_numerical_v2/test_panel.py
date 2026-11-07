"""CPU tests only. Synthetic analyzer files are never native/GPU evidence."""
import copy
import json
import math
import pathlib
import struct
import tempfile
import unittest
from unittest import mock
from panel_common import HERE,ROOT,MODES,STAGES,load,sha,serialize,parse,digest,build_plan
from reference import solve,fp64_metrics,decode
from analyzer import validate_semantics,normalize,analyze_files,compare,payloads
from native_audit import audit_capability,audit_raw,audit_lifecycle,walk_ids

def synthetic(folder,request,desc,logical):
    """Generate labeled CPU fixtures by independent physical row loops."""
    folder=pathlib.Path(folder);dest=folder/'vectors';dest.mkdir(parents=True)
    g=request['cell']['geometry'];q,n,h=(g[k] for k in ('q','n','h'));mode=request['mode']
    for stage,prefix,extent in (('QK','qk',n),('softmax','sm',n),('AV','av',128)):
        v=logical[stage]
        for part in desc['stages']:
            if mode=='PQ' and q>1:values=v[part['part']*h*extent:(part['part']+1)*h*extent]
            elif mode=='REPEAT4' and q>1:values=v
            else:
                values=[]
                for head in range(h):
                    for j in range(q):values.extend(v[(j*h+head)*extent:(j*h+head+1)*extent])
            (dest/f'{prefix}-{part["part"]}.f32').write_bytes(b''.join(struct.pack('<f',x) for x in values))
    (dest/'final.f32').write_bytes(b''.join(struct.pack('<f',x) for x in logical['final']))
    data=pathlib.Path(request['input']).read_bytes()
    for i,b in enumerate(payloads(data,request)):
        (dest/f'input-{i}.before.bin').write_bytes(b);(dest/f'input-{i}.after.bin').write_bytes(b)
    (folder/'CPU_ANALYZER_FIXTURE.json').write_text('{"origin":"SYNTHETIC_CPU_ANALYZER_TEST_NOT_GPU"}')

class PanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=load(HERE/'INPUTS.json');cls.plan=load(HERE/'PLAN.json');cls.wires=load(HERE/'WIRES.json')
        cls.graphs=load(HERE/'EXPECTED_GRAPHS.json');cls.binding=sha(HERE/'EXECUTION_BINDING.json')
        cls.cells={x['id']:x for x in cls.inputs}
    def request(self,q=2,mode='PQ',n=63,hk=2):
        s=next(s for s in self.plan['slots'][1:] if s['q']==q and s['mode']==mode and self.cells[s['input_id']]['cell']['geometry']['n']==n and self.cells[s['input_id']]['cell']['geometry']['hk']==hk)
        return parse(serialize(s,self.inputs,self.binding))
    def graph(self,r):return self.graphs[digest(r['cell'])+'/'+r['mode']]
    def test_exact160_and_q1_first(self):
        self.assertEqual(build_plan(self.inputs),self.plan)
        self.assertEqual(len(self.plan['slots']),161)
        self.assertTrue(all(s['q']==1 for s in self.plan['slots'][1:41]))
        self.assertTrue(all(s['q']>1 for s in self.plan['slots'][41:]))
        keys=[(s['input_id'],s['mode'],s['repeat']) for s in self.plan['slots'][1:]]
        self.assertEqual(len(set(keys)),160)
    def test_all_actual_wire_files_from_serializer(self):
        for slot,wire in zip(self.plan['slots'],self.wires):
            self.assertEqual((HERE/wire['path']).read_bytes(),serialize(slot,self.inputs,self.binding))
            self.assertEqual(sha(HERE/wire['path']),wire['sha256'])
    def test_native_parser_all161_and_same240_descriptors(self):
        rows=[parse(x) for x in pathlib.Path(load(HERE/'CPU_NATIVE_MANIFEST.json')['raw_path']).read_text().splitlines()]
        self.assertEqual(rows[0]['event'],'CPU_START');self.assertEqual(rows[-1]['event'],'CPU_CLOSE')
        counts={w['slot_id']:0 for w in self.wires}
        requests={w['slot_id']:load(HERE/w['path']) for w in self.wires}
        for row in rows[1:-1]:
            self.assertEqual(row['request'],requests[row['slot_id']]);counts[row['slot_id']]+=1
            self.assertEqual(row['graph'],self.graphs[digest(row['cell'])+'/'+row['mode']])
        self.assertEqual(sum(counts.values()),240)
        self.assertEqual(counts[self.plan['slots'][0]['id']],80)
        self.assertTrue(all(counts[s['id']]==1 for s in self.plan['slots'][1:]))
        for row in (rows[0],rows[-1]):
            self.assertFalse(any('vulkan' in p.lower() or 'ggml-cpu' in p.lower() or 'igvk' in p.lower() for p in row['modules']))
    def test_all80_independent_addresses_GQA_mask_KV(self):
        for item in self.inputs:
            data=pathlib.Path(item['path']).read_bytes();self.assertEqual(sha(item['path']),item['sha256'])
            for mode in MODES:
                r=dict(cell=item['cell'],mode=mode)
                result=validate_semantics(r,self.graph(r),data)
                self.assertGreater(result['Q_byte_addresses'],0)
    def test_q1_graph_metadata_identical_all_modes(self):
        for item in self.inputs:
            if item['cell']['geometry']['q']!=1:continue
            graphs=[self.graph(dict(cell=item['cell'],mode=m)) for m in MODES]
            self.assertTrue(all(g==graphs[0] for g in graphs))
    def test_bad_bound_PQ_mask_rejected_disconnected_old_view_not_gate(self):
        r=self.request();desc=copy.deepcopy(self.graph(r));ts={t['id']:t for t in desc['tensors']}
        # Rebind to old j1 view; it is otherwise retained and valid as metadata.
        old=next(t for t in ts.values() if t['op']=='VIEW' and t['view_root']==desc['mask'] and t['view_offset']==252)
        ts[desc['stages'][1]['softmax']]['src'][1]=old['id']
        with self.assertRaisesRegex(ValueError,'bound slab'):validate_semantics(r,desc,pathlib.Path(r['input']).read_bytes())
    def test_wrong_QH_KV_owner_rejected(self):
        r=self.request(mode='QH_C');d=copy.deepcopy(self.graph(r));d['K']=d['V']
        with self.assertRaises(ValueError):validate_semantics(r,d,pathlib.Path(r['input']).read_bytes())
    def test_wrong_GQA_tensor_shape_rejected(self):
        r=self.request(mode='QH_C');d=copy.deepcopy(self.graph(r));d['tensors'][d['K']]['ne'][2]=1
        with self.assertRaises(ValueError):validate_semantics(r,d,pathlib.Path(r['input']).read_bytes())
    def test_independent_analytic_FP64_GQA_and_causal_mask(self):
        q,n,h,hk=2,2,4,2;Q=[0.]*(q*h*128);K=[0.]*(hk*n*128)
        V=[x for group in range(hk) for d in range(128) for x in ((1.,3.) if group==0 else (9.,11.))]
        mask=[0.,-math.inf,0.,0.]+[-math.inf]*(32*n-4)
        data=struct.pack('<7i',q,n,h,hk,1,0,0)+b''.join(struct.pack('<f',x) for x in Q)+b''.join(struct.pack('<e',x) for x in K+V)+b''.join(struct.pack('<f',x) for x in mask)
        ref=solve(data)
        self.assertEqual(ref['QK'],[0.]*(q*h*n))
        self.assertEqual(ref['AV'],[v for row in ((1.,1.,9.,9.),(2.,2.,10.,10.)) for head,v0 in enumerate(row) for v in [v0]*128])
    def test_full_layout_restoration_all80_labeled_vectors(self):
        for item in self.inputs:
            g=item['cell']['geometry'];q,h,n=(g[k] for k in ('q','h','n'))
            logical={s:[float(j*100000+head*1000+e) for j in range(q) for head in range(h) for e in range(n if s in ('QK','softmax') else 128)] for s in STAGES}
            for mode in MODES:
                r=dict(cell=item['cell'],mode=mode,input=item['path']);d=self.graph(r)
                with tempfile.TemporaryDirectory() as folder:
                    synthetic(folder,r,d,logical);got=normalize(r,d,folder)
                    for s in STAGES:self.assertEqual(got[s],b''.join(struct.pack('<f',x) for x in logical[s]))
    def test_equal_wrong_outputs_still_have_independent_FP64_error(self):
        r=self.request();data=pathlib.Path(r['input']).read_bytes();ref=solve(data)
        wrong={s:list(ref[s]) for s in STAGES};wrong['QK']=[x+1. for x in wrong['QK']]
        wrong['AV']=[x+1. for x in wrong['AV']];wrong['final']=list(wrong['AV'])
        with tempfile.TemporaryDirectory() as folder:
            synthetic(folder,r,self.graph(r),wrong);analysis,logical=analyze_files(r,self.graph(r),folder,data,ref)
            self.assertTrue(compare(logical,logical)['all_stages_bitwise_equal'])
            self.assertGreater(analysis['FP64_error']['QK']['max_abs'],.9)
            self.assertIsNone(analysis['numerical_PASS_tolerance'])
    def test_truncated_or_nonfinite_full_vector_rejected(self):
        r=self.request(mode='QH_C');ref=solve(pathlib.Path(r['input']).read_bytes())
        for bad in (b'\x00',struct.pack('<f',math.nan)*len(ref['final'])):
            with tempfile.TemporaryDirectory() as folder:
                synthetic(folder,r,self.graph(r),ref);(pathlib.Path(folder)/'vectors/final.f32').write_bytes(bad)
                with self.assertRaises(ValueError):normalize(r,self.graph(r),folder)
    def test_mutated_input_slab_rejected(self):
        r=self.request();data=pathlib.Path(r['input']).read_bytes();ref=solve(data)
        with tempfile.TemporaryDirectory() as folder:
            synthetic(folder,r,self.graph(r),ref);p=pathlib.Path(folder)/'vectors/input-5.after.bin';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
            with self.assertRaisesRegex(ValueError,'input before/after'):analyze_files(r,self.graph(r),folder,data,ref)
    def test_masked_nonzero_softmax_rejected(self):
        r=self.request();data=pathlib.Path(r['input']).read_bytes();ref=solve(data);ref['softmax'][62]=.1
        with tempfile.TemporaryDirectory() as folder:
            synthetic(folder,r,self.graph(r),ref)
            with self.assertRaisesRegex(ValueError,'masked softmax zero'):analyze_files(r,self.graph(r),folder,data)
    def test_stage_pair_first_divergence_not_tolerance(self):
        z=struct.pack('<f',0.);one=struct.pack('<f',1.);a={s:z for s in STAGES};b=dict(a);b['softmax']=one
        relation=compare(a,b);self.assertEqual(relation['first_bitwise_divergence_stage'],'softmax')
        self.assertEqual(relation['stages']['softmax']['bit_mismatches'],1)
    def test_FP64_rounding_descriptive_and_relative_zero_separate(self):
        x=1/3;rounded=struct.unpack('<f',struct.pack('<f',x))[0]
        m=fp64_metrics([rounded,1.],[x,0.]);self.assertGreater(m['max_abs'],0)
        self.assertEqual(m['relative_undefined_at_zero'],1);self.assertEqual(m['zero_reference_nonzero_actual'],1)
        self.assertEqual(fp64_metrics([rounded],[x])['max_ULP_against_F32_rounded_reference'],0)
    def test_partial_or_wrong_census_graph_rejected(self):
        r=self.request();d=self.graph(r);nodes=[dict(t,supports_op=True) for i in walk_ids(d) for t in [d['tensors'][i]]]
        self.assertTrue(audit_capability(d,nodes,d))
        with self.assertRaises(ValueError):audit_capability(d,nodes[:-1],d)
        altered=copy.deepcopy(d);altered['final']=0
        with self.assertRaises(ValueError):audit_capability(altered,nodes,d)
    def test_no_native_origin_forgery(self):
        with self.assertRaises(ValueError):audit_raw([dict(event='HOST_START',origin='CPU_METADATA')],{},1,{})
    def test_no_author_approval_no_launch(self):
        import run_panel
        with mock.patch.object(run_panel,'sha',return_value='a'*64),mock.patch('subprocess.Popen') as launch:
            with self.assertRaisesRegex(ValueError,'author approval'):run_panel.admission('b'*64)
            launch.assert_not_called()
    def test_unstarted_panel_has_all161_denominators(self):
        from reconstruct import reconstruct
        with tempfile.TemporaryDirectory() as folder:
            r=reconstruct(pathlib.Path(folder));self.assertEqual(len(r['unstarted']),161)
            self.assertFalse(r['full_domain_execution_inventory_complete']);self.assertEqual(r['attempts'],0)
    def test_watchdog_and_both_runtime_inventories_reconstructed(self):
        deps=[dict(path='C:/frozen/ggml-base.dll',sha256='base'),dict(path='C:/frozen/ggml-vulkan.dll',sha256='vk')]
        raw=[dict(event=n,modules=[x['path'] for x in deps]) for n in ('AWAIT_RUNTIME_GATE','CLOSE')]
        life=dict(returncode=0,stop=None,pid=123,creation_FILETIME=1234,owned_wall_s=.2,
            watchdog_samples=[dict(elapsed_s=.1,gap_ms=100,RSS=1024,host_available=16*1024**3,disk_free=16*1024**3,output_bytes=1024,archive_reserve_bytes=1024)],
            actual_runtime_modules=deps,closing_runtime_modules=deps)
        f0=dict(dependencies=deps,driver_files=[])
        self.assertEqual(audit_lifecycle(life,raw,f0)['module_gates'],2)
        for change in ('gap','budget','module','identity','exit'):
            bad=copy.deepcopy(life)
            if change=='gap':bad['owned_wall_s']=2.
            elif change=='budget':bad['watchdog_samples'][0]['output_bytes']=3*1024**3
            elif change=='module':bad['closing_runtime_modules'][1]['sha256']='wrong'
            elif change=='identity':bad['creation_FILETIME']=None
            else:bad['returncode']=50
            with self.assertRaises(ValueError):audit_lifecycle(bad,raw,f0)
    def test_incomplete_attempt_retained_without_output_fabrication(self):
        from reconstruct import reconstruct
        from panel_common import save
        with tempfile.TemporaryDirectory() as folder:
            folder=pathlib.Path(folder);(folder/self.plan['slots'][0]['id']).mkdir()
            result=reconstruct(folder)
            self.assertEqual(result['attempts'],1);self.assertEqual(len(result['failed_or_invalid']),1)
            self.assertEqual(len(result['unstarted']),160);self.assertFalse(result['full_domain_execution_inventory_complete'])
            self.assertTrue(result['inventory_errors']);self.assertEqual(result['observed_graph_calls'],0)
    def test_build_inputs_and_frozen_backend_identity_bound(self):
        bound=load(HERE/'BUILD_INPUTS.json');self.assertFalse(bound['backend_modified']);self.assertFalse(bound['backend_rebuilt'])
        self.assertTrue(any(x['path'].endswith('ggml-vulkan.cpp') for x in bound['frozen_backend_sources']))
        self.assertTrue(any(x['path'].endswith('ggml-base.lib') for x in bound['files']))
        for x in bound['files']+bound['frozen_backend_sources']:self.assertEqual(sha(x['path']),x['sha256'])
    def test_attempt_before_folder_and_graph_without_lifecycle_count(self):
        from reconstruct import reconstruct
        with tempfile.TemporaryDirectory() as folder:
            folder=pathlib.Path(folder);first=self.plan['slots'][0]
            (folder/'LEDGER.jsonl').write_text(json.dumps(dict(event='ATTEMPT',slot=first))+'\n')
            r=reconstruct(folder);self.assertEqual(r['attempts'],1);self.assertEqual(len(r['failed_or_invalid']),1)
            self.assertFalse(r['owned_time_complete']);self.assertEqual(len(r['unstarted']),160)
            rawdir=folder/first['id'];rawdir.mkdir();(rawdir/'raw.jsonl').write_text('{"event":"GRAPH_START"}\n')
            r=reconstruct(folder);self.assertEqual(r['observed_graph_calls'],1);self.assertFalse(r['owned_time_complete'])
    def test_freezer_resolves_own_preparation_module(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('_test_panel_freeze',HERE/'freeze.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(pathlib.Path(module._prepare.__file__).resolve(),HERE/'prepare.py')
        self.assertEqual(module.BASE,'74d8bee4fd738c67e2f08169beb5164bac5efe98')
