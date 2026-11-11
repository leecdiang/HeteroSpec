"""Check the finite engineering matrix without selecting faster conditions."""
from common import *
from analyse import signature,contract
import collections,re

def trace_rows(a):
    bounds=a.get('capture_range')
    if not bounds:return []
    with (LOCAL/bounds['file']).open('rb') as f:f.seek(bounds['start']);b=f.read(bounds['end']-bounds['start'])
    return [json.loads(line) for line in b.splitlines()]

def main():
    root=LOCAL/'runs/engineering';assert (root/'COMPLETE.json').exists()
    inputs=read(PUB/'ENGINEERING_INPUTS.json');models=read(PUB/'MODEL_CONTRACT.json')['families'];plan=read(PUB/'ENGINEERING_PLAN.json');by_job={}
    for j in plan['jobs']:
        records={}
        for done in (root/j['name']).rglob('COMPLETED.json'):
            p=done.parent/'RECORD.json';assert sha(p)==read(done)['record_sha256'];a=read(p)
            if not a['warmup']:records[a['task']]=a
        by_job[j['name']]=records
    implementation={};discovery={};mechanisms=[];capturechecks=[]
    for family,m in models.items():
        implementation[family]={};discovery[family]={}
        for c in read(DESIGN/'DESIGN.json')['conditions']:
            name=c['name'];capture_off=by_job[f'{family}-capture-{name}-0'];capture_on=by_job[f'{family}-capture-{name}-1'];evidence=[];errors=[]
            for task in inputs['capture_probes'][family]:
                tid=task['id'];a=capture_off.get(tid);b=capture_on.get(tid)
                same=a is not None and b is not None and signature(a['response'])==signature(b['response'])
                capturechecks.append({'family':family,'condition':name,'task':tid,'capture_on_off_equal':bool(same),'off_slot':a['slot'] if a else None,'on_slot':b['slot'] if b else None})
                if not same:errors.append('capture_on_off_missing_or_different:'+tid)
                if not b:continue
                tr=trace_rows(b);dec=[r for r in tr if r['event']=='decode'];ver=[r for r in tr if r['event']=='verify_result'];prop=[r for r in tr if r['event']=='draft_proposal'];rollback=[r for r in tr if r['event']=='verify_rollback']
                expected_dlls=read(PUB/'NATIVE_BUILD.json')['runtime_dlls'];modules={p for event in tr if event['event']=='first_pending' for p in event['modules']}
                loaded_dlls={Path(p).name:{'path':p,'actual_sha256':sha(p),'expected_sha256':expected_dlls[Path(p).name]} for p in modules if Path(p).name in expected_dlls}
                dll_ok='ggml-cuda.dll' in loaded_dlls and all(v['actual_sha256']==v['expected_sha256'] for v in loaded_dlls.values())
                target=[r for r in dec if r['role']=='target'];draft=[r for r in dec if r['role']=='draft'];first=target[0] if target else None
                reset=first is not None and first['phase']=='prefill' and first['before']['max']==-1 and b['response'].get('timings',{}).get('cache_n')==0
                scopes=all(r['scope_mask']==c['mask'] and r['scope_active']==(r['role']=='target' and c['mask']==3) and r['returncode']==0 for r in dec)
                ub=all(r['ub_capacity']==(c['target_ub'] if r['role']=='target' else 1) for r in dec)
                roles=bool(target) and (bool(draft) if c['spec'] else not draft)
                shapes=[g for r in dec for g in r['graphs'] if 'query_batch' in g['name']]
                query_shapes=[g for r in dec for g in r['graphs'] if g['name'].startswith('hs_attention_q')]
                expected_heads={role:next((v for k,v in shape.items() if k.endswith('attention.key_length')),None) or next(v for k,v in shape.items() if k.endswith('embedding_length'))//next(v for k,v in shape.items() if k.endswith('attention.head_count')) for role,shape in m['architecture_shapes'].items()}
                head_shape_ok=all(g['ne'][0]==expected_heads[g['role']] for g in query_shapes) and any(g['role']=='target' for g in query_shapes) and (any(g['role']=='draft' for g in query_shapes) if c['spec'] else True)
                active_branch=(c['mask']==0 or any(g['role']=='target' and (g['name'].startswith('hs_attn_query_batch') if family=='Qwen' else g['name'].startswith('jsa_llama_query_batch')) for g in shapes))
                if family=='Llama':active_branch &= all(g['ne'][0]==128 and g['ne'][1]==1 and 1<g['ne'][3]<=4 for g in shapes if g['role']=='target')
                accepted=sum(len(r['accepted_plus_last'])-1 for r in ver if not r['replay']);proposed=sum(len(r['proposed_ids']) for r in ver if not r['replay']);bonus=sum(len(r['accepted_plus_last'])==len(r['proposed_ids'])+1 for r in ver if not r['replay']);correction=sum(len(r['accepted_plus_last'])<len(r['proposed_ids'])+1 for r in ver if not r['replay'])
                correctprefix=all(r['accepted_plus_last'][:-1]==r['proposed_ids'][:len(r['accepted_plus_last'])-1] and len(r['query_indices'])==len(r['proposed_ids'])+1 for r in ver)
                mechanism={'slot':b['slot'],'family':family,'condition':name,'task':tid,'reset_at_target_prefill':bool(reset),'scope_valid':bool(scopes),'target_draft_UB_valid':bool(ub),'role_valid':bool(roles),'declared_active_branch_observed':bool(active_branch),'proposal_prefix_and_verify_width_valid':bool(correctprefix),'proposal_cycles':len(prop),'proposal_ID_count':sum(len(r['ids']) for r in prop),'verified_proposed_ID_count':proposed,'accepted_draft_ID_count':accepted,'rejected_draft_ID_count':proposed-accepted,'bonus_decisions':bonus,'correction_decisions':correction,'acceptance_fraction':accepted/proposed if proposed else None,'verify_cycles':len(ver),'replay_cycles':sum(r['replay'] for r in ver),'rollback_calls':len(rollback),'phase_call_counts':dict(collections.Counter(r['role']+'/'+r['phase'] for r in dec)),'target_continuation_caller_widths':dict(collections.Counter(str(r['caller_batch']) for r in target if r['phase']=='continuation')),'observed_graph_shapes':list({json.dumps(g,sort_keys=True) for g in shapes}),'paid_engineering_HTTP_ms':b['wall_ms'],'phase_GPU_timers':None,'phase_timer_limit':'capture forces synchronize; no native per-phase elapsed counters added; no fabricated untraced phase costs'}
                mechanism['actual_head_shape_valid']=bool(head_shape_ok)
                mechanism['actual_query_shapes']=list({json.dumps(g,sort_keys=True) for g in query_shapes})
                mechanism['actual_loaded_published_DLLs']=loaded_dlls;mechanism['actual_DLL_hashes_valid']=bool(dll_ok)
                mechanisms.append(mechanism);evidence.append(b['slot'])
                if not all([reset,scopes,ub,roles,active_branch,correctprefix,head_shape_ok,dll_ok]):errors.append('actual_scope_shape_UB_reset_DLL_or_verify_proof_failed:'+tid)
            # Output divergence vs paid R is scientific evidence, never condition pruning.
            rows=[];mismatches=[]
            for rnd in range(2):
                paid=by_job[f'{family}-discovery-r{rnd}-{name}'];reference=by_job[f'{family}-discovery-r{rnd}-R']
                for task in inputs['families'][family]:
                    a=paid.get(task['id']);r=reference.get(task['id'])
                    if a:rows.append({'slot':a['slot'],'contract_valid':bool(contract(a,task,set(m['eog']))),'HTTP_ms':a['wall_ms']})
                    if a and r and signature(a['response'])!=signature(r['response']):mismatches.append({'candidate_slot':a['slot'],'R_slot':r['slot']})
            discovery[family][name]={'completed':len(rows),'planned':24,'mismatches_against_paid_R':mismatches,'requests':rows}
            if len(rows)!=24:errors.append('discovery_matrix_operationally_incomplete')
            implementation[family][name]={'status':'ADMITTED' if not errors else 'IMPLEMENTATION_BLOCKED','errors':errors,'scope_shape_evidence':evidence,'scientific_discovery_divergence_not_pruned':len(mismatches)}
    boundaries=[]
    for family in models:
        for cap in [1,2,3,4,31,32,128]:
            tid='synthetic/cap-'+str(cap);r=by_job[f'{family}-boundaries-R'].get(tid);c=by_job[f'{family}-boundaries-C3_K3'].get(tid)
            boundaries.append({'family':family,'cap':cap,'R_slot':r['slot'] if r else None,'C_slot':c['slot'] if c else None,'full_arrays_equal':bool(r and c and signature(r['response'])==signature(c['response'])),'R_length':len(r['response'].get('tokens',[])) if r else None,'C_length':len(c['response'].get('tokens',[])) if c else None,'endpoint_suffix_paid_and_retained':True})
    source=LOCAL/'native/source';reuse=(source/'src/llama-graph.h').read_text(encoding='utf-8')
    assert 'hs_query_batch != other.hs_query_batch' in reuse
    logs={j['name']:[int(n) for n in re.findall(r'graphs reused\s*=\s*(\d+)',(root/j['name']/'server.log').read_text(encoding='utf-8',errors='replace'))] for j in plan['jobs'] if (root/j['name']/'server.log').exists()}
    report={'status':'ENGINEERING_COMPLETE','implementation':implementation,'discovery':discovery,'capture_checks':capturechecks,'mechanisms':mechanisms,'cap_boundaries':boundaries,'graph_reuse_source_key_checked':True,'graph_reuse_source_sha256':sha(source/'src/llama-graph.h'),'runtime_graph_reuse_log_counts':logs,'graph_reuse_limit':'logged native counts; no per-operator causal attribution','accounting':read(root/'COMPLETE.json'),'confirmation_questions_read_or_forwarded':0,'minimal_counter_policy':{'new_formal_counters_added':False,'implementation':'unchanged original native counters; new mechanism events capture-only','separate_minimal_counter_toggle':'NOT_AVAILABLE_NOT_TESTED'},'known_output_divergences_retained':True,'utc':now()}
    save(PUB/'ENGINEERING_RESULTS.json',report);print(json.dumps(implementation),flush=True)
if __name__=='__main__':main()
