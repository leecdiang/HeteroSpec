# One-shot unattended RTX workflow

`start.ps1` launches a hidden, independent local process. It calls only the
already frozen F0B formal runner and deterministic CPU tools, then commits and
pushes the results, validates actual GitHub bytes and updates draft PR #84.
It never invokes Codex, an OpenAI API, a heartbeat or an AI scheduler.

Order: formal3456 +144 warmups → analysis → unchanged identity/budget checks →
report → two archives → independent local restoration → Git push → actual
authenticated remote restoration → receipt push → draft PR update.

The controller is outside the direct F0B code inventory. It cannot change the
frozen model runner, its inputs, numerical stack, statistics or schedule. Its own
files are bound in AUTORUN_BOUNDARY.json and remotely verified before launch.
Display routing is unchanged. A thread-scoped Windows keep-awake request blocks
automatic system sleep until exit without changing the fixed power plan.

Keep the computer on AC and the network available. The console need not remain
open. Progress is written to outputs/HeteroSpec_RTX_三家族实验_运行状态.md;
the frozen runner appends each block to work/third-family/autorun/run.log.

Duplicate launch is refused. Formal generations are never retried. Scientific
divergences and failed/missing planned slots are retained. An unexpected control
failure stops with FAILED_NEEDS_ATTENTION and preserves all existing evidence.
After formal COMPLETE, `autorun.py --resume-post` may continue unfinished CPU or
publication steps; it cannot replay formal requests. Only network publication
and remote CPU restoration have bounded operational retries.
