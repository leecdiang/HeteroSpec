"""Authenticated byte readback; token stays in memory and is never recorded."""
import datetime, hashlib, json, shutil, subprocess, urllib.request
from pathlib import Path

def main():
    b=Path(__file__).resolve().parent
    target=Path('D:/hs113-s1-authenticated-download-v2');target.mkdir(exist_ok=False)
    commit='b5e7b501138acbc7296cd02b25716169e66ea5b9'
    result=subprocess.run(['gh','auth','token'],capture_output=True,check=True)
    token=result.stdout.decode().strip();assert token
    files=[]
    for name in ('RAW_S1A.zip','RAW_MANIFEST.json','PREOUTPUT_SELECTION.json','ANALYSIS.json','restore_support.py'):
        endpoint='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/S1A/'+name+'?ref='+commit
        request=urllib.request.Request(endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-immutable-byte-readback'})
        with urllib.request.urlopen(request,timeout=60) as response:
            assert response.status==200
            assert response.headers.get('Content-Encoding','identity')=='identity'
            data=response.read()
        with (target/name).open('xb') as f:f.write(data)
        assert data==(b/name).read_bytes(),name
        files.append(dict(path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),endpoint=endpoint))
    receipt=dict(authenticated_commit=commit,authenticated_remote_bytes=True,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 transport='GitHub contents raw API with in-memory gh authentication and explicit identity encoding; token not recorded',
                 files=files,selection_sha256=hashlib.sha256((target/'PREOUTPUT_SELECTION.json').read_bytes()).hexdigest(),
                 census_archive_sha256=hashlib.sha256((target/'RAW_S1A.zip').read_bytes()).hexdigest(),
                 retained_transport_failure='control_history/readback-01: gh raw transform short source buffer; same immutable commit recovered, no scientific retry')
    for p in (b/'AUTHENTICATED_RAW.json',Path('D:/hs113-s1-v1/AUTHENTICATED_SELECTION.json')):
        with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,indent=2);f.write('\n')
    p=Path('D:/hs113-s1-v1/REMOTE_SELECTION_BYTES.json');assert not p.exists();shutil.copyfile(target/'PREOUTPUT_SELECTION.json',p)
    print(json.dumps({'authenticated_commit':commit,'verified_files':len(files),'selection_sha256':receipt['selection_sha256']}))
if __name__=='__main__':main()
