"""Push only additive study artifacts in bounded, recoverable Git batches."""
import time
from common import *
def push():
    for attempt in [1,2,3]:
        p=subprocess.Popen(['git','push','origin','codex/rtx-target-only-bridge-v1'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        try:output=p.communicate(timeout=180)[0]
        except subprocess.TimeoutExpired:
            if p.poll() is None:subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            output=p.communicate()[0]
        status={'commit':git('rev-parse','HEAD'),'attempt':attempt,'exit_code':p.returncode,'output':output.decode('utf-8',errors='replace'),'utc':now()}
        log=OUT/'PUBLISH_LEDGER.jsonl'
        with log.open('ab') as f:f.write(canon(status)+b'\n');f.flush();os.fsync(f.fileno())
        print(json.dumps(status),flush=True)
        if p.returncode==0:return
        if attempt<3:time.sleep(5)
    raise RuntimeError('bounded publication push failed; commits and payload retained')
def commit(message):
    diff=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT)
    if diff.returncode:
        subprocess.run(['git','commit','-m',message],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    push()
def main():
    index=load(ROOT/'artifacts/rtx_target_only_bridge_v1/ARCHIVE.json');manifest=load(ROOT/'artifacts/rtx_target_only_bridge_v1/MANIFEST.json')
    assert all(pathlib.PurePosixPath(n).suffix.lower() not in ['.exe','.dll','.gguf','.onnx','.pt','.safetensors'] for n in manifest['files'])
    subprocess.run(['git','add','--sparse','--','scripts/platform/rtx_target_only_bridge_v1','benchmarks/rtx_target_only_bridge_v1','artifacts/rtx_target_only_bridge_v1/.gitattributes','artifacts/rtx_target_only_bridge_v1/ARCHIVE.json','artifacts/rtx_target_only_bridge_v1/MANIFEST.json'],cwd=ROOT,check=True)
    commit('Report complete 171-run RTX bridge study and independent verification')
    for offset in range(0,len(index['parts']),2):
        batch=index['parts'][offset:offset+2]
        for b in batch:assert sha(ROOT/b['path'])==b['sha256']
        subprocess.run(['git','add','--sparse','--',*[b['path'] for b in batch]],cwd=ROOT,check=True)
        commit(f"Archive RTX bridge raw evidence parts {offset+1}-{offset+len(batch)}")
    save(OUT/'PUBLISHED.json',{'commit':git('rev-parse','HEAD'),'parts':len(index['parts']),'archive_sha256':index['sha256'],'utc':now()})
if __name__=='__main__':main()
