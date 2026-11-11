"""Fresh extraction, every member hash, unchanged packaged auditor, byte equality."""
import argparse,hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath
from common import BASE,DESIGN,owned,load,sha,write_new,need,now,task_storage
p=argparse.ArgumentParser();p.add_argument('--download',required=True);p.add_argument('--remote-manifest',required=True);a=p.parse_args()
download=owned(a.download);root=download/'extracted';root.mkdir(exist_ok=False)
remote_bytes=(BASE/a.remote_manifest).read_bytes();expected=json.loads(remote_bytes.decode());members={r['path']:r for r in expected['members']}
need(len(members)==len(expected['members']),'duplicate manifest member')
dirs={str(p) for name in members for p in PurePosixPath(name).parents if str(p)!='.'}
task_storage(projected=sum(((r['bytes']+4095)//4096)*4096+1024 for r in members.values())+4096*len(dirs)+4*1024**2)
begin=now();verified=[]
with zipfile.ZipFile(download/'RAW_EVIDENCE.zip') as z:
    names=z.namelist();need(len(names)==len(set(names)) and set(names)==set(members)|{'RAW_MANIFEST.json'},'archive member set mismatch')
    need(z.read('RAW_MANIFEST.json')==remote_bytes,'embedded manifest differs from authenticated remote bytes')
    for name in names:
        rel=PurePosixPath(name);need(not rel.is_absolute() and '..' not in rel.parts and ':' not in name and '\\' not in name,'archive path escape')
        info=z.getinfo(name);need((info.external_attr>>16)&0xF000!=0xA000,'archive symlink forbidden')
        data=z.read(name)
        if name!='RAW_MANIFEST.json':
            row=members[name];need(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'member hash mismatch '+name);verified.append(name)
        dest=root/Path(*rel.parts);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f:f.write(data)
run=load(root/'ARCHIVE_RUN.json');auditor=root/run['auditor'];expected_report=(root/run['report']).read_bytes()
output=root/'RECOMPUTED_RAW_AUDIT.json';command=[sys.executable,'-B',str(auditor),'--root',str(root),'--manifest',run['manifest'],'--ledger',run['ledger'],'--output',str(output)]
with (download/'AUDITOR.stdout.log').open('xb') as fo,(download/'AUDITOR.stderr.log').open('xb') as fe:
    proc=subprocess.run(command,stdout=fo,stderr=fe,timeout=180,cwd=root)
need(proc.returncode==0,'packaged raw auditor failed')
actual=output.read_bytes();need(actual==expected_report,'reconstructed report differs byte-for-byte')
write_new(DESIGN/'results/REMOTE_RESTORE.json',dict(status='REMOTE_RESTORE_RECOMPUTATION_MATCH',download=str(download),members_verified=len(verified),embedded_manifest_sha256=hashlib.sha256(remote_bytes).hexdigest(),packaged_auditor_sha256=sha(auditor),auditor_exit_code=proc.returncode,expected_report_sha256=hashlib.sha256(expected_report).hexdigest(),recomputed_report_sha256=hashlib.sha256(actual).hexdigest(),byte_identical=True,begin_ns=begin,end_ns=now(),command=command,scope='Actual fresh remote archive; every retained member; unchanged packaged auditor; no missing evidence manufactured'))
print('restored and independently recomputed',len(verified),'members byte-for-byte')
