"""CPU integration gates for prospective per-arm selection. No native starts."""
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import experiment as e

RAW=Path(__file__).parent/'execution_20261014/raw'

class RuntimeAdapterTests(unittest.TestCase):
    def fixtures(self, root):
        for n in ('NATIVE_BUILD.json','NATIVE_BUILD_V02.json'):
            shutil.copyfile(RAW/n, root/n)
        manifest=e.runtime_manifest(root)
        e.save(root/'RUNTIME_MANIFEST.json',manifest)
        return manifest

    def test_all_fifteen_routes_have_exact_pr98_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); m=self.fixtures(root)
            self.assertEqual(len(m['routes']),15)
            corrected={(r['family'],r['arm']) for r in m['routes'] if r['binary']=='llama-server-pq-metadata4.exe'}
            self.assertEqual(corrected,{(f,a) for f in ('SmolLM2','Llama') for a in ('M_PQ','C_PQ')})
            for r in m['routes']:
                self.assertEqual(r['binary_sha256'],e.read(root/r['build_manifest'])['server_sha256'])

    def test_changed_build_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixtures(root)
            (root/'NATIVE_BUILD_V02.json').write_text('{}')
            with self.assertRaises(ValueError):e.runtime_manifest(root)

    def test_mutated_route_rejected_before_native_load(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);m=self.fixtures(root)
            m['routes'][0]['binary_sha256']='0'*64
            (root/'RUNTIME_MANIFEST.json').write_bytes(e.encoded(m))
            with self.assertRaises(ValueError):e.verify_runtime_manifest(root)

    def test_worker_command_and_identity_share_one_arm_and_restore_helper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);m=self.fixtures(root)
            base_read=e.read
            class FakeResident:
                def __init__(self,*args):
                    self.cmd=['original.exe'];self.d=root/'stub';self.d.mkdir(exist_ok=True)
                    self.phase='formal'
                def __enter__(self):
                    self.observed_build=native.read(root/'NATIVE_BUILD.json');return self
                def verify_modules(self,obs):self.verified=True
            native=SimpleNamespace(read=base_read,Resident=FakeResident)
            route=next(r for r in m['routes'] if (r['family'],r['arm'])==('Llama','C_PQ'))
            with mock.patch.object(e,'sha',return_value=route['binary_sha256']):
                w=e.runtime_worker(native,root,None,'Llama',e.condition('C_PQ'),'formal','stub')
                with w:
                    self.assertEqual(Path(w.cmd[0]).name,'llama-server-pq-metadata4.exe')
                    self.assertEqual(w.observed_build['source_inventory_sha256'],route['source_inventory_sha256'])
                    w.verify_modules({'modules':[w.cmd[0]]})
                    self.assertTrue(w.verified)
                self.assertIs(native.read,base_read)

    def test_wrong_loaded_executable_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);m=self.fixtures(root)
            class FakeResident:
                def __init__(self,*args):self.cmd=['original.exe'];self.d=root/'stub'
            native=SimpleNamespace(read=e.read,Resident=FakeResident)
            route=next(r for r in m['routes'] if (r['family'],r['arm'])==('SmolLM2','M_PQ'))
            with mock.patch.object(e,'sha',return_value=route['binary_sha256']):
                w=e.runtime_worker(native,root,None,'SmolLM2',e.condition('M_PQ'),'formal','stub')
                with self.assertRaises(ValueError):w.verify_modules({'modules':['other.exe']})

    def test_original_failed_attempt_schedule_is_preserved(self):
        old=e.read(Path(__file__).parent/'execution_20261014/UNREGISTERED_PLAN.json')
        self.assertEqual(old['blocks'],e.schedule(old['panel']))
        self.assertEqual(sum(1+len(b['tasks']) for b in old['blocks']),1620)

if __name__=='__main__':unittest.main(verbosity=2)
