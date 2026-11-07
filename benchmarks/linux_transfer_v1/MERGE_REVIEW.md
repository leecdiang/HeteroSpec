# Reviewed integration, verified 2026-11-07

Before this Linux PR the interrupted author-authorized integration had already
persisted. It was re-read from GitHub before continuing; no merge was repeated.

| Reviewed tip PR | Original scientific tip | Main merge |
|---|---|---|
|195 RTX phase1|873d16712fbf3bc04f54e9b3753515c5dbebb60f|f2567e2c9a845df005fb40142d2b0e56619ce864|
|194 B570 phase1|0575a34a88acff8298191e172205bf8726fe4174|300feac85961098c3b6f3e19297b22d79d03f09e|
|163 B570 Llama|10a70566ce01ab707dbdcc57d8270c1434088f07|c8f63598304a8aca493d9b6f3567d7951104c817|
|162 CUDA Llama history|scientific/delivery history preserved in PR|cfc9edf4582bb3c02885c9171a2ab2635bf19588|

Tip merges retain ancestor experiments. Open ancestor PR UI status is not a reason
to merge them back into frozen parent branches. No need to recreate experimental
commits to make all old PR cards say merged.

The two hosts had colliding result/build names. Main is RTX-oriented; the complete
B570 original tree is preserved at `platforms/b570_snapshot/` (tree
3613fd0ff4f0cbec904d24a586ae6f4e36a231d5). CUDA reference-history conflicts were
preserved in `platforms/rtx_reference_snapshot`. Use detached worktrees at scientific
tips for exact historical replay, not the mixed integration root as a new executed
runtime. `platforms/README.md` explains the first namespace resolution.

Unqualified generic enforcement/all-veto, masked-MMA and tiny CPU-only prototypes
(#179/#181/#182/#183 and associated planning) are not adopted as production methods.
An older paper draft is not allowed to overwrite the latest separately delivered
arXiv source. This PR adds Linux study files only; it changes no prior result,
reference, release, manuscript or access setting.
