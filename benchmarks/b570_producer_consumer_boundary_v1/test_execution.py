"""CPU tests of transport custody and fail-closed native disposition handling."""
import unittest
from execute import module_check, classify

class ExecutionTests(unittest.TestCase):
    def test_loaded_library_substitution_cannot_qualify(self):
        expected=[{'path':'C:/runtime/boundary.exe','sha256':'driver'},
                  {'path':'C:/runtime/ggml-vulkan.dll','sha256':'qualified'}]
        receipt={'loaded_module_hashes':[{'path':'C:/runtime/boundary.exe','sha256':'driver'},
                    {'path':'C:/other/ggml-vulkan.dll','sha256':'different'}]}
        self.assertFalse(module_check(receipt,expected))
        receipt['loaded_module_hashes'][1]['sha256']='qualified'
        self.assertTrue(module_check(receipt,expected))
        receipt['loaded_module_hashes'].insert(0,{'path':'C:/unexpected/ggml-vulkan.dll','sha256':'different'})
        self.assertFalse(module_check(receipt,expected))
        receipt['loaded_module_hashes'].pop(0)
        receipt['loaded_module_hashes'].pop()
        self.assertFalse(module_check(receipt,expected))

    def test_native_failure_keeps_original_reason_and_endpoint(self):
        for reason,status in [('actual restored boundary differs','RESTORE_SHAM_FAILED'),
                ('own-path vector sham failed','RESTORE_SHAM_FAILED'),
                ('unexpected producer geometry','GEOMETRY_NOT_ADMITTED'),
                ('raw payload budget exhausted','BUDGET_EXHAUSTED')]:
            row={'status':'TECHNICAL_FAILURE','reason':reason,'endpoint':{'ids':[123]}}
            classify(row)
            self.assertEqual(row,{'status':status,'reason':reason,'endpoint':{'ids':[123]}})

if __name__=='__main__':unittest.main()
