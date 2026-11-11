# Public-tool-interface source validation: Windows not run

73 Python and 35 Node tests pass (108 total). Eight new cases cover public clock
elapsed duration, rounding, reversal/nonfinite values, preparation limits, minimum
environment allowlisting and conservative QPC ordering. Existing bootstrap and
source/build-binding regression tests also pass.

The actual restricted local node_repl service reported process undefined. Using
only its published APIs, it successfully imported the amended bootstrap module
and captured/sampled the public performance clock. This probe created no child
and loaded no native bridge. It establishes local tool-interface compatibility,
not Windows native loading, process creation, OS closure or B570 acceptance.

The amended entry no longer reads process, process.env, process.versions or
process.hrtime. It does not import node:process or retrieve process indirectly.
Platform/architecture come from node:os, the clock is explicitly injected from
public performance, and child environment is an explicit public allowlist. Public
clock duration is conservatively bridged to QPC without comparing their origins.

Independent Codex/GPT-6 Astra review found one P2 closure-interface mismatch:
stop returned broker_exit_code but audit expected exit_code. The auditor now
accepts and matches the actual persisted full receipt; a ColdSession.stop-to-audit
regression passes and rejects substituted receipts. The final full-candidate
review through P2 is scoped-clean.
Report/status are in review/. SOURCE_REVIEW_FREEZE.json is generated after review;
generated review artifacts, this summary and the freeze itself are not claimed as
independently reviewed runtime inputs. Earlier review findings and fixes remain
in Git history; the preceding source revision had 99 portable tests.

results/RESULT.md and results/COLD_START_RESULT.md remain byte-identical historical
BOOTSTRAP_BLOCKED records. All eight Windows cases remain unstarted by this local
task; no Windows compilation, GPU, model or scientific execution occurred. Native
bridge availability must still be demonstrated in the actual B570 service. A denial
must stop admission without a bypass or tool adaptation. PR115/117 and the paper
remain untouched. B570_NEXT_PROMPT.md writes results/TOOL_INTERFACE_RESULT.md and
a successful eight-case execution may only claim SMALL_WINDOWS_VALIDATION_PASS.
