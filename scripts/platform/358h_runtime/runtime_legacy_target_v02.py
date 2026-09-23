#!/usr/bin/env python3
"""Exact target-only extraction from frozen Phase-3 runner for process isolation.

Source: scripts/platform/358h/phase3_heterogeneous_runner.py, closed SHA-256
1d11e42d008f981ee6a91ac7bfeb478f11c060d51e79b9e060fe04ece70153e8.
Only its five target C-API classes are copied; target semantics are unchanged.
"""
from __future__ import annotations
import ctypes as C
import os
from pathlib import Path
from typing import Sequence
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
LLAMA_DIR = ROOT / "tools/llama-b10839"
TARGET = ROOT / "models/gguf/Qwen3-8B-Q8_0.gguf"


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
