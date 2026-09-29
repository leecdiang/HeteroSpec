"""Hardware-free independent recomputation. Does not import the study runner."""
import argparse, gzip, hashlib, json, re, subprocess
from datetime import datetime
from pathlib import Path

START='31e756f3311cee4226bd1be57ee6febadd032aa4'
DISCOVERY={'HumanEval/'+str(n) for n in (89,101,104,162,3,10,68,70,19,20,28,32)}
PREFIX='heterospec-b570-mechanism-v08-reserved|'

def digest(path):return hashlib.file_digest(Path(path).open('rb'),'sha256').hexdigest()
def array_digest(seq):return hashlib.sha256(json.dumps(seq,separators=(',',':')).encode('ascii')).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def ancestor(root,older,newer):
    proof=root/'provenance/git_checkpoints.json'
    if proof.exists():
        commits=load(proof)['commits'];seen=set();pending=[newer]
        while pending:
            item=pending.pop()
            if item==older:return True
            if item in seen:continue
            seen.add(item);pending.extend(commits.get(item,{}).get('parents',[]))
        return False
    return subprocess.run(['git','merge-base','--is-ancestor',older,newer],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def checkpoint_bytes(root,commit,path):
    proof=root/'provenance/git_checkpoints.json'
    if proof.exists():
        record=load(proof)['commits'][commit]['files'][path]
        return (root/'provenance/git_objects'/record['blob']).read_bytes()
    return subprocess.check_output(['git','show',commit+':'+path],cwd=root)
def temporal_audit(freeze_time,prediction_created,predictor_runs,outcome_runs,frozen_digest,current_digest):
    """Reject leaked or changed predictions, independently of sequence agreement."""
    errors=[]
    parse=lambda s:datetime.fromisoformat(s.replace('Z','+00:00'))
    if predictor_runs and any(parse(freeze_time)>=parse(r['start_utc']) for r in predictor_runs):errors.append('reserved inference before hypothesis freeze')
    if outcome_runs:
        first=min(parse(r['start_utc']) for r in outcome_runs)
        if not predictor_runs or max(parse(r['end_utc']) for r in predictor_runs)>=first:errors.append('predictor execution after actual outcome started')
        if parse(prediction_created)>=first:errors.append('prediction generated after actual outcome')
        if frozen_digest!=current_digest:errors.append('prediction bytes changed after outcome start')
    return errors
def divergence(reference,candidate):
    different=[k for k in range(max(len(reference),len(candidate))) if k>=len(reference) or k>=len(candidate) or reference[k]!=candidate[k]]
    k=different[0] if different else None
    return {'exact':not different,'first_divergence_index':k,'reference_token':reference[k] if k is not None and k<len(reference) else None,'candidate_token':candidate[k] if k is not None and k<len(candidate) else None,'reference_length':len(reference),'candidate_length':len(candidate)}

def verify(root):
    root=Path(root);p=root/'benchmarks/b570_mechanism_v08';raw=root/'artifacts/b570_mechanism_v08/raw'
    failures=[];checks=[]
    def require(ok,message):
        (checks if ok else failures).append(message)
    inventory=load(p/'exposure_inventory.json');reserved=load(p/'RESERVED_VALIDATION_SET.json');plan=load(p/'discovery_protocol.json');build=load(p/'build_manifest.json')
    require(inventory['starting_main']==START==plan['starting_main'],'exact starting main')
    require(not inventory['errors'],'exposure scope has no recorded audit errors')
    with gzip.open(root/'datasets/humaneval/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:dataset={r['task_id']:r for r in map(json.loads,f)}
    require(digest(root/'datasets/humaneval/HumanEval.jsonl.gz')==inventory['dataset_sha256']==reserved['dataset_sha256'],'included dataset bytes match inventory and reserved selection')
    exposed=set()
    for e in inventory['evidence']:exposed.update(e['task_ids'])
    eligible=set(dataset)-exposed
    require(eligible==set(reserved['eligible_pool']),'eligible pool independently recomputed from exposure records')
    selected=sorted(eligible,key=lambda t:hashlib.sha256((PREFIX+t).encode()).hexdigest())[:24]
    require(len(selected)==24 and selected==reserved['selected_task_ids'],'exact 24 deterministic reserved tasks')
    require(all(inventory['tasks'][t]['status']=='NO_KNOWN_B570_EXPOSURE' for t in selected),'reserved tasks have no recorded prior B570 exposure')
    require(set(plan['tasks'])==DISCOVERY and len(plan['tasks'])==12,'exact frozen 12-task discovery set')
    require(not DISCOVERY & set(selected),'discovery and reserved sets disjoint')
    v1=load(root/'benchmarks/b570_direct_id_v1/protocol_v1.json')
    require(digest(root/'scripts/platform/b570_mechanism_v08/harness.cpp')==build['harness_source_sha256'],'included harness source bytes')
    runtime=root/'runtime'
    if runtime.exists():
        for name,h in build['binary_hashes'].items():require(digest(runtime/name)==h,'included runtime binary bytes: '+name)
        if (runtime/'serialized').exists():
            for name,h in v1['binary_hashes'].items():require(digest(runtime/'serialized'/name)==h,'included historical serialized runtime bytes: '+name)
    for asset,section in [('models/gguf/Qwen3-8B-Q8_0.gguf','target'),('models/gguf/Qwen3-0.6B-Q8_0.gguf','draft'),('datasets/humaneval/HumanEval.jsonl.gz','dataset')]:
        require(build['assets'].get(asset,build['assets'].get(asset.replace('/','\\')))==v1[section]['sha256'],'asset recorded identity: '+section)
    historical=root/'provenance/historical_executions.json'
    if not historical.exists():historical=root/'work/b570_direct_id_v1/formal-v1-20260929-local/executions.json'
    require(digest(historical)==build['historical_executions_sha256'],'historical direct-ID evidence bytes')
    old=load(historical)['executions'];old_by={(r['task_id'],r['repetition'],r['condition']):r for r in old}
    all_rows=[];recomputed={}
    for stage in ['qualification','discovery_h1','discovery_h2','reserved_predictions','reserved_outcomes']:
        location=raw/stage/'executions.json'
        if not location.exists():continue
        rows=load(location)['executions'];all_rows.extend(rows)
        require(len({(r['task_id'],r['repetition'],r.get('condition',r.get('n_ubatch'))) for r in rows})==len(rows),'no duplicate observations: '+stage)
        for row in rows:
            label=stage+' '+row['task_id']+' r'+str(row['repetition'])
            if stage.startswith('discovery'):require(row['task_id'] in DISCOVERY and row['task_id'] not in selected,'no reserved discovery execution: '+label)
            if stage=='qualification':require(row['task_id'] in v1['task_ids'] and row['task_id'] not in selected,'qualification uses historical exposed task: '+label)
            require(row['start_utc']<=row['end_utc'],'operational temporal order: '+label)
            for kind in ['stdout','stderr','capture','sidecar']:
                if kind not in row:continue
                location=root/row[kind] if row[kind].startswith('artifacts/') else raw/stage/row[kind]
                require(digest(location)==row[kind+'_sha256'],'included '+kind+' bytes: '+label)
            if stage=='reserved_outcomes':
                sidecar=load(raw/stage/row['sidecar']);ids=sidecar['ids'];flags=sidecar['eog']
                end=min(128,next((i+1 for i,f in enumerate(flags) if f),len(ids)))
                actual=ids[:end]
                require(actual==row['generated_ids'] and array_digest(actual)==row['generated_ids_sha256'],'actual direct committed IDs and inclusive endpoint: '+label)
                require(array_digest(ids)==row['raw_ids_sha256'],'raw overshoot IDs hash: '+label)
                text=(raw/stage/row['stderr']).read_text(encoding='utf-8',errors='replace')
                off=re.findall(r'offloaded\s+(\d+)/(\d+) layers to GPU',text)
                place=[line for line in text.splitlines() if 'using device ' in line]
                require(off==[('37','37'),('29','29')] and len(place)==2 and all('using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' in line for line in place),'actual target 37/37 and draft 29/29 on B570 Vulkan0: '+label)
                require(row['command'][row['command'].index('--ubatch-size')+1]=='1' and row['command'][row['command'].index('--spec-draft-n-max')+1]=='2','actual serialized UB1 k2: '+label)
                continue
            if row['exit_code']!=0 or 'capture' not in row:
                require(row['execution_valid']==False,'failed observation classified invalid: '+label);continue
            data=load(root/row['capture']);ids=data['generated_ids']
            require(ids==row['generated_ids'] and array_digest(ids)==row['generated_ids_sha256'],'complete token-array hash: '+label)
            require(array_digest(data['prompt_ids'])==row['prompt_ids_sha256'],'direct prompt-ID hash: '+label)
            require(len(data['eog'])==len(ids) and len(ids)>0 and len(ids)<=128 and (len(ids)==128 or data['eog'][-1]) and not any(data['eog'][:-1]),'inclusive EOG / 128-ID endpoint: '+label)
            require(len(data['decisions'])==len(ids) and all(d['committed_id']==ids[i] and d['output_index']==i for i,d in enumerate(data['decisions'])),'committed decisions correspond to array: '+label)
            require(data['context']['n_ctx']==1024 and data['context']['n_batch']==512 and data['context']['n_ubatch']==row['n_ubatch'],'context partition: '+label)
            if stage=='qualification':require(row['n_ubatch']==128,'qualification reference UB128: '+label)
            if stage=='discovery_h1':require(row['n_ubatch']==1,'H1 target-only UB1: '+label)
            stderr=(root/row['stderr']).read_text(encoding='utf-8',errors='replace')
            placements=[line for line in stderr.splitlines() if 'using device ' in line]
            offloads=re.findall(r'offloaded\s+(\d+)/(\d+) layers to GPU',stderr)
            require(placements and all('using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' in line for line in placements),'B570 Vulkan0 placement: '+label)
            require(offloads==[('37','37')],'37/37 target offload: '+label)
            require(row['command'][row['command'].index('--seed')+1]=='123' and row['command'][row['command'].index('--flash-attn')+1]=='off','frozen seed/FA command: '+label)
            if stage=='qualification':
                ref=old_by[(row['task_id'],row['repetition'],'TARGET_REFERENCE')]['generated_ids']
                recomputed[(row['task_id'],row['repetition'])]=divergence(ref,ids)
    q=load(p/'HARNESS_QUALIFICATION.json')
    for pair in q['pairs']:
        actual=recomputed.get((pair['task_id'],pair['repetition']))
        if actual is not None:require(all(pair[k]==v for k,v in actual.items()),'independent qualification divergence recomputation')
    exact=sum(r['exact'] and next(x['execution_valid'] for x in all_rows if x['stage']=='qualification' and x['task_id']==t and x['repetition']==n) for (t,n),r in recomputed.items())
    require(q['exact_pairs']==exact,'qualification exact count')
    if q['status']=='HARNESS_NOT_QUALIFIED':
        require(len([r for r in all_rows if r['stage']!='qualification'])==0,'qualification failure stopped all discovery and reserved executions')
        require(q['executions']==len(q['pairs']) and q['executions']<90 or exact<90,'negative harness classification')
        require(exact<q['executions'] or any(not r['execution_valid'] for r in all_rows),'qualification has a concrete failed observation')
    elif q['status']=='PASS':
        require(q['executions']==90 and exact==90,'qualification 90/90 exact coverage')
        require({(r['task_id'],r['repetition']) for r in all_rows if r['stage']=='qualification'}=={(t,n) for t in v1['task_ids'] for n in (1,2,3)},'all 30 historical tasks × 3 repeats')
    else:require(False,'study qualification not closed')
    # A stopped study must never manufacture prediction or outcome data.
    if q['status']=='HARNESS_NOT_QUALIFIED':
        for filename in ['DISCOVERY_ANALYSIS.json','hypothesis_freeze.json','RESERVED_PREDICTIONS.json','VALIDATION_ANALYSIS.json']:
            if (p/filename).exists():require(load(p/filename).get('executed',True)==False,'unreached phase explicitly unexecuted: '+filename)
    if (p/'DISCOVERY_ANALYSIS.json').exists() and load(p/'DISCOVERY_ANALYSIS.json').get('executed',True):
        discovery=load(p/'DISCOVERY_ANALYSIS.json');h1=[r for r in all_rows if r['stage']=='discovery_h1']
        require({(r['task_id'],r['repetition']) for r in h1}=={(t,n) for t in DISCOVERY for n in (1,2,3)} and len(h1)==36,'exact 36 H1 discovery executions')
        h1_exact=0
        for row in h1:
            ser=old_by[(row['task_id'],row['repetition'],'B570_SERIALIZED_K2')]['generated_ids']
            h1_exact+=row['generated_ids']==ser
            pair=next(r for r in discovery['pairs'] if r['task_id']==row['task_id'] and r['repetition']==row['repetition'])
            require(all(pair[k]==v for k,v in divergence(ser,row['generated_ids']).items()),'independent H1 predictor-to-serialized comparison')
            ref=old_by[(row['task_id'],row['repetition'],'TARGET_REFERENCE')]['generated_ids']
            require(pair['relative_to_reference']==divergence(ref,row['generated_ids']),'independent H1 first divergence relative to reference')
        require(discovery['H1_exact_pairs']==h1_exact,'H1 agreement count recomputed')
        if discovery['status']=='H1_SELECTED':
            require(h1_exact==36,'H1 selected only at 36/36')
            require(not any(r['stage']=='discovery_h2' for r in all_rows),'H2 not constructed after H1 succeeds')
    if (p/'RESERVED_PREDICTIONS.json').exists() and load(p/'RESERVED_PREDICTIONS.json').get('executed',True):
        predictions=load(p/'RESERVED_PREDICTIONS.json');freeze=load(p/'hypothesis_freeze.json');prediction_rows=[r for r in all_rows if r['stage']=='reserved_predictions'];outcomes=[r for r in all_rows if r['stage']=='reserved_outcomes']
        freeze_commit=predictions['hypothesis_freeze_commit']
        freeze_path='benchmarks/b570_mechanism_v08/hypothesis_freeze.json'
        require(checkpoint_bytes(root,freeze_commit,freeze_path)==(p/'hypothesis_freeze.json').read_bytes(),'hypothesis freeze committed bytes')
        require(len(prediction_rows)==144 and {(r['task_id'],r['repetition'],r['n_ubatch']) for r in prediction_rows}=={(t,n,u) for t in selected for n in (1,2,3) for u in (1,128)},'exact 144 reference/predictor executions')
        require(all(freeze['created_utc']<r['start_utc'] and ancestor(root,freeze_commit,r['study_head']) for r in prediction_rows),'hypothesis freeze precedes every reserved inference')
        require(len(predictions['predictions'])==72 and {(r['task_id'],r['repetition']) for r in predictions['predictions']}=={(t,n) for t in selected for n in (1,2,3)},'exact 72 reserved predictions')
        require(all(len({r['generated_ids_sha256'] for r in prediction_rows if r['task_id']==t and r['n_ubatch']==u})==1 for t in selected for u in (1,128)),'within-condition repeat stability')
        for path,h in freeze['predictor_files'].items():require(digest(root/path)==h,'frozen predictor source bytes: '+path)
        for item in predictions['predictions']:
            t,n=item['task_id'],item['repetition']
            ref=next(r['generated_ids'] for r in prediction_rows if r['task_id']==t and r['repetition']==n and r['n_ubatch']==128)
            pred=next(r['generated_ids'] for r in prediction_rows if r['task_id']==t and r['repetition']==n and r['n_ubatch']==1)
            require(item['reference_ids']==ref and item['predicted_ids']==pred and array_digest(ref)==item['reference_ids_sha256'] and array_digest(pred)==item['predicted_ids_sha256'],'prediction derives from pre-outcome direct IDs')
            require(item['relative_to_reference']==divergence(ref,pred),'prediction first divergence recomputation')
        if outcomes:
            checkpoint=load(raw/'reserved_outcomes/checkpoint.json');prediction_commit=checkpoint['prediction_commit']
            prediction_path='benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json'
            require(not temporal_audit(freeze['created_utc'],predictions['created_utc'],prediction_rows,outcomes,checkpoint['prediction_sha256'],digest(p/'RESERVED_PREDICTIONS.json')),'independent temporal leakage/immutability audit')
            require(checkpoint_bytes(root,prediction_commit,prediction_path)==(p/'RESERVED_PREDICTIONS.json').read_bytes(),'prediction file bytes unchanged since committed freeze')
            require(digest(p/'RESERVED_PREDICTIONS.json')==checkpoint['prediction_sha256']==(p/'RESERVED_PREDICTIONS_SHA256.txt').read_text().split()[0],'prediction-file freeze SHA-256')
            require(len(outcomes)==72 and {(r['task_id'],r['repetition']) for r in outcomes}=={(t,n) for t in selected for n in (1,2,3)},'exact 72 live serialized outcomes')
            require(ancestor(root,freeze_commit,prediction_commit),'hypothesis commit precedes prediction commit')
            require(max(r['end_utc'] for r in prediction_rows)<min(r['start_utc'] for r in outcomes),'all predictions generated before any actual outcome; reject temporal leakage')
            require(predictions['created_utc']<min(r['start_utc'] for r in outcomes),'prediction file created before outcomes; reject post-outcome predictions')
            require(all(ancestor(root,prediction_commit,r['study_head']) and r['prediction_sha256']==checkpoint['prediction_sha256'] for r in outcomes),'prediction commit precedes each actual observation and digest unchanged')
            exact=0;classification={};first=0;nonexact=0
            report=load(p/'VALIDATION_ANALYSIS.json')
            for item in predictions['predictions']:
                t,n=item['task_id'],item['repetition'];actual=next(r['generated_ids'] for r in outcomes if r['task_id']==t and r['repetition']==n)
                primary=divergence(item['predicted_ids'],actual);observed=divergence(item['reference_ids'],actual);forecast=divergence(item['reference_ids'],item['predicted_ids'])
                exact+=primary['exact'];classification.setdefault(t,[]).append(observed['exact']==forecast['exact'])
                if not observed['exact']:nonexact+=1;first+=observed['first_divergence_index']==forecast['first_divergence_index']
                saved=next(r for r in report['pairs'] if r['task_id']==t and r['repetition']==n)
                require(saved['primary']==primary and saved['actual_relative_to_reference']==observed and saved['predicted_relative_to_reference']==forecast,'independent actual/predicted complete sequences and first divergences')
            require(report['exact_sequences']==exact and report['prompt_classification_matches']==sum(all(v) for v in classification.values()) and report['first_divergence_exact_pairs']==first and report['actual_mismatching_pairs']==nonexact,'all primary/secondary counts independently recomputed')
            require(report['status']==('MECHANISM_PREDICTION_VALIDATED' if exact==72 else 'MECHANISM_PREDICTION_NOT_FULLY_VALIDATED'),'strict all-72 classification')
    return {'schema':'heterospec.b570.mechanism.independent.v08','status':'PASS' if not failures else 'FAIL','checks_passed':len(checks),'checks':checks,'failures':failures,'scope':'Independent identity/selection, included bytes, direct sequences, placement, coverage, comparisons and applicable phase gating/temporal checks; unavailable model bytes are checked only by recorded identity. Reserved temporal checks are inapplicable when no reserved inference occurs.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=verify(args.root)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks_passed':result['checks_passed'],'failures':result['failures']}))
    raise SystemExit(0 if result['status']=='PASS' else 1)
