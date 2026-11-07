"""Full external-byte and host observation; no model forward."""
import argparse,ctypes,hashlib,json,os,platform,subprocess
from pathlib import Path
from prepare import ROOT,STUDY,save
from engine import ASSET,BIN,TARGET,DRAFT,now
EXPECTED={'target':'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6','draft':'9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031','dataset':'b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef'}
def file(p):
    with Path(p).open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return {'path':str(p),'bytes':Path(p).stat().st_size,'sha256':h}
def main(output=None):
    files={'target':file(TARGET),'draft':file(DRAFT),'dataset':file(ASSET/'datasets/humaneval/HumanEval.jsonl.gz')}
    assert all(files[k]['sha256']==v for k,v in EXPECTED.items())
    runtime={p.name:file(p) for p in BIN.iterdir() if p.suffix.lower() in ['.exe','.dll']}
    frontend={p.name:file(p) for p in (ROOT/'work/h2-bin').glob('*.exe')}
    driver_paths={Path('C:/Windows/System32/nvcuda.dll')}
    for p in (ROOT/'work').glob('engineering-attempt*/**/events.jsonl'):
        with p.open('rb') as f:
            for line in f:
                row=json.loads(line)
                if row['event']=='startup':
                    for name in row['response']['modules']:
                        q=Path(name)
                        if q.name.lower().startswith('nv') and '/windows/' in q.as_posix().lower():driver_paths.add(q)
    drivers={p.name:file(p) for p in driver_paths if p.is_file()}
    os.add_dll_directory(str(BIN));cuda=ctypes.WinDLL(str(BIN/'cudart64_12.dll'));version=ctypes.c_int();rc=cuda.cudaRuntimeGetVersion(ctypes.byref(version));assert rc==0
    record={'utc':now(),'assets':files,'runtime':runtime,'frontends':frontend,'driver_modules':drivers,'os':platform.platform(),'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,pci.bus_id,memory.total','--format=csv,noheader'],text=True).strip(),'cuda_runtime':version.value,'override_environment':{k:v for k,v in os.environ.items() if k.startswith(('LLAMA_','GGML_','CUDA_'))},'status':'PASS','scope':'full asset/runtime/frontend bytes; observed NVIDIA process modules and nvcuda; does not claim all driver files in Windows','timer_binaries':{p.name:file(p) for p in (ROOT/'work/timer-build/bin').iterdir() if p.suffix.lower() in ['.exe','.dll']},'initial_debug_exception':None}
    save(output or STUDY/'ASSET_ENVIRONMENT_BEFORE.json',record);print('External hashes and environment PASS')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args();main(a.output)
