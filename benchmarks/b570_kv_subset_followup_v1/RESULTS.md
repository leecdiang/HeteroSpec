# PR103 B570 boundary-0 KV subset results

Status: COMPLETE_FINITE_STATE_INTERVENTIONS. Control gate: PASS. PR remains Draft. No manuscript, baseline, model, inference runtime, PR101 archive or PR102 changes.

PR101 source commit: 26706c9fb4818ec3465e45acea029c4ab88a390f. Prospective freeze commit: dd33b24abebc335d39f3b63b4e7beff86bdcf934. Exactly 192/192 native request starts; 4104.092/21600 cumulative owned-process seconds; no scientific retries. Expected controls: 32; expected crosses: 160.

## Controls

A is the historical UB512 one-call prefill state; B is the historical partitioned prefill state. Both directions execute in the same clean UB512 receiver and retain recipient initial logits.
Completed 32/32. EMPTY preserves recipient KV; ALL imports all donor K/V while retaining recipient initial logits. Each endpoint comparison includes all token IDs, EOG flags, length, terminal ID, stop reason and cap. The native auditor checks clean UB512, no extra forward, exact KV/logits reserialization, continuation positions and same-PID memory.

| Task | Direction | Selector | Repeat 0 | Repeat 1 |
|---|---|---|---|---|
| GSM8K/test/1011 | A->B | ALL | PASS | PASS |
| GSM8K/test/1011 | B->A | ALL | PASS | PASS |
| GSM8K/test/1011 | A->B | EMPTY | PASS | PASS |
| GSM8K/test/1011 | B->A | EMPTY | PASS | PASS |
| GSM8K/test/1248 | A->B | ALL | PASS | PASS |
| GSM8K/test/1248 | B->A | ALL | PASS | PASS |
| GSM8K/test/1248 | A->B | EMPTY | PASS | PASS |
| GSM8K/test/1248 | B->A | EMPTY | PASS | PASS |
| GSM8K/test/1249 | A->B | ALL | PASS | PASS |
| GSM8K/test/1249 | B->A | ALL | PASS | PASS |
| GSM8K/test/1249 | A->B | EMPTY | PASS | PASS |
| GSM8K/test/1249 | B->A | EMPTY | PASS | PASS |
| GSM8K/test/831 | A->B | ALL | PASS | PASS |
| GSM8K/test/831 | B->A | ALL | PASS | PASS |
| GSM8K/test/831 | A->B | EMPTY | PASS | PASS |
| GSM8K/test/831 | B->A | EMPTY | PASS | PASS |

## Subset matrix

All selectors and order were fixed before inference. Positions are prefix [0,128) and tail [128,N); transposed V is addressed feature-major. Selected bytes count the selector extent; changed bytes count byte values differing from recipient. Native exact reserialization verifies actual changed bytes. All endpoint IDs and per-repeat fields are in ANALYSIS.json.

D denotes no endpoint change from EMPTY. The clean-recipient design cannot distinguish a separate A restoration mechanism from recipient-equivalent D. On stable tasks, donor/recipient endpoint overlap is recorded without asserting a donor effect. B requires a distinguishable historical full-cross endpoint. C is a valid third trajectory, not a failure.

| Task | Selector | Direction | Selected bytes | Changed bytes | Repeat 0 | Repeat 1 |
|---|---|---|---:|---:|---|---|
| GSM8K/test/1011 | KV_early | A->B | 6225920 | 3069455 | C | C |
| GSM8K/test/1011 | KV_early | B->A | 6225920 | 3069455 | D | D |
| GSM8K/test/1011 | KV_late | A->B | 6225920 | 3500465 | C | C |
| GSM8K/test/1011 | KV_late | B->A | 6225920 | 3500465 | C | C |
| GSM8K/test/1011 | KV_layer0 | A->B | 778240 | 236445 | C | C |
| GSM8K/test/1011 | KV_layer0 | B->A | 778240 | 236445 | D | D |
| GSM8K/test/1011 | KV_middle | A->B | 12451840 | 6965265 | D | D |
| GSM8K/test/1011 | KV_middle | B->A | 12451840 | 6965265 | C | C |
| GSM8K/test/1011 | KV_prefix128 | A->B | 16777216 | 9202707 | C | C |
| GSM8K/test/1011 | KV_prefix128 | B->A | 16777216 | 9202707 | C | C |
| GSM8K/test/1011 | KV_tail128 | A->B | 8126464 | 4332478 | C | C |
| GSM8K/test/1011 | KV_tail128 | B->A | 8126464 | 4332478 | C | C |
| GSM8K/test/1011 | K_all | A->B | 12451840 | 6549519 | C | C |
| GSM8K/test/1011 | K_all | B->A | 12451840 | 6549519 | C | C |
| GSM8K/test/1011 | K_layer0 | A->B | 389120 | 113167 | C | C |
| GSM8K/test/1011 | K_layer0 | B->A | 389120 | 113167 | C | C |
| GSM8K/test/1011 | V_all | A->B | 12451840 | 6985666 | C | C |
| GSM8K/test/1011 | V_all | B->A | 12451840 | 6985666 | C | C |
| GSM8K/test/1011 | V_layer0 | A->B | 389120 | 123278 | C | C |
| GSM8K/test/1011 | V_layer0 | B->A | 389120 | 123278 | D | D |
| GSM8K/test/1248 | KV_early | A->B | 5275648 | 2632511 | D | D |
| GSM8K/test/1248 | KV_early | B->A | 5275648 | 2632511 | D | D |
| GSM8K/test/1248 | KV_late | A->B | 5275648 | 2930851 | C | C |
| GSM8K/test/1248 | KV_late | B->A | 5275648 | 2930851 | B | B |
| GSM8K/test/1248 | KV_layer0 | A->B | 659456 | 235553 | B | B |
| GSM8K/test/1248 | KV_layer0 | B->A | 659456 | 235553 | D | D |
| GSM8K/test/1248 | KV_middle | A->B | 10551296 | 5819298 | D | D |
| GSM8K/test/1248 | KV_middle | B->A | 10551296 | 5819298 | D | D |
| GSM8K/test/1248 | KV_prefix128 | A->B | 16777216 | 9108944 | D | D |
| GSM8K/test/1248 | KV_prefix128 | B->A | 16777216 | 9108944 | B | B |
| GSM8K/test/1248 | KV_tail128 | A->B | 4325376 | 2273716 | D | D |
| GSM8K/test/1248 | KV_tail128 | B->A | 4325376 | 2273716 | B | B |
| GSM8K/test/1248 | K_all | A->B | 10551296 | 5515640 | D | D |
| GSM8K/test/1248 | K_all | B->A | 10551296 | 5515640 | B | B |
| GSM8K/test/1248 | K_layer0 | A->B | 329728 | 113464 | B | B |
| GSM8K/test/1248 | K_layer0 | B->A | 329728 | 113464 | D | D |
| GSM8K/test/1248 | V_all | A->B | 10551296 | 5867020 | D | D |
| GSM8K/test/1248 | V_all | B->A | 10551296 | 5867020 | B | B |
| GSM8K/test/1248 | V_layer0 | A->B | 329728 | 122089 | B | B |
| GSM8K/test/1248 | V_layer0 | B->A | 329728 | 122089 | B | B |
| GSM8K/test/1249 | KV_early | A->B | 5341184 | 2666977 | D | D |
| GSM8K/test/1249 | KV_early | B->A | 5341184 | 2666977 | D | D |
| GSM8K/test/1249 | KV_late | A->B | 5341184 | 2989199 | D | D |
| GSM8K/test/1249 | KV_late | B->A | 5341184 | 2989199 | D | D |
| GSM8K/test/1249 | KV_layer0 | A->B | 667648 | 235968 | D | D |
| GSM8K/test/1249 | KV_layer0 | B->A | 667648 | 235968 | D | D |
| GSM8K/test/1249 | KV_middle | A->B | 10682368 | 5948828 | D | D |
| GSM8K/test/1249 | KV_middle | B->A | 10682368 | 5948828 | D | D |
| GSM8K/test/1249 | KV_prefix128 | A->B | 16777216 | 9156115 | D | D |
| GSM8K/test/1249 | KV_prefix128 | B->A | 16777216 | 9156115 | D | D |
| GSM8K/test/1249 | KV_tail128 | A->B | 4587520 | 2448889 | D | D |
| GSM8K/test/1249 | KV_tail128 | B->A | 4587520 | 2448889 | D | D |
| GSM8K/test/1249 | K_all | A->B | 10682368 | 5621016 | D | D |
| GSM8K/test/1249 | K_all | B->A | 10682368 | 5621016 | D | D |
| GSM8K/test/1249 | K_layer0 | A->B | 333824 | 113565 | D | D |
| GSM8K/test/1249 | K_layer0 | B->A | 333824 | 113565 | D | D |
| GSM8K/test/1249 | V_all | A->B | 10682368 | 5983988 | D | D |
| GSM8K/test/1249 | V_all | B->A | 10682368 | 5983988 | D | D |
| GSM8K/test/1249 | V_layer0 | A->B | 333824 | 122403 | D | D |
| GSM8K/test/1249 | V_layer0 | B->A | 333824 | 122403 | D | D |
| GSM8K/test/831 | KV_early | A->B | 4358144 | 2242683 | B | B |
| GSM8K/test/831 | KV_early | B->A | 4358144 | 2242683 | C | C |
| GSM8K/test/831 | KV_late | A->B | 4358144 | 2464632 | D | D |
| GSM8K/test/831 | KV_late | B->A | 4358144 | 2464632 | C | C |
| GSM8K/test/831 | KV_layer0 | A->B | 544768 | 246601 | B | B |
| GSM8K/test/831 | KV_layer0 | B->A | 544768 | 246601 | C | C |
| GSM8K/test/831 | KV_middle | A->B | 8716288 | 4879928 | B | B |
| GSM8K/test/831 | KV_middle | B->A | 8716288 | 4879928 | D | D |
| GSM8K/test/831 | KV_prefix128 | A->B | 16777216 | 9187404 | B | B |
| GSM8K/test/831 | KV_prefix128 | B->A | 16777216 | 9187404 | D | D |
| GSM8K/test/831 | KV_tail128 | A->B | 655360 | 399839 | B | B |
| GSM8K/test/831 | KV_tail128 | B->A | 655360 | 399839 | D | D |
| GSM8K/test/831 | K_all | A->B | 8716288 | 4641521 | C | C |
| GSM8K/test/831 | K_all | B->A | 8716288 | 4641521 | C | C |
| GSM8K/test/831 | K_layer0 | A->B | 272384 | 118160 | C | C |
| GSM8K/test/831 | K_layer0 | B->A | 272384 | 118160 | C | C |
| GSM8K/test/831 | V_all | A->B | 8716288 | 4945722 | C | C |
| GSM8K/test/831 | V_all | B->A | 8716288 | 4945722 | C | C |
| GSM8K/test/831 | V_layer0 | A->B | 272384 | 128441 | B | B |
| GSM8K/test/831 | V_layer0 | B->A | 272384 | 128441 | C | C |

## Null results and failures

Validated subset endpoint classes: {'D': 76, 'C': 54, 'B': 30}. Structural nulls: 0; changed-byte endpoint nulls: 76.

Scientific failed slots: 0. Not-started slots: 0. Every failure and incomplete slot remains in ANALYSIS.json and the raw run directory. Infrastructure recovery failures are separately retained in execution/TOOLING_FAILURES.json.

## Evidence and limitations

Raw evidence is retained in C:/hs/b570-kv-subset-v1. Archive and fresh restoration receipts are reported separately; existence of these summary files does not certify restoration. No new-input validation, paid-cost claim, or speedup claim is made. Original R_stock qualification failures and NULL qualified costs remain unchanged.

## Local archive restoration

Final archive: C:\hs\b570-kv-subset-v1-archive\evidence-final.zip (2065535845 bytes), SHA256 2e6114e9a3019b71d7e7a1ac55dd483ee8191ce6fcb99310fcbeda588992b0b1. Fresh restored root: C:\hs\b570-kv-subset-v1-restored-final. All 2561 files match and CPU reanalysis is identical.

Manifest and restoration certificate: execution/final-seal/ARCHIVE_MANIFEST.json and execution/final-seal/RESTORATION.json. PR101 baseline source/runtime and model remain external byte-pinned prerequisites; immutable absolute FREEZE paths are retained and restored input copies are checked separately. Remote publication of the raw archive was not performed. The initial snapshot and its operation logs are retained; the final seal is taken after those logs close.
