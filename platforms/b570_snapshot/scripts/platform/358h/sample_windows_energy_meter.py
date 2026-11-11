#!/usr/bin/env python3
"""Low-overhead Windows PDH sampler for hardware-backed Energy Meter counters."""
from __future__ import annotations

import argparse
import csv
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


PDH_FMT_DOUBLE = 0x00000200
ERROR_SUCCESS = 0
PDH_CSTATUS_INVALID_DATA = 0xC0000BC6


class ValueUnion(ctypes.Union):
    _fields_ = [("long_value", wintypes.LONG), ("double_value", ctypes.c_double), ("large_value", ctypes.c_longlong)]


class FormattedValue(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = [("status", wintypes.DWORD), ("value", ValueUnion)]


pdh = ctypes.WinDLL("pdh.dll")
pdh.PdhOpenQueryW.argtypes = [wintypes.LPCWSTR, ctypes.c_size_t, ctypes.POINTER(wintypes.HANDLE)]
pdh.PdhAddEnglishCounterW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, ctypes.c_size_t, ctypes.POINTER(wintypes.HANDLE)]
pdh.PdhCollectQueryData.argtypes = [wintypes.HANDLE]
pdh.PdhGetFormattedCounterValue.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(FormattedValue)]
pdh.PdhCloseQuery.argtypes = [wintypes.HANDLE]


def check(code: int, action: str) -> None:
    if code != ERROR_SUCCESS:
        raise OSError(f"{action} failed with PDH status 0x{code & 0xffffffff:08x}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--metadata-json", type=Path, required=True)
    parser.add_argument("--period-ms", type=int, default=1000)
    parser.add_argument("--duration-seconds", type=float, default=20.0)
    parser.add_argument("--affinity-cpus", default="", help="Optional comma-separated logical CPU list.")
    parser.add_argument("--stop-file", type=Path,
                        help="Optional graceful-stop sentinel; checked between qualified 1000-ms samples.")
    parser.add_argument("--formal-measurement", action="store_true",
                        help="Mark output formal. The calling frozen Track-E runner owns admissibility.")
    args = parser.parse_args()
    if args.period_ms < 1000:
        parser.error("Windows Energy Meter provider is qualified only at periods >=1000 ms")

    counters = {
        "package_power_mw": r"\Energy Meter(RAPL_Package0_PKG)\Power",
        "package_energy_raw": r"\Energy Meter(RAPL_Package0_PKG)\Energy",
    }
    query = wintypes.HANDLE()
    handles: dict[str, wintypes.HANDLE] = {}
    check(pdh.PdhOpenQueryW(None, 0, ctypes.byref(query)), "PdhOpenQueryW")
    try:
        for name, path in counters.items():
            handle = wintypes.HANDLE()
            check(pdh.PdhAddEnglishCounterW(query, path, 0, ctypes.byref(handle)), f"PdhAddEnglishCounterW({path})")
            handles[name] = handle
        rows = []
        deadline = time.perf_counter() + args.duration_seconds
        process = __import__("psutil").Process()
        requested_affinity = [int(value) for value in args.affinity_cpus.split(",") if value.strip()]
        if requested_affinity:
            process.cpu_affinity(requested_affinity)
        cpu_start = process.cpu_times()
        while time.perf_counter() < deadline:
            if args.stop_file and args.stop_file.exists():
                break
            before = time.perf_counter_ns()
            check(pdh.PdhCollectQueryData(query), "PdhCollectQueryData")
            after = time.perf_counter_ns()
            row = {
                "utc": datetime.now(timezone.utc).isoformat(),
                "qpc_midpoint_ns": (before + after) // 2,
                "collection_call_ns": after - before,
                "package_power_w": None,
            }
            for name, handle in handles.items():
                value = FormattedValue()
                counter_type = wintypes.DWORD()
                status = pdh.PdhGetFormattedCounterValue(handle, PDH_FMT_DOUBLE, ctypes.byref(counter_type), ctypes.byref(value))
                if (status & 0xffffffff) not in (ERROR_SUCCESS, PDH_CSTATUS_INVALID_DATA):
                    check(status, f"PdhGetFormattedCounterValue({name})")
                row[name] = value.double_value if status == ERROR_SUCCESS and value.status == 0 else None
                row[name + "_cstatus"] = int(status & 0xffffffff)
                row[name + "_type"] = int(counter_type.value)
            if row["package_power_mw"] is not None:
                row["package_power_w"] = row["package_power_mw"] / 1000.0
            rows.append(row)
            remaining = args.period_ms / 1000.0 - (after - before) / 1e9
            if remaining > 0:
                time.sleep(remaining)
        cpu_end = process.cpu_times()
    finally:
        pdh.PdhCloseQuery(query)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    valid = [row for row in rows if row.get("package_power_w") is not None and row["package_power_w"] >= 0]
    cpu_seconds = (cpu_end.user - cpu_start.user) + (cpu_end.system - cpu_start.system)
    elapsed_seconds = max(0.0, time.perf_counter() - (deadline - args.duration_seconds))
    payload = {
        "schema": "heterospec.358h.windows_energy_meter.v1",
        "formal_measurement": args.formal_measurement,
        "invalid_for_claims": not args.formal_measurement,
        "source": "Windows PDH Energy Meter provider backed by RAPL_Package0_PKG",
        "physical_boundary": "CPU package; not wall/system energy and not an isolated NPU domain",
        "counter_paths": counters,
        "sampling_mechanism": "PdhCollectQueryData + PdhGetFormattedCounterValue",
        "period_ms": args.period_ms,
        "timestamp_domain": "host perf_counter/QPC nanoseconds; midpoint around each PDH collection call",
        "rows": len(rows),
        "valid_power_rows": len(valid),
        "collector_process_cpu_seconds": cpu_seconds,
        "collector_cpu_fraction_of_wall": cpu_seconds / elapsed_seconds if elapsed_seconds else None,
        "elapsed_seconds": elapsed_seconds,
        "stop_file": str(args.stop_file.resolve()) if args.stop_file else None,
        "requested_affinity_cpus": requested_affinity or None,
        "effective_affinity_cpus": process.cpu_affinity(),
        "max_collection_call_ms": max(row["collection_call_ns"] for row in rows) / 1e6,
        "power_scale": "provider Power is milliwatts; divide by 1000 for watts",
        "energy_counter_policy": "recorded for investigation only; no joule claim until provider scale/semantics are independently qualified",
        "csv": {"path": str(args.output_csv.resolve()), "sha256": sha256(args.output_csv)},
    }
    args.metadata_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if len(valid) >= 2 else 2


if __name__ == "__main__":
    raise SystemExit(main())

