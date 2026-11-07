"""Package settled transport receipts after complete fresh raw readback."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)


def main():
    p=argparse.ArgumentParser()
    for name in ('archive','upload','remote','out','operations','parent'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--snapshot',required=True);p.add_argument('--result-pr',required=True);p.add_argument('--pack-operation',default='PACK01');a=p.parse_args()
    assert not a.out.exists();index=read(a.archive/'RAW_ACCESS.json');uploaded=read(a.upload/'UPLOAD.json');verified=read(a.remote/'REMOTE_READBACK.json')
    index_hash=sha(a.archive/'RAW_ACCESS.json')
    assert index['status']=='LOCAL_ARCHIVE_READBACK_PASS'
    assert uploaded['status']=='UPLOAD_COMPLETE_NOT_YET_VERIFIED' and uploaded['raw_index_sha256']==index_hash
    assert verified['status']=='REMOTE_DOWNLOAD_AND_ALL_MEMBERS_READBACK_PASS' and verified['raw_index_sha256']==index_hash
    assert verified['parts']==uploaded['parts']==index['parts'] and verified['file_count']==len(index['files'])
    for receipt,name in [(uploaded,'parallel_upload.py'),(verified,'parallel_verify.py')]:
        assert receipt['script_sha256']==sha(a.parent/'diagnostics'/name)
    a.out.mkdir(parents=True);payload=a.out/'payload';payload.mkdir();entries=[]
    def copy(source,name):
        assert source.is_file() and not source.is_symlink() and source.suffix.lower() not in ('.gguf','.dll','.exe','.pem','.key','.zip')
        dest=payload/name;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();shutil.copy2(source,dest)
    for prefix,folder in [('upload',a.upload),('remote',a.remote)]:
        for f in sorted(folder.rglob('*')):
            if f.is_file():copy(f,Path(prefix)/f.relative_to(folder))
    # Release creation and source-snapshot commands settled before upload began.
    # Preserve these separate post-science receipts as well as the transfers.
    for f in sorted(a.upload.parent.iterdir()):
        if f.is_file() and f.suffix in ('.json','.log','.md'):
            copy(f,Path('release-setup')/f.name)
    for f in sorted(a.operations.iterdir()):
        if f.is_file() and f.name.startswith(('PACK','ARCHIVE','UPLOAD','REMOTE','CREATE_EVIDENCE','RELEASE','RESULT_PR')):
            copy(f,Path('operations')/f.name)
    code=Path(__file__).parent
    for name in ('pack_evidence.py','prepare_delivery_metadata.py','verify_delivery_metadata.py','finish_transport.py','publish_delivery.py'):
        copy(code/name,Path('source')/name)
    for name in ('parallel_upload.py','parallel_verify.py','remote_delivery.py'):
        copy(a.parent/'diagnostics'/name,Path('source/pinned-parent')/name)
    copy(a.parent/'archive.py',Path('source/pinned-parent/archive.py'))
    save(payload/'TRANSPORT_IDENTITY.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'result_pr':a.result_pr,'native_source_snapshot':a.snapshot,'raw_index_sha256':index_hash,'native_requests_added':0,
      'scope':'Transport receipts follow the immutable raw/source snapshot. All raw shards were freshly downloaded and every member rehashed. This is same-host delivery verification, not third-party replication.'})
    for f in sorted(payload.rglob('*')):
        if f.is_file():entries.append({'path':f.relative_to(payload).as_posix(),'bytes':f.stat().st_size,'sha256':sha(f)})
    save(a.out/'METADATA_MEMBERS.json',entries);archive=a.out/'TRANSPORT_METADATA.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for e in entries:z.write(payload/e['path'],e['path'])
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==len(entries) and set(z.namelist())=={e['path'] for e in entries}
        for e in entries:
            data=z.read(e['path']);assert len(data)==e['bytes'] and hashlib.sha256(data).hexdigest()==e['sha256']
    assert read(a.operations/(a.pack_operation+'.json'))['exit_code']==0
    for source,name in [(a.upload/'UPLOAD.json','UPLOAD.json'),(a.remote/'REMOTE_READBACK.json','REMOTE_READBACK.json'),(a.operations/(a.pack_operation+'.json'),'ARCHIVE_RECEIPT.json')]:
        shutil.copy2(source,a.out/name)
    names=('TRANSPORT_METADATA.zip','METADATA_MEMBERS.json','UPLOAD.json','REMOTE_READBACK.json','ARCHIVE_RECEIPT.json')
    save(a.out/'DELIVERY_ASSETS.json',{'status':'LOCAL_DELIVERY_METADATA_READBACK_PASS','tag':uploaded['tag'],'raw_index_sha256':index_hash,
      'assets':[{'name':n,'bytes':(a.out/n).stat().st_size,'sha256':sha(a.out/n)} for n in names],
      'metadata_members':len(entries),'native_requests_added':0,
      'note':'These separate post-archive receipts require their own fresh download and every-member verification before publication.'})
    print('DELIVERY_METADATA_READY',len(entries),flush=True)


if __name__=='__main__':main()
