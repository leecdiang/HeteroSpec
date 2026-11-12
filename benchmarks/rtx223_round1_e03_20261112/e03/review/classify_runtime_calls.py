"""Clarify lexical API inventory; API counts are not physical-kernel counts."""
from pathlib import Path
from collections import Counter
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

GROUPS = {
    "query_error_and_read_attributes": {"cudaHostGetDevicePointer", "cudaGetLastError", "cudaStreamIsCapturing", "cudaFuncGetAttributes", "cudaOccupancyMaxActiveBlocksPerMultiprocessor", "cudaGetDevice", "cudaGetDeviceCount", "cudaGetErrorString", "cudaGetDeviceProperties", "cudaDeviceGetAttribute", "cudaDeviceCanAccessPeer", "cudaMemGetInfo", "cudaDeviceGetPCIBusId"},
    "event_stream_sync_and_lifecycle": {"cudaEventSynchronize", "cudaEventRecord", "cudaStreamWaitEvent", "cudaStreamCreateWithFlags", "cudaEventCreateWithFlags", "cudaStreamSynchronize", "cudaEventDestroy", "cudaStreamDestroy", "cudaDeviceSynchronize"},
    "device_configuration_and_attribute_changes": {"cudaFuncSetAttribute", "cudaSetDevice", "cudaMemAdvise", "cudaSetDeviceFlags", "cudaDeviceEnablePeerAccess"},
    "host_memory_allocation_and_pinning": {"cudaHostAlloc", "cudaFreeHost", "cudaMallocHost", "cudaHostRegister", "cudaHostUnregister"},
    "device_memory_allocation_and_free": {"cudaMalloc", "cudaFree", "cudaMallocManaged"},
    "device_side_PDL_intrinsics_inside_existing_kernels": {"cudaGridDependencySynchronize", "cudaTriggerProgrammaticLaunchCompletion"}
}


def main():
    path = ROOT / "e03/launch_budget/SOURCE_COVERAGE_v2.json"
    source = json.loads(path.read_bytes())
    sites = [s for f in source["files"] for s in f["sites"]]
    counts = Counter(s["api"] for s in sites if s["kind"] == "runtime-call-unqualified")
    classified = []
    for group, names in GROUPS.items():
        selected = {name: counts[name] for name in sorted(names) if name in counts}
        classified.append({"category": group, "source_occurrences": sum(selected.values()), "distinct_API_names": len(selected), "API_counts": selected, "explicit_user_kernel_launch_API": False})
    known = set().union(*GROUPS.values())
    if set(counts) != known or sum(r["source_occurrences"] for r in classified) != 149:
        raise ValueError("Runtime inventory changed; classify before making summary claims")
    deny = Counter(s["api"] for s in sites if s["kind"] in ("deny-opaque", "deny-opaque-driver"))
    direct_work_names = {"cublasSgemm", "cublasGemmEx", "cublasGemmStridedBatchedEx", "cublasGemmBatchedEx", "cublasSgemmStridedBatched", "cublasSgemmBatched", "cublasStrsmBatched", "cub::DeviceScan::InclusiveSum", "ncclAllReduce", "cudaGraphLaunch", "cudaLaunchCooperativeKernel"}
    direct = {name: deny[name] for name in sorted(direct_work_names) if deny[name]}
    record = {
        "schema": "heterospec.e03.independent-runtime-API-scope.v1",
        "source_catalog_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "lexical_runtime_occurrences": sum(counts.values()), "distinct_API_names": len(counts),
        "classification": classified,
        "meaning": "The 149 occurrences are not 149 hidden kernels. None is an explicit user-kernel launch API. They include queries/errors, events/synchronization, configuration, allocations and in-kernel PDL intrinsics.",
        "concrete_work_submission_routes_denied_by_current_patch": direct,
        "source_count_limits": ["Counts describe lexical sites, not executed invocations", "The two CUB calls include a size-query call and a work call", "Library work may internally submit multiple kernels, hence site counts cannot price that work", "Graph replay can execute multiple nodes; graph policy is disabled and the source replay call is denied", "cudaLaunchHostFunc is a host callback, not an extra GPU kernel", "PDL device-side synchronization/completion intrinsics do not by themselves add a separate host kernel launch"],
        "memory_transfer_scope": "Memcpy/DMA calls and byte counts are not silently added to the kernel-launch quota. The current conservative implementation refuses memcpy/memset routes; that is a restrictive prepared-profile policy, not a claim that every transfer is one kernel.",
        "remaining_proof": "No real model path has been admitted or observed. The bounded relationship between charged explicit submissions and all model kernels is not certified by lexical transformation or CPU mocks. Ordinary numerical DLL initialization, real route use, guard coverage on that path and independent original-reference qualification remain NOT_RUN.",
        "current_policy": "Native arming remains blocked. Do not widen the frozen definition to all GPU activity or characterize all runtime APIs as kernel submissions.",
        "model_requests": 0, "CUDA_calls": 0, "kernel_launches": 0
    }
    (HERE / "RUNTIME_API_SCOPE.json").write_text(json.dumps(record, indent=2), encoding="utf8")
    print(json.dumps({"runtime_sites": sum(counts.values()), "distinct_APIs": len(counts), "groups": {r["category"]: r["source_occurrences"] for r in classified}, "explicit_kernel_launch_APIs_in_this_149": 0}, indent=2))


if __name__ == "__main__":
    main()
