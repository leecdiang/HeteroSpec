"""Compile/link source-only prototype with read-only qualified Windows cores.

Does not run the resulting executable, enumerate CUDA devices or load a model.
All compiler outputs and caches stay in the newly created workspace build dir.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import time

HERE = Path(__file__).resolve().parent
OLD = Path("D:/rtx211-q8-20261109")


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        while b := f.read(4 * 1024 * 1024):
            h.update(b)
    return h.hexdigest()


def put(p, v):
    with Path(p).open("x", encoding="utf8") as f:
        json.dump(v, f, indent=2)


def build(frontend, out, compiler=None):
    frontend, out = Path(frontend).resolve(), Path(out).resolve()
    workspace = HERE.parent.resolve()
    if workspace not in out.parents:
        raise ValueError("build output must be inside this independent workspace")
    if out.exists():
        raise ValueError("fresh build epoch required")
    out.mkdir(parents=True)
    for name in ("temp", "global-cache", "local-cache"):
        (out / name).mkdir()
    env = os.environ.copy()
    env.update(TEMP=str(out / "temp"), TMP=str(out / "temp"),
               ZIG_GLOBAL_CACHE_DIR=str(out / "global-cache"),
               ZIG_LOCAL_CACHE_DIR=str(out / "local-cache"))
    frontend_identity = {p.name: sha(p) for p in frontend.iterdir() if p.is_file()}
    all_inputs, commands, builds = {}, [], {}
    for core in ("loop4", "packed"):
        folder = out / core
        (folder / "bin").mkdir(parents=True)
        oldrun = OLD / (core + "-v2")
        original_build = json.loads((oldrun / "BUILD.json").read_bytes())
        expected_core = Path("D:/rtx192-review-v2/build-v2") / core / "src/libllama.a"
        if sha(expected_core) != original_build["core"]:
            raise ValueError("historical numerical core changed: " + core)
        all_inputs[str(oldrun / "BUILD.json")] = sha(oldrun / "BUILD.json")
        for label in ("worker", "link"):
            args = json.loads((oldrun / (label + ".json")).read_bytes())["argv"]
            args = [x.replace(str(oldrun), str(folder)).replace(str(OLD / "frontend-v2"), str(frontend)) for x in args]
            if compiler:
                compiler = Path(compiler).resolve()
                original_compiler = Path(args[0])
                if sha(compiler) != sha(original_compiler):
                    raise ValueError("staged compiler differs from historical compiler")
                args[0] = str(compiler)
            if label == "worker":
                args[2:2] = ["-include", str(HERE / "timeline.hpp")]
            for arg in args:
                path = Path(arg)
                if path.is_file() and not (out in path.resolve().parents):
                    all_inputs[str(path.resolve())] = sha(path)
            start = time.monotonic()
            log = folder / (label + ".log")
            with log.open("xb") as f:
                p = subprocess.run(args, cwd=out, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=300)
            record = {"argv": args, "cwd": str(out), "wall_seconds": time.monotonic() - start,
                      "returncode": p.returncode, "log_sha256": sha(log)}
            put(folder / (label + ".json"), record)
            commands.append(record)
            if p.returncode:
                put(out / "FAILED.json", {"stage": core + "/" + label, "commands": commands,
                                          "model_requests": 0, "GPU_launches": 0})
                raise RuntimeError("compile-only prototype build failed; inspect retained log")
        builds[core] = {"exe_path": str(folder / "bin/worker.exe"), "exe_sha256": sha(folder / "bin/worker.exe"),
                        "object_sha256": sha(folder / "worker.obj"), "core_sha256": original_build["core"],
                        "expected_modules_not_loaded": original_build["modules"],
                        "runtime_invocation": "NOT_RUN", "native_qualified": False}
    for path, before in all_inputs.items():
        if sha(path) != before:
            raise ValueError("read-only build input mutated: " + path)
    result = {"status": "BOTH_FRONTENDS_COMPILED_LINKED_NOT_RUN_NOT_QUALIFIED", "frontend": str(frontend),
              "frontend_identity": frontend_identity, "input_hashes_before_and_after_equal": all_inputs,
              "commands": commands, "builds": builds, "model_requests": 0, "GPU_launches": 0,
              "timeline_header": "COMPILES_BUT_NOT_INTEGRATED", "historical_numerical_core_modified": False,
              "original_R_modified": False, "DLL_loading_or_native_execution": "NOT_RUN"}
    put(out / "BUILD.json", result)
    print(json.dumps({"status": result["status"], "builds": builds}, indent=2))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--frontend", default=str(HERE / "prepared_frontend"))
    p.add_argument("--output", default=str(HERE / "build"))
    p.add_argument("--compiler", default=None)
    args = p.parse_args()
    build(args.frontend, args.output, args.compiler)
