"""Non-circular complete raw package; no old worktree or model assets."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from common import BASE,DESIGN,load,sha,write_new,need,task_storage
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--ledger',required=True);p.add_argument('--audit',required=True);a=p.parse_args()
manifest=load(BASE/a.manifest);members={r['path']:r for r in manifest['members']}
task_storage(projected=2*(sum(r['bytes'] for r in members.values())+len(members)*512)+32*1024**2)
audit_data=(BASE/a.audit).read_bytes()
argument_data=(json.dumps(dict(auditor='repo/benchmarks/b570_zero_gpu_repair_v1/host/raw_audit.py',manifest=a.manifest,ledger=a.ledger,report='RAW_AUDIT.json',expected_report_sha256=hashlib.sha256(audit_data).hexdigest()),sort_keys=True,indent=2)+'\n').encode()
extra={'RAW_AUDIT.json':audit_data,'ARCHIVE_RUN.json':argument_data,a.manifest:(BASE/a.manifest).read_bytes()}
for name,data in extra.items():members[name]=dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
raw_manifest=dict(schema=1,scope='Every retained raw/archive member except this manifest itself; no recursive hash',members=[members[k] for k in sorted(members)])
manifest_data=(json.dumps(raw_manifest,sort_keys=True,indent=2)+'\n').encode()
out=DESIGN/'results/RAW_EVIDENCE.zip'
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in sorted(members):
        if name in extra:data=extra[name]
        else:data=(BASE/name).read_bytes()
        need(len(data)==members[name]['bytes'] and hashlib.sha256(data).hexdigest()==members[name]['sha256'],'input changed while archiving '+name)
        z.writestr(name,data)
    z.writestr('RAW_MANIFEST.json',manifest_data)
with (DESIGN/'results/RAW_MANIFEST.json').open('xb') as f:f.write(manifest_data)
write_new(DESIGN/'results/ARCHIVE.json',dict(bytes=out.stat().st_size,sha256=sha(out),members=len(members)+1,uncompressed_bytes=sum(r['bytes'] for r in members.values())+len(manifest_data),raw_audit_sha256=hashlib.sha256(audit_data).hexdigest(),auditor_sha256=sha(DESIGN/'host/raw_audit.py'),manifest_sha256=hashlib.sha256(manifest_data).hexdigest()))
print(json.dumps(load(DESIGN/'results/ARCHIVE.json')))
