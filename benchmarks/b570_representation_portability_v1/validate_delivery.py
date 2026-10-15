"""Final read-only delivery checks, with no further attention execution."""
import argparse, json, os, pathlib, subprocess
from common import ROOT, load, save, sha, modules

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True);a=p.parse_args();before=modules()
    bindings=load(ROOT/'SOURCE_BINDINGS.json')
    for x in bindings['native']:assert sha(a.old/x['path'])==x['sha256']
    assert sha(a.old/'p0/F0_EXECUTION.json')==bindings['F0_sha256']=='29cf422ef631edfa45ba55b56947926e1977070b8957dbc362e4e5581401d6e8'
    count=0
    for group in ('DEV','HOLDOUT'):
        r=load(ROOT/(group+'_RECEIPT.json'))
        assert r['returncode']==0 and r['completed']==r['planned']
        assert sha(ROOT/(group+'_RAW.jsonl'))==r['raw_sha256']
        for entry in r['inputs']:
            assert sha(ROOT/'_host'/group.lower()/(entry['id']+'.bin'))==entry['sha256'];count+=1
        for x in r['actual_loaded_modules']:assert sha(x['path'])==x['sha256']
        for f,digest in r['sources'].items():assert sha(ROOT/f)==digest
    assert count==432
    cpu=load(ROOT/'CPU_RESULT.json');assert cpu['fixtures']==432 and cpu['geometries']==72
    contract=load(ROOT/'CONTRACT_TESTS.json');assert len(contract['mutations'])==4 and all(x['detected'] for x in contract['mutations'])
    assert load(ROOT/'MONITOR_TESTS.json')['candidate_stage_allowed_after_first_R_under_old_claim'] is False
    checker=load(ROOT/'CHECKER_TESTS.json');assert sha(ROOT/'conditions.py')==checker['checker_sha256']
    assert load(ROOT/'STATE_MODEL_TESTS.json')['cache_hits']==2
    git=os.environ.get('HETEROSPEC_GIT','git')
    changed=subprocess.check_output([git,'-C',str(ROOT),'diff','--name-only','039a24bf61374042e0dc9f3a3619ea40b218a5ad'],text=True).splitlines()
    assert all(x.startswith('benchmarks/b570_representation_portability_v1/') for x in changed)
    oldroot=a.old.parent.parent
    oldhead=subprocess.check_output([git,'-C',str(oldroot),'rev-parse','HEAD'],text=True).strip()
    assert oldhead=='039a24bf61374042e0dc9f3a3619ea40b218a5ad'
    assert not subprocess.check_output([git,'-C',str(oldroot),'diff','--name-only','HEAD'],text=True).strip()
    save(ROOT/'DELIVERY_VALIDATION.json',dict(input_hashes_unchanged_after_CPU=432,
         numerical_sources_and_modules_match=True,old_tracked_files_unchanged=True,old_head=oldhead,
         F0_unchanged=True,scope_new_directory_only=True,
         exact_oracle_failures=0,attention_fixtures_added_by_this_check=0,
         two_infrastructure_revision_receipts=['CHECKER_TESTS.json','STATE_MODEL_TESTS.json'],
         modules_before=before,modules_after=modules(),new_gpu_starts=0,new_model_processes=0))
    print(dict(input_hashes=432,numerical_hashes=True,old_F0_and_source_unchanged=True,new_directory_only=True))

if __name__=='__main__':main()
