"""Build v0.12 source and verify its public arithmetic. No inference."""
from pathlib import Path
import subprocess, json, csv, statistics, math, hashlib, shutil, re, zipfile
import numpy as np

ROOT=Path(__file__).resolve().parent
def run(*args):
    return subprocess.run(args,cwd=ROOT,check=True,text=True,capture_output=True)
def verify():
    bindings=json.loads((ROOT/'evidence/SOURCE_BINDINGS.json').read_text())
    for name,expected in bindings['exports'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
    raw=list(csv.DictReader((ROOT/'evidence/rtx66/RAW_COSTS.csv').open()))
    qual=list(csv.DictReader((ROOT/'evidence/rtx66/QUALIFICATION_RECOMPUTED.csv').open()))
    assert len(raw)==len(qual)==384
    rk={(r['task'],r['condition'],int(r['repetition'])):r for r in raw}
    qk={(r['task'],r['condition'],int(r['repetition'])):r for r in qual}
    assert len(rk)==len(qk)==384 and set(rk)==set(qk)
    tasks=list(dict.fromkeys(r['task'] for r in raw));conditions={r['condition'] for r in raw}
    assert len(tasks)==24 and len(conditions)==4
    assert set(rk)=={(t,c,k) for t in tasks for c in conditions for k in range(1,5)}
    for k,r in rk.items():
        q=qk[k]
        assert r['qualified']=='True' and r['timer_unit']=='ms'
        assert all(q[f]=='True' for f in ['qualified','reference_stable','full_array_equal','endpoint_equal'])
        assert r['tokens']==q['tokens'] and r['endpoint']==q['endpoint']
        ref=qk[k[0],'scalar_reference',k[2]]
        assert q['tokens_sha256']==ref['tokens_sha256'] and q['last_id']==ref['last_id']
        assert all(math.isfinite(float(r[f])) and float(r[f])>0 for f in ['generation_ms','whole_ms'])
    for task in tasks:
        assert len({qk[task,'scalar_reference',k]['tokens_sha256'] for k in range(1,5)})==1
    summary=json.loads((ROOT/'evidence/rtx66/COST_SUMMARY.json').read_text())
    published=list(csv.DictReader((ROOT/'evidence/rtx66/TASK_COST_PAIRS.csv').open()))
    order=list(dict.fromkeys(r['task'] for r in published))
    draws=np.random.Generator(np.random.PCG64(20261008)).integers(0,24,size=(10000,24))
    outputs={};identities=0
    for timer in ['generation','whole']:
        med={(t,c):statistics.median(float(rk[t,c,k][timer+'_ms']) for k in range(1,5)) for t in tasks for c in conditions}
        for t in tasks:
            a,b,c=[med[t,x] for x in ['scalar_reference','matched_target','target_scopes']]
            assert math.isclose(a/c,(a/b)*(b/c),rel_tol=1e-12);identities+=1
        for s in summary['comparisons']:
            if s['timer']!=timer:continue
            ratios=np.array([med[t,s['baseline']]/med[t,s['candidate']] for t in order])
            gm=float(np.exp(np.log(ratios).mean()))
            ci=np.quantile(np.exp(np.log(ratios)[draws].mean(axis=1)),[.025,.975],method='linear')
            assert math.isclose(gm,s['task_median_gm'],rel_tol=1e-11)
            assert np.allclose(ci,s['descriptive_task_bootstrap_95_linear'],rtol=1e-11)
            outputs[timer+':'+s['baseline']+'/'+s['candidate']]=gm
        assert math.isclose(outputs[timer+':scalar_reference/target_scopes'],outputs[timer+':scalar_reference/matched_target']*outputs[timer+':matched_target/target_scopes'],rel_tol=1e-12)
    return dict(status='PASS',public_rows=384,qualified_public_hash_rows=384,tasks=24,task_ratio_identities=identities,aggregate_ratio_identities=2,comparisons=outputs,private_archives_reopened=False,new_inference=0)

def figure(values):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({'font.size':9,'pdf.fonttype':42,'ps.fonttype':42})
    fig,ax=plt.subplots(figsize=(3.35,2.05),layout='constrained')
    colors=['#64748b','#16807c','#d17730']
    for j,(label,cond) in enumerate([('Ordinary R',None),('Matched M','matched_target'),('Speculative C','target_scopes')]):
        heights=[1. if cond is None else 1./values[t+':scalar_reference/'+cond] for t in ['generation','whole']]
        bars=ax.bar(np.arange(2)+(j-1)*.24,heights,width=.22,color=colors[j],label=label)
        for b,v in zip(bars,heights):ax.text(b.get_x()+b.get_width()/2,v+.022,f'{v:.3f}',ha='center',fontsize=7)
    ax.set_xticks([0,1],['Generation','Resident request']);ax.set_ylabel('Normalized time (lower is faster)')
    ax.set_ylim(0,1.2);ax.legend(frameon=False,fontsize=7,ncols=3,loc='upper center')
    ax.spines[['top','right']].set_visible(False)
    (ROOT/'figures').mkdir(exist_ok=True);fig.savefig(ROOT/'figures/reference_cost.pdf');plt.close(fig)

def build():
    checks=verify();figure(checks['comparisons'])
    out=ROOT/'output';out.mkdir(exist_ok=True)
    docs={}
    for stem in ['main','appendix']:
        p=run('latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-outdir=build',stem+'.tex')
        (out/(stem+'-console.log')).write_text(p.stdout+p.stderr)
        log=(ROOT/'build'/f'{stem}.log').read_text(errors='replace')
        issues=re.findall(r'Overfull.*|.*undefined.*|.*multiply defined.*',log,re.I)
        assert not issues,issues
        name='manuscript-v0.12.0.pdf' if stem=='main' else 'appendix-v0.12.0.pdf'
        shutil.copyfile(ROOT/'build'/f'{stem}.pdf',out/name)
        run('pdftotext','-layout',str(out/name),str(out/(stem+'.txt')))
        info=run('pdfinfo',str(out/name)).stdout
        pages=int(re.search(r'Pages:\s+(\d+)',info).group(1))
        text=(out/(stem+'.txt')).read_text()
        assert not any(s in text for s in ['leecdiang','YinnHuu','/workspace/','github.com'])
        docs[stem]=dict(pages=pages,overfull=0,undefined=0,text_sha256=hashlib.sha256(text.encode()).hexdigest())
    result=dict(version='v0.12.0',evidence=checks,documents=docs,scope='Scientific baseline; author self-review; not submitted')
    (out/'BUILD_QA.json').write_text(json.dumps(result,indent=2)+'\n')
    sources=[p for p in ROOT.rglob('*') if p.is_file() and not any(x in p.relative_to(ROOT).parts for x in ['build','output','__pycache__'])]
    with zipfile.ZipFile(out/'portable-source-v0.12.0.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(sources):z.write(p,p.relative_to(ROOT))
    (out/'SHA256SUMS.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.suffix in ['.pdf','.zip']},indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':build()
