from pathlib import Path
import json,hashlib,subprocess,os,time,datetime,zipfile,shutil
root=Path('E:/rtx160/transport01');out=root/'download_probe01';out.mkdir();downloads=out/'downloads';downloads.mkdir();name='evidence-160.zip';index_path=Path('F:/rtx160/archive01/RAW_ACCESS.json');index=json.loads(index_path.read_text(encoding='utf-8'));pin=next(p for p in index['parts'] if p['name']==name);assert shutil.disk_usage(out).free>pin['bytes']+20*2**30
args=['gh','release','download','rtx-llama-repair-v1-evidence-20261102','--repo','leecdiang/HeteroSpec','--dir',str(downloads),'--pattern',name]
start=time.monotonic()
with (out/'DOWNLOAD.log').open('xb') as log:
 proc=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,GODEBUG='http2client=0'))
 try:code=proc.wait(timeout=600)
 except subprocess.TimeoutExpired:proc.kill();proc.wait();code=-1
seconds=time.monotonic()-start
receipt={'argv':args,'pid':proc.pid,'exit_code':code,'seconds':seconds,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_requests_added':0,'scope':'One-part timing probe only; does not replace any required full remote verification.'}
(out/'COMMAND.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');shutil.copy2(out/'COMMAND.json',root/'DOWNLOAD_ETA_PROBE_COMMAND01.json');shutil.copy2(out/'DOWNLOAD.log',root/'DOWNLOAD_ETA_PROBE_LOG01.log');assert code==0
f=downloads/name;h=hashlib.sha256()
with f.open('rb') as stream:
 for block in iter(lambda:stream.read(4194304),b''):h.update(block)
assert f.stat().st_size==pin['bytes'] and h.hexdigest()==pin['sha256']
verify_start=time.monotonic();members={e['path']:e for e in index['files'] if e['part']==name}
with zipfile.ZipFile(f) as z:
 assert len(z.namelist())==len(members) and set(z.namelist())==set(members)
 for name,e in members.items():
  h=hashlib.sha256();size=0
  with z.open(name) as stream:
   for block in iter(lambda:stream.read(1048576),b''):h.update(block);size+=len(block)
  assert size==e['bytes'] and h.hexdigest()==e['sha256']
result={'status':'SINGLE_PART_DOWNLOAD_AND_ALL_MEMBERS_CHECKED_FOR_ETA_ONLY','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'part':pin,'download_seconds':seconds,'verification_seconds':time.monotonic()-verify_start,'verified_members':len(members),'single_stream_gib_per_hour':pin['bytes']/2**30/seconds*3600,'raw_index_sha256':hashlib.sha256(index_path.read_bytes()).hexdigest(),'native_requests_added':0,'scope':'Measured while uploads continue. One observation is an estimate, not guaranteed sustained speed. The mandatory complete fresh remote readback still includes every shard.'}
(out/'PROBE.json').write_text(json.dumps(result,indent=2),encoding='utf-8');shutil.copy2(out/'PROBE.json',root/'DOWNLOAD_ETA_PROBE01.json');print(json.dumps(result))
