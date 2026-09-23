#!/usr/bin/env python3
"""Backend-neutral process session shared by R0, R1 and R2."""
from __future__ import annotations

import hashlib
import json
import multiprocessing as mp
import os
import shutil
from pathlib import Path

from runtime_factory import parse_path
from runtime_process_v02 import RPCClient
from runtime_workers_v02 import draft_worker_entry, target_worker_entry

ROOT = Path(__file__).resolve().parents[3]
LEGACY_BINDING = Path.home() / "Documents/ChatGPT/HeteroSpec/runs/358h/qualification_ac_20260918/npu_cache_binding_ctx8192.json"


def prepare_legacy_npu_cache(output_dir: Path) -> dict:
    """Copy the frozen compiled blob into this run; never write the old cache."""
    binding = json.loads(LEGACY_BINDING.read_text(encoding="utf-8-sig"))
    blob = Path(binding["cache_blob"]["path"])
    digest = hashlib.sha256(blob.read_bytes()).hexdigest()
    if digest != binding["cache_blob"]["sha256"]:
        raise RuntimeError("legacy NPU cache blob differs from frozen binding")
    cache = output_dir / "npu_cache_copy"
    cache.mkdir(exist_ok=False)
    shutil.copy2(blob, cache / blob.name)
    os.environ["HETEROSPEC_RUNTIME_CACHE_DIR"] = str(cache.resolve())
    os.environ["HETEROSPEC_FROZEN_NPU_BINDING"] = str(LEGACY_BINDING.resolve())
    return {"binding": str(LEGACY_BINDING), "blob_sha256": digest, "copy": str(cache / blob.name)}


def draft_groups(paths: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for path in paths:
        spec = parse_path(path)
        if spec["kind"] == "TARGET":
            continue
        kind = "legacy" if spec["kind"] == "LEGACY" else "optimum"
        group = f"{kind}_{spec['device'].lower()}"
        groups.setdefault(group, []).append(path)
    return groups


class RuntimeProcessSession:
    def __init__(self, mask: list[int], groups: tuple[str, ...] = ("default",)):
        if not mask or len(groups) != len(set(groups)):
            raise ValueError("nonempty affinity and unique draft groups required")
        ctx = mp.get_context("spawn")
        driver_end, target_driver_end = ctx.Pipe(duplex=True)
        target_draft_ends = {}
        draft_ends = {}
        self.drafts = {}
        for group in groups:
            target_draft_ends[group], draft_ends[group] = ctx.Pipe(duplex=True)
            self.drafts[group] = ctx.Process(target=draft_worker_entry,
                args=(draft_ends[group], mask), name=f"HeteroSpecDraft-{group}")
        self.target = ctx.Process(target=target_worker_entry,
            args=(target_driver_end, target_draft_ends, mask), name="HeteroSpecTarget")
        for proc in self.drafts.values():
            proc.start()
        self.target.start()
        target_driver_end.close()
        for conn in target_draft_ends.values():
            conn.close()
        for conn in draft_ends.values():
            conn.close()
        self.draft = next(iter(self.drafts.values())) if len(self.drafts) == 1 else None
        self.client = RPCClient(driver_end, "target", self.target)
        self.start_method = ctx.get_start_method()

    def call(self, op: str, *, observation_id: str = "session", **kwargs):
        return self.client.call(op, observation_id=observation_id, **kwargs)[0]

    def initialize(self, paths: list[str]) -> dict:
        self.call("PING")
        groups = draft_groups(paths)
        if set(groups) != set(self.drafts):
            raise RuntimeError(f"draft groups mismatch: {set(groups)} != {set(self.drafts)}")
        draft_init = {group: self.call("DRAFT_INIT", payload={"group": group, "paths": names})
                      for group, names in groups.items()}
        target_init = self.call("INIT")
        info = self.call("INFO")
        return {"draft_init": draft_init, "target_init": target_init, "process_info": info}

    def run(self, path: str, formatted_prompt: str, output_cap: int, observation_id: str) -> dict:
        payload = {"path": path, "formatted_prompt": formatted_prompt, "output_cap": output_cap}
        response, harness = self.client.call("RUN", observation_id=observation_id, path_id=path,
                                             payload=payload)
        return {**response, "harness_roundtrip_ns": harness["realized_ns"],
                "target_worker_pid": self.target.pid}

    def reset(self) -> bool:
        return bool(self.call("RESET")["reset"])

    def info(self) -> dict:
        return self.call("INFO")

    def close(self) -> dict:
        status = {"shutdown_rpc": False, "target_exitcode": None, "draft_exitcodes": {}}
        try:
            status["shutdown_rpc"] = bool(self.call("SHUTDOWN").get("shutdown"))
        except Exception as exc:
            status["shutdown_error"] = repr(exc)
        for proc in (self.target, *self.drafts.values()):
            proc.join(timeout=10)
        status["target_exitcode"] = self.target.exitcode
        status["draft_exitcodes"] = {group: proc.exitcode for group, proc in self.drafts.items()}
        return status
