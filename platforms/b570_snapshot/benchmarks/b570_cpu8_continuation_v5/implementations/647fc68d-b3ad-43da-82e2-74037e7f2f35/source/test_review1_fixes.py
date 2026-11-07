"""Production-path review fixes: real hardlinks/archive/restore, synthetic explicitly marked budget boundaries."""
import sys,tempfile,unittest,json,datetime,os,shutil,hashlib,zipfile,copy,base64
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'source'),str(R/'src/rev2')]
import campaign_budget as cb
from evidence_pack import write_manifest,archive
from evidence_contract import member,inventory,manifest_check
import delivery_audit as da
class Fixes(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=R/'tmp');self.addCleanup(self.tmp.cleanup);self.b=Path(self.tmp.name);self.r=self.b/'root';self.r.mkdir();self.ext=self.b/'external';self.ext.mkdir()
  self.origin='2026-10-18T15:00:00+00:00';self.put('ACQUISITION.json',dict(first_preparation_utc=self.origin));self.put('CAMPAIGN.json',dict(schema=1,first_preparation_utc=self.origin,external_root=str(self.ext),original_root=str(self.r),previous=[]))
 def put(self,p,x):p=self.r/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x)+'\n');return p
 def test_actual_hardlink_member_and_inventory(self):
  p=self.put('x.json',{});os.link(p,self.r/'alias')
  for action in [lambda:member(self.r,'x.json'),lambda:inventory(self.r),lambda:write_manifest(self.r)]:
   with self.assertRaises(ValueError):action()
 def test_actual_manifest_hardlink(self):
  write_manifest(self.r);os.link(self.r/'delivery/EVIDENCE_MANIFEST.json',self.ext/'alias')
  with self.assertRaisesRegex(ValueError,'hardlink'):manifest_check(self.r,'delivery/EVIDENCE_MANIFEST.json')
 def journal(self,n,life=1,duplicate=False):
  p=self.r/'processes/fixture/OS_EVENTS.jsonl';p.parent.mkdir(parents=True);born=int(datetime.datetime(2026,10,18,15,0,tzinfo=datetime.timezone.utc).timestamp()*1e7)+116444736000000000
  rs=[dict(event='OS_EXIT',pid=1000+i,created_filetime=born+i,exit_filetime=born+i+int(life*1e7)) for i in range(n)]
  if duplicate:rs+=rs
  p.write_text(''.join(json.dumps(x)+'\n' for x in rs))
 def test_synthetic_start_limit(self):
  self.journal(3001)
  with self.assertRaisesRegex(ValueError,'PROCESS_START'):cb.process_check(self.r)
 def test_synthetic_lifetime_limit(self):
  self.journal(1,21601)
  with self.assertRaisesRegex(ValueError,'LIFETIME'):cb.process_check(self.r)
 def test_duplicate_identity_and_admission(self):
  self.journal(2,2,True);x=cb.process_check(self.r,reserve_starts=2998);self.assertEqual((x['known_identities'],x['actual_covered_lifetime_seconds']),(2,4))
  with self.assertRaisesRegex(ValueError,'PROCESS_START'):cb.process_check(self.r,reserve_starts=2999)
 def test_unknown_exit_charged(self):
  self.journal(1);p=self.r/'processes/fixture/OS_EVENTS.jsonl';x=json.loads(p.read_text());x.pop('exit_filetime');p.write_text(json.dumps(x)+'\n')
  a=cb.process_check(self.r,now=datetime.datetime(2026,10,18,15,1,tzinfo=datetime.timezone.utc));self.assertGreater(a['unresolved_identity_duration_charge_seconds'],0);self.assertEqual(a['known_closed'],0)
 def test_large_projection_rejected(self):
  with self.assertRaisesRegex(ValueError,'STORAGE_RESERVE'):cb.archive_reservation(self.r,self.ext,450*1024**2,100)
 def test_third_archive_rejected(self):
  for n in ['a','b']:(self.ext/n).mkdir();(self.ext/n/'RAW_EVIDENCE.zip').write_bytes(b'x')
  with self.assertRaisesRegex(ValueError,'ARCHIVE_COPY'):cb.archive_reservation(self.r,self.ext,1,1)
 def test_unregistered_external_rejected(self):
  with self.assertRaisesRegex(ValueError,'unregistered'):cb.archive_reservation(self.r,self.b/'other',1,1)
 def test_boolean_delivery_is_not_proof(self):
  with self.assertRaisesRegex(ValueError,'restoration proof'):da.check(self.r,dict(restored=True,verified=True),'none','none',lambda _:None)
 def proof(self):
  self.put('CAPABILITY_FREEZE.json',dict(python=sys.executable,python_sha256=da.sha(sys.executable)));self.put('CAMPAIGN_SEAL_CONTEXT.json',dict(observed_utc=self.origin,storage=dict(fixture=True)));self.put('reports/CPU8_PREFIX.json',dict(status='PENDING_DELIVERY'));(self.r/'reports/CPU8_PREFIX.json').write_bytes(da.canonical(dict(status='PENDING_DELIVERY')))
  p=self.r/'source/recompute_cpu8.py';p.parent.mkdir();p.write_bytes(b'fixture packaged auditor identity\n')
  write_manifest(self.r);a=archive(self.r,self.ext/'archive');ap=self.ext/'archive/RAW_EVIDENCE.zip'
  down=self.ext/'download/RAW_EVIDENCE.zip';down.parent.mkdir();shutil.copyfile(ap,down)
  restored=self.ext/'restored';restored.mkdir()
  with zipfile.ZipFile(down) as z:z.extractall(restored)
  report=self.ext/'recomputed.json';report.write_bytes((self.r/'reports/CPU8_PREFIX.json').read_bytes())
  chunk=self.ext/'actual-download.b64';chunk.write_bytes(base64.b64encode(down.read_bytes()));data=chunk.read_bytes()
  ar=dict(a,path=str(ap));dr=dict(path=str(down),bytes=a['bytes'],sha256=a['sha256'],manifest_sha256=a['manifest_sha256'],remote_commit='fixture-not-real-network',transport='github_authenticated_blob_chunks',chunks=[dict(path=str(chunk),remote_blob_sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),sha256=da.sha(chunk),bytes=len(data))])
  rr=dict(root=str(restored),manifest_sha256=a['manifest_sha256'],archive_sha256=a['sha256'],driver_sha256=da.sha(p),exit_code=0,isolated_import=True,argv=[sys.executable,'-I','-S','-B',str(restored/'source/recompute_cpu8.py'),'--root',str(restored),'--run','fixture','--manifest','delivery/EVIDENCE_MANIFEST.json','--tool-binding','none','--output',str(report)],report_path=str(report),report_sha256=da.sha(report),manifest_members=len(json.loads((self.r/'delivery/EVIDENCE_MANIFEST.json').read_bytes())['files']))
  refs={}
  for name,value in [('archive',ar),('download',dr),('restore',rr)]:
   f=self.ext/(name+'.json');f.write_text(json.dumps(value));refs[name]=dict(path=str(f),sha256=da.sha(f))
  return dict(restoration_proof=refs,formal_run='fixture'),restored,down
 def test_actual_bytes_restore_and_recompute_path(self):
  c,_,_=self.proof();a=da.check(self.r,c,'delivery/EVIDENCE_MANIFEST.json','none',lambda _:dict(status='PENDING_DELIVERY'));self.assertEqual(a['status'],'DOWNLOADED_RAW_RECOMPUTED')
 def test_actual_download_tampering_rejected(self):
  c,_,p=self.proof();p.write_bytes(p.read_bytes()+b'bad')
  with self.assertRaisesRegex(ValueError,'byte count'):da.check(self.r,c,'delivery/EVIDENCE_MANIFEST.json','none',lambda _:dict(status='PENDING_DELIVERY'))
 def test_actual_restored_mutation_rejected(self):
  c,r,_=self.proof();(r/'ACQUISITION.json').write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'manifest member'):da.check(self.r,c,'delivery/EVIDENCE_MANIFEST.json','none',lambda _:dict(status='PENDING_DELIVERY'))
 def test_recomputed_result_mismatch_rejected(self):
  c,_,_=self.proof()
  with self.assertRaisesRegex(ValueError,'byte-identical'):da.check(self.r,c,'delivery/EVIDENCE_MANIFEST.json','none',lambda _:dict(status='forged'))
 def test_real_campaign_helper_relocated_bytes_identical(self):
  from verify_cpu8 import campaign_snapshot
  c,r,_=self.proof();self.assertEqual(campaign_snapshot(self.r),campaign_snapshot(r,relocated=True))
  with self.assertRaisesRegex(ValueError,'relocated read-only'):campaign_snapshot(r)
 def test_external_tool_budget_is_enforced(self):
  p=self.ext/'tools';p.mkdir();(p/'synthetic.intent.json').write_text(json.dumps(dict(registered_utc=self.origin,request=dict(cmd='synthetic'),unobserved_start_reserve=3001)))
  with self.assertRaisesRegex(ValueError,'PROCESS_START'):cb.process_check(self.r)
 def test_actual_chunk_mutation_rejected(self):
  c,_,_=self.proof();(self.ext/'actual-download.b64').write_bytes(b'bad')
  with self.assertRaisesRegex(ValueError,'chunk bytes'):da.check(self.r,c,'delivery/EVIDENCE_MANIFEST.json','none',lambda _:dict(status='PENDING_DELIVERY'))
 def test_full_argv_change_rejected(self):
  c,_,_=self.proof();ref=c['restoration_proof']['restore'];p=Path(ref['path']);r=json.loads(p.read_bytes());r['argv'][-5]='wrong';p.write_text(json.dumps(r));ref['sha256']=da.sha(p)
  with self.assertRaisesRegex(ValueError,'auditor argv'):da.check(self.r,c,'delivery/EVIDENCE_MANIFEST.json','none',lambda _:dict(status='PENDING_DELIVERY'))
 def test_external_receipt_boundary_rejected(self):
  c,_,_=self.proof();ref=c['restoration_proof']['archive'];p=self.b/'unaccounted.json';shutil.copyfile(ref['path'],p);ref['path']=str(p)
  with self.assertRaisesRegex(ValueError,'registered area'):da.check(self.r,c,'delivery/EVIDENCE_MANIFEST.json','none',lambda _:dict(status='PENDING_DELIVERY'))
 def terminal_fixture(self):
  now=datetime.datetime.now(datetime.timezone.utc);origin=now.isoformat();self.put('ACQUISITION.json',dict(first_preparation_utc=origin));self.put('CAMPAIGN.json',dict(schema=1,first_preparation_utc=origin,external_root=str(self.ext),original_root=str(self.r),previous=[]))
  self.put('tools/control.intent.json',dict(registered_utc=origin,request=dict(cmd='synthetic terminal fixture')));self.put('tools/control.initial.json',dict(response=dict(session_id=777)))
  p=self.put('tools/control.poll.json',dict(request=dict(session_id=777),response=dict(exit_code=0)));s=p.stat();bound=dict(target='tools/control.poll.json',sha256=da.sha(p),bytes=p.stat().st_size,session_id=777,file_birth_utc=datetime.datetime.fromtimestamp(s.st_ctime,datetime.timezone.utc).isoformat(),file_last_write_utc=datetime.datetime.fromtimestamp(s.st_mtime,datetime.timezone.utc).isoformat(),terminal_upper_bound_utc=datetime.datetime.fromtimestamp(max(s.st_ctime,s.st_mtime),datetime.timezone.utc).isoformat(),metadata_observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),api_observed_utc=None,os_exit_filetime=None)
  return self.put('tools/control.terminal-bound.json',bound)
 def test_real_ntfs_terminal_upper_bound(self):
  self.terminal_fixture();x=cb.process_check(self.r);self.assertLess(x['infrastructure_lifetime_upper_charge_seconds'],2);self.assertEqual(x['known_identities'],0)
 def test_terminal_bound_cannot_forge_api_or_os_exit(self):
  p=self.terminal_fixture();b=json.loads(p.read_bytes());b['api_observed_utc']=b['file_birth_utc'];p.write_text(json.dumps(b))
  with self.assertRaisesRegex(ValueError,'fabricated lifecycle'):cb.process_check(self.r)
if __name__=='__main__':unittest.main()
