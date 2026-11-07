"""Bind real host resources and historical references without model execution.

The resulting identity must be committed and named in FREEZE_COMMIT.json before
host.py accepts requests. Preparation does not itself grant execution admission.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess

import study as s
from host import pin


def prepare(config_path, out):
    config = s.read(config_path)
    root = out.resolve()
    s.need(not root.exists(), "fresh bundle required")
    s.check_plan(s.DESIGN)
    plan, models, panel = [s.read(s.DESIGN / name) for name in ("PLAN.json", "MODEL_PINS.json", "PANEL.json")]
    binding = s.read(s.DESIGN / "EXECUTION_IDENTITY_TEMPLATE.json")
    binding.update(status="FROZEN_BEFORE_FIRST_NATIVE_REQUEST", is_synthetic=False,
                   frozen_utc=datetime.now(timezone.utc).isoformat(), calendar_dates=config["calendar_dates"],
                   resource_caps=config["resource_caps"])
    for key, name in (("plan_sha256", "PLAN.json"), ("panel_sha256", "PANEL.json"), ("schedule_sha256", "SLOTS.jsonl")):
        binding[key] = s.hash_file(s.DESIGN / name)
    root.mkdir(parents=True)
    local = {}
    contract = s.read(config["model_contract"])
    s.need(s.hash_file(config["model_contract"]) == s.MODEL_SHA, "historical model contract differs")
    for family in s.FAMILIES:
        build = Path(config["families"][family]["build"]).resolve()
        admission = Path(config["families"][family]["admission"]).resolve()
        report, admitted = s.read(build / "BUILD.json"), s.read(admission / "ADMISSION.json")
        s.need(report["status"] == "BUILT_NOT_QUALIFIED" and admitted["status"] == "RESOURCE_ADMITTED" and admitted["cleanup_verified"] is True, "resource admission missing")
        s.need(admitted["build_receipt_sha256"] == s.hash_file(build / "BUILD.json"), "admission used different build")
        identity = s.read(admission / "BINDING.json")["families"][family]
        s.need(identity["executable_sha256"] == s.hash_file(build / "bin/rtx-scope-transfer.exe"), "executable changed after admission")
        for name, key in (("worker.cpp", "worker_source_sha256"), ("arm_spec.h", "arm_spec_sha256")):
            s.need(s.hash_file(Path(__file__).parent / name) == report[key], "native source changed after build")
        binding["families"][family] = identity
        local[family] = {"executable": str(build / "bin/rtx-scope-transfer.exe"),
                         **{role: contract["families"][family]["models"][role]["path"] for role in ("target", "draft")}}
        for role in ("target", "draft"):
            path = Path(local[family][role]); expected = models["families"][family]["models"][role]
            s.need(path.stat().st_size == expected["bytes"] and s.hash_file(path) == expected["sha256"], "model hash differs")
        dest = root / "provenance" / family
        dest.mkdir(parents=True)
        for name in ("BUILD.json", "SOURCE_MEMBERS.json", "configure.log", "core.log", "worker.log", "link.log", "worker.cpp", "arm_spec.h"):
            shutil.copyfile(build / name, dest / name)
        for name in ("ADMISSION.json", "BINDING.json"):
            shutil.copyfile(admission / name, dest / name)
        shutil.copyfile(admission / "native/result.json", dest / "RESOURCE_NATIVE.json")
    s.need(not s.identity_errors(binding, plan, s.DESIGN, models), "execution binding invalid")
    dates = binding["calendar_dates"]
    s.need(len(set(dates)) == 3 and dates == sorted(dates) and all(datetime.fromisoformat(d).date().isoformat() == d for d in dates), "invalid local calendar dates")
    source_path = "benchmarks/rtx_jsa_closeout_v1/revision_a/results/RAW_FILE_MANIFEST.jsonl"
    data = subprocess.check_output(["git", "show", s.PANEL_COMMIT + ":" + source_path], cwd=s.REPO)
    manifest_file = root / "provenance/PR144_RAW_FILE_MANIFEST.jsonl"
    manifest_file.write_bytes(data)
    inventory = {r["path"].replace("\\", "/"): r for r in s.lines(manifest_file)}
    refs = {"source_commit": s.PANEL_COMMIT, "source_manifest": pin(root, manifest_file), "endpoints": {}}
    history = Path(config["historical_root"]).resolve()
    for family in s.FAMILIES:
        for item in panel["families"][family]:
            relative = f"runs/E1/{family}/{item['source_index']:02d}_R/requests"
            candidates = []
            for path in sorted((history / relative).glob("*/RECORD.json")):
                raw = s.read(path)
                if raw["mode"] == "heavy":
                    candidates.append((path, raw))
            s.need(len(candidates) == 1, "historical heavy R is missing or ambiguous")
            path, raw = candidates[0]
            name = path.relative_to(history).as_posix()
            s.need(name in inventory and path.stat().st_size == inventory[name]["bytes"] and s.hash_file(path) == inventory[name]["sha256"], "historical R source hash differs")
            s.need(raw["family"] == family and raw["arm"] == "R" and raw["task_id"] == item["id"] and raw["stage"] == "E1", "historical R identity differs")
            original = raw["output"]
            endpoint = {k: original[k] for k in ("ids", "length", "terminal_id", "stop_reason")}
            endpoint["eog"] = original["eog_flags"]
            s.endpoint(endpoint, models["families"][family])
            dest = root / "references" / family / f"{item['source_index']:02d}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
            refs["endpoints"][item["reference_id"]] = {"source_commit": s.PANEL_COMMIT, "source_kind": "PR144_HISTORICAL_R",
                    "raw_payload": pin(root, dest), "source_inventory_path": name, "endpoint_key_path": ["output"], "endpoint": endpoint}
    s.save(root / "REFERENCES.json", refs)
    s.save(root / "EXECUTION_IDENTITY.json", binding)
    s.save(root / "LOCAL_PATHS.json", local)
    s.save(root / "ATTEMPTS.json", [])
    s.save_lines(root / "REQUESTS.jsonl", [])
    print("PREPARED_NOT_EXECUTION_ADMITTED: commit identity and sources, then bind FREEZE_COMMIT.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.config, args.out)
