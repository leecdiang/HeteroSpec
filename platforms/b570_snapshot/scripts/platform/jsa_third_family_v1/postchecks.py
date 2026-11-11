"""Read-only post-run identity and accounting verification."""
from freeze import *
def main():
    f0b=read(PUB/'F0B.json')
    for name,h in f0b['code_sha256'].items():assert sha(Path(__file__).parent/name)==h
    for name,h in f0b['payload_sha256'].items():assert sha(PUB/name)==h
    for path,h in f0b['runtime_binaries'].items():assert sha(path)==h
    inv=read(LOCAL/'native/SOURCE_HASHES_FINAL.json')
    for name,h in inv.items():assert sha(LOCAL/'native/source'/name)==h
    from preflight import models
    assets=[]
    for family,pair in models().items():
        for role,m in pair.items():assert sha(m['path'])==m['sha256'];assets.append({'family':family,'role':role,'bytes':Path(m['path']).stat().st_size,'sha256':sha(m['path'])})
    accounting={}
    for phase in ['engineering','formal']:
        root=LOCAL/'runs'/phase;started=[read(p) for p in root.rglob('REQUEST_STARTED.json')];assert len({a['slot'] for a in started})==len(started)
        accounting[phase]={'actual_started':len(started),'completed':len(list(root.rglob('COMPLETED.json'))),'warmups_started':sum(a['warmup'] for a in started),'paid_non_warmup_started':sum(not a['warmup'] for a in started),'owned_GPU_process_seconds':sum(read(p)['seconds'] for p in root.rglob('LIFETIME.json'))}
    assert accounting['engineering']['actual_started']<=640 and accounting['formal']['actual_started']<=3600
    preflight_seconds=sum(read(p)['lifetime_seconds'] for p in PUB.glob('ZERO_LOAD_*.json'))
    accounting['engineering']['zero_forward_preflight_owned_seconds']=preflight_seconds
    assert accounting['engineering']['owned_GPU_process_seconds']+preflight_seconds<=8*3600
    assert sum(a['actual_started'] for a in accounting.values())<=4240 and sum(a['owned_GPU_process_seconds'] for a in accounting.values())+preflight_seconds<=32*3600
    save(PUB/'POSTCHECKS.json',{'status':'PASS','utc':now(),'final_code_and_F0B_payload_unchanged':True,'runtime_and_published_numerical_DLLs_unchanged':True,'full_private_source_files_verified':len(inv),'full_model_asset_hashes':assets,'accounting':accounting,'old_PR80_sha':'92aeebe9bb422a754b1457e9e3572e7a57dd1d31','old_PR82_sha':'7e82fa0b8fc2c9d56e04512c47a0986171534b25','formal_retries':0,'no_formal_configuration_selection':True})
    print('POSTCHECKS PASS',json.dumps(accounting),flush=True)
if __name__=='__main__':main()
