"""Offline binding only. Does not import the runner/probe or create approval or launch authority."""
from pathlib import Path
import argparse
import json
import runpy
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
helpers = runpy.run_path(str(HERE/"identify.py"))
identity, write = helpers["identity"], helpers["write"]
python = helpers["PYTHON"]
e04 = helpers["E04"]
ReadFreeze = runpy.run_path(str(e04/"runtime/input_closure_v2.py"))["ReadFreeze"]


def python_members():
    base = python.parent
    files = {p for p in base.iterdir() if p.is_file()}
    for path in (base/"Lib").rglob("*"):
        if path.is_file() and "site-packages" not in path.relative_to(base/"Lib").parts:
            files.add(path)
    files.update(p for p in (base/"DLLs").rglob("*") if p.is_file())
    return sorted(files,key=str)


def freeze_python(out):
    if Path(sys.executable).resolve() != python or not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        raise ValueError("expected isolated base interpreter, -I -S -B")
    paths = python_members()
    absent = [python.parent/n for n in ("python311.zip", "python311._pth", "python._pth", "pyvenv.cfg")]
    locks = ReadFreeze()
    try:
        for p in paths:
            locks.add(p)
        records = [identity(p) for p in paths]
        if paths != python_members() or any(p.exists() for p in absent):
            raise ValueError("runtime paths/overrides changed")
        write(out, {"schema":"heterospec.e06.python-inputs.v1", "version": sys.version,
            "flags":["-I","-S","-B"], "path": sys.path, "interpreter":identity(python),
            "base_root":str(python.parent), "files": records,
            "absent":[str(p) for p in absent],
            "membership":"all base-root files + DLLs recursive + Lib recursive excluding site-packages; includes existing bytecode. -B disables bytecode writes only.",
            "scope":"Disk snapshot locked during inventory. Native approval runner revalidates these files. Does not attest already executing process memory or OS loader before main."})
    finally:
        locks.release()


def bind(out, inventory, deployment, observer, probes, source, evidence):
    obsdir = observer.parent
    probedir = ROOT.parent / "rtx223-e06/build/probes-attempt-002"
    cpu = probedir/"cpu-probe.exe"
    contract = ROOT/"CONTRACT.json"
    # Include code-generating witnesses, final sources, linked binaries, runner and the nominal contract.
    # Pin receipts (including historical failures) as evidence only; a release has no allow bit.
    inputs = {contract, inventory, deployment, deployment.with_suffix(".edges.json"), probes, cpu, observer,
        ROOT/"runner/runner.py",ROOT/"runner/winjob.py",ROOT/"runner/observation.py",ROOT/"observation/observer.cpp",
        HERE/"frozen_build.py",HERE/"identify.py",Path(__file__).resolve(),
        *(source/p for p in ("main.cpp","backend.hpp","native.cpp","fake.cpp")),
        *evidence, *(p/n for p in (obsdir,probedir) for n in (
                "BUILD.json","RECIPE.json","FROZEN_INPUTS.json","LINK_FROZEN_OBJECTS.json"))}
    locks = ReadFreeze()
    try:
        for p in sorted(inputs,key=str):
            locks.add(p)
        for p in (obsdir,probedir):
            rec = json.loads((p/"BUILD.json").read_bytes())
            expected = rec["freeze_sha256"]
            if identity(p/"FROZEN_INPUTS.json")["sha256"] != expected:
                raise ValueError("build freeze mismatch")
            for name, output in rec["outputs"].items():
                if identity(p/name)["sha256"] != output["sha256"]:
                    raise ValueError("linked output drift")
        if any(identity(source/n)["sha256"] != identity(probedir/"source"/n)["sha256"]
               for n in ("main.cpp","backend.hpp","native.cpp","fake.cpp")):
            raise ValueError("probe sources differ from build")
        if identity(ROOT/"observation/observer.cpp")["sha256"] != identity(obsdir/"source/observer.cpp")["sha256"]:
            raise ValueError("observer source differs from build")
        d = json.loads(deployment.read_bytes())
        for item in [*d["modules"].values(), *d["candidates"], d["api_set_schema"]]:
            p = Path(item["path"])
            locks.add(p)
            if any(identity_data != item[k] for k,identity_data in identity(p).items()):
                raise ValueError(f"deployment identity changed {p}")
        py = json.loads(inventory.read_bytes())
        if python_members() != [Path(r["path"]) for r in py["files"]] or any(Path(p).exists() for p in py["absent"]):
            raise ValueError("Python membership drift")
        for r in py["files"]:
            p = Path(r["path"])
            locks.add(p)
            if identity(p) != r:
                raise ValueError(f"python drift {p}")
        receipt = {"schema":"heterospec.e06.release.v1", "contract":identity(contract),
            "deployment":identity(deployment),"python_inventory":identity(inventory),
            "probe":identity(probes),"cpu_probe":identity(cpu),"observation":identity(observer),
            "files":[identity(p) for p in sorted(inputs,key=str)],
            "scope":"disk identity, not execution clearance; explicit owner authorization and future admission still required"}
        write(out, receipt)
        builds = []
        for path in sorted(HERE.glob("*-attempt-*/BUILD.json")):
            report=json.loads(path.read_bytes())
            builds.append({"attempt":path.parent.name, "status":report["status"],
                "sha256":identity(path)["sha256"], "frozen_files":report["input_files"],
                "frozen_bytes":report["input_bytes"], "freeze_sha256": report["freeze_sha256"],
                "recipe_sha256":report["recipe_sha256"], "tu_input_counts":report["translation_units_dependencies"],
                "outputs":{k:{key:r[key] for key in ("bytes","sha256","imports","delay_imports","exports")}
                           for k,r in report["outputs"].items()}})
        compact=lambda row:{k:v for k,v in row.items() if k in ("sha256","bytes","version")}
        write(out.with_name("REVIEW_IDENTITIES.json"),{
            "schema":"heterospec.e06.offline-identities.v1","status":"STATIC_IDENTITY_ONLY",
            "builds":builds,"release_sha256":identity(out)["sha256"],
            "contract_sha256":identity(contract)["sha256"],"deployment_sha256":identity(deployment)["sha256"],
            "python_inventory_sha256":identity(inventory)["sha256"],"python_input_count":len(py["files"]),
            "python":compact(identity(python)),"module_roots":{n:compact(r) for n,r in d["modules"].items()},
            "pinned_additional_images":[{"name":r["name"],**compact(r)} for r in d["candidates"]],
            "local_reviewer_paths":{k: str(p.relative_to(ROOT)).replace("\\","/") for k,p in
                               (("release",out),("contract",contract),("python",inventory),("deployment",deployment))},
            "unresolved_static_non_delay_imports":len(d["unresolved_imports"]),
            "delay_or_other_edges_without_automatic_name_approval":len(d["other_routes"]),
            "bound_successor_files":{str(Path(r["path"]).relative_to(ROOT.parent)).replace("\\","/"):compact(r)
                                     for r in receipt["files"]},
            "limits":["Disk and PE identity do not prove actual mapped modules or runtime behavior.",
                      "Build locks cover the recorded code-generation files and link inputs, not the Windows system image.",
                      "No native probe was started or numerical DLL loaded by build or identity checks."]})
    finally:
        locks.release()


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("python","bind"))
    parser.add_argument("out",type=Path)
    parser.add_argument("--inventory",type=Path)
    parser.add_argument("--deployment",type=Path)
    parser.add_argument("--observer",type=Path)
    parser.add_argument("--probes",type=Path)
    parser.add_argument("--source",type=Path)
    parser.add_argument("--evidence",nargs="*",type=Path,default=[])
    args=parser.parse_args()
    if args.action=="python":
        freeze_python(args.out.resolve())
    else:
        bind(args.out.resolve(),*(p.resolve(strict=True) for p in (
            args.inventory,args.deployment,args.observer,args.probes,args.source)),
            [p.resolve(strict=True) for p in args.evidence])
