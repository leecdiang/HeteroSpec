# Manuscript entrypoint

The current source is [arxiv_v4_candidate](arxiv_v4_candidate/README.txt). It is based on the complete author-supplied v3 package, with the subsequent RTX/B570 evidence, source reconciliation, and contribution-led 2026-10-21 revision. It has not been submitted to arXiv or a journal.

```sh
cd paper/arxiv_v4_candidate
python -B scripts/build.py
```

The reviewed local PDF has 23 pages (13 article/references + 10 supplement), ten editable figures, 511 reported-value/source checks and 36 distinct regression/mutation tests. PDF SHA256: `111010ab9fa0f69892228cc9a4ea4318890494d0b009d49ad69f5fea5834f3ca`.

The arXiv upload package is separately filtered from the author repository: it contains no private peer-review/probability memos, build logs or binary runtime assets. Its 86 members were extracted and rebuilt; removing the ancillary folder still produces the same PDF. Editable TeX tables reside under `tables/`, not `anc/`.

The [repository synthesis](../docs/research/heterospec_synthesis_20261021/REPOSITORY_SYNTHESIS.md) distinguishes existing results, retrospective derivations and prospective hypotheses. The [platform closeout index](../docs/closeout_20261021/README.md) is DESIGN_ONLY and not execution-ready. Exact new inputs, execution identity, budgets and authorization must be resolved before running it.

Current author QA is `anc/review_round3/QA_FINAL.json`; earlier review records are preserved as history. Tests reconstruct saved report data; they are not independent native-model or full raw-logit replication. No previous experiment, failed result, CPU8/F0 status or budget is changed by this paper revision.
