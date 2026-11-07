import sys,os,json,hashlib,zipfile,time,urllib.request,subprocess,datetime
from pathlib import Path,PurePosixPath
root=Path("C:/hs/b570-capability-v1/fb20a198-4dc2-457a-9310-20a48ed30600");base=root/'delivery/post_manifest/remote-restore-20261018-01'
base.mkdir(exist_ok=False);out=base/'RAW_EVIDENCE.zip';begin=time.perf_counter_ns()
request=urllib.request.Request("https://raw.githubusercontent.com/leecdiang/HeteroSpec/80c1e0988ac694c109cada77318d5ddc983ce2b2/benchmarks/b570_pid_repair_v4/results/fb20a198-4dc2-457a-9310-20a48ed30600/RAW_EVIDENCE.zip",headers={'User-Agent':'HeteroSpec-CPU-evidence-recovery'})
with urllib.request.urlopen(request,timeout=60) as response,out.open('xb') as dest:
    status=response.status
    while True:
        block=response.read(1048576)
        if not block:break
        dest.write(block)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert out.stat().st_size==13269122 and digest(out)=='66371a66d8329799f037ec0bead71f966c5558137fb2144eeb8a082d5c08fd22'
extracted=base/'extracted';extracted.mkdir();verified=[]
with zipfile.ZipFile(out) as z:
    names=z.namelist();assert len(names)==len(set(names))==5281
    for n in names:
        p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts and ':' not in n and '\\' not in n
        info=z.getinfo(n);assert not ((info.external_attr>>16)&0o170000)==0o120000
    mr=z.read('delivery/EVIDENCE_MANIFEST.json');assert hashlib.sha256(mr).hexdigest()=='ddde566fa404ed1f52308f83cda57e0d47686b3283c9c1ca74aeca80cca2d2de'
    manifest=json.loads(mr);members=manifest['files']
    assert len(members)==5280 and len({x['path'] for x in members})==5280
    assert set(names)=={x['path'] for x in members}|{'delivery/EVIDENCE_MANIFEST.json'}
    for x in members:
        blob=z.read(x['path']);assert len(blob)==x['bytes'] and hashlib.sha256(blob).hexdigest()==x['sha256']
        p=extracted/x['path'];p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(blob)
        verified.append(x['path'])
    p=extracted/'delivery/EVIDENCE_MANIFEST.json'
    with p.open('xb') as f:f.write(mr)
isolated=base/'isolated-cwd';isolated.mkdir();command=[sys.executable,'-I','-S','-B',str(extracted/'delivery/RECONSTRUCT.py'),str(extracted)]
cp=subprocess.run(command,cwd=isolated,capture_output=True,timeout=120)
(base/'recompute.stdout.json').write_bytes(cp.stdout);(base/'recompute.stderr.log').write_bytes(cp.stderr)
assert cp.returncode==0,cp.stderr.decode(errors='replace')
expected=(extracted/'RECONSTRUCTED.json').read_bytes();assert cp.stdout==expected
record=dict(status='REMOTE_RESTORE_AND_RECOMPUTE_PASS',scope='Actual remote archive and unchanged blocked-task auditor only; not CPU8 qualification',
 remote_commit="80c1e0988ac694c109cada77318d5ddc983ce2b2",url="https://raw.githubusercontent.com/leecdiang/HeteroSpec/80c1e0988ac694c109cada77318d5ddc983ce2b2/benchmarks/b570_pid_repair_v4/results/fb20a198-4dc2-457a-9310-20a48ed30600/RAW_EVIDENCE.zip",http_status=status,
 archive_bytes=out.stat().st_size,archive_sha256=digest(out),manifest_sha256=hashlib.sha256(mr).hexdigest(),
 archive_members=len(names),verified_members=len(verified),recomputed_bytes=len(cp.stdout),
 expected_report_sha256=hashlib.sha256(expected).hexdigest(),recomputed_report_sha256=hashlib.sha256(cp.stdout).hexdigest(),byte_identical=True,
 downloaded_root=str(base),command=command,begin_ns=begin,end_ns=time.perf_counter_ns(),observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=cp.returncode,
 lifecycle_scope='Tool API plus actual Popen completion; independent OS FILETIME for delivery roots is UNKNOWN')
with (root/'delivery/post_manifest/REMOTE_RESTORE.json').open('x',encoding='utf8',newline='\n') as f:json.dump(record,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(record,sort_keys=True))
