# CPU-only reproduction and resume

Require Python3.12, NumPy2.2.6 and Matplotlib3.10.7 (requirements.txt). Create a new isolated analysis checkout/copy; never write into old experiment roots. The original RTX ZIP and already restored experiment/B data are external immutable inputs. Required archive identities and selected object hashes are in INPUT_BINDINGS/UNIT_MANIFEST. Also provide the existing Phase2 source root and identity-bound cd57ec… ZIP. No model/runtime restore or native smoke check is required or authorized.

At the new study directory run:

```powershell
python resume.py --archive 'PATH_TO/HeteroSpec_RTX_闭环_完整记录.zip' --restored 'PATH_TO/closeout-archive-verify' --phase2 'PATH_TO/rtx-consistency-phase2' --phase2-archive 'PATH_TO/HeteroSpec_RTX_第二阶段_完整记录.zip'
```

Replace placeholders with actual roots; restored root contains experiment/runs/b/RECORDS.json. This driver invokes only identity.py, analyze.py, verify.py and handoff.py with the current Python interpreter. It imports no old execution code. Stage checkpoints include script/input-root identity and every required output hash; resume reuses only complete verified units. --force-cpu forces CPU recomputation, never a model request. Old files are read only, new products remain alongside these scripts. If paths change, recompute in the new copy rather than calling a native runner. Checkpoint absolute roots are local-only and excluded from public delivery.

New bootstrap:PCG64(seed20261008), common10000×24 task-index draws, exp(mean(log ratios)), NumPy linear/type7 .025/.975. Repeats are compressed as four-cost medians first. verify.py re-reads raw and uses Decimal medians plus manual sorted linear interpolation. Historical Python random seed20261005/4000/sorted99,3899 is separately checked against generated/B_RESULTS; no old function is imported. Sources and archive hashes are rechecked after analysis.

Figures are SVG glyph paths and PDF embedded TrueType, with PNG companions. Recreating PDF/SVG may change metadata bytes (for example PDF creation timestamps); all qualification/absolute-cost/pair/statistical tables are the semantic reproduction targets, not incidental graphics timestamps. Use PUBLIC_FILES.json to verify original delivered bytes. RAW_COSTS is a CPU-derived whitelist of old costs/identities, not raw model arrays or bulk telemetry. The original content-addressed ZIP remains the authoritative complete input.

Publication is separate: create an additive branch from actual main, add only benchmarks/rtx_pr62_cpu_reference_closeout_v1/, create a new Draft PR and fresh-fetch/readback all new blobs. Keep previous PRs unmerged. No scientific source or manuscript modification is part of reproduction.
