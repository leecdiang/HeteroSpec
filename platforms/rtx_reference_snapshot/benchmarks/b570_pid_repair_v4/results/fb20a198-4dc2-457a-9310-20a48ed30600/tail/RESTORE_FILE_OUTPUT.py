import sys,os,json,hashlib,zipfile,subprocess,time,datetime
from pathlib import Path
root=Path("C:/hs/b570-capability-v1/fb20a198-4dc2-457a-9310-20a48ed30600");base=root/'delivery/post_manifest/remote-restore-20261018-02';extracted=base/'extracted'
begin=time.perf_counter_ns();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
archive=base/'RAW_EVIDENCE.zip';assert archive.stat().st_size==13269122 and sha(archive)=='66371a66d8329799f037ec0bead71f966c5558137fb2144eeb8a082d5c08fd22'
manifest=extracted/'delivery/EVIDENCE_MANIFEST.json';assert sha(manifest)=='ddde566fa404ed1f52308f83cda57e0d47686b3283c9c1ca74aeca80cca2d2de'
m=json.loads(manifest.read_bytes());members=m['files'];assert len(members)==5280 and len({r['path'] for r in members})==5280
actual={p.relative_to(extracted).as_posix() for p in extracted.rglob('*') if p.is_file()}
assert actual=={r['path'] for r in members}|{'delivery/EVIDENCE_MANIFEST.json'}
for row in members:
 p=extracted/row['path'];assert not p.is_symlink() and not p.is_junction() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
auditor=extracted/'delivery/RECONSTRUCT.py';auditor_hash=next(r['sha256'] for r in members if r['path']=='delivery/RECONSTRUCT.py');assert sha(auditor)==auditor_hash
cwd=base/'isolated-cwd-file-output';cwd.mkdir(exist_ok=False);output=base/'recompute.canonical.json'
command=[sys.executable,'-I','-S','-B',str(auditor),str(extracted),str(output)]
cp=subprocess.run(command,cwd=cwd,capture_output=True,timeout=120)
(base/'recompute-file.stdout.log').write_bytes(cp.stdout);(base/'recompute-file.stderr.log').write_bytes(cp.stderr)
assert cp.returncode==0,cp.stderr.decode(errors='replace')
expected=(extracted/'RECONSTRUCTED.json').read_bytes();actual=output.read_bytes();assert actual==expected
download=json.loads((base/'DOWNLOAD_RECEIPT.json').read_bytes())
record=dict(status='REMOTE_RESTORE_AND_RECOMPUTE_PASS',scope='Actual remote archive recovery and unchanged blocked-task auditor, not CPU8 acceptance',
 remote_commit=download['commit'],transport='20 actual authenticated GitHub connector chunks; reconstructed same immutable raw ZIP',
 archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),manifest_sha256=sha(manifest),archive_members=5281,verified_members=len(members),
 auditor_sha256=auditor_hash,expected_report_sha256=hashlib.sha256(expected).hexdigest(),recomputed_report_sha256=sha(output),recomputed_bytes=len(actual),byte_identical=True,
 command=command,exit_code=cp.returncode,begin_ns=begin,end_ns=time.perf_counter_ns(),observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 preserved_failures=['HTTP404 raw download','large connector response Transport closed','stdout CRLF byte mismatch with identical parsed JSON'],
 lifecycle_scope='Actual API/Popen completion; independent OS FILETIME for delivery roots UNKNOWN')
with (root/'delivery/post_manifest/REMOTE_RESTORE.json').open('x',encoding='utf8',newline='\n') as f:json.dump(record,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(record,sort_keys=True))
