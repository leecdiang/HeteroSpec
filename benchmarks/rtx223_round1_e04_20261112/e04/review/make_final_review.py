"""Compose independent e04 findings; never loads producer verifiers/DLLs."""
import datetime
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent


def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


native = read("e04/review/NATIVE_FINAL_RECHECK.json")
if not native["passed_preparation_only"] or native["errors"]:
    raise ValueError("Independent native preparation checks failed")
parent = read("e04/review/PARENT_PRESERVATION_FINAL.json")
source = read("e04/review/SOURCE_PRESERVATION_FINAL.json")
ledger = read("e04/review/LEDGER_PRESERVATION_FINAL.json")
responses = read("e04/review/COMPILER_RESPONSES_RECHECK.json")
if not all(x["passed"] for x in (parent, source, ledger, responses)):
    raise ValueError("Preservation/raw response check failed")
life = read("e04/review/lifecycle/final-independent-v1/FINAL_REVIEW.json")
if any(x["exit_code"] != 0 or x["tests"] != 26 for x in life["runs"]):
    raise ValueError("Independent new lifecycle CPU fixtures failed")
if life["native_preflight"]["complete_lifecycle_upper_bound"] is not None or \
        life["native_preflight"]["native_proof_registry_entries"] != 0 or \
        life["native_preflight"]["native_release"] is not False:
    raise ValueError("Unproved lifecycle bound promoted to native admission")
qualification = read("e04/qualification/NATIVE_STATUS.json")
if qualification["executed"] != 0 or len(qualification["cells"]) != 66 or \
        any(x["status"] != "NOT_RUN" for x in qualification["cells"]):
    raise ValueError("Unexpected native qualification claim")
if sha("e04/qualification/CASES.json") != "3f166dafe052c574d5ff80076921f4042e231d4a96201b67a0d8609486e0c9c7":
    raise ValueError("Frozen22-case expectations changed")
front = read("e04/review/frontend-final/FINAL_FRONTEND_REVIEW.json")
pe = read("e04/review/frontend-final/pe-native/PE_RECEIPT.json")
deployment = read("e04/review/frontend-final/DEPLOYMENT_PROPOSAL_REVIEW.json")
if front["status"] != "PASS_CPU_BUILD_WHOLE_ARCHIVE_CLOSURE_AND_PE_DISK_IDENTITY_ONLY" or \
        pe["target"]["sha256"] != native["DLL_sha256"] or pe["target_LoadLibrary_calls"] != 0:
    raise ValueError("Frontend/native offline identity binding failed")

artifacts = [
    "e04/review/INDEPENDENT_REVIEW_ZH.md", "e04/review/DESIGN_GATES.json",
    "e04/review/PARENT_PRESERVATION_FINAL.json", "e04/review/SOURCE_PRESERVATION_FINAL.json",
    "e04/review/LEDGER_PRESERVATION_FINAL.json", "e04/review/NATIVE_FINAL_RECHECK.json",
    "e04/review/COMPILER_RESPONSES_RECHECK.json", "e04/review/check_native_build.py",
    "e04/review/lifecycle/final-independent-v1/FINAL_REVIEW.json",
    "e04/review/frontend-final/FINAL_FRONTEND_REVIEW.json",
    "e04/review/frontend-final/RAW_LABEL_SUPPLEMENT.json",
    "e04/review/frontend-final/DEPLOYMENT_PROPOSAL_REVIEW.json",
    "e04/review/frontend-final/pe-native/PE_RECEIPT.json", "e04/review/make_final_review.py",
    "e04/qualification/CASES.json", "e04/qualification/NATIVE_STATUS.json",
]
result = {
    "schema": "heterospec.e04.independent-final-review.v1",
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "decision": "INCONCLUSIVE", "round2": "DO_NOT_START", "native_release": False,
    "scope": "New CPU/source/freezing/actual fresh compile-link/disk identity only; no producer verifier imports for independent raw recomputation",
    "gates": [
        {"gate": "old_material_preservation", "status": "PASS_REHASH", "e03_files": 1749,
         "original_core_files": 3540, "e03_uniform_source_files": 3546, "ledgers": 5},
        {"gate": "new_lifecycle_planner", "status": "PASS_CPU_MOCK_ONLY", "cases_per_mode": 26,
         "modes": ["normal", "-O"], "independent_fixture_directories": 52,
         "raw_SQLite_sentinel_items_audited": 56,
         "all266_archived_CPU_records_independently_recomputed": False},
        {"gate": "complete_source_codegen_input_freeze", "status": "PASS_PREPARATION_ONLY",
         "input_files": 12706, "input_bytes": 3028201393, "complete_source_members": 3546,
         "raw_nvcc_response_files_independently_matched": 429},
        {"gate": "actual_new_numerical_DLL", "status": "PASS_FRESH_COMPILE_SEPARATE_LINK_ONLY",
         "fresh_e04_v2_units": 145, "CUDA": 143, "HOST": 2, "old_e03_or_failed_v1_objects": 0,
         "actual_raw_dependency_units_verified": 145, "separate_link_freeze_inputs": 12861,
         "uninterrupted_compile_link_session": False,
         "DLL_bytes": native["DLL_bytes"], "DLL_sha256": native["DLL_sha256"]},
        {"gate": "frontend", "status": "PASS_CPU_WHOLE_ARCHIVE_INPUT_CLOSURE_ONLY",
         "raw_headers_each_core": 1051, "resolved_CPU_features": 117,
         "archive_containers_each_core": 33, "exact_duplicate_member_occurrence": "NOT_ATTESTED",
         "separate_lock_sessions": True},
        {"gate": "PE_and_deployment_disk_identities", "status": "PASS_DISK_PROPOSAL_ONLY",
         "prior_pinned_dependencies_each_arm": 7,
         "vcomp_prior_identity": "UNKNOWN_NEW_SYSTEM32_PROPOSAL_NOT_QUALIFIED",
         "producer248_static_name_checks": "PRODUCER_ONLY_NOT_INDEPENDENTLY_RECOMPUTED",
         "actual_loaded_modules_or_loader_resolution": "NOT_RUN"},
        {"gate": "original_threads_host_window_lease_queue", "status": "BLOCKED_PENDING_EVIDENCE",
         "earlier_host_snapshot": "TRANSIENT_ONLY"},
        {"gate": "complete_lifecycle_physical4096_proof", "status": "BLOCKED",
         "native_proof_registry_entries": 0, "complete_lifecycle_bound": None,
         "first_refusal": "worker_bootstrap before numerical DLL load"},
        {"gate": "runnable_complete_model_profile", "status": "NOT_ESTABLISHED",
         "blanket_zero_work_denial_is_runnable_policy": False},
        {"gate": "actual_numerical_DLL_normal_load_metadata_and_dispatch", "status": "NOT_RUN"},
        {"gate": "native_22_by_3_qualification", "status": "NOT_RUN", "cells": 66},
        {"gate": "actual_q8_ABC_bytes_outputs_kernel_operator_timing", "status": "NOT_RUN"},
        {"gate": "real_bonus_seed_L4_correction_trim_pending_continuation", "status": "NOT_RUN"},
        {"gate": "same_contract_strong_fixed_control_complete_service_cost", "status": "NOT_RUN"},
    ],
    "proof_boundaries": {
        "full_kernel_scope": "Original family target/draft/runtime/standalone kernel launches from bootstrap/DLL constructors through teardown; API/DMA occurrences are separate",
        "119_standalone_operator_launch_plan_is_model_bound": False,
        "source_visible_counter_is_full_model_counter": False,
        "CPU_mocks_or_zero_refusal_prove_physical_coverage": False,
        "graphs_libraries": "Graph/library submissions are not one-kernel equivalents; actual admitted lifecycle needs trustworthy counts/bounds or denials plus a usable profile",
        "native_provider": "Canonical07f4b162 source compiled once without CPU-test flag, native configure remains -6; export not executed",
        "native_release_via_JSON": False,
        "process_failure": "Only own-process failstop or DLL-local graph error boundary; no generic cross-ABI recoverability claim",
        "unknown_actual_cost": "Durable reservation retained, no refund from missing result or poststats",
        "archive_scope": "All candidate bytes inside frozen complete archive are bound; exact selected occurrence can remain ambiguous without an unknown input",
        "compiler_trace_scope": "Raw dependencies/include diagnostics/response files and held copied inputs, not an OS filesystem-read or process-memory attestation",
        "OS_Python_scope": "Windows/driver/hardware/runtime DLLs and complete Python runtime/stdlib are not immutable copied closures",
        "historical_e03_gap": "Old provider sync and missing full per-invocation dependency-time witness remain historical, not retroactively repaired",
    },
    "C_mechanism": {
        "source_identity": "Complete numerical source3546 members equals e03 uniform tree",
        "subdomain": "Q8_0/F32 q8g2 independent two-four-column accumulators and preserved per-output case4 order, source only",
        "actual_quantization_dispatch_outputs": "NOT_RUN",
        "A_to_B": "Existing layout/dispatch consolidation, not all new C gain",
        "B_to_C": "CTA merge and weight fragment reuse with resource/parallelism tradeoffs, not another launch reduction claim",
        "fresh_registers_spill_shared_occupancy_DRAM_L2": "UNKNOWN",
        "performance_increment": None, "old_speculation_total_gain_attributed_to_C": False,
    },
    "budget": {
        "family": "rtx221-round1-20261112-e01", "new_allowance": False,
        "limits": {"model_requests": 256, "target_draft_rows": 1000000, "native_GPU_seconds": 10800,
                   "all_kernel_launches": 4096, "GPU_capture_bytes": 2147483648},
        "canonical_tables": ledger["canonical_tables"],
        "new_native_usage": {"model_requests": 0, "target_draft_rows": 0, "CUDA_contexts": 0,
                             "GPU_launches": 0, "native_GPU_seconds": 0, "GPU_capture_bytes": 0},
        "tool_copy_and_compiler_output_bytes_are_GPU_capture": False,
        "old_41_or_18_or_prior_counter_suites_rerun": False,
    },
    "retained_preparation_failures": [
        "Initial Make dependency/quoted-CPU/helper-binding gaps fixed before final respective freezes",
        "CPU mock ledger isolation/pending lease/policy hex issues, initial own repros retained; final26 ordinary/O and raw SQLite audit pass",
        "Nativev1 missing exact VC/Auxiliary/Build support layout;143CUDA failures and2HOST successes preserved",
        "NVCC emits duplicated first source dependency; vendor-specific strictv2 grammar and real214-entry recipe preserved",
        "Nativev2 all145compile/closure pass but linkLNK1104 from missing TEMP/TMP; immutable failed link preserved, link-v3 is separate freeze",
        "Frontend provisional containment/cc1 diagnostic/JSON tuple-list metadata failures preserved",
        "Narrow selected-member witness ambiguity retained; complete frozen archive scope accepted without gratuitous codegen rerun",
        "Deployment reviewer initial CRT-pin concern corrected by directly checking both prior audit pin rows; additive reconciliation metadata retained",
    ],
    "release_steps": [
        "Obtain original thread terminal/queued-worker/lease attribution; recheck fresh normal-host window at actual admission",
        "Establish trustworthy complete original-kernel lifecycle bound and actually usable same-policy profile before numerical DLL constructors/init; host confirmation alone is insufficient",
        "Bind actual runtime modules/device/graph policy and pass all66 qualification cells within the original durable family quota",
        "Then collect actual ABC and real consumer request-chain paired service costs; require explanatory improvement over packed and realistic net space before round2",
    ],
    "artifact_sha256": {rel: sha(rel) for rel in artifacts},
}
out = HERE / "FINAL_REVIEW.json"
if out.exists():
    raise ValueError("Do not overwrite frozen overall review")
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"decision": result["decision"], "native_release": False,
                  "sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "path": str(out)}))
