import array,copy,pathlib,tempfile,unittest,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import regression as r

class RegressionTests(unittest.TestCase):
    def test_model_specific_geometry(self):
        self.assertEqual(r.model_geometry('Qwen'),{'layers':36,'embd':4096})
        self.assertEqual(r.model_geometry('Llama'),{'layers':32,'embd':4096})
        with self.assertRaises(ValueError):r.model_geometry('unknown')
    def test_host_driver_changes_only_bound_family(self):
        _,before,after=r.derived_driver({})
        self.assertEqual(after,before.replace("'Qwen',str(bundle/","c['regression_family'],str(bundle/"))
        for guard in ['<=1200','<=480','job.wait_empty','save(lock','runtime RAM reserve','worker safety timeout']:
            self.assertIn(guard,after)
    def fixture(self,folder):
        folder.mkdir(exist_ok=True);(folder/'target').mkdir();a=array.array('f',[0.])*128256;a[2]=1.;(folder/'target/initial.f32').write_bytes(a.tobytes());(folder/'target_final.state').write_bytes(b'test')
        slot={'family':'Llama','observer':'heavy','repair':{'prefill':'native'}};item={'id':'CPU_FIXTURE','prompt_ids':[1],'prompt_ids_sha256':r.prompt_hash([1])};e={'ids':[2],'eog':[True],'length':1,'terminal_id':2,'stop_reason':'EOG'};ident={'fixture':True};binding={'families':{'Llama':ident}}
        record=dict(e,endpoint=e,slot=slot,family='Llama',identity=ident,input_id=item['id'],prompt_ids=item['prompt_ids'],prompt_ids_sha256=item['prompt_ids_sha256'],teacher_forced=False,qualification_eligible=True,observer_mode='off',repair_prefill='native',draft_enabled=False,cycles=[],prompt_tokens=1,vocabulary_eog=[2],target_final_kv={'max':0},target_state={'bytes':4,'sha256':r.file_hash(folder/'target_final.state')},geometry=[{'name':f'kq-{i}','op':'MUL_MAT','layer':i,'scheduler_backend':'CPU','buffer_owner_device':'CPU'} for i in range(32)])
        return record,slot,item,folder,binding
    def test_exact_llama_vocabulary_and_layer_count(self):
        with tempfile.TemporaryDirectory() as d:
            args=self.fixture(pathlib.Path(d));r.profile_check(*args)
            p=pathlib.Path(d)/'target/initial.f32';p.write_bytes(p.read_bytes()+b'\0'*4)
            with self.assertRaises(ValueError):r.profile_check(*args)
    def test_missing_layer_and_foreign_identity_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            args=self.fixture(pathlib.Path(d));args[0]['geometry'].pop()
            with self.assertRaises(ValueError):r.profile_check(*args)
            args[0]['identity']={'changed':True}
            with self.assertRaises(ValueError):r.profile_check(*args)
    def test_qwen36_coverage_rejects_llama32_geometry(self):
        with tempfile.TemporaryDirectory() as d:
            args=self.fixture(pathlib.Path(d));record,slot,_,folder,binding=args
            record['family']=slot['family']='Qwen';binding['families']['Qwen']=binding['families'].pop('Llama')
            a=array.array('f',[0.])*151936;a[2]=1.;(folder/'target/initial.f32').write_bytes(a.tobytes())
            with self.assertRaises(ValueError):r.profile_check(*args)
            record['geometry'] += [dict(record['geometry'][0],name=f'kq-{i}',layer=i) for i in range(32,36)]
            r.profile_check(*args)

if __name__=='__main__':unittest.main()
