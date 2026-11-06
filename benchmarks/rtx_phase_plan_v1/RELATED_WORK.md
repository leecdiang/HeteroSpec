# Scope relative to related work

This implementation targets a fixed, pre-existing numerical reference in a
bounded llama dense-cache deployment. Its evidence is finite native comparison,
not a formal equivalence proof or a new GPU arithmetic implementation.

[Taming](https://arxiv.org/abs/2609.11356) reconstructs reduction behavior,
enforces arithmetic during compiler lowering, and checks compiled kernels.
Here the arithmetic kernels are inherited; the experiment composes their
qualified choices with reference-derived cache extents and phase groups.

[Vosti](https://arxiv.org/abs/2609.38981) specifies deterministic inference and
connects engine/cache reasoning with kernel verification. Its stated guarantee
is broader than the finite, dense, single-sequence scope tested here. A typed
plan, matching metadata or this experiment's byte comparisons do not establish
Vosti's system-level proof.

[LLM-42](https://arxiv.org/abs/2601.17768v2) uses a verifier that replays candidate
tokens under a fixed-shape schedule and rolls back inconsistent work. The
supported clean method in this experiment plans compatible execution before
mutation and performs no online original-reference replay. Ordinary speculative
decoding with the existing draft remains a workload/control, separate from
that numerical consistency mechanism.

Same-context execution, four-column projection, prefix grouping and explicit
contracts are established ingredients. The result must therefore be judged by
its demonstrated composition across phases/structures and by measured complete
cost against SIMPLE. No cross-paper speed comparison is claimed: the numerical
contracts, model deployments and supported features have not been matched.

The three primary arXiv abstracts/version records were checked on 2026-11-06.
