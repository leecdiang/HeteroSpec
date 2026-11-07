"""One actual remote blob request. Credentials stay in memory and out of logs."""
import argparse,hashlib,json,subprocess,urllib.request
from pathlib import Path
from common import BASE,owned,load,write_new,need,now,task_storage
p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--blob',required=True);p.add_argument('--destination',required=True);p.add_argument('--sha256',required=True);p.add_argument('--bytes',required=True,type=int);a=p.parse_args()
dest=owned(a.destination);dest.mkdir(parents=True,exist_ok=False);out=dest/'RAW_EVIDENCE.zip'
need(sum(1 for _ in BASE.rglob('RAW_EVIDENCE.zip'))<2,'maximum two complete archive copies')
task_storage(projected=a.bytes+1024**2)
g='C:/hs/pr108-tools/git/cmd/git.exe'
credential=subprocess.run([g,'credential','fill'],input=b'protocol=https\nhost=github.com\n\n',capture_output=True)
fields={}
if credential.returncode==0:
    fields=dict(line.split('=',1) for line in credential.stdout.decode().splitlines() if '=' in line)
headers={'Accept':'application/vnd.github.raw+json','User-Agent':'HeteroSpec-PR117-CPU-evidence-restore'}
if fields.get('password'):headers['Authorization']='Bearer '+fields['password']
url='https://api.github.com/repos/leecdiang/HeteroSpec/git/blobs/'+a.blob
begin=now();h=hashlib.sha256();blob=hashlib.sha1(b'blob '+str(a.bytes).encode()+b'\0');count=0
with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=60) as response,out.open('xb') as f:
    status=response.status
    while True:
        block=response.read(1024**2)
        if not block:break
        count+=len(block);need(count<=a.bytes,'remote archive exceeds exact reservation');h.update(block);blob.update(block);f.write(block)
    f.flush();__import__('os').fsync(f.fileno())
need(count==a.bytes and h.hexdigest()==a.sha256 and blob.hexdigest()==a.blob,'remote archive identity mismatch')
write_new(dest/'DOWNLOAD.json',dict(commit=a.commit,git_blob=a.blob,url=url,http_status=status,bytes=count,sha256=h.hexdigest(),begin_ns=begin,end_ns=now(),credential_contents_recorded=False,attempts=1))
print('downloaded',count,'bytes from exact remote blob',a.blob)
