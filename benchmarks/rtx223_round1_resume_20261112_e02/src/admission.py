"""Fail-closed host admission and offline evidence checks for RTX round 1.

These checks do not certify a native binary. Native qualification and clean
dispatch guards must be executed and bound separately.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from typing import Any, Callable


class AdmissionError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise AdmissionError(code, message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def integer(value: Any, name: str, minimum: int = 0, maximum: int = 2**31 - 1) -> int:
    require(type(value) is int and minimum <= value <= maximum, "INTEGER", name)
    return value


def sha256_text(value: Any, name: str) -> str:
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            "IDENTITY", name)
    return value


def fields(mapping: Any, names: tuple[str, ...], label: str) -> dict:
    require(isinstance(mapping, dict), "SCHEMA", label)
    require(all(name in mapping for name in names), "MISSING_FIELD", label + ": " + ",".join(names))
    return mapping


def read_artifact(root: Path | str, record: dict) -> bytes:
    fields(record, ("path", "bytes", "sha256"), "artifact")
    root = Path(root).resolve(strict=True)
    require(isinstance(record["path"], str) and bool(record["path"]), "PATH", "artifact path")
    relative = Path(record["path"])
    require(not relative.is_absolute() and relative.drive == "" and ".." not in relative.parts,
            "PATH", "artifact path must remain under evidence root")
    path = (root / relative).resolve(strict=True)
    require(path.is_relative_to(root) and path.is_file(), "PATH", "artifact leaves evidence root")
    expected_bytes = integer(record["bytes"], "artifact bytes", maximum=2**63 - 1)
    expected_sha = sha256_text(record["sha256"], "artifact hash")
    raw = path.read_bytes()
    require(len(raw) == expected_bytes, "TRUNCATED_OR_EXTENDED", str(relative))
    require(digest(raw) == expected_sha, "HASH", str(relative))
    return raw


def validate_full_vector(raw: bytes, vocab_size: int) -> dict:
    integer(vocab_size, "vocab size", minimum=1)
    require(len(raw) == vocab_size * 4, "FULL_VECTOR", "one complete little-endian F32 vocabulary vector required")
    best_value = -math.inf
    best_token = 0
    for token, (value,) in enumerate(struct.iter_unpack("<f", raw)):
        require(math.isfinite(value), "NONFINITE", f"logit {token}")
        if value > best_value:
            best_value, best_token = value, token
    return {"sha256": digest(raw), "bytes": len(raw), "vocab_size": vocab_size, "greedy": best_token}


def compare_operator_pair(quantized_a: bytes, quantized_b: bytes, output_a: bytes, output_b: bytes,
                          expected_quantized_bytes: int, expected_output_elements: int) -> dict:
    """Compare complete A/B/C buffers using sizes from the frozen real descriptor."""
    integer(expected_quantized_bytes, "frozen quantized activation bytes", minimum=1)
    integer(expected_output_elements, "frozen output elements", minimum=1)
    require(len(quantized_a) == expected_quantized_bytes and len(quantized_b) == expected_quantized_bytes,
            "ACTIVATION_SIZE", "all quantized rows and padding bytes required")
    require(quantized_a == quantized_b, "ACTIVATION_MISMATCH", "complete quantized activation bytes differ")
    a = validate_full_vector(output_a, expected_output_elements)
    b = validate_full_vector(output_b, expected_output_elements)
    require(output_a == output_b, "OUTPUT_MISMATCH", "all projection output elements must be bitwise equal")
    return {"relation": "BITWISE_EQUAL", "quantized_sha256": digest(quantized_a),
            "output_sha256": a["sha256"], "output_elements": expected_output_elements,
            "quantized_bytes": expected_quantized_bytes}


@dataclass(frozen=True)
class NativeStateSpec:
    layers: int
    key_elements: int
    value_elements: int
    capacity: int
    ggml_type: int = 1
    element_bytes: int = 2


def read_native_state(raw: bytes, expected_positions: int, spec: NativeStateSpec) -> dict:
    """Read the pinned dense-sequence export, rejecting untrimmed/trailing data."""
    integer(expected_positions, "active positions", minimum=1, maximum=spec.capacity)
    for name in ("layers", "key_elements", "value_elements", "capacity", "element_bytes"):
        integer(getattr(spec, name), name, minimum=1)
    require(spec.ggml_type == 1 and spec.element_bytes == 2,
            "STATE_RECIPE", "this parser qualifies F16 K/V only")
    offset = 0

    def scalar(fmt: str) -> int:
        nonlocal offset
        size = struct.calcsize("<" + fmt)
        require(size <= len(raw) - offset, "TRUNCATED_STATE", "state scalar")
        value = struct.unpack_from("<" + fmt, raw, offset)[0]
        offset += size
        return value

    def payload(size: int) -> bytes:
        nonlocal offset
        require(0 <= size <= len(raw) - offset, "TRUNCATED_STATE", "state tensor")
        data = raw[offset:offset + size]
        offset += size
        return data

    require(scalar("I") == 0xAF143CD8 and scalar("i") == 0, "STATE_HEADER", "magic and version")
    require(scalar("I") == 1, "STATE_STREAMS", "one sequence stream required")
    n = scalar("I")
    require(n == expected_positions, "UNTRIMMED_STATE", "exported position count differs from active frontier")
    for pos in range(n):
        require((scalar("i"), scalar("I"), scalar("i")) == (pos, 1, 0),
                "STATE_MAPPING", "dense sequence-0 mapping required")
    transposed = scalar("I")
    require(transposed in (0, 1), "STATE_LAYOUT", "unsupported V orientation")
    require(scalar("I") == spec.layers, "STATE_LAYERS", "layer count")
    active = hashlib.sha256()
    active.update(struct.pack("<IIII", n, spec.layers, spec.key_elements, spec.value_elements))
    for _ in range(spec.layers):
        require(scalar("i") == spec.ggml_type, "STATE_DTYPE", "K dtype")
        require(scalar("Q") == spec.key_elements * spec.element_bytes, "STATE_WIDTH", "K row width")
        active.update(payload(n * spec.key_elements * spec.element_bytes))
    for _ in range(spec.layers):
        require(scalar("i") == spec.ggml_type, "STATE_DTYPE", "V dtype")
        if transposed:
            require((scalar("I"), scalar("I")) == (spec.element_bytes, spec.value_elements),
                    "STATE_WIDTH", "transposed V dimensions")
            data = payload(n * spec.value_elements * spec.element_bytes)
            for pos in range(n):
                for element in range(spec.value_elements):
                    index = (element * n + pos) * spec.element_bytes
                    active.update(data[index:index + spec.element_bytes])
        else:
            require(scalar("Q") == spec.value_elements * spec.element_bytes, "STATE_WIDTH", "V row width")
            active.update(payload(n * spec.value_elements * spec.element_bytes))
    require(offset == len(raw), "TRAILING_STATE", "unregistered or untrimmed trailing bytes")
    return {"raw_sha256": digest(raw), "active_sha256": active.hexdigest(), "positions": n,
            "active_bytes": n * spec.layers * (spec.key_elements + spec.value_elements) * spec.element_bytes,
            "transposed_V": bool(transposed)}


def validate_identity(actual: dict, frozen: dict) -> None:
    names = ("model_sha256", "vocab_sha256", "core_sha256", "frontend_sha256", "exe_sha256",
             "compiler", "loaded_modules", "producer", "kv", "graph_policy", "device_uuid", "compute_capability")
    fields(actual, names, "actual deployment identity")
    fields(frozen, names, "frozen deployment identity")
    for name in names[:5]:
        sha256_text(actual[name], name)
        sha256_text(frozen[name], "frozen " + name)
    for which in (actual, frozen):
        require(isinstance(which["loaded_modules"], dict) and bool(which["loaded_modules"]),
                "IDENTITY", "loaded module inventory required")
        for module, h in which["loaded_modules"].items():
            require(isinstance(module, str) and bool(module), "IDENTITY", "loaded module name")
            sha256_text(h, "loaded module hash")
        require(all(which[name] for name in names[5:]), "IDENTITY", "empty identity field")
    require(actual == frozen, "IDENTITY_MISMATCH", "actual deployment differs from frozen exact-contract identity")


def validate_geometry(geometry: dict, expected: dict) -> None:
    names = ("capacity", "physical_head", "physical_used", "active_positions", "padding",
             "prefix_vector", "layout_policy", "sequence_ids")
    fields(geometry, names, "native geometry")
    fields(expected, names, "expected geometry")
    for key in ("capacity", "physical_head", "physical_used", "active_positions", "padding"):
        integer(geometry[key], key, minimum=1 if key in ("capacity", "padding") else 0)
    require(geometry["physical_head"] <= geometry["capacity"] and
            geometry["physical_used"] <= geometry["capacity"] and
            geometry["active_positions"] <= geometry["capacity"], "GEOMETRY", "capacity bounds")
    require(isinstance(geometry["prefix_vector"], list) and bool(geometry["prefix_vector"]),
            "GEOMETRY", "complete physical prefix vector required")
    for prefix in geometry["prefix_vector"]:
        integer(prefix, "physical prefix", minimum=1, maximum=geometry["capacity"])
    require(geometry["sequence_ids"] == [0], "GEOMETRY", "dense single sequence required")
    require(geometry == expected, "GEOMETRY_MISMATCH", "geometry differs from frozen expected case")


def validate_graph_reuse(previous: dict, current: dict, reused: bool) -> str:
    names = ("prefix_vector", "active_policy", "layout_policy", "head_placement_key", "n_outputs",
             "ubatch_topology", "recipe_identity")
    fields(previous, names, "previous graph key")
    fields(current, names, "current graph key")
    require(type(reused) is bool, "GRAPH", "reuse verdict required")
    same = all(previous[name] == current[name] for name in names)
    require(not reused or same, "GRAPH_REUSE", "changed semantic graph key must rebuild")
    return "REUSED" if reused else "REBUILT"


def _tensor(tensor: dict, role: str, dtype: str, device: str) -> tuple[list[int], list[int]]:
    names = ("dtype", "ne", "nb", "contiguous", "buffer_backend", "buffer_device", "buffer_usage",
             "view", "padding_clear_conflict", "allocation_bytes", "data_offset")
    fields(tensor, names, role)
    require(tensor["dtype"] == dtype, "DTYPE", role)
    require(isinstance(tensor["ne"], list) and len(tensor["ne"]) == 4 and
            isinstance(tensor["nb"], list) and len(tensor["nb"]) == 4, "SHAPE", role)
    ne = [integer(x, role + " shape", minimum=1) for x in tensor["ne"]]
    nb = [integer(x, role + " stride", minimum=1) for x in tensor["nb"]]
    require(tensor["contiguous"] is True, "STRIDE", role + " must be contiguous")
    require(tensor["buffer_backend"] == "CUDA" and tensor["buffer_device"] == device,
            "PLACEMENT", role + " actual buffer device")
    require(tensor["buffer_usage"] in ("WEIGHTS", "COMPUTE"), "BUFFER", role + " buffer usage")
    require(type(tensor["view"]) is bool and tensor["padding_clear_conflict"] is False,
            "PADDING", role + " unsafe padded compute view")
    block = 32 if dtype == "Q8_0" else 1
    unit = 34 if dtype == "Q8_0" else 4
    require(ne[0] % block == 0, "SHAPE", role + " block alignment")
    expected = [unit, (ne[0] // block) * unit]
    expected += [expected[1] * ne[1], expected[1] * ne[1] * ne[2]]
    require(nb == expected, "STRIDE", role + " exact contiguous byte strides")
    start = integer(tensor["data_offset"], role + " data offset")
    allocation = integer(tensor["allocation_bytes"], role + " allocation bytes", minimum=1, maximum=2**63-1)
    span = nb[3] * ne[3]
    require(start + span <= allocation, "BUFFER_SPAN", role + " data outside allocation")
    require(start + span <= 2**31 - 1 and all(x <= 2**31 - 1 for x in nb),
            "INTEGER_SPAN", role + " MMVQ offsets exceed int32 recipe")
    return ne, nb


def admit_descriptor(arm: str, descriptor: dict, bound_device_uuid: str) -> dict:
    """Admit metadata to the *prospective* strict recipe, never to old packed guards."""
    require(arm in ("A", "B", "C"), "ARM", "A=backend-loop4, B=current packed, C=pair4")
    names = ("q", "g", "device_uuid", "backend", "warp_size", "compute_capability", "weight", "activation",
             "output", "op", "precision", "ids", "fusion", "output_mask", "reserve", "dispatch", "quantizer")
    fields(descriptor, names, "projection descriptor")
    q = integer(descriptor["q"], "q", minimum=1, maximum=32)
    require(descriptor["backend"] == "CUDA" and descriptor["warp_size"] == 32,
            "BACKEND", "NVIDIA CUDA warp32 required")
    require(isinstance(descriptor["device_uuid"], str) and descriptor["device_uuid"].startswith("GPU-"),
            "PLACEMENT", "actual authorized UUID required")
    require(isinstance(bound_device_uuid, str) and bound_device_uuid.startswith("GPU-") and
            descriptor["device_uuid"] == bound_device_uuid,
            "PLACEMENT", "actual device must equal independently frozen authorized UUID")
    require(descriptor["compute_capability"] == "12.0", "BACKEND", "round-1 bound SM120 only")
    require(descriptor["op"] == "MUL_MAT" and descriptor["precision"] == "DEFAULT" and
            descriptor["ids"] is False and descriptor["fusion"] is False,
            "ARITHMETIC_RECIPE", "unfused no-IDs default-precision projection required")
    wn, _ = _tensor(descriptor["weight"], "weight", "Q8_0", descriptor["device_uuid"])
    an, _ = _tensor(descriptor["activation"], "activation", "F32", descriptor["device_uuid"])
    on, _ = _tensor(descriptor["output"], "output", "F32", descriptor["device_uuid"])
    require(wn[2:] == [1, 1] and an == [wn[0], q, 1, 1] and on == [wn[1], q, 1, 1],
            "SHAPE", "logical projection dimensions")
    groups = q // 4
    require(descriptor["g"] == groups, "SHAPE", "independent group count")
    require(arm != "C" or (q == 8 and groups == 2), "C_DOMAIN", "pair4 starts at q=8,g=2 only")
    mask = descriptor["output_mask"]
    require(isinstance(mask, list) and len(mask) == q and all(type(x) is bool for x in mask),
            "OUTPUT_MASK", "one explicit flag per logical row required")
    require(mask == [True] * q or mask == [False] * (q-1) + [True],
            "OUTPUT_MASK", "only all or last masks are in this recipe")
    require(integer(descriptor["reserve"], "reserve", minimum=1) >= sum(mask),
            "OUTPUT_RESERVE", "insufficient requested output reserve")
    require(descriptor["quantizer"] == {"type": "Q8_1", "wide_once": True, "arithmetic_columns": 4},
            "QUANTIZER", "one common unchanged wide Q8_1 quantizer required")
    if arm == "A" or (arm == "B" and q < 8):
        expected_dispatch = [{"route": "MMVQ_Q8_0", "ncols": min(4, q-start), "channels": 1,
                              "samples": 1, "logical_start": start} for start in range(0, q, 4)]
    elif arm == "B":
        expected_dispatch = [{"route": "MMVQ_Q8_0", "ncols": 4, "channels": groups,
                              "samples": 1, "logical_start": 0}]
        if q % 4:
            expected_dispatch.append({"route": "MMVQ_Q8_0", "ncols": q % 4, "channels": 1,
                                      "samples": 1, "logical_start": groups * 4})
    else:
        expected_dispatch = [{"route": "MMVQ_Q8_0_PAIR4", "ncols": 4, "channels": 2,
                              "samples": 1, "logical_start": 0}]
    require(descriptor["dispatch"] == expected_dispatch, "DISPATCH", "actual dispatch differs from admitted route")
    return {"decision": "ADMITTED_METADATA_ONLY", "arm": arm, "q": q, "g": groups,
            "native_qualified": False, "dispatch": expected_dispatch}


def qualified_fallback(primary_error: AdmissionError, fallback_id: str, fallback_receipt: dict,
                       frozen_identity: dict, descriptor: dict, qualification_allowlist: dict) -> dict:
    fields(fallback_receipt, ("id", "status", "identity", "descriptor", "evidence_sha256"), "fallback receipt")
    require(fallback_receipt["id"] == fallback_id and fallback_receipt["status"] == "NATIVE_QUALIFIED",
            "FALLBACK_UNQUALIFIED", "named native qualification is required")
    receipt_sha = digest(json.dumps(fallback_receipt, sort_keys=True, separators=(",", ":")).encode())
    require(qualification_allowlist.get(fallback_id) == receipt_sha,
            "FALLBACK_UNQUALIFIED", "receipt must belong to the separately frozen qualification allowlist")
    validate_identity(fallback_receipt["identity"], frozen_identity)
    sha256_text(fallback_receipt["evidence_sha256"], "fallback qualification evidence")
    require(fallback_receipt["descriptor"] == descriptor, "FALLBACK_UNQUALIFIED", "descriptor not qualified")
    return {"decision": "QUALIFIED_FALLBACK", "id": fallback_id, "primary_rejection": primary_error.code}


@dataclass
class Owner:
    identity: str
    valid: bool = True
    executed: bool = False

    def call(self, action: Callable[[], Any], *, native_work: bool = False) -> Any:
        require(self.valid, "OWNER_INVALID", "owner cannot execute, reset, trim or continue")
        if native_work:
            self.executed = True
        try:
            return action()
        except BaseException:
            if self.executed:
                self.valid = False
            raise

    def invalidate(self) -> None:
        self.valid = False


def validate_clean_binding(receipt: dict, frozen_identity: dict, expected_descriptor: dict) -> None:
    fields(receipt, ("mode", "identity", "descriptor", "always_on_guard", "capture_observation"), "clean receipt")
    require(receipt["mode"] == "clean", "CLEAN_BINDING", "clean receipt required")
    validate_identity(receipt["identity"], frozen_identity)
    require(receipt["descriptor"] == expected_descriptor, "CLEAN_BINDING", "qualified descriptor changed")
    guard = fields(receipt["always_on_guard"], ("executed", "predicate_sha256", "verdict"), "always-on guard")
    require(guard["executed"] is True and guard["verdict"] == "PASS", "CLEAN_GUARD", "capture observer cannot replace clean guard")
    sha256_text(guard["predicate_sha256"], "clean predicate source")
    require(guard["predicate_sha256"] == frozen_identity.get("clean_guard_sha256"),
            "CLEAN_GUARD", "always-on predicate source is not frozen")
    require(receipt["capture_observation"] is False, "CLEAN_BINDING", "capture must be disabled for clean timing")


def validate_bundle(root: Path | str, receipt: dict, frozen_identity: dict, state_spec: NativeStateSpec,
                    expected_geometries: dict[str, dict], expected_requested_rows: list[int],
                    expected_vocab_size: int) -> dict:
    fields(receipt, ("schema", "identity", "vocab_size", "requested_rows", "vectors", "states", "geometries"), "evidence bundle")
    require(receipt["schema"] == "heterospec.rtx-round1.evidence.v1", "SCHEMA", "evidence version")
    validate_identity(receipt["identity"], frozen_identity)
    integer(expected_vocab_size, "independently frozen vocab size", minimum=1)
    require(receipt["vocab_size"] == expected_vocab_size, "FULL_VECTOR", "vocabulary size differs from independent frozen model contract")
    rows = receipt["requested_rows"]
    require(isinstance(rows, list) and bool(rows), "FULL_VECTOR", "requested rows required")
    for row in rows:
        integer(row, "requested row")
    require(len(rows) == len(set(rows)) and rows == expected_requested_rows,
            "FULL_VECTOR", "all and only independently frozen requested rows required")
    require(isinstance(receipt["vectors"], list) and len(receipt["vectors"]) == len(rows), "FULL_VECTOR", "all requested rows required")
    vectors = {}
    for item in receipt["vectors"]:
        fields(item, ("row", "owner", "artifact"), "vector record")
        require(item["row"] in rows and item["row"] not in vectors, "FULL_VECTOR", "unexpected or duplicated row")
        require(item["owner"] == "OWNED_COPY", "OUTPUT_OWNER", "borrowed output pointers cannot survive group reuse")
        vectors[item["row"]] = validate_full_vector(read_artifact(root, item["artifact"]), receipt["vocab_size"])
    state_names = ("target_untrimmed", "draft_untrimmed", "target", "draft")
    fields(receipt["states"], state_names, "complete untrimmed and committed target/draft state")
    require(set(receipt["geometries"]) == set(expected_geometries), "GEOMETRY", "complete stage geometries required")
    for stage in expected_geometries:
        validate_geometry(receipt["geometries"][stage], expected_geometries[stage])
    states = {}
    for owner in state_names:
        item = fields(receipt["states"][owner], ("expected_positions", "artifact", "geometry_stage", "complete_native_sequence", "capture_point"), owner + " state")
        require(item["complete_native_sequence"] is True, "INCOMPLETE_STATE", "complete sequence export required")
        expected_point = {"target_untrimmed": "POST_VERIFY_PRE_TRIM", "draft_untrimmed": "POST_DRAFT_PRE_TRIM",
                          "target": "POST_COMMIT_POST_TRIM", "draft": "POST_COMMIT_POST_TRIM"}[owner]
        require(item["capture_point"] == expected_point, "INCOMPLETE_STATE", "state capture point differs from obligation")
        require(item["geometry_stage"] in expected_geometries, "GEOMETRY", owner + " state geometry stage")
        require(item["expected_positions"] == expected_geometries[item["geometry_stage"]]["active_positions"],
                "UNTRIMMED_STATE", owner + " state count differs from expected active geometry")
        owner_spec = state_spec[owner.split("_")[0]] if isinstance(state_spec, dict) else state_spec
        states[owner] = read_native_state(read_artifact(root, item["artifact"]), item["expected_positions"], owner_spec)
    return {"status": "OFFLINE_EVIDENCE_VALID", "vectors": vectors, "states": states,
            "native_qualification": "NOT_INFERRED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--descriptor", type=Path)
    parser.add_argument("--arm", choices=("A", "B", "C"))
    parser.add_argument("--device-uuid", required=True, help="independently frozen authorized physical GPU UUID")
    args = parser.parse_args()
    require(args.descriptor is not None and args.arm is not None, "ARGUMENTS", "--descriptor and --arm required")
    print(json.dumps(admit_descriptor(args.arm, json.loads(args.descriptor.read_bytes()), args.device_uuid), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
