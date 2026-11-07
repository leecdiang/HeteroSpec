# Reproduce or continue

Windows PowerShell on the qualified host, repository directory `C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec-v3`. The Python interpreter is `D:/HeteroSpec-PC/python311/python.exe`. Weight, released llama-b10839 DLL and compiler identities are ASSET_IDENTITY/BUILD_IDENTITY. They are omitted from Git. Hash them again with identity.py on a host where those assets exist; offline archives cannot authenticate omitted external bytes.

Use a clean independent checkout for a new preparation. Place the exact pinned source archive (SHA-256 5892a57221b9e7b6451ff368c085f95bd61697f879792b2da63d0f835b0eef31) at a chosen local path. This is an archive input argument, not a downloaded build product. All eight supported modes appear in `study.py --help`.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& 'D:/HeteroSpec-PC/python311/python.exe' -B 'C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec-v3/scripts/platform/rtx_trajectory_cost_v3/study.py' prepare --source-tar 'C:/Users/ASUS/Documents/Codex/2026-09-28/files-pasted-by-the-user-you/work/llama-b10839-source.tar'
& 'D:/HeteroSpec-PC/python311/python.exe' -B 'C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec-v3/scripts/platform/rtx_trajectory_cost_v3/study.py' seal-protocol
```

Do not rerun prepare on a frozen/current checkout. Engineering repair requires preserving failed attempts; formal stages permit no reruns/replacement rows or numerical source edits. F0 guards reject any changed bound file. After reviewing the exact remote F0 content SHA, author supplies `EXECUTE_FROZEN` and that full SHA. The following PowerShell variable is read directly from the already-verified real F0 receipt; the command still requires explicit author review of precisely that value.

```powershell
$reviewed=(Get-Content -Raw -LiteralPath 'benchmarks/rtx_trajectory_cost_v3/F0_REMOTE_RECEIPT.json' | ConvertFrom-Json).commit
& 'D:/HeteroSpec-PC/python311/python.exe' -B 'C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec-v3/scripts/platform/rtx_trajectory_cost_v3/study.py' A-pre-live --authorization EXECUTE_FROZEN --reviewed-sha $reviewed
& 'D:/HeteroSpec-PC/python311/python.exe' -B 'C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec-v3/scripts/platform/rtx_trajectory_cost_v3/study.py' seal-predictions
& 'D:/HeteroSpec-PC/python311/python.exe' -B 'C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec-v3/scripts/platform/rtx_trajectory_cost_v3/study.py' A-live
& 'D:/HeteroSpec-PC/python311/python.exe' -B 'C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec-v3/scripts/platform/rtx_trajectory_cost_v3/study.py' B-formal --authorization EXECUTE_FROZEN --reviewed-sha $reviewed
& 'D:/HeteroSpec-PC/python311/python.exe' -B 'C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec-v3/scripts/platform/rtx_trajectory_cost_v3/study.py' verify
& 'D:/HeteroSpec-PC/python311/python.exe' -B 'C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec-v3/scripts/platform/rtx_trajectory_cost_v3/study.py' archive
```

Each formal stage creates a new directory once and preserves an operational failure prefix. A pre-live qualification/operational failure writes A_TERMINAL; skip seal-predictions/live and B can run the same frozen 24 tasks after its own identity/thermal check. A is never resumed on that cohort. Identity changes block dependent execution. Scientific B mismatch continues all scheduled runs and sets only that path speedup/CI to null.

For a portable evidence check, select an exact `.parts.json` index in ARTIFACT_MANIFEST.json, keep its named parts beside it, and use `package.py reconstruct --index FULL_INDEX_PATH --output NEW_EMPTY_DIRECTORY`. This performs part/whole archive hash checks, safe extraction and independent offline recomputation, with `-B` and no GPU/network. Author and anonymous results record distinct privacy/chronology limits; no anonymous capsule is claimed to authenticate original remote time.

The prepare/seal commands document the actual pre-F0 preparation entry. The delivered frozen checkout refuses prepare. Recompute retained evidence offline or continue that exact freeze after review; a separate future A needs a new study and new unexposed reserved pool. This study-specific branch is not a generic study-name reset tool.
