"""Focused source/CPU checks; these do not build or qualify CUDA/Vulkan."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("integrate", ROOT / "src/reference_batching/integrate_llama_cpp.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def source_fixture(backend):
    initial = ("    inp->prefix_n_kv=mctx_cur->get_prefix_n_kv();" if backend == "cuda" else
               "    inp->prefix_n_kv=(hs_b570::prefix_extent && hs_b570::mode != 0) ? mctx_cur->get_prefix_n_kv() : std::vector<uint32_t>{};")
    return {
        "src/llama-kv-cache.cpp": MODULE.METHOD + "\n" + MODULE.OLD_METHOD_BODY + "\n}\n" + MODULE.METHOD_END + "unused",
        "src/llama-graph.h": "    std::vector<uint32_t> prefix_n_kv;\n",
        "src/llama-graph.cpp": initial + "\n" +
            "bool llm_graph_input_attn_kv::can_reuse(const llm_graph_params & params) {\n"
            "    const auto * mctx = static_cast<const llama_kv_cache_context *>(params.mctx);\n"
            "    if (prefix_n_kv != mctx->get_prefix_n_kv()) return false;\n}\n" +
            "    const bool grouped = existing_backend_shape_and_semantic_guards;\n" +
            MODULE.OLD_LOOP + "\n            begin=end;\n        }\n        ggml_build_forward_expand(gf,cur);\n",
    }


class IntegrationChecks(unittest.TestCase):
    def test_both_backend_transforms_preserve_guards_and_add_policy_check(self):
        for backend in ("cuda", "vulkan"):
            old = source_fixture(backend)
            new = MODULE.transform(old, backend)
            self.assertIn("existing_backend_shape_and_semantic_guards", new["src/llama-graph.cpp"])
            self.assertIn("reference_policy!=hs_reference_policy_identity()", new["src/llama-graph.cpp"])
            self.assertIn("partition_adjacent(prefix)", new["src/llama-graph.cpp"])
            self.assertIn("scalar_prefix_requirements(state)", new["src/llama-kv-cache.cpp"])
            self.assertIn(MODULE.OLD_LOOP, old["src/llama-graph.cpp"])

    def test_drift_rejected_before_output_is_written(self):
        with tempfile.TemporaryDirectory() as d:
            source, out = Path(d) / "old", Path(d) / "new"
            for name, text in source_fixture("vulkan").items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            path = source / "src/llama-graph.cpp"
            path.write_text(path.read_text().replace(MODULE.OLD_LOOP, "changed loop"))
            with self.assertRaises(ValueError): MODULE.stage(source, out, "vulkan")
            self.assertFalse(out.exists())

    def test_actual_generated_cache_method_compiles_and_preserves_boundary(self):
        compiler = shutil.which("g++")
        if compiler is None: self.skipTest("g++ unavailable; compile on native build host")
        text = MODULE.transform(source_fixture("cuda"), "cuda")["src/llama-kv-cache.cpp"]
        begin, end = text.index(MODULE.METHOD), text.index(MODULE.METHOD_END)
        method = text[begin:end]
        fixture = r'''
#include "reference_batching.hpp"
#include <cassert>
struct Cells {uint32_t used=769,max=769,capacity=1024;uint32_t get_used()const{return used;}uint32_t used_max_p1()const{return max;}uint32_t size()const{return capacity;}};
struct slot_info {std::vector<uint32_t> strm{0};uint32_t h=765,count=4,streams=1;bool contiguous=true;bool empty()const{return !count;}uint32_t n_stream()const{return streams;}bool is_contiguous()const{return contiguous;}uint32_t head()const{return h;}uint32_t size()const{return count;}};
struct llama_kv_cache {uint32_t n_swa=0,n_pad=32;std::vector<Cells> v_cells{Cells{}};std::vector<uint32_t>get_prefix_n_kv(const slot_info&)const;};
''' + method + r'''
int main(){llama_kv_cache c;slot_info s;
 assert((c.get_prefix_n_kv(s)==std::vector<uint32_t>{768,768,768,1024}));
 s.streams=2;s.strm.clear();assert(c.get_prefix_n_kv(s).empty());
 s.streams=1;s.strm={0};c.v_cells[0].used=768;assert(c.get_prefix_n_kv(s).empty());}
'''
        with tempfile.TemporaryDirectory() as d:
            cpp, exe = Path(d) / "fixture.cpp", Path(d) / "fixture"
            cpp.write_text(fixture)
            subprocess.run([compiler,"-std=c++17","-Wall","-Wextra","-Werror",
                            "-I"+str(ROOT/"src/reference_batching"),str(cpp),"-o",str(exe)], check=True)
            subprocess.run([str(exe)], check=True)


if __name__ == "__main__": unittest.main()
