"""CPU fault injection into private copies of actual qualification evidence."""
import copy,json,shutil,time
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from runner import audit

def run():
    r=root();a=r/'attempts/qualification-T0-2-v0-QB_A-r0';job=load(a/'JOB.json');c=job['context'];source=a/'native';dest=r/'CPU_RAW_NEGATIVE';dest.mkdir();original={p.name:sha(p) for p in source.iterdir() if p.is_file()};results=[]
    def rewrite(p,x):p.write_text(json.dumps(x),encoding='utf-8')
    for kind in ['ordinary','truncated','input','placement','IAT','graph','clock','module']:
        n=dest/kind;shutil.copytree(source,n)
        if kind in ['ordinary','truncated']:
            p=n/'ordinary_all.bin';data=bytearray(p.read_bytes())
            if kind=='ordinary':data[0]^=1
            else:data=data[:10]
            p.write_bytes(data)
        if kind=='input':
            p=n/'input_Q_after.bin';data=bytearray(p.read_bytes());data[0]^=1;p.write_bytes(data)
        if kind in ['placement','graph']:
            p=n/'GRAPH.json';x=load(p)
            if kind=='placement':x['addresses'][0]['CUDA_owned']=False
            else:x['nodes'][0]['op_params'][0]^=1
            rewrite(p,x)
        if kind in ['IAT','clock','module']:
            p=n/'RECORD.json';x=load(p)
            if kind=='IAT':x['plugin_core_IAT'][0]['target']+=1
            elif kind=='clock':x['calls'][0]['sync_return']=x['calls'][0]['begin']-1
            else:x['modules'][0]='wrong';x['modules_end'][0]='wrong_cuda.dll'
            rewrite(p,x)
        try:audit(n,c,job)
        except (AssertionError,ValueError) as e:results.append(dict(case=kind,rejected=True,reason=str(e)))
        else:raise AssertionError('bad raw evidence accepted '+kind)
    assert original=={p.name:sha(p) for p in source.iterdir() if p.is_file()},'original evidence mutation'
    save(r/'CPU_RAW_NEGATIVE.json',dict(status='PASS',tests=len(results),results=results,original_unchanged=True,GPU_calls=0));print(results)
if __name__=='__main__':run()
