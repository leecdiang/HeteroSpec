import sys,unittest,json,tempfile
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import history,source
class HistoricalMappingTests(unittest.TestCase):
 def test_sparse_historical_panel_recovery(self):
  panel={'inputs':[None,None]+[{'id':i,'cap':128,'prompt_ids':[128000,42]} for i in history.DEVELOPMENT]}
  def payload(repo,ref,path):
   if path.endswith('PANEL.json'):return json.dumps(panel).encode()
   if path.endswith('EXECUTION_IDENTITY.json'):return b'{"families":{"Llama":{}}}'
   return b'{}'
  with tempfile.TemporaryDirectory() as d,patch.object(history,'git_bytes',side_effect=payload):
   out=history.recover('.',Path(d)/'history')
   self.assertEqual(json.loads((out/'panel.json').read_text()),panel)
   self.assertEqual([x['id'] for x in json.loads((out/'DEVELOPMENT.json').read_text())],history.DEVELOPMENT)
 def test_variable_accepted_prefix(self):
  r={'ids':[1,2,3,4,5],'draft_enabled':True,'cycles':[{'cycle':0,'seed':1,'output_length':2,'decisions':[2,8,9,10]}, {'cycle':1,'seed':2,'output_length':5,'decisions':[3,4,5,6]}]}
  m=history.decision_rows(r);self.assertEqual(m[2],'target/verify-1-0.f32');self.assertEqual(m[4],'target/verify-1-2.f32')
 def test_old_seed_error(self):
  r={'ids':[1,2],'draft_enabled':True,'cycles':[{'cycle':0,'seed':8,'output_length':2,'decisions':[2,3]}]}
  with self.assertRaises(ValueError):history.decision_rows(r)
 def test_ordinary_map(self):
  self.assertEqual(history.decision_rows({'ids':[1,2,3],'draft_enabled':False})[2],'target/ordinary-2.f32')
 def test_port_source_not_global_replace(self):
  s='// Exact E2 AV domain only.\n(a->ne[0] == 256 || a->ne[0] == 512)\n(b->ne[3] == 2 || b->ne[3] == 4)\nstatic void ggml_vk_mul_mat_vec_nc_f16_f32\nconst bool qb_batch_broadcast = (b->ne[3] == 2 || b->ne[3] == 4);\n(a->ne[1] == 256 || a->ne[1] == 512);\n(a->ne[0] == 256 || a->ne[0] == 512);\n(b->ne[3] == 2 || b->ne[3] == 4);\nif (!(ggml_vk_dim01_contiguous\nKEEP (b->ne[3] == 2 || b->ne[3] == 4)'
  r=source.vulkan_port(s);self.assertIn('KEEP (b->ne[3] == 2 || b->ne[3] == 4)',r);self.assertEqual(r.count('b->ne[3] <= 4'),3)
 def test_graph_mode_is_library_scope(self):
  s='#include "query_head.h"\n    // Private request bridge: immutable layout per fresh context, single-threaded host.\nold\n    const bool use_flash_attn = cparams.flash_attn && kq_b == nullptr;'
  r=source.graph_port(s);self.assertIn('hs_b570::mode',r);self.assertNotIn('HS_REQUEST_LAYOUT',r);self.assertIn('q->ne[1] <= 4',r)
if __name__=='__main__':unittest.main()
