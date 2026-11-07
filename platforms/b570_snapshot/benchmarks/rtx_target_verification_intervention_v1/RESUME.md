# Durable recovery

Inspect BUDGET.json, ASSET_ENVIRONMENT.json, PREPARED.json, G0_PROGRESS.json and
work/rtx-target-v1/STATUS.json before doing anything. Read any STOP_REASON.json.
Do not reset the 12-hour budget or overwrite attempts, old arrays or frozen code.

Local checkout: D:/HeteroSpec-RTX-Target-V1. Assets are configured with
HETEROSPEC_ASSET_ROOT (default D:/HeteroSpec-PC). Python is the existing local
Python3.11 runtime. The original user checkout is not a scientific work directory.

No formal queue may start before G0, fixtures, cohort/input qualification and a
recorded implementation freeze. Native formal runs additionally require a complete
prediction seal and guard. Check exclusive controller PID plus creation identity;
never start a second active worker. Valid cached outputs must be hash-checked and
preserved byte for byte. Incomplete attempts remain as separate attempts.

The preparation script has already verified model/data/runtime identities and
written the historical mapping. Running it again is deliberately refused. Continue
from the recorded stage. No new-task model forward has occurred at preparation.

If qualification fails against historical arrays, retain the raw output, investigate
read-only, report BLOCKED_QUALIFICATION, and do not change expected arrays or run
the formal candidate. A later new scientific version requires explicit direction.

Controller entry (one active process only):

```powershell
& "$env:HETEROSPEC_ASSET_ROOT/python311/python.exe" scripts/platform/rtx_target_verification_intervention_v1/controller.py
```

If that environment variable is unset, use the configured asset root stated above.
STATUS.json contains the controller PID and Windows creation identity, current unit,
stage, actual completion, latest error and remaining original budget. Heartbeat is
local every60 seconds. Inspect it at stage boundaries or every20-30 minutes during
normal measurements. G0_LEGACY_THREADS12.json and EARLY_G0.json remain preparatory;
G0_THREADS24.json is the qualification for the actual formal native setting.

Formal nativeN0/N1 cannot start without all387 pre-live completions and the258-entry
prediction seal. H1 makes its own draft tape. N0 completion triggers all171 historical
comparisons and repeat checks; failure preventsN1. Outputs/results are atomic, every
attempt retained, incomplete recovery limited to one further attempt after checking
registered process creation identities. Deterministic/scientific failure is not retried.

After measurements, independent_verify.py directly reads raw without importing the
collector. restore.py reconstructs the content-addressed archive into an empty target;
run the independent verifier against that target. ARCHIVE.json provides ordered
parts/size/SHA256; omitted model/runtime bytes are explicitly listed. Delivery uses
the existing authenticated private branch and creates a Draft PR, never merging it.
