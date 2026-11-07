"""Independent output, graph, padding, rollback and state checks."""
import json,hashlib,os
from pathlib import Path
REPO=Path(__file__).resolve().parents[3];PUB=REPO/'benchmarks/jsa_rtx_validation_v1';LOCAL=Path(os.environ.get('JSA_LOCAL_ROOT',str(REPO.parent/'jsa')))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def native_bridge():
    root=LOCAL/'runs/new_core_bridge';refs={r['id']:r for r in read(LOCAL/'OFFLINE_BRIDGE_REFERENCES.json')};checks=[]
    for p in sorted(root.glob('*/*.json')):
        a=read(p)
        if 'task' not in a:continue
        r=a['response'];ref=refs[a['task']];checks.append({'slot':a['slot'],'equal':r['tokens']==ref['original_reference_ids'] and ('EOS' if r['stop_type']=='eos' else 'limit')==ref['original_endpoint'],'cache_zero':r['timings']['cache_n']==0})
    passed=len(checks)==16 and all(r['equal'] and r['cache_zero'] for r in checks);save(PUB/'NEW_CORE_BRIDGE.json',{'status':'PASS' if passed else 'STACK_INCOMPATIBLE','requests':len(checks),'checks':checks});return passed
def family_graph():
    root=LOCAL/'runs/F_graph_proof';checks=[]
    for p in root.glob('*/trace.jsonl'):
        rows=[json.loads(line) for line in p.read_text().splitlines()];command=read(p.parent/'COMMAND.json');mask=command['condition']['mask'];dec=[r for r in rows if r.get('event')=='decode'];valid=True;paths={}
        for r in dec:
            bit={'target':1,'draft':4}[r['role']]*(1 if r['phase']=='prefill' else 2);active=bool(mask&bit);valid&=r['scope_active']==active and r['scope_mask']==mask
            shapes=[g['ne'] for g in r.get('graphs',[]) if g['name']=='jsa_llama_query_batch-0']
            if active and r['caller_batch']>1:
                valid&=bool(shapes) and all(a[1]==1 and 1<a[3]<=4 for a in shapes)
            if shapes:paths[r['role']+'_'+r['phase']]=shapes[:8]
        resets=sum(r['role']=='target' and r['phase']=='prefill' and r['positions'][0]==0 for r in dec);checks.append({'condition':command['condition']['name'],'scope_valid':valid,'reset_count':resets,'actual_llama_paths':paths})
    passed=len(checks)==4 and all(r['scope_valid'] and r['reset_count']>=5 for r in checks)
    save(PUB/'F_GRAPH_QUALIFICATION.json',{'status':'PASS' if passed else 'IMPLEMENTATION_BLOCKED','checks':checks,'output_equality_not_inferred_from_graph_shapes':True});return passed
def discovery():
    root=LOCAL/'runs/F_discovery';records={}
    for p in root.glob('*/*.json'):
        a=read(p)
        if 'task' in a:records[(a['condition']['name'],a['repetition'],a['task'])]=a
    tasks=[r['id'] for r in read(PUB/'F_DISCOVERY_INPUTS.json')];eog=set(read(PUB/'MODEL_CHOICE.json')['eog']);checks={};stable=True
    for t in tasks:
        a=records.get(('R',1,t));b=records.get(('R',2,t));stable&=a is not None and b is not None and a['response']['tokens']==b['response']['tokens'] and a['response']['stop_type']==b['response']['stop_type']
    for c in ['R']+['N'+str(n) for n in range(16)]+['M'+str(n) for n in range(4)]:
        valid=True;failures=[];completed=0
        for rep in [1,2]:
            for t in tasks:
                a=records.get((c,rep,t));ref=records.get(('R',rep,t));completed+=int(a is not None)
                if a is None or ref is None:valid=False;continue
                r=a['response'];ids=r['tokens'];contract=r['timings']['cache_n']==0 and not r['truncated'] and len(ids)==r['tokens_predicted'] and (len(ids)==128 or r['stop_type']=='eos') and not any(i in eog for i in ids[:-1]) and ((ids[-1] in eog)==(r['stop_type']=='eos'))
                equal=ids==ref['response']['tokens'] and r['stop_type']==ref['response']['stop_type'];valid&=contract and equal
                if not equal:failures.append({'task':t,'repetition':rep,'reference_length':len(ref['response']['tokens']),'candidate_length':len(ids)})
        checks[c]={'qualified':stable and valid and completed==24,'completed':completed,'mismatches':failures}
    eligible=[n for n in range(16) if checks['N'+str(n)]['qualified'] and checks['M'+str(n&3)]['qualified']];eligible.sort(key=lambda m:(m.bit_count(),m));selected=eligible[0] if eligible else None
    capture=[]
    for name,c in [('R','R'),('N0','N0'),('C3','N3'),('C15','N15')]:
        for tid in tasks[:4]:
            p=LOCAL/'runs/F_graph_proof'/name/(tid.replace('/','-')+'.json');a=read(p)['response'];equal=all(a['tokens']==records[(c,rep,tid)]['response']['tokens'] and a['stop_type']==records[(c,rep,tid)]['response']['stop_type'] for rep in [1,2]);capture.append({'condition':name,'task':tid,'capture_on_matches_both_capture_off_repeats':equal})
    result={'status':'COMPLETE' if len(records)==504 else 'INCOMPLETE','requests':len(records),'stable_R':stable,'condition_qualification':checks,'capture_on_off_checks':capture,'capture_on_off_qualified':all(r['capture_on_matches_both_capture_off_repeats'] for r in capture),'fixed_C3_qualified':checks['N3']['qualified'],'native_N0_qualified':checks['N0']['qualified'],'eligible_masks':eligible,'selected_mask_output_only':selected,'optional_Csel':selected if selected is not None and selected!=3 else None,'selection_uses_timing':False,'no_trigger_on_discovery':checks['N0']['qualified'],'natural_cross':'NOT_TRIGGERED' if checks['N0']['qualified'] else 'PENDING_ALIGNMENT_AUDIT'}
    save(PUB/'F_DISCOVERY.json',result);return result
def dvr(model):
    root=LOCAL/'runs'/('E_engineering_'+model);plan=read(root/'PLAN.json');eog=set(read(PUB/'MODEL_CHOICE.json')['eog' if model=='SmolLM2' else 'Qwen_eog']);checks=[];arrays={};forced=[];verify_shapes=[]
    for c in plan['cases']:
        p=root/(c['name']+'.json')
        if not p.exists():checks.append({'case':c['name'],'valid':False,'reason':'MISSING'});continue
        a=read(p);r=a['response'];out=r['tokens'];cap=c['body']['n_predict'];expected=[out[0]];good=r['request_reset'] and r['timings']['cache_n']==0 and not r['truncated'] and r['prompt']==c['body']['prompt'] and len(out)==r['tokens_predicted'] and (len(out)==cap or r['stop_type']=='eos') and not any(i in eog for i in out[:-1]) and ((out[-1] in eog)==(r['stop_type']=='eos'))
        for b in r['blocks']:
            good&=b['actual_queries']==32 and len(b['verification_predictions'])==32 and 0<=len(b['proposal'])<=31 and b['pending_in']==expected[-1] and b['retained_kv_owner']=='verifier' and b['copy_roundtrip_equal']
            accepted=0;mismatch=False;terminal=False;keep=1
            for j,tok in enumerate(b['proposal']):
                chosen=b['verification_predictions'][j];expected.append(chosen);keep=j+1
                if chosen!=tok:mismatch=True;break
                accepted+=1
                if chosen in eog or len(expected)==cap:terminal=True;break
            if not mismatch and not terminal:
                keep=1+len(b['proposal'])
                if len(expected)<cap and expected[-1] not in eog:expected.append(b['verification_predictions'][len(b['proposal'])])
            good&=accepted==b['accepted_proposals'] and mismatch==b['mismatch'] and keep==b['kv_kept_queries']
        good&=expected==out and len(r['blocks'])==r['verify_decode_calls']
        shapes=[g for g in r['graph_observations'] if g['stage']=='verify' and g['name']=='attn_norm-0'];verify_shapes.extend(shapes);good&=len(shapes)==len(r['blocks']) and all(g['ne'][1]==32 for g in shapes)
        if c['kind']=='synthetic_rollback':forced.append({'case':c['name'],'first_block_mismatch':bool(r['blocks']) and r['blocks'][0]['mismatch'],'accepted_first':r['blocks'][0]['accepted_proposals'] if r['blocks'] else None,'injected_index':c['body']['fixture_bad_proposal_at']})
        arrays[c['name']]=out;checks.append({'case':c['name'],'valid':bool(good),'length':len(out),'endpoint':r['stop_type'],'verify_calls':len(r['blocks'])})
        if c['kind']=='synthetic_verified_eog_decision':
            index=c['body']['fixture_verified_eog_at'];checks[-1]['valid'] &= len(out)==index+2 and r['stop_type']=='eos' and len(r['blocks'])==1 and r['blocks'][0]['synthetic_verified_eog_at']==index and len(r['blocks'][0]['native_verification_predictions'])==32
    padding=[]
    for cap in [2,5,12]:
        values=[arrays.get(f'padding-cap{cap}-dummy{d}-r{rep}') for d in [32,33] for rep in [1,2]];padding.append({'cap':cap,'equal':values[0] is not None and all(v==values[0] for v in values)})
    statefiles={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'state-proof').glob('*.state')};state_equal=len(statefiles)==4 and len({statefiles.get(n) for n in ['verifier_prefix.state','verifier_after_copy.state','fast_loaded_prefix.state']})==1
    repeated=[{'case_prefix':name[:-3],'equal':arrays[name]==arrays.get(name[:-3]+'-r2')} for name in arrays if name.endswith('-r1')]
    passed=len(checks)==len(plan['cases']) and all(c['valid'] for c in checks) and all(p['equal'] for p in padding) and all(f['first_block_mismatch'] and f['accepted_first']==f['injected_index'] for f in forced) and bool(verify_shapes) and state_equal and all(r['equal'] for r in repeated)
    result={'status':'PASS' if passed else 'IMPLEMENTATION_BLOCKED','model':model,'requests':len(checks),'planned':len(plan['cases']),'checks':checks,'repeat_checks':repeated,'padding':padding,'forced_rollback':forced,'actual_verify_query_range':[min(g['ne'][1] for g in verify_shapes),max(g['ne'][1] for g in verify_shapes)] if verify_shapes else None,'state_files_sha256':statefiles,'prefix_state_copy_source_unchanged_and_exact':state_equal,'ordinary_reference_gate':'DEFERRED_TO_PAID_CONFIRMATION; repeat stability alone is not R equality','pending_eog_fixture':'explicitly synthetic forced pending runtime EOG; no fabricated ordinary model decision'}
    save(PUB/('E_ENGINEERING_'+model+'.json'),result);return passed
if __name__=='__main__':
    import sys
    mode=sys.argv[1];r={'bridge':native_bridge,'family_graph':family_graph,'discovery':discovery}.get(mode,lambda:dvr(mode))();print(r if isinstance(r,bool) else {k:r[k] for k in ['status','requests','native_N0_qualified','fixed_C3_qualified','selected_mask_output_only']},flush=True)
    if r is False:raise SystemExit(1)
