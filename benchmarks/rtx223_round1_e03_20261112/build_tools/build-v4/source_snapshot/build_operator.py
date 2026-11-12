"""Build only. Does not create a CUDA context, load a model, or execute a probe."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def need(value, message):
    if not value:
        raise RuntimeError(message)

def extract_function(source, marker):
    begin = source.index(marker)
    opening = source.index("{", begin)
    depth = 1
    closing = opening + 1
    while depth:
        depth += (source[closing] == "{") - (source[closing] == "}")
        closing += 1
    return source[begin:closing] + "\n"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", default="D:/rtx192-review-v2/native-v2/cores/packed")
    parser.add_argument("--cuda", default="D:/rtx184-tools/cuda")
    parser.add_argument("--msvc", default="D:/rtx184-tools/msvc")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    core, cuda, msvc = map(Path, (args.core, args.cuda, args.msvc))
    out = Path(args.out).resolve()
    need(out.is_relative_to(ROOT), "build output must stay inside the isolated study")
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out / "source_snapshot"
    for p in (ROOT / "native").glob("*"):
        if p.is_file():
            target = snapshot / "native" / p.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())
    (snapshot / "build_operator.py").write_bytes(Path(__file__).read_bytes())
    cudasrc = core / "ggml/src/ggml-cuda"
    source = (cudasrc / "mmvq.cu").read_text(encoding="utf-8")
    marker = "// Dedicated MoE multi-token kernel."
    prefix = source[:source.index(marker)]
    # The standalone probe does not export the unrelated generic dispatcher.
    omitted_dispatcher = extract_function(prefix, "bool ggml_cuda_should_use_mmvq(")
    prefix = prefix.replace(omitted_dispatcher, "")
    source_hash = digest(cudasrc / "mmvq.cu")
    need(source_hash == "d9c69fafab943383b29e525417f5e2157a445c9b1afca97b7d9de23d20a2564a", "unexpected original MMVQ source")
    for include in re.findall(r'^#include "([^"]+)"', prefix, re.MULTILINE):
        absolute = (cudasrc / include).resolve().as_posix()
        prefix = prefix.replace(f'#include "{include}"', f'#include "{absolute}"')
    (out / "bound_mmvq_prefix.cuh").write_text(prefix, encoding="utf-8", newline="\n")
    quantizer = (cudasrc / "quantize.cu").read_text(encoding="utf-8")
    body = extract_function(quantizer, "__launch_bounds__(CUDA_QUANTIZE_BLOCK_SIZE, 1)\nstatic __global__ void quantize_q8_1(")
    (out / "bound_quantizer.cuh").write_text(body, encoding="utf-8", newline="\n")
    vc = msvc / "VC/Tools/MSVC/14.44.35207"
    sdk = msvc / "Windows Kits/10"
    sdkver = "10.0.26100.0"
    env = os.environ.copy()
    env["PATH"] = ";".join(map(str, [vc / "bin/Hostx64/x64", sdk / f"bin/{sdkver}/x64", cuda / "bin"])) + ";" + env.get("PATH", "")
    env["INCLUDE"] = ";".join(str(p) for p in [vc / "include", *[sdk / f"Include/{sdkver}/{x}" for x in ("ucrt", "shared", "um", "winrt", "cppwinrt")]])
    env["LIB"] = ";".join(str(p) for p in [vc / "lib/x64", sdk / f"Lib/{sdkver}/ucrt/x64", sdk / f"Lib/{sdkver}/um/x64"])
    env["CUDA_PATH"] = str(cuda)
    env["TEMP"] = env["TMP"] = str(out)
    command = [str(cuda / "bin/nvcc.exe"), "-std=c++17", "-O3", "-arch=sm_120", "--ptxas-options=-v", "-lineinfo",
               "-ccbin", str(vc / "bin/Hostx64/x64"), "-Xcompiler=/MT,/O2,/EHsc", "-DGGML_CUDA_NO_VMM",
               "-I"+str(out), "-I"+str(core / "ggml/include"), "-I"+str(core / "ggml/src"),
               "-I"+str(core / "vendor"), "-I"+str(cudasrc),
               str(ROOT / "native/operator_probe.cu"), "-o", str(out / "operator_probe.exe"), "psapi.lib", "bcrypt.lib"]
    began = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=out, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        (out / "build.log").write_bytes(completed.stdout)
        code, error = completed.returncode, None
    except Exception as exc:
        code, error = None, repr(exc)
    receipt = {"kind":"BUILD_ONLY_NO_GPU", "command":command, "returncode":code, "error":error,
               "wall_seconds":time.monotonic()-began, "native_execution":"NOT_RUN", "source_core":str(core),
               "mmvq_sha256":source_hash,
               "bound_mmvq_prefix_sha256":digest(out / "bound_mmvq_prefix.cuh"),
               "bound_quantizer_sha256":digest(out / "bound_quantizer.cuh"),
               "omitted_unused_host_dispatcher_sha256":hashlib.sha256(omitted_dispatcher.encode()).hexdigest(),
               "dependency_headers_sha256":{str(p.relative_to(core)):digest(p) for p in sorted(core.rglob("*"))
                   if p.is_file() and p.suffix in (".h", ".hpp", ".cuh") and not any(x.startswith(".") for x in p.relative_to(core).parts)},
               "source_sha256":{str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT / "native").glob("*")) if p.is_file()},
               "toolchain":{str(p):digest(p) for p in [cuda/"bin/nvcc.exe",cuda/"bin/ptxas.exe",vc/"bin/Hostx64/x64/cl.exe"]},
               "kernel_launches":0,"model_requests":0,"target_rows":0,"draft_rows":0}
    if (out / "operator_probe.exe").is_file():
        receipt["executable_sha256"] = digest(out / "operator_probe.exe")
    (out / "BUILD.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    print(json.dumps({k:receipt.get(k) for k in ("kind","returncode","error","wall_seconds","native_execution","executable_sha256")},indent=2))
    return 0 if code == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
