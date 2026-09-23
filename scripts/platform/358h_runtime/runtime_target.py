#!/usr/bin/env python3
from __future__ import annotations

import ctypes as C
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LEGACY_DIR = ROOT / "scripts" / "platform" / "358h"
if str(LEGACY_DIR) not in sys.path:
    sys.path.insert(0, str(LEGACY_DIR))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from phase3_heterogeneous_runner import (  # noqa: E402
    LlamaAPI,
    LlamaTarget as LegacyLlamaTarget,
    TARGET,
)
from runtime_types import PathIdentity  # noqa: E402

LEGACY_RUNNER = LEGACY_DIR / "phase3_heterogeneous_runner.py"
LEGACY_RUNNER_SHA256 = "1d11e42d008f981ee6a91ac7bfeb478f11c060d51e79b9e060fe04ece70153e8"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def assert_frozen_legacy_runner() -> None:
    actual = sha256(LEGACY_RUNNER)
    if actual != LEGACY_RUNNER_SHA256:
        raise RuntimeError(
            f"closed Phase-3 runner changed: {actual} != {LEGACY_RUNNER_SHA256}; "
            "do not silently inherit modified target semantics"
        )


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
    """Closed Phase-3 target semantics with prospective `n_ubatch` only.

    Tokenization, verification, ordered acceptance, rollback, correction, bonus
    and baseline methods are inherited from the frozen Phase-3 implementation.
    Multiple instances may share one RuntimeTargetModel while keeping completely
    separate llama contexts/KV state.
    """

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
            raise RuntimeError("llama context init failed")

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
    """Load Qwen3-8B once and expose independent UB1/UB2 contexts."""

    def __init__(self, api: LlamaAPI, *, device: str = "Vulkan0", n_ctx: int = 4096):
        self.api = api
        self.host = RuntimeTargetModel(api, device=device)
        self.targets = {
            1: RuntimeLlamaTarget(api, ubatch=1, device=device, n_ctx=n_ctx, shared_model=self.host),
            2: RuntimeLlamaTarget(api, ubatch=2, device=device, n_ctx=n_ctx, shared_model=self.host),
        }

    def __getitem__(self, ubatch: int) -> RuntimeLlamaTarget:
        return self.targets[int(ubatch)]


__all__ = [
    "LlamaAPI",
    "RuntimeLlamaTarget",
    "RuntimeTargetModel",
    "RuntimeTargetPool",
    "TARGET",
    "assert_frozen_legacy_runner",
]
