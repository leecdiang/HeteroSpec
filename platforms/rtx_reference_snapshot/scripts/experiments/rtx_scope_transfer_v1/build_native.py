"""Build a new scope-transfer cohort from an authenticated source archive.

This command does not execute a model. Historical objects are never reused.
The vendor numerical DLLs are copied only after checking the delivered manifest.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import zipfile

import study as s


def build(args):
    root = args.out.resolve()
    s.need(not root.exists(), "fresh build directory required")
    s.need(s.hash_file(args.archive) == s.SOURCE_ZIPS[args.variant], "source archive hash differs")
    manifest = s.read(args.dll_manifest)["numerical_DLL_sha256"]
    s.need(len(manifest) == 21, "exact delivered 21-module manifest required")
    for name, digest in manifest.items():
        s.need(Path(name).name == name and s.hash_file(args.dll_dir / name) == digest, "numerical DLL differs: " + name)
    for tool in (args.zig, args.cmake, args.ninja):
        s.need(tool.is_file(), "missing build tool: " + str(tool))
    root.mkdir(parents=True)
    source, core, binary = root / "source", root / "core", root / "bin"
    core.mkdir(); binary.mkdir()
    receipts = []
    report = {"status": "BUILDING", "source_variant": args.variant,
              "source_zip_sha256": s.hash_file(args.archive), "commands": receipts,
              "numerical_modules": manifest,
              "tools": {k: {"path": str(getattr(args, k).resolve()), "sha256": s.hash_file(getattr(args, k))}
                        for k in ("zig", "cmake", "ninja")},
              "native_requests": 0}
    s.save(root / "BUILD.json", report)

    def execute(label, argv):
        start = time.perf_counter()
        argv = list(map(str, argv))
        with (root / (label + ".log")).open("xb") as log:
            process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                code = process.wait(timeout=args.command_timeout)
            except BaseException:
                process.kill(); process.wait()
                raise
        receipts.append({"label": label, "argv": argv, "pid": process.pid, "exit_code": code,
                         "seconds": time.perf_counter() - start, "log_sha256": s.hash_file(root / (label + ".log"))})
        s.save(root / "BUILD.json", report)
        s.need(code == 0, label + " failed; retained log: " + str(root / (label + ".log")))

    try:
        with zipfile.ZipFile(args.archive) as archive:
            index = s.strict_json(archive.read("INDEX.json"))["files"]
            source_files = {}
            for name, pin in index.items():
                if not name.startswith("native/source/"):
                    continue
                relative = Path(name).relative_to("native/source")
                dest = (source / relative).resolve()
                s.need(dest.is_relative_to(source.resolve()), "unsafe archive path")
                data = archive.read(name)
                s.need(len(data) == pin["bytes"] and hashlib.sha256(data).hexdigest() == pin["sha256"], "source member hash differs")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                source_files[relative.as_posix()] = pin
        s.save(root / "SOURCE_MEMBERS.json", source_files)
        header = source / "src/hs_scope.h"
        original = header.read_text(encoding="utf-8")
        start, end = original.index("inline int layout95()"), original.index("inline int mask()")
        changed = original[:start] + "inline int requested_layout=0;\ninline int layout95(){return requested_layout;}\n" + original[end:]
        header.write_text(changed, encoding="utf-8", newline="\n")
        report["source_changes"] = {"src/hs_scope.h": {"before": source_files["src/hs_scope.h"]["sha256"], "after": s.hash_file(header)}}
        code = Path(__file__).parent
        for name in ("worker.cpp", "arm_spec.h"):
            shutil.copyfile(code / name, root / name)
        report["worker_source_sha256"] = s.hash_file(root / "worker.cpp")
        report["arm_spec_sha256"] = s.hash_file(root / "arm_spec.h")
        for name, subcommand in (("ar", "ar"), ("ranlib", "ranlib")):
            (core / (name + ".cmd")).write_text('@echo off\n"' + str(args.zig.resolve()) + '" ' + subcommand + ' %*\n', encoding="utf-8")
        configure = [args.cmake, "-S", source, "-B", core, "-G", "Ninja",
                     f"-DCMAKE_MAKE_PROGRAM={args.ninja.resolve()}",
                     f"-DCMAKE_C_COMPILER={args.zig.resolve()}", "-DCMAKE_C_COMPILER_ARG1=cc",
                     f"-DCMAKE_CXX_COMPILER={args.zig.resolve()}", "-DCMAKE_CXX_COMPILER_ARG1=c++",
                     f"-DCMAKE_AR={core}/ar.cmd", f"-DCMAKE_RANLIB={core}/ranlib.cmd",
                     "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF", "-DGGML_BACKEND_DL=ON",
                     "-DGGML_CPU=OFF", "-DGGML_CUDA=OFF", "-DLLAMA_SUBPROCESS=OFF", "-DLLAMA_BUILD_APP=OFF",
                     "-DLLAMA_BUILD_TESTS=OFF", "-DLLAMA_BUILD_EXAMPLES=OFF", "-DLLAMA_BUILD_MTMD=OFF",
                     "-DLLAMA_OPENSSL=OFF", "-DLLAMA_BUILD_UI=OFF", "-DLLAMA_USE_PREBUILT_UI=OFF",
                     "-DLLAMA_BUILD_NUMBER=10839", "-DLLAMA_BUILD_COMMIT=0cae43063", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
        execute("configure", configure)
        execute("core", [args.cmake, "--build", core, "--target", "llama", "vendor-hash", "-j", str(args.jobs)])
        includes = [source / "src", core / "src", source / "include", source / "ggml/include", source / "common", source / "vendor", root]
        execute("worker", [args.zig, "c++", "-std=c++17", "-O3", "-DNDEBUG", "-DGGML_BACKEND_DL",
                           "-D_CRT_SECURE_NO_WARNINGS", '-DHS_SOURCE_VARIANT="' + args.variant + '"',
                           *[f"-I{p}" for p in includes], "-c", root / "worker.cpp", "-o", root / "worker.obj"])
        execute("link", [args.zig, "c++", "-O3", root / "worker.obj", core / "src/libllama.a",
                         core / "ggml/src/ggml.a", core / "ggml/src/ggml-base.a", core / "vendor/hash/libvendor-hash.a",
                         "-lpsapi", "-lws2_32", "-lbcrypt", "-o", binary / "rtx-scope-transfer.exe"])
        for name in manifest:
            shutil.copyfile(args.dll_dir / name, binary / name)
            s.need(s.hash_file(binary / name) == manifest[name], "copied DLL differs")
        report.update(status="BUILT_NOT_QUALIFIED", executable_sha256=s.hash_file(binary / "rtx-scope-transfer.exe"),
                      core_sha256=s.hash_file(core / "src/libllama.a"),
                      compile_commands_sha256=s.hash_file(core / "compile_commands.json"))
    except BaseException as exc:
        report.update(status="BUILD_FAILED", error=str(exc))
        raise
    finally:
        s.save(root / "BUILD.json", report)
    print(json.dumps({"status": report["status"], "receipt": str(root / "BUILD.json"), "native_requests": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("original", "metadata4"), required=True)
    for option in ("archive", "out", "dll-manifest", "dll-dir", "zig", "cmake", "ninja"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--command-timeout", type=int, default=3600)
    build(parser.parse_args())
