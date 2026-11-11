# Supervision v3 boundaries; numerical policy stays frozen

The old1.032s interval mixed live-process observation with post-wait raw parsing
and module hashing. Old records lack the phase split and remain invalid under
their old auditor; no part or all of1.032s is retrospectively attributed to
post-exit work. No old receipt/sample/ledger/controller/F0 is changed.

The new monotonic_ns timeline records launch-begin, Popen-return, each resource
and directory read begin/end/discard/error, first coordinator poll confirming
exit, post-exit audit begin/end, lifecycle write begin and separate write-complete
commit marker. Windows GetProcessTimes creation/actual exit FILETIME and CPU
times are retained as OS evidence only, never subtracted from monotonic time.
Exit is stamped immediately after poll confirms completion, before post-exit
parsing/hashing. The independent monitor's own exit observations remain separate.

One lightweight coordinator owns the target and two CPU subprocesses per slot:
one monitor process with resource and directory-scan reading threads (plus its
main thread), and one full identity/output auditor process. The coordinator
does not perform a full raw parse, module hash or recursive scan while the
target is alive. Each stream must remain fresh while waiting for GO and while
executing. Identity audit success and at least one valid resource/directory
observation are mandatory before GO. Both complete runtime module hashes and
complete closing/output/numerical audits remain mandatory.

The maximum effective runtime gap remains exactly1,000,000,000ns. Conservative
qualification uses first-read-completion minus launch-begin; each read duration;
next-read-completion minus previous-valid-read-BEGIN; and exit-observed minus
last-valid-read-BEGIN. All must be<=1s for both independent streams. A live
pending read/freshness exceeding1s stops and terminates the target. Read duration
is never hidden inside an instantaneous timestamp. Exit/read races are discarded
without resource values. A read finishing after exit is not a runtime sample.
No valid samples means no runtime eligibility. Slow directory reads still leave
the resource stream running, but can independently invalidate directory coverage.
A stalled/crashed monitor/auditor, failed read, timeout or abnormal exit stops;
the coordinator retains PIDs and OS lifecycle evidence and performs bounded
kill/wait cleanup. There are no production expected failures or retries.

After exit, runtime sampling ends; full logs/module hashes/inputs/all four stage
vectors are audited independently. Post-exit delay cannot expand a runtime gap,
but consumes engineering budget and never waives identity/output checks. Receipt
write completion is recorded after its close in a separate immutable commit
file, avoiding a fabricated self-contained future write timestamp.

Budget: at most161 experiment hosts (1 support-only census+160 graph hosts) and
160 graph calls. At most322 additional CPU control workers, not GPU experiments;
one controller, two sampler threads plus monitor main and one audit main per
active slot. These are registered costs, not a claim about total OS processes.
The future controller's entire engineering wall, starting before admission,
is<=3600s; each complete slot including CPU workers, live monitoring, all hashes,
post-audit, cleanup, comparisons and lifecycle writes is<=180s. Observed native
lifetime and post-exit audit wall are separately reported; the conservative
engineering upper bound includes both and control overhead. Old41.327s accounting
is never translated into this new definition. Independent later CPU delivery is
separately timed. CPU preparation/fault tests have separate actual-wall/process
receipts and are not experiment attempts. All new source/build/CPU-test/output
bytes plus one full raw-export reserve fit2GiB. Native and CPU-control RSS<=8GiB
each, available hostRAM>=8GiB, free disk>=4GiB; nominal resource/directory period
100ms, actual effective gap<=1s. The unchanged native records GPU memory only at
its charged-host checkpoints (free>=512MiB); no device query occurs here.

Numerical contract is byte-for-byte the old aligned_numerical_v2/RULES.md and
its analyzer/reference/build/query_head.h: same16 exposed inputs, five modes,
two independent processes per input/mode,40 q1 first then120 q>1, fixed QH_C,
Q0 and PQ independent mask slabs, precisions/CONT/REPEAT/ownership/output layout,
all hard numerical/control stops and descriptive finite q>1 differences. No old
sample is imported. The native interface changes only the hard-bound run_id
literal; host.cpp and all graph/arithmetic code and DLL bytes are unchanged.
No new GPU query/library load/graph/model is authorized until exact new F0 approval.
