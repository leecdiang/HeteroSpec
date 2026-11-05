# Native integration contract (remaining original-host work)

## Reuse the correct working code, not every new research branch

RTX operator starts from the PR171 candidate source kit and the PR177 working host environment. `stage_sources.py rtx-loop4` retrieves only PR180's baseline stager and three helper headers from a fixed local git commit. It does **not** apply PR179's fail-closed contracts or PR182's always-veto scheduler.

RTX draft starts from the exact PR151 Windows worker and its historical numerical library/deployment. `stage_sources.py rtx-draft` generates UB1/2/4 clean and diagnostic variants. It leaves target context expressions/transaction code and draft output reserve1 unchanged; the callback/readback derivative is separately tested against the unchanged oracle. Do not automatically link it against the PR171 library just because that is newer.

B570 draft starts from recovered PR165 post-adaptation `boundary.cpp`, the original strict R library and qualified F32-activation/p021 candidate path. The old file is normally in the platform's source/build kit, not necessarily the checked-out tree. Preserve the current corrected resource admission; source hashes must come from the authenticated kit/record, not an arbitrary input with a freshly computed matching hash.

## `runner.py` adapter protocol

The binding supplies an argv list, e.g. the original-host Python controller plus a new adapter module. It is invoked once per **logical paired session**:

```
<adapter argv> --session-job /fresh/attempt/job.json --output-dir /fresh/attempt
```

The adapter loads the model pool and creates/resets contexts according to the declared lifecycle. For resident RTX, preserve construction outside the service clock, declared priming/reset history, and scheduled warmup/measurement order. A controller may load version-specific worker processes sequentially; it need not hold all arms on the GPU at once. Preserve or replay the admitted priming history when a worker is restarted, qualify that lifecycle, and record every model load. Do not silently replace resident-reset service with cold context construction inside each request. For fresh Vulkan, fresh contexts remain inside each service, while model loading is outside and separately charged as before.

`session-result.json` contains `attempt_id`, `binding_sha256`, `completed`, `actual_work` (`requests`, `token_rows`, `operators`), and normalized records. Each service record contains its planned slot/root/input/session/period/arm/kind, complete `service_s`, status, endpoint identity, actual numerical profile/source freeze and observed fallback count. Record GPU dispatch triggers in separate diagnostic passes, not fabricated from the planned width.

`binding.json` includes actual file pins, cwd, timeout, reference/profile/candidate identities, input-manifest hash, host resource limits and completed finite qualification. A readiness Boolean is a host record, not a cryptographic attestation. The agent must inspect the native trace/source and retain the matching evidence, not just fill in `true`.

## Existing record normalization

`normalize.py capture` consumes actual request rows and raw samples. Add only the following explicit sidecar fields to each request record after checking the actual slot: `study_cap`, `study_fallback_count`, and for B570 `study_draft_enabled`. The free reference additionally requires `study_reference_received_forced_tape=false` from the actual job construction. Do not obtain free-reference expected tokens from a candidate.

RTX native-root is the request's **target** directory, with initial/ordinary/verify `.f32` files plus the new `state/` captures. B570 native-root is the original payload CAS root; records already contain payload byte lengths/hashes. `normalize.py` checks the raw bytes, not only these hashes.

The trained-model `active_kv.py` profile must pin actual writer source, model and layer mapping, sizes, context and F16 stream/layout. New profiles are not blanket extensions of the tiny-Llama parser. Validate the parser on known actual layouts and sentinel data, and compare canonical values with the independent reference. The bytes do not encode tokens; the native caller trace establishes them. A raw sequence serializer and active KV are different artifacts. Other formats fail explicitly rather than being guessed.

## Separate reference construction

1. Execute unchanged autonomous original R without any candidate trace, with its original prompt/caller/mask and lifecycle.
2. Run the observer derivative and establish its finite correspondence with original R using original available full outputs. Same output reserve, capacity, cap admission, resident history and numerical library.
3. Candidate heavy captures give actual token prefixes. `normalize.py reference-jobs` creates maximal scalar replay paths and estimates their real request/token-row cost. The forced process receives tokens and immutable producer metadata, never candidate logits/KV.
4. Wire `native/replay_path.hpp` into the actual historical observer context. It does not create/reset contexts; the host must do exactly the original lifecycle. Historical prompt caller lengths AND per-caller last-output flags are explicit inputs. Each appended forced token uses scalar continuation with its requested last row.
5. At each needed prefix export already-computed frontier and committed active KV. Normalize each path as `forced_reference_path`. `merge_references.py` rejects inconsistent duplicated prefixes across independent paths.
6. `qualify.py` compares candidate captures with both the autonomous output and forced-prefix values. Do not compare rejected suffix values against an unrelated free-generation prefix. Read the right verification row after trim.

The clean timing adapter must also bridge to heavy execution on the same admitted inputs. Light endpoints alone do not establish hidden-state closure. Final active state/frontier can be exported after the service clock; report that diagnostic cost outside online service. Any state check required for the deployed method is timed online instead.

## Minimal native completion checklist

- Original binaries/weights retained; actual old-R plus observer-R finite bridge.
- Actual physical draft width **and caller widths** observed; output reserve remains1.
- Source derivative and builds pinned; complete DLL/runtime list recorded with path/case collisions checked.
- Trained-model profile and independent free/forced references actually executed.
- Backend-loop4 uses its marked CUDA route, no silently unmarked wide fallback.
- Correct finite resource admission before full panels.
- Dirty padding, future KV writes and reset behavior are investigated only when a real mismatch depends on them; do not claim them universally proven by metadata.

If the adapter discovers a real unsupported native detail, fix or explicitly narrow the **development** configuration, retain the old evidence and refreeze before unseen confirmation. This document delegates engineering, not the right to alter the numerical contract after seeing test outcomes.

## Executing the bridge itself

The launcher accepts `phase=admission` or `bridge` with `status=HOST_READY_BRIDGE`, actual original assets verified and the bounded native entry reviewed. This deliberately does not require the bridge to have passed before running it. Every model trajectory still consumes its reservation. Later qualification/development/main requires `HOST_READY_FINITE_STUDY` and the actual bridge result; main also requires a pre-test freeze. These labels are host assertions tied to retained artifacts, not automated proof or permission to skip inspection.
