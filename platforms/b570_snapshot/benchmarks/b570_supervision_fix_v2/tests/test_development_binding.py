import copy,hashlib,subprocess,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'host'))
from development_binding import validate

class DevelopmentBinding(unittest.TestCase):
    def setUp(self):
        self.freeze={'scope':'source_review_only','review_status':'scoped-clean','bound_files':{'host/LauncherCapture.cs':'cs','host/controller.py':'controller'}}
        self.build={'source_review_sha256':'freeze','source_hashes':dict(self.freeze['bound_files']),'dll_sha256':'dll','compiler_sha256':'compiler','pid':42,'begin_ns':10,'end_ns':30,'exit_code':0,'argv':['C:/csc.exe','/target:library']}
        self.cfg={'source_review_sha256':'freeze','build_record_sha256':'build','code_hashes':{**self.freeze['bound_files'],'host/LauncherCapture.dll':'dll'}}
        self.ledger=[{'kind':'PROCESS_CREATE','pid':42,'created_filetime':123,'at_ns':20,'command_sha256':hashlib.sha256(subprocess.list2cmdline(self.build['argv']).encode()).hexdigest()},{'kind':'PROCESS_CLOSED','pid':42,'created_filetime':123,'exit_code':0}]
    def check(self):return validate(self.cfg,self.freeze,'freeze',self.build,'build',self.ledger)
    def test_reviewed_runtime_and_observed_build_pass(self):self.assertTrue(self.check())
    def test_restoring_packaged_source_cannot_hide_runtime_drift(self):
        self.cfg['code_hashes']['host/controller.py']='modified'
        with self.assertRaises(ValueError):self.check()
    def test_missing_or_extra_runtime_member_fails(self):
        del self.cfg['code_hashes']['host/controller.py']
        with self.assertRaises(ValueError):self.check()
    def test_old_review_cannot_qualify_runtime(self):
        self.cfg['source_review_sha256']='old'
        with self.assertRaises(ValueError):self.check()
    def test_unobserved_compiler_cannot_qualify_dll(self):
        self.ledger=[]
        with self.assertRaises(ValueError):self.check()
    def test_different_compiler_command_cannot_qualify_dll(self):
        self.build['argv'].append('/different')
        with self.assertRaises(ValueError):self.check()
    def test_failed_compiler_cannot_qualify_dll(self):
        self.ledger[1]['exit_code']=1
        with self.assertRaises(ValueError):self.check()
    def test_different_dll_cannot_qualify_runtime(self):
        self.cfg['code_hashes']['host/LauncherCapture.dll']='other'
        with self.assertRaises(ValueError):self.check()
