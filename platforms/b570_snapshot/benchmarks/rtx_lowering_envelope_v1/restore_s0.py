"""New-directory native CPU reconstruction from authenticated archive bytes."""
import argparse,json,subprocess,zipfile
from pathlib import Path
from s0_budget import ROOT,save
from recover_s0 import sha
def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--manifest',required=True);p.add_argument('--destination',required=True);p.add_argument('--commit',required=True);a=p.parse_args()
    archive=Path(a.archive);manifest=json.loads(Path(a.manifest).read_bytes());assert sha(archive)==manifest['sha256'] and archive.stat().st_size==manifest['bytes']
    target=Path(a.destination);target.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist())==len(manifest['members'])
        for n in z.namelist():assert not Path(n).is_absolute() and '..' not in Path(n).parts
        z.extractall(target)
    for item in manifest['members']:
        p=target/item['path'];assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256']
    # This really executes the restored native GGML builder, with no backend
    # initialization or arithmetic compute, rather than reusing old PASS flags.
    command=[str(target/'native/build/bin/lowering113.exe'),'--cpu-registry',str(target/'DESCRIPTOR_PLAN.json'),str(target/'FRESH_CPU_REGISTRY.json')]
    r=subprocess.run(command,capture_output=True);(target/'FRESH_CPU.stdout.log').write_bytes(r.stdout);(target/'FRESH_CPU.stderr.log').write_bytes(r.stderr);assert r.returncode==0,r.stderr
    fresh=json.loads((target/'FRESH_CPU_REGISTRY.json').read_bytes());old=json.loads((target/'CPU_ACCEPTED/SUPPORT_REGISTRY_S0.json').read_bytes())
    assert fresh['records']==old['records'] and fresh['graphs']==1680 and fresh['graph_computes']==0 and fresh['GPU_initializations']==0
    assert all(not any(s in Path(m).name.lower() for s in ('nvcuda','cudart','cublas','ggml-cuda','cupti')) for m in fresh['modules'])
    receipt=dict(status='PASS',authenticated_data_commit=a.commit,archive_sha256=manifest['sha256'],members_verified=len(manifest['members']),
        destination=str(target),actual_restored_native_CPU_graphs=1680,full_node_records_equal=True,new_GPU_model_operator_device_queries=0,
        not_numerical_or_full_request_qualification=True,external_auditor=False)
    save(ROOT/'FRESH_RESTORE_ACCEPTANCE.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':main()
