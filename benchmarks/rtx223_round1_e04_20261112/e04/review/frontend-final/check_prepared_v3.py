"""Independent v3 pre-codegen artifact check; no producer helpers imported."""
from pathlib import Path
import datetime
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / "e04/frontend/run-v3"
EXPECTED = "3b42dc1da597c587790718eee32b8317d52730a16190a7db10fe757ffc0aba93"


def need(ok, text):
    if not ok:
        raise ValueError(text)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    out = HERE / "PREPARED_V3_REVIEW.json"
    need(not out.exists(), "fresh pre-codegen review required")
    prepared_path = RUN / "PREPARED_INPUTS.json"
    need(sha(prepared_path) == EXPECTED, "prepared input manifest SHA differs")
    prepared = json.loads(prepared_path.read_bytes())
    recipe = json.loads((RUN / "RECIPE.json").read_bytes())
    need(sha(RUN / "RECIPE.json") == prepared["recipe_sha256"], "recipe differs")
    here = ROOT / "e04/frontend"
    roots = [Path(recipe[k]) for k in ("toolchain", "source", "dependencies")] + [RUN / "workflow"]
    need(all(p.resolve().is_relative_to(here) for p in roots), "an input root is not an owned e04 copy")
    actual_paths = {str(p.resolve()) for base in roots for p in base.rglob("*") if p.is_file()}
    need(actual_paths == set(prepared["tree_membership"]), "prepared input-tree membership differs")
    for entry in prepared["entries"]:
        p = Path(entry["path"])
        need(p.resolve().is_relative_to(here), "outside/old input in prepared set")
        stat = p.stat()
        need(stat.st_size == entry["bytes"] and stat.st_mtime_ns == entry["mtime_ns"] and sha(p) == entry["sha256"], "prepared bytes/stat mismatch: " + str(p))
    by_path = {entry["path"]: entry["sha256"] for entry in prepared["entries"]}
    for path, h in prepared["tree_membership"].items():
        need(by_path.get(path) == h, "tree member missing from complete freeze entries")
    for path, h in recipe["workflow_files"].items():
        need(sha(path) == h == by_path[path], "actual staged workflow helper not bound")
    tool = Path(recipe["toolchain"])
    tool_inputs = {p for p in actual_paths if Path(p).is_relative_to(tool)}
    need(tool_inputs and all(p in by_path for p in tool_inputs), "reused run-v1 tooltree not included in v3 freeze")
    for core, info in recipe["cores"].items():
        need(len(info["prescan_dependencies"]) > 1 and len(set(info["prescan_dependencies"])) == len(info["prescan_dependencies"]), "dependency list empty or duplicate")
        need(all(str(Path(p).resolve()) in by_path for p in info["prescan_dependencies"]), "prescan dependency is not frozen")
        need(info["effective_CPU"] and info["effective_CPU"][0] == ["cpu", "arrowlake-s"] and any(k == "feature" for k, v in info["effective_CPU"]), "resolved CPU/features absent")
        need(all(path in by_path for path in info["archives"]), "link archive not frozen")
        need("-MD" in info["compile"] and "-v" in info["compile"], "actual codegen lacks dependency/effective-command witness")
        need("/verbose" in info["link"] and any(a.startswith("/map:") for a in info["link"]), "link lacks extraction trace/map")
    workflow = (RUN / "workflow/frozen_build_v3.py").read_text(encoding="utf8")
    need("Path(active_freeze_module.__file__).resolve()==workflow/'input_freeze.py'" in workflow and "Path(active_dependency_module.__file__).resolve()==workflow/'dep_witness_v2.py'" in workflow, "active helper-origin checks missing")
    need("execute the staged, frozen workflow copy" in workflow and "actual==info['prescan_dependencies']" in workflow, "active workflow/dependency equality guard missing")
    need(recipe["native_release"] == "BLOCKED", "preparation native gate released")
    result = {"schema": "heterospec.e04.independent-frontend-prepared-v3-review.v1", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "PASS_FOR_CPU_CODEGEN_PREPARATION_ONLY", "prepared_manifest_sha256": EXPECTED, "entries_independently_rehashed": len(prepared["entries"]), "tree_membership": len(actual_paths), "reused_toolchain_members_in_actual_v3_freeze": len(tool_inputs), "reused_toolchain_root": str(tool), "workflow_helpers_bound": recipe["workflow_files"], "core_dependencies": {c: len(i["prescan_dependencies"]) for c, i in recipe["cores"].items()}, "source_review": "strict quoted cc1 parser and Make dependency target/source checks; staged actual helper identities; generated-object snapshot includes mtime before freezing link input", "old_files_locked_by_reviewer": False, "producer_verifier_imported": False, "normal_DLL_loads": 0, "CUDA_calls": 0, "model_requests": 0, "GPU_launches": 0, "native_admission": False, "pending": ["Actual Win32 handle freeze receipt", "Actual -MD dependencies versus -M prescan equality", "Actual resolved cc1 CPU/features equality", "LLD archive/member bytes and map/trace agreement", "Final EXE hashes and offline PE identity"], "scope_limit": "This CPU preflight is not codegen/link success, complete OS filesystem-read attestation, numerical qualification or native release"}
    out.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({k: result[k] for k in ("status", "entries_independently_rehashed", "tree_membership", "reused_toolchain_members_in_actual_v3_freeze", "core_dependencies")}, indent=2))


if __name__ == "__main__":
    main()
