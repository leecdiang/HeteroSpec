"""Stage guarded PR171 source without modifying the source tree.

Only the known packed-graph anchor and shared-planner prefix extraction are
accepted. Native exceptions must reach the host transaction boundary; a caller
must not continue a partially changed context. This tool does not build CUDA.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import os

ROOT = Path(__file__).resolve().parents[2]
PACKED = 'if (ggml_is_contiguous(cur) && w->ne[2]==1 && w->ne[3]==1 && cur->ne[1]>=8) {'
GUARDED = 'if (hs_reference_batching::packing_allowed(w, cur) && ggml_is_contiguous(cur) && w->ne[2]==1 && w->ne[3]==1 && cur->ne[1]>=8) {'
PREFIX = 'return hs_reference_batching::scalar_prefix_requirements(state).extents;'

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('missing/nonunique pinned source anchor: ' + old[:100])
    return text.replace(old, new, 1)

def transform(graph: str, cache: str, graph_header: str):
    graph = once(graph, PACKED, GUARDED)
    graph = '#define HS_CONTRACT_BUILD\n#include "hs_packing_gate.cpp"\n#include "hs_scope.h"\nextern "C" HS_GATE_API bool hs_exchange_runtime_scope(bool active) { const bool old=hs_scope::active; hs_scope::active=active; return old; }\n' + graph
    cache = once(cache, PREFIX, 'return hs_reference_batching::checked_prefix(state);')
    cache = '#include "hs_packing_gate.hpp"\n' + cache
    # These early exits otherwise bypass checked_prefix before DenseAppendState.
    cache = once(cache,
        'if (sinfo.n_stream()!=1 || !sinfo.is_contiguous() || n_swa) return {};',
        'if (sinfo.n_stream()!=1 || !sinfo.is_contiguous() || n_swa) {\n'
        '        if (hs_reference_batching::hs_get_packing_binding())\n'
        '            throw std::runtime_error("reference prefix unsupported: restore before retry");\n'
        '        return {}; // legacy, no reference-preserving claim\n'
        '    }')
    graph_header=once(graph_header,
        '    hs_reference_batching::PolicyIdentity reference_policy;',
        '    hs_reference_batching::PolicyIdentity reference_policy;\n    bool reference_contract_active = false;')
    graph=once(graph,'    inp->reference_policy=hs_reference_policy_identity();',
        '    inp->reference_policy=hs_reference_policy_identity();\n    inp->reference_contract_active=hs_reference_batching::hs_get_packing_binding()!=nullptr;')
    graph=once(graph,'    if (reference_policy!=hs_reference_policy_identity()) return false;',
        '    if (reference_contract_active || hs_reference_batching::hs_get_packing_binding()) return false;\n    if (reference_policy!=hs_reference_policy_identity()) return false;')
    graph += '\n#include "hs_native_preflight.inc"\n'
    return graph,cache,graph_header

def stage(source: Path, out: Path):
    source,out=source.resolve(),out.resolve()
    if not source.is_dir() or out.exists() or out==source or out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('source must exist; output must be fresh and outside source')
    if any(p.is_symlink() for p in source.rglob('*')):
        raise ValueError('source symlinks are not supported')
    names=('src/llama-graph.cpp','src/llama-kv-cache.cpp','src/llama-graph.h')
    original={p:(source/p).read_bytes() for p in names}
    transformed=transform(*(original[p].decode('utf-8') for p in names))
    headers={
        'execution_contract.hpp':'execution_contract.hpp',
        'packing_gate.hpp':'hs_packing_gate.hpp',
        'packing_gate.cpp':'hs_packing_gate.cpp',
        'native_preflight.inc':'hs_native_preflight.inc',
    }
    backend_header=(source/'src/hs_reference_batching.hpp').read_bytes()
    if hashlib.sha256(backend_header).hexdigest() != '746cce0b2ef4f1aa5504ff3921a6676f3158e0325f6dca035f81829b1ae8261c':
        raise ValueError('unexpected source shared header; do not overwrite backend rules')
    # Materialize/validate all replacement bytes before creating output.
    payload={p:t.encode() for p,t in zip(names,transformed)}
    for src,dst in headers.items():
        data=(ROOT/'src/reference_batching'/src).read_bytes()
        if src=='packing_gate.cpp':
            data=data.replace(b'"packing_gate.hpp"',b'"hs_packing_gate.hpp"')
        if src=='execution_contract.hpp':
            data=data.replace(b'"reference_batching.hpp"',b'"hs_reference_batching.hpp"')
        payload['src/'+dst]=data
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix='.hs-stage-',dir=out.parent))
    try:
        shutil.copytree(source,temp,dirs_exist_ok=True,symlinks=True)
        for p,data in payload.items():
            target=temp/p
            if target.is_symlink(): raise ValueError('refuse to overwrite symlink: '+p)
            target.write_bytes(data)
        receipt={'status':'STAGED_NOT_NATIVE_QUALIFIED','model_requests':0,
                 'preserved_backend_header_sha256':hashlib.sha256(backend_header).hexdigest(),
                 'default':'reject without explicit bound qualification; tiled fallback separately qualified',
                 'failure':'prefix rejection requires abort and full checkpoint recovery',
                 'files':{p:{'before_sha256':hashlib.sha256(original[p]).hexdigest(),
                              'after_sha256':hashlib.sha256(payload[p]).hexdigest()} for p in names},
                 'headers':{p:hashlib.sha256(v).hexdigest() for p,v in payload.items() if p not in names}}
        (temp/'EXECUTION_CONTRACT_STAGE.json').write_text(json.dumps(receipt,indent=2)+'\n')
        # Never replace an output that appeared after validation.
        out.mkdir() # exclusive reservation; never overwrite a concurrent output
        try:
            shutil.copytree(temp,out,dirs_exist_ok=True)
        except BaseException:
            shutil.rmtree(out)
            raise
        return receipt
    finally:
        if temp.exists(): shutil.rmtree(temp)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(stage(a.source,a.out),indent=2))
