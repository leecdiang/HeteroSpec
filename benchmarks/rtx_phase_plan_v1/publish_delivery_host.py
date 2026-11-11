"""Publish verified private-repository evidence; never changes repo visibility."""
from deliver_host import *
import datetime

def verify(path):
    a=next(a for a in release()['assets'] if a['name']==path.name)
    assert a['size']==path.stat().st_size and a['digest']=='sha256:'+sha(path)
    return dict(name=a['name'],bytes=a['size'],sha256=sha(path),url=a['browser_download_url'],asset_id=a['id'])

def main():
    began=time.monotonic();raw=json.loads((ROOT/'ARTIFACT_DELIVERY.json').read_bytes());assert raw['all_remote_digests_verified']
    index=OUT/'raw-evidence.zip.parts.json';old=index.read_bytes();assert hashlib.sha256(old).hexdigest()==raw['index_asset']['sha256']
    (OUT/'prepublication-parts-index.json').write_bytes(old);public=json.loads(old)
    for p in public['parts']:
        p['draft_url_observed']=p['url'];p['url']='https://github.com/'+REPO+'/releases/download/'+TAG+'/'+p['name']
    index.write_text(json.dumps(public,indent=2),encoding='utf8')
    subprocess.run([GH,'release','upload',TAG,str(index),'--repo',REPO,'--clobber'],check=True);verify(index)
    for name in ('restore_delivered_host.py','RESULTS.md','REPRODUCE.md'):upload(HERE/name)
    subprocess.run([GH,'release','edit',TAG,'--repo',REPO,'--draft=false','--latest=false'],check=True)
    state=release();assert not state['draft'] and state['prerelease'];assets={a['name']:a for a in state['assets']}
    for p in public['parts']:
        a=assets[p['name']];assert a['size']==p['bytes'] and a['digest']=='sha256:'+p['sha256'] and a['browser_download_url']==p['url']
    put(ROOT/'ARTIFACT_DELIVERY_PUBLISHED.json',dict(status='PUBLISHED_ALL_SERVER_DIGESTS_VERIFIED',published_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),release=state['html_url'],release_id=state['id'],target_commit=state['target_commitish'],parts=public['parts'],index_asset=verify(index),total_zip_bytes=raw['total_bytes'],logical_files=raw['logical_files'],logical_bytes=raw['logical_bytes'],unique_chunks=raw['unique_chunks'],stream_and_part_upload_wall_s=raw['delivery_wall_before_index_upload_s'],publication_wall_s=time.monotonic()-began,GPU_work_remained_stopped=True,repository_visibility_unchanged=True))
    print('Published and verified',state['html_url'],len(public['parts']),'parts',flush=True)

if __name__=='__main__':main()
