"""Independent CPU-only v4 delivery: no prior sample can qualify a v4 slot."""
import itertools
import pathlib
import struct
import time
from legacy import HERE,OLD,RUN,load,save,sha,need,STAGES,compare,analyze_files,modules
from lifecycle_audit import audit
from workers import rows

def inventory(plan):
    by={}
    for s in plan['slots']:
        if s['kind']=='graph':by.setdefault((s['input_id'],s['repeat']),{})[s['mode']]=s
    comparisons=[dict(input_id=k[0],repeat=k[1],a=v[a]['id'],b=v[b]['id'],pair=a+'/'+b) for k,v in by.items() for a,b in itertools.combinations(v,2)]
    repeats=[dict(input_id=k[0],mode=m,a=v[m]['id'],b=by[k[0],1][m]['id']) for k,v in by.items() if k[1]==0 for m in v]
    return comparisons,repeats

def main():
    begin=time.monotonic_ns();before=modules();f0=load(HERE/'F0.json');plan=load(HERE/'PLAN.json');close=load(RUN/'CLOSEOUT.json')
    for row in f0['bound_files']:need(sha(row['path'])==row['sha256'],'frozen identity drift')
    data={};identities={};results=[];records={r['slot']['id']:r for r in close['records']}
    for slot in plan['slots']:
        r=records.get(slot['id']);state=r['status'] if r else 'UNSTARTED';result=dict(slot=slot,status=state)
        if state=='ADMITTED':
            folder=RUN/slot['id'];audit(folder)
            if slot['kind']=='graph':
                request=load(folder/'REQUEST.wire');raw=rows(folder/'raw.jsonl');graph=next(x['graph'] for x in raw if x['event']=='GRAPH_OUTPUT')
                ref=load(OLD/'REFERENCE_MANIFEST.json')['inputs'][slot['input_id']]['stages'];reference={}
                for s,x in ref.items():
                    need(sha(OLD/x['path'])==x['sha256'],'reference identity');reference[s]=[v[0] for v in struct.iter_unpack('<d',(OLD/x['path']).read_bytes())]
                analysis,vectors=analyze_files(request,graph,folder,pathlib.Path(request['input']).read_bytes(),reference)
                for s in STAGES:need(vectors[s]==(folder/'normalized'/(s+'.f32')).read_bytes(),'fresh full-vector logical reconstruction')
                data[slot['id']]=vectors;life=load(folder/'LIFECYCLE.json');identities[slot['id']]=(life['pid'],life['creation_FILETIME']);result['analysis']=analysis
        results.append(result)
    pairs,repeats=inventory(plan)
    for collection,independent in ((pairs,False),(repeats,True)):
        for row in collection:
            if row['a'] in data and row['b'] in data:
                if independent:need(identities[row['a']]!=identities[row['b']],'independent process identity')
                row['relation']=compare(data[row['a']],data[row['b']]);row['status']='AVAILABLE'
                if independent:need(row['relation']['all_stages_bitwise_equal'],'independent repeat mismatch')
            else:row['status']='MISSING';row['relation']=None
    # Descriptive cross-run anchors only; never fill/qualify a v4 slot from v3.
    oldroot=HERE.parents[1]/'host_outputs/supervised_numerical_v3/b570-supervised-numerical-v3-20261015-01'
    old={tuple(r['slot'].get(k) for k in ('input_id','mode','repeat')):r for r in load(oldroot/'CLOSEOUT.json')['records'] if r['status']=='ADMITTED' and r['slot']['kind']=='graph'}
    anchors=[]
    for slot in plan['slots']:
        if slot.get('group')!='B':continue
        previous=old.get(tuple(slot[k] for k in ('input_id','mode','repeat')))
        relation=None
        if slot['id'] in data and previous:
            folder=oldroot/previous['slot']['id'];prior={s:(folder/'normalized'/(s+'.f32')).read_bytes() for s in STAGES};relation=compare(data[slot['id']],prior)
        anchors.append(dict(v4_slot=slot['id'],v3_slot=previous['slot']['id'] if previous else None,relation=relation,status='AVAILABLE' if relation else 'MISSING',role='DESCRIPTIVE_SEPARATE_HISTORY_NOT_A_V4_SAMPLE'))
    save(RUN/'V4_RECONSTRUCTION.json',dict(run_id=f0['run_id'],slots=results,cross_representation=pairs,independent_repeats=repeats,
        separate_v3_anchors=anchors,
        CPU_wall_seconds=(time.monotonic_ns()-begin)/1e9,modules_before=before,modules_after=modules(),old_samples_imported=0,
        scope='Only this targeted panel; missing stays missing; no tolerance gates or speed claim; v3 is separate history',GPU_hosts_started=0))

if __name__=='__main__':main()
