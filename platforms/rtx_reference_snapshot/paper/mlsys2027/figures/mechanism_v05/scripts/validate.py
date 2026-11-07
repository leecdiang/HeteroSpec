#!/usr/bin/env python3
"""Independent check: no imports from extraction or drawing helpers."""
from pathlib import Path
import csv, hashlib, json, math, re, statistics, subprocess, xml.etree.ElementTree as ET
import numpy as np
import fitz

HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[3]

def raw(p): return (ROOT/p).read_text(encoding='utf-8-sig')
def js(p): return json.loads(raw(p))
def csvrows(p): return list(csv.DictReader(raw(p).splitlines()))
def near(a,b): assert abs(float(a)-float(b))<1e-11,(a,b)
def gm(xs): return float(np.exp(np.mean(np.log(xs))))

def main():
    e=json.loads((HERE/'data/evidence.json').read_text())
    checks=[]
    for lock in json.loads((HERE/'data/source_lock.json').read_text()):
        b=(ROOT/lock['path']).read_bytes()
        assert len(b)==lock['bytes']
        assert hashlib.sha256(b).hexdigest()==lock['sha256']
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==lock['git_blob_sha1']
    checks.append('All 32 input files unchanged; Git blob hashes checked against exact base separately.')
    # Independent original-table point-estimate replay; original CIs are not re-estimated.
    a=js('analysis/m4_confirmatory_summary.json')
    b=js('analysis/m4_humaneval_summary.json')['conditions']['fixed_k2']
    for key,s,col,p in [('representative',a,'speedup','analysis/m4_confirmatory_prompt_summary.csv'),
                       ('humaneval',b,'fixed_k2_speedup','analysis/m4_humaneval_prompt_summary.csv')]:
        rows=csvrows(p); v=gm([float(r[col]) for r in rows]);near(v,e['m4'][key]['speedup'])
        assert e['m4'][key]['ci95']==s['bootstrap_95_ci' if key=='representative' else 'prompt_bootstrap_95_ci']
        assert e['m4'][key]['exact_pairs']==s['exact_pairs']==e['m4'][key]['pairs']
    checks.append('M4: both prompt GMs independently reproduced; all original CI bounds and 72/72, 90/90 counts retained.')
    micro=js('artifacts/windows_verification_mechanism/windows-exact-verification-microbench.json')
    for path in ('batched_ubatch2','serialized_ubatch1'):
        values=[]
        for ctx,cells in micro['depths'].items():
            c=cells[path];assert all(len(c[k]['samples_ns'])==20 for k in ('pp1','pp2'))
            ratio=float(np.median(c['pp2']['samples_ns'])/np.median(c['pp1']['samples_ns']))
            near(ratio,e['rtx'][path]['cells'][ctx]);values.append(ratio)
        assert np.allclose(sorted(values),e['rtx'][path]['range'],rtol=0,atol=1e-12)
    # Confirm the second, secondary path is actually qualified; do not imply every RTX path fails.
    rtx=csvrows('reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.csv')
    assert len(rtx)==180
    for condition in ('cpu_k2','rtx_k2'):
        r=[x for x in rtx if x['condition']==condition]
        assert len(r)==90 and all(x['exact_match']=='True' for x in r)
        assert e['rtx']['serialized_controls'][condition]['exact_pairs']==90
    checks.append('RTX: all four micro ratios independently reproduced from 20-repetition raw cells; original reports bound the batched failure and serialized exact control.')
    bf=js('artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/diagnostic_summary.json')
    bs=js('analysis/b570_exact_fallback_summary.json')
    assert e['b570']['fast']['exact_pairs']==bf['counts']['exact_pairs']==45
    assert e['b570']['fast']['pairs']==bf['counts']['exact_pairs']+bf['counts']['mismatch_pairs']==90
    assert e['b570']['serialized']==bs['correctness']
    assert bs['correctness']['exact_pairs']==60 and bs['correctness']['total_pairs']==90
    assert not bs['correctness']['global_admissible'] and bf['original_correctness']=='FAIL'
    checks.append('B570: 45/90 and 60/90 confirmed; both diagnostic and globally inadmissible; legacy field names not promoted.')
    p1=csvrows('analysis/358h_draft_device_summary.csv')
    p1j=js('analysis/358h_draft_device_summary.json'); p3=csvrows('analysis/358h_phase3_prompt_summary.csv')
    p3j=js('analysis/358h_phase3_summary.json')
    for dev in ('CPU','NPU'):
        row=next(r for r in p1 if r['device']==dev and r['context']=='8192')
        near(row['median_tokens_s'],e['state'][dev]['isolated_8192_tokens_s'])
        assert e['state'][dev]['isolated_ci95']==p1j['devices'][dev]['8192']['throughput_tokens_s']['bootstrap_ci95']
        r=[r for r in p3 if r['condition']==dev+'_DRAFT_K2']; assert len(r)==90
        assert all(x['formal']==x['admissible']==x['exact']=='True' for x in r)
        promptids=set(x['task_id'] for x in r); assert len(promptids)==30
        ratios=[]
        for task in promptids:
            reps=[x for x in r if x['task_id']==task]; assert len(reps)==3
            # Independent denominator/numerator reconstruction, not stored speedup field.
            ratios.append(float(np.median([float(x['baseline_end_to_end_ms'])/float(x['end_to_end_ms']) for x in reps])))
        near(gm(ratios),e['state'][dev]['speedup'])
        assert e['state'][dev]['ci95']==p3j['performance'][dev]['bootstrap_ci95']
        total=sum(float(x['end_to_end_ms']) for x in r)
        near(100*sum(float(x['draft_replay_proposal_ms']) for x in r)/total,e['state'][dev]['draft_pct'])
        near(100*sum(float(x['verification_ms']) for x in r)/total,e['state'][dev]['target_pct'])
        assert e['state'][dev]['exact_pairs']==e['state'][dev]['pairs']==90
    checks.append('358H: isolated 8192 medians/CIs; both 90/90 counts, prompt GMs from matched times, unchanged headline CIs, and ratio-of-totals fractions verified.')
    source=raw('scripts/platform/358h/phase3_heterogeneous_runner.py')
    assert 'draft.propose(pt+out,width)' in source and 'r=self.pipe.generate(inp,self.cfg)' in source
    report=raw('reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md')
    assert 'indivisible synchronous OpenVINO LLMPipeline call' in report
    assert 'post-prefill' in report and 'proposal-only values are not available' in report
    assert not csvrows('analysis/358h_phase3_prompt_level.csv')
    checks.append('State interface and post-prefill boundary corroborated by closed formal report and qualification-runner/mapping; no replay-only timing or source-identity upgrade.')
    outputs={}
    for which in ('a','b'):
        p=HERE/('candidate_'+which);d=fitz.open(p/'mechanism.pdf');page=d[0]
        assert len(d)==1 and not page.get_images(full=True)
        assert abs(page.rect.width/72-6.75)<.0001
        assert abs(page.rect.height/72-({'a':2.4,'b':2.1}[which]))<.0001
        spans=[s for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for s in line['spans']]
        assert all(fitz.Rect(s['bbox']).x0>=-.05 and fitz.Rect(s['bbox']).y0>=-.05 and fitz.Rect(s['bbox']).x1<=page.rect.width+.05 and fitz.Rect(s['bbox']).y1<=page.rect.height+.05 for s in spans)
        fonts=[]
        for f in page.get_fonts(full=True):
            _,ext,_,data=d.extract_font(f[0]); assert data and ext!='n/a',f
            fonts.append(f[3])
        xml=ET.parse(p/'mechanism.svg');assert not any(x.tag.rsplit('}',1)[-1]=='image' for x in xml.iter())
        actual=' '.join(page.get_text().split()); src=(p/'mechanism.tex').read_text()
        for phrase in ['Local opportunity','Path qualification','Stateful realization','Realized outcome',
                       'Chosen token-ID contract','admissible path','blocked / diagnostic only',
                       'realized draft cost','complete target work','residual cost','committed output',
                       'Qualified integrated' if which=='a' else 'Qualified post-prefill decode','post-prefill decode','Observed regimes:',
                       'profitable','exact but negative','configuration-scoped and non-exhaustive']:
            assert phrase in actual,(which,phrase)
        for phrase in [r'Acceptance is not $C$',r'$\microv$ is not complete $\rtarget$',
                       'dash pattern=on 2bp off 1.5bp',r'\fill[accent]',r'fill=white']:
            assert phrase in src,(which,phrase)
        for bad in ['V2_exact','replay-only','universal solution','CUDA is broken','NPU hardware causes']:
            assert bad not in src
        cap=(p/'caption.tex').read_text(); proof=fitz.open(HERE/f'qa/proof_{which}.pdf')
        prooftext=' '.join(proof[0].get_text().split())
        for phrase in ['not a guarantee of gain','Blocked timings remain diagnostic','one synchronous OpenVINO call',
                       'Workload and session conditions differ','neither diagnosis is assigned',
                       'configuration-scoped and non-exhaustive','timing excludes loading and initial prompt prefill']:
            assert phrase in prooftext,(which,phrase)
        if which=='a':
            expected=[f'{v:.3f}' for v in e['rtx']['batched_ubatch2']['range']]
            expected += [f'{e["state"][dev]["isolated_8192_tokens_s"]:.2f}' for dev in ('CPU','NPU')]
            expected += [f'{e["state"]["NPU"]["draft_pct"]:.2f}',f'{e["state"]["NPU"]["speedup"]:.3f}']
            expected += [f'{e["m4"][w]["speedup"]:.3f}' for w in ('representative','humaneval')]
            expected += ['60/90','8192']
            assert all(v in actual for v in expected),(expected,actual)
            assert 'globally inadmissible' in actual and '0.983–1.009; blocked.' in actual
            # Per-anchor binding, including denominator and throughput order.
            assert '48.08 vs CPU 30.81 tok/s' in actual and '58.35% replay + proposal' in actual
            assert '24Q: 0.842' in actual and 'HE30: 1.387' in actual
            for dev in ('CPU','NPU'):
                for v in e['state'][dev]['isolated_ci95']: assert f'{v:.2f}' in prooftext
            for vs in [e['state']['NPU']['ci95'],*[e['m4'][w]['ci95'] for w in ('representative','humaneval')]]:
                for v in vs: assert f'{v:.3f}' in prooftext
            assert 'ratio of arithmetic totals of speculative post-prefill time' in prooftext
            assert 'not a CI' in prooftext
        else:
            assert 'RTX batched / B570 diagnostics: qualification failure.' in actual and '358H NPU:' in actual
            assert 'isolated advantage does not survive the tested stateful integration' in actual
            assert 'opposite observed outcomes' in actual and 'Neither diagnosis assigned' in actual
            assert not re.search(r'\d+\.\d+',actual),actual
        outputs[which]=dict(status='PASS',width_in=page.rect.width/72,height_in=page.rect.height/72,
            vector_only=True,embedded_fonts=sorted(set(fonts)),no_clipped_text=True,
            minimum_glyph_font_bp=min(s['size'] for s in spans),body_font_tex_pt=8,
            pdf_sha256=hashlib.sha256((p/'mechanism.pdf').read_bytes()).hexdigest(),
            svg_sha256=hashlib.sha256((p/'mechanism.svg').read_bytes()).hexdigest())
    result=dict(status='PASS within authored scope',checks=checks,candidates=outputs,
                limits=['No new experiment or bootstrap estimation.',
                        'Semantic support and visual inspection documented separately; automated phrase checks are not causal proof.',
                        'No manuscript integration, pagination claim, or physical printer test.'])
    (HERE/'qa/validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
