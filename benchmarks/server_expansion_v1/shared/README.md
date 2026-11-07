# Shared offline study tools

These files are byte-identical across six independent study PRs. Each PR adds only
this shared subtree and its own lane directory; none changes PR196, old experiments,
models, manuscript or main. Identical shared blobs can be merged without choosing
one platform's data over another. Never edit a sibling study's result directory.

Use Python 3.11+ standard library. Start from a fresh lane worktree and read that
lane's PLAN.md, HOST_PROMPT.md and study.json, then COORDINATION.md and ADAPTER.md.
Do not run all six panels merely because six PRs exist.

Useful commands (replace LANE/PANEL/ROOTS with actual study data):

```sh
S=benchmarks/server_expansion_v1/shared
python3 -m unittest discover -s "$S/tests" -v
python3 "$S/gguf_inventory.py" /approved/model.gguf inventory.json --hash
python3 "$S/experiment.py" plan benchmarks/server_expansion_v1/LANE/study.json PANEL ROOTS.json plan.json
python3 "$S/experiment.py" analyze plan.json checked-records.json analysis.json
```

Plan roots are objects with `root`, one per independent source/conversation root.
The schedule records arm/session workers and root slots; native primers, references,
qualification and failures have separate reservations and records. An exposed
transfer panel is never renamed a new blind cohort. `experiment.py` requires every
planned qualified slot and bound receipt before comparative inference; it does not
interpret a receipt or attest the host's numerical PASS. Complete vector/active-state
and independent transaction checks still belong to the native adapter.

The analyzer uses sum-over-sessions per root, paired root resampling, all fixed
contrasts and a declared family correction. The M interaction is separately
specified. Mechanism grids and small pilots are descriptive; do not apply natural
population intervals to deliberately chosen offsets. Unknown cost components stay
null, and partial coverage is not a total. Failed versions and outcomes remain.

These tools never initialize a GPU or launch a model. Native source integration,
actual compile/ABI qualification, zero-forward admission and GPU measurements are
NOT_RUN in this authoring package. Synthetic tests are not experimental findings.
