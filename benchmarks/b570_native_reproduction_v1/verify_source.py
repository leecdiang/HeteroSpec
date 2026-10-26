"""Authenticate recovery against exact Git objects, never directory labels."""
from pathlib import Path
import argparse,hashlib,io,json,subprocess,zipfile
def check(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    check(not a.out.exists(),'Existing receipt');kit=Path(__file__).resolve().parent
    def blob(commit,path):return subprocess.check_output(['git','show',commit+':'+path],cwd=a.repo)
    checks=[]
    for commit,base,inside,local in [
      ('b5370cab7ce853d4b284e42e5515ffa50f1e8ce7','b570_gqa_admission_v1','query_head.h','native/query_head.h'),
      ('7e98e288b4137c998604a0809c7e956474967de1','b570_gqa_av_preserve_v1','candidate/ggml-vulkan.cpp','native/ggml-vulkan.cpp'),
      ('34787ab56f0ae8b533d18fe02db2d37e8ebb63a4','b570_spec_request_bridge_v1','candidate/llama-graph.cpp','native/llama-graph.cpp')]:
        archive=blob(commit,'benchmarks/'+base+'/SOURCE_SNAPSHOT.zip');data=zipfile.ZipFile(io.BytesIO(archive)).read(inside)
        check(data==(kit/local).read_bytes(),'Source mismatch '+local)
        checks.append({'commit':commit,'archive':'benchmarks/'+base+'/SOURCE_SNAPSHOT.zip','archive_sha256':hashlib.sha256(archive).hexdigest(),'member':inside,'delivered':local,'sha256':hashlib.sha256(data).hexdigest()})
    for name in ['INPUT_PANEL.json','MODEL_IDENTITY.json']:
        data=blob('51febaddcf49bb18565e568cf964a6e5c78876c9','benchmarks/b570_formal_request_v1/'+name)
        check(data==(kit/name).read_bytes(),'PR134 input mismatch '+name)
        checks.append({'commit':'51febaddcf49bb18565e568cf964a6e5c78876c9','delivered':name,'sha256':hashlib.sha256(data).hexdigest()})
    av=blob('7e98e288b4137c998604a0809c7e956474967de1','benchmarks/b570_gqa_av_preserve_v1/av-preserve.patch')
    check(av==(kit/'patches/02-av-preserve.patch').read_bytes(),'AV patch mismatch')
    r={'status':'SOURCE_RECOVERY_PASS','checks':checks,'av_patch_sha256':hashlib.sha256(av).hexdigest(),'upstream_commit':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2','numerical_qualification':False}
    a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(r['status'])
if __name__=='__main__':main()
