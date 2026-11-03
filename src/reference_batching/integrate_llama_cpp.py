"""Stage a shared-planner candidate from the restored PR162/163 source tree.

Reads the source, validates every edit, then writes a fresh copy. Existing
experimental trees and historical records are never modified. No model runs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
METHOD = "std::vector<uint32_t> llama_kv_cache::get_prefix_n_kv(const slot_info & sinfo) const {"
METHOD_END = "\nggml_tensor * llama_kv_cache::get_k("
OLD_METHOD_BODY = """    if (n_swa || sinfo.empty() || sinfo.n_stream()!=1 || !sinfo.is_contiguous()) return {};
    const auto & cells=v_cells[sinfo.strm[0]];
    const auto head=sinfo.head();
    if (cells.get_used()!=cells.used_max_p1() || cells.used_max_p1()!=head+sinfo.size()) return {};
    const uint32_t padding=std::max(n_pad,256u);
    std::vector<uint32_t> result;
    for (uint32_t row=0;row<sinfo.size();++row) {
        result.push_back(std::min(cells.size(),std::max(padding,GGML_PAD(head+row+1,padding))));
    }
    return result;"""
NEW_METHOD_BODY = """    if (sinfo.empty()) return {};
    // Stream count is checked before indexing strm/cells.
    if (sinfo.n_stream()!=1 || !sinfo.is_contiguous() || n_swa) return {};
    const auto & cells=v_cells[sinfo.strm[0]];
    const hs_reference_batching::DenseAppendState state{
        sinfo.head(), uint32_t(sinfo.size()), cells.get_used(), cells.used_max_p1(),
        cells.size(), std::max(n_pad,256u), uint32_t(sinfo.n_stream()),
        sinfo.is_contiguous(), n_swa != 0};
    return hs_reference_batching::scalar_prefix_requirements(state).extents;"""
OLD_LOOP = """        for (size_t begin=0;begin<prefix.size();) {
            size_t end=begin+1;while(end<prefix.size() && prefix[end]==prefix[begin])++end;
            const int64_t width=end-begin,extent=prefix[begin];"""
NEW_LOOP = """        const auto groups=hs_reference_batching::partition_adjacent(prefix);
        for (const auto & planned : groups) {
            const size_t begin=planned.begin;
            const int64_t width=planned.end-planned.begin,extent=planned.requirement.extent;"""


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("missing/nonunique final-source anchor: " + old[:90])
    return text.replace(old, new, 1)


def transform(contents: dict[str, str], backend: str) -> dict[str, str]:
    """Pure transform: no partial writes if a pinned source anchor has drifted."""
    if backend not in ("cuda", "vulkan"):
        raise ValueError("backend must be cuda or vulkan")
    result = dict(contents)
    name = "src/llama-kv-cache.cpp"
    result[name] = '#include "hs_reference_batching.hpp"\n' + once(
        result[name], OLD_METHOD_BODY, NEW_METHOD_BODY)
    name = "src/llama-graph.h"
    result[name] = '#include "hs_reference_batching.hpp"\n' + once(
        result[name], "    std::vector<uint32_t> prefix_n_kv;",
        "    std::vector<uint32_t> prefix_n_kv;\n"
        "    hs_reference_batching::PolicyIdentity reference_policy;")
    name = "src/llama-graph.cpp"
    text = result[name]
    if backend == "vulkan":
        include = '#include "companion_scope.hpp"\n'
        policy = """static hs_reference_batching::PolicyIdentity hs_reference_policy_identity() {
    return {hs_reference_batching::Backend::vulkan, hs_b570::mode,
        hs_b570::prefix_extent, hs_b570::reference_q8, false, 1};
}
"""
        initial = "    inp->prefix_n_kv=(hs_b570::prefix_extent && hs_b570::mode != 0) ? mctx_cur->get_prefix_n_kv() : std::vector<uint32_t>{};"
    else:
        include = '#include "hs_scope.h"\n'
        policy = """static hs_reference_batching::PolicyIdentity hs_reference_policy_identity() {
    return {hs_reference_batching::Backend::cuda, hs_scope::layout95(),
        hs_scope::active, false, hs_scope::active, 1};
}
"""
        initial = "    inp->prefix_n_kv=mctx_cur->get_prefix_n_kv();"
    text = '#include "hs_reference_batching.hpp"\n' + include + policy + text
    text = once(text, initial, initial + "\n    inp->reference_policy=hs_reference_policy_identity();")
    anchor = """bool llm_graph_input_attn_kv::can_reuse(const llm_graph_params & params) {
    const auto * mctx = static_cast<const llama_kv_cache_context *>(params.mctx);"""
    text = once(text, anchor, anchor + "\n    if (reference_policy!=hs_reference_policy_identity()) return false;")
    text = once(text, OLD_LOOP, NEW_LOOP)
    text = once(text, "            begin=end;\n        }\n        ggml_build_forward_expand(gf,cur);",
                "        }\n        ggml_build_forward_expand(gf,cur);")
    result[name] = text
    return result


def stage(source: Path, out: Path, backend: str) -> dict:
    source, out = source.resolve(), out.resolve()
    if out.exists() or out == source or out.is_relative_to(source):
        raise ValueError("output must be a fresh directory outside the source")
    names = ("src/llama-kv-cache.cpp", "src/llama-graph.h", "src/llama-graph.cpp")
    before = {n: (source / n).read_bytes() for n in names}
    changed = transform({n: b.decode("utf-8") for n, b in before.items()}, backend)
    if backend == "cuda":
        scheduler = source / "ggml/src/ggml-backend.cpp"
        if not scheduler.is_file() or "hs_repair_offload::offload_op(" not in scheduler.read_text(encoding="utf-8"):
            raise ValueError("CUDA integration requires the PR162 combined head-norm/prefix source")
    shutil.copytree(source, out)
    for name, text in changed.items():
        (out / name).write_text(text, encoding="utf-8", newline="\n")
    shutil.copyfile(HERE / "reference_batching.hpp", out / "src/hs_reference_batching.hpp")
    if backend == "cuda":
        from activate_cuda_requirements import install
        additional = ("ggml/src/ggml-backend.cpp", "ggml/src/repair_offload.hpp")
        before.update({name: (source / name).read_bytes() for name in additional})
        names += additional
        install(out)
    receipt = {
        "status": "SOURCE_STAGED_NOT_GPU_QUALIFIED", "backend": backend,
        "source": str(source), "candidate": str(out), "model_requests": 0,
        "files": {n: {"before_sha256": hashlib.sha256(before[n]).hexdigest(),
                      "after_sha256": hashlib.sha256((out / n).read_bytes()).hexdigest()}
                  for n in names},
        "shared_header_sha256": hashlib.sha256((HERE / "reference_batching.hpp").read_bytes()).hexdigest(),
        "preserved": ["existing backend/shape guards", "original R and draft scope",
                      "Q/K/V/mask views", "Vulkan Q8 projection implementation"],
    }
    (out / "SHARED_PLANNER_SOURCE.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--backend", choices=("cuda", "vulkan"), required=True)
    args = ap.parse_args()
    print(json.dumps(stage(args.source, args.out, args.backend), indent=2))
