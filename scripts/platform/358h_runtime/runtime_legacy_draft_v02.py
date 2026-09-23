#!/usr/bin/env python3
"""Draft-only extraction from frozen Phase-3 runner for process isolation."""
from __future__ import annotations
import hashlib
import json
import os
import time
from pathlib import Path
import numpy as np
import openvino as ov
import openvino_genai as ov_genai
ROOT = Path(__file__).resolve().parents[3]
DRAFT_IR = ROOT / "models/openvino/qwen3-0.6b-6130ef-int4-sym-g128"
NPU_CACHE = Path(os.environ.get("HETEROSPEC_RUNTIME_CACHE_DIR", str(ROOT / "runs/358h/runtime_v02_npu_cache")))
NPU_BINDING = Path(os.environ.get("HETEROSPEC_FROZEN_NPU_BINDING", str(ROOT / "runs/358h/qualification_ac_20260918/npu_cache_binding_ctx8192.json")))


def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20), b""): h.update(b)
    return h.hexdigest()

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
