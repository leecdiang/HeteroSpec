# Actual joint closeout

{
  "status": "FORMAL_COMPLETE",
  "updated_utc": "2026-10-02T11:38:29.109934+00:00",
  "mode": "A19_B19",
  "states": {
    "A": "COMPLETE_VALID",
    "B": "COMPLETE_VALID",
    "A_terminal": {
      "status": "INCOMPLETE_OPERATIONAL_FAILURE",
      "utc": "2026-10-02T09:16:22.859231+00:00",
      "reason": "RuntimeError('HOST_CONFIGURATION_CHANGED')",
      "same_cohort_A_resume_forbidden": true
    }
  },
  "actual_counts": {
    "A_reserved_processes": 342,
    "A_reserved_model_forwards": null,
    "A_reserved_live_processes": 57,
    "B_formal_processes": 171,
    "engineering_model_processes": 476,
    "worker_logical_forwards": 21549,
    "worker_operation_calls": 18252,
    "tokenizer_only_processes": 3,
    "tokenizer_only_forwards": 0,
    "launch_rejections": 2,
    "native_allocator_records": 307643,
    "ledger_events": 348518,
    "native_forward_count_limit": "Native allocator records include logical and physical metadata, so this is not a distinct logical-forward denominator; zero reserved inference follows no reserved process launch"
  },
  "checkpoints": {
    "F0": "06562c920046360bd1243a6d845408e9a371f3a1",
    "F1": "d02f55c5d136b9043c5dd208db53511c15443f4b",
    "F2": "f9b88dcdc5541297a32faa0437b2bad2b93ffafc",
    "B_START": "d0a1238580f3daff0d8011fb07b4c5c63640828e"
  },
  "independent_status": "PASS",
  "formal_planned_is_not_actual": true
}
