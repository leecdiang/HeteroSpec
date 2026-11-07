"""Stage the completed evidence without changing any native observation."""
from pathlib import Path
import datetime, json, shutil, time, zipfile
from prepare import ROOT, read, write, item

started=time.monotonic();reg=read(ROOT/'REGISTRATION.json');dest=Path(reg['worktree'])/reg['result_path']
ledger=read(ROOT/'BUDGET_LEDGER.json');close=read(ROOT/'CLOSEOUT.json')
assert close['complete_matrix'] and len(ledger['sessions'])==9
now=datetime.datetime.now(datetime.timezone.utc)
used=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
elapsed=(now-datetime.datetime.fromisoformat(reg['owned_start_utc'])).total_seconds()
assert used<reg['budget']['storage_bytes'] and elapsed<reg['budget']['owned_seconds']
write('RESOURCE_RECEIPT.json',{
 'status':'NATIVE_LIMITS_PASS_HELPER_PROCESS_COUNT_NOT_INDEPENDENTLY_METERED',
 'recorded_utc':now.isoformat(),'owned_wall_seconds_through_delivery_staging':elapsed,
 'owned_wall_reservation_seconds':reg['budget']['owned_seconds'],
 'current_new_root_file_bytes':used,'storage_reservation_bytes':reg['budget']['storage_bytes'],
 'native_worker_starts':9,'native_completed_requests':156,
 'minimum_available_host_memory_bytes':min(x['minimum_available_host_bytes'] for x in ledger['sessions']),
 'enforced_native_process_commit_limit_bytes':reg['budget']['memory_bytes'],
 'all_native_process_timeouts_observed_within_fixed_limits':True,
 'other_process_reservation':128,'other_process_descendant_count':None,
 'other_process_count_independently_reconciled':False,
 'host_cpu_cost_boundary':'Compiler/control/auditor/coordination work is charged in conservative continuous owned wall and wrapper/packaging/auditor windows; individual helper descendants were not separately metered. Do not claim that128 helper processes were observed or fully reconciled.',
 'additional_native_execution':False})
note='\nOnly the nine native model workers have individual process receipts. Compiler/control/auditor/coordination costs use conservative owned wall and command-level evidence; individual helper descendants were not separately counted. The 128-other-process reservation is not independently reconciled. RESOURCE_RECEIPT.json records this limit on the full resource-accounting claim; the complete scientific panel and native safety/accounting checks remain separately reported.\n'
for name in ['RESULT.md','REPRODUCTION.md']:
 p=ROOT/name;p.write_text(p.read_text()+note,encoding='utf-8')
# Refresh the compact review archive after report edits, retaining all original native bytes.
with zipfile.ZipFile(ROOT/'COMPACT_EVIDENCE.zip') as z:
 members={name:z.read(name) for name in z.namelist()}
for p in ROOT.iterdir():
 if p.is_file() and p.suffix in ['.json','.md','.py','.csv'] and p.name not in ['COMPACT_MANIFEST.json','PACKAGE_MANIFEST.json']:
  members[p.name]=p.read_bytes()
with zipfile.ZipFile(ROOT/'COMPACT_EVIDENCE.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,data in members.items():z.writestr(name,data)
write('COMPACT_MANIFEST.json',item(ROOT/'COMPACT_EVIDENCE.zip'))
for mode,indices in [('E0',range(1)),('E1',range(4)),('E2',range(4))]:
 for i in indices:
  folder=dest/f'{mode}-{i}';folder.mkdir(exist_ok=True)
  shutil.copy2(ROOT/f'{mode}-{i}/result.json',folder/'result.json')
for p in ROOT.iterdir():
 if p.is_file() and p.name!='FULL_RAW_LOCAL.zip' and p.suffix in ['.json','.md','.py','.cpp','.inc','.patch','.csv','.zip','.log','.txt']:
  shutil.copy2(p,dest/p.name)
write('FINAL_STAGING_COST.json',{'cpu_parent_wall_seconds':time.monotonic()-started,
 'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_process_starts':0})
shutil.copy2(ROOT/'FINAL_STAGING_COST.json',dest/'FINAL_STAGING_COST.json')
manifest=[]
for p in sorted(dest.rglob('*')):
 if p.is_file() and p.name not in ['PACKAGE_MANIFEST.json','GIT_PAYLOAD_CHECK.json']:
  row=item(p);row['path']=str(p.relative_to(dest)).replace('\\','/');manifest.append(row)
(dest/'PACKAGE_MANIFEST.json').write_text(json.dumps({'files':manifest,'count':len(manifest)},indent=2)+'\n')
print('Staged',len(manifest),'files; native evidence unchanged; helper-count limitation explicit')
