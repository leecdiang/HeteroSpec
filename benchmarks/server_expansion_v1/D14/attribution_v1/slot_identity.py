"""Lane-scoped frozen-slot adapter derived from qualified M1 admission."""
from pathlib import Path
ARMS={'W_L4_D4','W_P_D4','L_L4_D4','L_P_D4'}
def identity(frozen,build_path,build,job_path,out,reserved):
    from common import need,read,sha
    path=Path(frozen['plan']['path']).resolve();need(sha(path)==frozen['plan']['sha256'],'Frozen attribution plan changed')
    p=read(path);workers={x['id']:x for x in p['workers']};arms=set(p['arms'])
    need(p['study']=='server_d14_d4_attribution_v1' and p['panel'] in ('attribution','packed_pair'),'Registered14B attribution study only')
    expected=16 if p['panel']=='attribution' else 8
    need(arms==(ARMS if expected==16 else {'W_P_D4','L_P_D4'}),'Exact registered arms')
    need(len(workers)==len(p['workers'])==expected and p['measurements']==16*expected and p['primers']==2*expected,'Exact frozen worker/request envelope')
    out=Path(out).resolve();slot=workers.get(out.name)
    need(slot is not None and out==path.parent/'runs'/slot['id'],'Unregistered attribution output slot')
    need(Path(job_path).resolve()==path.parent/slot['job'] and sha(job_path)==slot['job_sha256'],'Different frozen slot job')
    need(build['role']==slot['core'],'Different numerical core for frozen slot')
    known=frozen['executables'].get(build['executable_sha256']);need(known is not None and sha(build_path)==known['build']['sha256'],'Different frozen build')
    for row in reserved:
        if row['phase']!='confirmation':continue
        prior=workers.get(Path(row['out']).name)
        need(prior is not None and Path(row['out']).resolve()==path.parent/'runs'/prior['id'],'Unresolved prior slot identity')
        need(row['job_sha256']==prior['job_sha256'] and row['plan_sha256']==frozen['plan']['sha256'],'Prior slot/plan binding changed')
        need(prior['id']!=slot['id'],'Slot already reserved; retain failed or finished slot, no selected retry')
    return dict(confirmation_slot_id=slot['id'],plan_sha256=frozen['plan']['sha256'],build_sha256=sha(build_path))
