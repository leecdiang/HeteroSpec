"""Preserve every attempted P1 byte in a CAS; no native execution or scientific retry."""
import hashlib,json,pathlib,sys,zipfile,shutil,io
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from protocol import read_json,file_sha,encode
from raw_audit import audit
OUT=ROOT/'p1';HOST=ROOT/'_host';RUN=HOST/'run';BUDGET=4*1024**3

def size(p):return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
def save(p,x):
 with p.open('xb') as f:f.write(encode(x))
def main():
 close=read_json(RUN/'CLOSEOUT.json');assert not any(p.name=='P1_COMPLETE_CAS.zip' for p in HOST.glob('P1_COMPLETE_CAS.zip'))
 files=sorted([p for p in RUN.rglob('*') if p.is_file()]+[OUT/n for n in ('AUTHOR_APPROVAL.json','ANALYSIS_P1.json','ENDPOINTS_P1.json','VERIFY_WITNESSES.json','PRODUCER_STATE_OBSERVATIONS.json','EXECUTION_CONTRACT_AUDIT.json','analyze_p1.py','contract_audit.py','test_contract_audit.py')]+[ROOT/n for n in ('raw_audit.py','evidence_adapter.py','contracts.py','protocol.py')]+[ROOT/'p0'/n for n in ('F0_EXECUTION.json','PLAN_P1.json','RUNTIME.json','RAW_FIELD_SOURCES.json')])
 entries=[dict(path=str(p.relative_to(ROOT)).replace(chr(92),'/'),bytes=p.stat().st_size,sha256=file_sha(p)) for p in files];objects={x['sha256']:p for p,x in zip(files,entries)}
 manifest=dict(schema=1,phase='PR108_P1',F0_sha256=file_sha(ROOT/'p0/F0_EXECUTION.json'),files=entries,logical_files=len(entries),unique_objects=len(objects),model_weights_included=False,credentials_included=False,all_attempted_slots_retained=True,prior_P0_dependency='bb803c94f23af0e5ab4e250c52f74e0b60621a66',original_PR97_CAS_sha256='816b802f915373c861e754bba448048705ce790ee8a230e114fef8197079a530')
 archive=HOST/'P1_COMPLETE_CAS.zip'
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.writestr('MANIFEST.json',encode(manifest))
  for sha,p in sorted(objects.items()):
   assert size(RUN)+size(OUT)+archive.stat().st_size < BUDGET,'No output budget expansion during sealing';z.write(p,'objects/'+sha)
 save(OUT/'ARCHIVE_MANIFEST.json',manifest)
 raw_bytes=size(RUN);archive_bytes=archive.stat().st_size
 # Worst case includes archive + published chunks + one temporary reconstructed request.
 largest_slot=max((size(d) for d in RUN.iterdir() if d.is_dir()),default=0)
 assert raw_bytes+size(OUT)+2*archive_bytes+largest_slot+16*1024**2<BUDGET,'Cannot seal/restore within original4GiB; retain existing bytes and report limitation'
 parts_dir=OUT/'archive';parts_dir.mkdir(exist_ok=False);parts=[]
 with archive.open('rb') as f:
  i=0
  while data:=f.read(8*1024**2):
   p=parts_dir/('part-%04d.bin'%i);p.write_bytes(data);parts.append(dict(path=str(p.relative_to(OUT)).replace(chr(92),'/'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()));i+=1
 save(OUT/'ARCHIVE_PARTS.json',dict(archive_sha256=file_sha(archive),archive_bytes=archive_bytes,parts=parts))
 # Fresh sequential reconstruction bounds output size while restoring/auditing every slot.
 slots={s['slot']:s for s in read_json(ROOT/'p0/PLAN_P1.json')['slots']};runtime=read_json(ROOT/'p0/RUNTIME.json');valid=[];invalid=[];restored=0
 with zipfile.ZipFile(archive) as z:
  assert z.read('MANIFEST.json')==encode(manifest)
  for sha,p in objects.items():assert hashlib.sha256(z.read('objects/'+sha)).hexdigest()==sha
  for slot in sorted(d.name for d in RUN.iterdir() if d.is_dir()):
   temp=HOST/('p1-local-restore-'+slot);assert not temp.exists();temp.mkdir();assert temp.resolve().is_relative_to(HOST.resolve()) and temp!=HOST
   selected=[x for x in entries if x['path'].startswith('_host/run/'+slot+'/')]
   try:
    for row in selected:
     data=z.read('objects/'+row['sha256']);p=temp/pathlib.PurePosixPath(row['path']).name;assert len(data)==row['bytes'];p.write_bytes(data);assert file_sha(p)==row['sha256'];restored+=1
    if (temp/'NORMALIZED.json').exists():audit(temp,slots[slot],runtime);valid.append(slot)
    else:invalid.append(dict(slot=slot,reason='Original incomplete/invalid attempt retained; not promoted to completed evidence'))
   finally:
    resolved=temp.resolve();assert resolved.is_relative_to(HOST.resolve()) and resolved.name=='p1-local-restore-'+slot;shutil.rmtree(resolved)
 save(OUT/'LOCAL_RESTORE.json',dict(status='PASS_FRESH_SEQUENTIAL_LOGICAL_RESTORE_AND_RAW_AUDIT',archive_sha256=file_sha(archive),objects_rehashed=len(objects),restored_slot_files=restored,complete_slots_independently_audited=valid,incomplete_or_invalid_slots_retained=invalid,output_strategy='Each slot restored fresh and independently read before deleting only that owned temporary directory; no scientific start',native_starts_added=0,raw_bytes=raw_bytes,archive_bytes=archive_bytes,new_output_bytes_including_archive_and_chunks=size(RUN)+size(OUT)+archive_bytes,original_budget_bytes=BUDGET))
 print(json.dumps(dict(archive_bytes=archive_bytes,parts=len(parts),logical_files=len(entries),unique_objects=len(objects),audited_complete_slots=len(valid),retained_incomplete_slots=len(invalid))))
if __name__=='__main__':main()
