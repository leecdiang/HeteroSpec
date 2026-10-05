#!/usr/bin/env python3
"""Deterministically process frozen 358H Phase-1/2 observations."""
from __future__ import annotations
import csv, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
CPU=ROOT/'runs/358h/phase1/358h-p1-cpu-20260918T082639-63294459'
NPU=ROOT/'runs/358h/phase1/358h-p1-npu-20260918T082821-e1471810'
ENERGY=ROOT/'runs/358h/phase1/358h-p1-energy-cpu-20260918T082952'
TB=ROOT/'runs/358h/phase2/358h-tb-20260918T094615/session.json'
V2=ROOT/'runs/358h/phase2/358h-v2-20260918T104308/session.json'
EXACT=ROOT/'runs/358h/phase2/358h-exactness-20260918T092722/result.json'
GATE=ROOT/'scripts/platform/358h/threshold_gate_v2.py'
ANALYSIS=ROOT/'analysis'; REPORTS=ROOT/'reports/358h'

def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def q(values):
    a=np.asarray(values,float); return {'values':[float(x) for x in a],'median':float(np.median(a))}
def ci(values,seed):
    a=np.asarray(values,float); rng=np.random.default_rng(seed); med=np.median(rng.choice(a,(10000,len(a)),replace=True),axis=1)
    return [float(np.quantile(med,.025)),float(np.quantile(med,.975))]
def phase1(root,device):
    s=load(root/'session.json'); out={}
    for cell in s['cells']:
        ctx=int(cell['context_tokens']); rows=[load(root/(rid+'.json')) for rid in cell['runs']]
        out[ctx]={'device':device,'runs':rows,'warmups':cell['warmups']}
    return out
def target_rows(path):
    s=load(path); out={}
    for cell in s['cells']:
        out[int(cell['context_tokens'])]=cell['formal']['rows']
    return out
def main():
    ANALYSIS.mkdir(exist_ok=True); REPORTS.mkdir(parents=True,exist_ok=True)
    exact=load(EXACT)
    if exact.get('status')!='PASS' or exact.get('exact_pairs')!=18: raise RuntimeError('exactness gate inadmissible')
    p1={'CPU':phase1(CPU,'CPU'),'NPU':phase1(NPU,'NPU')}; tb=target_rows(TB); v2=target_rows(V2)
    energy={}
    for p in ENERGY.glob('c*-r*.energy.json'):
        x=load(p); energy.setdefault(int(x['context_tokens']),[]).append(float(x['package_j_per_output_token']))
    draft_rows=[]; machine={'schema':'heterospec.358h.draft_device_summary.v1','formal':True,'devices':{}}
    for device,cells in p1.items():
        machine['devices'][device]={}
        for ctx in sorted(cells):
            runs=cells[ctx]['runs']; metrics={name:[float(r[name]) for r in runs] for name in
                ('host_generate_duration_ms','ttft_ms','tpot_ms','throughput_tokens_s','rss_start_bytes','rss_end_bytes')}
            summary={'repetitions':len(runs),'warmups':cells[ctx]['warmups'],'failures':0,
                     'output_tokens':[int(r['output_tokens']) for r in runs],
                     'token_hashes':[r['generated_token_ids_sha256'] for r in runs]}
            for name,vals in metrics.items(): summary[name]={'median':float(np.median(vals)),'bootstrap_ci95':ci(vals,20260921+ctx)}
            if device=='CPU': summary['package_j_per_output_token']={'median':float(np.median(energy[ctx])),'values':energy[ctx],'boundary':'RAPL_Package0_PKG CPU package'}
            else: summary['energy']='NOT_ADMISSIBLE'
            machine['devices'][device][str(ctx)]=summary
            draft_rows.append({'device':device,'context':ctx,'repetitions':len(runs),
                'median_host_ms':summary['host_generate_duration_ms']['median'],'median_ttft_ms':summary['ttft_ms']['median'],
                'median_tpot_ms':summary['tpot_ms']['median'],'median_tokens_s':summary['throughput_tokens_s']['median'],
                'package_j_per_output_token':summary.get('package_j_per_output_token',{}).get('median','NOT_ADMISSIBLE')})
    (ANALYSIS/'358h_draft_device_summary.json').write_text(json.dumps(machine,indent=2)+'\n',encoding='utf-8')
    with (ANALYSIS/'358h_draft_device_summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(draft_rows[0]));w.writeheader();w.writerows(draft_rows)
    md=['# 358H draft-device characterization','','Formal Track-L latency is telemetry-OFF. CPU Track-E duration is used only for energy integration.','']
    for row in draft_rows: md.append(f"- {row['device']} ctx {row['context']}: host median {row['median_host_ms']:.3f} ms, TTFT {row['median_ttft_ms']:.3f} ms, TPOT {row['median_tpot_ms']:.3f} ms, {row['median_tokens_s']:.3f} tok/s, energy {row['package_j_per_output_token']}")
    md += ['','NPU energy: NOT_ADMISSIBLE.']
    (REPORTS/'358H_DRAFT_DEVICE_CHARACTERIZATION.md').write_text('\n'.join(md)+'\n',encoding='utf-8')

    combined={'schema':'heterospec.358h.threshold_summary.v1','formal':True,'exactness':{'status':'PASS','pairs':18},'devices':{}}
    for device,cells in p1.items():
        points=[]
        for ctx in (512,2048,8192):
            td=[2*float(r['tpot_ms']) for r in cells[ctx]['runs']]
            tb_samples=[float(x)/1e6 for x in tb[ctx][0]['samples_ns']]
            pp1=next(r for r in v2[ctx] if int(r['n_prompt'])==1); pp2=next(r for r in v2[ctx] if int(r['n_prompt'])==2)
            fractions=[float(b)/float(a) for a,b in zip(pp1['samples_ns'],pp2['samples_ns'])]
            points.append({'context_tokens':ctx,'draft_round_ms_samples':td,'target_token_ms_samples':tb_samples,
                           'verification_fraction_samples':fractions,'residual_ms_favorable_bound':0,
                           'verification_exactness_admissible':True})
        inp=ANALYSIS/f'358h_threshold_input_{device.lower()}.json';out=ANALYSIS/f'358h_threshold_gate_{device.lower()}.json'
        inp.write_text(json.dumps({'context_points':points},indent=2)+'\n',encoding='utf-8')
        subprocess.run([sys.executable,str(GATE),str(inp),str(out),'--seed','20260919','--resamples','10000'],check=True,capture_output=True,text=True)
        combined['devices'][device]=load(out)
    (ANALYSIS/'358h_threshold_summary.json').write_text(json.dumps(combined,indent=2)+'\n',encoding='utf-8')
    lines=['# 358H draft threshold analysis','','Formula: `speedup = T_b*C/(T_d(2)+V_2*T_b+T_x)`; T_x=0 favorable bound. Exactness: 18/18 PASS.','']
    for device,result in combined['devices'].items():
        lines.append(f"## {device} — overall {result['overall_classification']}")
        lines.append('')
        for p in result['points']:
            lines.append(f"- {p['context_tokens']}: {p['classification']}; central median {p['central_C2']['median']:.4f}, CI95 [{p['central_C2']['ci95'][0]:.4f}, {p['central_C2']['ci95'][1]:.4f}]; optimistic CI95 [{p['optimistic_C3']['ci95'][0]:.4f}, {p['optimistic_C3']['ci95'][1]:.4f}]")
        lines.append('')
    lines.append('Phase 3 was not started.')
    (REPORTS/'358H_DRAFT_THRESHOLD_ANALYSIS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'draft_summary':str(ANALYSIS/'358h_draft_device_summary.json'),'threshold_summary':combined},indent=2))
if __name__=='__main__': main()

