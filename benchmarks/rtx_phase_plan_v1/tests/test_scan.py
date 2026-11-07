import importlib.util, unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'analysis/b570_online_scan.py'
s=importlib.util.spec_from_file_location('scan',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class ScanTests(unittest.TestCase):
 def test_volume(self):
  a=m.scan_published()['active_payload_lower_bound'];self.assertEqual(a['bytes_per_active_token'],196608);self.assertEqual(a['mean_three_exports_plus_one_import_MiB'],337.5)
 def test_cost(self):
  a=m.scan_published();self.assertAlmostEqual(a['fastest_speculative_over_M'],9.3546908,places=5);self.assertGreater(a['fraction_of_spec_service_to_remove_for_parity'],.89)
 def test_unmeasured(self):self.assertTrue(all(v is None for v in m.scan_published()['unmeasured_seconds'].values()))
 def test_partition(self):
  p=m.partitions(dict(service_ms=112,whole_request_ms=110,prefill_ms=10,generation_ms=95));self.assertEqual(p['host_reset_setup_cleanup_residual_ms'],5);self.assertEqual(p['capture_finish_ms'],2)
 def test_overlap(self):
  with self.assertRaises(ValueError):m.partitions(dict(service_ms=100,whole_request_ms=110,prefill_ms=10,generation_ms=95))
 def test_nan(self):
  with self.assertRaises(ValueError):m.number({'x':float('nan')},'x')
 def test_bool(self):
  with self.assertRaises(ValueError):m.number({'x':True},'x')
if __name__=='__main__':unittest.main()
