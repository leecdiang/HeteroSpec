# Admission/budget/writer coverage and gaps

All native execution statuses in this table are NOT_RUN. Static wiring and CPU
mocks are separate from hardware truth.

| Boundary | Prepared implementation | CPU evidence / unresolved gap |
| --- | --- | --- |
| Whole source, archives, toolchain and original binaries | audit scripts pin full-file identities and full source/dependency closures |205 server identities and169 old source files match; loaded/runtime identity NOT_RUN |
| Before native ELF initialization | bounded_launcher.hpp starts with the concrete closed ProductionGate | No native fork/exec; launch-owner/BINDCHILD/close-before-worker connector remains review-only BLOCKED |
| Backend initialization/model load/context creation | Unchanged BoundCore in PR228 runtime.cpp checks ProductionGate and BudgetHooks before each actual API | New client routes those hooks to one stage broker; actual APIs never invoked |
| Before request/producer work | Unchanged Session.begin_lazy charges before lazy serialization and any decode | Controller enforces exact per-worker request order, active identity and no repeats |
| Every actual decode | Unchanged guarded_decode reserves actual llama_decode batch.n_tokens | Per-request and cumulative rows are capped; mock row events are not model rows |
| Trim/reset and pending reconciliation | Session/BoundCore mutation hooks and poison on uncertain native errors | A failed actual trim cannot be justified by unchanged head; retained raw bytes remain required |
| Active K/V reads and complete outputs | Original source-bound active_kv and producer/output adapters remain compiled | Native device synchronization/tensor reads NOT_RUN; provided-byte Python consumers do not certify physical extraction |
| Ordinary capture/receipt writes | controller_io checks FD/path/owner and reserves exact raw/metadata bytes before writes | Short/failed writes poison, no refund/retry; all three writer callsites use injected I/O |
| Syncs and root receipt directory sync | Guarded controller_io sync, including formerly direct root fsync | File/directory failure cases stop; native device/disk behavior still unmeasured |
| Writer failure marker after poison |1KiB metadata credit reserved before capture creation |348 captures fit the old1MiB partial-marker allowance; cleanup is bounded evidence, not new work |
| Worker stdout/stderr | Parent-side two-pipe bounded draining in the std-only supervisor |12MiB each ×20 streams ≤240MiB, within the old256MiB worker-log carve; no process-wide limit that breaks KV files |
| Worker exit and stage completion | WAIT_EXIT holds the active owner through complete output and owned normal exit0 | Bare waitpid is BLOCKED; trusted supervisor-result production connector remains unconnected |
| Stage/raw eligibility | Frozen27/81/72/81 graph, exact inventory, full bits+finite, prior seals and R18-input handoff | Artificial261 consumer checks and12 differential cases pass; native261 all NOT_RUN |
| RAM/pids hard limits | Delegated-cgroup path and owned ordinary-file rehearsal implementation | Real activation/membership NOT_RUN; no existing system limit changed |
| GPU UUID/peak/quiet window | ResourcePolicy requires exact bound identity, fresh measurements and external lease | No allocation or peak test; idle NVML cannot enforce continuous isolation |
| Five-hour stop | Fixed wall+monotonic lease/deadline, bounded host supervisor | CPU-owned stop delivery tested; actual uninterruptible GPU/device quiescence remains BLOCKED |

The combined broker/controller journal is capped at512MiB. Compact records have
a2048-byte maximum, with at most250000 RPC commands and bounded control events.
Source-derived upper cost and byte/file/restore margins are in RESOURCE_PLAN.md.
The8GiB build/text pool includes the controller state/log carve; no new quota
was added. Per-request ceilings intersect the global raw/metadata limits.

This build cannot promote JSON PASS, source hashes, a clear lock, an accounting
ACK or an idle GPU into production permission. Activating any native path needs
separate review/approval and the explicitly missing connections above.
