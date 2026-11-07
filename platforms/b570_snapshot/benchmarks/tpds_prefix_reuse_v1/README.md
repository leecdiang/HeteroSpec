# TPDS follow-up: cache-aligned compatible append

**Status: published experiment design and tested CPU toolkit; native adaptation, GPU qualification and measurements NOT RUN by this publication.**
Date: 2026-11-04. Owner: Chengzhan Li. The arXiv manuscript is a separate artifact and contains none of these proposed results.

## The question that can change the publication decision

Does local attention grouping retain a useful complete-request advantage on unmodified conversational prefix reuse, after comparing it with a caller that both cuts at physical boundaries **and restarts its chunk alignment**?

A positive answer would add application relevance beyond deliberately crossed append cells. A negative answer would show that a simpler caller captures the benefit, and should narrow the claim rather than trigger repeated timing. More passed vectors or an extra device alone cannot settle this question.

## Read and run

1. Read `PROTOCOL.md`, `NATIVE_CONTRACT.md`, `GITHUB_HANDOFF.md` and the platform prompt.
2. Run `python -m unittest -v test_study.py`. These are CPU tests only; 49 passed in the authoring environment.
3. Prepare the native-tokenized public conversation manifest described in `MANIFEST_SCHEMA.md`; do not use the synthetic fixture for science.
4. `python study.py census manifest.json > census.json`
5. `python study.py select manifest.json > panel.json`
6. After the native calibration: `python selector.py calibration.json panel.json > policy.json`; bind the result to the source freeze. `python study.py schedule panel.json > schedule.json`
7. After native execution: `python study.py analyze results.json panel.json > analysis.json`

The toolkit intentionally has no GPU runner. The host agent extends the already-executed native adapters and owns their build, immutable reference, actual memory admission, full vectors, timing and process cleanup. A CPU schedule is not a native execution freeze.

## Two-platform division

RTX continues PR171's packed CUDA implementation. B570 continues PR169's corrected Vulkan candidate. Both first attempt the same target-only Qwen3-8B Q8_0, F16-KV, non-flash, ordinary greedy configuration. They share frozen input IDs and tokenization when feasible; each backend keeps its own numerical reference and separate statistics. Existing k3/k1 histories remain unchanged.

The main comparison is QB, inherited WB-cut, alignment-aware WB-rechunk and a calibration-frozen selector. The selector is deliberately small and may degenerate to one fixed policy. Before any main timing, it must preserve the same full-vector reference.

`RENTAL_GATE.md` states when a third, stronger CUDA GPU would be useful. No rental or paid service is requested by this package.
