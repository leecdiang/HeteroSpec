import copy,hashlib,tempfile,unittest
from pathlib import Path
from receipt_validator import check_identity,BindingRefusal

class BoundIdentity(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.directory=Path(self.temp.name);dll=self.directory/'ggml-cuda.dll';dll.write_bytes(b'CPU_fixture_not_PE_not_loaded');self.sha=hashlib.sha256(dll.read_bytes()).hexdigest()
        self.expected={'arm':'C','linked_graph_core':'packed','graph_policy':'disabled_for_all_arms_draft_and_reference','exe_sha256':'a'*64,'job_sha256':'b'*64,'runtime_directory':str(self.directory),'modules':{'ggml-cuda.dll':{'path':str(dll),'sha256':self.sha}},'runtime_metadata':{'schema':'heterospec.e03.cpu-loader-mock.v1'},'provider_scope':'CPU_STANDIN'}
        self.actual={k:self.expected[k] for k in ('arm','linked_graph_core','graph_policy','exe_sha256','job_sha256','runtime_metadata')};self.actual.update(modules=copy.deepcopy(self.expected['modules']),actual_numeric_route_observed=False,observation_kind='CPU_STANDIN_LOAD')
    def tearDown(self):self.temp.cleanup()
    def test_mock_identity_never_admits_numeric_route_or_performance(self):
        r=check_identity(self.expected,self.actual);self.assertFalse(r['actual_numeric_DLL_loaded']);self.assertFalse(r['performance_admitted']);self.assertEqual(r['native_qualification'],'NOT_RUN')
    def test_old_foreign_resolution_and_missing_modules_refuse(self):
        b=copy.deepcopy(self.actual);b['modules']['ggml-cuda.dll']['path']=str(self.directory/'old/ggml-cuda.dll')
        with self.assertRaisesRegex(BindingRefusal,'old or foreign'):check_identity(self.expected,b)
        b=copy.deepcopy(self.actual);b['modules']={}
        with self.assertRaisesRegex(BindingRefusal,'missing/extra'):check_identity(self.expected,b)
    def test_changed_disk_hash_and_foreign_metadata_refuse(self):
        b=copy.deepcopy(self.actual);b['modules']['ggml-cuda.dll']['sha256']='f'*64
        with self.assertRaisesRegex(BindingRefusal,'disk hash'):check_identity(self.expected,b)
        b=copy.deepcopy(self.actual);b['runtime_metadata']={'schema':'other'}
        with self.assertRaisesRegex(BindingRefusal,'metadata'):check_identity(self.expected,b)
    def test_identity_cannot_claim_actual_route_or_upgrade_mock(self):
        b=copy.deepcopy(self.actual);b['actual_numeric_route_observed']=True
        with self.assertRaisesRegex(BindingRefusal,'executed numeric route'):check_identity(self.expected,b)
        b=copy.deepcopy(self.actual);b['observation_kind']='NUMERICAL_METADATA_LOAD'
        with self.assertRaisesRegex(BindingRefusal,'masquerade'):check_identity(self.expected,b)
    def test_wrong_core_arm_and_job_hash_refuse(self):
        for key,value in [('arm','A'),('linked_graph_core','loop4'),('job_sha256','c'*64)]:
            b=copy.deepcopy(self.actual);b[key]=value
            with self.assertRaisesRegex(BindingRefusal,'bound field mismatch'):check_identity(self.expected,b)
    def test_kind_string_does_not_prove_actual_numerical_DLL_load(self):
        frozen=copy.deepcopy(self.expected);frozen['provider_scope']='NUMERICAL_RUNTIME';frozen['runtime_metadata']={'schema':'heterospec.e03.cuda-runtime.v1'}
        actual=copy.deepcopy(self.actual);actual['observation_kind']='NUMERICAL_METADATA_LOAD';actual['runtime_metadata']=frozen['runtime_metadata']
        result=check_identity(frozen,actual);self.assertTrue(result['numeric_DLL_load_claimed']);self.assertIsNone(result['actual_numeric_DLL_loaded']);self.assertFalse(result['performance_admitted']);self.assertEqual(result['native_qualification'],'NOT_RUN')

if __name__=='__main__':unittest.main()
