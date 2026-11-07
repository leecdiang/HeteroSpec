from evidence import *
import math,statistics
from collections import Counter

def gm(xs):return math.exp(statistics.mean(math.log(x) for x in xs))
def main():
    begin('cost_work');eog=set(load('dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids']); rows=[]; works=[];development=[];matched=[];targetdev=[]
    for p in sorted((RAW/'raw').glob('*/RESULT.json')):
        d=load(p.relative_to(RAW).as_posix());u=d['unit_id']
        if not u.startswith(('E/FORMAL/','C/','E/BRIDGE/')) or d['warm']:continue
        c=load(next(p for p in d['files'] if p.endswith('/capture.json')));ep=endpoint(c['ids'],c['eog'],eog)
        if u.startswith('E/FORMAL/'):
            rows.append(dict(unit_id=u,task=d['task'],label=d['config']['label'],round=d['config']['round'],generation_ms=d['metrics']['generation_ms'],whole_ms=d['metrics']['whole_request_ms'],host_ms=1000*d['host_seconds'],endpoint_length=len(ep['ids']),raw_length=len(c['ids']),raw_suffix=len(c['ids'])-len(ep['ids']),qualified=True,source_receipt=p.relative_to(RAW).as_posix()))
        if d['config']['label'] in ['matched_target','matched_bridge']:
            w=c['work'];P=len(c['prompt_ids']);L=len(c['ids']);assert w['target_calls']==math.ceil(P/512)+L-1 and w['target_caller_tokens']==P+L-1 and w['draft_calls']==w['draft_caller_tokens']==0
            mr=dict(unit_id=u,prompt_tokens=P,endpoint_tokens=len(ep['ids']),target_continuation_caller_tokens=w['target_caller_tokens']-P,target_continuation_caller_calls=w['target_calls']-math.ceil(P/512))
            if c['trace']:
                dec=[t for t in c['trace'] if t['event']=='decode'];assert len(dec)==w['target_calls'] and sum(t['caller_batch_length'] for t in dec)==w['target_caller_tokens'];assert [t['id'] for t in c['commits']]==c['ids'];targetdev.append(mr)
            if d['config']['label']=='matched_target':matched.append(mr)
        if not d['config']['native'] or (u.startswith('E/FORMAL/') and d['config']['label']!='candidate'):continue
        w=c['work'];P=len(c['prompt_ids']);A=d['metrics']['accepted'];D=d['metrics']['drafted'];L=len(c['ids']);V=w['target_calls']-math.ceil(P/512);catch=w['draft_calls']-1-D
        assert d['config']['k']==2 and w['target_caller_tokens']-P==3*V and D==2*V
        assert catch==w['draft_caller_tokens']-P-D==L-A==V+1
        assert 0<=A<=D
        x=dict(unit_id=u,task=d['task'],round=d['config']['round'],prompt_tokens=P,endpoint_tokens=len(ep['ids']),raw_tokens=L,raw_suffix=L-len(ep['ids']),drafted=D,accepted=A,acceptance=A/D if D else 0,target_calls=w['target_calls'],target_caller_tokens=w['target_caller_tokens'],draft_calls=w['draft_calls'],draft_caller_tokens=w['draft_caller_tokens'],target_prompt_caller_calls=math.ceil(P/512),target_prompt_caller_tokens=P,draft_prompt_caller_calls=1,draft_prompt_caller_tokens=P,target_verification_caller_calls=V,target_verification_caller_tokens=w['target_caller_tokens']-P,draft_proposal_calls=D,draft_proposal_tokens=D,draft_catchup_calls=catch,draft_catchup_tokens=catch,nonaccepted_commits=L-A,initial_commit=1,bonus_commits='unknown_capture_off',correct_commits='unknown_capture_off',source_target_KV_mutation_calls=4*catch+V,source_draft_KV_mutation_calls=4*catch,source_sampler_clones=V,source_distribution_vector_copy_calls=D,target_continuation_caller_tokens_per_endpoint=(w['target_caller_tokens']-P)/len(ep['ids']),draft_continuation_caller_tokens_per_endpoint=(w['draft_caller_tokens']-P)/len(ep['ids']),source_duration_ms='unknown_component_timers',kernel_dispatches='unknown_not_caller_calls')
        if c['trace']:
            calls=[t for t in c['trace'] if t['event']=='caller_decode']
            # Observer records begin/end; verify against the begin records, one per caller.
            begins=[t for t in c['trace'] if t['event']=='decode']
            for role in ['target','draft']:
                rs=[t for t in begins if t['role']==role]
                assert len(rs)==w[role+'_calls'], 'trace caller count '+u
                assert sum(t['caller_batch_length'] for t in rs)==w[role+'_caller_tokens']
                assert sum(t['event']=='kv_mutation' and t['role']==role for t in c['trace'])==x['source_'+role+'_KV_mutation_calls']
            assert [t['id'] for t in c['commits']]==c['ids'] and sum(t['accepted'] for t in c['commits'])==A
            rel=Counter(t['relationship'] for t in c['commits']);x['correct_commits']=rel['correct'];x['bonus_commits']=rel['sample_or_bonus']-1
            development.append(x)
        if u.startswith('E/FORMAL/') and d['config']['label']=='candidate':works.append(x)
    assert len(rows)==119 and len(works)==30
    # Qualify each cost against both paid R repeats, not an executor-supplied flag.
    qrows=list(csv.DictReader((OUT/'QUALIFICATION_RECOMPUTED.csv').open(encoding='utf-8')));qual={r['unit_id']:r['reference_endpoint_equal']=='True' for r in qrows}
    assert all(qual[x['unit_id']] for x in rows)
    keyed={(r['task'],r['label'],r['round']):r for r in rows};tasks=sorted(set(r['task'] for r in rows));pairs=[];summary={};roundrows=[]
    for baseline,candidate in [('ordinary_R','candidate'),('matched_target','candidate'),('old_N1','candidate'),('ordinary_R','matched_target')]:
        ts=[t for t in tasks if all((t,l,k) in keyed for l in [baseline,candidate] for k in [1,2])]
        stats={};bytime={m:[] for m in ['generation_ms','whole_ms','host_ms']}
        for t in ts:
            p=dict(task=t,baseline=baseline,candidate=candidate,rounds=2)
            for m in bytime:
                b=statistics.median(keyed[t,baseline,k][m] for k in [1,2]);c=statistics.median(keyed[t,candidate,k][m] for k in [1,2]);ratio=b/c
                p[baseline+'_'+m]=b;p[candidate+'_'+m]=c;p['speed_'+m]=ratio;p['duration_multiplier_'+m]=c/b;bytime[m].append(ratio)
            pairs.append(p)
            for k in [1,2]:
                rr=dict(task=t,round=k,baseline=baseline,candidate=candidate)
                for m in bytime:rr[m+'_speed']=keyed[t,baseline,k][m]/keyed[t,candidate,k][m]
                roundrows.append(rr)
        for m,ratios in bytime.items():stats[m]=dict(task_GM=gm(ratios),task_faster=sum(x>1 for x in ratios),task_slower=sum(x<1 for x in ratios),paired_round_faster=sum(r[m+'_speed']>1 for r in roundrows if r['baseline']==baseline and r['candidate']==candidate),paired_round_slower=sum(r[m+'_speed']<1 for r in roundrows if r['baseline']==baseline and r['candidate']==candidate),round_direction_exceptions=[dict(task=r['task'],round=r['round'],speed=r[m+'_speed']) for r in roundrows if r['baseline']==baseline and r['candidate']==candidate and ((r[m+'_speed']<1) if baseline=='old_N1' else (r[m+'_speed']>1))])
        summary[baseline+'/'+candidate]=dict(tasks=len(ts),rounds=2,metrics=stats)
    # Unified schemas for variable baseline names.
    uniform=[]
    for p in pairs:
        x={k:p[k] for k in ['task','baseline','candidate','rounds']}
        for m in ['generation_ms','whole_ms','host_ms']:
            for field,key in [('baseline_',p['baseline']+'_'+m),('candidate_',p['candidate']+'_'+m),('speed_','speed_'+m),('duration_multiplier_','duration_multiplier_'+m)]:x[field+m]=p[key]
        uniform.append(x)
    table('COSTS_RECOMPUTED.csv',rows);table('COST_TASK_PAIRS.csv',uniform);table('COST_ROUND_PAIRS.csv',roundrows);table('WORK_BREAKDOWN.csv',works)
    if development:table('DEVELOPMENT_WORK_CHECK.csv',development)
    table('MATCHED_TARGET_WORK.csv',matched);table('DEVELOPMENT_TARGET_WORK_CHECK.csv',targetdev)
    for key,expected in [('ordinary_R/candidate',[.28258755350958753,.2012895931787418,.2018837104115267]),('matched_target/candidate',[.28576136794192253,.2057042276473282,.20624276201591446]),('old_N1/candidate',[3.993091253126628,2.6339404210545707,2.6333865472136697])]:
        for m,e in zip(['generation_ms','whole_ms','host_ms'],expected):assert math.isclose(summary[key]['metrics'][m]['task_GM'],e,rel_tol=1e-12)
    totals={k:sum(x[k] for x in works) for k in ['prompt_tokens','endpoint_tokens','raw_tokens','raw_suffix','drafted','accepted','target_calls','target_caller_tokens','draft_calls','draft_caller_tokens','target_verification_caller_calls','target_verification_caller_tokens','draft_proposal_calls','draft_catchup_calls','source_target_KV_mutation_calls','source_draft_KV_mutation_calls','source_sampler_clones','source_distribution_vector_copy_calls']}
    totals['pooled_accepted_over_drafted']=totals['accepted']/totals['drafted'];totals['target_continuation_tokens_over_endpoint']=totals['target_verification_caller_tokens']/totals['endpoint_tokens'];totals['draft_continuation_tokens_over_endpoint']=(totals['drafted']+totals['draft_catchup_calls'])/totals['endpoint_tokens']
    assert len(matched)==30 and len(targetdev)==4
    write('COST_SUMMARY.json',dict(ratio_definition='baseline_ms/candidate_ms; >1 candidate faster',aggregation='per task median of two absolute costs, ratio, unweighted task geometric mean',comparisons=summary,formal_candidate_work_totals=totals,matched_target_continuation_caller_tokens=sum(x['target_continuation_caller_tokens'] for x in matched),development_capture_on_checked=len(development),bridge_capture_on_checked=len(targetdev),component_durations='Full decomposition unavailable; scoped target common-sampling log timer in LOG_TIMER_AUDIT; draft, verification, complete sampling, rollback, synchronization and host scheduling durations unknown',cold_model_loads='outside warm-session per-request whole timer',suffix_work='all paid; never time-rescaled to endpoint',new_model_requests=0,new_forward=0,new_warmup=0))
    for p in ['candidate-front/native.cpp','candidate-front/target.cpp','candidate-front/phase.h','candidate-front/observer.h','candidate-src/llama-context.cpp','candidate-common/sampling.cpp','C_PRIVATE_LIBRARY.patch']:read(p)
    finish('cost_work');print(json.dumps(dict(comparisons=summary,totals=totals,development=len(development))))
if __name__=='__main__':main()
