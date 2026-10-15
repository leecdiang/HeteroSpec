"""Compose one final RESULT from actual reconstructed data; never run inference."""
import collections
import csv
from pathlib import Path
import experiment as e

OUT=Path(__file__).parent/'final_20261015'
def main():
    counts=e.read(OUT/'COUNTS.json');cost=e.read(OUT/'E2_ANALYSIS.json');diag=e.read(OUT/'E1_ANALYSIS.json')
    acceptance=e.read(OUT/'AUTHENTICATED_COMBINED_RESTORE.json')
    e.require(acceptance['status']=='PASS' and acceptance['analysis_bitwise_equal'],'final remote/fresh CPU archive acceptance missing')
    a,b=counts['E2'],counts['E1'];assembly=e.read(OUT/'E1_ARCHIVE_ASSEMBLY.json')
    pairs=collections.defaultdict(list)
    for row in diag['numerical']:pairs[row['pair'],row['stage']].append(row)
    tasks=list(csv.DictReader((OUT/'E2_TASK_SUMMARY.csv').open(newline='',encoding='utf-8')))
    economics=list(csv.DictReader((OUT/'E2_ECONOMICS_COUNTERS.csv').open(newline='',encoding='utf-8')))
    regression=sum(float(r['six_session_geometric_ratio'])<1 for r in tasks)
    lines=['# PR104 — complete E2 and bounded native E1 results','',
           'E2 completed all six original sessions. E1 terminal state: **'+b['status']+'**. A completed matrix counts attempted coordinates, not a guarantee that every geometry was observed or admitted. All old failures, cancellation and stopped-state receipts remain immutable. No main, PR102, historical empirical values, release or B570 execution was changed. PR104 remains Draft.','',
           '## Execution and costs','',
           '| Phase | Native workers | Requests (warmups included) | Warmups | Standalone operator starts | Native owned seconds |',
           '|---|---:|---:|---:|---:|---:|',
           f"| E2 | {a['native_workers']} | {a['native_requests']} | {a['warmups']} | 0 | {a['native_owned_seconds']:.6f} |",
           f"| E1 | {b['native_workers']} | {b['native_requests']} | {b['warmups']} | {b['operator_starts']} | {b['combined_native_owned_seconds']:.6f} |",'',
           f"This resumption added54 E2 workers/270 requests and {b['native_workers']} E1 workers/{b['native_requests']} requests/{b['operator_starts']} standalone replay starts. E2 logical model caller invocations={a['logical_model_caller_invocations']}; E1={b['logical_model_caller_invocations']}. These caller counters and physical micrograph counters are not hardware kernel launches. Global auxiliary OS/compiler process starts were not comprehensively captured and remain NOT_GLOBALLY_CAPTURED.",'',
           f"E1 compilation/configuration command wall seconds={b['compilation_command_seconds']:.6f}; actual native-header CPU compile/test seconds={b['actual_native_CPU_selector_test_command_seconds']:.6f}. These are engineering costs, separate from combined native model/replay lifetime; no model/operator probe was inserted.",'',
           f"E2 request failures={a['failed_requests']}, failed blocks={a['failed_blocks']}, output mismatches={a['output_mismatches']}, invalid contracts={a['invalid_contracts']}, workload errors={a['workload_errors']}, heavy-observer flags={a['heavy_observer_flags']}. E1 request failures={b['failed_requests']}, operator failures={b['operator_failures']}, invalid output contracts={b['invalid_output_contracts']}, workload errors={b['workload_errors']}.",'',
           'The whole E2 ceiling remained324 workers/1,620 requests/43,200 native seconds. E1 remained72 contexts/216 requests including warmups/432 standalone replay starts/21,600 combined native seconds. Unused ceilings cannot be transferred. All failed/started/unstarted coordinates are retained in ledgers and context tables; none is retried.','',
           '## E2 PQ/QB cost confirmation','',
           'Ratio=T_PQ/T_QB. Equal task weights within each session and equal weights over six sessions; intervals use the original six-session bootstrap. No request-level bootstrap, latency trimming, task pruning or sample expansion.','',
           '| Family | Path | Geometric speed ratio | Approx. six-session interval | QB latency reduction | 1.02 interpretation |',
           '|---|---|---:|---|---:|---|']
    for c in cost['comparisons']:
        x=c['estimate']
        if x is None:
            lines.append(f"| {c['family']} | {c['path']} | WITHHELD | {c['status']} | — | affected qualification failed |");continue
        lo,hi=x['session_cluster_percentile_interval'];label='practical point evidence' if x['speed_ratio_PQ_over_QB']>1.02 else 'weak/no practical difference'
        if lo<=1.02<=hi:label+='; interval crosses1.02'
        lines.append(f"| {c['family']} | {c['path']} | {x['speed_ratio_PQ_over_QB']:.6f} | [{lo:.6f}, {hi:.6f}] | {100*x['QB_latency_reduction']:.3f}% | {label} |")
    lines+=['',f"All session log contrasts and all task/session ratios are in E2_SESSION_CONTRASTS.csv and E2_TASK_CONTRASTS.csv. E2_TASK_SUMMARY.csv retains all72 family/path/task contrasts; {regression} have a six-session point ratio below1. No task-level significance test is claimed. E2_SESSION_TABLE.csv gives the six actual starts/completions and lifetime accounting. All1,620 raw request latencies remain in the complete E2 archive and paid-request table; nonpositive/nonfinite latency count={a['nonpositive_or_nonfinite_latency']}. No posthoc outlier threshold removes data.",'',
            f"Recorded C_PQ/C_QB acceptance/rollback and logical-workload counters/histograms agree in {sum(r['same_recorded_acceptance_and_logical_workload']=='True' for r in economics)}/{len(economics)} task/session pairs. Full original serial-R endpoint qualification passes across the six sessions. Counter agreement does not establish identical complete control traces, physical kernel schedules or reduction trees.",'',
            '## E1 geometry and numerical correspondence','',
            'The fixed matrix is three families × target layers0/floor(L/2)/L-1 × prefill/continuation × q1..4. GGUF block counts are Qwen36, SmolLM224, Llama32. Longest inherited P2 prompts with lexical-ID ties select GSM8K/test/443, with105/126/123 input IDs respectively. q2/4 use minimum observed key extent128; q1/3 use0. Input choices were frozen before E1 forwards.','',
            'Context qualification states: `'+str(b['context_statuses'])+'`. E1_CONTEXTS.csv includes every coordinate, observed key extent, visible mask keys, observer equality, own-path and within-arm repeatability. PASS means admission, not that every pair is numerically equal. q1 is an ordinary-decoding negative control.','',
            '| Pair | Operator | Bitwise-equal admitted contexts | Maximum finite absolute error | Maximum finite ULP |',
            '|---|---|---:|---:|---:|']
    for (pair,stage),rows in sorted(pairs.items()):
        errors=[r['max_error'] for r in rows if r['max_error']is not None];ulps=[r['max_ULP'] for r in rows if r['max_ULP']is not None]
        lines.append(f"| {pair} | {stage} | {sum(r['bitwise_equal'] for r in rows)}/{len(rows)} | {max(errors,default=None)} | {max(ulps,default=None)} |")
    first={}
    for pair in ('MQ/PQ','MQ/QB','PQ/QB'):
        rows=[r for r in diag['numerical'] if r['pair']==pair and r['stage']=='QK']
        first[pair]=dict(collections.Counter(r['first_divergence_operator'] or 'NONE' for r in rows))
    geometries=collections.defaultdict(set);layers=collections.defaultdict(set);visible=collections.defaultdict(list)
    restored=Path(acceptance['restoration_directory'])/'E1/data'
    for row in diag['contexts']:
        layers[row['family']].add(row['layer'])
        if row['status']!='PASS':continue
        reg=e.read(restored/'snapshot_registry'/f"{row['index']:03d}.json")
        snapshot=restored/Path(reg['root']).relative_to(Path('D:/hs104-e1-v1'))
        m=e.read(snapshot/'snapshot.json');q,k=m['Q']['ne'],m['K']['ne']
        geometries[row['family']].add((q[0],q[2],k[2],k[1]))
        visible[row['family']].extend(__import__('json').loads(row['visible_mask_keys']))
    lines+=['','First bitwise-divergent operator, by admitted context/pair: `'+str(first)+'`. All detailed stage/ULP/nonfinite values are in E1_NUMERICAL.csv. Failed own-path/repeatability cases withhold qualified pair inference; their original tensor bytes remain archived.','',
            '| Family | Observed layers | (head dimension, query heads, KV heads, tensor key extent) | Unmasked visible-key range |',
            '|---|---|---|---|']
    for family in e.FAMILIES:
        values=visible[family]
        lines.append(f"| {family} | {sorted(layers[family])} | {sorted(geometries[family])} | {min(values,default=None)}–{max(values,default=None)} |")
    lines+=['','All captured Q/K/V dtypes are F32/F16/F16 with F32 masks; complete actual shapes/strides/GQA and masks are in each snapshot, not reconstructed by changing geometry.','',
            '## Freeze, recovery and raw evidence','',
            'Original PR98 baseline:3235d44c26edd92db33e574094c26af8e29d2452. Scientific E2 F0:49b992b2ed1cabd05fad6e234cad2d3418c2b65a. Transport supplement:e06dc8df53622eddd3f9306addbeaf428cdb3548. Exact-restoration registration:c51354bb19061ed3863cb457068dc727aa46d8ab. Prospective native E1 F0:fea46ef7ffa0f553b6aa5c9f1a26f6296f1cd1ca.','',
            'The original Phase0 routing failure ccfbc2e4c3ab3026a6bbec5caf4c98646781913c, pre-scientific authenticated transport EOF, CPU export path-length failure, user cancellation, interpreter-drift stop f784386 and recovery/control failures are retained. The drift stop was genuine before recovery; it is not the final execution state. The exact original d41bad… launcher was recovered from official bundle26.1011.11113, whose complete SHA-256 is81466ad85b7074e5694a3d45e8edae6387f09548cd2e8f144841951a329dd7c7. Original frozen files and original authenticated F0 passed without guard changes before untouched session5; no scientific retry or identity exception was introduced.','',
            'Complete E2 raw archive:26,237,013 bytes, SHA-256 ed3a87567b62c2610627783d43db00e187aef865aa7874d806428dd51d4a7227. All10,179 members passed fresh restoration and separate-interpreter CPU recomputation; authenticated remote archive bytes at75e01db7b2b471137b638a0d6c2e5bb61a23838f match. The export helper removes only a legacy non-scientific code-bundle flag, with no scientific field or estimate excluded.','',
            f"Full E1 archive SHA-256={assembly['full_archive_sha256']}, bytes={assembly['full_archive_bytes']}, parts={len(assembly['parts'])}. E1_ARCHIVE_ASSEMBLY.json defines exact concatenation order and part hashes. RAW_ARCHIVE_MANIFEST_E1.json inventories retained members. Authenticated remote bytes from data commit {acceptance['data_commit']} passed full fresh combined restoration and separate-interpreter CPU reconstruction, byte-equal across all analysis files. Models and numerical DLL bytes are excluded; immutable identities, actual native module receipts, complete private source and native executables are retained.",'',
            '## Claim/evidence and limitations','',
            'The completed fixed-panel RTX evidence supports the narrow claim that QB can lower local-repair request cost while preserving the recorded speculative-decoding workload/endpoint economics. C-path gains are observed in all three families. Llama M remains below the practical threshold, and Qwen M practical uncertainty overlaps it. Per-task regressions remain part of the result. This is not a blanket per-task, new-input, multi-device or six-independent-dates claim.','',
            'E1 provides only finite observed geometry/operator correspondence under the frozen CUDA stack. Tensor extent includes masked padding and does not prove long unmasked contexts. One selected exposed prompt per family is not broad input generalization. Own-path/repeatability and capture-on/off endpoints do not identify the counts-mode kernel schedule or establish a universal numerical theorem. Physical-query token attribution inside a wider caller can remain UNKNOWN; full raw caller positions/ownership are preserved without inventing prefixes.','',
            'Before/after input identity is enforced by frozen driver assertions against retained immutable hashes; separate per-replay hash-dump files were not produced. Native worker PIDs and actual module receipts are retained; standalone replay executable/loader paths and fixed DLL hashes are bound, but a separate module enumeration/PID receipt was not added to the inherited replay executable. Kernel identity, reduction tree, hardware launch count, continuous thermal residency, DRAM/SM shares, energy, silicon area and cross-platform bitwise reference remain UNKNOWN or unmeasured.','',
            'Fresh-directory separate-interpreter CPU reconstruction on this host is not an external audit or a new GPU run. Original conversion/checkpoint lineage limits remain. PR102 and B570 results are not changed. PR110 may begin only after this actual E2/E1 closure, ended owned tasks and accepted new raw restoration.']
    with (OUT/'RESULT.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    print('Wrote final RESULT after actual authenticated archive acceptance')
if __name__=='__main__':main()
