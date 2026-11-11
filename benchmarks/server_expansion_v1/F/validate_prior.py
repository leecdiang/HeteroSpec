"""Preserve completed Llama comparisons; add genuine EOG without native replay.

Existing proofs are admitted only after native bindings and their exact vector/
state operands are rehashed at the same reconstructed logical prefixes. The
original checker/reader sources and state profile remain pinned.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse, copy, fcntl, inspect, json, shutil, sys, textwrap
import integrate as d

def main():
    p=argparse.ArgumentParser()
    for key in ('work','baseline','runtime','builds','repo','audit'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-commit',required=True);p.add_argument('--validate-retained-only',action='store_true');a=p.parse_args()
    if not a.validate_retained_only:raise ValueError("This entrypoint permits only zero-forward retained-proof audit")
    for key,value in vars(a).items():
        if isinstance(value,Path):setattr(a,key,value.resolve())
    d.load(a.runtime);need,read,save,sha=d.need,d.read,d.save,d.sha
    old=a.work/'qualification-01';out=a.work/('qualification-retained-audit-03' if a.validate_retained_only else 'qualification-complete-02');source=Path(__file__).parent
    need(not a.audit.exists() and not out.exists(),'Fresh explicit EOG completion epoch');a.audit.mkdir(parents=True)
    failed=read(a.work.parent/'f-study-audit-01/STATUS.json');need(failed['status']=='FAILED_RETAINED' and failed['last_phase']=='qualify','Preserve original stopped pipeline')
    need(sha(a.work/'termination-fixture-01/FIXTURE.json')==sha(source/'EOG_FIXTURE_V1.json'),'Published fixed termination diagnostic')
    frozen={str(x):sha(x) for x in source.rglob('*') if x.is_file() and x.suffix in ('.py','.cpp','.hpp','.json')}
    save(a.audit/'SOURCE_FREEZE.private.json',dict(source_commit=a.source_commit,files=frozen,original_failed_status_sha256=sha(a.work.parent/'f-study-audit-01/STATUS.json'),
        independent_R_sha256=sha(a.work/'reference-01/REFERENCE_FREEZE.json'),fixture_sha256=sha(source/'EOG_FIXTURE_V1.json'),
        native_binaries_changed=False,reference_replaced=False,formal_performance='NOT_RUN'))
    if a.validate_retained_only:
        for root in (a.work,a.work.parent/'d14-run-01'):
            need(not (root/'panel-01/CONFIRMATION_FREEZE.json').exists(),'Offline revalidation must finish before any formal window')
    else:
        lock=(a.work.parent/'STUDY_SCHEDULING.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
    try:
        for name,h in frozen.items():need(sha(name)==h,'Completion source changed while waiting')
        original_freeze=read(a.work.parent/'f-study-audit-01/SOURCE_FREEZE.private.json')
        for name,h in original_freeze['files'].items():need(sha(name)==h,'Original running/checker source changed')
        pin=read(source/'PREDECESSOR_PIN.json')
        for name,h in pin['files'].items():
            if name.startswith('benchmarks/linux_transfer_v1/'):
                if Path(name).name in ('host.py','pins.json'):continue # Explicit family/budget-only supervisor port.
                path=a.runtime/Path(name).name
            else:path=a.repo/name
            need(sha(path)==h,'Pinned original checker/reader changed: '+name)
        need(sha(a.runtime/'host.py')==read(a.runtime/'LLAMA_F_PORT.json')['host_sha256'],'Versioned supervisor changed')
        cfg=read(a.work/'config-reference-frozen-01.json');rf=a.work/'reference-01/REFERENCE_FREEZE.json'
        need(sha(rf)==cfg['reference_freeze_sha256'] and read(rf)['status']=='REFERENCE_FROZEN','Original independent Llama reference remains frozen')
        need(read(rf)['build']['sha256']==sha(a.builds/'reference/BUILD.json'),'Original R executable binding')
        original_bindings=read(source/'ORIGINAL_PROOF_BINDINGS.json')
        need(sha(rf)==original_bindings['reference_freeze_sha256'] and sha(old/'STATE_PROFILES.json')==original_bindings['state_profiles_sha256'],'Exact original R/profile bindings')
        for name,h in original_bindings['proofs'].items():need(sha(old/name)==h,'Original published byte proof changed')
        out.mkdir();models=read(a.work/'inputs-01/MODELS.json')[d.FAMILY];structures=read(a.work/'MODEL_STRUCTURES.json')
        profiles=read(old/'STATE_PROFILES.json');trace,parse=d.checks.legacy_readers(a.repo)
        cache={};bindings=[];modules={};references={}
        def hashed(path):
            path=Path(path).resolve()
            if path not in cache:cache[path]=sha(path)
            return cache[path]
        def verify_run(dest,job_path,core):
            job=read(job_path);build=a.builds/core/'BUILD.json';launch=read(dest/'launch.json')
            need(read(dest/'HOST.json')['status']=='COMPLETE' and launch['job_sha256']==hashed(job_path) and launch['build_sha256']==hashed(build),'Exact complete native worker only')
            b=read(build);need(hashed(b['executable'])==b['executable_sha256'],'Unchanged original executable')
            need(job['target_sha256']==models['target_sha256'] and read(dest/'native/CAPABILITY.json')==job['capability_request'],'Original native model/capability binding')
            if job.get('draft_model'):need(job['draft_sha256']==models['draft_sha256'],'Original exact draft model')
            actual=read(dest/'LOADED_MODULES.json')
            for name,row in actual.items():
                if row['kind']=='ELF_file':need(hashed(name)==row['sha256'],'Original actual module changed')
            modules.setdefault(core,dest/'LOADED_MODULES.json');need(read(modules[core])==actual,'Per-core actual module maps differ')
            bindings.append(dict(job_sha256=hashed(job_path),launch_sha256=hashed(dest/'launch.json'),native_result_sha256=hashed(dest/'native/result.json'),core=core,native_replayed=False))
            return job
        def add(prefix,path,kind):
            if path.exists():references.setdefault(tuple(prefix),{}).setdefault(kind,[]).append(path)
        events=[json.loads(x) for x in (a.work/'ledger.jsonl').read_text().splitlines()]
        for event in events:
            if event.get('event')!='RESERVE':continue
            dest=Path(event['out']);need(dest.is_relative_to(a.work),'Study-native reservation only')
            job_path=(a.work/'inputs-01' if dest.parent==a.work/'reference-01' else old/'jobs')/(dest.name+'.json')
            candidate=read(job_path);core=candidate['capability_request']['core'];job=verify_run(dest,job_path,core)
            if core!='reference':continue
            for case in job.get('cases',[]):
                tape=sum((x['ids'] for x in case['forced']),[])
                for n in case['observe_positions']:
                    base=dest/'native'/case['name']/'captures'/str(n);add(tape[:n],base/'frontier.f32','vector')
                    if n in case['state_positions']:add(tape[:n],base/'sequence.bin','state')
            for entry in job.get('inputs',[]):
                base=dest/'native'/entry['name'];rec=read(base/'receipt.json');prompt=entry['input']['prompt_ids']
                for k in range(len(rec['ids'])):
                    prefix=prompt+rec['ids'][:k];cap=base/'captures'/str(len(prefix));add(prefix,cap/'frontier.f32','vector');add(prefix,cap/'sequence.bin','state')
        def expected(prefix,kind,h):
            paths=references.get(tuple(prefix),{}).get(kind,[])
            need(any(hashed(p)==h for p in paths),'Exact original R operand missing at logical prefix')
        def vector(actual,prefix,proof):
            need(proof['equal'] and proof['actual_sha256']==proof['reference_sha256'] and hashed(actual)==proof['actual_sha256'],'Original full-vector operand changed')
            expected(prefix,'vector',proof['reference_sha256'])
        def state(actual,prefix,proof):
            need(proof['equal'] and hashed(actual)==proof['actual_raw_sha256'],'Original state operand changed')
            expected(prefix,'state',proof['reference_raw_sha256'])
        prior=[]
        for arm,(core,cut,draft) in d.ARMS.items():
            path=old/(d.FAMILY+'-natural-'+arm+'-CHECKED.json');proof=read(path);need(proof['passed'],'Original finite natural comparison must pass')
            run=old/'runs'/(d.FAMILY+'-natural-'+arm);meta=read(run/'native/result.json')
            roots=read(a.work/'inputs-01'/f'{d.FAMILY}-DEVELOPMENT.json')['inputs']
            need(roots==read(source/'HISTORICAL_DEVELOPMENT.json')['inputs'] and len(roots)==len(proof['roots'])==3,'All original retained natural inputs')
            for i,(root,row) in enumerate(zip(roots,proof['roots'])):
                base=run/'native'/f'dev-{i}-heavy';clean=run/'native'/f'dev-{i}-clean';rec=read(base/'receipt.json');cr=read(clean/'receipt.json')
                need(hashed(base/'receipt.json')==row['heavy_receipt_sha256'] and hashed(clean/'receipt.json')==row['clean_receipt_sha256'],'Original request receipt changed')
                need(row['root']==root['id'] and row['terminal_kind']=='CAP' and all(v==0 for v in cr['observed_API_calls_within_service'].values()),'Original root/termination/clean-service binding')
                rec['study_cap']=cr['study_cap']=root['cap'];_,t=trace(rec,root['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx');_,tc=trace(cr,root['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
                need(t==tc,'Original heavy/clean transaction changed');d.native.Study.physical(rec,root,draft);d.native.Study.physical(cr,root,draft)
                need(len(t['vector_uses'])==len(row['vectors']) and len(t['states'])==len(row['states']),'Original proof coverage changed')
                for use,pair in zip(t['vector_uses'],row['vectors']):
                    key=use['key'];name='initial' if key=='initial' else ('verify-'+key[4:].replace('/','-') if draft else 'ordinary-'+str(int(key[4:].split('/')[0])+1))
                    need(key==pair['key'] and len(use['prefix'])==pair['prefix_tokens'],'Original requested-vector mapping');vector(base/'target'/(name+'.f32'),use['prefix'],pair)
                for logical,saved in zip(t['states'],row['states']):
                    capture=base/'target/state'/saved['key'];state(capture/'sequence.bin',logical['prefix'],saved['active_KV']);vector(capture/'frontier.f32',logical['prefix'],saved['frontier'])
                last=t['states'][-1]['prefix'];state(base/'target/state/terminal/sequence.bin',last,row['terminal_active_KV']);vector(base/'target/state/terminal/frontier.f32',last,row['terminal_frontier'])
            cap=run/'native/cap1-heavy/target';prefix=roots[0]['prompt_ids'];vector(cap/'initial.f32',prefix,proof['cap1']['full_vector']);state(cap/'state/terminal/sequence.bin',prefix,proof['cap1']['active_state'])
            prior.append(path)
            if not draft:
                path=old/(d.FAMILY+'-matrix-'+arm+'-CHECKED.json');m=read(path);need(m['passed'],'Original geometry comparison must pass');locations={}
                for i,g in enumerate(m['groups']):
                    actual=old/'runs'/(d.FAMILY+'-matrix-'+arm+f'-group{i}');need(hashed(actual/'native/result.json')==g['actual_native_result_sha256'],'Original matrix metadata changed');locations.update({c:actual for c in g['cases']})
                cases={x['name']:x for x in read(a.work/'inputs-01'/f'{d.FAMILY}-GEOMETRY.json')['cases']}
                need(set(locations)==set(cases) and len(cases)==12,'All12 original geometry cases')
                for row in m['rows']:
                    tape=sum((x['ids'] for x in cases[row['case']]['forced']),[]);prefix=tape[:row['position']];actual=locations[row['case']]/'native'/row['case']/'captures'/str(row['position'])
                    vector(actual/'frontier.f32',prefix,row['vector'])
                    if 'active_KV' in row:state(actual/'sequence.bin',prefix,row['active_KV'])
                prior.append(path)
        need(len(prior)==10,'Preserve every original natural/geometry control')
        for path in prior:shutil.copy2(path,out/path.name)
        save(out/'ORIGINAL_PROOFS_REVALIDATED.json',dict(passed=True,source_checker_commit='d258870b69f91f8ad61b4bed5dbf00235212d057',
            native_launches=bindings,consumed_files_rehashed=len(cache),original_native_requests_replayed=0,independent_R_replaced=False,
            state_profile_sha256=sha(old/'STATE_PROFILES.json'),proofs=[dict(path=p.name,sha256=sha(p)) for p in prior],
            scope='Existing complete byte comparisons remain valid after exact operand, logical-prefix, receipt, source and module revalidation; no relaxed comparison or new parser'))
        print('ALL_TEN_ORIGINAL_LLAMA_PROOFS_REVALIDATED',flush=True)
        if a.validate_retained_only:
            save(a.audit/'STATUS.json',dict(status='RETAINED_PROOFS_REVALIDATED_ZERO_NEW_NATIVE_WORK',new_model_forwards=0,
                consumed_files_rehashed=len(cache),native_qualification='NOT_GRANTED_BY_THIS_AUDIT',formal_performance='NOT_RUN'))
            return

    except BaseException as e:
        save(a.audit/'STATUS.json',dict(status='FAILED_RETAINED',error=str(e),formal_performance='NOT_RUN'));raise

if __name__=='__main__':main()
