#!/usr/bin/env python3
"""Post-study CPU analysis; input preparation reads sealed archives, never runners.

compute(inputs) is also the stdlib anonymous recalculation entry. No old output
is written. The plan, source mappings, primary streams and missing rules are
explicitly separate from new secondary sensitivity statistics.
"""
import argparse, collections, csv, hashlib, json, math, random, re, statistics, tarfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
E = ROOT / 'paper/mlsys2027/evidence'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def quantile(values, q):
    a = sorted(values); x = (len(a)-1)*q; lo = int(x); hi = math.ceil(x)
    return a[lo] + (a[hi]-a[lo])*(x-lo)
def describe(a):
    assert a and all(math.isfinite(x) for x in a)
    return dict(n=len(a), minimum=min(a), q25=quantile(a,.25), median=quantile(a,.5), q75=quantile(a,.75), q95=quantile(a,.95), maximum=max(a))
def gm(a):
    assert a and all(x > 0 and math.isfinite(x) for x in a)
    return math.exp(math.fsum(math.log(x) for x in a)/len(a))
def endpoint(ids, eog):
    assert len(ids) == len(eog)
    n = min(128, next((i+1 for i,x in enumerate(eog) if x),len(ids)))
    assert n == 128 or (n and eog[n-1])
    return ids[:n], 'EOG' if eog[n-1] else 'cap'
def first_diff(a,b):
    return next((i for i in range(max(len(a),len(b))) if i>=len(a) or i>=len(b) or a[i]!=b[i]),None)
def prepare(work):
    sources = {}
    def input_json(p):
        sources[str(p.relative_to(ROOT))] = {'sha256':sha(p),'bytes':p.stat().st_size}
        return read(p)
    def forkrow(p):
        c = input_json(p); r = input_json(p.parent/'record.json'); cp = c['checkpoint'] or {}
        a,ae = endpoint(c['primary_ids'],c['primary_eog'])
        b,be = endpoint(c['alternate_ids'],c['alternate_eog']) if c['alternate_ids'] else ([],None)
        return {'task_id':r['task_id'],'repetition':r['repetition'],'mode':c['mode'],
                'checkpoint_output_index':cp.get('output_index'), 'primary_ids':a,'alternate_ids':b,
                'primary_endpoint':ae,'alternate_endpoint':be,
                'primary_scores':c['primary_scores'],'alternate_scores':c['alternate_scores'],
                'state':{k:cp[k] for k in ('state_bytes','consumed_bytes','serialized_kv_equal','source_unchanged','sampler_seed','clone_seed','sampler_chain','clone_chain') if k in cp}}
    base = work/'b570-fork/artifacts/b570_partition_intervention_v1/raw'
    forks = [forkrow(p) for p in sorted((base/'reserved').glob('*/capture.json'))]
    controls = [forkrow(p) for p in sorted((base/'r0').glob('*/capture.json'))]
    m4dir = ROOT/'artifacts/m4_runtime/runtime-profitability-control-20260925'
    descriptor = input_json(m4dir/'archive_descriptor.json'); archive = m4dir/descriptor['archive']
    assert sha(archive)==descriptor['sha256']; sources[str(archive.relative_to(ROOT))]={'sha256':sha(archive),'bytes':archive.stat().st_size}
    member = 'm4-runtime-evidence/attempts/formal/observations.jsonl'
    with tarfile.open(archive) as t: raw = t.extractfile(member).read()
    sources[member]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'container_sha256':sha(archive)}
    obs = [json.loads(x) for x in raw.splitlines()]
    m4 = [{k:x[k] for k in ('task_id','workload_family','repetition','condition')} | {'end_to_end_ns':x['result']['end_to_end_ns'],'fallback_triggered':x['result']['fallback_triggered'],'fallback_round':x['result']['fallback_round']} for x in obs]
    medians = input_json(ROOT/'benchmarks/m4_runtime/FORMAL_ANALYSIS.json')['per_prompt']
    csvpath = ROOT/'analysis/358h_phase3_prompt_summary.csv'
    sources[str(csvpath.relative_to(ROOT))]={'sha256':sha(csvpath),'bytes':csvpath.stat().st_size}
    hrows = list(csv.DictReader(csvpath.open()))
    hsummary = input_json(ROOT/'analysis/358h_phase3_summary.json')
    h = {'rows':[{k:r[k] for k in ('task_id','repetition','condition','baseline_end_to_end_ms','end_to_end_ms','draft_replay_proposal_ms','verification_ms','orchestration_residual_ms','rounds','realized_c')} for r in hrows],
         'output_tokens_per_path':{k:v['committed_output_tokens'] for k,v in hsummary['acceptance'].items()},
         'original_decomposition':hsummary['decomposition']}
    records = input_json(work/'rtx-latency/formal/records.json')['runs']
    latency = [{k:r[k] for k in ('task_id','repetition','condition')} | {'milliseconds':r['timer']['milliseconds']} for r in records]
    logcounts=[]
    for r in records:
        p=work/'rtx-latency/formal/runs'/r['run_id']/'native.log'
        raw=p.read_bytes();sources[str(p.relative_to(ROOT))]={'sha256':sha(p),'bytes':len(raw)}
        events=re.findall(rb'process_toke: id\s+0 \| task \d+ \| n_gen = (\d+), n_remaining = (-?\d+), next token:\s+(\d+)',raw)
        assert [int(x[2]) for x in events]==r['generated_ids']
        logcounts.append({k:r[k] for k in ('task_id','repetition','condition')} | {'native_log_bytes':len(raw),'native_log_lines':len(raw.splitlines()),'committed_ID_events':len(events)})
    probe = input_json(ROOT/'benchmarks/rtx_transfer_latency_v1/R0_REVIEW.json')['hook_probe']
    original = input_json(ROOT/'benchmarks/rtx_transfer_latency_v1/latency/REPORT.json')
    inputs = {'post_study':True,'B570':forks,'B570_R0':controls,'M4':m4,'M4_original_medians':medians,'358H':h,'RTX':latency,'RTX_log_counts':logcounts,'RTX_hook_probe':probe,'RTX_original':{k:original[k] for k in ('speedup','bootstrap_95_ci','per_prompt')}}
    return inputs,sources
def compute(inputs):
    assert inputs['post_study'] is True
    forks = inputs['B570']; assert len(forks)==72 and len({r['task_id'] for r in forks})==24
    score_rows=[]; changed=0; cases=[]
    for r in forks:
        a,b = r['primary_scores'],r['alternate_scores']; assert len(a)==len(b)==3
        numeric_change=False
        assert all(r['state'][k] for k in ('serialized_kv_equal','source_unchanged'))
        assert r['state']['state_bytes']==r['state']['consumed_bytes']
        for j,(p,z) in enumerate(zip(a,b)):
            assert p['raw_top1_id']==z['raw_top1_id'] and p['proposal_id']==z['proposal_id']
            row={'task_id':r['task_id'],'repetition':r['repetition'],'row':j}
            for side,v in [('primary',p),('alternate',z)]:
                assert v['top1_score']>=v['top2_score']
                assert abs(v['margin']-(v['top1_score']-v['top2_score']))<1e-5
                row[side+'_margin']=v['top1_score']-v['top2_score']
                row[side+'_top1_id']=v['raw_top1_id']; row[side+'_top2_id']=v['raw_top2_id']
            for field in ('top1_score','top2_score','proposal_score'):
                assert (p[field] is None)==(z[field] is None)
                row['primary_'+field]=p[field];row['alternate_'+field]=z[field]
                delta=None if p[field] is None else z[field]-p[field]
                row[field+'_delta']=delta
                numeric_change |= delta is not None and delta!=0
            row['margin_delta']=row['alternate_margin']-row['primary_margin'];score_rows.append(row)
        changed+=numeric_change
        d=first_diff(r['primary_ids'],r['alternate_ids'])
        if d is not None:
            assert d>r['checkpoint_output_index']
            cases.append({k:r[k] for k in ('task_id','repetition','checkpoint_output_index','primary_endpoint','alternate_endpoint')} | {'first_divergence':d,'distance':d-r['checkpoint_output_index'],'primary_length':len(r['primary_ids']),'alternate_length':len(r['alternate_ids'])})
    assert changed==72 and len(cases)==18 and len({r['task_id'] for r in cases})==6
    distributions={}
    for field in ('top1_score','top2_score','proposal_score','margin'):
        a=[r[field+'_delta'] for r in score_rows if r[field+'_delta'] is not None]
        distributions[field]={'signed_alternate_minus_primary':describe(a),'absolute':describe([abs(x) for x in a])}
    controls=[r for r in inputs['B570_R0'] if r['mode']=='control']; assert len(controls)==6
    for r in controls: assert r['primary_ids']==r['alternate_ids'] and r['primary_scores']==r['alternate_scores']
    stable={t:len({tuple(r[k] for k in ('checkpoint_output_index','first_divergence','distance','primary_endpoint','alternate_endpoint','primary_length','alternate_length')) for r in cases if r['task_id']==t})==1 for t in sorted({r['task_id'] for r in cases})}
    b570={'numeric_changed_runs':changed,'score_rows':216,'score_units':'unnormalized raw float logits before sampler transformations; top-two over full vocabulary; proposal score for fixed proposal, None on bonus row','distributions':distributions,'primary_margin':describe([r['primary_margin'] for r in score_rows]),'alternate_margin':describe([r['alternate_margin'] for r in score_rows]),'top2_ID_changed_rows':sum(r['primary_top2_id']!=r['alternate_top2_id'] for r in score_rows),'later_cases':cases,'later_repeat_stable':stable,'R0_same_partition_controls':len(controls),'endpoint_distribution':{s:dict(collections.Counter(r[s+'_endpoint'] for r in forks)) for s in ('primary','alternate')},'cohort_order':sorted({r['task_id'] for r in forks},key=lambda t:int(t.split('/')[-1]))}
    obs=inputs['M4']; assert len(obs)==540
    canonical=inputs['M4_original_medians']; assert len(canonical)==60
    rows=[]
    for p in canonical:
        key=(p['workload_family'],p['task_id']);d={}
        for condition,field in [('TARGET_ONLY','target_median_ns'),('ALWAYS_SPEC_K2','always_median_ns'),('GUARD_K2','guard_median_ns')]:
            matches=[r for r in obs if (r['workload_family'],r['task_id'])==key and r['condition']==condition]
            assert len(matches)==3 and {r['repetition'] for r in matches}=={0,1,2}
            d[field]=statistics.median(r['end_to_end_ns'] for r in matches);assert d[field]==p[field]
        d['oracle_median_ns']=min(d['target_median_ns'],d['always_median_ns']);assert d['oracle_median_ns']==p['oracle_median_ns']
        guard=[r for r in obs if (r['workload_family'],r['task_id'])==key and r['condition']=='GUARD_K2']
        rows.append({'family':key[0],'task_id':key[1],**d,'guard_over_always':d['guard_median_ns']/d['always_median_ns'],'always_over_oracle':d['always_median_ns']/d['oracle_median_ns'],'always_over_target':d['always_median_ns']/d['target_median_ns'],'guard_over_target':d['guard_median_ns']/d['target_median_ns'],'fallback_runs':sum(x['fallback_triggered'] for x in guard),'fallback_rounds':[x['fallback_round'] for x in guard]})
    families=sorted({p['family'] for p in rows}); assert len(families)==2
    groups=[[p for p in rows if p['family']==f] for f in families];assert [len(x) for x in groups]==[30,30]
    rng=random.Random(2026100101);ga=[];ao=[]
    for _ in range(10000):
        sample=[g[rng.randrange(30)] for g in groups for _ in range(30)]
        ga.append(gm([r['guard_over_always'] for r in sample]));ao.append(gm([r['always_over_oracle'] for r in sample]))
    target_faster=[r for r in rows if r['target_median_ns']<r['always_median_ns']]
    m4={'prompt_rows':rows,'always_over_oracle':gm([r['always_over_oracle'] for r in rows]),'guard_over_always':gm([r['guard_over_always'] for r in rows]),'guard_always_distribution':describe([r['guard_over_always'] for r in rows]),'families':{f:{'n':30,'guard_over_always':gm([r['guard_over_always'] for r in g]),'always_over_oracle':gm([r['always_over_oracle'] for r in g])} for f,g in zip(families,groups)},'target_faster_than_always_prompts':target_faster,'target_faster_count':len(target_faster),'always_over_target_on_target_faster':describe([r['always_over_target'] for r in target_faster]),'guard_over_target_on_target_faster':describe([r['guard_over_target'] for r in target_faster]),'target_faster_fallback_runs':sum(r['fallback_runs'] for r in target_faster),'target_faster_guard_runs':3*len(target_faster),'stratified_sensitivity':{'post_study_secondary':True,'family_order':families,'seed':2026100101,'draws':10000,'percentile':'linear','guard_over_always_ci95':[quantile(ga,q) for q in (.025,.975)],'always_over_oracle_ci95':[quantile(ao,q) for q in (.025,.975)]}}
    h={}
    for path in ('CPU','NPU'):
        rows358=[r for r in inputs['358H']['rows'] if r['condition']==path+'_DRAFT_K2'];assert len(rows358)==90
        sums={k:math.fsum(float(r[k]) for r in rows358) for k in ('baseline_end_to_end_ms','end_to_end_ms','draft_replay_proposal_ms','verification_ms','orchestration_residual_ms','rounds')}
        n=inputs['358H']['output_tokens_per_path'][path]; rounds=sums['rounds'];tb=sums['baseline_end_to_end_ms']/n;c=n/rounds
        assert all(float(r['draft_replay_proposal_ms'])>=0 and float(r['orchestration_residual_ms'])>=0 for r in rows358)
        assert math.isclose(sums['draft_replay_proposal_ms']+sums['verification_ms']+sums['orchestration_residual_ms'],sums['end_to_end_ms'],abs_tol=.0001)
        assert math.isclose(math.fsum(float(r['realized_c'])*float(r['rounds']) for r in rows358),n)
        d=sums['draft_replay_proposal_ms']/(tb*rounds);rt=sums['verification_ms']/(tb*rounds);x=sums['orchestration_residual_ms']/(tb*rounds);bound=c/rt;speed=c/(d+rt+x)
        assert speed<=bound<1
        h[path]={'sums':sums,'output_ids':n,'C':c,'Tb_ms_per_ID':tb,'D':d,'R_target':rt,'X':x,'total_time_ratio':speed,'zero_draft_residual_bound':bound,'conditional_arithmetic_only':True}
    lat=inputs['RTX'];assert len(lat)==180; tasks=sorted({r['task_id'] for r in lat},key=lambda t:int(t.split('/')[-1])); assert len(tasks)==30
    med=[];dist={}
    for t in tasks:
        vals={c:[r['milliseconds'] for r in lat if r['task_id']==t and r['condition']==c] for c in ('TARGET_REFERENCE','RTX_SERIALIZED_K2')}
        assert all(len(v)==3 for v in vals.values())
        a=statistics.median(vals['TARGET_REFERENCE']);b=statistics.median(vals['RTX_SERIALIZED_K2']);med.append({'task_id':t,'reference_median_ms':a,'serialized_median_ms':b,'ratio':a/b})
    assert med==inputs['RTX_original']['per_prompt']
    for c,f in [('TARGET_REFERENCE','reference_median_ms'),('RTX_SERIALIZED_K2','serialized_median_ms')]:dist[c]={'90_run_ms':describe([r['milliseconds'] for r in lat if r['condition']==c]),'30_prompt_medians_ms':describe([r[f] for r in med])}
    logs=[math.log(r['ratio']) for r in med];g=gm([r['ratio'] for r in med]);rng=random.Random(2026093002)
    boot=[math.exp(math.fsum(logs[rng.randrange(30)] for _ in range(30))/30) for _ in range(10000)];ci=[quantile(boot,q) for q in (.025,.975)]
    assert g==0.6458157742698285 and abs(g-inputs['RTX_original']['speedup'])<1e-14
    assert all(abs(a-b)<1e-14 for a,b in zip(ci,inputs['RTX_original']['bootstrap_95_ci']))
    probe=inputs['RTX_hook_probe'];assert probe['PASS'] and probe['p99_microseconds']<=probe['threshold_us'] and probe['p99_microseconds']/1000 < probe['relative_threshold']*probe['shortest_r0_ms']
    counts=inputs['RTX_log_counts'];assert len(counts)==180
    paired={(r['task_id'],r['repetition'],r['condition']):r for r in counts};assert len(paired)==180
    for t in tasks:
        for rep in (1,2,3):assert paired[t,rep,'TARGET_REFERENCE']['committed_ID_events']==paired[t,rep,'RTX_SERIALIZED_K2']['committed_ID_events']
    logdist={c:{field:describe([r[field] for r in counts if r['condition']==c]) for field in ('native_log_bytes','native_log_lines','committed_ID_events')} for c in ('TARGET_REFERENCE','RTX_SERIALIZED_K2')}
    rtx={'prompt_rows':med,'distributions':dist,'independent_primary_GM':g,'original_sealed_GM':inputs['RTX_original']['speedup'],'original_ci95':inputs['RTX_original']['bootstrap_95_ci'],'replayed_ci95':ci,'original_seed':2026093002,'hook_probe':probe,'hook_p99_fraction_shortest':probe['p99_microseconds']/1000/probe['shortest_r0_ms'],'logging_counts':logdist,'logging_scope':'Complete native-log file counts include initialization outside timer; counts/bytes are not logging cost and do not imply condition-dependent cancellation'}
    return {'post_study':True,'B570':b570,'M4':m4,'358H':h,'RTX':rtx},score_rows
def analyze(work):
    assert (E/'DERIVED_ANALYSIS_PLAN_V086.md').exists()
    # Transparent output-only adaptation of the unchanged prior raw projector.
    old = ROOT/'paper/mlsys2027/scripts/project_evidence_v085.py'
    source = old.read_text()
    replacements = [("(E/'FOLLOWUP_PROJECTION_V085.json')", "(work.parent/'FOLLOWUP_RAW_REPLAY_V086.json')"),
                    ("(H/'tables/followup_values_v085.tex')", "(work.parent/'followup_replay_v086.tex')"),
                    ("E/'ARCHIVE_REPLAY_V085_QA.json'", "E/'ARCHIVE_REPLAY_V086_QA.json'")]
    for original,redirected in replacements:
        assert original in source; source=source.replace(original,redirected)
    namespace={'__file__':str(old),'__name__':'v086_raw_projection'}
    exec(compile(source,str(old),'exec'),namespace)
    projection=namespace['project'](work)
    # JSON object keys (endpoint length bins) are strings after serialization.
    assert json.loads(json.dumps(projection['studies']))==read(E/'FOLLOWUP_PROJECTION_V085.json')['studies']
    assert (work.parent/'followup_replay_v086.tex').read_bytes()==(ROOT/'paper/mlsys2027/manuscript/tables/followup_values_v085.tex').read_bytes()
    (E/'FOLLOWUP_RAW_REPLAY_V086_QA.json').write_text(json.dumps({'status':'RERUN_PASS','original_projector_sha256':sha(old),'adaptation':replacements,'complete_studies_element_equal':True,'all_prior_assertions_active':True,'raw_projection_sha256':sha(work.parent/'FOLLOWUP_RAW_REPLAY_V086.json'),'new_archive_receipt_sha256':sha(E/'ARCHIVE_REPLAY_V086_QA.json')},indent=2)+'\n')
    inputs,sources=prepare(work);result,score_rows=compute(inputs)
    (E/'DERIVED_INPUTS_V086.json').write_text(json.dumps(inputs,indent=2)+'\n')
    result['author_input_manifest']=sources;result['plan_sha256']=sha(E/'DERIVED_ANALYSIS_PLAN_V086.md');result['inputs_sha256']=sha(E/'DERIVED_INPUTS_V086.json')
    (E/'DERIVED_ANALYSIS_V086.json').write_text(json.dumps(result,indent=2)+'\n')
    for filename,rows in [('B570_SCORE_ROWS_V086.csv',score_rows),('B570_LATER_CASES_V086.csv',result['B570']['later_cases']),('M4_PROMPT_RATIOS_V086.csv',result['M4']['prompt_rows']),('RTX_ABSOLUTE_LATENCY_V086.csv',result['RTX']['prompt_rows'])]:
        with (E/filename).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    macro={'DerCPUZero':f"{result['358H']['CPU']['zero_draft_residual_bound']:.4f}",'DerNPUZero':f"{result['358H']['NPU']['zero_draft_residual_bound']:.4f}",'DerAlwaysOracle':f"{result['M4']['always_over_oracle']:.4f}",'DerTargetFaster':str(result['M4']['target_faster_count']),'DerScoreAbsMedian':f"{result['B570']['distributions']['top1_score']['absolute']['median']:.4f}",'DerScoreAbsMax':f"{result['B570']['distributions']['top1_score']['absolute']['maximum']:.4f}",'DerMarginMin':f"{result['B570']['primary_margin']['minimum']:.4f}",'DerMarginAltMin':f"{result['B570']['alternate_margin']['minimum']:.4f}",'DerRTXTargetMs':f"{result['RTX']['distributions']['TARGET_REFERENCE']['30_prompt_medians_ms']['median']:.1f}",'DerRTXSerialMs':f"{result['RTX']['distributions']['RTX_SERIALIZED_K2']['30_prompt_medians_ms']['median']:.1f}"}
    (ROOT/'paper/mlsys2027/manuscript/tables/derived_values_v086.tex').write_text('% Post-study existing-record derived values; no original primary macro altered.\n'+''.join('\\newcommand{\\'+k+'}{'+v+'}\n' for k,v in macro.items()))
    print(json.dumps({'status':'RERUN_PASS','B570':{'score_rows':216,'absolute_top1_delta':result['B570']['distributions']['top1_score']['absolute'],'primary_margin':result['B570']['primary_margin'],'later_cases':[r for r in result['B570']['later_cases'] if r['repetition']==1]},'M4':{k:result['M4'][k] for k in ('always_over_oracle','target_faster_count','target_faster_fallback_runs','stratified_sensitivity')},'358H':{p:r['zero_draft_residual_bound'] for p,r in result['358H'].items()},'RTX':{c:r['30_prompt_medians_ms'] for c,r in result['RTX']['distributions'].items()}},indent=2))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);a=p.parse_args();analyze(a.work.resolve())
