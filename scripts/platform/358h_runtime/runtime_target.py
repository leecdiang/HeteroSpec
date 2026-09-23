#!/usr/bin/env python3
from __future__ import annotations

import ctypes as C
import ast
import hashlib
import sys
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LEGACY_DIR = ROOT / "scripts" / "platform" / "358h"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from runtime_legacy_target_v02 import (  # noqa: E402
    LlamaAPI,
    LlamaTarget as LegacyLlamaTarget,
    TARGET,
)
from runtime_types import PathIdentity  # noqa: E402

LEGACY_RUNNER = LEGACY_DIR / "phase3_heterogeneous_runner.py"
LEGACY_RUNNER_SHA256 = "1d11e42d008f981ee6a91ac7bfeb478f11c060d51e79b9e060fe04ece70153e8"
LEGACY_RUNNER_MAIN_BLOB = "ce0fe27a34e2c162962c7a2eef834a3b758596e7"
TARGET_EXTRACTION = HERE / "runtime_legacy_target_v02.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def assert_frozen_legacy_runner() -> None:
    raw = LEGACY_RUNNER.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    # The main Git blob ends in an extra CRLF after the final Python newline.
    # The closed runner's frozen SHA256 was taken from the otherwise identical
    # 16003-byte Windows file without that terminal CRLF.  Require BOTH the
    # exact main Git blob and the exact historical SHA after removing only
    # those two bytes; this does not permit any executable source difference.
    canonical_main_copy = (
        raw.endswith(b"\n\r\n")
        and hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        == LEGACY_RUNNER_MAIN_BLOB
        and hashlib.sha256(raw[:-2]).hexdigest() == LEGACY_RUNNER_SHA256
    )
    if actual != LEGACY_RUNNER_SHA256 and not canonical_main_copy:
        raise RuntimeError(
            f"closed Phase-3 runner changed: {actual} != {LEGACY_RUNNER_SHA256}; "
            "do not silently inherit modified target semantics"
        )
    names = {"Batch", "ModelParams", "ContextParams", "LlamaAPI", "LlamaTarget"}
    def classes(path: Path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        return {n.name: ast.dump(n, include_attributes=False) for n in tree.body
                if isinstance(n, ast.ClassDef) and n.name in names}
    if classes(LEGACY_RUNNER) != classes(TARGET_EXTRACTION):
        raise RuntimeError("target-only extraction differs from frozen Phase-3 C API classes")


class RuntimeTargetModel:
    """One pinned target model shared by independent UB1/UB2 contexts."""

    def __init__(
        self,
        api: LlamaAPI,
        *,
        model_path: Path = TARGET,
        device: str = "Vulkan0",
    ):
        assert_frozen_legacy_runner()
        self.api = api
        self.model_path = model_path
        self.device = device
        dev = api.gg.ggml_backend_dev_by_name(device.encode())
        if not dev:
            raise RuntimeError(f"llama.cpp device unavailable: {device}")
        self._devices = (C.c_void_p * 2)(dev, None)
        mp = api.ll.llama_model_default_params()
        mp.devices = C.cast(self._devices, C.POINTER(C.c_void_p))
        mp.n_gpu_layers = -1
        mp.main_gpu = 0
        self.model = api.ll.llama_model_load_from_file(str(model_path).encode(), mp)
        if not self.model:
            raise RuntimeError("llama model load failed")
        self.vocab = api.ll.llama_model_get_vocab(self.model)
        self.n_vocab = api.ll.llama_vocab_n_tokens(self.vocab)


class RuntimeLlamaTarget(LegacyLlamaTarget):
    """Closed Phase-3 target semantics with prospective `n_ubatch` only."""

    def __init__(
        self,
        api: LlamaAPI,
        *,
        ubatch: int,
        model_path: Path = TARGET,
        device: str = "Vulkan0",
        n_ctx: int = 4096,
        shared_model: RuntimeTargetModel | None = None,
    ):
        assert_frozen_legacy_runner()
        if ubatch not in (1, 2):
            raise ValueError("prospective target study permits only n_ubatch=1 or 2")
        host = shared_model or RuntimeTargetModel(api, model_path=model_path, device=device)
        if host.api is not api:
            raise ValueError("shared target model belongs to a different LlamaAPI instance")
        if host.device != device:
            raise ValueError(f"shared target device mismatch: {host.device} != {device}")

        self.a = api
        self._host = host
        self._devices = host._devices
        self.model = host.model
        self.vocab = host.vocab
        self.n_vocab = host.n_vocab

        cp = api.ll.llama_context_default_params()
        cp.n_ctx = n_ctx
        cp.n_batch = n_ctx
        cp.n_ubatch = ubatch
        cp.n_seq_max = 1
        cp.n_outputs_max = n_ctx
        cp.n_outputs_max_per_seq = n_ctx
        cp.no_perf = False
        self.ctx = api.ll.llama_init_from_model(self.model, cp)
        if not self.ctx:
            raise RuntimeError(f"llama context init failed for n_ubatch={ubatch}")

        self.mem = api.ll.llama_get_memory(self.ctx)
        self.history: list[int] = []
        self._logits = None
        self.ubatch = ubatch
        self.requested_device = device
        self.identity = PathIdentity(
            name=f"TARGET_UB{ubatch}",
            target_ubatch=ubatch,
            draft_device=None,
            draft_frontend=None,
            state_policy=None,
        )

    def state_position(self) -> int | None:
        if not self.history:
            return None
        return int(self.a.ll.llama_memory_seq_pos_max(self.mem, 0))

    def binding_record(self) -> dict:
        return {
            "requested_target_device": self.requested_device,
            "target_n_ubatch": self.ubatch,
            "expected_target_placement": "37/37 model layers and 36/36 KV layers on Vulkan0; session stderr remains authoritative",
            "legacy_semantics_runner_sha256": LEGACY_RUNNER_SHA256,
            "shared_target_model": True,
        }


class RuntimeTargetPool:
    """Load target weights once and lazily create only requested UB1/UB2 contexts."""

    def __init__(
        self,
        api: LlamaAPI,
        *,
        ubatches: Iterable[int] = (1,),
        device: str = "Vulkan0",
        n_ctx: int = 4096,
    ):
        requested = tuple(sorted(set(int(x) for x in ubatches)))
        if any(x not in (1, 2) for x in requested):
            raise ValueError(f"unsupported target ubatches: {requested}")
        self.api = api
        self.device = device
        self.n_ctx = int(n_ctx)
        self.host = RuntimeTargetModel(api, device=device)
        self.targets: dict[int, RuntimeLlamaTarget] = {}
        for ubatch in requested:
            self._create(ubatch)

    def _create(self, ubatch: int) -> RuntimeLlamaTarget:
        key = int(ubatch)
        if key not in (1, 2):
            raise KeyError(f"unsupported target UB{key}")
        if key not in self.targets:
            self.targets[key] = RuntimeLlamaTarget(
                self.api,
                ubatch=key,
                device=self.device,
                n_ctx=self.n_ctx,
                shared_model=self.host,
            )
        return self.targets[key]

    def __getitem__(self, ubatch: int) -> RuntimeLlamaTarget:
        return self._create(int(ubatch))

    def binding_records(self) -> dict[str, dict]:
        return {f"UB{k}": v.binding_record() for k, v in sorted(self.targets.items())}


__all__ = [
    "LlamaAPI",
    "RuntimeLlamaTarget",
    "RuntimeTargetModel",
    "RuntimeTargetPool",
    "TARGET",
    "assert_frozen_legacy_runner",
]
