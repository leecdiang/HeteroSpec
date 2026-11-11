import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capacity import estimate
class Capacity(unittest.TestCase):
 def model(self,layers,size):return dict(file_bytes=size,metadata={'general.architecture':'qwen3','qwen3.block_count':layers,'qwen3.attention.head_count_kv':8,'qwen3.attention.head_count':40,'qwen3.embedding_length':5120})
 def test_d14(self):
  r=estimate(self.model(40,15698533728),self.model(28,639446688),4096);self.assertEqual(r['target_KV_bytes']+r['draft_KV_bytes'],1140850688);self.assertEqual(r['actual_admission'],'NOT_ESTABLISHED')
 def test_capacity_is_new(self):self.assertEqual(estimate(self.model(40,1),self.model(28,1),1024)['context'],1024)
 def test_context_guard(self):
  with self.assertRaises(ValueError):estimate(self.model(40,1),self.model(28,1),8192)
if __name__=='__main__':unittest.main()
