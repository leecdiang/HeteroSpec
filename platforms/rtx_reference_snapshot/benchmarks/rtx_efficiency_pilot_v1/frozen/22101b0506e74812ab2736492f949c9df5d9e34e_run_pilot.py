"""Bounded, exposed-task RTX speculative efficiency pilot; no runtime edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
CONDITIONS = {
    "target": [],
    "draft_k2": ["--spec-type", "draft-simple", "--spec-draft-n-max", "2"],
    "draft_k4": ["--spec-type", "draft-simple", "--spec-draft-n-max", "4"],
    "ngram": ["--spec-type", "ngram-simple", "--spec-ngram-simple-size-n", "4", "--spec-ngram-simple-size-m", "8"],
    "hybrid": ["--spec-type", "ngram-simple,draft-simple", "--spec-ngram-simple-size-n", "4", "--spec-ngram-simple-size-m", "8", "--spec-draft-n-max", "4"],
}
ORDERS = [list(CONDITIONS), ["hybrid", "ngram", "draft_k4", "draft_k2", "target"], ["draft_k2", "target", "hybrid", "ngram", "draft_k4"]]

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime", required=True)
    ap.add_argument("--models", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--conditions", nargs="+", choices=list(CONDITIONS), default=list(CONDITIONS))
    ap.add_argument("--flash-attn", choices=["on", "off"], default="on")
    ap.add_argument("--ubatch", type=int, default=512)
    ap.add_argument("--input-file", default="inputs.json")
    args = ap.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    inputs = json.loads((ROOT / args.input_file).read_text(encoding="utf-8"))
    source_sha = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    exe = Path(args.runtime) / "llama-server.exe"
    common = [str(exe), "--model", str(Path(args.models) / "Qwen3-8B-Q8_0.gguf"),
              "--device", "CUDA0", "--n-gpu-layers", "all", "--fit", "off", "--ctx-size", "2048",
              "--batch-size", "512", "--ubatch-size", str(args.ubatch), "--flash-attn", args.flash_attn,
              "--parallel", "1", "--threads", "24", "--threads-batch", "24", "--cache-ram", "0",
              "--host", "127.0.0.1", "--port", "18763", "--no-webui", "--no-warmup", "--no-cache-prompt"]
    env = {k: v for k, v in os.environ.items() if not k.startswith(("HS_", "LLAMA_ARG_", "LLAMA_BATCH_DEBUG"))}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(route, body=None, timeout=120):
        req = urllib.request.Request("http://127.0.0.1:18763" + route,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Content-Type": "application/json"})
        with opener.open(req, timeout=timeout) as r:
            return json.load(r)
    def completion(prompt, cap):
        return request("/completion", {"prompt": prompt, "n_predict": cap, "temperature": 0,
            "top_k": 0, "top_p": 1, "min_p": 0, "seed": 123, "cache_prompt": False,
            "return_tokens": True, "stream": False})
    save(out / "manifest.json", {"args": vars(args), "source_commit": source_sha,
         "source_sha256": sha(__file__), "inputs_sha256": sha(ROOT / args.input_file),
         "runtime_sha256": sha(exe), "upstream_commit": "0cae43063cf15170e91a2ff4d034da0ecef4a1b2",
         "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "boundary": "resident single-slot uncached full request; separately reported generation timer"})
    records = []
    for rnd in range(args.rounds):
        for condition in ORDERS[rnd % len(ORDERS)]:
            if condition not in args.conditions:
                continue
            cmd = common + CONDITIONS[condition]
            if condition.startswith("draft") or condition == "hybrid":
                cmd += ["--model-draft", str(Path(args.models) / "Qwen3-0.6B-Q8_0.gguf"),
                        "--spec-draft-device", "CUDA0", "--spec-draft-ngl", "all",
                        "--spec-draft-threads", "24", "--spec-draft-threads-batch", "24",
                        "--spec-draft-n-min", "0"]
            prefix = f"r{rnd}_{condition}"
            save(out / (prefix + "_command.json"), cmd)
            print(f"START {prefix}", flush=True)
            with open(out / (prefix + ".log"), "wb") as log:
                process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env,
                                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                try:
                    ready = False
                    deadline = time.monotonic() + 120
                    while time.monotonic() < deadline:
                        if process.poll() is not None:
                            raise RuntimeError(f"server exited {process.returncode}: {prefix}")
                        try:
                            if request("/health", timeout=2).get("status") == "ok":
                                ready = True
                                break
                        except (OSError, urllib.error.URLError):
                            time.sleep(0.5)
                    if not ready:
                        raise RuntimeError("server readiness timeout")
                    warm_prompt = request("/apply-template", {"messages": [{"role": "user", "content": "Write Python code to add two integers."}], "chat_template_kwargs": {"enable_thinking": False}})["prompt"]
                    save(out / (prefix + "_warmup.json"), completion(warm_prompt, 32))
                    ordered = inputs[rnd % len(inputs):] + inputs[:rnd % len(inputs)]
                    for task in ordered:
                        prompt = task.get("prompt_ids")
                        if prompt is None:
                            prompt = request("/apply-template", {"messages": [{"role": "user", "content": task["prompt"]}], "chat_template_kwargs": {"enable_thinking": False}})["prompt"]
                        start = time.perf_counter()
                        response = completion(prompt, task["cap"])
                        elapsed = 1000 * (time.perf_counter() - start)
                        record = {"round": rnd, "condition": condition, "task": task["id"],
                                  "group": task["group"], "cap": task["cap"], "wall_ms": elapsed,
                                  "response": response, "source_commit": source_sha}
                        records.append(record)
                        save(out / f"{prefix}_{task['id']}.json", record)
                        if not response.get("tokens") or response['timings']['cache_n'] != 0:
                            raise RuntimeError("missing native IDs or unexpected prompt reuse")
                        t = response["timings"]
                        print(f"DONE {prefix} {task['id']} n={len(response['tokens'])} stop={response['stop_type']} wall={elapsed:.1f} gen={t['predicted_ms']:.1f} draft={t.get('draft_n',0)}/{t.get('draft_n_accepted',0)}", flush=True)
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=10)
    save(out / "records.json", records)
    print(f"COMPLETE {len(records)} measured requests", flush=True)

if __name__ == "__main__":
    main()
