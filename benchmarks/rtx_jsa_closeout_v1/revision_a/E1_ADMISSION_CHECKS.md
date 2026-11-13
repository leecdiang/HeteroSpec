# Complete observer admission before clean timing

The native four-arm implementation, inclusive HTTP clock, model/library identities and numerical rules remain the primary freeze at `e57c38a051f41d506563d3bf594dbdb31e614df2`. No held-out input has been selected or evaluated when this supplementary CPU check is registered.

`PRIMARY_IMPLEMENTATION_FREEZE_V2.json` prospectively pins the complete verification/analysis pipeline before selection. It preserves those native binaries and introduces exact integer-bit batching in the CPU raw auditor. The scalar implementation remains in `audit_raw_scalar_v1.py`; all 24 immutable calibration readouts match exactly, and all F16 bit patterns are independently checked. No NumPy operation is added to the native worker or resident HTTP clock.

In addition to `audit_raw.py`'s strict byte-offset, finite-vector, sample ownership, committed-output and raw-mask checks, execute `verify_complete_capture.py` after E1 and before any E2 worker. It reconstructs the complete requested-row set from every successful native decode's `logits_mask` and requires exactly one captured vector for every such row. This explicitly includes rejected verification rows that were never sampled. It also requires all registered core arm/input workers for each admitted family; an admitted FAST arm has its own complete set.

This implements PR140's existing full-vector requirement. It adds no model requests, numerical tolerance, input choice or candidate change. The 24 immutable calibration workers already pass the complete requested-row reconstruction. Their earlier append-offset metadata failure remains separately reported; no calibration request is retried. E1 uses the prospectively corrected observer and requires valid declared offsets, without reconstruction.

If this mandatory gate fails for an otherwise admitted family, do not launch its timing panel. Preserve the failure and unstarted slots. Numerical/state/placement/reference failures retain the original family and FAST stopping rules. All verification source bytes and this policy are pinned in the execution registration before the first held-out request.
