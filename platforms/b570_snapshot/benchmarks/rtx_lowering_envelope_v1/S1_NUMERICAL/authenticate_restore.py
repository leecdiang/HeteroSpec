"""Authenticated same-commit byte download and new-directory CPU-only reanalysis."""
import argparse,csv,datetime,hashlib,importlib.util,json,subprocess,urllib.request,zipfile
from pathlib import Path,PurePosixPath

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);a=p.parse_args()
    source=Path(__file__).resolve().parent
    download=Path('D:/hs113-s1-numeric-authenticated-v1');download.mkdir(exist_ok=False)
    token=subprocess.run(['gh','auth','token'],capture_output=True,check=True).stdout.decode().strip();assert token
    files=[]
    for name in ('RAW_NUMERICAL_STOP.zip','RAW_MANIFEST.json','ANALYSIS.json','SLOT_STATUS.csv','analyze_failure.py','authenticate_restore.py'):
        endpoint='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/S1_NUMERICAL/'+name+'?ref='+a.commit
        request=urllib.request.Request(endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-immutable-byte-readback'})
        with urllib.request.urlopen(request,timeout=60) as response:
            assert response.status==200 and response.headers.get('Content-Encoding','identity')=='identity';data=response.read()
        with (download/name).open('xb') as f:f.write(data)
        assert data==(source/name).read_bytes()
        files.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),endpoint=endpoint))
    save(source/'AUTHENTICATED_RAW.json',dict(authenticated_commit=a.commit,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),authenticated_remote_bytes=True,files=files,transport='GitHub contents raw API, in-memory gh token, explicit identity encoding; credentials not recorded'))
    manifest=json.loads((download/'RAW_MANIFEST.json').read_bytes());archive=download/'RAW_NUMERICAL_STOP.zip'
    assert sha(archive)==manifest['sha256'] and archive.stat().st_size==manifest['bytes']
    restore=Path('D:/hs113-s1-numeric-fresh-restore-v1');restore.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        names=z.namelist();assert len(names)==len(set(names))==len(manifest['members'])
        assert set(names)=={m['path'] for m in manifest['members']}
        for name in names:
            path=PurePosixPath(name);assert not path.is_absolute() and '..' not in path.parts and ':' not in name and '\\' not in name
        z.extractall(restore)
    for m in manifest['members']:
        path=restore/m['path'];assert path.stat().st_size==m['bytes'] and sha(path)==m['sha256']
    spec=importlib.util.spec_from_file_location('restored_failure_analysis',restore/'code/analyze_failure.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);report=module.analyze(restore)
    save(restore/'RECOMPUTED_ANALYSIS.json',report)
    assert (restore/'RECOMPUTED_ANALYSIS.json').read_bytes()==(download/'ANALYSIS.json').read_bytes()==(restore/'expected/ANALYSIS.json').read_bytes()
    with (restore/'RECOMPUTED_SLOT_STATUS.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(report['slots'][0]));writer.writeheader();writer.writerows(report['slots'])
    assert (restore/'RECOMPUTED_SLOT_STATUS.csv').read_bytes()==(download/'SLOT_STATUS.csv').read_bytes()==(restore/'expected/SLOT_STATUS.csv').read_bytes()
    receipt=dict(status='PASS',authenticated_data_commit=a.commit,archive_sha256=manifest['sha256'],members_verified=len(manifest['members']),
                 destination=str(restore),analysis_and_720_slot_table_bytes_equal=True,started=report['numeric_hosts_started'],failed=report['numeric_hosts_failed'],not_started=719,
                 exception_capsule_audit='PASS: exception code, RIP/module RVA, IDIV RCX, RCX0, raw frequency0, frozen instruction bytes, source/linkage independently reconstructed',
                 limitation='Full original local process dump/WER are retained by path/hash, not published or remotely restored. No successful numerical output exists.',
                 new_native_GPU_hosts=0,new_graph_computes=0,new_model_requests=0,new_device_queries=0,external_auditor=False)
    save(source/'FRESH_RESTORE.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':main()
