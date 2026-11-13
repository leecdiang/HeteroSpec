# CPU native-chain handover

Read README.md, STATUS.json, NATIVE_PLAN.md, BUILD_EVIDENCE/BUILD.json,
coverage_map/generated/SUMMARY.json and review/RESOURCE_PROPOSAL_REVIEW.json.
Parent PR227 is d1b4f909fdb33c732b951489c123237c4f057850; PR226 is
87ea17971642f65468678cee8477505b9956611a. Check actual latest heads before
continuing. The prior missing full source has been recovered and matched.

Only CPU preparation is authorized. DO NOT run either native-linked binary,
including help/selftest/default-denial, nor any old model/vocab tool. Do not
initialize backends, models, contexts, placement, N1a/N1b/N2 or timing. ProductionGate
is a final permanent deny gate, not a grant waiting for a Boolean switch.

The actual A5000 host is available through the existing private workspace and
audit handover. Exact host paths, allocated historical UUID, private original
build logs and full source/dependency copies are kept outside public Git.
New build epochs01–04 and failed artifacts are retained in an independent
successor directory. No experiment controller, runner queue, native request or
GPU resource lock was started. Old ledgers/STATE were only read; closeout
rehashed120 old files and all120 matched. Do not infer permission from free VRAM
or old unlimited-window authorizations.

The final native ELF hashes are in BUILD_EVIDENCE/BUILD.json. The source-input
manifest binds all actual compiled native and accounting files. Original
reference and loop4 numerical archive SHA values, parser-only object identities,
dynamic dependencies and file-only shared-library hashes are included. These
prove compile/link/file identity only; actual loaded library identity and native
state remain NOT_RUN. The producer build's numerical libllama/libggml was not used.

For CPU replay use run_cpu_tests.py in a fresh absolute output directory with
Python3, Linux C++17, readelf and Node available. It builds and inspects only
standard-library mock executables, never the native artifacts. Saved job templates
can be rechecked without a model. assemble_checks.js must return incomplete/
NOT_RUN against an empty real capture set. Public archive restoration and saved
receipt checking are CPU-only evidence, not a native rerun.

No-Go items: separate finite GPU authority and current quiet window/UUID;
reviewed admission/strict-stage controller and one outstanding worker;
actual no-forward placement/RSS/VRAM preflight implementation/admission;
actual loaded identity; R repeat and cold semantic alignment/equality; truthful
native raw captures and all261 strict comparisons. The accounting broker itself
does not grant stage permission. No model or placement request may be made to
fill those gaps under this handover.

The next reviewer may assess the proposed72/76 requests,69354/85738rows,
10 deployment axes,553094505923-byte space bound and5-hour watchdog.
These remain unapproved, including failure reserve. If future authorized
qualification fails, preserve the first raw difference and counters, stop before
strong or timing, and never relax equality, change R, refund work or restart STATE.

Paper claims supported now: original-source recovery, CPU compile/link and
synthetic fault-safety preparation. Unsupported: native lifecycle correctness,
resident/cold equivalence, real retained KV, LOCAL-specific opportunity,
four-arm qualification, natural service speed, or a5% benefit.
