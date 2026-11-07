"""CPU-only reconstruction of frozen exports, editable tables and vector figures.

No runtime, model, network, warmup or hardware experiment is invoked.
Export checks do not reopen private raw archives. Source copies are authenticated
against the Git blob and SHA-256 receipts acquired at the PR #70 baseline.
"""
from pathlib import Path
import csv, hashlib, importlib.util, json, math, random, statistics
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'


def read_json(name):
    return json.loads((ROOT / name).read_text())


def rows(name):
    with (ROOT / name).open(newline='') as f:
        return list(csv.DictReader(f))


def gm(values):
    values = list(values)
    assert values and all(math.isfinite(v) and v > 0 for v in values)
    return math.exp(statistics.mean(math.log(v) for v in values))


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12), (a, b)


def authenticate_sources():
    records = read_json('provenance/READ_SOURCE_INDEX.json')['files']
    records += read_json('provenance/ADDITIONAL_SOURCE_INDEX.json')['records']
    for r in records:
        b = (ROOT / 'source_records' / r['path']).read_bytes()
        assert len(b) == r['bytes'], r['path']
        assert hashlib.sha256(b).hexdigest() == r['sha256'], r['path']
        git_sha = hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
        assert git_sha == r.get('git_blob', r.get('git_blob_sha')), r['path']
    # New copies of evidence and historical files must equal the prior version.
    for directory in ['evidence', 'historical_sources']:
        for p in (ROOT / directory).rglob('*'):
            if p.is_file():
                q = ROOT / 'source_records/paper/jsa/manuscript_v013' / p.relative_to(ROOT)
                assert p.read_bytes() == q.read_bytes(), p
    return dict(authenticated_read_source_files=len(records),
                inherited_evidence_files=len(list((ROOT/'evidence').rglob('*.*'))),
                historical_source_files=len(list((ROOT/'historical_sources').rglob('*.*'))),
                private_archives_reopened=False)


def compute():
    source = authenticate_sources()
    spec = importlib.util.spec_from_file_location('inherited_verifier', ROOT/'frozen_verifier.py')
    inherited = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inherited)
    frozen = inherited.verify()
    raw = rows('evidence/rtx66/RAW_COSTS.csv')
    tasks = list(dict.fromkeys(r['task'] for r in rows('evidence/rtx66/TASK_COST_PAIRS.csv')))
    conditions = ['scalar_reference', 'matched_target', 'target_scopes', 'all_scopes']
    med = {}
    for timer in ['generation', 'whole']:
        for t in tasks:
            for c in conditions:
                a = [float(r[timer+'_ms']) for r in raw if r['task']==t and r['condition']==c]
                assert len(a) == 4
                med[timer,t,c] = statistics.median(a)
    summaries = read_json('evidence/rtx66/COST_SUMMARY.json')['comparisons']
    # Historical interval replay is independent of the inherited PCG64 verifier.
    hist_stream = random.Random(20261005)
    hist_indices = [hist_stream.choices(range(24), k=24) for _ in range(4000)]
    for s in summaries:
        v = [med[s['timer'],t,s['baseline']]/med[s['timer'],t,s['candidate']] for t in tasks]
        close(gm(v), s['task_median_gm'])
        hs = sorted(gm(v[i] for i in draw) for draw in hist_indices)
        # These endpoints retain the old interval convention, not a new interval.
        for actual, expected in zip([hs[99],hs[3899]],s['historical_interval_replication']):
            close(actual,expected)
        for rr in s['rounds']:
            rr_map = {(r['task'],r['condition']):float(r[s['timer']+'_ms']) for r in raw
                      if int(r['repetition'])==rr['repetition']}
            close(gm(rr_map[t,s['baseline']]/rr_map[t,s['candidate']] for t in tasks),rr['gm'])
    request_regressions = [t for t in tasks if med['whole',t,'matched_target'] < med['whole',t,'target_scopes']]
    assert len(request_regressions)==7
    matched_req = next(s for s in summaries if s['timer']=='whole' and s['baseline']=='matched_target' and s['candidate']=='target_scopes')
    assert matched_req['rounds'][1]['gm'] < 1

    a1 = read_json('source_records/benchmarks/rtx_consistency_phase2/results/A1_RESULTS.json')['conditions']
    aggregate = {int(r['mask']):r for r in rows('evidence/RTX_PHASE_FACTORIAL.csv')}
    probes = ['HumanEval/15','HumanEval/18','HumanEval/25','HumanEval/31']
    assert set(aggregate)==set(range(16)) and len(a1)==16
    for c in a1:
        a=aggregate[c['mask']]
        assert c['requests']==8 and c['repeat_stable']
        assert c['reference_matches']==2*sum(c['task_matches'].values())
        assert int(a['reference_matches'])==c['reference_matches']
        assert (a['qualifies']=='True')==c['qualifies']
        assert c['qualifies']==all(c['task_matches'][p] for p in probes)
    passing=[c['mask'] for c in a1 if c['qualifies']]
    assert passing==[3,7,11,15]
    assert not any(c['qualifies'] and c['mask']!=3 and c['mask']&3==c['mask'] for c in a1)

    rtx_cross=read_json('evidence/RTX_NATURAL_CROSSES.json')
    crosses=[]
    for task,pos,expected in [(15,2,[[9147,4199],[9147,4199]]),(25,0,[[1406,1406],[1406,271]])]:
        rs=[r for r in rtx_cross if r['task']==task]
        mm=[[[r['matrix'][d][ub]['sampled_ids'][pos] for ub in ['2','1']] for d in ['N0','N1']] for r in rs]
        assert len(mm)==3 and all(x==expected for x in mm)
        crosses.append(dict(platform='RTX',task=f'HumanEval/{task}',matrix=expected,
                            rows=['N0','N1'],columns=['UB2','UB1'],repeats=3,
                            title='Current path' if task==15 else 'Interaction',position=pos))
    bcausal=read_json('evidence/b57065/CAUSAL_RECHECK.json')['cases']
    for task,expected in [('HumanEval/145',[[71465,279],[279,279]]),('HumanEval/42',[[432,1817],[1817,1817]]),('MBPP/72',[[320,320],[308,308]])]:
        rs=[r for r in bcausal if r['task']==task]
        assert len(rs)==2 and all(r['focus']['decisions']==expected for r in rs)
        identical=task=='MBPP/72'
        assert all(r['current_columns_identical']==identical for r in rs)
        crosses.append(dict(platform='B570',task=task,matrix=expected,rows=['N1','E'],
                            columns=['UB1/r3','UB1/r3'] if identical else ['N1 recipe','E recipe'],
                            repeats=2,title='State control' if identical else 'Interaction'))

    braw=rows('evidence/b57065/COSTS_RECOMPUTED.csv')
    assert len(braw)==119 and len({r['unit_id'] for r in braw})==119
    assert 'E/FORMAL/1/old_N1/MBPP/400' not in {r['unit_id'] for r in braw}
    labels=['ordinary_R','matched_target','candidate','old_N1']
    btasks=sorted({r['task'] for r in braw})
    assert len(btasks)==15
    for r in braw:
        assert r['qualified']=='True'
        assert int(r['raw_length'])==int(r['endpoint_length'])+int(r['raw_suffix'])
        assert all(float(r[m])>0 for m in ['generation_ms','whole_ms','host_ms'])
    bmed={}
    for t in btasks:
        for c in labels:
            rs=[r for r in braw if r['task']==t and r['label']==c]
            assert len(rs)==(1 if t=='MBPP/400' and c=='old_N1' else 2)
            if len(rs)==2:
                for m in ['generation_ms','whole_ms','host_ms']:
                    bmed[t,c,m]=statistics.median(float(r[m]) for r in rs)
    bsumm=read_json('evidence/b57065/COST_SUMMARY.json')
    bpairs={}
    for name,b,c in [('ordinary_R/candidate','ordinary_R','candidate'),('matched_target/candidate','matched_target','candidate'),('old_N1/candidate','old_N1','candidate'),('ordinary_R/matched_target','ordinary_R','matched_target')]:
        eligible=[t for t in btasks if (t,b,'generation_ms') in bmed and (t,c,'generation_ms') in bmed]
        s=bsumm['comparisons'][name]
        assert len(eligible)==s['tasks']==(14 if b=='old_N1' else 15)
        bpairs[name]={}
        for m in ['generation_ms','whole_ms','host_ms']:
            v={t:bmed[t,b,m]/bmed[t,c,m] for t in eligible}
            close(gm(v.values()),s['metrics'][m]['task_GM'])
            assert sum(x>1 for x in v.values())==s['metrics'][m]['task_faster']
            bpairs[name][m]=v
    qual=rows('evidence/b57065/QUALIFICATION_RECOMPUTED.csv')
    assert len(qual)==299
    formalq=[r for r in qual if r['unit_id'].startswith('E/FORMAL/')]
    assert len(formalq)==119 and {r['unit_id'] for r in formalq}=={r['unit_id'] for r in braw}
    for r in formalq:
        assert r['reference_endpoint_equal']=='True' and r['all_suffix_work_paid']=='True'
    candidate=[r for r in braw if r['label']=='candidate']
    suffix_totals={k:sum(int(r[f]) for r in candidate) for k,f in [('endpoint', 'endpoint_length'),('raw','raw_length'),('suffix','raw_suffix')]}
    assert suffix_totals==dict(endpoint=1150,raw=1176,suffix=26)
    work=rows('evidence/b57065/WORK_BREAKDOWN.csv')
    assert len(work)==30
    totals={f:sum(int(r[f]) for r in work) for f in ['drafted','accepted','target_verification_caller_tokens','draft_proposal_tokens','draft_catchup_tokens']}
    assert totals['drafted']==888 and totals['accepted']==702
    assert totals['target_verification_caller_tokens']==1332
    assert totals['draft_proposal_tokens']+totals['draft_catchup_tokens']==1362

    fixed=read_json('evidence/RTX_FIXED_UB_RESULTS.json')
    for group in [fixed]+list(fixed['cohorts'].values()):
        for c in group['costs']:
            if not c['qualified']:continue
            for m in ['generation','wall']:
                close(gm(c[m]['task_ratios'].values()),c[m]['task_median_geomean_speedup'])
    assert fixed['qualification']==dict(matched_target=True,anchor_speculation=True,wider_speculation=True,ordinary_wider=False)
    m4=read_json('evidence/M4_FORMAL_ANALYSIS.json')
    pp=m4['per_prompt'];assert len(pp)==60
    for cand,key in [('always','geometric_mean_target_over_always_spec'),('guard','geometric_mean_target_over_guard')]:
        close(gm(p['target_median_ns']/p[cand+'_median_ns'] for p in pp),m4['overall'][key])
    guard_latency=[p['guard_median_ns']/p['always_median_ns'] for p in pp]
    close(gm(guard_latency),1.0270760219826773)
    rng=random.Random(20260924)
    draws=sorted(gm(guard_latency[rng.randrange(60)] for _ in range(60)) for _ in range(10000))
    ci=np.quantile(draws,[.025,.975],method='linear')
    assert np.allclose(ci,[1.0129560055428655,1.0435592653980876],rtol=1e-10)
    oracle=gm(p['always_median_ns']/min(p['target_median_ns'],p['always_median_ns']) for p in pp)
    close(oracle,1.0006919671212657)
    assert sum(p['target_median_ns']<p['always_median_ns'] for p in pp)==2
    result=dict(status='PASS',sources=source,inherited_rtx_verifier=frozen,
                rtx_historical_intervals_checked=12,rtx_round_summaries_checked=48,
                rtx_request_regressions=request_regressions,rtx_matched_request_rounds=matched_req['rounds'],
                phase_passing_masks=passing,phase_requests=128,natural_crosses=crosses,
                b570_formal_complete=119,b570_formal_planned=120,
                b570_task_pairs={'ordinary_R/candidate':15,'matched_target/candidate':15,'old_N1/candidate':14},
                b570_suffix_totals=suffix_totals,b570_formal_work=totals,
                fixed_ub_checks='GM of saved task ratios; not a raw timing audit',
                m4_guard_latency_gm=gm(guard_latency),m4_guard_latency_ci=list(ci),
                m4_oracle_factor=oracle,m4_oracle_latency_reduction_percent=(1-1/oracle)*100,
                new_model_requests=0,new_forwards=0,new_warmups=0,
                scope='Author-side CPU export/source validation; private raw archive audits inherited, not repeated')
    return result,dict(tasks=tasks,med=med,summaries=summaries,a1=a1,probes=probes,crosses=crosses,
                       bmed=bmed,bpairs=bpairs,bsumm=bsumm,btasks=btasks,fixed=fixed,m4=m4)


def table_file(name,caption,label,columns,header,body,long=False,tail='',column_sep=None):
    if long:
        s='\\begingroup\\small\n\\begin{longtable}{'+columns+'}\n\\caption{'+caption+'}\\label{'+label+'}\\\\\n\\toprule\n'+header+'\\\\\\midrule\n\\endfirsthead\n\\toprule\n'+header+'\\\\\\midrule\n\\endhead\n\\midrule\\multicolumn{'+str(len(header.split('&')))+'}{r}{Continued on next page}\\\\\n\\endfoot\n\\bottomrule\n\\endlastfoot\n'
        s+='\n'.join(' & '.join(map(str,r))+r'\\' for r in body)+'\n\\end{longtable}\n'+tail+'\n\\endgroup\n'
    else:
        s='\\begin{table}[ht]\\centering\\small\n\\caption{'+caption+'}\\label{'+label+'}\n\\begin{tabular}{'+columns+'}\\toprule\n'+header+'\\\\\\midrule\n'
        if column_sep is not None:
            s=s.replace('\\begin{tabular}', '\\setlength{\\tabcolsep}{'+str(column_sep)+'pt}\n\\begin{tabular}', 1)
        s+='\n'.join(' & '.join(map(str,r))+r'\\' for r in body)+'\n\\bottomrule\\end{tabular}\n'+tail+'\n\\end{table}\n'
    (ROOT/'tables'/name).write_text('% Generated by scripts/reconstruct.py from frozen exports.\n'+s)


def make_tables(d,qa):
    labels={'scalar_reference':'$R$','matched_target':'$M$','target_scopes':'$C_3$','all_scopes':'$C_{15}$'}
    get=lambda b,c,t:next(s for s in d['summaries'] if s['baseline']==b and s['candidate']==c and s['timer']==t)
    body=[]
    for b,c in [('scalar_reference','target_scopes'),('matched_target','target_scopes'),('scalar_reference','matched_target')]:
        for t in ['generation','whole']:
            s=get(b,c,t);lo,hi=s['descriptive_task_bootstrap_95_linear']
            body.append([labels[b]+'/'+labels[c], 'Gen.' if t=='generation' else 'Request',
                         f"{s['task_median_gm']:.6f}", f'[{lo:.3f},{hi:.3f}]'])
    table_file('rtx_cost.tex','RTX frozen expansion paid ratios: 24 task medians, four repeats. Gen. denotes generation; Request denotes resident request. Intervals describe task resampling. $C_3$ is mask 3 speculation.','tab:rtx_cost','@{}llrr@{}','Ratio & Timer & Speed & 95\\% interval',body,column_sep=4)
    allbody=[]
    for s in d['summaries']:
        lo,hi=s['descriptive_task_bootstrap_95_linear']
        allbody.append([labels[s['baseline']]+'/'+labels[s['candidate']],'Gen.' if s['timer']=='generation' else 'Request',f"{s['task_median_gm']:.6f}",f'[{lo:.6f},{hi:.6f}]',f"{s['faster_tasks']}/24"])
    table_file('rtx_all_comparisons.tex','All RTX expansion comparisons, baseline/candidate. Each uses 24 task medians; $C_3$/$C_{15}$ are mask 3/15 speculation.','tab:rtx_all','@{}llrrr@{}','Ratio & Timer & Speed & Descriptive interval & Faster',allbody,long=True)
    for t,label in [('generation','generation'),('whole','request')]:
        body=[]
        for task in d['tasks']:
            r,m,c=[d['med'][t,task,x] for x in ['scalar_reference','matched_target','target_scopes']]
            body.append([task.split('/')[-1],f'{r:.3f}',f'{m:.3f}',f'{c:.3f}',f'{r/c:.6f}',f'{m/c:.6f}'])
        tail=''
        if t=='whole':
            tail='Matched-request regressions: '+', '.join(qa['rtx_request_regressions'])+'. Round GMs: '+', '.join(f"{r['gm']:.6f}" for r in qa['rtx_matched_request_rounds'])+'.'
        table_file('rtx_task_'+label+'.tex','RTX '+label+' absolute task medians (ms) and ratios. MBPP task IDs follow the saved order.','tab:rtx_task_'+label,'@{}rrrrrr@{}','Task & $R$ ms & $M$ ms & $C_3$ ms & $R/C_3$ & $M/C_3$',body,long=True,tail=tail)
    bbody=[]
    bn={'ordinary_R/candidate':'$R/C$','matched_target/candidate':'$M/C$','old_N1/candidate':'Old N1/$C$','ordinary_R/matched_target':'$R/M$'}
    for name,s in d['bsumm']['comparisons'].items():
        bbody.append([bn[name],str(s['tasks'])]+[f"{s['metrics'][m]['task_GM']:.6f}" for m in ['generation_ms','whole_ms','host_ms']])
    table_file('b570_cost.tex','B570 paid baseline/candidate task-median ratios. $n$ counts complete two-round task pairs: 15 for $R/C$, $M/C$ and $R/M$, and 14 for old N1/$C$. Gen., Request and Host denote generation, whole request and host-observed time. The missing old-N1 task is not imputed; raw suffix work stays charged.','tab:b570_cost','@{}lrrrr@{}','Ratio & $n$ & Gen. & Request & Host',bbody,column_sep=3)
    body=[]
    for task in d['btasks']:
        row=[task.split('/')[-1]]
        for name in ['ordinary_R/candidate','matched_target/candidate','old_N1/candidate']:
            for m in ['generation_ms','whole_ms']:
                v=d['bpairs'][name][m].get(task);row.append('--' if v is None else f'{v:.6f}')
        body.append(row)
    table_file('b570_task_cost.tex','All B570 two-round task-median speed ratios. G/W denote generation/whole request; old N1 has no complete pair for MBPP/400.','tab:b570_task_cost','@{}rrrrrrr@{}','MBPP & $R/C$ G & $R/C$ W & $M/C$ G & $M/C$ W & N1/$C$ G & N1/$C$ W',body,long=True)
    body=[]
    fn={'wider_speculation':'Wide','anchor_speculation':'Anchor','matched_target':'Matched'}
    for groupname,group in [('All (28)',d['fixed']),('MBPP (24)',d['fixed']['cohorts']['MBPP']),('HE (4)',d['fixed']['cohorts']['HumanEval'])]:
        for c in group['costs']:
            if c['qualified']:
                body.append([groupname,fn[c['denominator']]+'/'+fn[c['numerator']],f"{c['generation']['task_median_geomean_speedup']:.6f}",f"{c['wall']['task_median_geomean_speedup']:.6f}"])
    table_file('fixed_ub.tex','Fixed-UB4 width costs: baseline/candidate. Anchor is $k=3$, wide is $k=7$, and matched has no draft. Partitions are descriptive.','tab:fixed_ub','@{}llrr@{}','Panel & Ratio & Generation & Request',body)
    body=[]
    for name,data in [('Overall',d['m4']['overall']),('HumanEval',d['m4']['strata']['HumanEval']),('Spec-Bench',d['m4']['strata']['Spec-Bench'])]:
        body.append([name,str(data['prompt_count']),f"{data['geometric_mean_target_over_always_spec']:.6f}",f"{data['geometric_mean_target_over_guard']:.6f}"])
    table_file('m4_strata.tex','M4 formal post-prefill baseline/candidate speeds from three-repeat condition medians. Family strata are descriptive.','tab:m4_strata','@{}lrrr@{}','Panel & Tasks & Target/Always & Target/Guard',body)


def make_figures(d):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import FancyBboxPatch, Rectangle
    matplotlib.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,'pdf.fonttype':42,
                                'ps.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'HeteroSpec-v0141','axes.titlesize':11,
                                'axes.labelsize':10,'savefig.facecolor':'white'})
    teal='#16756e';orange='#b86232';ink='#203341';grey='#748391'
    figure_inputs={}
    def save(fig,name,data):
        for ext in ['pdf','svg']:
            kw={'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {'metadata':{'Date':None}}
            # Exact 7.2-inch canvases match the normal elsarticle 5p text area.
            # Preserve physical text sizes; do not trim and then enlarge assets.
            fig.savefig(ROOT/'figures'/(name+'.'+ext),**kw)
        plt.close(fig);figure_inputs[name]=data

    fig,ax=plt.subplots(figsize=(7.2,3.0));ax.set(xlim=(0,12),ylim=(0,5.2));ax.axis('off')
    fig.subplots_adjust(left=.02,right=.98,bottom=.025,top=.96)
    def box(x,y,w,h,text,color='#e7eef2'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',linewidth=1,edgecolor=grey,facecolor=color))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10,color=ink)
    def arrow(xy,to):
        ax.annotate('',xy=to,xytext=xy,arrowprops={'arrowstyle':'->','color':ink,'lw':1.1})
    box(.15,3.6,1.85,.8,'Target prefill\nbit 1');box(.15,2.35,1.85,.8,'Draft prefill\nbit 4')
    box(2.6,2.7,2.6,1.25,'Retained state\nKV, pending event,\npositions')
    box(5.75,2.7,1.75,1.25,'Draft proposals\nbit 8:\ncontinuation','#e0efec')
    box(8.05,2.7,1.75,1.25,'Target verify\nbit 2:\ncontinuation','#e0efec')
    box(10.35,2.7,1.5,1.25,'Commit /\nrollback\nEOG or cap')
    arrow((2,4.0),(2.6,3.6));arrow((2,2.75),(2.6,3.05))
    arrow((5.2,3.325),(5.75,3.325));arrow((7.5,3.325),(8.05,3.325));arrow((9.8,3.325),(10.35,3.325))
    ax.plot([11.1,11.1,3.9],[2.7,1.8,1.8],color=grey,lw=1.1)
    arrow((3.9,1.8),(3.9,2.7));ax.text(7.45,1.9,'Reconcile retained state for the next iteration',ha='center',va='bottom',fontsize=9.5)
    box(.15,.15,11.7,1.05,'RTX constrained attention: query view (d, q, h, 1) → (d, 1, h, q)\nK/V broadcast; mask columns match query batches\nProjection, FFN and output remain batched','#f4f7f9')
    ax.text(6,4.9,'Phase bits control graph selection; R and M omit drafting',ha='center',fontsize=10.5,fontweight='bold')
    save(fig,'figure_1_architecture',dict(type='Source-bound conceptual diagram',sources=['query_batch_patch.py','scope_patch.py','native_scope_delta.patch','B570 phase.h/target.cpp/native.cpp'],ai_assisted_plotting_code=True,no_generated_data=True))

    fig,axes=plt.subplots(2,3,figsize=(7.2,3.4))
    fig.subplots_adjust(left=.065,right=.978,bottom=.145,top=.835,wspace=.34,hspace=.82)
    for ax,c in zip(axes.flat,d['crosses']):
        m=np.array(c['matrix']);ids=list(dict.fromkeys(m.ravel()));cats=np.array([[ids.index(v) for v in r] for r in m])
        ax.imshow(cats,cmap=ListedColormap(['#e0eeeb','#edcbb6']),vmin=0,vmax=1,aspect='auto')
        for i in range(2):
            for j in range(2):ax.text(j,i,str(m[i,j]),ha='center',va='center',fontsize=11.5,color=ink)
        column_labels=[x.replace(' recipe','\nrecipe') for x in c['columns']]
        ax.set_xticks([0,1],column_labels,fontsize=9.5);ax.set_yticks([0,1],c['rows'],fontsize=9.5)
        ax.set_title(c['platform']+' '+c['task'].replace('HumanEval/','HE/').replace('MBPP/','MBPP/')+'\n'+c['title'],fontsize=10.5,pad=6)
        ax.tick_params(length=0)
        for spine in ax.spines.values():spine.set_visible(False)
    axes[1,2].axis('off');axes[1,2].text(0,.97,'Rows: natural donor\nColumns: current recipe\n\nEqual colors mean equal IDs\nwithin each task only.\n\nOwn-path shams pass.',fontsize=9.5,va='top',transform=axes[1,2].transAxes)
    save(fig,'figure_2_natural_crosses',d['crosses'])

    fig,ax=plt.subplots(figsize=(7.2,3.6))
    maskdata=[]
    for c in d['a1']:
        r=c['mask'];bits=[bool(r&bit) for bit in [1,2,4,8]];passes=[c['task_matches'][p] for p in d['probes']]
        for j,v in enumerate(bits+passes):
            color=('#526a7b' if v else '#eef1f3') if j<4 else (teal if v else '#e2ba9e')
            ax.add_patch(Rectangle((j-.44,r-.45),.88,.9,facecolor=color,edgecolor='white'))
            ax.text(j,r,('1' if v else '0') if j<4 else ('✓' if v else '×'),ha='center',va='center',fontsize=10,color='white' if v else ink)
        if c['qualifies']:
            ax.text(8,r,'PASS',ha='left',va='center',fontsize=9.5,color=teal,fontweight='bold')
        maskdata.append(dict(mask=r,bits=bits,probe_passes=passes,qualifies=c['qualifies']))
    ax.axvline(3.5,color=grey,lw=1)
    ax.set_xticks(range(8),['Target\nprefill','Target\ncont.','Draft\nprefill','Draft\ncont.','HE/15','HE/18','HE/25','HE/31'],fontsize=9.5)
    ax.xaxis.tick_top();ax.set_yticks(range(16),[f'{m:02d}' for m in range(16)],fontsize=10)
    ax.set_ylabel('Phase mask');ax.set(xlim=(-.6,8.9),ylim=(15.5,-.5))
    ax.tick_params(length=0)
    fig.text(.29,.966,'Enabled constraints',ha='center',va='top',fontsize=10.5)
    fig.text(.70,.966,'Full-response qualification',ha='center',va='top',fontsize=10.5)
    for spine in ax.spines.values():spine.set_visible(False)
    fig.subplots_adjust(top=.815,left=.072,bottom=.055,right=.985)
    save(fig,'figure_3_phase_matrix',maskdata)

    fig,axes=plt.subplots(1,2,figsize=(7.2,2.6),sharey=True)
    fig.subplots_adjust(left=.105,right=.98,bottom=.235,top=.815,wspace=.26)
    comparisons=[('scalar_reference','target_scopes','R / C'),('matched_target','target_scopes','M / C'),('scalar_reference','matched_target','R / M')]
    costdata=[]
    for ax,t,title,col in zip(axes,['generation','whole'],['Generation','Resident request'],[teal,orange]):
        for y,(b,c,label) in enumerate(comparisons):
            s=next(s for s in d['summaries'] if s['timer']==t and s['baseline']==b and s['candidate']==c)
            v=s['task_median_gm'];lo,hi=s['descriptive_task_bootstrap_95_linear']
            ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',capsize=3,color=col,ms=6)
            ax.text(v,y-.24,f'{v:.3f}',ha='center',fontsize=10,color=ink)
            costdata.append(dict(timer=t,baseline=b,candidate=c,ratio=v,interval=[lo,hi]))
        ax.axvline(1,color=grey,lw=1);ax.set_title(title);ax.set_xlabel('Baseline / candidate time')
        ax.set_ylim(2.5,-.65);ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.15)
        ax.set_xlim((.975,1.255) if t=='generation' else (.94,1.91))
        ax.set_yticks(range(3),[x[2] for x in comparisons])
    save(fig,'figure_4_paid_cost',costdata)

    task_values={t:{task:d['med'][t,task,'matched_target']/d['med'][t,task,'target_scopes'] for task in d['tasks']} for t in ['generation','whole']}
    order=sorted(d['tasks'],key=lambda t:(task_values['whole'][t],t))
    fig,axes=plt.subplots(1,2,figsize=(7.2,4.5),sharey=True)
    fig.subplots_adjust(left=.105,right=.98,bottom=.15,top=.91,wspace=.22)
    for ax,t,title in zip(axes,['generation','whole'],['Generation: 22/24 faster','Resident request: 17/24 faster']):
        v=[task_values[t][task] for task in order];mean=gm(v)
        ax.axvspan(0,1,facecolor='#f8efe9',zorder=0);ax.axvline(1,color=grey,lw=1)
        ax.axvline(mean,color=teal,lw=1,ls='--')
        ax.scatter(v,range(24),c=[teal if x>1 else orange for x in v],s=26,zorder=3)
        ax.set_yticks(range(24),[task.replace('MBPP/','') for task in order],fontsize=9.5)
        ax.set_ylim(23.6,-.6);ax.set_xlim(min(.85,min(v)*.96),max(1.3,max(v)*1.05))
        ax.set_title(title+'; GM '+f'{mean:.3f}',fontsize=10.5,pad=7);ax.set_xlabel('Matched / candidate time')
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.15)
    axes[0].set_ylabel('MBPP task (same request-sorted order)')
    save(fig,'figure_5_task_variation',dict(order=order,ratios=task_values))
    return figure_inputs


def main():
    OUT.mkdir(exist_ok=True);(ROOT/'tables').mkdir(exist_ok=True);(ROOT/'figures').mkdir(exist_ok=True)
    qa,data=compute();make_tables(data,qa);fi=make_figures(data)
    (OUT/'NUMERICAL_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
    (OUT/'FIGURE_INPUTS.json').write_text(json.dumps(fi,indent=2)+'\n')
    print(json.dumps({k:qa[k] for k in ['status','sources','phase_passing_masks','rtx_request_regressions','b570_formal_complete','b570_task_pairs','new_model_requests']},indent=2))


if __name__=='__main__':
    main()
