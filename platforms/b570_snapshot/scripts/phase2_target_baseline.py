import os
import argparse, csv, hashlib, json, os, threading, time, uuid
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path

import ittapi, psutil, torch
from torch.nn.attention import SDPBackend, sdpa_kernel
from pynvml import *
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

ROOT=Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1])); MODEL=ROOT/"models"/"qwen3-8b"
REV="b968826d9c46dd6066d109eabc6255188de91218"; DOMAIN=ittapi.domain("HeteroSpec-PC")
TEXT=("Heterogeneous computing assigns work to processors with different strengths. A reproducible experiment records every configuration, timestamp, and device name. Correctness is checked before performance. ")
def iso(): return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")
def sha(ids): return hashlib.sha256(torch.tensor(ids,dtype=torch.int64).numpy().tobytes()).hexdigest()
def attention_context(backend):
    if backend=="flash": return sdpa_kernel(SDPBackend.FLASH_ATTENTION)
    if backend=="cudnn": return sdpa_kernel(SDPBackend.CUDNN_ATTENTION)
    return nullcontext()

class NvmlSampler:
    def __init__(self,path): self.path=path; self.stop=threading.Event(); self.run_id=""; self.rows=[]; self.keys=["timestamp","run_id","power_W","gpu_util_pct","memory_util_pct","temperature_C","sm_clock_MHz","memory_clock_MHz","vram_used_MB","sample_source","error"]
    def loop(self):
        with self.path.open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=self.keys); w.writeheader(); f.flush()
            while not self.stop.is_set():
                row={"timestamp":iso(),"run_id":self.run_id}
                try:
                    nvmlInit(); h=nvmlDeviceGetHandleByIndex(0)
                    row.update(power_W=round(nvmlDeviceGetPowerUsage(h)/1000,1),temperature_C=nvmlDeviceGetTemperature(h,NVML_TEMPERATURE_GPU),gpu_util_pct=nvmlDeviceGetUtilizationRates(h).gpu,memory_util_pct=nvmlDeviceGetUtilizationRates(h).memory,sm_clock_MHz=nvmlDeviceGetClockInfo(h,NVML_CLOCK_SM),memory_clock_MHz=nvmlDeviceGetClockInfo(h,NVML_CLOCK_MEM),vram_used_MB=round(nvmlDeviceGetMemoryInfo(h).used/1024**2,1),sample_source="NVML")
                except Exception as e: row.update(error=f"{type(e).__name__}: {e}")
                finally:
                    try: nvmlShutdown()
                    except: pass
                self.rows.append(row); w.writerow(row); f.flush(); self.stop.wait(1.0)
    def start(self): self.thread=threading.Thread(target=self.loop,daemon=True); self.thread.start()
    def close(self):
        self.stop.set(); self.thread.join()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--contexts",default="512,2048,8192"); ap.add_argument("--outputs",default="128,256"); ap.add_argument("--repetitions",type=int,default=5); ap.add_argument("--warmups",type=int,default=3); ap.add_argument("--min-free-vram-mib",type=int,default=1024); ap.add_argument("--sdpa-backend",choices=["auto","flash","cudnn"],default="auto"); ap.add_argument("--diagnostic",action="store_true"); a=ap.parse_args()
    if not torch.cuda.is_available(): raise RuntimeError("CUDA unavailable; fallback forbidden")
    contexts=[int(x) for x in a.contexts.split(',')]; outputs=[int(x) for x in a.outputs.split(',')]
    if a.sdpa_backend=="auto" and max(contexts)>=4096:
        raise RuntimeError("Unsafe configuration: Windows auto SDPA reached near-full VRAM and caused HYPERVISOR_ERROR; use --sdpa-backend cudnn")
    stamp=datetime.now().strftime("%Y%m%dT%H%M%S"); config="P2-STABILITY-DIAG" if a.diagnostic else "B0"; base=ROOT/"runs"/datetime.now().strftime("%Y-%m-%d")/"qwen3"/config/"RTX"; base.mkdir(parents=True,exist_ok=True)
    nvpath=ROOT/"telemetry"/f"qwen_target_nvml_{stamp}.csv"; sampler=NvmlSampler(nvpath); sampler.start()
    session={"session_id":f"p2-RTX-{stamp}","started":iso(),"model":"Qwen/Qwen3-8B","revision":REV,"precision":"bnb_NF4_BF16_double_quant","device":torch.cuda.get_device_name(0),"contexts":contexts,"outputs":outputs,"repetitions":a.repetitions,"warmups":a.warmups,"min_free_vram_mib":a.min_free_vram_mib,"sdpa_backend":a.sdpa_backend,"telemetry_prefix":os.getenv("HETEROSPEC_TELEMETRY_PREFIX"),"nvml_csv":str(nvpath),"valid":False,"runs":[]}
    try:
        tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
        q=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=True)
        model=AutoModelForCausalLM.from_pretrained(MODEL,local_files_only=True,device_map={"":0},quantization_config=q,dtype=torch.bfloat16,low_cpu_mem_usage=True,attn_implementation="sdpa").eval()
        if not str(next(model.parameters()).device).startswith("cuda"): raise RuntimeError("model fallback")
        encoded=tok(TEXT*700,add_special_tokens=False).input_ids
        for c in contexts:
            ids=torch.tensor([encoded[:c]],device="cuda:0"); mask=torch.ones_like(ids); prompt_hash=sha(encoded[:c])
            for outn in outputs:
                # Formal runs use three warmups; bounded stability canaries may request fewer.
                for w in range(1,a.warmups+1):
                    with ittapi.task(f"warmup|RTX|c{c}|o{outn}|w{w}",domain=DOMAIN),torch.inference_mode(),attention_context(a.sdpa_backend): model.generate(input_ids=ids,attention_mask=mask,max_new_tokens=outn,min_new_tokens=outn,do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id)
                for rep in range(1,a.repetitions+1):
                    free_bytes,total_bytes=torch.cuda.mem_get_info()
                    free_mib=free_bytes/1024**2
                    if free_mib<a.min_free_vram_mib: raise RuntimeError(f"VRAM headroom guard: {free_mib:.1f} MiB free < {a.min_free_vram_mib} MiB")
                    rid=f"p2{'diag' if a.diagnostic else ''}-RTX-c{c}-o{outn}-r{rep}-{uuid.uuid4().hex[:8]}"; rd=base/f"context_{c}"/f"output_{outn}"/rid; rd.mkdir(parents=True)
                    sampler.run_id=rid; torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize(); start=iso(); t0=time.perf_counter_ns()
                    with ittapi.task(f"run|{rid}",domain=DOMAIN),torch.inference_mode(),attention_context(a.sdpa_backend): generated=model.generate(input_ids=ids,attention_mask=mask,max_new_tokens=outn,min_new_tokens=outn,do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id)
                    torch.cuda.synchronize(); t1=time.perf_counter_ns(); end=iso(); sampler.run_id=""
                    new=generated[0,c:].tolist(); ms=(t1-t0)/1e6; result={"start_utc":start,"end_utc":end,"completion_ms":ms,"input_tokens":c,"output_tokens":len(new),"decode_ms_per_token":ms/len(new),"throughput_tokens_s":len(new)/(ms/1000),"token_ids":new,"token_ids_sha256":sha(new),"peak_allocated_gib":torch.cuda.max_memory_allocated()/1024**3,"rss_mb":psutil.Process().memory_info().rss/1024**2}
                    meta={"run_id":rid,"phase":"P2-DIAG" if a.diagnostic else "P2","config":config,"model_pair":"qwen","target_model":"Qwen/Qwen3-8B","target_revision":REV,"target_device_requested":"cuda:0","target_device_actual":torch.cuda.get_device_name(0),"target_precision":"bnb_NF4_BF16_double_quant","context_tokens":c,"max_new_tokens":outn,"repetition":rep,"warmups":a.warmups,"sdpa_backend":a.sdpa_backend,"free_vram_before_run_mib":round(free_mib,1),"prompt_token_ids_sha256":prompt_hash,"telemetry_trace_prefix":session["telemetry_prefix"],"nvml_csv":str(nvpath),"valid":len(new)==outn}
                    (rd/"meta.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8"); (rd/"result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); session["runs"].append(rid)
        session["valid"]=len(session["runs"])==len(contexts)*len(outputs)*a.repetitions
    finally:
        sampler.close(); session["ended"]=iso(); (ROOT/"logs"/f"phase2-target-{stamp}.json").write_text(json.dumps(session,indent=2)+"\n",encoding="utf-8"); print(json.dumps(session,indent=2))
    raise SystemExit(0 if session["valid"] else 2)
if __name__=="__main__": main()
