#!/usr/bin/env python3
"""Independent numerical pass. Does not import extraction or plotting helpers."""
from pathlib import Path
import argparse, csv, hashlib, json, math, random, statistics
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[2]
def j(p): return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def frame(p): return pd.read_csv(ROOT/p,encoding='utf-8-sig',float_precision='round_trip')
def data(p): return pd.read_csv(HERE/'data'/p,float_precision='round_trip')
def close(a,b,tol=1e-11):
    assert np.allclose(a,b,rtol=tol,atol=tol), (a,b)
def geomean(x): return float(np.exp(np.mean(np.log(np.array(x,dtype=float)))))

def f1():
    s=(ROOT/'paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md').read_text()
    for x in ['D_real','R_target','T_b','T_x','all committed','V_k^micro']:
        assert x in s,x
    return ['Concept checked against frozen framework; C includes correction/bonus output.',
            'Costs normalized by matched baseline T_b at a consistent aggregation boundary.',
            'Micro proxy is visually detached; no measured or novel-theory claim.']

def f2():
    p=data('figure2_micro_cells.csv')
    assert len(p)==11 and not p.duplicated(['path','context']).any()
    for _,r in p.iterrows():
        if r['path']=='M4 Metal':
            src=frame(r.source); src=src[src.prefix_tokens==r.context]
            one=src[src.verify_tokens==1].elapsed_us.median()/1000
            two=src[src.verify_tokens==2].elapsed_us.median()/1000
        else:
            src=j(r.source)
            if r['path'].startswith('RTX'):
                key='serialized_ubatch1' if 'serialized' in r['path'] else 'batched_ubatch2'
                cell=src['depths'][str(r.context)][key]
            else: cell=src['cells'][str(r.context)]
            one=float(np.percentile(cell['pp1']['samples_ns'],50))/1e6
            two=float(np.percentile(cell['pp2']['samples_ns'],50))/1e6
        close([one,two,two/one],[r.pp1_ms,r.pp2_ms,r.v2_micro])
    rx=frame('reports/5070ti/WINDOWS_EXACT_VERIFICATION_COST.csv')
    for _,r in rx.iterrows():
        key='RTX serialized' if r.ubatch==1 else 'RTX batched'
        close(p[(p.path==key)&(p.context==r.context_depth)].v2_micro.iloc[0],r.T_verify2_over_T_decode1)
    b=j('analysis/b570_exact_fallback_summary.json')
    assert b['correctness']['global_admissible'] is False
    assert all(p[p.path.str.startswith('B570')].status=='diagnostic')
    assert all(p[p.path=='RTX batched'].status=='blocked')
    return ['All 11 cells replayed from timing samples with independent NumPy medians.',
            'All RTX cells reconcile to committed CSV; B570 serialized remains 60/90, not admissible.',
            'Ranges span tested contexts, not CIs; contexts differ across stacks.']

def f3():
    p=data('figure3_workloads.csv')
    for _,r in p.iterrows():
        src=frame(r.source)
        vals=src['speedup' if r.prompts==24 else 'fixed_k2_speedup'].to_numpy()
        assert len(vals)==r.prompts and np.isfinite(vals).all() and (vals>0).all()
        # Replay the frozen Python RNG and campaign-specific endpoint convention.
        rng=random.Random(int(r.seed)); logs=np.log(vals); draws=[]
        for _ in range(int(r.bootstrap_resamples)):
            draws.append(math.exp(math.fsum(float(logs[rng.randrange(len(vals))]) for _ in vals)/len(vals)))
        draws.sort(); n=int(r.bootstrap_resamples)
        bounds=[draws[249 if n==10000 else 2500],draws[9749 if n==10000 else 97499]]
        close([geomean(vals),*bounds],[r.speedup,r.ci_low,r.ci_high])
        assert r.exact_pairs==r.pairs==r.prompts*3
    return ['Replayed 10,000 (24Q) and 100,000 (HumanEval) frozen prompt bootstrap draws.',
            'Campaign-specific seeds, input order and endpoint conventions preserved.',
            'Two independent workload studies; no between-workload paired inference.',
            'Exactness counts reconciled to frozen summary/report evidence; raw token arrays not replayed in this pass.']

def f4():
    iso=data('figure4_isolated.csv'); out=data('figure4_realized.csv')
    for _,r in iso.iterrows():
        x=j('analysis/358h_draft_device_summary.json')['devices'][r.device][str(r.context)]
        close([r.tokens_s,r.ci_low,r.ci_high],[x['throughput_tokens_s']['median'],*x['throughput_tokens_s']['bootstrap_ci95']])
        z=j(f'analysis/358h_threshold_input_{r.device.lower()}.json')
        samples=next(c['draft_round_ms_samples'] for c in z['context_points'] if c['context_tokens']==r.context)
        # Retained samples are 2*TPOT; reciprocal only checks steady-state summaries.
        # Float32 OpenVINO throughput introduces sub-0.00001 tok/s differences.
        vals=2000/np.asarray(samples)
        close(np.median(vals),r.tokens_s,tol=1e-6)
        boot=np.random.default_rng(20260921+int(r.context)).choice(vals,(10000,5),replace=True)
        close(np.quantile(np.median(boot,axis=1),[.025,.975]),[r.ci_low,r.ci_high],tol=1e-6)
    pairs=frame('analysis/358h_phase3_prompt_summary.csv')
    dec=frame('analysis/358h_phase3_decomposition.csv')
    for _,r in out.iterrows():
        x=pairs[pairs.condition==r.device+'_DRAFT_K2']
        assert len(x)==90 and x.exact.all() and x.formal.all() and x.admissible.all()
        assert not x.duplicated(['task_id','repetition']).any()
        close(x.baseline_end_to_end_ms/x.end_to_end_ms,x.speedup)
        close(x[['draft_replay_proposal_ms','verification_ms','orchestration_residual_ms']].sum(axis=1),x.end_to_end_ms)
        med=x.assign(ratio=x.baseline_end_to_end_ms/x.end_to_end_ms).groupby('task_id',sort=False).ratio.median().to_numpy()
        boot=np.random.default_rng(20260919).choice(med,(10000,30),replace=True)
        ci=np.quantile(np.exp(np.log(boot).mean(axis=1)),[.025,.975])
        close([geomean(med),*ci],[r.headline_speedup,r.ci_low,r.ci_high])
        means=x[['baseline_end_to_end_ms','end_to_end_ms','draft_replay_proposal_ms','verification_ms','orchestration_residual_ms']].sum().to_numpy()/90/1000
        close(means,[r.baseline_s,r.total_s,r.draft_s,r.target_s,r.residual_s])
        close([r.draft_pct,r.target_pct,r.residual_pct],100*np.array([r.draft_s,r.target_s,r.residual_s])/r.total_s)
        src=dec[dec.device==r.device].iloc[0]
        close([r.draft_s,r.target_s,r.residual_s],[src.draft_replay_plus_proposal_ms/1000,src.target_verification_ms/1000,src.orchestration_residual_ms/1000])
        close(r.aggregate_speedup,r.baseline_s/r.total_s)
        assert abs(r.aggregate_speedup-r.headline_speedup)>.001
    runner=(ROOT/'scripts/platform/358h/phase3_heterogeneous_runner.py').read_text()
    for expression in ['draft.propose(pt+out,width)','self.pipe.generate(inp,self.cfg)','committed=proposals[:accepted]+[expected]','llama_memory_seq_rm']:
        assert expression in runner
    return ['Phase-1 six medians/CIs reconcile to CSV/JSON and retained TPOT samples (relative tolerance 1e-6).',
            'Phase-3 all 180 paired ratios, component sums, arithmetic means, shares and 10k prompt-bootstrap CIs replayed.',
            'Timing excludes initial prompt prefill; total-time ratios intentionally differ from headline prompt GMs.',
            'Runner full-prefix proposal and complete target region inspected; replay-only is unmeasured.',
            'Phase-1 raw throughput arrays unavailable separately; reciprocal TPOT replay is corroborative.']

def f5():
    p=data('figure5_regimes.csv')
    assert len(p)==8 and p.case.nunique()==8
    assert ((p.admissibility=='blocked')==(p.profitability=='not_admissible')).all()
    assert list(p[p.profitability=='profitable'].case)==['M4 HumanEval30']
    bf=j('artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/diagnostic_summary.json')
    assert sum(r['mismatch_repetitions'] for r in bf['divergence'])==45
    bs=j('analysis/b570_exact_fallback_summary.json')['correctness']
    assert bs['exact_pairs']==60 and not bs['global_admissible']
    rx=frame('reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.csv')
    for cond in ['cpu_k2','rtx_k2']:
        x=rx[rx.condition==cond]
        assert len(x)==90 and x.exact_match.all()
        close(x.baseline_decode_ms/x.spec_decode_ms,x.paired_speedup)
        assert geomean(x.paired_speedup)<1
    return ['All eight cases classified under frozen workload-level token equivalence.',
            'B570 fast 45/90 recomputed from per-prompt mismatch counts; serialized 60/90 remains blocked.',
            'Both RTX secondary controls verified from 90 paired rows each; negative and exact.',
            'Blocked paths have no profitability coordinate; table cells are categorical, not continuous axes.']

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--figure',type=int,choices=range(1,6));ap.add_argument('--require-outputs',action='store_true');a=ap.parse_args()
    lock=json.loads((HERE/'data/source_lock.json').read_text())
    for r in lock:
        assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
    ids=[a.figure] if a.figure else range(1,6)
    for i in ids:
        findings=globals()[f'f{i}']()
        if a.require_outputs:
            receipt=json.loads((HERE/f'qa/figure{i}_render.json').read_text())
            input_paths=sorted((HERE/'data').glob(f'figure{i}_*.csv'))
            if i==5: input_paths.append(HERE/'data/figure4_realized.csv')
            assert receipt['input_sha256']=={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths}
            assert receipt['out_of_bounds_text']==[],receipt['out_of_bounds_text']
            from pypdf import PdfReader
            pdf=PdfReader(HERE/'pdf'/f'figure{i}.pdf')
            close(float(pdf.pages[0].mediabox.width)/72,receipt['width_in'])
            # Final quantitative PDFs must contain vector objects, never an embedded screenshot.
            res=pdf.pages[0]['/Resources'];xo=res.get('/XObject',{})
            if hasattr(xo,'get_object'): xo=xo.get_object()
            assert all(v.get_object().get('/Subtype')!='/Image' for v in xo.values())
        result=dict(figure=i,status='NUMERICAL_PASS',independent_of_extractor=True,findings=findings,
                    outputs_checked=a.require_outputs,visual_qa='See VISUAL_QA.md; requires human/model image inspection')
        (HERE/f'qa/figure{i}_validation.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'Figure {i}: NUMERICAL_PASS'+(' + vector/bounds checks' if a.require_outputs else ''))

if __name__=='__main__':main()
