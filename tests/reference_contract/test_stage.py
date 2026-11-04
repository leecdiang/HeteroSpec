import importlib.util
from pathlib import Path
import tempfile
import unittest
import subprocess
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('stage',ROOT/'scripts/reference_contract/stage.py')
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
GRAPH=stage.PACKED+'\n    // original numerical graph\n}\n'
CACHE='if (sinfo.n_stream()!=1 || !sinfo.is_contiguous() || n_swa) return {};\n'+stage.PREFIX
class StageTests(unittest.TestCase):
    def test_transform(self):
        g,c=stage.transform(GRAPH,CACHE)
        self.assertIn('packing_allowed(w, cur)',g)
        self.assertIn('checked_prefix(state)',c)
        self.assertIn('throw std::runtime_error',c)
    def test_missing_or_duplicate_anchor(self):
        for graph in ('',GRAPH+GRAPH):
            with self.assertRaises(ValueError):stage.transform(graph,CACHE)
    def test_reapply_rejected(self):
        g,c=stage.transform(GRAPH,CACHE)
        with self.assertRaises(ValueError):stage.transform(g,c)
    def test_stage_source_untouched_and_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'source';(src/'src').mkdir(parents=True)
            (src/'src/llama-graph.cpp').write_text(GRAPH);(src/'src/llama-kv-cache.cpp').write_text(CACHE)
            out=root/'output';receipt=stage.stage(src,out)
            self.assertEqual(receipt['model_requests'],0)
            self.assertEqual((src/'src/llama-graph.cpp').read_text(),GRAPH)
            self.assertTrue((out/'src/hs_packing_gate.hpp').is_file())
            with self.assertRaises(ValueError):stage.stage(src,out)
    def test_source_symlink_denied(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'source';src.mkdir();(src/'link').symlink_to(root)
            with self.assertRaises(ValueError):stage.stage(src,root/'output')
    def test_no_output_on_anchor_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'source';(src/'src').mkdir(parents=True)
            for f in ('llama-graph.cpp','llama-kv-cache.cpp'):(src/'src'/f).write_text('unknown source')
            out=root/'output'
            with self.assertRaises(ValueError):stage.stage(src,out)
            self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
