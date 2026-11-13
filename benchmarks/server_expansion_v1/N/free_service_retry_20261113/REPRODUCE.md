# Reproduction and evidence boundaries

Start with [README](README.md), [status](STATUS.json), [initial prospective plan](../free_service_20261113/PLAN.md), [explicit ABI successor](RETRY_PLAN.md) and [resource review](RESOURCE_AND_ABI_REVIEW.md). The copied PLAN/MANIFEST_PROPOSED in the successor source tree are historical; the executed successor MANIFEST approves43 and records the extra charged failure. No existing STATE is a restart authorization. This grant has0 model requests and0 deployments remaining.

## Public, CPU-only replay

From a checkout of the immutable result commit, run these standard-library checks. They make0 model calls, GPU contexts and placement actions:

```bash
python3 benchmarks/server_expansion_v1/N/free_service_retry_20261113/public_replay.py \
  --evidence benchmarks/server_expansion_v1/N/free_service_retry_20261113/EVIDENCE \
  --out /tmp/free-service-public-replay-fresh.json
node benchmarks/server_expansion_v1/N/free_service_retry_20261113/independent_statistics.js \
  benchmarks/server_expansion_v1/N/free_service_retry_20261113/EVIDENCE/PUBLIC_TEXT_PACKET.tar.gz \
  /tmp/free-service-statistics-fresh.json
```

Use fresh output names. Public replay verifies every text member against its indexed SHA256/size; inherited failure charges; byte-identical old/new window; real sampled-token→parser→wire→history→next-canonical chain; physical input/row receipts; and equal/different recorded geometry. The Node implementation independently reconstructs paired round/root and ratio-of-totals results from response/reset receipts. It does not treat rounds as independent roots. Packet members are privacy transformed; [mapping](EVIDENCE/PRIVACY_TRANSFORM.json) records original and published hashes, never claims transformed JSON equals original private bytes.

The packet contains353 text members and0 raw tensor bytes. Its archive member index points to original private artifacts. A certificate or matching index is **not** a rerun of GPU or independent validation of unavailable original numeric bytes. Supplementary release/preservation/cost evidence was produced after the core private archive and is published separately; the private archive's index is inside the text packet.

## Private original-byte replay

Authorized maintainers can locate the original and successor directories, config, frozen images and actual raw archive using the private local/server handover. The core archive has6,697 regular files arranged as `original/` and `successor/`, SHA256 `af05448c7a84aee6d5af47506b82f1606acae1bb0b403bbf5c598c4eaead8e87`. It retains actual source/build epochs, raw vectors/KV, real producer/request/dispatch receipts, all original failure data and immutable STATE/ledgers. The successful reference trees exist once under original/R and original/REFERENCE; successor reference aliases are intentionally not dereferenced/duplicated in the archive. Restore aliases to those two archived directories in a separate restoration area; never overwrite active/historical server paths or STATE.

The std-only `raw_cpu.cpp` scanner plus a fresh raw manifest can recheck all original F32/F16 finiteness and full-vector first-index greedy, with complete byte comparisons and retained-prefix tensor strides independently replayed by closeout.py. Use a fresh analysis area/output, and remap recorded paths to the authorized restoration. Its raw scan includes128 vectors from the incomplete failed request; those do not become a passed consumer/episode. Complete original comparison uses full bytes, not SHA equality, argmax alone or tolerance. [Recorded audit](EVIDENCE/FINAL_AUDIT.json) and [full archive readback](EVIDENCE/ARCHIVE_READBACK.json) give exact counts and limitations. The complete261-case qualification suite remains NOT_RUN.

## Rebuild without execution

Build receipts preserve every command, flags, archive identity, generated source digest and resulting image SHA. Original full reference SHA is `111401574d53c534e3a39cac75785ae5ae5fa9a61b44fc7ada989a96305f4723`; complete reference/loop4 source closures and original historical assets were rechecked at admission and closeout. Do not substitute excerpts, a newer runtime, Windows DLLs, another GGUF or different parser objects. Restore the original source/build bindings from the inherited native-chain material and the fixed Linux transfer source acquisition record. CUDA12.5 and GCC11.4 were used; no drivers or upstream dependencies were upgraded.

Initial GPU R image SHA `9b6c57fc3720b8788b9e2ee20bc21845285e972af52c88fce4aed65c3c88919e`; failed candidate `639962ed2293387a248bc8252d80a059809e73e5993ca6f41c61a3616e349c33`; corrected candidate `615cdc1afcc7d8956799a15dc1844549eade83de426cc7698ad1619129b89f85`. Pinned frontend objects require R headers for producer.cpp; native/KV use loop4 headers and unchanged numerical archives. CPU consumer replay links CPU-only core symbols and is deliberately separate from the actual GPU numerical images.

build.py compiles/links only; do not execute the GPU ELF as a self-test. Actual launcher binding, sealed image, model FD, real kernel cgroup, authenticated peer, specific device, lease and durable budget must all be admitted under a **new separately approved** protocol before any future model execution. No receipt, reproduction instruction, old ledger or unused rows extends this exhausted grant. Do not restart either historical controller or remove a lock/STATE. The current controllers and GPU workers have already completed and released their domains/locks.
