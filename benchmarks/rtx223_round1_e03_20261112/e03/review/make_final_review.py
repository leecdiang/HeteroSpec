"""Compose the independent review from raw disk checks and scoped receipts."""
import datetime
import hashlib
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    absolute = str(pathlib.Path(path).resolve())
    if os.name == "nt" and not absolute.startswith("\\\\?\\"):
        absolute = "\\\\?\\" + absolute
    with open(absolute, "rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


bindings = read("e03/review/FINAL_BINDINGS.json")
if not bindings["passed"] or bindings["errors"]:
    raise ValueError("Independent binding check did not pass")
counter = read("e03/review/counter-independent-v1/RECEIPT.json")
if counter["scenario_count"] != 16 or not counter["all_pass"]:
    raise ValueError("Independent CPU counter result did not pass")
pe = read("e03/review/pe-independent/PE_INDEPENDENT_RECEIPT.json")
if pe["missing_required_exports"] or not pe["CPU_only_reentry_export_absent"]:
    raise ValueError("Independent offline PE identity failure")
expected = read("runtime/FINAL_SOURCE_IDENTITIES.json")["source_files_sha256"]
reconstruction = read("runtime/RECONSTRUCTION_V2_RECEIPT.json")
bad = [rel for rel, digest in expected.items()
       if sha(ROOT / "runtime/reconstruction-v2" / rel) != digest]
if bad or len(expected) != 3546 or reconstruction["returncode"] != 0:
    raise ValueError("Independent reconstruction member check failed: " + str(bad[:5]))
if sha(ROOT / "runtime/materialize_final_source.py") != reconstruction["helper_sha256"]:
    raise ValueError("Reconstruction helper receipt does not match")

artifacts = [
    "e03/review/INDEPENDENT_REVIEW_ZH.md", "e03/review/FINAL_BINDINGS.json",
    "e03/review/verify_final_bindings.py", "e03/review/make_final_review.py",
    "e03/review/counter-independent-v1/RECEIPT.json",
    "e03/review/pe-independent/PE_INDEPENDENT_RECEIPT.json",
    "e03/review/RUNTIME_API_SCOPE.json", "e03/review/COMPILER_RESOURCE_RECHECK.json",
    "runtime/RECONSTRUCTION_V2_RECEIPT.json", "runtime/AS_BUILT_BINDINGS_FINAL.json",
    "runtime/FINAL_SOURCE_IDENTITIES.json", "e03/launch_budget/STATUS.json",
    "e03/frontend/STATUS.json", "e03/frontend/SOURCE_v4.json",
    "e03/frontend/build-v4/BUILD.json", "e03/dedup/DEDUP_E03_RESULT.json",
    "e03/BUDGET_CONTINUITY.json",
]
result = {
    "schema": "heterospec.e03.independent-final-review.v1",
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "decision": "INCONCLUSIVE", "round2": "DO_NOT_START", "native_release": False,
    "scope": "New e03 source/CPU/link/disk identity only; no producer verifier imported",
    "reviewer_activity": {"numerical_DLL_LoadLibrary": 0, "CUDA_calls": 0,
                          "model_requests": 0, "GPU_kernel_launches": 0,
                          "old_41_suite_rerun": False, "old_18_suite_rerun": False},
    "gates": [
        {"gate": "original_e02_and_runtime_core_preservation", "result": "PASS_REHASH", "files": [764, 3540]},
        {"gate": "new_shared_atomic_CPU_counter", "result": "PASS_CPU_ONLY", "independent_scenarios": 16},
        {"gate": "actual_numerical_DLL_compile_link", "result": "PASS_LINK_ONLY", "objects": 145,
         "reused": 141, "fresh": 4, "canonical_provider_objects": 1},
        {"gate": "actual_numerical_DLL_identity", "result": "PASS_OFFLINE_PE_ONLY",
         "sha256": pe["target"]["sha256"], "bytes": pe["target"]["bytes"]},
        {"gate": "future_source_reconstruction", "result": "PASS_INDEPENDENT_MEMBER_REHASH",
         "members": 3546, "source_delta_overrides": 66, "reconstruction_mismatches": bad},
        {"gate": "frontend_binding_and_refusal", "result": "PASS_PREPARATION_ONLY",
         "compiled_preflight_receipt_cases": 22, "receipt_validator_cases_per_mode": 6,
         "normal_numeric_loader_called": False},
        {"gate": "original_thread_terminal_and_host_scope_clearance", "result": "BLOCKED_UNVERIFIED",
         "reason": "MCP -32000 prevents original terminal timeline; local metadata and five-process restricted namespace are insufficient"},
        {"gate": "normal_numerical_DLL_initialization_and_metadata_calls", "result": "NOT_RUN",
         "reason": "CUDA DLL constructors/fatbinary registration are not established zero-CUDA work; standalone CPU mock loads do not attest numerical DLL binding"},
        {"gate": "all_model_original_kernel_budget_coverage", "result": "UNQUALIFIED_BLOCKED",
         "reason": "Lexical guards and CPU mocks do not prove all kernels on real target/draft/runtime paths; native configure always returns -6"},
        {"gate": "runnable_same_contract_narrow_model_profile", "result": "NOT_ESTABLISHED",
         "reason": "Current conservative opaque memcpy/memset/library denials make complete request usability unproved"},
        {"gate": "native_66_case_qualification", "result": "NOT_RUN"},
        {"gate": "real_q8_quantization_bytes_and_all_output_ABC", "result": "NOT_RUN"},
        {"gate": "real_consumer_request_state_chain", "result": "NOT_RUN"},
        {"gate": "paired_packed_increment_and_complete_service_cost", "result": "NOT_RUN"},
    ],
    "counter_failure_semantics": {
        "C_ABI_exceptions": "Final provider C exports do not throw; status APIs return or instrumented void refusals TerminateProcess only own process",
        "own_process_failstop_exit_codes_tested": [3761438721, 3761438724],
        "general_owner_recoverability": False,
        "DLL_local_graph_callback": "C++ errors caught inside MSVC DLL, returned as GGML_STATUS_FAILED; not generic allocator/transfer recovery",
        "unknown_actual_after_death": "Supervisor must retain/charge durable reservation, not refund a missing result",
        "scope": "One bound DLL instance shares all linked TUs; not arbitrary multiple DLL copies",
    },
    "kernel_accounting_scope": {
        "family_limit": 4096, "new_allowance": False,
        "intended_scope": "Original model/runtime/standalone kernel launches, including target and draft",
        "lexical_149_runtime_sites_are_kernel_count": False,
        "runtime_categories": {"query_error_attribute": 59, "event_stream_sync_lifecycle": 59,
                               "configuration": 11, "host_memory": 8, "device_allocation": 10,
                               "in_kernel_PDL_intrinsics": 2},
        "DMA_added_to_kernel_quota": False,
        "libraries_graphs": "Library internals and graph replay require proof or denial; static site counts are not dynamic kernels",
        "current_execution_policy": "Graphs/NCCL/PDL disabled and NO_VMM on, same policy required A/B/C/draft/reference; actual native policy remains unqualified",
    },
    "C_source_assessment": {
        "subdomain": "Q8_0/F32 q8 g2, two independent four-column groups, no IDs/fusion/precision change, SM120warp32case4",
        "weight_fragment_reuse": "v and dw loaded outside group loop and reused across both accumulator groups",
        "per_output_order": "Original case4 K/lane partition, per-output arithmetic and cross-warp/lane reduction retained at source level",
        "native_width_replaced_by_8": False,
        "guard_fixes": "K/M equality, contiguous geometry, actual same-device CUDA buffer and allocation-span checks precede original quantizer",
        "numerical_correctness": "NOT_RUN", "outside_C_subdomain_packed_qualified_fallback": False,
        "compiler_only_resources": {"case4_registers": 63, "case4_shared_bytes": 3072,
                                    "C_registers": 91, "C_shared_bytes": 6144,
                                    "both_stack_and_spills_bytes": [0, 0, 0],
                                    "occupancy": "UNKNOWN", "DRAM": "UNKNOWN", "L2": "UNKNOWN"},
    },
    "provenance_limit": {
        "v1_catalog_members": 283,
        "known_mutation": "Superseded provider .cu body synchronized during batch; exact time unrecorded, approximate catalog time only; old source preserved and old object excluded",
        "old_provider_sha256": "74e727d1a30dd9c09349371b9a937b25d489f861909234ccbbc3d33f3a4af90d",
        "final_provider_sha256": "07f4b16222dc260491592a1f9369ecd829fdb393a1f6991f40eb17647882439c",
        "header_variants": "Old CUDA TUs use 2da1...; final provider uses45e1...; existing C ABI identical, one unused status-helper declaration additive",
        "noncatalog_changed_original_member": "vendors/hip.h, inactive HIP profile, declared frozen delta match",
        "all_dependency_compile_time_immutability_attested": False,
        "what_is_proved": "Recorded successful object bytes/CUDA catalog plus current whole original/final/delta source hashes",
        "future_fresh_candidate": "Freeze/hash complete code-generating dependency tree before compile; no universal bit-identical DLL rebuild claim",
    },
    "retained_failures": [
        "CPU v1 CABI exception/optimized assumption corrupted three opaque-route results",
        "CPU v2 OPAQUE Windows macro collision compilation failed",
        "CPU v3 aggregator initially mishandled expected nonzero failstop codes; original receipt retained and corrected offline",
        "Native v1 incomplete private type MMVQ failure, native v2 include-path failure",
        "First materializer long-Windows-path partial output retained; v2 extended-path reconstruction succeeded",
        "Independent review composer first used ordinary MAX_PATH reads; failed on long UI path. Original reviewer script/error receipt retained and extended-path reader applied before successful rehash",
    ],
    "no_performance_claim": True,
    "speculation_total_gain_attributed_to_C": False,
    "artifact_sha256": {rel: sha(ROOT / rel) for rel in artifacts},
    "recommendation": "Finish original-thread/host clearance, complete-dependency freeze and a runnable fully chargeable kernel profile before any native admission; then 66-case qualification, real ABC/request chain and complete service costs within original family quota. Do not start round2 from CPU/link evidence.",
}
(HERE / "FINAL_REVIEW.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"decision": result["decision"], "native_release": False,
                  "reconstructed_members_independently_rehashed": len(expected),
                  "review": str(HERE / "FINAL_REVIEW.json")}))
