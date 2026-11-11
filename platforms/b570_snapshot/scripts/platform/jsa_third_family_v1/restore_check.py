"""Fresh hash-checked restore and independent CPU process, local or remote Git bytes."""
from freeze import *
import zipfile,uuid
def main(mode):
    archive=read(PUB/'ARCHIVE_MANIFEST.json')['private_author_archive' if mode=='local' else 'raw_scientific'];source=Path(archive['path']);root=REPO.parent/('third-family-restored-'+mode+'-'+uuid.uuid4().hex[:8]);root.mkdir(exist_ok=False)
    if mode=='remote':
        commit=head();tree=gh_json('repos/leecdiang/HeteroSpec/git/trees/'+commit+'?recursive=1');path='benchmarks/jsa_third_family_v1/RAW_EVIDENCE.zip';item=next(r for r in tree['tree'] if r['path']==path);blob=gh_json('repos/leecdiang/HeteroSpec/git/blobs/'+item['sha']);assert blob['encoding']=='base64';source=root/'remote-RAW_EVIDENCE.zip';source.write_bytes(base64.b64decode(blob['content']))
    assert sha(source)==archive['sha256'] and source.stat().st_size==archive['bytes']
    with zipfile.ZipFile(source) as z:
        index=json.loads(z.read('INDEX.json'))
        for name,row in index['files'].items():
            p=(root/name).resolve();assert p.is_relative_to(root.resolve()) and not p.exists();b=z.read(name);assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    repo=root/'repository';local=root/'third-family';out=root/'RESULTS_CPU_REPRODUCED.json'
    import sys
    run=subprocess.run([sys.executable,str(repo/'scripts/platform/jsa_third_family_v1/analyse.py'),str(out)],capture_output=True,timeout=240)
    (root/'CPU.stdout.txt').write_bytes(run.stdout);(root/'CPU.stderr.txt').write_bytes(run.stderr);assert run.returncode==0
    assert sha(out)==sha(PUB/'RESULTS.json')==sha(repo/'benchmarks/jsa_third_family_v1/RESULTS.json')
    source_proof=None
    if mode=='local':
        inv=read(local/'native/SOURCE_HASHES_FINAL.json')
        for name,h in inv.items():assert sha(local/'native/source'/name)==h
        source_proof={'source_files_verified':len(inv),'source_inventory_sha256':sha(local/'native/SOURCE_HASHES_FINAL.json'),'restored_server_sha256':sha(local/'native/build/bin/llama-server.exe')}
        assert source_proof['restored_server_sha256']==read(PUB/'NATIVE_BUILD.json')['binary_sha256']
    save(PUB/('RESTORE_'+mode.upper()+'.json'),{'status':'PASS','utc':now(),'mode':mode,'actual_authenticated_remote_bytes':mode=='remote','archive_sha256':sha(source),'restored_root':str(root),'logical_files_verified':len(index['files']),'independent_CPU_process_exit':run.returncode,'recomputed_results_sha256':sha(out),'exact_byte_reproduction':True,'private_source':source_proof,'remote_commit':head() if mode=='remote' else None})
    print('INDEPENDENT RESTORE PASS',mode,'files',len(index['files']),flush=True)
if __name__=='__main__':
    import sys
    main(sys.argv[1])
