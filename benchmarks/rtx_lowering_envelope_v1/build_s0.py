"""Exact inherited toolchain; compile only, zero backend initialization."""
import json,subprocess,sys
from pathlib import Path
from s0_budget import ROOT,save
from recover_s0 import sha
def main():
    attempt=sys.argv[1] if len(sys.argv)>1 else 'R1'
    old=json.loads(Path('D:/hs104-e1-v1/NATIVE_BUILD.json').read_bytes());command=old['attempts'][0]['command'][:]
    source=ROOT/'native/source';build=ROOT/'native/build'
    command[command.index('-S')+1]=str(source);command[command.index('-B')+1]=str(build)
    assert sha(command[0])==old['cmake_sha256'];compiler=next(s.split('=',1)[1] for s in command if s.startswith('-DCMAKE_CXX_COMPILER='));assert sha(compiler)==old['compiler_sha256']
    commands=[('configure',command),('build',[command[0],'--build',str(build),'--target','lowering113','llama-server','native-cache113','-j','2'])]
    for label,cmd in commands:
        prefix=label+'-'+attempt
        save(ROOT/(prefix+'-START.json'),dict(command=cmd))
        with (ROOT/(prefix+'.stdout.log')).open('xb') as out,(ROOT/(prefix+'.stderr.log')).open('xb') as err:r=subprocess.run(cmd,stdout=out,stderr=err)
        save(ROOT/(prefix+'-EXIT.json'),dict(exit_code=r.returncode));assert r.returncode==0,label
    save(ROOT/('NATIVE_BUILD_'+attempt+'.json'),dict(status='BUILT_NOT_GPU_QUERIED',server_sha256=sha(build/'bin/llama-server.exe'),operator_sha256=sha(build/'bin/lowering113.exe'),cache_test_sha256=sha(build/'bin/native-cache113.exe'),cmake_sha256=old['cmake_sha256'],compiler_sha256=old['compiler_sha256'],commands=commands,new_GPU_model_device_query_starts=0))
    print(json.dumps(dict(status='BUILT_NOT_GPU_QUERIED')))
if __name__=='__main__':main()
