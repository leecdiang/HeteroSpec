# Host evidence and launch boundary

Start with RESULT.md. S0 actual CPU results differ from the delivered toy tests.
All host files are additions inside PR112; old PR109/111 restores are read-only.

Main evidence: HOST_SOURCE_BINDINGS.json, HOST_RULE_LOCK.json, S0_RESULT.json,
S0_FULL_VECTOR_RELATIONS.json, S0_RAW_MANIFEST.json, S0_RESTORE_RECEIPT.json,
OLD_ASSET_RECHECK.json, ACTOR_BUILD.json (retained failure), ACTOR_REPAIR_01.json,
HOST_WIRE_TESTS.json, HOST_CONTROL_TESTS.json. CPU evidence and exact compiled
runtime bytes are archived separately. Numerical DLLs/models remain dependencies
of their old fixed restores; no weights are committed.

CPU-only reproduction in a fresh result workspace uses prepare.py, run_s0.py,
lock_s0.py, audit_s0.py with the --old/--pr111/--source paths shown in the retained
build logs. Commit the plan/input/harness before development, lock the unchanged
CPU executable before held outputs. Do not overwrite the committed first runs.
S0_CMakeLists.frozen.txt is the exact original CPU build file; the current host
CMake file additionally builds the offline-only S1 target. Three reused sources
retain original CRLF bytes via explicit -text attributes to preserve their
recorded compiled-source hashes. The prototype's q3/q4 toy exposure stays visible.

S1_F0_DRAFT_00/01 and earlier readiness/control-failure receipts are historical
unapproved artifacts. The sole current execution object is S1_F0.json:
8935c7cb5369ec052d074f060d9519ac51311620830819b74be5e3c49d3a0fb7.
S1_INPUTS.json binds actual16 generated input files; S1_PLAN.json binds161 slots.
Rebuilding/changing a binary, dependency, source, input or relevant environment
requires a new prospective F0; a source-compatible rebuild does not inherit its
old binary hash or approval.

After explicit human approval of that exact SHA, and only then, the intended
command on this qualified host is:

```
python host/run_s1.py --author-approved-f0-sha 8935c7cb5369ec052d074f060d9519ac51311620830819b74be5e3c49d3a0fb7
```

Do not run it as a help/smoke test or a free device probe. It starts the charged
capability-only process first, then eligible predeclared graph hosts. It cannot
resume an existing S1_RUN or silently retry failed slots. The admission unit
tests use process-launch mocks and are not author approval. No GPU support,
placement or arithmetic evidence exists until the actual raw events are checked.

Native actor: build_actor.py derives actual worker/source from the frozen old
restore, changes only representation admission/wire labels and the new actor's
honest sampling field, and compiles without launch. repair_actor_header.py records
the one missing-include repair. wire_s2.py serializes the real parser schema from
old source-bound exposed prompt recipes. It prepares no model execution; actual
S2 actor/request/raw/observer qualification remains a separate gated stage.
