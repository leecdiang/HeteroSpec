"""Host-only regression checks for the frozen work budget and admission rules."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from run_probe import clean_environment,validate_inputs,run_owned_native,partial_result_snapshot,validate_model_binding,pci_address,physical_gpu_binding,verify_cuda_visible_device,PUBLIC_TARGET_SHA

HERE=Path(__file__).resolve().parent


class Protocol(unittest.TestCase):
    def setUp(self):self.profile=json.loads((HERE/'inputs_cpu.json').read_text())

    def test_frozen_full_budget(self):
        self.assertEqual(validate_inputs(self.profile)['budget'],{'contexts':190,'native_calls':3032,'target_rows':68048})
        public=json.loads((HERE/'inputs_public.json').read_text())
        self.assertEqual(validate_inputs(public)['budget'],{'contexts':190,'native_calls':3032,'target_rows':68447})

    def test_fixed_scope_rejections(self):
        for key,value in [('q_values',[1,1]),('q_values',[0]),('q_values',[9]),('repeats',3),('threads',3)]:
            with self.subTest(key=key,value=value):
                bad=deepcopy(self.profile);bad[key]=value
                with self.assertRaises(ValueError):validate_inputs(bad)
        bad=deepcopy(self.profile);bad['cases'][0]['rows'][0]=True
        with self.assertRaises(ValueError):validate_inputs(bad)
        bad=deepcopy(self.profile);bad['cases']*=2
        with self.assertRaises(ValueError):validate_inputs(bad)

    def test_declared_env(self):
        with patch.dict(os.environ,{'GGML_CUDA_DISABLE_FUSION':'1','HS_SCOPE_MASK':'0','CUDA_VISIBLE_DEVICES':'7'},clear=True):
            env=clean_environment(Path('/bound-libs'),'cpu',None)
            self.assertEqual(env['LD_LIBRARY_PATH'],'/bound-libs');self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'')
            self.assertEqual(env['CUDA_DEVICE_ORDER'],'PCI_BUS_ID')
            self.assertNotIn('GGML_CUDA_DISABLE_FUSION',env);self.assertNotIn('HS_SCOPE_MASK',env)
        for name in ('LD_PRELOAD','LD_AUDIT'):
            with patch.dict(os.environ,{name:'/unbound.so'},clear=True):
                with self.assertRaises(ValueError):clean_environment(Path('/bound-libs'),'cpu',None)
        self.assertEqual(pci_address('00000000:0a:00.0'),pci_address('0000:0A:00.0'))
        with self.assertRaises(ValueError):pci_address('GPU-not-a-PCI-address')

    def test_fresh_output_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);existing=root/'existing';existing.mkdir();marker=existing/'marker';marker.write_text('retain')
            for target in [existing,root/'link']:
                if target.name=='link':target.symlink_to(root/'not-created',target_is_directory=True)
                result=subprocess.run([sys.executable,str(HERE/'run_probe.py'),'--inputs',str(HERE/'inputs_cpu.json'),'--output',str(target),'--plan-only'],capture_output=True)
                self.assertNotEqual(result.returncode,0);self.assertEqual(marker.read_text(),'retain');self.assertFalse((root/'not-created').exists())

    def test_owned_child_timeout_preserves_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            code="import pathlib,time;pathlib.Path('partial').write_text('preserved');print('owned child',flush=True);time.sleep(10)"
            # Run only a sleeping Python fixture, with no model/library or GPU access.
            argv=[sys.executable,'-c',"import os;os.chdir("+repr(str(root))+");"+code]
            result=run_owned_native(argv,root/'native',dict(os.environ),timeout=0.25)
            self.assertTrue(result['timed_out']);self.assertTrue(result['child_reaped'])
            self.assertLess(result['wall_seconds'],2);self.assertLess(result['returncode'],0)
            self.assertEqual((root/'partial').read_text(),'preserved')
            self.assertEqual((root/'native.stdout').read_text(),'owned child\n')
            with self.assertRaises(ProcessLookupError):os.kill(result['owned_pid'],0)
            broken=root/'RESULT.json';broken.write_text('{"status":')
            retained=partial_result_snapshot(broken)
            self.assertIn('partial_result_parse_error',retained)
            self.assertEqual(retained['partial_result']['bytes'],len(broken.read_bytes()))
            self.assertEqual(broken.read_text(),'{"status":')

    def test_public_model_identity_cannot_be_overridden(self):
        profile=json.loads((HERE/'inputs_public.json').read_text())
        self.assertEqual(validate_model_binding(profile,PUBLIC_TARGET_SHA)['status'],'ORIGINAL_PR213_TARGET_SHA_MATCHED')
        with self.assertRaises(ValueError):validate_model_binding(profile,'0'*64,'0'*64)
        altered=deepcopy(profile);altered['model_binding']['expected_sha256']='0'*64
        with self.assertRaises(ValueError):validate_model_binding(altered,PUBLIC_TARGET_SHA)

    def test_physical_gpu0_mig_and_ambiguity_rejections(self):
        good='0, 00000000:01:00.0, Disabled\n1, 00000000:02:00.0, N/A\n'
        self.assertEqual(physical_gpu_binding(good,1)['physical_index'],1)
        reordered='0, 00000000:03:00.0, Disabled\n1, 00000000:02:00.0, Disabled\n'
        self.assertEqual(physical_gpu_binding(reordered,1)['CUDA_PCI_order_ordinal'],0)
        for inventory,index in [(good,0),(good,-1),(good,2),(good.replace('N/A','Enabled'),1),
                                (good.replace('N/A','Unknown'),1),(good.replace('02:00.0','01:00.0'),1),
                                (good.replace('1,','0,'),1),('1, 0000:02:00.0, Disabled\n',1)]:
            with self.subTest(inventory=inventory,index=index):
                with self.assertRaises(ValueError):physical_gpu_binding(inventory,index)

    def test_visible_cuda_pci_binding_without_driver_execution(self):
        for bus,count,passes in [('0000:02:00.0',1,True),('0000:01:00.0',1,False),('0000:02:00.0',2,False)]:
            fake=SimpleNamespace(stdout=json.dumps({'pci_bus_id':bus,'visible_device_count':count,'model_forwards':0}))
            with patch('run_probe.subprocess.run',return_value=fake):
                if passes:self.assertEqual(verify_cuda_visible_device('00000000:02:00.0',{})['pci_bus_id'],bus)
                else:
                    with self.assertRaises(ValueError):verify_cuda_visible_device('00000000:02:00.0',{})


if __name__=='__main__':unittest.main()
