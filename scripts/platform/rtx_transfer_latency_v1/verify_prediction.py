"""Independent A-arm check, including lawful pre-reserved stop states."""
import argparse, hashlib, itertools, json
from pathlib import Path
from verify_common import read, meta, require, validate_phase, package_checks

def check(root,asset_root=None):
    m=meta(root);p=read(m/'protocol.json');report=read(m/'prediction/REPORT.json')
    q=validate_phase(root,'harness_qualification','prediction',m)
    expected=[(t,r,'TARGET_REFERENCE') for t in p['prediction']['harness_qualification_tasks'] for r in (1,2,3)]
    require([tuple(x) for x in q['schedule']]==expected,'harness schedule differs')
    oldpath=root/'old_reference.json'
    if not oldpath.exists():oldpath=Path(__file__).resolve().parents[3]/'work/old-reference/formal_records.json'
    old=read(oldpath);refs={(r['task_id'],r['repetition']):r['generated_ids'] for r in old['runs'] if r['condition']=='TARGET_REFERENCE'}
    matches=sum(r['generated_ids']==refs[r['task_id'],r['repetition']] for r in q['runs'])
    require(matches==90,'harness did not independently reproduce 90/90')
    disc=validate_phase(root,'discovery_H1','prediction',m)
    expected=[(t,r,c) for t in p['prediction']['discovery_tasks'] for r in (1,2,3) for c in ('H1_TARGET_UB2','RTX_BATCHED_K2')]
    require([tuple(x) for x in disc['schedule']]==expected,'discovery schedule differs')
    k={(r['task_id'],r['repetition'],r['condition']):r['generated_ids'] for r in disc['runs']};rows=[]
    for t in p['prediction']['discovery_tasks']:
        for rep in (1,2,3):
            a=k[t,rep,'H1_TARGET_UB2'];b=k[t,rep,'RTX_BATCHED_K2'];diff=None
            for i,(x,y) in enumerate(itertools.zip_longest(a,b)):
                if x!=y:diff={'index':i,'reference_id':x,'candidate_id':y};break
            rows.append({'task_id':t,'repetition':rep,'exact':not bool(diff),'first_divergence':diff})
    count=sum(r['exact'] for r in rows);require(rows==report['comparisons'] and count==report['discovery_complete_matches'],'A discovery result differs')
    if count<36:
        require(report['status']=='MECHANISM_NOT_ISOLATED' and report['reserved_runs']==0,'A lawful stop differs')
        require(not (root/'reserved_prediction').exists() and not (root/'reserved_live').exists(),'reserved inference after discovery stop')
        require(not (m/'prediction/RESERVED_PREDICTIONS.json').exists(),'fabricated reserved predictions')
    else:
        pred=validate_phase(root,'reserved_prediction','prediction',m);live=validate_phase(root,'reserved_live','prediction',m)
        frozen=read(m/'prediction/RESERVED_PREDICTIONS.json');keys={(r['task_id'],r['repetition']):r['generated_ids'] for r in live['runs']}
        require(len(frozen['rows'])==72 and len(keys)==72,'reserved coverage differs')
        require(sum(row['prediction']==keys[row['task_id'],row['repetition']] for row in frozen['rows'])==report['predictor_live_matches'],'72 prediction comparisons differ')
        chronology=read(m/'chronology/predictions.json');require(chronology['commit']==chronology['remote_ref'],'prediction remote commitment differs')
        require(chronology['remote_ack_utc']<live['started_utc'],'prediction push not before first live')
        hypo=read(m/'chronology/hypothesis.json');require(hypo['remote_ack_utc']<pred['started_utc'],'hypothesis push not before reserved inference')
    salt=p['prediction']['selection_salt'];pool=p['prediction']['eligible_pool']
    require(sorted(pool,key=lambda t:hashlib.sha256((salt+t).encode()).hexdigest())[:24]==p['prediction']['task_ids'],'reserved deterministic selection differs')
    result={'status':'PASS','scientific_status':report['status'],'harness_pairs_independently_checked':90,'discovery_pairs_independently_checked':36,'H1_exact':count,'reserved_pairs':0 if count<36 else 72}
    result.update(package_checks(root,m,'prediction',asset_root));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--asset-root',type=Path);a=p.parse_args();print(json.dumps(check(a.root,a.asset_root),indent=2))
