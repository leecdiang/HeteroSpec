"""Describe a stopped attempt; never qualify incomplete outputs or launch GPU work."""
import csv,json,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parents[1]))
from common import V,load,save,sha

def build():
    f=load(OUT/'FORENSIC.json');manifest=load(OUT/'RESULT_RAW_MANIFEST.json')
    remote=load(OUT/'RAW_REMOTE_AUTHENTICATED.json') if (OUT/'RAW_REMOTE_AUTHENTICATED.json').exists() else {'status':'NOT_VERIFIED'}
    fresh=load(OUT/'FRESH_RECOMPUTE_VERIFIED.json') if (OUT/'FRESH_RECOMPUTE_VERIFIED.json').exists() else {'status':'NOT_VERIFIED'}
    phases=[load(p) for parent in [OUT/'cpu_ledger',V/'delivery/cpu_ledger'] for p in parent.glob('*/CPU_ENDED.json')]
    result=dict(run_id=f['run_id'],execution_id=f['execution_id'],status='STOPPED_NO_RETRY',coordinate_counts=f['coordinate_counts'],graph_counts=f['graph_counts'],coordinates=f['coordinates'],ordinary_observations=f['ordinary_observations'],q1_control=f['q1_public_control'],cross_layout='UNKNOWN / NO QUALIFIED PAIRS',qualified_costs=None,qualified_QPC_median_p95_max=None,partial_QPC_unqualified=f['partial_QPC_unqualified'],readiness=f['readiness'],supervision=f['supervision'],input_occurrences=f['input_occurrences'],GPU_stage=f['stopped'],controlled_process_starts=9,process_breakdown=dict(controller=1,readiness=1,native=1,CPU_watchdogs=2,conhost=4),CPU_finished_phase_wall_seconds=sum(p['seconds'] for p in phases),CPU_finished_phase_conservative_owned_seconds=sum(p['conservative_owned_seconds'] for p in phases),CPU_current_phase_charged_separately=True,CPU_delivery_wall_limit_seconds=900,CPU_delivery_owned_limit_seconds=15300,F0_sha256=f['F0_sha256'],execution_bound_Census_sha256='d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256',previous_CPU_archive_manifest_sha256='3b84a2d8f000e2a8be7aceb46695d562696cb6912c8b875b90913e4b1db11c56',result_archive_sha256=manifest['archive']['sha256'],result_manifest_sha256=sha(OUT/'RESULT_RAW_MANIFEST.json'),archive_members=manifest['member_count'],archive_member_bytes=manifest['member_bytes'],archive_bytes=manifest['archive']['bytes'],remote_authentication=remote,fresh_recompute=fresh,root_cause='UNKNOWN',first_observed_divergence='ordinary output;QK/softmax/AV not observed in clean host',input_after='UNKNOWN / MISSING',complete_loaded_module_inventory='UNKNOWN / MISSING',Block1_2_admission='NO_GO',all_further_GPU_authority=False,history_unchanged=True)
    save(OUT/'RESULT.json',result)
    with (OUT/'COORDINATES.csv').open('w',newline='',encoding='utf-8') as file:
        cols=['id','family','layer','phase','q','layout','status','started','completed_qualified','graph_calls','warmups','formal_evaluations','cost_status']
        writer=csv.DictWriter(file,fieldnames=cols,extrasaction='ignore');writer.writeheader();writer.writerows(f['coordinates'])
    (OUT/'RESULT.md').write_text('''# PR118 Clean Block 0 r2 — stopped

Canonical run: `pr116-s1b-cost-v1`; execution: `pr116-s1b-exact-r2`.

| Coordinates | Planned | Started | Qualified | Failed | Unstarted |
|---|---:|---:|---:|---:|---:|
| Block 0 |72|1|0|1|71|
| PQ |24|1|0|1|23|
| QB |24|0|0|0|24|
| QH_C |24|0|0|0|24|

The first coordinate, Qwen layer0 / prefill / q1 / PQ, stopped at its first formal ordinary-output check. Actual calls: 1 warmup + 1 formal = 2 of 648; both compute and synchronization returns were observed. This establishes no qualified clean host or performance sample. All other families/phases/q/layout coordinates remain unstarted; see COORDINATES.csv.

Warmup ordinary matched PR116 byte-for-byte. First formal ordinary was finite but differed at 32 of 4096 float32 words; max absolute error 511.9579162597656, max ULP 2091933697 (descriptive only). First value: 512 versus 0.042083740234375. Root cause UNKNOWN. Intermediate diagnostic stages were not observed, so no kernel/reduction/accumulator attribution is made. No MQ/QB/QH_C execution or qualified cross-layout comparison exists.

Allocation, packing/mask/preparation, upload, qualified compute/sync/readback, resident and input-inclusive distributions: UNKNOWN / NO QUALIFIED SAMPLE. Median/p95/max are UNKNOWN, never zero. Partial raw QPC observations are retained in FORENSIC.json and RESULT.json as invalid-coordinate records, not performance estimates.

Complete input-before bytes matched; input-after bytes and final module inventory are missing after the early native failure and remain UNKNOWN. Saved graph support/placement and partial core/IAT checks passed the frozen CPU inspection; complete host qualification failed. Frozen raw failure records, locks and original evidence are retained.

Readiness: utilization 0%, temperature 40 C, driver 616.92, AC power. Native maximum actual monitoring interval 77,161,100 ns (limit 1,000,000,000); missing samples 0. Controlled starts 9: controller 1, readiness 1, native 1, CPU watchdogs 2, conhost 4. GPU-stage wall 15.8800406 s; conservative owned 79.400203 s. Native peak process commit 450,641,920 bytes; peak job commit 467,083,264 bytes. Post-exit audit is recorded separately.

Raw archive: 242 members / 89,070,945 uncompressed bytes; ZIP 21,766,592 bytes. SHA256 `ddaa1adbf7875de55ff0ce5de4309cf312abca19ce587983f4340cbb207e0009`. Multipart transport concatenates to the exact original ZIP. Remote authentication and fresh interpreter recomputation are reported only when their actual receipts exist; see RESULT.json. CPU delivery failures remain charged to the independent 900 s wall / 15300 s conservative-owned limit. Current delivery phase has its own terminal receipt and is not omitted from accounting.

F0: `f2d6965646e1f53c5d8a8b974f0277efc2903ed022689374af3f178fbad8e587`.
Census exact CRLF bytes: `d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256`.

Block 1/2: **NO-GO**. r2 is permanently stopped. No retry, extra GPU probe, profiling, model request or algorithm change was performed for closure. Historical PR evidence and frozen numerical implementation were not modified. Further engineering or GPU work requires separate authorization.
''',encoding='utf-8')
    return result
if __name__=='__main__':build()
