"""Prospective cohorts and counterbalanced schedules; no model launches."""
from __future__ import annotations
import argparse,itertools
from pathlib import Path
from common import digest,need,read,write_new

ARMS={
 'rtx-operator':['graph_tiles','backend_loop4','packed'],
 'rtx-draft':['M','D1','D2','D4'],
 'b570-draft':['M','C1U1','C4U1','C4U2','C4U4'],
}
SESSIONS={'rtx-operator':6,'rtx-draft':4,'b570-draft':5}
SEED='tpds-decisive-20261105-v1'

def caller_chunks(length:int,width:int)->list[int]:
    need(type(length) is int and length>0,'positive prompt length')
    need(type(width) is int and width in (1,2,4),'supported caller width')
    out=[];i=0
    while i<length:
        n=min(width,length-i)
        if n==3:n=2
        out.append(n);i+=n
    return out

def williams(n:int)->list[list[int]]:
    need(2<=n<=8,'arm count')
    seq=[0];lo=1;hi=n-1
    while lo<=hi:
        seq.append(lo);lo+=1
        if lo<=hi:seq.append(hi);hi-=1
    rows=[[(x+r)%n for x in seq] for r in range(n)]
    return rows if n%2==0 else rows+[list(reversed(r)) for r in rows]

def select(rows:list[dict], exclusions:set[str], n:int=12, development:int=4)->dict:
    """Pick a path per root BEFORE any length or opportunity conditioning.
    Caller supplies only admissible, native-tokenized records. No truncation.
    """
    need(type(n) is int and n>=8 and type(development) is int and development>=2,'panel size')
    groups={};seen=set()
    for r in rows:
        need(not set(r)&{'seconds','latency','answer','candidate_output','speedup'},'outcome in selector')
        need(isinstance(r['root_id'],str) and isinstance(r['id'],str),'input identity')
        need(r['id'] not in seen,'duplicate input id');seen.add(r['id'])
        if r['root_id'] in exclusions:continue
        need(r.get('native_tokenized') is True,'native tokenizer binding missing')
        need(type(r['tokens']) is int and r['tokens']>0,'token count')
        need(r.get('admitted') is True,'inadmissible source record')
        groups.setdefault(r['root_id'],[]).append(r)
    ordered=sorted(groups,key=lambda k:(digest([SEED,'root',k]),k))
    need(len(ordered)>=n+development,'insufficient unexposed roots; amend before freeze, never pad')
    chosen=[min(groups[k],key=lambda r:(digest([SEED,'path',r['id']]),r['id'])) for k in ordered[:n+development]]
    return {'schema':1,'seed':SEED,'selection':'uniform hash-ranked roots, one hash-ranked path per root',
            'development':chosen[:development],'test':chosen[development:],
            'excluded_roots':sorted(exclusions),'eligible_roots':len(groups),
            'scope':'this deployment/model/lifecycle only; no cross-platform pooling'}

def schedule(panel:dict,lane:str)->dict:
    need(lane in ARMS,'unknown lane');arms=panel.get('arms_by_lane',{}).get(lane,ARMS[lane])
    need(len(arms)==len(set(arms)) and 2<=len(arms)<=len(ARMS[lane]) and set(arms)<=set(ARMS[lane]),'invalid admitted arm roster')
    if arms!=ARMS[lane]:
        need(panel.get('eligibility_decision_pretest') is True,'arm exclusion requires pre-test disposition')
        required={'rtx-operator':set(ARMS[lane]),'rtx-draft':{'M','D1'},'b570-draft':{'M','C1U1','C4U1'}}[lane]
        need(required<=set(arms),'missing mandatory strong control')
        excluded=set(ARMS[lane])-set(arms)
        need(excluded==set(panel.get('excluded_arm_reasons',{})),'missing excluded-arm reasons')
        need(all(panel['excluded_arm_reasons'][x] in ('CAPACITY','NUMERICAL_INELIGIBLE') for x in excluded),'cannot drop an arm because it is slow')
    n=len(arms);sessions=SESSIONS[lane] if arms==ARMS[lane] else (6 if n==3 else 4 if n in (2,4) else n)
    roots=panel['test'];need(len(roots)>=8,'fewer than eight test roots')
    need(len({r['root_id'] for r in roots})==len(roots),'duplicate test roots')
    need(not {r['root_id'] for r in roots}&{r['root_id'] for r in panel.get('development',[])},'development/test leakage')
    if n%2:need(len(roots)%2==0,'odd-arm Williams design requires even root count')
    orders=williams(n);jobs=[]
    for s in range(sessions):
        order=sorted(enumerate(roots),key=lambda x:digest([SEED,lane,s,x[1]['root_id']]))
        for ix,r in order:
            row=((s+ix)%n)+(n if n%2 and ((ix+s//n)%2) else 0)
            if n%2 and sessions==2*n:row=((s+ix)%n)+(n if ((ix+s//n)%2) else 0)
            for period,a in enumerate(orders[row]):
                for kind in ('warmup','measure'):
                    identity=[lane,r['root_id'],s,arms[a],kind]
                    jobs.append({'slot':digest(identity)[:24],'lane':lane,'root_id':r['root_id'],
                                 'input_id':r['id'],'session':s,'period':period,'arm':arms[a],'kind':kind})
    return {'schema':1,'lane':lane,'panel_sha256':digest(panel),'arms':arms,
            'sessions':sessions,'slots':jobs,'measurement_count':len(jobs)//2,
            'note':'one persistent native session where the frozen lifecycle is resident; do not spawn one model per slot'}

def operator_matrix()->list[dict]:
    return [{'q':q,'prefix':p,'purpose':'scalar/tail/boundary numerical probe'}
            for q in (1,4,5,7,8,9,16,31,32) for p in (1,255,256,257,511)]

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('select');s.add_argument('manifest',type=Path);s.add_argument('exclusions',type=Path);s.add_argument('out',type=Path)
    t=sub.add_parser('schedule');t.add_argument('panel',type=Path);t.add_argument('lane',choices=list(ARMS));t.add_argument('out',type=Path)
    a=ap.parse_args()
    if a.cmd=='select':write_new(a.out,select(read(a.manifest)['rows'],set(read(a.exclusions)['roots'])))
    else:write_new(a.out,schedule(read(a.panel),a.lane))
if __name__=='__main__':main()
