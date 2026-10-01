"""Derived anonymous recomputation capsule; never overwrite original evidence."""
import json,hashlib,re,shutil,tarfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
from prepare import ROOT,STUDY,save
from engine import digest,canonical
from package import ART,offline
def main():
    stage=ROOT/'work/anonymous-review';stage.mkdir(exist_ok=False)
    folders=['reference-qualification','discovery','pre-live','live']
    for folder in folders:
        p=ROOT/'work'/folder
        if p.exists():shutil.copytree(p,stage/folder)
    shutil.copytree(STUDY,stage/'metadata')
    source=stage/'frozen_source/scripts/platform/rtx_independent_proposal_replay_v2';source.mkdir(parents=True)
    for name in ['verify.py','offline.py']:shutil.copyfile(Path(__file__).with_name(name),source/name)
    originals={};timestamps=set()
    for p in stage.rglob('*'):
        if not p.is_file():continue
        b=p.read_bytes();originals[p.relative_to(stage).as_posix()]={'sha256':digest(b),'bytes':len(b)}
        for stamp in re.findall(rb'2026-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:\+00:00|Z)',b):timestamps.add(stamp.decode())
    ordinal={s:(datetime(2000,1,1,tzinfo=timezone.utc)+timedelta(seconds=i+1)).isoformat() for i,s in enumerate(sorted(timestamps))}
    def clean(s):
        s=s.replace('C:\\\\Users\\\\ASUS\\\\','AUDITED_HOST/').replace('C:\\\\Users\\\\DIANG\\\\','AUDITED_HOST/').replace('D:\\\\HeteroSpec-PC','EXTERNAL_ASSET_ROOT')
        s=s.replace('C:\\Users\\ASUS\\','AUDITED_HOST/').replace('C:/Users/ASUS/','AUDITED_HOST/').replace('C:\\Users\\DIANG\\','AUDITED_HOST/').replace('C:/Users/DIANG/','AUDITED_HOST/')
        s=s.replace('D:\\HeteroSpec-PC','EXTERNAL_ASSET_ROOT').replace('D:/HeteroSpec-PC','EXTERNAL_ASSET_ROOT')
        s=re.sub(r'(?i)[A-Z]:[\\/]Users[\\/][^\\/]+[\\/]','AUDITED_HOST/',s)
        for a,b in ordinal.items():s=s.replace(a,b)
        s=re.sub(r'("created":)\d+',r'\g<1>0',s)
        s=s.replace('leecdiang/HeteroSpec','ANON_REPOSITORY')
        return s
    def scrub(o):
        if isinstance(o,dict):return {k:scrub(v) for k,v in o.items() if k not in ['server_headers','git_author','author','committer']}
        if isinstance(o,list):return [scrub(v) for v in o]
        return clean(o) if isinstance(o,str) else o
    for p in stage.rglob('*'):
        if not p.is_file():continue
        if p.suffix=='.json':save(p,scrub(json.loads(p.read_text(encoding='utf-8'))))
        elif p.suffix=='.jsonl':p.write_bytes(b''.join(canonical(scrub(json.loads(line)))+b'\n' for line in p.read_bytes().splitlines()))
        elif p.suffix in ['.log','.txt','.md']:p.write_bytes(clean(p.read_bytes().decode('latin-1')).encode('latin-1'))
    # Derive new tape chains while preserving original frozen digests separately.
    tape_map={}
    for p in stage.rglob('tape.jsonl'):
        previous='0'*64;rows=[]
        for line in p.read_bytes().splitlines():
            row=json.loads(line);row.pop('event_sha256');row['previous_event_hash']=previous;row['event_sha256']=digest(canonical(row));previous=row['event_sha256'];rows.append(row)
        p.write_bytes(b''.join(canonical(row)+b'\n' for row in rows));tape_map[p.parent.name]=digest(p.read_bytes())
    for p in stage.rglob('record.json'):
        r=json.loads(p.read_text(encoding='utf-8'))
        if r['condition']=='H2_P_R':r['tape_sha256']=tape_map[r['run_id']]
        elif r['condition']=='R_ONLY':r['replayed_tape_sha256']=tape_map[r['run_id'].replace('R_ONLY','H2_P_R')]
        r['files']={name:{'bytes':(p.parent/name).stat().st_size,'sha256':digest((p.parent/name).read_bytes())} for name in r['files']};save(p,r)
    for folder in folders:
        p=stage/folder/'records.json'
        if p.exists():r=json.loads(p.read_text(encoding='utf-8'));r['runs']=[json.loads((stage/folder/'runs'/x['run_id']/'record.json').read_text(encoding='utf-8')) for x in r['runs']];save(p,r)
    predictions=stage/'metadata/RESERVED_PREDICTIONS.json'
    if predictions.exists():
        o=json.loads(predictions.read_text(encoding='utf-8'))
        for row in o['rows']:row['tape_sha256']=tape_map[row['runs']['H2_P_R']['run_id']]
        save(predictions,o)
    save(stage/'ORIGINAL_FROZEN_DIGESTS.json',{'original_files':originals,'original_complete_archive':json.loads((STUDY/'COMPLETE_ARCHIVE.json').read_text(encoding='utf-8')),'limit':'Original digests are references to the separately sealed package, not authentication of anonymized bytes.'})
    (stage/'ANONYMIZATION_LIMITS.md').write_text('Anonymous derived review capsule. Task IDs and input bytes retain public benchmark mapping. Full arrays and necessary tape/events support standard-library recomputation. Personal paths, usernames, Git author metadata and exact UTC/server time have been removed. Replacement dates encode ordinal order only and are not original times. Rehashed tapes/inventories are derived content, not original freeze bytes. Original frozen digests are retained separately. This capsule cannot independently prove remote chronology or authenticate omitted external model/runtime/driver bytes. The complete original evidence package remains unchanged.\n',encoding='utf-8')
    entries={p.relative_to(stage).as_posix():{'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in sorted(stage.rglob('*')) if p.is_file()};save(stage/'MANIFEST.json',{'schema':'RTX_H2_V2.anonymous_inventory','mode':'anonymous','content_head':'anonymous-derived','files':entries})
    temporary=ROOT/'work/anonymous-review.tar.gz'
    with tarfile.open(temporary,'w:gz',compresslevel=6) as tar:
        for p in sorted(stage.rglob('*')):
            if p.is_file():tar.add(p,arcname=p.relative_to(stage).as_posix(),recursive=False)
    h=digest(temporary.read_bytes());dest=ART/('anonymous-'+h+'.tar.gz');shutil.copyfile(temporary,dest);result=offline(dest);save(STUDY/'ANONYMOUS_REVIEW.json',{'status':'PASS','path':dest.relative_to(ROOT).as_posix(),'sha256':h,'bytes':dest.stat().st_size,'independent_offline_result':result,'limit':'Content recomputation only; replacement ordinal timestamps cannot prove original remote chronology.'});print(dest)
if __name__=='__main__':main()
