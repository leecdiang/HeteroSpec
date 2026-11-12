"""Fresh tiny CPU compile/link fixture. It is never executed or DLL-loaded.

Phase manifests bind known inputs before each compiler/ar/link invocation.
The original read-only Zig tool is hash checked, not OS-write-locked here;
this fixture does not claim the parent's stronger isolated product freeze.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import time

HERE = Path(__file__).resolve().parent
OUT = HERE / "actual-trace-v1"
OUT.mkdir(exist_ok=False)
ZIG = Path("C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx221-round1-20261112/request/compiler_copy/zig.exe")
KERNEL32 = Path("D:/rtx211-q8-20261109/compiler-cache/o/5af3175ccaf8cae15ba0fc4c0a1096aa/kernel32.lib")


def identity(p):
    p = Path(p).resolve()
    data = p.read_bytes()
    return {"path": str(p), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def put(p, value):
    with Path(p).open("x", encoding="utf8") as f:
        json.dump(value, f, indent=2)


def run(label, args, inputs):
    before = [identity(p) for p in inputs]
    freeze = {"label": label, "argv": args, "cwd": str(OUT), "inputs": before,
              "scope": "tiny CPU trace fixture logical pre/post binding; not OS immutability or numerical qualification"}
    put(OUT / (label + "-PRE.json"), freeze)
    start = time.monotonic()
    r = subprocess.run(args, cwd=OUT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    (OUT / (label + ".log")).write_bytes(r.stdout)
    after = [identity(p) for p in inputs]
    result = {"returncode": r.returncode, "seconds": time.monotonic() - start,
              "inputs_pre_post_equal": before == after,
              "log_sha256": hashlib.sha256(r.stdout).hexdigest(), "inputs": after}
    put(OUT / (label + "-POST.json"), result)
    if r.returncode or before != after:
        raise RuntimeError(label + " failed: " + r.stdout.decode("utf8", errors="replace"))


sources = {
    "fixture_selected.c": "int chosen(void){return 9;}\n",
    "fixture_unused.c": "int never_used(void){return 10;}\n",
    "entry.c": "__declspec(dllimport) unsigned long __stdcall GetLastError(void); int chosen(void); int mainCRTStartup(void){return chosen()+(int)GetLastError();}\n",
}
for name, text in sources.items():
    p = OUT / name
    p.write_bytes(text.encode())
    run(name, [str(ZIG), "clang", "-target", "x86_64-windows-msvc", "-O2", "-nostdinc", "-fno-stack-protector", "-MD", "-MF", str(OUT / (name + ".d")), "-c", str(p), "-o", str(p.with_suffix(".obj"))],
        [ZIG, p, Path(__file__)])
lib = OUT / "fixture.lib"
selected = OUT / "fixture_selected.obj"
unused = OUT / "fixture_unused.obj"
run("archive", [str(ZIG), "ar", "rcs", str(lib), str(selected), str(unused)], [ZIG, selected, unused, Path(__file__)])
args = [str(ZIG), "lld-link", "/nologo", "/nodefaultlib", "/entry:mainCRTStartup", "/subsystem:console", "/verbose:lib", "/map:" + str(OUT / "fixture.map"), "/out:" + str(OUT / "never-executed.exe"), str(OUT / "entry.obj"), str(lib), str(KERNEL32)]
run("link", args, [ZIG, OUT / "entry.obj", lib, KERNEL32, Path(__file__)])
spec = importlib.util.spec_from_file_location("fixture_link_witness", HERE.parent / "link_witness.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.analyze_link_inputs((OUT / "link.log").read_text(encoding="utf8"), [lib, KERNEL32])
put(OUT / "WITNESS.json", result)
put(OUT / "RESULT.json", {"status": "PASS", "scope": "actual tiny CPU LLD trace; no EXE execution or DLL load", "selected_members": result["selected_member_count"], "model_requests": 0, "GPU_launches": 0})
print(json.dumps({"status": "PASS", "selected_members": result["selected_member_count"], "trace": (OUT / "link.log").read_text(encoding="utf8")}, indent=2))
