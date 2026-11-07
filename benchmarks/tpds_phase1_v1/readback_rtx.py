"""Authenticated selected raw-evidence readback and saved-state comparison.

No model execution; not a new qualification or external native replication.
"""
from host_rtx import *
import readback_delivery as remote
import deliver_rtx as delivery
import zipfile,zlib
from active_kv import parse
import qualification as q

remote.TAG=delivery.TAG;remote.ROOT=ROOT
DEST=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/phase192-readback')

def main():
    assert (ROOT/'GPU_STOP.json').exists() and not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    DEST.mkdir(exist_ok=False);began=time.monotonic();published=read(ROOT/'ARTIFACT_DELIVERY.json')
    for name in ('raw-evidence.zip.parts.json','rtx-phase1-source.zip','rtx-phase1-runtime.zip'):
        subprocess.run([remote.GH,'release','download',delivery.TAG,'--repo',remote.REPO,'--pattern',name,'--dir',str(DEST)],check=True)
        receipt=published['index_asset'] if name.endswith('.parts.json') else published['small_assets']['source' if 'source.zip' in name else 'runtime']
        assert (DEST/name).stat().st_size==receipt['bytes'] and sha(DEST/name)==receipt['sha256']
    with zipfile.ZipFile(DEST/'rtx-phase1-source.zip') as z:
        m=json.loads(z.read('SOURCE_ASSET_MANIFEST.json'))
        for n,r in m['files'].items():
            raw=z.read(n);assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
    with zipfile.ZipFile(DEST/'rtx-phase1-runtime.zip') as z:
        m=json.loads(z.read('RUNTIME_MANIFEST.json'))
        for h,r in m['blobs'].items():
            raw=z.read('blobs/'+h);assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==h
    reader=remote.RemoteParts(read(DEST/'raw-evidence.zip.parts.json'),DEST/'cache');records=[];restored={}
    paths=[]
    for arm in ('R','W_L4','W_P','L_L4','L_P'):
        base=ROOT/'runs'/('Qwen-v2-matrix-'+arm)/'native/q4-crossing/captures/771'
        paths.extend([base/'frontier.f32',base/'sequence.bin'])
    reference_result=ROOT/'runs/Qwen-v2-matrix-R/native/result.json';paths.append(reference_result)
    with zipfile.ZipFile(reader) as z:
        rows={str(Path(r['path'])).casefold():r for r in json.loads(z.read('FILES.json'))['files']}
        for i,p in enumerate(paths):
            row=rows[str(p).casefold()];dest=DEST/'restored'/str(i)/p.name;dest.parent.mkdir(parents=True)
            assert shutil.disk_usage(DEST).free-row['bytes']>=20*1024**3
            if row['sha256'] in restored:os.link(restored[row['sha256']],dest)
            else:
                h=hashlib.sha256();size=0
                with dest.open('xb') as f:
                    for chunk in row['chunks']:
                        raw=zlib.decompress(z.read('chunks/'+chunk[:2]+'/'+chunk));assert hashlib.sha256(raw).hexdigest()==chunk;h.update(raw);size+=len(raw);f.write(raw)
                assert size==row['bytes'] and h.hexdigest()==row['sha256'];restored[row['sha256']]=dest
            records.append(dict(original=row['path'],restored=str(dest),sha256=sha(dest),bytes=dest.stat().st_size))
    spec=q.profile(prior.native_fields(Path(records[-1]['restored']),['model_structure']),'Qwen')
    vectors=[Path(r['restored']).read_bytes() for r in records if r['original'].endswith('frontier.f32')]
    states=[parse(Path(r['restored']).read_bytes(),list(range(771)),spec)[0] for r in records if r['original'].endswith('sequence.bin')]
    assert len(vectors)==len(states)==5 and all(v==vectors[0] for v in vectors) and all(s==states[0] for s in states)
    put(ROOT/'ARTIFACT_READBACK.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=records,downloaded_parts=reader.downloads,small_asset_full_contents_hash_verified=True,all_downloaded_part_chunk_file_hashes_verified=True,full_requested_frontier_equal_all_four_arms=True,complete_active_KV_771_positions_all_layers_equal_all_four_arms=True,new_GPU_requests=0,scope='Selected retained q4 crossing GPU evidence and complete source/runtime asset bytes; not full raw-bundle download or external native replication.',wall_s=time.monotonic()-began,GPU_work_remained_stopped=True))
    print('Fresh authenticated download verified; original R/four saved GPU vector and active-KV comparisons equal',flush=True)

if __name__=='__main__':main()
