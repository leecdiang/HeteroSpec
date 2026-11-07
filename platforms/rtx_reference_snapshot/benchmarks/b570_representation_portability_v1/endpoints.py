"""Reconstruct endpoint classes from raw stdout, not prior normalized analysis."""
import argparse, collections, hashlib, json, pathlib
from common import ROOT, load, save, sha, modules

def signature(r):
    return (tuple(r['ids']),tuple(r['eog']),r['length'],r['terminal_id'],r['stop_reason'])

def main():
    p=argparse.ArgumentParser(); p.add_argument('--old',type=pathlib.Path,required=True)
    a=p.parse_args(); before=modules(); b=a.old; run=b/'_host/run'
    plan=load(b/'p0/PLAN_P1.json'); slots={s['slot']:s for s in plan['slots']}
    manifest={x['path']:x['sha256'] for x in load(b/'p1/ARCHIVE_MANIFEST.json')['files']}
    def bind(f):
        rel=f.relative_to(b).as_posix(); actual=sha(f)
        # The CAS uses registered paths, including _host/run.
        assert manifest[rel]==actual, rel
        return dict(path=rel,sha256=actual)
    attempts=[json.loads(x) for x in (run/'LEDGER.jsonl').read_text().splitlines()]
    attempts=[x for x in attempts if x['event']=='PROCESS_ATTEMPT']
    rows=[]; incomplete=[]; raw_results={}
    for attempt in attempts:
        sid=attempt['slot']; s=slots[sid]; d=run/sid
        request=load(d/'REQUEST.json'); launch=load(d/'LAUNCH.json')
        assert request['request_id']==sid and launch['arm']==s['arm']
        assert sha(d/'REQUEST.wire')==launch['wire_sha256']
        source=[bind(d/n) for n in ['stdout.jsonl','REQUEST.json','REQUEST.wire','LAUNCH.json','IDENTITY.json','LIFECYCLE.json']]
        events=[json.loads(x) for x in (d/'stdout.jsonl').read_text().splitlines()]
        found=[x for x in events if x.get('event')=='RESULT']
        if not found:
            incomplete.append(dict(slot=sid,task=s['task'],arm=s['arm'],endpoint=None,source=source)); continue
        assert len(found)==1
        r=found[0]; assert r==load(d/'RESULT.json'); source.append(bind(d/'RESULT.json'))
        assert r['length']==len(r['ids'])==len(r['eog']) and r['terminal_id']==r['ids'][-1]
        assert r['prompt_ids']==request['prompt_ids']==s['request']['prompt_ids']
        assert all(type(x) is int for x in r['ids']) and all(type(x) is bool for x in r['eog'])
        assert r['observation_mode']==s['mode']
        ep={k:r[k] for k in ['ids','eog','length','terminal_id','stop_reason']}
        digest=hashlib.sha256(json.dumps(ep,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        row=dict(slot=sid,task=s['task'],arm=s['arm'],session=s['session'],
                 producer=s['request']['recipe']['producer'],runtime=launch['runtime_role'],
                 timing_channel=r['observation_mode'],native_request_ms=r['native_request_ms'],
                 endpoint=ep,endpoint_sha256=digest,source=source)
        rows.append(row); raw_results[sid]=r
    classes={}
    for task in sorted({x['task'] for x in rows}):
        by=collections.defaultdict(list)
        for x in rows:
            if x['task']==task: by[x['endpoint_sha256']].append(x['arm']+f":{x['timing_channel']}:s{x['session']}")
        classes[task]=[dict(endpoint_sha256=k,members=v) for k,v in by.items()]
    pairs=[('C_B_MQ','C_B_PQ'),('C_B_PQ','C_B_QB'),('C_B_MQ','C_B_QB'),
           ('C_R_MQ','C_R_PQ'),('C_R_PQ','C_R_QB'),('C_R_MQ','C_R_QB'),
           ('M_B_QB','C_B_PQ'),('M_R_QB','C_R_PQ'),('M_R_QB','C_R_QB')]
    relations=[]; counterexamples=0
    for task in classes:
        counts={x['arm']:x for x in rows if x['task']==task and x['timing_channel']=='counts'}
        reference=next(x for x in rows if x['task']==task and x['arm']=='R')
        for x in counts.values():
            if x['arm'] not in ('R','R_SHADOW') and signature(x['endpoint'])!=signature(reference['endpoint']): counterexamples+=1
        for left,right in pairs:
            l=counts[left]['endpoint']; r=counts[right]['endpoint']
            diff=next((i for i,(u,v) in enumerate(zip(l['ids'],r['ids'])) if u!=v),None)
            relations.append(dict(task=task,left=left,right=right,full_endpoint_equal=signature(l)==signature(r),first_id_difference_0based=diff))
    assert len(rows)==48 and len(incomplete)==1 and len(attempts)==49 and counterexamples==14
    close=load(run/'CLOSEOUT.json'); assert len(close['unstarted'])==31
    save(ROOT/'ENDPOINTS.json',dict(scope='Exploratory original NO-GO, CAP128 window only',
         source_manifest_sha256=sha(b/'p1/ARCHIVE_MANIFEST.json'),rows=rows,classes=classes,relations=relations,
         incomplete=incomplete,unstarted=close['unstarted'],counterexamples_to_R=counterexamples,
         historical_native_callers=8110, qualified_speedup=None,state_distance=None,
         modules_before=before,modules_after=modules(),new_model_processes=0,new_gpu_starts=0))
    text=['# Full endpoint equivalence classes (IDs + EOG + length + terminal + stop)','',
          'Original NO-GO remains: 49 starts, 48 complete, 1 incomplete, 31 unstarted, 14 treatment counterexamples.',
          'Classes include timing-channel/session repeats. Equality is limited to this CAP128 window.','',
          '| Input | Class | Members |','|---|---|---|']
    for task,cs in classes.items():
        for i,c in enumerate(cs): text.append(f"| {task} | {i+1} ({c['endpoint_sha256'][:12]}) | {', '.join(c['members'])} |")
    text+=['','| Pair | Full endpoints equal across four inputs |','|---|---|']
    for l,r in pairs:
        yes=[x['task'].split('/')[-1] for x in relations if x['left']==l and x['right']==r and x['full_endpoint_equal']]
        text.append(f"| {l} / {r} | {', '.join(yes) or 'none'} |")
    text+=['','M_R_QB q1 executes the common original path. C_R_PQ 4/4 does not confer full-P1, unseen-input or safety qualification.',
           'No state snapshots: operand/KV identity and state distance remain unknown. No qualified speedup is calculated.']
    (ROOT/'ENDPOINT_RELATIONS.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print(dict(complete=len(rows),incomplete=len(incomplete),counterexamples=counterexamples,classes={k:len(v) for k,v in classes.items()}))

if __name__=='__main__':main()
