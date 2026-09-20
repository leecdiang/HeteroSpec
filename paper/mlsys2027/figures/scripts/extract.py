#!/usr/bin/env python3
"""Extract candidate plotting tables from frozen repository evidence; never from prompt text."""
from pathlib import Path
import csv, hashlib, json, math, statistics as st
import numpy as np

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
DATA = HERE / 'data'
SOURCE_COMMIT = '62d1c134b096882c37ce58c1d0ac140236acd9c3'
BFAST = 'artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/'
BSER = 'artifacts/b570_backend_control/exact-fallback-v1-20260912-222617/exact_fallback/processed/'
RTX = 'artifacts/windows_verification_mechanism/windows-exact-verification-microbench.json'
SOURCES = set()
AUDIT = []

def read(path):
    SOURCES.add(path)
    return (ROOT / path).read_text(encoding='utf-8-sig')

def js(path):
    return json.loads(read(path))

def table(path, keys, expected):
    rows = list(csv.DictReader(read(path).splitlines()))
    assert len(rows) == expected, (path, len(rows), expected)
    ids = [tuple(r[k] for k in keys) for r in rows]
    assert len(set(ids)) == len(ids), (path, 'duplicate key')
    assert all(all(v is not None and v != '' for v in r.values()) for r in rows), path
    AUDIT.append(dict(source=path, rows=len(rows), columns=len(rows[0]) if rows else 0,
                      grain=keys, duplicate_keys=0, missing_cells=0))
    return rows

def write(name, rows):
    with (DATA / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader(); w.writerows(rows)

def gm(xs):
    return math.exp(st.fmean(map(math.log, xs)))

def main():
    DATA.mkdir(exist_ok=True)
    # Scientific authority is explicit even for the entirely conceptual Figure 1.
    for p in ['paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md','paper/mlsys2027/OUTLINE.md',
              'paper/mlsys2027/WRITING_STATUS.md','paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md',
              'paper/notes/CROSS_PLATFORM_MECHANISM.md']:
        read(p)
    micro = []
    def add(path, context, one, two, repetitions, status, evidence, source):
        assert one > 0 and two > 0
        micro.append(dict(path=path, context=context, pp1_ms=one, pp2_ms=two,
                          v2_micro=two/one, repetitions=repetitions, status=status,
                          evidence_class=evidence, source=source))
    p = 'work/m4/llama_verify_q8_synced.csv'
    m4 = table(p, ['prefix_tokens','verify_tokens','repetition'], 84)
    for n in (512,2048,8192):
        v = [[float(r['elapsed_us'])/1000 for r in m4 if int(r['prefix_tokens'])==n and int(r['verify_tokens'])==k] for k in (1,2)]
        assert all(len(x)==7 for x in v)
        add('M4 Metal',n,*map(st.median,v),7,'qualified','MECHANISM_SUPPORTED',p)
    raw = js(RTX)
    for path, key, status, ec in [('RTX batched','batched_ubatch2','blocked','DIAGNOSTIC'),
                                  ('RTX serialized','serialized_ubatch1','qualified','MECHANISM_SUPPORTED')]:
        for n, paths in raw['depths'].items():
            x = paths[key]
            assert len(x['pp1']['samples_ns'])==len(x['pp2']['samples_ns'])==20
            add(path,int(n),st.median(x['pp1']['samples_ns'])/1e6,
                st.median(x['pp2']['samples_ns'])/1e6,20,status,ec,RTX)
    for path,p in [('B570 fast',BFAST+'v2_raw.json'),('B570 serialized',BSER+'v2_exact.json')]:
        for n,x in js(p)['cells'].items():
            assert len(x['pp1']['samples_ns'])==len(x['pp2']['samples_ns'])==20
            add(path,int(n),st.median(x['pp1']['samples_ns'])/1e6,
                st.median(x['pp2']['samples_ns'])/1e6,20,'diagnostic','DIAGNOSTIC',p)
    write('figure2_micro_cells.csv',micro)

    a = js('analysis/m4_confirmatory_summary.json')
    b = js('analysis/m4_humaneval_summary.json')['conditions']['fixed_k2']
    workloads = [dict(workload='Representative 24Q',speedup=a['geomean_speedup'],
        ci_low=a['bootstrap_95_ci'][0],ci_high=a['bootstrap_95_ci'][1],
        prompts=a['prompt_count'],pairs=a['paired_repetitions'],exact_pairs=a['exact_pairs'],
        bootstrap_resamples=10000,seed=20260907,source='analysis/m4_confirmatory_prompt_summary.csv'),
        dict(workload='Preregistered HumanEval30',speedup=b['prompt_geomean_speedup'],
        ci_low=b['prompt_bootstrap_95_ci'][0],ci_high=b['prompt_bootstrap_95_ci'][1],
        prompts=b['prompt_count'],pairs=b['pair_count'],exact_pairs=b['exact_pairs'],
        bootstrap_resamples=100000,seed=20260910,source='analysis/m4_humaneval_prompt_summary.csv')]
    for r,key,idcol in zip(workloads,['speedup','fixed_k2_speedup'],['question_id','task_id']):
        rows = table(r['source'],[idcol],r['prompts'])
        assert abs(gm([float(x[key]) for x in rows])-r['speedup'])<1e-12
        r.update(evidence_class='PRIMARY',status='qualified',estimator='GM of within-prompt GMs of 3 paired decode-time ratios')
    read('benchmarks/m4_code_conditioned_30q/preregistration.json')
    write('figure3_workloads.csv',workloads)

    p1 = table('analysis/358h_draft_device_summary.csv',['device','context'],6)
    p1json = js('analysis/358h_draft_device_summary.json')
    iso = []
    for r in p1:
        x = p1json['devices'][r['device']][r['context']]
        assert x['repetitions']==5 and x['failures']==0 and x['output_tokens']==[128]*5
        med = float(r['median_tokens_s'])
        assert med == x['throughput_tokens_s']['median']
        iso.append(dict(device=r['device'],context=int(r['context']),tokens_s=med,
            ci_low=x['throughput_tokens_s']['bootstrap_ci95'][0],
            ci_high=x['throughput_tokens_s']['bootstrap_ci95'][1],repetitions=5,
            estimator='median; 95% repetition bootstrap CI',boundary='Phase-1 telemetry-OFF isolated steady-state',
            source='analysis/358h_draft_device_summary.csv'))
    write('figure4_isolated.csv',iso)
    pairs = table('analysis/358h_phase3_prompt_summary.csv',['condition','task_id','repetition'],180)
    summary = js('analysis/358h_phase3_summary.json')
    realized=[]
    for dev in ('CPU','NPU'):
        rows=[r for r in pairs if r['condition']==dev+'_DRAFT_K2']
        assert len(rows)==90 and all(r['exact']==r['formal']==r['admissible']=='True' for r in rows)
        assert len(set(r['task_id'] for r in rows))==30
        for task in set(r['task_id'] for r in rows):
            assert sorted(int(r['repetition']) for r in rows if r['task_id']==task)==[0,1,2]
        means={k:st.fmean(float(r[k]) for r in rows)/1000 for k in
            ['baseline_end_to_end_ms','end_to_end_ms','draft_replay_proposal_ms','verification_ms','orchestration_residual_ms']}
        total=means['end_to_end_ms']
        assert abs(total-sum(means[k] for k in ['draft_replay_proposal_ms','verification_ms','orchestration_residual_ms']))<1e-10
        perf=summary['performance'][dev]
        realized.append(dict(device=dev,requests=90,exact_pairs=90,baseline_s=means['baseline_end_to_end_ms'],
            total_s=total,draft_s=means['draft_replay_proposal_ms'],target_s=means['verification_ms'],residual_s=means['orchestration_residual_ms'],
            draft_pct=100*means['draft_replay_proposal_ms']/total,target_pct=100*means['verification_ms']/total,
            residual_pct=100*means['orchestration_residual_ms']/total,
            headline_speedup=perf['geometric_mean_speedup'],ci_low=perf['bootstrap_ci95'][0],ci_high=perf['bootstrap_ci95'][1],
            aggregate_speedup=means['baseline_end_to_end_ms']/total,
            boundary='Phase-3 post-prefill decode; arithmetic mean seconds per request',
            source='analysis/358h_phase3_prompt_summary.csv'))
    write('figure4_realized.csv',realized)

    bs=js('analysis/b570_exact_fallback_summary.json')['correctness']
    bf=js(BFAST+'diagnostic_summary.json')
    rx=js('reports/5070ti/windows_humaneval_summary.json')
    regimes=[
        dict(case='M4 representative 24Q',mechanism='Workload-conditioned',admissibility='qualified',profitability='negative',exact='72/72',evidence_class='PRIMARY',source='analysis/m4_confirmatory_summary.json'),
        dict(case='M4 HumanEval30',mechanism='Workload-conditioned',admissibility='qualified',profitability='profitable',exact='90/90',evidence_class='PRIMARY',source='analysis/m4_humaneval_summary.json'),
        dict(case='RTX batched',mechanism='Verification-constrained',admissibility='blocked',profitability='not_admissible',exact='frozen gate FAIL',evidence_class='MECHANISM_SUPPORTED',source='reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md'),
        dict(case='RTX serialized controls',mechanism='Verification-constrained',admissibility='qualified',profitability='negative',exact='90/90 each',evidence_class='SECONDARY',source='reports/5070ti/windows_humaneval_summary.json'),
        dict(case='B570 fast',mechanism='Correctness-blocked',admissibility='blocked',profitability='not_admissible',exact=f"{bf['counts']['exact_pairs']}/90",evidence_class='DIAGNOSTIC',source=BFAST+'diagnostic_summary.json'),
        dict(case='B570 serialized',mechanism='Correctness-blocked',admissibility='blocked',profitability='not_admissible',exact=f"{bs['exact_pairs']}/{bs['total_pairs']}",evidence_class='DIAGNOSTIC',source='analysis/b570_exact_fallback_summary.json'),
        dict(case='358H CPU',mechanism='Target-side dominated',admissibility='qualified',profitability='negative',exact='90/90',evidence_class='PRIMARY',source='analysis/358h_phase3_summary.json'),
        dict(case='358H NPU',mechanism='State-interface bound',admissibility='qualified',profitability='negative',exact='90/90',evidence_class='PRIMARY',source='analysis/358h_phase3_summary.json')]
    assert bs['global_admissible'] is False and bf['original_correctness']=='FAIL'
    for r in regimes: read(r['source'])
    write('figure5_regimes.csv',regimes)
    # Deliberately reject the historical blocked-preflight scaffold.
    empty=list(csv.DictReader(read('analysis/358h_phase3_prompt_level.csv').splitlines()))
    assert len(empty)==0
    AUDIT.append(dict(source='analysis/358h_phase3_prompt_level.csv',rows=0,action='EXCLUDED: historical blocked-preflight header-only scaffold'))
    for p in ['analysis/358h_phase3_decomposition.csv','analysis/358h_threshold_input_cpu.json',
              'analysis/358h_threshold_input_npu.json','scripts/platform/358h/phase3_heterogeneous_runner.py',
              'scripts/platform/358h/process_phase1_phase2_results.py','scripts/platform/358h/analyze_phase3_campaign.py',
              'scripts/summarize_m4_confirmatory.py','scripts/summarize_m4_humaneval.py',
              'reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.csv','reports/5070ti/WINDOWS_EXACT_VERIFICATION_COST.csv',
              'reports/b570/B570_VERIFICATION_MECHANISM.md','reports/b570/B570_HUMANEVAL30_DIAGNOSTIC.md',
              'reports/b570/B570_CORRECTNESS_GATE.md','reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md',
              'reports/358h/358H_DRAFT_DEVICE_CHARACTERIZATION.md','reports/m4/M4_CONFIRMATORY_VALIDATION.md',
              'reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md']:
        read(p)
    source_lock=[]
    for p in sorted(SOURCES):
        b=(ROOT/p).read_bytes()
        source_lock.append(dict(path=p,source_commit=SOURCE_COMMIT,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),
            git_blob_sha1=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
    (DATA/'source_lock.json').write_text(json.dumps(source_lock,indent=2)+'\n')
    (HERE/'qa/data_quality.json').write_text(json.dumps(dict(status='PASS',profiles=AUDIT,notes=[
        'Figure IDs follow user request: F2 is paths and F3 is M4, overriding older outline numbering.',
        'Windows CSV BOM and CRLF are parsed explicitly; original source bytes retained.',
        'Phase-3 prompt_summary has request grain: 180 rows, not 60 prompt aggregates.',
        'B570 old reconnection-contaminated fallback cells 2.0352/2.0177 are excluded.',
        'B570 formal V2 NOT RUN; only explicitly diagnostic post-gate fast and final serialized cells used.',
        'Phase-1 raw run files are not tracked separately; CSV/JSON summaries and retained TPOT sample vectors support checks.',
        'Micro ranges are across tested contexts, not confidence intervals or matched cross-platform comparisons.'
    ]),indent=2)+'\n')
    print('PASS: extracted 11 micro cells, 2 M4 contrasts, 6 Phase-1 cells, 2 Phase-3 paths, 8 regimes')

if __name__=='__main__': main()
