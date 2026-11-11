# B570 CPU8 closeout v6 — proposed, not executed

Parent: PR119 `aa7d64b5e4c198699a2f1fcc52c8ff2e31103fa7`.

This is an additive plan and portable guard prototype, not a Windows repair qualification or CPU8 result. Read [AUDIT.md](AUDIT.md), execute [PROTOCOL.md](PROTOCOL.md), and use [B570_PROMPT.md](B570_PROMPT.md) for handoff. Preserve PR119 and all earlier evidence. New work belongs in a new implementation/results UUID beneath this directory.

`admission.py` is deliberately small. Its inputs must be derived by the native auditor from actual evidence, never supplied as trusted flags in a candidate receipt. It does not replace job supervision, filesystem identity, native qualification, source freeze, process accounting, or tool provenance. `bind_download` verifies content identity, not network origin. `bind_invocation` checks execution transcript consistency, not provider authenticity. `role_guard` compares lexical Windows paths; the native adapter must also establish filesystem identity and reject aliases/reparse points.

Local validation: `python -m unittest discover -s benchmarks/b570_cpu8_closeout_v6 -v`. Eight portable test methods pass on Linux. Windows execution, deployed integration, final review, and formal CPU8 remain NOT_RUN. No GPU/model/scientific work is authorized by this plan.
