"""Check the frozen resident pool's resource feasibility without generating tokens.

The output is resource admission, never numerical qualification or a study freeze.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

import study as s


def now():
    return datetime.now(timezone.utc).isoformat()


def admit(args):
    s.check_plan(s.DESIGN)
    root, build = args.out.resolve(), args.build.resolve()
    s.need(not root.exists(), "fresh admission directory required")
    s.need(args.timeout > 0, "positive timeout required")
    report = s.read(build / "BUILD.json")
    pins = s.read(s.DESIGN / "MODEL_PINS.json")["families"][args.family]
    contract = s.read(args.models)["families"][args.family]
    s.need(report["status"] == "BUILT_NOT_QUALIFIED" and report["source_zip_sha256"] == pins["source_zip_sha256"], "build source/status differs")
    for name, key in (("worker.cpp", "worker_source_sha256"), ("arm_spec.h", "arm_spec_sha256")):
        s.need(s.hash_file(Path(__file__).parent / name) == report[key] == s.hash_file(build / name), "build source differs: " + name)
    s.need(s.hash_file(build / "core/src/libllama.a") == report["core_sha256"], "core archive differs")
    executable = build / "bin/rtx-scope-transfer.exe"
    s.need(s.hash_file(executable) == report["executable_sha256"], "worker executable differs")
    for role, pin in pins["models"].items():
        model = Path(contract["models"][role]["path"])
        s.need(model.stat().st_size == pin["bytes"] and s.hash_file(model) == pin["sha256"], "model differs: " + role)
    for name, digest in report["numerical_modules"].items():
        s.need(s.hash_file(build / "bin" / name) == digest, "numerical module differs")
    gpu_text = subprocess.check_output(["nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.used", "--format=csv,noheader,nounits"], text=True, timeout=30)
    gpu_rows = list(csv.reader(gpu_text.strip().splitlines()))
    s.need(len(gpu_rows) == 1 and "5070" in gpu_rows[0][1], "ambiguous or unsupported GPU")
    gpu_id, gpu_name, driver, used_mib = [v.strip() for v in gpu_rows[0]]
    s.need(int(used_mib) < 1024, "GPU not idle enough for resource admission")
    s.need(shutil.disk_usage(root.parent).free >= 16 * 1024**3, "less than 16 GiB disk headroom")
    root.mkdir(parents=True)
    plan = s.read(s.DESIGN / "PLAN.json")
    identity = {k: pins[k] for k in ("source_variant", "source_zip_sha256", "models", "vocabulary_sha256", "template_sha256")}
    identity.update({k: report[k] for k in ("executable_sha256", "core_sha256", "worker_source_sha256", "numerical_modules")})
    identity.update(build_receipt_sha256=s.hash_file(build / "BUILD.json"), host_id=socket.gethostname(), device_id=gpu_id, driver=driver, context=plan["context"])
    s.save(root / "BINDING.json", {"schema": 1, "study_id": s.STUDY, "is_synthetic": False,
                                  "status": "PREPARED_RESOURCE_ADMISSION_ONLY", "families": {args.family: identity}})
    panel = s.read(s.DESIGN / "PANEL.json")["families"][args.family]
    s.save(root / "PANEL.json", {"inputs": panel})
    slots = [x for x in s.lines(s.DESIGN / "SLOTS.jsonl") if x["unit_id"] == "qualification/" + args.family]
    s.save(root / "SLOTS.json", slots)
    shutil.copyfile(s.DESIGN / "PLAN.json", root / "PLAN.json")
    cmd = [str(executable), str(root / "native"), contract["models"]["target"]["path"], contract["models"]["draft"]["path"],
           str(root / "PANEL.json"), str(root / "SLOTS.json"), args.family, str(root / "BINDING.json"), str(root / "PLAN.json"), "--admit-pools"]
    receipt = {"status": "STARTED", "family": args.family, "new_native_requests": 0, "process_start_utc": now(),
               "argv": cmd, "timeout_seconds": args.timeout, "gpu": {"uuid": gpu_id, "name": gpu_name, "driver": driver},
               "build_receipt_sha256": s.hash_file(build / "BUILD.json"), "plan_sha256": s.hash_file(root / "PLAN.json")}
    s.save(root / "ADMISSION.json", receipt)
    environment = {k: v for k, v in os.environ.items() if not k.startswith(("HS_", "LLAMA_ARG_", "GGML_", "CUDA_"))}
    process, start = None, time.perf_counter()
    try:
        with (root / "stdout.log").open("xb") as out, (root / "stderr.log").open("xb") as err:
            process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=err, env=environment,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            receipt["pid"] = process.pid
            s.save(root / "ADMISSION.json", receipt)
            try:
                code = process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=30)
                receipt["status"] = "RESOURCE_ADMISSION_TIMEOUT"
                raise
        native = s.read(root / "native/result.json")
        s.need(native["requests"] == [], "resource admission unexpectedly generated a request")
        receipt.update(exit_code=code, native_result_sha256=s.hash_file(root / "native/result.json"),
                       status="RESOURCE_ADMITTED" if code == 0 and native["status"] == "RESOURCE_ADMITTED" else "RESOURCE_NOT_ADMITTED")
        if "error" in native:
            receipt["error"] = native["error"]
        if "memory_after_provisioning" in native:
            receipt["memory_after_provisioning"] = native["memory_after_provisioning"]
    except BaseException as exc:
        if receipt["status"] == "STARTED":
            receipt["status"] = "RESOURCE_ADMISSION_FAILED"
        receipt["error"] = str(exc)
        raise
    finally:
        if process is not None and process.poll() is None:
            process.kill(); process.wait(timeout=30)
        receipt.update(cleanup_verified=process is None or process.poll() is not None,
                       process_end_utc=now(), owned_seconds=time.perf_counter() - start)
        s.save(root / "ADMISSION.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt["status"] == "RESOURCE_ADMITTED" else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=s.FAMILIES, required=True)
    for name in ("build", "models", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    raise SystemExit(admit(parser.parse_args()))
