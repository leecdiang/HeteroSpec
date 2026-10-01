"""Remote checkpoint receipts, exact Git membership and content retrieval."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from prepare import ROOT,STUDY,save
from engine import now,digest
BRANCH='experiment/rtx-independent-proposal-replay-v2'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def manifest(checkpoint):
    names=git('ls-files','scripts/platform/rtx_independent_proposal_replay_v2','benchmarks/rtx_independent_proposal_replay_v2').decode().splitlines()
    files={n:{'sha256':digest((ROOT/n).read_bytes()),'bytes':(ROOT/n).stat().st_size} for n in names if 'REMOTE_RECEIPT' not in n and not n.endswith('_MANIFEST.json')}
    save(STUDY/(checkpoint+'_MANIFEST.json'),{'checkpoint':checkpoint,'created_utc':now(),'files':files,'binary_asset_manifest_sha256':digest((STUDY/'ASSET_ENVIRONMENT_BEFORE.json').read_bytes()),'source_identity_limit':'source membership proves Git content relationships; local timestamps are not independent server times'})
def receipt(checkpoint,retrieve=None):
    head=git('rev-parse','HEAD').decode().strip();subprocess.run(['git','push','--set-upstream','origin',BRANCH],cwd=ROOT,check=True)
    remote=git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
    if remote!=head:raise RuntimeError('remote ref differs')
    response=subprocess.check_output(['gh','api','-i',f'repos/leecdiang/HeteroSpec/git/commits/{head}'])
    text=response.decode('utf-8');header,body=text.split('\r\n\r\n' if '\r\n\r\n' in text else '\n\n',1);obj=json.loads(body)
    tree=json.loads(subprocess.check_output(['gh','api',f'repos/leecdiang/HeteroSpec/git/trees/{obj["tree"]["sha"]}?recursive=1']))
    remote_blobs={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'}
    local={}
    m=json.loads((STUDY/(checkpoint+'_MANIFEST.json')).read_text(encoding='utf-8'))
    for n,v in m['files'].items():
        b=git('show',head+':'+n);blob=git('rev-parse',head+':'+n).decode().strip()
        if digest(b)!=v['sha256'] or remote_blobs.get(n)!=blob:raise RuntimeError('remote source membership/content mismatch '+n)
        local[n]={'git_blob':blob,**v}
    headers={}
    for line in header.splitlines():
        if ':' in line:
            k,v=line.split(':',1)
            if k.lower() in ['date','etag','x-github-request-id']:headers[k.lower()]=v.strip()
    r={'checkpoint':checkpoint,'commit':head,'remote_ref':remote,'remote_ack_utc':now(),'server_headers':headers,'tree_sha':obj['tree']['sha'],'files':local,'manifest_sha256':digest((STUDY/(checkpoint+'_MANIFEST.json')).read_bytes()),'chronology_limit':'Git ancestry/content and a server response Date are retained. Response receipt time uses host clock; server Date resolution and request latency are not a trusted per-process timestamp service.'}
    if retrieve:
        path=Path(retrieve);name=path.relative_to(ROOT).as_posix();blob=remote_blobs[name]
        payload=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',f'repos/leecdiang/HeteroSpec/git/blobs/{blob}'])
        # GitHub blob API may return a JSON wrapper despite negotiated raw media.
        if payload.startswith(b'{'):
            import base64
            candidate=json.loads(payload)
            if 'content' in candidate:payload=base64.b64decode(candidate['content'])
        if digest(payload)!=digest(path.read_bytes()):raise RuntimeError('remote frozen prediction archive retrieval/hash failed')
        r['retrieved_content']={'path':name,'git_blob':blob,'sha256':digest(payload),'bytes':len(payload),'retrieved_utc':now()}
        # Include the exact archive in the Git Merkle proof, not only its declaration.
        local[name]={'git_blob':blob,'sha256':digest(payload),'bytes':len(payload)}
    # Archive exact frozen file bytes and raw Git Merkle objects for offline membership.
    snapshot=ROOT/'work/frozen-checkpoints'/checkpoint;snapshot.mkdir(parents=True,exist_ok=False)
    proof={'commit':head,'root_tree':obj['tree']['sha'],'trees':{}}
    (snapshot/'commit.object').write_bytes(git('cat-file','commit',head))
    directories={''}
    for name in local:
        dest=snapshot/'files'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(git('show',head+':'+name))
        parent=Path(name).parent
        while str(parent)!='.':directories.add(parent.as_posix());parent=parent.parent
    for directory in sorted(directories):
        tree_sha=obj['tree']['sha'] if not directory else git('rev-parse',head+':'+directory).decode().strip()
        b=git('cat-file','tree',tree_sha);dest=snapshot/'trees'/(tree_sha+'.object');dest.parent.mkdir(exist_ok=True);dest.write_bytes(b);proof['trees'][directory]=tree_sha
    save(snapshot/'GIT_MEMBERSHIP.json',proof);r['git_membership_proof']='frozen-checkpoints/'+checkpoint
    save(STUDY/(checkpoint+'_REMOTE_RECEIPT.json'),r);print(json.dumps({'checkpoint':checkpoint,'commit':head,'ack_utc':r['remote_ack_utc']}));return r
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['manifest','receipt']);p.add_argument('checkpoint',choices=['F0','F1','F2']);p.add_argument('--retrieve',type=Path);a=p.parse_args();manifest(a.checkpoint) if a.mode=='manifest' else receipt(a.checkpoint,a.retrieve)
