import os
import json
import time
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
MODEL = ROOT / "models" / "qwen3-8b"
LOG = ROOT / "logs" / "phase2-target-smoke.json"
REVISION = "b968826d9c46dd6066d109eabc6255188de91218"

record = {
    "started": datetime.now().astimezone().isoformat(timespec="milliseconds"),
    "model": "Qwen/Qwen3-8B",
    "revision": REVISION,
    "quantization": "bitsandbytes_NF4",
    "compute_dtype": "bfloat16",
    "torch": torch.__version__,
    "cuda_runtime": torch.version.cuda,
    "cuda_available": torch.cuda.is_available(),
}
try:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; CPU fallback is forbidden")
    record["device_before_load"] = torch.cuda.get_device_name(0)
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    torch.cuda.reset_peak_memory_stats(0)
    t0 = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL,
        local_files_only=True,
        device_map={"": 0},
        quantization_config=quant,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )
    record["load_seconds"] = time.perf_counter() - t0
    record["model_device"] = str(next(model.parameters()).device)
    if not record["model_device"].startswith("cuda"):
        raise RuntimeError(f"Silent fallback detected: model device is {record['model_device']}")
    prompt = "Explain in one sentence why deterministic decoding is useful for reproducible experiments."
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda:0")
    torch.cuda.synchronize()
    t1 = time.perf_counter()
    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=16,
            do_sample=False,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    torch.cuda.synchronize()
    record["generation_seconds"] = time.perf_counter() - t1
    new_ids = output[0, inputs.input_ids.shape[1]:].tolist()
    record["output_token_ids"] = new_ids
    record["output_text"] = tokenizer.decode(new_ids, skip_special_tokens=True)
    record["allocated_gib"] = torch.cuda.memory_allocated(0) / 1024**3
    record["reserved_gib"] = torch.cuda.memory_reserved(0) / 1024**3
    record["peak_allocated_gib"] = torch.cuda.max_memory_allocated(0) / 1024**3
    record["pass"] = True
except Exception as exc:
    record["pass"] = False
    record["error_type"] = type(exc).__name__
    record["error"] = str(exc)
    raise
finally:
    record["ended"] = datetime.now().astimezone().isoformat(timespec="milliseconds")
    LOG.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(record, indent=2, ensure_ascii=False))
