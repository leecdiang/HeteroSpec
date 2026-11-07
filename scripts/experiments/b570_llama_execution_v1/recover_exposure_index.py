"""Fetch the authenticated RTX159 raw member index; no model work or RTX writes."""
from pathlib import Path
import json,subprocess,sys,time,urllib.request,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from recover_release import SafeRedirect
from common import read,write,need,sha

def session():
    p=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True)
    credential=dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)
    def get(url,accept='application/vnd.github+json'):
        request=urllib.request.Request(url,headers={'Authorization':'Bearer '+credential['password'],'Accept':accept,'User-Agent':'HeteroSpec-B570-exposure-readback'})
        return urllib.request.build_opener(SafeRedirect).open(request,timeout=90)
    return get

def main(root):
    root=Path(root);pin=read(root/'RAW_ACCESS.json');get=session()
    with get('https://api.github.com/repos/leecdiang/HeteroSpec/releases/tags/rtx-reference-repair-v1-evidence-20261102') as r:release=json.load(r)
    write(root/'RELEASE.json',release);assets={x['name']:x for x in release['assets']};p=root/'FULL_RAW_ACCESS.json'
    with get(assets['RAW_ACCESS.json']['url']+'?readback='+str(time.time_ns()),'application/octet-stream') as r,p.open('xb') as f:
        while b:=r.read(4*1024**2):f.write(b)
    need(p.stat().st_size==pin['full_index_bytes'] and sha(p)==pin['full_index_sha256'],'authenticated complete index')
    print('verified full member index',flush=True)

if __name__=='__main__':main(sys.argv[1])
