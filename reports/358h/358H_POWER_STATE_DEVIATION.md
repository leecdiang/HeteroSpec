# 358H Power-State Deviation

Status: **PREVIOUS MACHINE-SIDE QUALIFICATION INVALID / RETAINED FOR DIAGNOSIS**

The 2026-09-14 through 2026-09-17 machine-side qualification was executed without a preregistered, positively verified AC-power condition. The operator subsequently confirmed that the experiment computer was not connected to external power. Those runs are retained unchanged as engineering evidence, but they are excluded from Phase-0 qualification and from all performance or energy inference.

The following must be repeated with `PowerOnline=true`, `Discharging=false`, a frozen Windows power scheme, and power state captured before and after every run:

- CPU and NPU device-binding checks;
- CPU and NPU bounded functional smoke;
- NPU 8192-token shape-profile compilation and cache binding;
- telemetry sanity, sampling-stability, and overhead qualification;
- the final Phase-0 manifest and gate.

Content-addressed provenance work remains valid: model repositories/revisions, model and tokenizer hashes, semantic-equivalence analysis, conversion recipe, package freeze, and IR hashes do not depend on the host power state. They must nevertheless be re-hashed during the replacement qualification.

Superseded remote evidence commit: `a957791b9a13fe51a35e62b66a12f88ace83a6bb`.

No formal Phase-1 timing or energy observation was collected before this deviation was identified.


