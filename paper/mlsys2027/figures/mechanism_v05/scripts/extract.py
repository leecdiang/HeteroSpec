#!/usr/bin/env python3
"""Extract small evidence anchors from closed sources; never run experiments."""
from pathlib import Path
import csv, hashlib, json, math, statistics as st

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[3]
BASE = '974e84540b5193b416e20920629260ff320f759d'
SOURCES, AUDIT = set(), []

def read(p):
    SOURCES.add(p)
    return (ROOT / p).read_text(encoding='utf-8-sig')

def js(p):
    return json.loads(read(p))

def rows(p, keys, n):
    r = list(csv.DictReader(read(p).splitlines()))
    assert len(r) == n, (p, len(r))
    assert len({tuple(x[k] for k in keys) for x in r}) == n, p
    assert all(v not in ('', None) for x in r for v in x.values()), p
    AUDIT.append(dict(source=p, rows=n, grain=keys, duplicate_keys=0, missing_cells=0))
    return r

def gm(xs):
    return math.exp(st.fmean(map(math.log, xs)))

def main():
    (HERE/'data').mkdir(parents=True, exist_ok=True)
    # Scientific definitions, final narrative, style, and timing semantics.
    for p in [
        'paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md',
        *['paper/mlsys2027/manuscript/sections/'+n+'.tex' for n in
          ['01_introduction','02_framework','04_outcomes','05_diagnoses','06_synthesis']],
        'paper/mlsys2027/manuscript/main.tex',
        'paper/mlsys2027/figures/FIGURE_STYLE_REVIEW_V04.md',
        'paper/mlsys2027/figures/style_v04/README.md',
        'reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md',
        'reports/5070ti/CUDA_DIVERGENCE_NUMERICAL_DIAGNOSIS.md',
        'reports/b570/B570_VERIFICATION_MECHANISM.md',
        'reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md',
        'reports/358h/358H_RUNNER_SEMANTICS_MAPPING.md',
        'scripts/platform/358h/phase3_heterogeneous_runner.py',
        'benchmarks/m4_code_conditioned_30q/preregistration.json',
        'analysis/README.md']:
        read(p)
    a=js('analysis/m4_confirmatory_summary.json')
    b=js('analysis/m4_humaneval_summary.json')['conditions']['fixed_k2']
    ra=rows('analysis/m4_confirmatory_prompt_summary.csv',['question_id'],24)
    rb=rows('analysis/m4_humaneval_prompt_summary.csv',['task_id'],30)
    assert abs(gm([float(r['speedup']) for r in ra])-a['geomean_speedup'])<1e-12
    assert abs(gm([float(r['fixed_k2_speedup']) for r in rb])-b['prompt_geomean_speedup'])<1e-12
    m4=dict(representative=dict(speedup=a['geomean_speedup'],ci95=a['bootstrap_95_ci'],
              exact_pairs=a['exact_pairs'],pairs=a['paired_repetitions']),
            humaneval=dict(speedup=b['prompt_geomean_speedup'],ci95=b['prompt_bootstrap_95_ci'],
              exact_pairs=b['exact_pairs'],pairs=b['pair_count']),
            status='PRIMARY; qualified within each separate frozen study',
            contrast='Observed opposite regimes; not assigned to either diagnosis; not workload-only causality')
    mr=rows('work/m4/llama_verify_q8_synced.csv',['prefix_tokens','verify_tokens','repetition'],84)
    m4['v2_micro']={}
    for ctx in ('512','2048','8192'):
        cells=[[float(r['elapsed_us']) for r in mr if r['prefix_tokens']==ctx and r['verify_tokens']==k] for k in ('1','2')]
        assert list(map(len,cells))==[7,7]
        m4['v2_micro'][ctx]=st.median(cells[1])/st.median(cells[0])
    raw=js('artifacts/windows_verification_mechanism/windows-exact-verification-microbench.json')
    rr=rows('reports/5070ti/WINDOWS_EXACT_VERIFICATION_COST.csv',['context_depth','path'],4)
    rtx={}
    for path in ('batched_ubatch2','serialized_ubatch1'):
        cells={}
        for ctx, pp in raw['depths'].items():
            x=pp[path]
            assert len(x['pp1']['samples_ns'])==len(x['pp2']['samples_ns'])==20
            val=st.median(x['pp2']['samples_ns'])/st.median(x['pp1']['samples_ns'])
            cr=next(r for r in rr if r['path']==path and r['context_depth']==ctx)
            assert abs(val-float(cr['T_verify2_over_T_decode1']))<1e-12
            cells[ctx]=val
        rtx[path]=dict(cells=cells,range=[min(cells.values()),max(cells.values())],
          status='correctness-blocked diagnostic' if path.startswith('batched') else 'qualified exact secondary control')
    controls=rows('reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.csv',['condition','task_id','repetition'],180)
    rtx['serialized_controls']={}
    for condition in ('cpu_k2','rtx_k2'):
        selected=[r for r in controls if r['condition']==condition]
        assert len(selected)==90 and all(r['exact_match']=='True' for r in selected)
        rtx['serialized_controls'][condition]=dict(exact_pairs=90,pairs=90,evidence_class='SECONDARY')
    bf=js('artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/diagnostic_summary.json')
    bs=js('analysis/b570_exact_fallback_summary.json')
    assert bf['original_correctness']=='FAIL' and not bs['correctness']['global_admissible']
    b570=dict(fast=dict(exact_pairs=bf['counts']['exact_pairs'],pairs=bf['counts']['exact_pairs']+bf['counts']['mismatch_pairs'],globally_admissible=False),
              serialized=bs['correctness'],status='DIAGNOSTIC; globally inadmissible in both paths')
    isolated=rows('analysis/358h_draft_device_summary.csv',['device','context'],6)
    isojson=js('analysis/358h_draft_device_summary.json')
    s=js('analysis/358h_phase3_summary.json')
    requests=rows('analysis/358h_phase3_prompt_summary.csv',['condition','task_id','repetition'],180)
    state={}
    for dev in ('CPU','NPU'):
        tr=[r for r in requests if r['condition']==dev+'_DRAFT_K2']
        assert len(tr)==90 and all(r['exact']==r['formal']==r['admissible']=='True' for r in tr)
        tasks=list(dict.fromkeys(r['task_id'] for r in tr)); assert len(tasks)==30
        prompt=[]
        for task in tasks:
            q=[r for r in tr if r['task_id']==task]
            assert sorted(int(r['repetition']) for r in q)==[0,1,2]
            prompt.append(st.median(float(r['speedup']) for r in q))
        total=st.fmean(float(r['end_to_end_ms']) for r in tr)
        draft=st.fmean(float(r['draft_replay_proposal_ms']) for r in tr)
        target=st.fmean(float(r['verification_ms']) for r in tr)
        residual=st.fmean(float(r['orchestration_residual_ms']) for r in tr)
        assert abs(total-draft-target-residual)<1e-8
        assert abs(gm(prompt)-s['performance'][dev]['geometric_mean_speedup'])<1e-12
        v=float(next(r for r in isolated if r['device']==dev and r['context']=='8192')['median_tokens_s'])
        assert v==isojson['devices'][dev]['8192']['throughput_tokens_s']['median']
        state[dev]=dict(isolated_8192_tokens_s=v,isolated_ci95=isojson['devices'][dev]['8192']['throughput_tokens_s']['bootstrap_ci95'],
           speedup=s['performance'][dev]['geometric_mean_speedup'],ci95=s['performance'][dev]['bootstrap_ci95'],
           exact_pairs=s['correctness'][dev]['exact_pairs'],pairs=s['correctness'][dev]['total_pairs'],
           draft_pct=100*draft/total,target_pct=100*target/total,
           total_mean_s=total/1000,status='PRIMARY exact negative; MECHANISM_SUPPORTED timed regions')
        assert abs(draft/total-s['decomposition'][dev]['fractions_of_speculative_time']['draft_replay_plus_proposal'])<1e-12
        assert abs(target/total-s['decomposition'][dev]['fractions_of_speculative_time']['target_verification'])<1e-12
    assert not list(csv.DictReader(read('analysis/358h_phase3_prompt_level.csv').splitlines()))
    out=dict(source_commit=BASE,m4=m4,rtx=rtx,b570=b570,state=state,
        boundaries=dict(timing='integrated post-prefill decode; excludes loading and initial prefill',
          micro='target-forward proxy, not complete R_target; context range is not a CI',
          state='Replay and proposal are inseparable within one synchronous OpenVINO call',
          mechanism='configuration-scoped and non-exhaustive; not a new theoretical model'))
    (HERE/'data/evidence.json').write_text(json.dumps(out,indent=2)+'\n')
    (HERE/'data/quality.json').write_text(json.dumps(dict(profiles=AUDIT,
        excluded=['analysis/358h_phase3_prompt_level.csv: historical header-only blocked-preflight scaffold',
          'B570 formal verification: NOT RUN after gate failure; later paths diagnostic only',
          'B570 contaminated early serialized values excluded; legacy V2_exact is not an exactness label'],
        note='No new experiments or statistical estimates; existing point estimates corroborated, original CI bounds retained.'),indent=2)+'\n')
    lock=[]
    for p in sorted(SOURCES):
        b=(ROOT/p).read_bytes()
        lock.append(dict(path=p,source_commit=BASE,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),
            git_blob_sha1=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
    (HERE/'data/source_lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    print(f'Extracted anchors; {len(AUDIT)} table profiles, {len(lock)} locked sources.')

if __name__=='__main__': main()
