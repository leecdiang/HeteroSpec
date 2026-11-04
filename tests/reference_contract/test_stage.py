import importlib.util
from pathlib import Path
import tempfile
import unittest
import subprocess
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('stage',ROOT/'scripts/reference_contract/stage.py')
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
GRAPH=stage.PACKED+'\n    // original numerical graph\n}\n    inp->reference_policy=hs_reference_policy_identity();\n    if (reference_policy!=hs_reference_policy_identity()) return false;'
HEADER='    hs_reference_batching::PolicyIdentity reference_policy;'
CACHE='if (sinfo.n_stream()!=1 || !sinfo.is_contiguous() || n_swa) return {};\n'+stage.PREFIX
class StageTests(unittest.TestCase):
    def test_transform(self):
        g,c,h=stage.transform(GRAPH,CACHE,HEADER)
        self.assertIn('packing_allowed(w, cur)',g)
        self.assertIn('reference_contract_active ||',g)
        self.assertIn('reference_contract_active = false',h)
        self.assertIn('checked_prefix(state)',c)
        self.assertIn('throw std::runtime_error',c)
    def test_missing_or_duplicate_anchor(self):
        for graph in ('',GRAPH+GRAPH):
            with self.assertRaises(ValueError):stage.transform(graph,CACHE,HEADER)
    def test_reapply_rejected(self):
        g,c,h=stage.transform(GRAPH,CACHE,HEADER)
        with self.assertRaises(ValueError):stage.transform(g,c,h)
    def test_stage_source_untouched_and_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'source';(src/'src').mkdir(parents=True)
            (src/'src/llama-graph.cpp').write_text(GRAPH);(src/'src/llama-kv-cache.cpp').write_text(CACHE)
            (src/'src/llama-graph.h').write_text(HEADER)
            (src/'src/hs_reference_batching.hpp').write_bytes((ROOT/'src/reference_batching/reference_batching.hpp').read_bytes())
            out=root/'output';receipt=stage.stage(src,out)
            self.assertEqual(receipt['model_requests'],0)
            self.assertEqual((src/'src/llama-graph.cpp').read_text(),GRAPH)
            self.assertTrue((out/'src/hs_packing_gate.hpp').is_file())
            self.assertEqual((out/'src/hs_reference_batching.hpp').read_bytes(),(src/'src/hs_reference_batching.hpp').read_bytes())
            with self.assertRaises(ValueError):stage.stage(src,out)
    def test_source_symlink_denied(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'source';src.mkdir();(src/'link').symlink_to(root)
            with self.assertRaises(ValueError):stage.stage(src,root/'output')
    def test_no_output_on_anchor_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'source';(src/'src').mkdir(parents=True)
            for f in ('llama-graph.cpp','llama-kv-cache.cpp','llama-graph.h'):(src/'src'/f).write_text('unknown source')
            out=root/'output'
            with self.assertRaises(ValueError):stage.stage(src,out)
            self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
