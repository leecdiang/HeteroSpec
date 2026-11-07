"""Authenticated GitHub readback of this lane, never any raw upload/GPU action."""
import base64,hashlib,json,subprocess,time
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
def main():
    repo=V.parents[1];head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();prefix=V.relative_to(repo).as_posix();arc=Path(str(root())+'-archive');attempts=[]
    def api(route):
        for i in range(3):
            begin=time.monotonic();p=subprocess.run(['gh','api',route],capture_output=True,timeout=40);attempts.append(dict(route=route,exit=p.returncode,seconds=time.monotonic()-begin,stderr=p.stderr.decode(errors='replace')))
            if p.returncode==0:return json.loads(p.stdout)
        raise RuntimeError('Git transport readback failed;no GPU retry')
    pr=api('repos/leecdiang/HeteroSpec/pulls/122');assert pr['draft'] and pr['head']['sha']==head
    expected={}
    for line in subprocess.check_output(['git','-C',str(repo),'ls-tree','-r',head,'--',prefix],text=True).splitlines():
        left,path=line.split('\t');mode,kind,h=left.split();assert kind=='blob';expected[path]=h
    remote={};queue=[prefix]
    while queue:
        folder=queue.pop();entries=api(f'repos/leecdiang/HeteroSpec/contents/{folder}?ref={head}')
        for x in entries:
            if x['type']=='dir':queue.append(x['path'])
            else:remote[x['path']]=x['sha']
    assert remote==expected,'scoped committed tree mismatch';actual={}
    for path,h in sorted(expected.items()):
        blob=api('repos/leecdiang/HeteroSpec/git/blobs/'+h);assert blob['encoding']=='base64';data=base64.b64decode(blob['content']);assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==h
        local=subprocess.check_output(['git','-C',str(repo),'show',head+':'+path]);assert data==local;actual[path]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),git_blob_sha1=h)
    for rel,x in load(V/'EXACT_ARTIFACTS.json').items():assert actual[prefix+'/'+rel]['sha256']==x['sha256'],'consumed artifact bytes not authenticated'
    again=api('repos/leecdiang/HeteroSpec/pulls/122');assert again['draft'] and again['head']['sha']==head
    save(arc/'GIT_DELIVERY_READBACK.json',dict(status='ALL_SCOPED_BLOBS_BYTE_EXACT',commit=head,files=len(actual),actual_downloads=len(actual),exact_consumed_artifacts=11,draft=True,remote_raw_uploaded=False,source='authenticated gh api GitHub contents/tree and every blob;compared actual downloaded bytes with local committed bytes',blobs=actual,transport_attempts=attempts));print('remote verified',head,len(actual),'downloaded blobs')
if __name__=='__main__':main()
