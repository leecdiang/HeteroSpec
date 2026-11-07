"""One frozen 160-request campaign. No resume, retry, or root replacement."""
from host import *
import coverage,itertools,hashlib

def schedule():
    selected=read(ROOT/'coverage.json')['selected'];perms=list(itertools.permutations(coverage.ARMS));sessions=[]
    for s in range(2):
        order=sorted(range(len(selected)),key=lambda i:hashlib.sha256(f'{coverage.SEED}|session|{s}|{selected[i]["root_id"]}'.encode()).hexdigest())
        sessions.append([dict(index=i,arms=perms[(2*i+s)%6]) for i in order])
    return sessions

def unit(i,name,arm,capture,state=True):
    r=read(ROOT/'selected-inputs.json')[i];p=read(ROOT/'coverage.json')['selected'][i]
    u=dict(id=name,tokens=r['request_ids'],head=p['physical_head'],arm=arm,cap=128,capture=capture)
    if state:u['state']=str(ROOT/f'science-r-{i:02}/r0/prefix.bin')
    return u

def check(i,p,heavy=False):
    plan=read(ROOT/'coverage.json')['selected'][i];ref=ROOT/f'science-r-{i:02}/r0';a=read(ref/'receipt.json');b=read(p/'receipt.json')
    row=dict(index=i,path=str(p.relative_to(ROOT)),output=a['output']==b['output'],position=a['final_position']==b['final_position'],pending=a['pending_token']==b['pending_token'])
    if heavy:row.update(vectors={x.name:sha(x) for x in ref.glob('*.f32')}=={x.name:sha(x) for x in p.glob('*.f32')},state=sha(ref/'final.bin')==sha(p/'final.bin'))
    if b['arm']!='R':
        row.update(calls=[[c['head'],c['width']] for c in b['calls']]==plan['plans'][b['arm']],head=b['physical_dense_head']==plan['physical_head'],phases=abs(b['service_s']-sum(b[k] for k in ('lookup_import_ready_s','append_execution_s','continuation_s')))<1e-8)
    row['passed']=all(v for k,v in row.items() if k not in ('index','path'));return row

def main():
    frozen=read(ROOT/'FREEZE.json');pub=read(ROOT/'PUBLISHED_FREEZE.json');assert pub['freeze_sha256']==sha(ROOT/'FREEZE.json')
    for p,h in frozen['files'].items():assert sha(ROOT/p)==h,p
    for p,h in frozen['sources'].items():assert sha(HERE/p)==h,p
    for build in (OLD/'oracle02',ROOT/'candidate01'):
        b=read(build/'binding.json');assert sha(build/'worker.exe')==b['exe']
        for name,h in b['modules'].items():assert sha(build/name)==h
    assert not list(ROOT.glob('science-*/launch.json'))
    proof=[]
    try:
        for i in range(8):
            out=run(f'science-r-{i:02}',OLD/'oracle02',[unit(i,'r0','R',True,False),unit(i,'r1','R',True,False)],'scientific')
            row=check(i,out/'r1',True);proof.append(row);assert row['passed'],row
        units=[unit(i,f'{i:02}/{arm}/{kind}',arm,kind=='heavy') for i in range(8) for arm in coverage.ARMS for kind in ('heavy','off')]
        out=run('science-qualification',ROOT/'candidate01',units,'scientific')
        for i in range(8):
            for arm in coverage.ARMS:
                for kind in ('heavy','off'):
                    row=check(i,out/f'{i:02}/{arm}/{kind}',kind=='heavy');proof.append(row);assert row['passed'],row
        put(ROOT/'QUALIFICATION.json',proof)
        for s,blocks in enumerate(read(ROOT/'schedule.json')):
            units=[unit(b['index'],f'{b["index"]:02}/{arm}/{kind}',arm,False) for b in blocks for arm in b['arms'] for kind in ('warmup','measure')]
            out=run(f'science-session-{s}',ROOT/'candidate01',units,'scientific')
            for b in blocks:
                for arm in b['arms']:
                    for kind in ('warmup','measure'):
                        row=check(b['index'],out/f'{b["index"]:02}/{arm}/{kind}');proof.append(row);assert row['passed'],row
        put(ROOT/'COMPLETE.json',dict(passed=True,checks=proof,scientific_requests=160,all_stage_requests=174))
    except BaseException as e:
        put(ROOT/'CAMPAIGN_FAILURE.json',dict(error=repr(e),checks=proof));raise

if __name__=='__main__':main()
