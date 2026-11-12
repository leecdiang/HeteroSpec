"""Run the closed native preflight without loading any numerical DLL."""
from pathlib import Path
import hashlib
import json
import sys
from lifecycle_budget import NativeProofRegistry, Node, Phase, REQUIRED_PHASES, REQUIRED_ACTORS, inspect_native_candidate, fingerprint

HERE=Path(__file__).resolve().parent
out=HERE/(sys.argv[1] if len(sys.argv)>1 else "NATIVE_PREFLIGHT.json")
if out.exists(): raise FileExistsError(out)
# This proposal deliberately contains self-issued names and zero claims. They
# remain untrusted; even the zero bootstrap claim cannot bypass the registry.
artifact="bcdb7642d32609c9242dc8aaecfadfb9f4e082ac8cfeccf5de6b7466546eb24b"
phases=tuple(Phase(p,(Node("opaque","unproved:"+p,"SELF_ISSUED:"+p,artifact),)) for p in REQUIRED_PHASES)
policy=fingerprint({"graph_policy":"OFF","opaque_routes":"DENY","all_physical_coverage":"NOT_QUALIFIED"})
result=inspect_native_candidate(phases,{a:policy for a in REQUIRED_ACTORS})
result.update({"scope":"CURRENT_NATIVE_PROPOSAL_NOT_A_PERMISSION","original_physical_ceiling":4096,
               "resource_family":"rtx221-round1-20261112-e01","new_epoch_allowance":False,
               "native_claimed_zero_work_phases_do_not_prove_zero":True,
               "all_required_phases":list(REQUIRED_PHASES),
               "missing_trusted_obligations":[{"phase":p,"physical_upper_bound":None,"proof":"UNAVAILABLE"} for p in REQUIRED_PHASES],
               "remaining_family_allowance_not_recomputed_from_partial_local_data":True,
               "normal_numeric_DLL_LoadLibrary":0,"numeric_worker_processes_started":0,
               "GPU_launches":0,"model_requests":0,"target_draft_rows":0,
               "canonical_production_ledger_writes":0,
               "planner_source_sha256":hashlib.sha256((HERE/"lifecycle_budget.py").read_bytes()).hexdigest()})
out.write_text(json.dumps(result,indent=2),encoding="utf8")
print(json.dumps({"decision":result["decision"],"complete_lifecycle_upper_bound":None,"normal_DLL_loads":0,"native_registry_entries":0}))
