"""Resolve superseded zero-forward publication-index exclusions by actual source bytes."""
from common import *
import shutil

def transport_proof():
    canonical_path=OLD/'benchmarks/jsa_rtx_validation_v1/EXPOSURE_AUDIT.json'
    committed=subprocess.check_output(['git','show','92aeebe9bb422a754b1457e9e3572e7a57dd1d31:benchmarks/jsa_rtx_validation_v1/EXPOSURE_AUDIT.json'],cwd=OLD)
    assert hashlib.sha256(committed).hexdigest()==sha(canonical_path)
    canonical=json.loads(committed);assert canonical['status']=='PASS'
    eligible=set(canonical['eligible_ranked']);failed_path=OLDLOCAL/'EXPOSURE_SHORTPATH_ATTEMPT.json';failed=read(failed_path)
    assert failed['status']=='INPUT_POOL_BLOCKED' and failed['new_confirmation_forwards']==0 and failed['selected']==[]
    wrappers={};safe_ids=set()
    for row in failed['rows']:
        e=row.get('evidence')
        if row['id'] not in eligible or not isinstance(e,dict) or e['count']!=len(e['examples']) or not e['examples']:continue
        if not all('PUBLISH' in x['path'] and '!' not in x['path'] for x in e['examples']):continue
        for x in e['examples']:
            if x['sha256'] in wrappers:continue
            p=Path(x['path']);assert sha(p)==x['sha256'];a=read(p);tree=a.get('tree') if isinstance(a,dict) else a
            assert isinstance(tree,list) and tree and all(isinstance(r,dict) and r.get('type')=='blob' and isinstance(r.get('path'),str) and isinstance(r.get('content'),str) for r in tree)
            wrappers[x['sha256']]={'path':x['path'],'sha256':x['sha256'],'logical':{r['path']:hashlib.sha256(r['content'].encode()).hexdigest() for r in tree}}
        safe_ids.add(row['id'])
    return {'canonical_sha256':sha(canonical_path),'failed_index_sha256':sha(failed_path),'safe_IDs':safe_ids,'wrappers':wrappers}

def main():
    assert not (PUB/'CONFIRMATION_INPUTS.json').exists() and not list((LOCAL/'runs').rglob('REQUEST_STARTED.json'))
    original=read(PUB/'EXPOSURE_AUDIT.json');assert not original['errors']
    proof=transport_proof();catalog=read(LOCAL/'EXPOSURE_CATALOG.json');paths={(r['path'].replace('\\','/'),r['sha256']) for r in catalog}
    available={r['sha256']:r['path'] for r in original['availability_only'] if r['classification'].startswith('GitHub publication transport wrapper')}
    for h,w in proof['wrappers'].items():
        assert h in available,'publication wrapper not actually decoded in fresh audit'
        for name,logical_h in w['logical'].items():
            assert (available[h].replace('\\','/')+'!publish:'+name,logical_h) in paths,'decoded logical source missing from fresh audit'
    corrected=[]
    for r in original['rows']:
        e=r.get('evidence')
        # Never erase independent evidence or an abbreviated evidence list.
        if r['id'] in proof['safe_IDs'] and isinstance(e,dict) and e['count']==1 and len(e['examples'])==1 and e['examples'][0]['sha256']==proof['failed_index_sha256']:
            r['evidence']=None;r['exclusions']=[x for x in r['exclusions'] if x!='prior_execution_or_ambiguous_project_ID_description_evidence'];corrected.append(r['id'])
    mbpp=read('D:/HeteroSpec-RTX-Target-V1/work/rtx-target-v1/sanitized-mbpp.json');gsm=[json.loads(line) for line in (LOCAL/'datasets/gsm8k-test.jsonl').read_text(encoding='utf-8').splitlines()]
    descriptions={'MBPP/'+str(t['task_id']):t['prompt'] for t in mbpp};descriptions.update({'GSM8K/test/'+str(i):t['question'] for i,t in enumerate(gsm)})
    pool=[]
    for r in original['rows']:
        if r['exclusions']:continue
        desc=descriptions[r['id']];prefix='Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n' if r['domain']=='MBPP' else 'Solve the following problem and explain your reasoning.\n\n'
        pool.append({'id':r['id'],'domain':r['domain'],'description':desc,'raw_prompt':prefix+desc,'description_sha256':hashlib.sha256(desc.encode()).hexdigest(),'cap':128,'selection_hash':r['selection_hash']})
    pool.sort(key=lambda t:(t['selection_hash'],t['id']));counts={d:sum(t['domain']==d for t in pool) for d in ['MBPP','GSM8K']};assert all(v>=12 for v in counts.values())
    old_hash=sha(PUB/'EXPOSURE_AUDIT.json');shutil.move(PUB/'EXPOSURE_AUDIT.json',LOCAL/'preparation-versions/EXPOSURE_INDEX_ATTEMPT.json')
    original.update(status='PASS',eligible_ranked=[t['id'] for t in pool],utc=now(),static_index_correction={'original_fresh_audit_sha256':old_hash,'superseded_zero_forward_index_sha256':proof['failed_index_sha256'],'canonical_PR80_audit_sha256':proof['canonical_sha256'],'corrected_metadata_only_IDs':corrected,'actual_wrapper_logical_objects_verified':sum(len(w['logical']) for w in proof['wrappers'].values()),'independent_evidence_never_erased':True,'forward_calls_before_correction':0})
    save(PUB/'EXPOSURE_AUDIT.json',original);save(LOCAL/'AVAILABLE_CANDIDATES.json',{'eligible_pool':pool,'selected':[],'model_forwards':0})
    save(PUB/'AUDIT_INDEX_CORRECTION.json',{'status':'PASS','utc':now(),'eligible_pool':sorted(proof['safe_IDs']),'selected':[],'source_proof':{**proof,'safe_IDs':sorted(proof['safe_IDs'])},'corrected':corrected,'eligible_counts':counts,'catalog_sha256':sha(LOCAL/'EXPOSURE_CATALOG.json'),'policy':'Only superseded zero-forward metadata-index evidence is removed after verified actual wrapper decoding; independent execution/ambiguous/reservation evidence retained. No model output used.'})
    print('FULL AUDIT + SOURCE INDEX CORRECTION PASS',json.dumps(counts),'corrected',len(corrected),flush=True)
if __name__=='__main__':main()
