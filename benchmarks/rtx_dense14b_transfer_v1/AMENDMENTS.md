# Host engineering record

## 2026-11-01, before any native request

1. The first build invocation from `D:/rtx155/build_source` failed on import:
   inherited `study.py` indexes `Path(__file__).parents[3]`. No compiler or model
   ran. Retained that stage and restaged identical bytes at
   `D:/rtx155/staging/native/build_source`; build01 completed successfully.
   No native or arithmetic source change was required.
2. Source inspection found a prospective placement-auditor off-by-one.
   Authenticated `llama-model.cpp:1479` uses `n_layer_all + 1 - n_gpu_layers`,
   assigns the output layer at index40, and logs output-first offload at1792–1804.
   The frozen knobs24/20/16 therefore mean23/19/15 repeating layers plus output,
   starting at target layers17/21/25; embeddings stay CPU. The original auditor
   incorrectly expected starts16/20/24. Corrected only the CPU auditor and its
   fixtures, with explicit boundary/rejection regression tests. Native binary,
   capacity ladder, arithmetic, reference, timer and panel selection are unchanged.
   This is source-grounded metadata correction before outcomes, not tuning.
3. A no-model Windows Job acceptance test exposed an accounting race: after
   `Popen.wait()` returned exit0, Job active count was initially1 and became0
   within100ms. The initial assertion failure and subsequent samples are retained
   in `JOB_HOST_DIAGNOSIS.json`. Added a bounded five-second accounting wait in
   normal and failure cleanup, holding the Job and lock throughout. A nonzero
   count at the deadline remains a failure. No model was loaded or rerun; no
   scientific timer, native binary, input or endpoint changes.

Build01 executable SHA256: `db4bc97fef83f7ff2204ba76f58958b55339a96f998049ff245f0ff60beed516`.
Worker SHA256: `e1c1d77994ae1ec9b403f7699013ce17f00344621f85cbceb0b917abc256a533`.
Original implementation retained at PR155 head `afddffc016573cb78b398c95734a4363eedf1936`.
Native requests consumed by these repairs:0. Request ceiling remains800,
including736 planned and64 engineering reserve. Test receipt and source identities
will be included with the host freeze.
