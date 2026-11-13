# Bibliography verification

Checked 2026-11-11. All 16 existing citation keys correspond to identifiable primary sources. This audit verifies identity and metadata; it does not imply full-text verification of every substantive claim in the related-work section.

## Source-by-source identity checks

| Key | Primary record | Result |
|---|---|---|
| `leviathan2023` | <https://proceedings.mlr.press/v202/leviathan23a.html> | Authors, title, ICML 2023, PMLR volume 202 and pages 19274–19286 agree. |
| `chen2023` | <https://arxiv.org/abs/2302.01318> | All six authors, title, year and DOI agree. |
| `thinkingmachines` | <https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/> | Official suggested citation explicitly credits Horace He and Thinking Machines Lab and supplies the DOI. Changed type to `article` and added its named publication, Connectionism. |
| `llm42` | <https://arxiv.org/abs/2601.17768v2> | Four authors, title and 2026 date agree. Version 2 is the January 30 revision. |
| `corun` | <https://arxiv.org/abs/2608.14376> | Seven authors, title, identifier and 2026 date agree with the primary arXiv search record. |
| `vosti` | <https://arxiv.org/abs/2609.38981> | Five authors, title, identifier and 2026 date agree with the primary arXiv search record. |
| `qwen3` | <https://arxiv.org/abs/2505.09388> | Title, first author An Yang, year and identifier agree. |
| `llama3` | <https://arxiv.org/abs/2407.21783> | Title, first author Aaron Grattafiori, year and identifier agree with the current record. |
| `smol` | <https://arxiv.org/abs/2502.02737> | Title, first author Loubna Ben Allal, year and identifier agree. |
| `apps` | <https://arxiv.org/abs/2105.09938> | Listed authors, title and year agree; the primary record identifies NeurIPS 2021. Added its arXiv-issued DOI. |
| `math` | <https://arxiv.org/abs/2103.03874> | Listed authors, title and year agree; the primary record identifies NeurIPS 2021. Added its arXiv-issued DOI. |
| `records` | <https://github.com/leecdiang/HeteroSpec> | Internal companion repository audited at main `701079f265c0ff8fd05d43fbc2d8d5054a711e1b` and additional result tips. The citation points to the repository as a whole; the supplement binds individual experiments to their immutable commits, including results on separate branches. |
| `liu2026heterospec` | <https://aclanthology.org/2026.acl-long.589/> | All five authors, title, proceedings, July 2026, pages 12930–12947 and DOI agree with the Anthology's own BibTeX. This is Liu et al.'s separate work, not the present repository's prior manuscript. |
| `taming` | <https://arxiv.org/abs/2609.11356> | Four authors, title, identifier and 2026 date agree with the primary arXiv search record. |
| `loop4code` | <https://github.com/amiller/llama_reproducible/commit/f0dafdbd9dba40bd0e596f74f3da5f592900fca4> | The fixed commit exists, names Andrew Miller as author, and contains the referenced deterministic quantized implementation. Replaced a GitHub handle with the verified personal name and refreshed the access date. |
| `gsm8k` | <https://arxiv.org/abs/2110.14168> | All twelve listed authors, title, year and DOI agree. |

## Retrieval qualifications

The current HTML pages for CoRun, Vosti and Taming returned `DisabledError` through direct opening, including version-specific URLs. A subsequent primary-source search returned their arXiv records with complete author lists, titles, dates and abstracts. These records support the metadata checks above; no third-party summary was used as the authority. Their full texts were not newly read during this bibliography audit.

The `llama_reproducible` commit metadata and complete fixed-commit README were retrieved with the GitHub connector. Its README limits its tested hardware/software configuration and records a large prefill cost for one model. Any related-work comparison should remain about the actually reconstructed execution path; it should not imply that this external repository generally attains fast portable inference.

## Actual changes

Only `source/references.bib` was changed in this audit. All 16 citation keys were preserved, and no literature item was removed. Changes were the Thinking Machines publication fields, APPS/MATH DOI fields, the companion-repository description, and Andrew Miller's name plus the access date for the public implementation. An initial fixed-main URL was returned to the repository homepage after checking that the evidence also includes separate result branches; the supplement supplies the actual immutable bindings.

The manuscript's own experiment claims must remain linked through the supplementary evidence map to the immutable source records. Existence of a citation is not evidence for an unrelated performance number or a stronger determinism guarantee.
