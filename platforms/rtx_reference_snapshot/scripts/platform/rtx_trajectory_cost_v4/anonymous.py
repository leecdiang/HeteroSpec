"""Derived anonymous engineering/results capsule; original evidence is never overwritten."""
import json,re,shutil
from datetime import datetime,timezone,timedelta
from pathlib import Path
from prepare import ROOT,save,sha
from package import publish
def make(original,mode,arm):
    original=Path(original);stage=ROOT/'work'/('anonymous-stage-'+arm+'-'+mode);stage.mkdir(exist_ok=False)
    # Preserve all recomputable observations; exclude unnecessary original host
    # catalogs, build snapshots and Git author/commit objects from the derivative.
    shutil.copytree(original/'metadata',stage/'metadata',ignore=shutil.ignore_patterns('USER_SPECIFICATION.md','READ_RECEIPTS.json','SOURCE_ADAPTATION.json','OPERATOR_SOURCE','*_GIT_PROOF.json','F0_MANIFEST.json','F1_MANIFEST.json','F2_MANIFEST.json','B_START_MANIFEST.json'))
    for name in ['engineering-attempt1','engineering-extra','capture-repair','capture-regression','negative-fixtures','A-pre-live','A-live','B-formal']:
        p=original/'work'/name
        if p.exists():shutil.copytree(p,stage/'work'/name,ignore=shutil.ignore_patterns('source_snapshot'))
    dest=stage/'frozen_source/scripts/platform/rtx_trajectory_cost_v4';dest.mkdir(parents=True)
    for name in ['verify_common.py','verify_replay.py','verify_joint.py','verify_A.py','verify_B.py','verify_capture_repair.py','verify_receipts.py','observations.py','offline.py']:shutil.copyfile(original/'frozen_source/scripts/platform/rtx_trajectory_cost_v4'/name,dest/name)
    stamps=set();originals={};pids=set()
    for p in stage.rglob('*'):
        if not p.is_file():continue
        originals[p.relative_to(stage).as_posix()]={'bytes':p.stat().st_size,'sha256':sha(p)}
        for s in re.findall(rb'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:\+00:00|Z)',p.read_bytes()):stamps.add(s.decode())
    ordinal={s:(datetime(2000,1,1,tzinfo=timezone.utc)+timedelta(seconds=i+1)).isoformat() for i,s in enumerate(sorted(stamps))}
    pidmap={}
    def clean(s):
        s=s.replace('C:\\\\Users\\\\ASUS\\\\','AUDITED_HOST/').replace('C:\\Users\\ASUS\\','AUDITED_HOST/').replace('C:/Users/ASUS/','AUDITED_HOST/')
        s=s.replace('D:\\\\HeteroSpec-PC','EXTERNAL_ASSET_ROOT').replace('D:\\HeteroSpec-PC','EXTERNAL_ASSET_ROOT').replace('D:/HeteroSpec-PC','EXTERNAL_ASSET_ROOT')
        s=re.sub(r'(?i)[A-Z]:[\\/]Users[\\/][^\\/]+[\\/]','AUDITED_HOST/',s)
        s=s.replace('leecdiang/HeteroSpec','ANON_REPOSITORY');s=re.sub(r'wxid_[A-Za-z0-9_]+','ANON_ACCOUNT',s)
        s=re.sub(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:\+00:00|Z)',lambda m:ordinal[m.group(0)],s)
        return s
    def scrub(o):
        if isinstance(o,dict):
            result={}
            for k,v in o.items():
                if k in ['server_headers','git_author','author','committer']:continue
                if k=='pid' and isinstance(v,int):
                    if v not in pidmap:pidmap[v]=len(pidmap)+1
                    result[k]=pidmap[v]
                else:result[clean(k)]=scrub(v)
            return result
        if isinstance(o,list):return [scrub(x) for x in o]
        return clean(o) if isinstance(o,str) else o
    for p in stage.rglob('*'):
        if not p.is_file():continue
        if p.suffix=='.json':save(p,scrub(json.loads(p.read_text(encoding='utf-8'))))
        elif p.suffix=='.jsonl':p.write_bytes(b''.join(json.dumps(scrub(json.loads(x)),separators=(',',':')).encode()+b'\n' for x in p.read_bytes().splitlines()))
        elif p.suffix in ['.log','.txt','.md']:p.write_bytes(clean(p.read_bytes().decode('latin-1')).encode('latin-1'))
    tapes={}
    for p in stage.rglob('tape.jsonl'):
        rows=[json.loads(x) for x in p.read_bytes().splitlines()];previous='0'*64
        for r in rows:
            r.pop('event_sha256');r['previous_event_hash']=previous;raw=json.dumps(r,separators=(',',':')).encode();r['event_sha256']=__import__('hashlib').sha256(raw).hexdigest();previous=r['event_sha256']
        p.write_bytes(b''.join(json.dumps(x,separators=(',',':')).encode()+b'\n' for x in rows));tapes[p.parent]=sha(p)
    for p in stage.rglob('record.json'):
        r=json.loads(p.read_text())
        if r.get('condition')=='H2_P_R':r['tape_sha256']=tapes[p.parent]
        if r.get('condition')=='R_ONLY':r['replayed_tape_sha256']=tapes[p.parent.parent/r['run_id'].replace('R_ONLY','H2_P_R')]
        if 'files' in r:r['files']={name:{'bytes':(p.parent/name).stat().st_size,'sha256':sha(p.parent/name)} for name in r['files']}
        save(p,r)
    for p in stage.glob('work/*/records.json'):
        m=json.loads(p.read_text())
        if 'runs' in m:
            m['runs']=[{**json.loads((stage/r['path']/'record.json').read_text()),**{k:r[k] for k in ['path','canonical_condition'] if k in r}} for r in m['runs']]
        save(p,m)
    predictions=stage/'metadata/A_trajectory/RESERVED_PREDICTIONS.json'
    if predictions.exists():
        p=json.loads(predictions.read_text())
        for row in p['rows']:
            rid=row['conditions']['A_H2_P_R']['run_id'];row['tape_sha256']=tapes[stage/'work/A-pre-live/runs'/rid]
        save(predictions,p)
    save(stage/'ORIGINAL_FROZEN_DIGESTS.json',{'original_files':originals,'limit':'References to original bytes, not authentication of derived bytes; digest linkage is possible'})
    (stage/'ANONYMIZATION_LIMITS.md').write_text('Derived content for anonymous recomputation. Host paths, account names and PIDs are replaced; UTC values encode ordinal order only. Native timer intervals remain actual retained engineering measurements. Tape chains and file inventories are rehashed after path/time redaction. Original byte digests can link back to author evidence. This capsule does not independently authenticate original remote chronology, omitted weights/runtime/driver bytes, or unlinkability.\n',encoding='utf-8')
    for p in stage.rglob('*'):
        if p.is_file() and p.suffix in ['.json','.jsonl','.log','.txt','.md','.py']:
            b=p.read_bytes()
            if b'ASUS' in b or b'wxid_' in b or b'leecdiang' in b:raise RuntimeError('anonymous privacy check failed '+str(p))
    return publish(stage,mode,arm,True)
