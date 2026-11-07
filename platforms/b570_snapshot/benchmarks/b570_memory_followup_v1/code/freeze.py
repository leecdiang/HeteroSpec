"""F0A transport and exact actual remote Git blob readback, before token forward."""
from common import *
import shutil,zipfile,sys
def publish():
 assert load(R/'PLAN_REMOTE_READBACK.json')['status']=='PASS' and load(R/'ASSET_CHECKS.json')['status']=='ASSET_BYTES_PASS' and load(R/'VOCAB_CHECKS.json')['status']=='PASS'
 assert load(R/'NATIVE_NEGATIVE_GUARDS.json')['negative_cases']==12
 if (R/'LEDGER.jsonl').exists():assert not any(json.loads(s)['event']=='REQUEST_START' for s in (R/'LEDGER.jsonl').read_text().splitlines())
 files={}
 shutil.copyfile(R/'LEDGER.jsonl',R/'PRE_FORWARD_LEDGER.jsonl')
 for folder in ['code','native','build/Release','dependencies','vocab','versions','probes','source-blobs']:
  for p in sorted((R/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pdb','.obj','.ilk','.exp']:
    files[p.relative_to(R).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
 for name in ['HELDOUT_POOL_RESERVATION.json','PRE_FORWARD_LEDGER.jsonl','ENDPOINT_NEGATIVE_TESTS.json','PIN_POLICY.json','ASSET_CHECKS.json','VOCAB_CHECKS.json','ENGINEERING_INPUTS.json','SYNTHETIC_INPUTS.json','PLAN_REMOTE_READBACK.json','NATIVE_NEGATIVE_GUARDS.json','HISTORY_AUDIT.json','HISTORY_CATALOG.json','MANDATORY_EXCLUSIONS.json','INHERITED_RECHECK.json','SOURCE_RECHECK.json','PR86_FRESH_RESTORE.json','DATASET_BINDINGS.json','HOST_INVENTORY.json']:
  p=R/name;files[name]=dict(bytes=p.stat().st_size,sha256=sha(p))
 f=dict(schema='heterospec.b570.memory.followup.F0A.v1',utc=now(),design_head='ab9dc1f935618931c3779f46a95f3b056b707457',policy=load(DOC/'POLICY.json'),files=files,model_forwards_before_freeze=0,mode_definition={'native_greedy':'Unrepaired native greedy draft and batched target k+1 verification using prefill UB.','vulkan_batched_repair':'Inherited live phase binding of target continuation to physical UB1, with logical k+1 output batches. Full continuation target partition repair; all rows, no selective mask or future reference.','matched':'No draft; same target context capacity4 and mode-specific target partition/pre-fill.','ordinary':'Same exact profile target, ordinary one output capacity1; UB grid32/128/512; stock128.'},capacity={'ordinary':1,'all_candidates_and_matched':4,'draft':1},residency_status='UNKNOWN_NO_PHYSICAL_WEIGHT_KV_OR_PAGING_CERTIFICATION',formal_admission='REFUSED_UNLESS_ACTUAL_RESIDENCY_AND_FULL_ENGINEERING_GATES_PASS',engineering_controller='Serial fixed two-repeat12-task grid; source versions and paid failures retained. No automatic retries.',confirmation_implementation='NOT_YET_IMPLEMENTED_NOT_ADMITTED',candidate_space={p:[dict(draft=q,mode=m,k_max=k) for q in x['draft_assets'] for m in ['native_greedy','vulkan_batched_repair'] for k in [1,2,3]] for p,x in load(DOC/'POLICY.json')['profiles'].items()},diagnostic_stop_scope='Raw engineering collection can proceed on UNKNOWN; no qualified candidate/F0B/speedup claim from those records.')
 save(R/'F0A.json',f);PUBLIC.mkdir(parents=True,exist_ok=True);(PUBLIC/'.gitattributes').write_text('* -text\n*.log whitespace=-blank-at-eol\n')
 for name in ['F0A.json','ASSET_CHECKS.json','VOCAB_CHECKS.json','ENGINEERING_INPUTS.json','SYNTHETIC_INPUTS.json','PLAN_REMOTE_READBACK.json','NATIVE_NEGATIVE_GUARDS.json','MANDATORY_EXCLUSIONS.json','PR86_FRESH_RESTORE.json','HOST_INVENTORY.json']:
  shutil.copyfile(R/name,PUBLIC/name)
 for folder in ['code','native']:
  for p in (R/folder).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:
    rel=p.relative_to(R);dest=PUBLIC/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 # Exact binary/vocabulary/compile dependency bytes travel as a hash-bound archive.
 transport=R/'f0a-transport.zip'
 with zipfile.ZipFile(transport,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for rel in files:z.write(R/rel,rel)
 art=REPO/'artifacts/b570_memory_followup_v1/f0a';art.mkdir(parents=True,exist_ok=True);parts=[]
 with transport.open('rb') as src:
  while b:=src.read(48*1024*1024):
   h=hashlib.sha256(b).hexdigest();p=art/(h+'.part');p.write_bytes(b);parts.append(dict(path=p.relative_to(REPO).as_posix(),bytes=len(b),sha256=h))
 save(PUBLIC/'F0A_TRANSPORT.json',dict(archive_sha256=sha(transport),archive_bytes=transport.stat().st_size,parts=parts,files=files))
 (art/'.gitattributes').write_text('*.part -text\n')
 print('F0A materialized',len(files),'files;',transport.stat().st_size,'transport bytes',flush=True)
def readback(dest):
 dest=Path(dest);assert not dest.exists();head=git('rev-parse','HEAD').decode().strip();branch=git('branch','--show-current').decode().strip()
 subprocess.run(['git','clone','--filter=blob:none','--depth','1','--single-branch','--branch',branch,'--no-checkout','https://github.com/leecdiang/HeteroSpec.git',str(dest)],check=True)
 assert git('rev-parse','HEAD',cwd=dest).decode().strip()==head
 paths=git('ls-tree','-r','--name-only',head,'benchmarks/b570_memory_followup_v1','artifacts/b570_memory_followup_v1').decode().splitlines();rows=[]
 for rel in paths:
  b=git('show',head+':'+rel,cwd=dest);assert b==(REPO/rel).read_bytes()==git('show',head+':'+rel);rows.append(dict(path=rel,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
 meta=load(PUBLIC/'F0A_TRANSPORT.json');buf=bytearray()
 for part in meta['parts']:
  b=git('show',head+':'+part['path'],cwd=dest);assert len(b)==part['bytes'] and hashlib.sha256(b).hexdigest()==part['sha256'];buf.extend(b)
 assert len(buf)==meta['archive_bytes'] and hashlib.sha256(buf).hexdigest()==meta['archive_sha256']
 archive=dest/'ACTUAL_REMOTE_F0A.zip';archive.write_bytes(buf);restore=dest/'ACTUAL_F0A_RESTORED';restore.mkdir()
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None and set(z.namelist())==set(meta['files'])
  for rel,m in meta['files'].items():
   b=z.read(rel);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'] and b==(R/rel).read_bytes();p=restore/rel;assert p.resolve().is_relative_to(restore.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 save(R/'F0A_REMOTE_READBACK.json',dict(status='PASS',utc=now(),head=head,files=rows,frozen_logical_files_restored=len(meta['files']),all_frozen_bytes_restored_from_actual_remote_Git=True,fresh_remote_repository=str(dest),model_forwards=0))
 shutil.copyfile(R/'F0A_REMOTE_READBACK.json',PUBLIC/'F0A_REMOTE_READBACK.json');print('ACTUAL F0A remote readback PASS',head,len(rows),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='publish':publish()
 else:readback(sys.argv[2])
