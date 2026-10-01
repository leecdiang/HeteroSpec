"""Read-only prerequisites and clean pinned headers; no inference."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'benchmarks/rtx_independent_proposal_replay_v2'
OLD=Path('C:/Users/ASUS/Documents/Codex/2026-09-30/an-zh-a/work/HeteroSpec')
def sha(data):return hashlib.sha256(data).hexdigest()
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
    reads=[]
    names=['PREREGISTRATION.md','protocol.json','asset_identity.json','runtime_freeze.json','RESERVED_SET.json','prediction/REPORT.md','prediction/REPORT.json','CLOSEOUT.md','CLOSEOUT.json','REPRODUCTION.md']
    names=['benchmarks/rtx_transfer_latency_v1/'+n for n in names]+['scripts/platform/rtx_transfer_latency_v1/'+n+'.py' for n in ['native','study','audit','verify_common','verify_prediction','verify_provenance']]
    names += ['docs/'+n for n in ['data_policy.md','experiment_protocol.md','reproduction.md']]
    names += [str(p.relative_to(OLD)).replace('\\','/') for p in (OLD/'benchmarks/rtx_direct_id_v2').glob('*') if p.is_file()]
    for n in names:
        b=(OLD/n).read_bytes();b.decode('utf-8-sig');reads.append({'path':n,'sha256':sha(b),'bytes':len(b),'source_head':'3d60ac010523bbb0bf5c9db879d221159473bf0e'})
    pr=ROOT/'work/pr41-readonly';pr.mkdir(exist_ok=True)
    for n in ['RESERVED_SET.json','FORMAL_EXECUTION.json','ENDPOINT_ANALYSIS.json']:
        path='benchmarks/b570_partition_intervention_v1/'+n
        response=subprocess.check_output(['gh','api',f'repos/leecdiang/HeteroSpec/contents/{path}?ref=61a1eb104d9bd1f6220a066d797dcc10dfed268d'])
        import base64
        blob=json.loads(response);b=base64.b64decode(blob['content']);(pr/n).write_bytes(b)
        reads.append({'path':path,'sha256':sha(b),'git_blob':blob['sha'],'bytes':len(b),'source_head':'61a1eb104d9bd1f6220a066d797dcc10dfed268d'})
    src=ROOT/'work/pinned-source';src.mkdir(exist_ok=True)
    tar=Path('C:/Users/ASUS/Documents/Codex/2026-09-28/files-pasted-by-the-user-you/work/llama-b10839-source.tar')
    with tarfile.open(tar) as t:t.extractall(src,filter='data')
    for n in ['tools/cli/cli.cpp','tools/cli/cli-context.cpp','tools/server/server-context.cpp','tools/server/server-common.cpp','common/speculative.cpp','common/sampling.cpp','common/common.cpp','common/chat.cpp','include/llama.h','src/llama-context.cpp','src/llama-memory.cpp','src/llama-batch.cpp']:
        p=src/n
        if p.exists():reads.append({'path':'llama.cpp/'+n,'sha256':sha(p.read_bytes()),'source_head':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2'})
    save(STUDY/'READ_RECEIPTS.json',{'utc':datetime.now(timezone.utc).isoformat(),'starting_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'read_receipts':reads,'source_archive_sha256':sha(tar.read_bytes()),'inference_executed':False})
    print('Prerequisites saved; no inference.')
if __name__=='__main__':main()
