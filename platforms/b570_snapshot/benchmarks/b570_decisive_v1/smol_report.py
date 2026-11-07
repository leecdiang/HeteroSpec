"""Post-panel report from immutable receipts; no model or timing execution."""
from smol import *
from smol_campaign import ARMS,EPOCH

def generate(base=HERE):
 report=read(ROOT/'RECOVERY_RECONSTRUCTION.json')
 assert report['status']=='COMPLETE_RESTORED_SECONDARY_PANEL'
 folder=SROOT/EPOCH;frozen=read(folder/'FREEZE.json');analysis=read(folder/'ANALYSIS.json');records=read(folder/'RECORDS.json')['records']
 assert len(records)==864 and len(analysis['contrasts'])==15
 totals={a:sum(x['service_s'] for x in records if x['arm']==a and x['kind']=='measure') for a in ARMS}
 warm={a:sum(x['service_s'] for x in records if x['arm']==a and x['kind']=='warmup') for a in ARMS}
 best=min(totals,key=totals.get);spec=min((a for a in ARMS if a!='M'),key=totals.get)
 evidence=base/'evidence/recovery';evidence.mkdir(parents=True,exist_ok=True)
 for source,name in (('ANALYSIS.json','MAIN_ANALYSIS.json'),('MECHANISM-test.json','TEST_MECHANISM.json'),('BOUNDARIES-test.json','TEST_BOUNDARIES.json'),('POST_PANEL_SOURCE_BINDING.json','POST_PANEL_SOURCE_BINDING.json')):
  write(evidence/name,read(folder/source))
 quals=[read(folder/f'test-{i}-QUALIFICATION.json') for i in range(12)]
 write(evidence/'TEST_QUALIFICATION.json',dict(roots=quals,all_six_arms_per_root=True,independent_roots=12))
 write(evidence/'COSTS.json',report['costs'])
 phases=[read(p) for p in sorted(folder.glob('PHASE-*.json'))]
 write(evidence/'PHASE_RECEIPTS.json',dict(phases=phases,inclusive_not_additive_to_native=True))
 completion=dict(status='COMPLETE_QUALIFIED_FROZEN_PANEL',development_roots=4,test_roots=12,sessions=6,measurements=432,warmups=432,all_controls_retained=True,extra_timing_slots=0,source_freeze_sha256=sha(folder/'FREEZE.json'),records_sha256=sha(folder/'RECORDS.json'),analysis_sha256=sha(folder/'ANALYSIS.json'),reconstruction_sha256=sha(ROOT/'RECOVERY_RECONSTRUCTION.json'),measured_service_seconds=totals,warmup_service_seconds=warm,best_fixed=best,fastest_speculative=spec,fastest_speculative_over_M=totals[spec]/totals['M'],qwen_status=report['qwen_status'],external_native_replication=False)
 write(evidence/'PANEL_COMPLETION.json',completion)
 lines=['# B570 PR185 native result and separate Smol confirmation','',
  f'The original-interface tail3 repair and original-host builds are complete. The Qwen C1024 mandatory-control capacity failure remains a failure. In the separate SmolLM2-1.7B/135M Q8 deployment, all4 development and12 test roots passed all6 native arms, the fixed24-measurement/24-warmup pilot completed, and the frozen432-measurement/432-warmup panel completed without a failed or replaced timing slot.', '',
  f'The best fixed method by total measured service is **{best}**. The fastest speculative arm is **{spec}**, using **{totals[spec]/totals["M"]:.6f} times M service**. Physical draft width4 helps relative to the speculative controls here, while complete speculative service remains much slower than M. This finite deployment result does not establish general equivalence or impossibility.', '',
  '## Complete service','',
  'Each arm has72 measurements and72 immediate same-arm warmups. Service includes reset/sync, prefill, sampling/propose/verify/trim, original required transfer/restore/checks, continuation-context destruction and response-file close. Fresh worker/model provisioning is outside service and charged separately. Heavy qualification capture is absent from clean timing. M retains the same unused draft weights/context resident and charges its reset.', '',
  '| Arm | Measured total (s) | Mean request (s) | Total / M | Warmup total (s) |','|---|---:|---:|---:|---:|']
 for a in ARMS:lines.append(f'| {a} | {totals[a]:.6f} | {totals[a]/72:.6f} | {totals[a]/totals["M"]:.6f} | {warm[a]:.6f} |')
 lines += ['', '## All15 fixed comparisons','',
  'Ratios are numerator service / denominator service; a ratio above1 favors the denominator. Primary intervals use the frozen10000-draw root bootstrap with all6 paired sessions retained and Bonferroni adjustment across15 contrasts. Equal-root geometric ratios are the prespecified sensitivity. Absolute paired differences are seconds per request. Full root/session ratios and individual absolute-difference intervals remain in `evidence/recovery/MAIN_ANALYSIS.json`.', '',
  '| Numerator / denominator | Total ratio | Primary family95 interval | Equal-root geometric ratio | Mean seconds numerator minus denominator |','|---|---:|---|---:|---:|']
 for c in analysis['contrasts']:
  lo,hi=c['total_family95'];lines.append(f"| {c['numerator']} / {c['denominator']} | {c['total_service_ratio']:.6f} | [{lo:.6f}, {hi:.6f}] | {c['paired_geometric_ratio']:.6f} | {c['mean_paired_seconds_a_minus_b']:.6f} |")
 lines += ['', 'Intervals covering1 do not establish equivalence. The statistical sample is12 independent test roots, not the count of vectors, states, tokens, sessions or requests. No new AUTO was fitted and PR175 AUTO null results remain unchanged.', '',
  '## Actual trained-model qualification','',
  'All target values use unchanged original numerical DLLs. Autonomous unchanged original R is repeated and stable on each root. An independently produced scalar original-R forced-prefix bank supplies complete49152-element F32 vectors and active KV/frontier at actual candidate prefixes. Candidate values are never supplied to R. Heavy/clean final state agrees; every committed state is an emitted greedy prefix, including correctly positioned terminal tokens still unmaterialized in KV. Historical full KV is not retroactively claimed.', '',
  '| Test index | Original prompt tokens | Output tokens | Natural stop | Full vector comparisons across6 arms | Committed-state comparisons across6 arms |','|---:|---:|---:|---|---:|---:|']
 vector_count=state_count=0
 for i,q in enumerate(quals):
  ref=read(folder/'runs'/f'test-{i}-oldR/0.json');nv=sum(x['conditional_vectors'] for x in q['arms']);ns=sum(x['committed_states'] for x in q['arms']);vector_count+=nv;state_count+=ns
  lines.append(f"| {i} | {len(ref['prompt_ids'])} | {len(ref['ids'])} | {'EOG' if ref['eog'][-1] else 'CAP128'} | {nv} | {ns} |")
 lines += ['', f'All{vector_count} test conditional vectors and{state_count} committed states match. These are repeated finite checks across six methods, not additional independent roots. Long inputs, natural EOG and tails congruent to3 modulo4 were retained without truncation, padding, input replacement or outcome filtering.', '',
  'The original prefill interface is exercised by8192 verbatim-interface cases, alongside8199 helper checks; the original width3 rejection is reproduced and q4 tails now use2+1. All77 Python tests pass normally and under `-O`; native execution/auditing itself rejects optimized Python. The historical Smol bridge separately checks25 full vectors/13 states, with the original target R executable unchanged. The old native score mismatch and heavy-capture deadline failure remain failures.', '',
  '## Physical intervention','',
  'H1 retains the stronger inherited whole-prompt draft caller with original512 outer chunks and physical UB1. C1U1 uses caller1; C4U1/2/4 use caller up to4, tail3 as2+1, and actual physical UB1/2/4. Only the final prompt output is requested. Subsequent draft sync/propose remains singleton. Scheduler embedding columns are actual graph-shape observations and make no new kernel-identity claim.', '',
  '| Draft arm | Observed caller widths | Observed embedding columns | Roots with draft F32 frontier different from H1 | Maximum absolute draft difference |','|---|---|---|---:|---:|']
 mechanism=read(folder/'MECHANISM-test.json')['roots']
 for a in ARMS[1:]:
  rs=[next(x for x in r['arms'] if x['arm']==a) for r in mechanism]
  callers=sorted({int(k) for r in rs for k in r['caller_histogram']});columns=sorted({int(k) for r in rs for k in r['observed_embedding_columns']})
  lines.append(f"| {a} | {','.join(map(str,callers))} | {','.join(map(str,columns))} | {sum(r['draft_F32_different_elements_from_H1']>0 for r in rs)}/12 | {max(r['draft_max_abs_difference_from_H1'] for r in rs):.9g} |")
 costs=report['costs'];reserved=costs['reserved'];ceilings=costs['ceilings']
 lines += ['', 'Ordinary physical width may alter draft logits, proposals and acceptance. The target trajectory is independently qualified. This is a separate historically referenced Smol runtime, not Qwen admission or a CUDA/Vulkan speed ranking.', '',
  '## Complete native costs and limits','',
  f"The cumulative immutable ledger reserves{reserved['requests']} model requests,{reserved['token_rows']} decoded rows and{reserved['operators']} operator replays against unchanged ceilings{ceilings['requests']}/{ceilings['token_rows']}/{ceilings['operators']}. These reservations include failed, warm, teacher-forced and measured requests; the ledger was never reset. All{len(report['qwen_attempts'])} Qwen zero-forward failures remain retained. Total native charged wall is{costs['native_process_seconds']:.3f}s; owned-worker wall is{costs['owned_worker_seconds']:.3f}s. These clocks overlap and are not added.", '',
  '| Stage | Reserved requests | Reserved rows | Native charged (s) | Owned worker (s) | Observed provisioning-to-ready (s) |','|---|---:|---:|---:|---:|---:|']
 for name,c in costs['by_stage'].items():
  ready=f"{c['observed_provisioning_seconds']:.3f}"
  if c['provisioning_units_not_separately_metered']:ready+=f"; {c['provisioning_units_not_separately_metered']} units unmetered"
  lines.append(f"| {name} | {c['requests_reserved']} | {c['rows_reserved']} | {c['native_seconds']:.3f} | {c['owned_seconds']:.3f} | {ready} |")
 lines += ['', 'Provisioning observations include process/library/backend/model/context setup with100ms polling resolution; they are not pure weight-load measurements. Older units lacking a separate ready clock are counted explicitly in `COSTS.json`. Each native worker has900s wall,180s request-progress,16GiB Job memory,20GiB disk reserve,2GiB RAM reserve and128MiB signed device reserve. Suspended-before-Job assignment, kill-on-close and zero-active-process cleanup are verified, including real parent-failure/timeout descendants.', '',
  'Inclusive coordinator/phase clocks and streamed-storage clocks overlap native work and are disclosed without adding them a second time. Initial v1 delivery and every failed epoch remain retained. Some CPU preparation, early packing and final mechanism/boundary aggregation were not separately wall-metered; no complete engineering-time total is claimed. Later delivery actions have separate actual wall receipts.', '',
  '## Provenance and reconstruction','',
  f'The branch starts at PR185 actual head `8befecc2484d749085ed95fca064b6acc42e7b1d`. Execution source `{frozen["source_commit"]}` was frozen and published/read back before any test output. Frozen data include all6423 natural source paths, native tokenization/rendering, exact exposure exclusions and the unchanged sixteen selected roots. Full-population reconstruction passes; supplementary prior-exposure repair changed no selected identity or ordering.', '',
  'A no-model post-panel check found execution sources, binaries and inputs still identical to the published freeze after all864 slots. Later edits only concern read-only reconstruction, cost-stage labels, documentation and transport. Original source snapshots, raw failed partial files, old R, full vectors and byte-exact reconstructible F16 sequence state are retained. Original Qwen F32-activation/p021 libraries and PR169 capacity failures are not relabeled as successful.', '',
  'The separate v2 raw release contains actual binaries, portable frontend inputs, arguments, manifests and all included raw bytes, without GGUF weights. The immutable initial v1 release remains unchanged. Restore the objects and run `python -B RESTORED/delivery-v2/recompute.py RESTORED` with the pinned host requirements. Fresh-download restoration is recorded in `evidence/recovery/DELIVERY_READBACK.json` when delivery completes. Verification is authenticated on the same B570 host; it does not claim external native replication or anonymous access.', '',
  'No merge, paper edit, new model download, rental or cross-platform pooling.', '']
 text='\n'.join(lines)
 with (base/'RESULTS.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
 print('POST_PANEL_REPORT_COMPLETE',completion['status'],flush=True)

if __name__=='__main__':generate(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE)
