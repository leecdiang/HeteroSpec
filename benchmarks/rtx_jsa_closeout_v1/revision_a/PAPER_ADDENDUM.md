# Paper addendum: RTX held-out reference and length transfer

## Registered scope

We completed one finite RTX study under PR140 and the prospectively authorized natural-source/worker-accounting amendment. The platform was an NVIDIA GeForce RTX 5070 Ti Laptop GPU (12,227 MiB reported, driver616.92). The execution retained PR104's three-family k3 resident HTTP contract: Q8_0 models, F16 KV, context1024, target UB4/draft UB1, original PQ/QB mask3, non-flash primary attention, serial reference R UB1, seed123 greedy and EOG/cap128. Primary implementation and observer semantics were frozen before held-out selection; execution is pinned to `87570e6ac4c3f5060b5086969dfc5214e7b17da2`.

The sealed panel comprised 12 natural inputs per family, four in each actual formatted-token stratum 64–192, 256–448 and 640–832. The approved source addition consisted of the 117 original CodeContests validation descriptions at snapshot `802411c3010cb00d1b05bad57ca77365a3c699d6`, with source attribution and CC BY 4.0 non-code licensing retained. Selection followed the frozen task/snapshot SHA256 ordering after project exposure exclusion; tasks were not concatenated, padded, repeated or truncated to manufacture length. The 36 family/input cells represented 21 distinct tasks. E1 reached 33 cells covering 20 distinct tasks before the registered Llama family stop.

Short inputs were exclusively GSM8K math, and medium/long inputs exclusively CodeContests code. Thus domain and length are confounded, and the stratum contrasts cannot establish a causal length effect. Cross-family task reuse does not create independent tasks. The study evaluates finite deployed-reference fidelity and bounded-request cost; it does not establish training-set novelty, task-solution accuracy or 8K/32K context transfer.

## Reference and mechanism transfer

Qwen and SmolLM2 qualified on all 12 inputs. Independent CPU reconstruction verified complete endpoint IDs/EOG/length/terminal semantics, heavy/count agreement, full requested decision-vector ownership, raw mask visibility, PQ/QB matched-prefix vector and canonical causal-trace agreement, pending/KV reconciliation receipts and actual q>1 verification witnesses. First/middle/last target-layer traces observed continuation q values1–4 for both families, with visible keys reaching938 for Qwen and924 for SmolLM2. Natural early-EOG cases remained in the panel.

Llama failed on its first long input, CodeContests/valid/108, with737 formatted prompt tokens. PQ and QB agreed with one another in full vectors, canonical causal trace and output, while both diverged from deployed R at zero-based output index81; all corresponding outputs reached128 tokens. Heavy/count pairs were stable. The remaining three Llama inputs and all Llama cost slots remained NOT_RUN. The observed Llama continuation widths were1,2,4; q=3 was unobserved. This is a deployed-reference transfer counterexample, without an identified numerical root cause or a claim that the QB layout alone caused the discrepancy. No successful-subset timing estimate is reported.

The single stronger comparator, NATIVE_FAST, failed numerical admission for SmolLM2 and Llama on the old calibration input GSM8K/test/111, first differing at indices8 and22. Qwen passed both old inputs but failed held-out GSM8K/test/70 at index68. All three families therefore lack qualified FAST timing. These observed counterexamples complete the prescribed comparator disposition while leaving the qualified stronger-baseline performance comparison unavailable.

## Cost result and interpretation

The two qualified families each completed all12 inputs × four sessions × four fresh single-layout arms R/PQ_A/PQ_B/QB. Every worker performed one separately charged identical-input warmup followed by one measurement. The original resident HTTP clock included request encoding/submission through response parsing and endpoint validation; model load, warmup, file hashing and disk writes were separate. Timed counts mode included no heavy observer writes or added synchronization. PQ_A/PQ_B used identical implementations with independent invocations. The primary ratio was QB divided by the within-block arithmetic mean of the two PQ times, aggregated in log space with equal input/session weights.

| Family | QB / dual PQ | Layout reduction | Max input A/A imbalance | Four session ratios | QB / R | Disposition |
|---|---:|---:|---:|---|---:|---|
| Qwen | 0.967781 | 3.2219% | 4.7781% | 0.975669, 0.960604, 0.967773, 0.967138 | 0.560577 | Noise-limited incremental layout result |
| SmolLM2 | 0.930056 | 6.9944% | 1.5014% | 0.928001, 0.929086, 0.931868, 0.931273 | 1.007007 | Supported finite-panel layout gain |
| Llama | — | — | — | All timing NOT_RUN | — | Reference counterexample |

The registered engineering screen required a reduction exceeding max(2%, maximum input-aggregate A/A imbalance) and a QB advantage in every session aggregate. SmolLM2 passed; Qwen did not clear its A/A threshold despite all four session aggregates favoring QB. QB was not faster in8/48 Qwen blocks and0/48 SmolLM2 blocks, with all blocks retained. SmolLM2's QB remained0.7007% slower than R overall, while dual PQ/R was1.082739. Its representation gain therefore did not produce a complete-request speedup over R. Qwen's QB/R was0.560577 and dual PQ/R0.579239, distinct from its noise-limited incremental layout estimate. Four sessions support these finite descriptive results, without a population confidence interval or request bootstrap.

## Audit and bounded completion

The final reconstruction accounts for509 native workers and1,018 completed requests: calibration24/48, E1 101/202, and E2 384/768 (384 warmups plus384 measurements). All1,776 request and888 worker slots remain enumerated, including758 and379 NOT_RUN slots respectively. All exits and lifetimes were verified, with no watchdog failure or unfinished charged request. Owned native time was6,962.350772 seconds; the maximum worker lifetime was44.207315 seconds. Original historical charges, failures and UUIDs remain separate and unchanged.

Calibration's append-offset metadata defect is retained with complete reconstructible byte streams. A heavy-only correction and the canonical causal-trace interpretation were frozen before held-out selection; E1 used strict offsets, without reconstruction recovery. Canonical equality excludes only an unused draft sampler return ID; actual proposal IDs and all raw returns remain available. The CPU verifier's integer/NumPy batching was checked exactly against the preserved scalar audit and operates outside native execution/the request clock. Post-execution authentication and hashing rechecked all7,729 frozen file pins.

Complete raw vectors/masks, native traces, requests/responses, identities, all slots, warmups, cleanup receipts, input/block/session contrasts, exact estimators and access/hash manifests accompany [RESULT.md](RESULT.md) and [RAW_ACCESS.json](RAW_ACCESS.json). Candidate code, tolerance, inputs and matrix size were not changed after held-out outputs. This closes the registered RTX matrix with a mixed disposition and without additional hardware/model/k sweeps or automatic manuscript/arXiv submission.
