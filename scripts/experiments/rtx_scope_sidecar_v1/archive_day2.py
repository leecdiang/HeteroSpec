import sys,hashlib,stat,shutil,json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as c
import archive
root=Path('D:/rtx151-archives/main-day2-increment')
dayroot=c.DESIGN/'host_execution/day2'
status=c.s.read(dayroot/'DAY2_STATUS.json')
assert status['status']=='COMPLETE_DATE_AUDITED'
assert not root.exists(),'never replace an existing increment'
with c.exclusive('day2-increment-seal',3600) as deadline:
    attempts=c.s.read(c.MAIN/'ATTEMPTS.json')
    day=[a for a in attempts if a['date_slot']==2]
    assert len(day)==4 and all(a['status']=='COMPLETE' and a['cleanup_verified'] for a in day)
    sources={name:c.MAIN/name for name in ('REQUESTS.jsonl','ATTEMPTS.json','EXECUTION_IDENTITY.json','FREEZE_COMMIT.json','REFERENCES.json','Qwen-QUALIFICATION.json','SmolLM2-QUALIFICATION.json','LOCAL_PATHS.json')}
    for a in day:
        for p in (c.MAIN/'attempts'/a['attempt_id']).rglob('*'):
            if p.is_file():sources[p.relative_to(c.MAIN).as_posix()]=p
    for p in dayroot.rglob('*'):
        if p.is_file():sources['day2_closeout/'+p.relative_to(dayroot).as_posix()]=p
    root.mkdir();snapshot=root/'snapshot';snapshot.mkdir()
    c.check_room(root,sum(p.stat().st_size for p in sources.values())+20*1024**3)
    members=[]
    for rel,src in sorted(sources.items()):
        assert c.now()<deadline and src.suffix!='.tmp'
        dst=snapshot/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        before=src.stat();shutil.copyfile(src,dst);digest=c.sha(src)
        assert src.stat().st_size==before.st_size and src.stat().st_mtime_ns==before.st_mtime_ns
        assert c.sha(dst)==digest
        members.append({'path':rel,'bytes':dst.stat().st_size,'sha256':digest});dst.chmod(stat.S_IREAD)
    lookup={m['path']:m for m in members}
    pins=c.s.lines(dayroot/'RETAINED_PAYLOADS.jsonl')
    for p in pins:assert all(lookup[p['path']][k]==p[k] for k in ('bytes','sha256'))
    base={'release_tag':archive.TAG,'previous_increment':'main-day1-increment',
      'prerequisite_indices':[
        {'asset':'completed-through-day0.OBJECT_PARTS.json','sha256':'ae2fcd4a0333bb2d594a21d6e48b76f8ddb78d4162ccaa090eb72623a50fcbe0'},
        {'asset':'main-day1-increment.PARTS.json','sha256':'92b894fe54abd6c79fcf9c0350f7c3b5da5aa89821f6b4f2a55aa2d9bf29aed6'}],
      'restore':'Restore the verified main-through-day0 base into a new working copy, overlay the verified main-day1-increment, then overlay this increment. Root REQUESTS.jsonl and ATTEMPTS.json contain the complete 1288-request/14-attempt state and replace only the working copy versions. Preserve all immutable archive batches and earlier indices. Old raw payloads and provenance resolve from earlier batches; new date2 payloads resolve from this increment.'}
    c.save(root/'MEMBERS.json',{'schema':1,'label':'main-day2-increment','created_utc':c.now().isoformat(),
      'source':str(c.MAIN),'files':members,'source_bytes':sum(m['bytes'] for m in members),'source_attempts':day,
      'status':'IMMUTABLE_SNAPSHOT_HASH_VERIFIED','base':base,'new_requests':364,'total_main_requests':1288,
      'audited_new_payload_pins':len(pins),'models_and_dlls_included':False})
    print(json.dumps({'sealed_members':len(members),'bytes':sum(m['bytes'] for m in members),'audited_payloads':len(pins)}),flush=True)
archive.pack(root)
archive.transfer(root)
with c.exclusive('day2-index-readback',600):
    receipts=[]
    for name in ('MEMBERS.json','PARTS.json','REMOTE_READBACK.json'):
        asset='main-day2-increment.'+name
        c.subprocess.run(['gh','release','download',archive.TAG,'--repo',archive.REPOSITORY,'--pattern',asset,'--dir',str(root/'download-readback')],check=True,timeout=180)
        assert c.sha(root/'download-readback'/asset)==c.sha(root/name)
        receipts.append({'asset':asset,'sha256':c.sha(root/name),'downloaded_verified':True})
    c.save(root/'INDEX_READBACK.json',{'status':'ALL_THREE_INDEX_ASSETS_DOWNLOADED_VERIFIED','indices':receipts,'verified_utc':c.now().isoformat()})
    print('DAY2_ARCHIVE_AND_INDEX_READBACK_COMPLETE',flush=True)
