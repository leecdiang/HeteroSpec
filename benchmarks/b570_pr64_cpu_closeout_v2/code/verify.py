"""Third CPU pass over raw costs/IDs and derived outputs; no execution comparator imports."""
from evidence import *
import copy, math, numpy as np, statistics, zipfile

def validate_keys(rows,expected):
    keys=[(r['task'],r['label'],int(r['round'])) for r in rows]
    assert len(keys)==len(set(keys)), 'duplicate request key'
    assert set(keys)==expected,'missing/extra denominator'
    assert all(str(r['qualified']) in ['True','true'] for r in rows),'unqualified costs'

def validate_ratio(pair,baseline,candidate):
    assert math.isclose(float(pair),baseline/candidate,rel_tol=1e-12),'inverted/incorrect ratio'

def validate_raw_claim(ids,reference,claim):
    if claim:assert ids==reference,'endpoint agreement relabelled as raw equality'

def main():
    begin('verification');checks=0
    def ck(x,label):
        nonlocal checks
        assert x,label;checks+=1
    bindings=json.loads((OUT/'INPUT_BINDINGS.json').read_text())['files']
    for n,x in bindings.items():
        data=(RAW/n).read_bytes();ck(len(data)==x['bytes'] and digest(data)==x['sha256'],'old restore changed '+n)
    with open(CFG['archive'],'rb') as f:ck(hashlib.file_digest(f,'sha256').hexdigest()==CFG['archive_sha256'],'old CAS archive identity')
    db=json.loads((OUT/'D_REFERENCE_BINDINGS.json').read_text())
    for n,x in db['verified_files'].items():ck(digest((pathlib.Path(db['read_only_restore'])/n).read_bytes())==x['sha256'],'PR63 raw changed '+n)
    counts=json.loads((OUT/'COUNTS.json').read_text());ck(counts['missing_units']==['E/FORMAL/1/old_N1/MBPP/400'],'missing old N1 exact')
    tasks=[x['id'] for x in load('E_INPUTS.json')];missing=('MBPP/400','old_N1',1);expected={(t,l,k) for t in tasks for l in ['ordinary_R','matched_target','candidate','old_N1'] for k in [1,2]}-{missing}
    costs=list(csv.DictReader((OUT/'COSTS_RECOMPUTED.csv').open(encoding='utf-8')));validate_keys(costs,expected);checks+=3
    raw={};scalar={};q={r['unit_id']:r for r in csv.DictReader((OUT/'QUALIFICATION_RECOMPUTED.csv').open(encoding='utf-8'))}
    eog=set(load('dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids'])
    for c in costs:
        r=load(c['source_receipt']);p=next(p for p in r['files'] if p.endswith('/capture.json'));a=load(p)
        # Independent length derivation, separate from evidence.endpoint.
        stop=128
        for i,token in enumerate(a['ids']):
            if token in eog:stop=min(stop,i+1);break
        ck(a['eog']==[t in eog for t in a['ids']] and len(a['ids'])>=stop,'runtime EOG/end condition')
        ck(stop==int(c['endpoint_length']) and len(a['ids'])-stop==int(c['raw_suffix']),'raw suffix charged')
        for m,k in [('generation_ms','generation_ms'),('whole_ms','whole_request_ms')]:ck(float(c[m])==r['metrics'][k],'native absolute timer')
        ck(float(c['host_ms'])==r['host_seconds']*1000,'host absolute timer')
        raw[c['task'],c['label'],int(c['round'])]=dict(ids=a['ids'],eog=a['eog'],end=(a['ids'][:stop],a['eog'][:stop]))
        scalar[c['task'],c['label'],int(c['round'])]=c
    for key,a in raw.items():
        ref=raw[key[0],'ordinary_R',1];ck(a['end']==ref['end'],'cost eligibility endpoint')
        row=q[scalar[key]['unit_id']];actual=a['ids']==ref['ids'] and a['eog']==ref['eog'];ck((row['raw_reference_equal']=='True')==actual,'raw equality distinct')
    pairs=list(csv.DictReader((OUT/'COST_TASK_PAIRS.csv').open(encoding='utf-8')))
    sums={}
    for p in pairs:
        t,b,c=p['task'],p['baseline'],p['candidate']
        for m in ['generation_ms','whole_ms','host_ms']:
            B=sum(float(scalar[t,b,k][m]) for k in [1,2])/2;C=sum(float(scalar[t,c,k][m]) for k in [1,2])/2
            validate_ratio(p['speed_'+m],B,C);checks+=1;ck(float(p['baseline_'+m])==B and float(p['candidate_'+m])==C,'pair absolute median')
            sums.setdefault((b+'/'+c,m),[]).append(B/C)
    summary=json.loads((OUT/'COST_SUMMARY.json').read_text())
    for (key,m),xs in sums.items():
        independently=math.prod(xs)**(1/len(xs));ck(math.isclose(independently,summary['comparisons'][key]['metrics'][m]['task_GM'],rel_tol=1e-12),'task GM')
        ck(len(xs)==(14 if key.startswith('old_N1') else 15),'paired denominator')
    fig=json.loads((OUT/'FIGURE_DATA.json').read_text())
    for series in fig['speed']:
        for t,v in zip(series['tasks'],series['values']):
            p=next(x for x in pairs if x['task']==t and x['baseline']==series['baseline'] and x['candidate']=='candidate');ck(v==float(p['speed_'+series['timer']]),'plotted scalar')
    causal=json.loads((OUT/'CAUSAL_RECHECK.json').read_text());scores=list(csv.DictReader((OUT/'CAUSAL_ALL_ROW_SCORES.csv').open(encoding='utf-8')))
    for c in causal['cases']:
        for cell in c['cells']:
            r=load('aux/'+cell['unit_id'].replace('/','_')+'/RESULT.json');p=next(n for n in r['files'] if n.endswith('/cross.json'));a=np.frombuffer(read(p+'.logits.f32'),dtype='<f4').reshape(-1,151936)
            di,ri=map(int,cell['unit_id'].split('/')[-2:]);focus=int(np.argmax(a[c['focus_row']]));ck(c['focus']['decisions'][di][ri]==focus,'plotted argmax raw')
            for i,x in enumerate(a):
                row=next(s for s in scores if int(s['case'])==c['case'] and int(s['donor'])==di and int(s['recipe'])==ri and int(s['row'])==i);top=int(np.argmax(x));second=int(np.argmax(np.where(np.arange(len(x))==top,-np.inf,x)))
                ck(top==int(row['top1']) and second==int(row['top2']) and float(x[top])==float(row['top1_score']),'all raw score rows')
    negatives=[]
    fixtures=[('missing_denominator',lambda:validate_keys(costs[:-1],expected)),('duplicate_key',lambda:validate_keys(costs+[costs[0]],expected)),('wrong_ratio_direction',lambda:validate_ratio(2,1,2)),('endpoint_suffix_misqualification',lambda:validate_raw_claim([151645,271],[151645],True)),('unqualified_cost',lambda:validate_keys([dict(x,qualified='False') if i==0 else x for i,x in enumerate(costs)],expected))]
    for n,fn in fixtures:
        try:fn()
        except AssertionError as e:negatives.append(dict(case=n,status='REJECTED',reason=str(e)))
        else:raise AssertionError('negative fixture accepted '+n)
    ck(len(negatives)==5,'negative fixture count')
    qa=json.loads((OUT/'FIGURE_VISUAL_QA.json').read_text());ck(qa['status']=='PASS','visual QA')
    sampler=list(csv.DictReader((OUT/'SAMPLER_TIMER_AUDIT.csv').open(encoding='utf-8')));ck({r['unit_id'] for r in sampler}=={c['unit_id'] for c in costs if c['label']=='candidate'},'target sampling timer denominator')
    audit=json.loads((OUT/'LOG_TIMER_AUDIT.json').read_text());ck(math.isclose(sum(float(r['target_common_sampling_ms_printed']) for r in sampler),audit['target_common_sampling_ms_sum'],rel_tol=1e-12) and not audit['full_component_breakdown_available'],'scoped sampling timer and scope')
    for n,h in qa['figures'].items():ck(digest((OUT/'figures'/n).read_bytes())==h,'visually reviewed figure changed')
    for x in [counts,summary,json.loads((OUT/'SOURCE_BINDINGS.json').read_text(encoding='utf-8'))]:ck(all(x[k]==0 for k in ['new_model_requests','new_forward','new_warmup']),'zero new model work')
    decisions=json.loads((OUT/'DECISION.json').read_text());ck(decisions['E_status']=='PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED' and decisions['B570_GPU_NEXT_ACTION']=='STOP','scientific state')
    mandatory=['REPORT.zh-CN.md','DECISION.json','COUNTS.json','COST_EXPLANATION.md','WORK_BREAKDOWN.csv','COSTS_RECOMPUTED.csv','CAUSAL_RECHECK.json','CLAIM_EVIDENCE_MATRIX.csv','RELATED_WORK.md','PAPER_HANDOFF.md','CROSS_PLATFORM_GAPS.md','REOPEN_GATE.json','NEXT_STAGE.md','SOURCE_BINDINGS.json','README.md']
    for n in mandatory:ck((OUT/n).is_file() and (OUT/n).stat().st_size>0,'required deliverable '+n)
    write('INDEPENDENT_VERIFICATION.json',dict(status='PASS',checks=checks,negative_fixtures=negatives,raw_CAS_selected_files=len(bindings),raw_PR63_reference_files=len(db['verified_files']),formal_cost_rows=119,derived_pair_rows=len(pairs),cross_cases=6,raw_score_rows=len(scores),old_source_raw_and_archive_unchanged=True,RTX_raw_status='DEFERRED_RTX_RAW_ACCESS',no_new_models_or_forwards=True,limits=['D HumanEval references are endpoint exports; complete historical raw not available in selected evidence','formal per-step bonus/correct and component times unknown','RTX public sources are not independently reanalyzed private raw'],verification_source_sha256=digest(pathlib.Path(__file__).read_bytes())))
    decisions['CPU_closeout']='CPU_AUDIT_COMPLETE';decisions['remote_delivery']='VERIFY_AFTER_NEW_DRAFT_PR';write('DECISION.json',decisions)
    finish('verification');print('PASS',checks,'checks; 5 negative fixtures rejected')
if __name__=='__main__':main()
