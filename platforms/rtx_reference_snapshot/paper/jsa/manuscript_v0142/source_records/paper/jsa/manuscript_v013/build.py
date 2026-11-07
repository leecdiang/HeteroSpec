"""Build JSA structural draft from frozen evidence; no inference or figure regeneration."""
from pathlib import Path
import json,csv,hashlib,statistics,math,subprocess,re,shutil,zipfile
import frozen_verifier
ROOT=Path(__file__).resolve().parent

def gm(values):
    values=list(values)
    assert values and all(math.isfinite(v) and v>0 for v in values)
    return math.exp(statistics.mean(math.log(v) for v in values))

def run(*args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
    if p.returncode:
        print((p.stdout+p.stderr)[-7500:])
        raise RuntimeError("Command failed: "+args[0])
    return p.stdout+p.stderr

def verify_extended():
    m=json.loads((ROOT/'RECONSTRUCTION_BINDINGS.json').read_text())
    for source in m['historical_sources']:
        b=(ROOT/source['local_path']).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==source['git_blob'],source['repo_path']
    late=frozen_verifier.verify()
    factorial=list(csv.DictReader((ROOT/'evidence/RTX_PHASE_FACTORIAL.csv').open()))
    masks=[int(x['mask']) for x in factorial if x['qualifies']=='True' and x['spec']=='True']
    assert sorted(masks)==[3,7,11,15]
    minima=[a for a in masks if not any(b!=a and (b&a)==b for b in masks)]
    assert minima==[3]
    c4=json.loads((ROOT/'evidence/RTX_FIXED_UB_RESULTS.json').read_text())
    c4checks=[];rows=[]
    for comp in c4['costs']:
        for timer in ['generation','wall']:
            v=comp[timer];calc=gm(v['task_ratios'].values())
            assert len(v['task_ratios'])==28
            assert math.isclose(calc,v['task_median_geomean_speedup'],rel_tol=1e-12)
            c4checks.append(dict(pair=comp['denominator']+'/'+comp['numerator'],timer=timer,n=28,gm=calc,qualified=comp['qualified']))
    for group,obj in c4['cohorts'].items():
        for comp in obj['costs']:
            vals=[]
            for timer in ['generation','wall']:
                v=comp[timer];calc=gm(v['task_ratios'].values())
                assert len(v['task_ratios'])==(24 if group=='MBPP' else 4)
                assert math.isclose(calc,v['task_median_geomean_speedup'],rel_tol=1e-12)
                vals.append(calc)
            rows.append(('RTX width',group,len(v['task_ratios']),'Matched / wide' if comp['denominator']=='matched_target' else 'Anchor / wide',*vals))
    m4=json.loads((ROOT/'evidence/M4_FORMAL_ANALYSIS.json').read_text())
    assert len(m4['per_prompt'])==60
    overall=gm(x['target_median_ns']/x['always_median_ns'] for x in m4['per_prompt'])
    assert math.isclose(overall,m4['overall']['geometric_mean_target_over_always_spec'],rel_tol=1e-12)
    for group in ['HumanEval','Spec-Bench']:
        entries=[x for x in m4['per_prompt'] if x['workload_family']==group]
        assert len(entries)==30
        for field,summary,label in [
            ('always_median_ns','geometric_mean_target_over_always_spec','Target / fixed'),
            ('guard_median_ns','geometric_mean_target_over_guard','Target / guard')]:
            value=gm(x['target_median_ns']/x[field] for x in entries)
            assert math.isclose(value,m4['strata'][group][summary],rel_tol=1e-12)
            rows.append(('M4',group,30,label,value,None))
    oracle=gm(x['always_median_ns']/min(x['target_median_ns'],x['always_median_ns']) for x in m4['per_prompt'])
    assert math.isclose(oracle,1.0006919671212657,rel_tol=1e-12)
    b=list(csv.DictReader((ROOT/'evidence/b57065/COSTS_RECOMPUTED.csv').open()))
    b=[x for x in b if x['unit_id'].startswith('E/FORMAL/')]
    assert len(b)==119 and len({x['unit_id']for x in b})==119
    labels={x['label']for x in b}
    assert {'ordinary_R','matched_target','candidate','old_N1'}==labels,labels
    bs=json.loads((ROOT/'evidence/b57065/COST_SUMMARY.json').read_text())
    bc=[]
    for base in ['ordinary_R','matched_target','old_N1']:
        tasks=sorted(set(x['task']for x in b))
        for timer in ['generation_ms','whole_ms','host_ms']:
            ratios=[]
            for task in tasks:
                x=[float(v[timer])for v in b if v['task']==task and v['label']==base]
                y=[float(v[timer])for v in b if v['task']==task and v['label']=='candidate']
                if len(x)==len(y)==2:ratios.append(statistics.median(x)/statistics.median(y))
            expected=bs['comparisons'][base+'/candidate']['metrics'][timer]
            value=gm(ratios)
            assert len(ratios)==(14 if base=='old_N1' else 15)
            assert math.isclose(value,expected['task_GM'],rel_tol=1e-12)
            bc.append(dict(base=base,timer=timer,tasks=len(ratios),gm=value))
    table=[r'\begin{table}[t]\centering\footnotesize\setlength{\tabcolsep}{4pt}',
      r'\caption{Saved workload partitions. Speed is named baseline/candidate. RTX uses generation and resident-request timers; M4 uses its post-prefill timer. Rows are not cross-platform comparisons or independent validation panels.}',
      r'\label{tab:strata}',
      r'\begin{tabular}{llrlcc}\toprule',
      r'Study & Partition & Tasks & Comparison & Gen./post-prefill & Request\\\midrule']
    for study,group,n,label,a,bv in rows:
        table.append(f'{study} & {group} & {n} & {label} & {a:.3f} & '+('--'if bv is None else f'{bv:.3f}')+r'\\')
    table.extend([r'\bottomrule\end{tabular}\end{table}'])
    (ROOT/'tables').mkdir(exist_ok=True)
    (ROOT/'tables/workload_strata.tex').write_text('\n'.join(table)+'\n')
    data=dict(late_RTX=late,historical_git_blobs=len(m['historical_sources']),fixed_UB_comparisons=c4checks,workload_rows=rows,M4_oracle_factor=oracle,B570_formal_rows=119,B570_complete_comparisons=bc,passing_masks=masks,inclusion_minima=minima,raw_archives_reopened=False,new_inference=0,new_warmup=0,figure_regeneration=False)
    return data

def build():
    out=ROOT/'output';out.mkdir(exist_ok=True)
    figures_before={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'figures').glob('*.pdf')}
    checks=verify_extended();docs={}
    main=(ROOT/'main.tex').read_text()
    abstract=main.split(r'\begin{abstract}',1)[1].split(r'\end{abstract}',1)[0]
    words=len(abstract.split());assert words<=250,words
    for stem,name in [('main','jsa-manuscript-v0.13.0.pdf'),('appendix','jsa-supplement-v0.13.0.pdf')]:
        console=run('latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-outdir=build',stem+'.tex')
        (out/(stem+'-console.log')).write_text(console)
        log=(ROOT/'build'/f'{stem}.log').read_text(errors='replace')
        issues=re.findall(r'Overfull.*|.*undefined.*|.*multiply defined.*',log,re.I)
        assert not issues,issues
        shutil.copyfile(ROOT/'build'/f'{stem}.pdf',out/name)
        run('pdftotext','-layout',str(out/name),str(out/(stem+'.txt')))
        text=(out/(stem+'.txt')).read_text()
        assert all(s not in text for s in ['/workspace/','anon.email@domain.com','MLSys 2027'])
        assert 'Type 3' not in run('pdffonts',str(out/name))
        pages=int(re.search(r'Pages:\s+(\d+)',run('pdfinfo',str(out/name))).group(1))
        docs[stem]=dict(pages=pages,overfull=0,undefined=0,type3_fonts=0,text_sha256=hashlib.sha256(text.encode()).hexdigest(),text_words=len(text.split()))
    figures_after={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'figures').glob('*.pdf')}
    assert figures_before==figures_after
    evidence={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'evidence').rglob('*')if p.is_file()}
    result=dict(version='v0.13.0',base_commit='f3fd2aecc6288c661033ee83d5216db6481dac3f',checks=checks,documents=docs,abstract_words=words,evidence_file_count=len(evidence),retained_figure_hashes=figures_after,scope='JSA structural draft; frozen experiments; author self-review; not submitted')
    (out/'BUILD_QA.json').write_text(json.dumps(result,indent=2)+'\n')
    with zipfile.ZipFile(out/'overleaf-jsa-v0.13.0.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            if p.is_file() and not any(x in p.relative_to(ROOT).parts for x in ['output','build','__pycache__']):
                z.write(p,p.relative_to(ROOT))
    (out/'SHA256SUMS.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in out.iterdir()if p.suffix in ['.pdf','.zip']},indent=2)+'\n')
    print(json.dumps(dict(version='v0.13.0',documents=docs,abstract_words=words,late_evidence_files=len(evidence),historical_blobs=checks['historical_git_blobs'],new_inference=0),indent=2))

if __name__=='__main__':build()

