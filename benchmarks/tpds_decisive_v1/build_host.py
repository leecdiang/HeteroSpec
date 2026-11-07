"""Original-host derivative builds; no numerical qualification asserted."""
from pathlib import Path
import json,hashlib,subprocess,time,shutil
OLD=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/native-original-v4')
ROOT=Path('F:/rtx184')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2)
def main():
    binding=json.loads((OLD/'BUILD.json').read_bytes())
    assert sha(OLD/'bin/rtx-scope-transfer.exe')==binding['executable_sha256']
    assert sha(OLD/'core/src/libllama.a')==binding['core_sha256']
    for n,h in binding['numerical_modules'].items():assert sha(OLD/'bin'/n)==h
    for arm in ['reference-observer','D1','D1-observer','D2','D2-observer','D4','D4-observer']:
        dest=ROOT/'draft'/arm;binary=dest/'bin';binary.mkdir()
        for name in binding['numerical_modules']:shutil.copy2(OLD/'bin'/name,binary/name)
        records=[]
        for rec in binding['commands']:
            if rec['label'] not in ('worker','link'):continue
            argv=[x.replace(str(OLD/'worker.cpp'),str(dest/'worker.cpp')).replace(str(OLD/'worker.obj'),str(dest/'worker.obj')).replace(str(OLD/'bin/rtx-scope-transfer.exe'),str(binary/'rtx-scope-transfer.exe')) for x in rec['argv']]
            start=time.monotonic()
            with (dest/(rec['label']+'.log')).open('xb') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=600)
            records.append(dict(argv=argv,code=r.returncode,seconds=time.monotonic()-start))
            put(dest/(rec['label']+'.json'),records[-1]);r.check_returncode()
        put(dest/'BUILD.json',dict(status='BUILT_NOT_GPU_QUALIFIED',commands=records,exe=sha(binary/'rtx-scope-transfer.exe'),source=sha(dest/'worker.cpp'),original_exe=binding['executable_sha256'],core=binding['core_sha256'],modules=binding['numerical_modules']))
        print(arm,'built, GPU qualification pending',flush=True)
if __name__=='__main__':main()
