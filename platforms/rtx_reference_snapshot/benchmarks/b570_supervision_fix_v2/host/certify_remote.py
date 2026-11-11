"""Authenticate actual connector-delivered bytes at one pushed commit."""
import argparse,base64,hashlib
from pathlib import Path
from common import BASE,DESIGN,load,write_new,sha,need
p=argparse.ArgumentParser();p.add_argument('--payload',required=True);p.add_argument('--commit',required=True);a=p.parse_args()
f=DESIGN/'results/CONFIRMATION_FREEZE.json';freeze=load(f);payload=load(BASE/a.payload)
expected=dict(freeze['bound_files']);expected['results/CONFIRMATION_FREEZE.json']=sha(f);expected['results/REVIEW_STATUS.json']=freeze['review_status_sha256']
need(payload['commit']==a.commit,'remote commit identity mismatch')
need({r['path'] for r in payload['files']}==set(expected),'incomplete remote source/artifact set')
destination=BASE/'frozen_remote';destination.mkdir();members=[]
for row in payload['files']:
    data=base64.b64decode(row['content'],validate=True);digest=hashlib.sha256(data).hexdigest()
    need(digest==expected[row['path']],'remote byte drift '+row['path'])
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();need(blob==row['git_blob'],'remote Git blob mismatch')
    out=destination/row['path'];out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('xb') as f:f.write(data)
    members.append(dict(path=row['path'],bytes=len(data),sha256=digest,git_blob=blob,downloaded_path=out.relative_to(BASE).as_posix()))
write_new(DESIGN/'results/REMOTE_FREEZE.json',dict(remote_commit=a.commit,freeze_sha256=expected['results/CONFIRMATION_FREEZE.json'],members=members,payload_path=a.payload,payload_sha256=sha(BASE/a.payload),scope='Actual GitHub connector response bytes; SHA256 and Git blob SHA1 checked against prospective freeze; no confirmation started'))
print('certified',len(members),'remote members at',a.commit)
