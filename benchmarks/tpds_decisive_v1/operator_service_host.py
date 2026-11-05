"""C1536 original-reference and full-state natural-service qualification."""
from native_adapter import *
from build_operator_driver import ORIG,FROZEN
from qualify_host import blob,QUAL
from common import digest,write_new
from normalize import trace_from_row,normalize
from active_kv import parse
from qualify import qualify
from archive_host import archive_paths
import hashlib
ARMS=('graph_tiles','backend_loop4','packed')
def job(label,arm,input,names=('heavy','warmup','off')):
    if arm=='old':
        exe=FROZEN.parent/'oracle01/service.exe';prior=json.loads((FROZEN.parent/'formal01/freeze.json').read_bytes());assert sha(exe)==prior['inputs'][str(exe)];build=dict(exe=sha(exe),modules=prior['numerical_modules'])
    else:
        root=Path('D:/rtx184-operator')/(arm+'-service-v3');exe=root/'bin/service.exe';build=json.loads((root/'BUILD.json').read_bytes())
    manifest=dict(ctx=1536,width=32,layers=999,blocks=[dict(arm='R' if arm in ('old','original') else 'QB-local',study_arm=arm,slots=[dict(id=n,capture=n.startswith('heavy'),input=input) for n in names])])
    return dict(attempt_id=label,exe=str(exe),build_manifest=build,operator_service=manifest,reservation=dict(requests=len(names),token_rows=8000*len(names),operators=0))
def clean_check(native,case,bank,names):
    c=json.loads((case/'capture.json').read_bytes());last=c['states'][-1];refs=json.loads((bank/'capture.json').read_bytes());ref=next(x for x in refs['prefixes'] if x['prefix']==last['prefix']);profile=json.loads((ROOT/'O-profile-8B/PROFILE.json').read_bytes());rows=[]
    for name in names:
        p=native/name/'target/state/final-clean';r=json.loads((native/name/'receipt.json').read_bytes());assert r['ids']==__import__('trace').reconstruct(c['trace'])['tokens']
        can,_=parse((p/'sequence.bin').read_bytes(),list(range(len(last['prefix']))),profile);assert hashlib.sha256(can).hexdigest()==ref['active_kv']['sha256'] and sha(p/'frontier.f32')==ref['frontier']['sha256']
        rows.append(dict(slot=name,active_kv_equal=True,frontier_equal=True,endpoint_equal=True,service_s=r['service_seconds']))
    return rows
def main():
    os.environ['TPDS_EVIDENCE_CAS']='D:/rtx184-cas';inputs=json.loads((OLD.parent/'admission-Qwen-v4/PANEL.json').read_bytes())['inputs'][:4];allproof=[]
    for ix,input in enumerate(inputs):
        case=QUAL/('O-root'+str(ix));case.mkdir();runs=[]
        old=execute(job('O-old-root'+str(ix),'old',input,('heavy0','heavy1')));runs.append(old)
        obs=execute(job('O-observer-root'+str(ix),'original',input,('heavy0','heavy1')));runs.append(obs)
        vectors=[{p.name:sha(p) for p in (base/'native'/name/'target').glob('*.f32')} for base in (old,obs) for name in ('heavy0','heavy1')]
        endpoints=[json.loads((base/'native'/name/'receipt.json').read_bytes())['endpoint'] for base in (old,obs) for name in ('heavy0','heavy1')]
        assert vectors[0] and all(x==vectors[0] for x in vectors) and all(x==endpoints[0] for x in endpoints)
        put(case/'OLD_OBSERVER_BRIDGE.json',dict(full_vectors_equal=True,endpoints_equal=True,vector_count=len(vectors[0]),old_exe=sha(FROZEN.parent/'oracle01/service.exe'),observer_exe=sha(Path('D:/rtx184-operator/original-service-v3/bin/service.exe'))))
        profile=json.loads((ROOT/'O-profile-8B/PROFILE.json').read_bytes());prompt=input['prompt_ids'];eog=[128247,151643,151645,151662,151663,151664];producer=dict(caller_lengths=[len(prompt)],last_output_flags=[True])
        binding=dict(reference_identity_sha256=sha(FROZEN.parent/'oracle01/service.exe'),target_model_sha256=profile['target_model_sha256'],producer_sha256=digest(producer),lifecycle_sha256=digest(dict(original='PR171',capacity=1536,width=32,priming='sequential version worker, same-arm warmup then resident-reset')),input_sha256=digest(prompt),cap=128,vocab=151936,eog_ids=eog,active_kv_bytes_per_token=147456,reference_bridge_passed=True)
        for name,value in [('binding',binding),('profile',profile),('prompt',dict(prompt_ids=prompt))]:write_new(case/(name+'.json'),value)
        derived=[];normalized={}
        for arm in ('free',*ARMS):
            if arm=='free':base=obs/'native/heavy0';role='free_reference'
            else:
                out=execute(job('O-development-'+arm+'-root'+str(ix),arm,input));runs.append(out);base=out/'native/heavy';role='candidate'
            row=json.loads((base/'receipt.json').read_bytes());row.update(study_cap=128,study_fallback_count=0,study_reference_received_forced_tape=False);write_new(case/(arm+'-row.json'),row)
            derived.append(trace_from_row(row,prompt,151936,eog,'rtx')[1]);normalize('rtx',case/(arm+'-row.json'),base/'target',case/'prompt.json',case/'binding.json',case/'profile.json',role,'O-'+arm+'-root'+str(ix),case/arm);normalized[arm]=case/arm
        assert all(d['tokens']==derived[0]['tokens'] for d in derived)
        prefixes={tuple(x['prefix']) for d in derived for key in ('states','vector_uses') for x in d[key]};maximal=[]
        for p in sorted(prefixes,key=lambda p:(-len(p),p)):
            if not any(q[:len(p)]==p for q in maximal):maximal.append(p)
        assigned=set();paths=[]
        for p in maximal:
            positions=sorted(set([n for n in range(len(prompt),len(p)+1) if p[:n] in prefixes and p[:n] not in assigned]+[len(prompt)]));assigned.update(p[:n] for n in positions);paths.append(dict(suffix=list(p[len(prompt):]),positions=positions))
        assert assigned==prefixes
        replay=job('O-forced-root'+str(ix),'original',input);replay['operator_service'].pop('blocks');replay['operator_service']['forced']=dict(no_candidate_payload=True,prompt_ids=prompt,producer=producer,paths=paths);replay['reservation']=dict(requests=len(paths),token_rows=sum(len(prompt)+len(p['suffix']) for p in paths),operators=0)
        out=execute(replay);runs.append(out);result=json.loads((out/'native/result.json').read_bytes());bank=case/'bank';bank.mkdir();entries={};duplicates=0
        for path in result['paths']:
            full=prompt+path['suffix']
            for cap in path['captures']:
                count=cap['position'];p=out/'native'/cap['directory'];can,scope=parse((p/'sequence.bin').read_bytes(),list(range(count)),profile);entry=dict(prefix=full[:count],active_layout_sha256=scope['active_layout_sha256'],frontier=blob(bank,(p/'frontier.f32').read_bytes()),active_kv=blob(bank,can));key=digest(entry['prefix'])
                if key in entries:assert entries[key]==entry;duplicates+=1
                entries[key]=entry
        write_new(bank/'capture.json',dict(role='forced_reference',execution='NATIVE',completed=True,binding={k:v for k,v in binding.items() if k not in ('eog_ids','reference_bridge_passed')},reference_bridge_passed=True,fallback_count=0,invocation_id='O-forced-root'+str(ix),prefixes=list(entries.values())))
        for arm in ARMS:
            proof=qualify(normalized[arm]/'capture.json',normalized['free']/'capture.json',bank/'capture.json');proof['heavy_off']=clean_check(RUNS/('O-development-'+arm+'-root'+str(ix))/'native',normalized[arm],bank,('warmup','off'))
            prime=execute(job('O-priming-'+arm+'-root'+str(ix),arm,input,('warmup','measure')));runs.append(prime);proof['priming']=clean_check(prime/'native',normalized[arm],bank,('warmup','measure'));proof['stable_duplicate_prefixes']=duplicates;write_new(case/(arm+'-QUALIFICATION.json'),proof);allproof.append(dict(root=ix,arm=arm,proof=proof));print('C1536 service qualified',ix,arm,flush=True)
        archive_paths('O-root'+str(ix),runs+[p/'cas' for p in normalized.values()]+[bank/'cas'])
    put(ROOT/'O-SERVICE-QUALIFICATION.json',dict(status='FINITE_NATIVE_CAPTURE_MATCH',proofs=allproof,roots=4,arms=list(ARMS),same_version=True))
if __name__=='__main__':main()
