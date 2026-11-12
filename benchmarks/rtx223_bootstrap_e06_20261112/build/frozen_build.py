"""Fresh MSVC artifacts from frozen files. No probe or observer loading/execution."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
E04 = ROOT.parent / "rtx223-round1-resume-20261112-e04"
TC = E04 / "runtime/toolchain-v1"
VC = TC / "vc"
COMPILER = VC / "bin/Hostx64/x64"
SDK = TC / "sdk"
SDKVER = "10.0.26100.0"
CUDA = TC / "cuda/include"
CUPTI = Path("E:/rtx170/profiler/sdk/nvidia/cuda_cupti/include")
SYSTEM = Path(os.environ["SystemRoot"]).resolve()
PY = Path(sys.executable).resolve()
LOCKLIB = E04 / "runtime/input_closure_v2.py"
PELIB = E04 / "e04/frontend/pe_identity_v2.py"


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def dump(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n")


def files_in(roots):
    selected = set()
    for root in roots:
        if not root.exists():
            raise FileNotFoundError(root)
        if root.is_file():
            selected.add(root.resolve())
        else:
            selected.update(p.resolve() for p in root.rglob("*") if p.is_file())
    return sorted(selected, key=str)


def snapshot(paths):
    return {str(p): {"sha256": digest(p), "bytes": p.stat().st_size} for p in paths}


def build(src, kind, attempt):
    freeze = runpy.run_path(str(LOCKLIB))["ReadFreeze"]()
    try:
        execute_build(src, kind, attempt, freeze)
    except BaseException:
        (attempt / "FAILURE.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    finally:
        freeze.release()


def execute_build(src, kind, attempt, freeze):
    sources = {"probes": ["main.cpp", "backend.hpp", "native.cpp", "fake.cpp"],
               "observer": ["observer.cpp"]}[kind]
    stages = {"probes": [("cpu-probe.exe", ["main", "fake"]), ("native-probe.exe", ["main", "native"])],
              "observer": [("observation.dll", ["observer"])]}[kind]
    inputs = attempt / "source"
    inputs.mkdir()
    temp = attempt / "temp"
    temp.mkdir()
    for name in sources:
        freeze.add(src / name)
        shutil.copyfile(src / name, inputs / name)
        if digest(src / name) != digest(inputs / name):
            raise ValueError(f"copy changed {name}")
    sdkinclude = SDK / "Include" / SDKVER
    include_dirs = [inputs, VC / "include", *(sdkinclude / s for s in ("ucrt", "um", "shared", "winrt"))]
    if kind == "probes":
        include_dirs.extend([CUPTI, CUDA])
    lib_dirs = [VC / "lib/x64", SDK / "Lib" / SDKVER / "um/x64", SDK / "Lib" / SDKVER / "ucrt/x64"]
    ordered_libs = ["kernel32.lib", "bcrypt.lib", "advapi32.lib", "psapi.lib", "user32.lib"]
    if kind == "observer":
        ordered_libs.append("tdh.lib")
    env = {
        "SystemRoot": str(SYSTEM), "WINDIR": str(SYSTEM),
        "PATH": ";".join(map(str, [COMPILER, SDK / "bin" / SDKVER / "x64", SYSTEM / "System32"])),
        "TEMP": str(temp), "TMP": str(temp), "LIB": ";".join(map(str, lib_dirs)),
        "VSLANG": "1033", "NUMBER_OF_PROCESSORS": "1", "VCToolsInstallDir": str(VC) + "\\",
    }
    compiles = {}
    for name in sources:
        if name.endswith(".cpp"):
            stem = Path(name).stem
            compiles[stem] = [str(COMPILER / "cl.exe"), "/nologo", "/std:c++17", "/EHsc",
                              "/utf-8", "/W4", "/O2", "/MT", "/X", "/c",
                              *(f"/I{p}" for p in include_dirs), "/sourceDependencies",
                              str(attempt / (stem + ".deps.json")), f"/Fo{attempt / (stem + '.obj')}", str(inputs / name)]
    links = {}
    for image, stems in stages:
        flags = ["/DLL"] if image.endswith(".dll") else ["/SUBSYSTEM:CONSOLE"]
        links[image] = [str(COMPILER / "link.exe"), "/nologo", "/INCREMENTAL:NO",
                        "/MACHINE:X64", "/DYNAMICBASE", "/NXCOMPAT", "/VERBOSE:LIB",
                        *flags, f"/OUT:{attempt / image}", *(str(attempt / (s + ".obj")) for s in stems), *ordered_libs]
    recipe = attempt / "RECIPE.json"
    dump(recipe, {"kind": kind, "sources": str(src), "original_files": sources, "cwd": str(attempt),
                  "compile": compiles, "link": links, "env": env})
    trees = [inputs, COMPILER, SDK / "bin" / SDKVER / "x64", *include_dirs[1:], *lib_dirs,
             Path(__file__).resolve(), PY, LOCKLIB, PELIB, recipe]
    paths = files_in(trees)
    for path in paths:
        freeze.add(path)
    initial = snapshot(paths)
    freeze_path = attempt / "FROZEN_INPUTS.json"
    dump(freeze_path, initial)
    freeze.add(freeze_path)
    freeze_hash = digest(freeze_path)
    dependency_counts = {}

    def run(name, command):
        with (attempt / (name + ".log")).open("xb") as output:
            result = subprocess.run(command, cwd=attempt, env=env, stdout=output,
                                    stderr=subprocess.STDOUT, timeout=240)
        if result.returncode:
            raise ValueError(f"{name} exit {result.returncode}; inspect retained log")

    for stem, command in compiles.items():
        run(stem, command)
        deps = json.loads((attempt / (stem + ".deps.json")).read_bytes())["Data"]
        dependencies = {Path(s).resolve() for s in [deps["Source"], *deps["Includes"]]}
        if len(dependencies) < 2 or any(str(p) not in initial for p in dependencies):
            raise ValueError(f"unexpected source dependency for {stem}: {dependencies-set(paths)}")
        dependency_counts[stem] = len(dependencies)
    objects = [attempt / (stem + ".obj") for stem in compiles]
    for obj in objects:
        freeze.add(obj)
    object_ids = snapshot(objects)
    dump(attempt / "LINK_FROZEN_OBJECTS.json", object_ids)
    freeze.add(attempt / "LINK_FROZEN_OBJECTS.json")
    inspect = runpy.run_path(str(PELIB))["inspect"]
    outputs = {}
    for image, command in links.items():
        run(image, command)
        link_log = (attempt / (image + ".log")).read_text(encoding="utf-8", errors="replace")
        searched = {Path(s.strip().strip('"')).resolve() for s in re.findall(
            r"^\s*Searching (.+?\.lib):\s*$", link_log, re.M | re.I)}
        if not searched or any(str(p) not in initial for p in searched):
            raise ValueError(f"unbound link libs: {searched-set(paths)}")
        pe = inspect(attempt / image)
        imports = sorted(set(pe["imports"] + pe["delay_imports"]), key=str.lower)
        # An explicit startup allowlist applies to both probe flavors. Dynamic targets
        # are covered by source review and separate runtime observation requirements.
        system_imports = {"kernel32.dll","advapi32.dll","bcrypt.dll","psapi.dll","tdh.dll",
                          "user32.dll","ntdll.dll","sechost.dll"}
        unknown = [s for s in imports if s.lower() not in system_imports]
        if unknown or pe["is_dll"] != image.endswith(".dll") or pe["machine"] != "AMD64":
            raise ValueError(f"unexpected PE profile: {image} {unknown}")
        outputs[image] = {"path": str(attempt / image), "sha256": pe["sha256"],
                          "bytes": pe["bytes"], "machine": pe["machine"], "imports": imports,
                          "exports": sorted(pe["exports"]), "delay_imports": pe["delay_imports"],
                          "link_libraries": sorted(map(str, searched))}
        dump(attempt / (image + ".pe.json"), pe)
    if files_in(trees) != paths or snapshot(paths) != initial or snapshot(objects) != object_ids:
        raise ValueError("frozen inputs or their membership changed")
    dump(attempt / "BUILD.json", {"status": "PASS_STATIC_BUILD_ONLY", "kind": kind,
         "input_files": len(initial), "input_bytes": sum(r["bytes"] for r in initial.values()),
         "freeze_sha256": freeze_hash, "recipe_sha256": digest(recipe),
         "translation_units_dependencies": dependency_counts, "objects": object_ids, "outputs": outputs,
         "GPU_calls": 0, "normal_numerical_DLL_loads": 0, "binaries_executed": 0,
         "limits": "Controlled code-generation files and commands locked throughout; Windows system services, system DLLs, interpreter runtime and hardware are not a sealed build environment."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("probes","observer"))
    parser.add_argument("src", type=Path)
    parser.add_argument("attempt", type=int)
    args = parser.parse_args()
    out = HERE / f"{args.kind}-attempt-{args.attempt:03d}"
    out.mkdir(exist_ok=False)
    build(args.src.resolve(strict=True), args.kind, out)
