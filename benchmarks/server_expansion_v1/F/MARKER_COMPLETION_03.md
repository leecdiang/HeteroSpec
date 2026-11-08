# Preserve the graph-name failure; observe the actual backend marker

All six native EOG diagnostics completed and passed their requested full-vector,
active-state/frontier and transaction comparisons. The completion then correctly
stopped at the actual loop4 projection gate. No formal timing was admitted.

The original name-based checker expected `hs_backend_loop4_...`. Llama model
callbacks rename final projection tensors to names such as `Qcur-*`, `Kcur-*`
and `ffn_*`; the packed implementation retains its named internal batch tensor.
The actual backend does not dispatch by that display name: it tests the private
`op_params[HS_LOOP4_MARKER_SLOT]` marker through `hs_loop4::marked`.

The old native receipts did not record that field. Static source reasoning alone
does not complete the missing observation. `build_marker_observer.py` therefore
relinks the exact unchanged numerical archives with one heavy-only metadata
extension: actual marker predicate/raw value/expected value on scheduled graph
nodes. Clean callback behavior, numerical/control rules, original formal
executables and independent reference remain unchanged. This is a generic
observer adaptation, not an arithmetic recipe or model-name exception.

The new epoch must compare an observer-heavy/clean request and the original
formal binary's clean request for every one of the six paths. It uses the same
independent R reader for all requested vectors and committed/terminal states,
checks actual marker/packed descriptors and q4 negative controls, and retains
every failure. A generation cap8 probe remains k3/physical-q4/reserve4; it is not
M2 physical-q8 verification. The observed backend marker must be present where
the source's supported Q8/F32 wide projection predicate applies.

`validate_prior.py --validate-retained-only` first revalidates original complete
job/build/launch/module/profile/source bindings and every consumed original
natural/geometry operand. It cannot execute a new model forward and grants no
new native eligibility. Completed EOG evidence is rechecked separately, without
replaying those native requests. Both earlier gate failures remain distinct
from completed byte comparisons. Only the actual observer/formal bridge and
remaining native negative gates can complete the new qualification epoch.

The first new offline audit retained a path-adapter failure: it assumed every
ledger job still belonged to qualification-01, while completed EOG jobs now live
in qualification-complete-02. `validate_prior_v2.py` uses the actual owned native
epoch, permits only the two recorded predecessor directories, and checks every
real job/build/launch binding. The failed audit remains; no native request was
executed or replayed by that error or its repair.
