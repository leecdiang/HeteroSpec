#!/usr/bin/env python3
"""NON-FORMAL heterogeneous speculative runner qualification.

Pinned llama.cpp target through its exported C API; frozen OpenVINO draft through
full-prefix replay. Formal Phase-3 execution is deliberately not implemented here.
"""
from __future__ import annotations

import argparse, ctypes as C, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from typing import Sequence

import numpy as np
import openvino as ov
import openvino_genai as ov_genai

ROOT = Path(__file__).resolve().parents[3]
LLAMA_DIR = ROOT / "tools/llama-b10839"
TARGET = ROOT / "models/gguf/Qwen3-8B-Q8_0.gguf"
DRAFT_GGUF = ROOT / "models/gguf/Qwen3-0.6B-Q8_0.gguf"
DRAFT_IR = ROOT / "models/openvino/qwen3-0.6b-6130ef-int4-sym-g128"
NPU_CACHE = ROOT / "runs/358h/qualification_ac_20260918/npu_cache_ctx8192"
NPU_BINDING = ROOT / "runs/358h/qualification_ac_20260918/npu_cache_binding_ctx8192.json"
EXPECTED = {
    TARGET: "408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6",
    DRAFT_GGUF: "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031",
    DRAFT_IR / "openvino_model.xml": "fc8ad94dbecfc0c45cf3db4f0624344d2bea2cdd6997e0b45ca52d4f7baa1103",
    DRAFT_IR / "openvino_model.bin": "2e129cffb1a7239007a3df27e0f3f7bb12f65a40e5c9b1e24a250d952da47837",
}

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20), b""): h.update(b)
    return h.hexdigest()

class Batch(C.Structure):
    _fields_=[("n_tokens",C.c_int32),("token",C.POINTER(C.c_int32)),("embd",C.POINTER(C.c_float)),
              ("pos",C.POINTER(C.c_int32)),("n_seq_id",C.POINTER(C.c_int32)),
              ("seq_id",C.POINTER(C.POINTER(C.c_int32))),("logits",C.POINTER(C.c_int8))]

class ModelParams(C.Structure):
    _fields_=[("devices",C.POINTER(C.c_void_p)),("tensor_buft_overrides",C.c_void_p),
              ("n_gpu_layers",C.c_int32),("split_mode",C.c_int),("load_mode",C.c_int),
              ("lazy_mode",C.c_int),("main_gpu",C.c_int32),("tensor_split",C.POINTER(C.c_float)),
              ("progress_callback",C.c_void_p),("progress_callback_user_data",C.c_void_p),
              ("kv_overrides",C.c_void_p),("vocab_only",C.c_bool),("check_tensors",C.c_bool),
              ("use_extra_bufts",C.c_bool),("no_host",C.c_bool),("no_alloc",C.c_bool),("load_mtp",C.c_bool)]

class ContextParams(C.Structure):
    _fields_=[("n_ctx",C.c_uint32),("n_batch",C.c_uint32),("n_ubatch",C.c_uint32),
              ("n_seq_max",C.c_uint32),("n_rs_seq",C.c_uint32),("n_outputs_max",C.c_uint32),
              ("n_outputs_max_per_seq",C.c_uint32),("n_threads",C.c_int32),("n_threads_batch",C.c_int32),
              ("ctx_type",C.c_int),("rope_scaling_type",C.c_int),("pooling_type",C.c_int),
              ("attention_type",C.c_int),("flash_attn_type",C.c_int),
              ("rope_freq_base",C.c_float),("rope_freq_scale",C.c_float),("yarn_ext_factor",C.c_float),
              ("yarn_attn_factor",C.c_float),("yarn_beta_fast",C.c_float),("yarn_beta_slow",C.c_float),
              ("yarn_orig_ctx",C.c_uint32),("defrag_thold",C.c_float),("cb_eval",C.c_void_p),
              ("cb_eval_user_data",C.c_void_p),("type_k",C.c_int),("type_v",C.c_int),
              ("abort_callback",C.c_void_p),("abort_callback_data",C.c_void_p),
              ("embeddings",C.c_bool),("offload_kqv",C.c_bool),("no_perf",C.c_bool),
              ("op_offload",C.c_bool),("swa_full",C.c_bool),("kv_unified",C.c_bool),
              ("samplers",C.c_void_p),("n_samplers",C.c_size_t),("ctx_other",C.c_void_p)]

class LlamaAPI:
    def __init__(self):
        os.add_dll_directory(str(LLAMA_DIR))
        self.gg=C.CDLL(str(LLAMA_DIR/"ggml.dll")); self.ll=C.CDLL(str(LLAMA_DIR/"llama.dll"))
        self.gg.ggml_backend_load_all_from_path.argtypes=[C.c_char_p]
        self.gg.ggml_backend_dev_by_name.argtypes=[C.c_char_p]; self.gg.ggml_backend_dev_by_name.restype=C.c_void_p
        self.ll.llama_model_default_params.restype=ModelParams; self.ll.llama_context_default_params.restype=ContextParams
        self.ll.llama_model_load_from_file.argtypes=[C.c_char_p,ModelParams]; self.ll.llama_model_load_from_file.restype=C.c_void_p
        self.ll.llama_init_from_model.argtypes=[C.c_void_p,ContextParams]; self.ll.llama_init_from_model.restype=C.c_void_p
        self.ll.llama_model_get_vocab.argtypes=[C.c_void_p]; self.ll.llama_model_get_vocab.restype=C.c_void_p
        self.ll.llama_tokenize.argtypes=[C.c_void_p,C.c_char_p,C.c_int32,C.POINTER(C.c_int32),C.c_int32,C.c_bool,C.c_bool]; self.ll.llama_tokenize.restype=C.c_int32
        self.ll.llama_batch_init.argtypes=[C.c_int32,C.c_int32,C.c_int32]; self.ll.llama_batch_init.restype=Batch
        self.ll.llama_batch_free.argtypes=[Batch]
        self.ll.llama_decode.argtypes=[C.c_void_p,Batch]; self.ll.llama_decode.restype=C.c_int32
        self.ll.llama_get_logits_ith.argtypes=[C.c_void_p,C.c_int32]; self.ll.llama_get_logits_ith.restype=C.POINTER(C.c_float)
        self.ll.llama_vocab_n_tokens.argtypes=[C.c_void_p]; self.ll.llama_vocab_n_tokens.restype=C.c_int32
        self.ll.llama_get_memory.argtypes=[C.c_void_p]; self.ll.llama_get_memory.restype=C.c_void_p
        self.ll.llama_memory_clear.argtypes=[C.c_void_p,C.c_bool]
        self.ll.llama_memory_seq_rm.argtypes=[C.c_void_p,C.c_int32,C.c_int32,C.c_int32]; self.ll.llama_memory_seq_rm.restype=C.c_bool
        self.ll.llama_memory_seq_pos_max.argtypes=[C.c_void_p,C.c_int32]; self.ll.llama_memory_seq_pos_max.restype=C.c_int32
        self.ll.llama_model_free.argtypes=[C.c_void_p]; self.ll.llama_free.argtypes=[C.c_void_p]
        self.ll.llama_backend_init(); self.gg.ggml_backend_load_all_from_path(str(LLAMA_DIR).encode())

class LlamaTarget:
    def __init__(self, api:LlamaAPI, model_path:Path, device:str="Vulkan0", n_ctx:int=4096):
        self.a=api; dev=api.gg.ggml_backend_dev_by_name(device.encode())
        if not dev: raise RuntimeError(f"llama.cpp device unavailable: {device}")
        self._devices=(C.c_void_p*2)(dev,None)
        mp=api.ll.llama_model_default_params(); mp.devices=C.cast(self._devices,C.POINTER(C.c_void_p)); mp.n_gpu_layers=-1; mp.main_gpu=0
        self.model=api.ll.llama_model_load_from_file(str(model_path).encode(),mp)
        if not self.model: raise RuntimeError("llama model load failed")
        cp=api.ll.llama_context_default_params(); cp.n_ctx=n_ctx; cp.n_batch=n_ctx; cp.n_ubatch=1; cp.n_seq_max=1
        cp.n_outputs_max=n_ctx; cp.n_outputs_max_per_seq=n_ctx; cp.no_perf=False
        self.ctx=api.ll.llama_init_from_model(self.model,cp)
        if not self.ctx: raise RuntimeError("llama context init failed")
        self.vocab=api.ll.llama_model_get_vocab(self.model); self.n_vocab=api.ll.llama_vocab_n_tokens(self.vocab)
        self.mem=api.ll.llama_get_memory(self.ctx); self.history=[]; self._logits=None
    def tokenize(self,text:str,parse_special:bool=False)->list[int]:
        raw=text.encode(); cap=max(64,len(raw)+16); arr=(C.c_int32*cap)()
        n=self.a.ll.llama_tokenize(self.vocab,raw,len(raw),arr,cap,False,parse_special)
        if n<0:
            cap=-n; arr=(C.c_int32*cap)(); n=self.a.ll.llama_tokenize(self.vocab,raw,len(raw),arr,cap,False,parse_special)
        if n<0: raise RuntimeError("tokenize failed")
        return list(arr[:n])
    def _decode(self,tokens:Sequence[int],start:int,all_logits:bool=True)->list[int]:
        b=self.a.ll.llama_batch_init(len(tokens),0,1); b.n_tokens=len(tokens)
        for i,t in enumerate(tokens):
            b.token[i]=int(t); b.pos[i]=start+i; b.n_seq_id[i]=1; b.seq_id[i][0]=0; b.logits[i]=1 if all_logits or i==len(tokens)-1 else 0
        rc=self.a.ll.llama_decode(self.ctx,b)
        if rc!=0: self.a.ll.llama_batch_free(b); raise RuntimeError(f"llama_decode={rc}")
        out=[]
        indices=range(len(tokens)) if all_logits else [-1]
        for i in indices:
            p=self.a.ll.llama_get_logits_ith(self.ctx,i)
            arr=np.ctypeslib.as_array(p,shape=(self.n_vocab,)); out.append(int(np.argmax(arr)))
        self.a.ll.llama_batch_free(b); self._logits=out[-1]; return out
    def reset_prefill(self,prompt:list[int]):
        self.a.ll.llama_memory_clear(self.mem,True); self.history=list(prompt); self._decode(prompt,0,False)
    def next_token(self)->int: return int(self._logits)
    def verify(self,proposals:list[int])->list[int]:
        before=len(self.history); expected0=self.next_token()
        if not proposals:
            self._decode([expected0],before,True); self.history.append(expected0)
            return [expected0]
        nexts=self._decode(proposals,before,True)
        accepted=0; expected=expected0
        for i,d in enumerate(proposals):
            if d!=expected: break
            accepted+=1; expected=nexts[i]
        committed=proposals[:accepted]+[expected]
        # Candidate suffix at [before+accepted, before+len(proposals)) is invalid.
        if accepted<len(proposals):
            if not self.a.ll.llama_memory_seq_rm(self.mem,0,before+accepted,-1): raise RuntimeError("target KV rollback failed")
        # Accepted candidates already reside in KV; decode correction/bonus.
        self._decode([expected],before+accepted,True)
        self.history.extend(committed)
        pos=self.a.ll.llama_memory_seq_pos_max(self.mem,0)
        if pos!=len(self.history)-1: raise AssertionError(f"target state drift {pos} != {len(self.history)-1}")
        return committed
    def baseline(self,n:int)->list[int]:
        out=[]
        for _ in range(n):
            t=self.next_token(); self._decode([t],len(self.history),True); self.history.append(t); out.append(t)
        return out

class OpenVINODraftReplay:
    def __init__(self,device:str):
        self.device=device; core=ov.Core()
        if device not in core.available_devices: raise RuntimeError(f"OpenVINO device unavailable: {device}")
        props={"PERFORMANCE_HINT":"LATENCY"}
        if device=="NPU": props={"MAX_PROMPT_LEN":8192,"MIN_RESPONSE_LEN":128,"PREFILL_HINT":"DYNAMIC","GENERATE_HINT":"FAST_COMPILE","CACHE_DIR":str(NPU_CACHE.resolve())}
        self.pipe=ov_genai.LLMPipeline(str(DRAFT_IR),device,props); self.tokenizer=self.pipe.get_tokenizer()
        self.cfg=ov_genai.GenerationConfig(); self.cfg.do_sample=False; self.cfg.ignore_eos=True; self.cfg.apply_chat_template=False
        # Strict binding evidence from the same frozen IR and physical plugin.
        if device=="NPU":
            # The NPU requires the GenAI static-profile compilation path. A generic
            # dynamic Core.compile_model is known to fail and is not the runtime used
            # by this adapter. Re-validate the frozen lower-level cache binding instead.
            ev=json.loads(NPU_BINDING.read_text(encoding="utf-8-sig"))
            if not ev.get("qualification_pass") or ev.get("actual_execution_devices")!="NPU":
                raise RuntimeError("frozen NPU binding evidence is not admissible")
            if sha(Path(ev["cache_blob"]["path"]))!=ev["cache_blob"]["sha256"]:
                raise RuntimeError("frozen NPU cache hash mismatch")
            self.execution_devices=["NPU"]
        else:
            cm=core.compile_model(str(DRAFT_IR/"openvino_model.xml"),device)
            self.execution_devices=list(cm.get_property("EXECUTION_DEVICES"))
        if self.execution_devices!=[device]: raise RuntimeError(f"binding mismatch {self.execution_devices}")
    def propose(self,full_prefix:list[int],n:int)->tuple[list[int],int]:
        self.cfg.max_new_tokens=n; self.cfg.min_new_tokens=n
        ids=np.asarray(full_prefix,dtype=np.int64).reshape(1,-1); inp=ov_genai.TokenizedInputs(ov.Tensor(ids),ov.Tensor(np.ones_like(ids)))
        s=time.perf_counter_ns(); r=self.pipe.generate(inp,self.cfg); e=time.perf_counter_ns()
        return [int(x) for x in r.tokens[0]][:n],e-s

class LlamaDraftReplay:
    """Qualification-only historical GGUF adapter for native semantic reference."""
    def __init__(self,api:LlamaAPI):
        self.model=LlamaTarget(api,DRAFT_GGUF,"CPU",4096); self.execution_devices=["CPU"]
    def propose(self,full_prefix:list[int],n:int)->tuple[list[int],int]:
        s=time.perf_counter_ns(); self.model.reset_prefill(full_prefix); out=self.model.baseline(n); e=time.perf_counter_ns()
        return out,e-s

def run_bridge(device:str,prompt:str,n:int=16,draft_backend:str="OPENVINO")->dict:
    for p,h in EXPECTED.items():
        if sha(p)!=h: raise RuntimeError(f"hash mismatch {p}")
    # Exact b10839 Qwen3 --reasoning off, single-turn generation boundary.
    formatted=f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    api=LlamaAPI(); tgt=LlamaTarget(api,TARGET); pt=tgt.tokenize(formatted,True)
    tgt.reset_prefill(pt); baseline=tgt.baseline(n)
    tgt.reset_prefill(pt)
    draft=LlamaDraftReplay(api) if draft_backend=="GGUF_REFERENCE" else OpenVINODraftReplay(device)
    out=[]; rounds=[]; draft_ns=target_ns=0
    start=time.perf_counter_ns()
    # b10839 server/simple-IO path commits one target token before the first
    # draft round; native debug trace begins drafting from the resulting prefix.
    ts=time.perf_counter_ns(); first=tgt.verify([]); te=time.perf_counter_ns(); target_ns+=te-ts
    out.extend(first[:n]); rounds.append({"prefix_before":len(pt),"proposals":[],"target_committed":first[:n],
        "accepted":0,"correction":first[0],"bonus":None,"C":len(first[:n]),
        "target_state_position":len(pt)+len(first[:n])-1,"draft_logical_state_length":len(pt)+len(first[:n]),
        "native_initial_target_only":True})
    while len(out)<n:
        remaining=n-len(out); width=min(2,max(0,remaining-1))
        if width:
            props,dt=draft.propose(pt+out,width); draft_ns+=dt
        else: props=[]
        ts=time.perf_counter_ns(); committed=tgt.verify(props); te=time.perf_counter_ns(); target_ns+=te-ts
        committed=committed[:remaining]; out.extend(committed)
        accepted=max(0,len(committed)-1) if props else 0
        rounds.append({"prefix_before":len(pt)+len(out)-len(committed),"proposals":props,"target_committed":committed,
                       "accepted":accepted,"correction":committed[-1] if accepted<len(props) else None,
                       "bonus":committed[-1] if accepted==len(props) and props else None,"C":len(committed),
                       "target_state_position":len(pt)+len(out)-1,"draft_logical_state_length":len(pt)+len(out)})
    end=time.perf_counter_ns()
    return {"schema":"heterospec.358h.phase3.runner_dryrun.v1","formal":False,"claim_status":"NON_FORMAL / INVALID_FOR_CLAIMS",
            "device":device,"draft_backend":draft_backend,"execution_devices":draft.execution_devices,"prompt":prompt,"formatted_prompt":formatted,"prompt_tokens":pt,
            "baseline_tokens":baseline,"speculative_tokens":out,"exact":baseline==out,"rounds":rounds,
            "instrumentation":{"end_to_end_ns":end-start,"draft_replay_ns":draft_ns,"target_verification_ns":target_ns,
                               "orchestration_residual_ns":max(0,(end-start)-draft_ns-target_ns)},
            "proposed":sum(len(x["proposals"]) for x in rounds),"accepted":sum(x["accepted"] for x in rounds)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--device",choices=["CPU","NPU"],required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--tokens",type=int,default=16); ap.add_argument("--draft-backend",choices=["OPENVINO","GGUF_REFERENCE"],default="OPENVINO")
    a=ap.parse_args(); result=run_bridge(a.device,"Write a Python function that returns the square of an integer.",a.tokens,a.draft_backend)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"device":a.device,"exact":result["exact"],"rounds":len(result["rounds"]),"binding":result["execution_devices"]},indent=2))
    return 0 if result["exact"] else 2
if __name__=="__main__": raise SystemExit(main())

