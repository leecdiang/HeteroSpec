import json,pathlib,shutil
import argparse
p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);args=p.parse_args()
repo=pathlib.Path(__file__).resolve().parents[2];bench=repo/'benchmarks/rtx_native_bridge_20261026';results=bench/'results';a=json.loads((results/'ANALYSIS.json').read_bytes());out=args.out;out.mkdir(parents=True,exist_ok=True)
lines=['# RTX native reproduction and matched deployment bridge','','**Completed finite campaign:** native recovery/rebuild/replay and all 936 registered formal requests (864 measurements + 72 warmups). No formal technical retry, missing slot, outlier deletion or adaptive extension.','',
'The common new runtime uses the twelve exposed Qwen3 inputs and one RTX 5070 Ti Laptop, with k1/k3 × resident/fresh × PQ_A/PQ_B/QB. All 204 v2 qualification requests pass full endpoint/state/vector and 36-layer layout/placement checks. All outputs also match the historical E2 R endpoints. This is a new service driver, not a claim that its timer or implementation is the historical HTTP E2 contract.','',
'| k | Lifecycle | QB / dual PQ | Reduction | Simultaneous 95% family interval | Largest input A/A | Practical gain established |','|---|---|---:|---:|---|---:|---|']
for c in a['cells']:
 lo,hi=c['simultaneous_family95_interval'];lines.append(f"| {c['k']} | {c['lifecycle']} | {c['ratio']:.6f} | {c['reduction_percent']:.3f}% | [{lo:.6f}, {hi:.6f}] | {100*c['largest_input_AA']:.3f}% | {'YES' if c['practical_gain_established'] else 'NO'} |")
lines+=['','Each primary cell has a Bonferroni-adjusted 98.75% percentile interval, giving nominal 95% family coverage for four registered cells. The paired bootstrap clusters six process sessions and preserves all four cells together. Inputs are fixed, previously exposed examples, not independent runtime sessions.','',
'Established requires upper CI<0.98, point reduction exceeding max(2%,input-aggregate A/A), and improvement in every session. Failure to establish this does not prove zero effect or equivalence. No timing-based input subset is selected.','',
'Within this new stack, the secondary k contrasts favor a larger QB layout effect at k3 in both lifecycles. Individual lifecycle contrasts include unity. The interaction is exploratory; these measurements do not identify CUDA Graph causality or decompose the old E2-versus-service difference.', '', '## Absolute service cost','','| k | Lifecycle | Mean dual PQ (s) | Mean QB (s) | Mean QB−PQ (ms) | Reversed blocks |','|---|---|---:|---:|---:|---:|']
for c in a['cells']:lines.append(f"| {c['k']} | {c['lifecycle']} | {c['mean_PQ_seconds']:.6f} | {c['mean_QB_seconds']:.6f} | {c['difference_ms']:.3f} | {c['block_reversals']}/{c['blocks']} |")
lines+=['','The primary ratio is the exponential of equal session/input mean log paired ratios. Absolute seconds/differences above are arithmetic block means and need not produce the identical ratio.','',
'## Paired factor contrasts','','These are ratios of QB/PQ layout ratios, not absolute service-time speedups. Intervals are pointwise 95% and secondary/exploratory.','',
'| Contrast | Ratio of layout ratios | Pointwise 95% interval |','|---|---:|---|']
for c in a['secondary_contrasts']:
 lo,hi=c['pointwise95_interval'];lines.append(f"| {c['name']} | {c['ratio_of_layout_ratios']:.6f} | [{lo:.6f}, {hi:.6f}] |")
lines+=['','## Native evidence and limits','',
'- Recovered 3542 original and 3537 metadata4 indexed files; both source archives and all 21 numerical DLLs checked. Full core/frontend rebuild completed from a new source/build directory. External CUDA/BLAS numerical DLLs were retained, not rebuilt. Rebuilt executable hashes differ from historical binaries and are separately identified.',
'- Real E1 q3/layer0/GSM8K443 fixture: twelve replay processes, original and rebuilt × MQ/PQ/QB × two repeats. QK/softmax/AV match authenticated own-arm outputs; MQ own-path and PQ/QB byte identity pass.',
'- Six historical/rebuilt HTTP requests (R/PQ/QB for each build) match the archived R endpoint. Full input bytes/IDs, state, stop conditions, commands and raw responses are packaged.',
'- Engineering pilot 25 requests. Initial qualification 135 native requests then Windows aggregate-file replacement failure;69 pending slots remain NOT_RUN. All v1 records remain local. v2 changes recording only, has a new executable identity, and independently reruns all 204 qualification requests. No formal observations are mixed across builds.',
'- Additional hsc backend counters/callback/full-logit writes are disabled for clean timing; common driver phase timers and state bookkeeping remain included. Counter pilot showed an unresolved approximately 2.9% difference; no counter time was subtracted. Identical inherited backend logging remains enabled. Actual CUDA capture/instantiate/replay/eager/fallback counts are not completely measured, so no Graph causal mechanism is claimed.',
'- Six sessions ran on one date. Session, leave-one-session, first 3/last 3 and pointwise t sensitivities plus every input regression remain in ANALYSIS.json. Date-level robustness is unidentifiable. Power/thermal admission is checked per session; continuous thermal/clock/energy traces are absent.',
'- Both weights stay loaded. Resident PQ/QB context pairs remain available throughout each process; fresh contexts are created/reserved/destroyed inside the timer. All cells share the same request implementation, and every request clears/recreates KV state. No prompt prefix reuse.',
'- Bulk raw tensors/build products/interrupted attempt are local and SHA256 indexed. The compact native fixtures and complete formal result records are in Git and freshly extracted/verified; this does not imply remote delivery of all bulk raw tensors or a third-party audit.',
'- Historical M3/C3 label-to-implementation mapping remains unresolved. No B570 run, manuscript rewrite, PR merge, publication or extension of the separate PR142 long-input scope.','',
'## Review and reproduction','',
'[Frozen plan](registration/FREEZE.json) · [Full analysis](results/ANALYSIS.json) · [936 timing rows](results/TIMING.csv) · [288 paired blocks](results/BLOCKS.csv) · [Independent raw audit](results/INDEPENDENT_AUDIT.json) · [Raw access](results/RAW_ACCESS.json) · [Request accounting](results/ACCOUNTING.json) · [Native fixtures](results/NATIVE_FIXTURES.zip) · [Native records](results/NATIVE_RECORDS.zip)','',
'Reproduction and timer details: [runtime guide](../../scripts/native_reproduction/rtx_bridge/README.md). Execution freeze commit: `30ad53be0f3e281a2731b05fb2b13a51a00e1bb6`.','']
(bench/'RESULT.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
(bench/'RESUME.md').write_text('''# Completed campaign

No pending scientific slot remains. Do not rerun the finite study to seek significance.
Review RESULT.md and results/INDEPENDENT_AUDIT.json. The run checkpoint records six
complete process sessions; every registered formal request is present.

CPU-only reconstruction on the original host:

```text
python scripts/native_reproduction/rtx_bridge/analyze.py <raw_root> <new_analysis_directory>
python scripts/native_reproduction/rtx_audit_bridge.py <raw_root> benchmarks/rtx_native_bridge_20261026/registration <new_analysis_directory> <new_audit.json>
```

Use results/RAW_ACCESS.json for the raw root and hash manifest. Native fixtures
and compact records are ZIPs with MEMBERS.json and verified fresh extraction
receipts. Missing local bulk data must be recovered by hash; it is not embedded
in the compact ZIPs. New dates, inputs, implementation changes or further
precision require a separately registered cohort; they are outside this result.
''',encoding='utf-8',newline='\n')
cn=['# RTX 平台实验报告','','已按 PR #146 完成原生复现和四组受控实验；结果提交至 [PR #147](https://github.com/leecdiang/HeteroSpec/pull/147)。','','- 原始与干净重建程序：12 次阶段重放、6 次完整请求复现通过。','- 12 个输入的204次资格请求通过；正式6个会话完成864次测量和72次预热，无正式重试或缺失。','- 首次资格尝试的落盘故障及135次已运行、69次未运行位置均保留，修复后重新完成整次资格。','','| k | 生命周期 | QB / 双PQ | 服务时间降低 | 同时区间 | 实用收益成立 |','|---|---|---:|---:|---|---|']
for c in a['cells']:
 lo,hi=c['simultaneous_family95_interval'];cn.append(f"| {c['k']} | {c['lifecycle']} | {c['ratio']:.4f} | {c['reduction_percent']:.2f}% | [{lo:.4f}, {hi:.4f}] | {'是' if c['practical_gain_established'] else '未建立'} |")
cn+=['','“实用收益成立”要求同时区间上界低于0.98、点估计改善超过2%和A/A噪声门槛、且所有会话均改善。“未建立”不代表零收益或等价。','','本轮使用单台设备、同一天和12个已暴露输入，不能外推跨日期或未见输入。CUDA Graph机制未完成因果测量；本轮也未修改论文或合并PR。','','完整指标、原始证据索引、构建记录、失败记录与复现命令见PR中的RESULT.md和results目录。','']
(out/'RTX实验报告.md').write_text('\n'.join(cn),encoding='utf-8',newline='\n')
shutil.copyfile(results/'TIMING.csv',out/'RTX完整计时.csv');shutil.copyfile(results/'ANALYSIS.json',out/'RTX统计结果.json');shutil.copyfile(results/'NATIVE_FIXTURES.zip',out/'RTX原生复现样本.zip')
print('REPORTS_WRITTEN')
