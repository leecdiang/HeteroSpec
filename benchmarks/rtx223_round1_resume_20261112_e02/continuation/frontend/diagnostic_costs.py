"""Partition capture-heavy host costs without admitting clean performance."""
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("round1_capture_cost_reader",ROOT/"request/costs.py")
reader=importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
# A private module instance: neither the original file nor another reader's
# allowed serving categories is changed by this capture diagnostic adapter.
reader.ALLOWED=reader.ALLOWED|{"state"}


def decompose_capture(timeline, *, request_id, arm, source_sha256, input_sha256):
    if timeline.get("state_capture_enabled") is not True:
        raise reader.CostError("this adapter is restricted to capture-heavy diagnostics")
    record={"request_id":request_id,"arm":arm,"source_sha256":source_sha256,
            "input_sha256":input_sha256,"clock":timeline["clock"],
            "service":timeline["service"],"spans":timeline["spans"],
            "complete_endpoint":False}
    result=reader.decompose(record)
    result["performance_admitted"]=False
    result["scope"]="CAPTURE_HEAVY_EXCLUSIVE_HOST_PARTITION_ONLY"
    result["native_qualification"]=False
    return result
