"""Independent full-tensor mathematical oracle;never a byte-qualification tolerance."""
import math,struct,time,os
from pathlib import Path
import numpy as np
from common import V,load,save,sha
from run import root
from analyze import writecsv
raw=root();plan=load(raw/'R1/PLAN.json');out=Path(os.environ.get('HETEROSPEC_ORACLE_OUT',str(Path(str(raw)+'-archive')/'CPU_FP64_ORACLE')));out.mkdir(exist_ok=False);rows=[];begin=time.monotonic();summary_out=Path(os.environ.get('HETEROSPEC_ORACLE_SUMMARY',str(V)));summary_out.mkdir(parents=True,exist_ok=True)
mapping=load(os.environ['HETEROSPEC_SOURCE_MAP']) if os.environ.get('HETEROSPEC_SOURCE_MAP') else {}
def input_path(p):return Path(mapping.get(os.path.normcase(str(Path(p).resolve())),str(p)))
for c in plan['fixtures']:
    folder=Path(c['root']);m=c['metadata']
    def tensor(role):
        p=input_path(folder/(role+'.bin'));b=p.read_bytes();return np.ndarray(tuple(m[role]['ne']),dtype='<f4' if m[role]['type']==0 else '<f2',buffer=b,strides=tuple(m[role]['nb']))[...,0].astype(np.float64)
    Q=tensor('Q').transpose(2,1,0);K=tensor('K').transpose(2,1,0);values=tensor('V').transpose(2,0,1);mask=tensor('mask')[:,:,0].T
    H=m['Q']['ne'][2];G=m['K']['ne'][2];group=np.arange(H)//(H//G);scale=struct.unpack('<f',bytes(m['native_softmax']['op_params_bytes'][:4]))[0]
    scores=np.einsum('hqd,hsd->hqs',Q,K[group],optimize=True)*scale+mask[None,:,:];scores-=np.max(scores,axis=2,keepdims=True);prob=np.exp(scores);prob/=np.sum(prob,axis=2,keepdims=True);answer=np.einsum('hqs,hsd->hqd',prob,values[group],optimize=True).transpose(1,0,2)
    assert np.isfinite(answer).all();reference=np.fromfile(input_path(folder/'ordinary_reference.bin'),dtype='<f4').reshape(answer.shape).astype(np.float64);error=np.abs(answer-reference);destination=out/(c['id']+'.fp64.bin');answer.astype('<f8').tofile(destination)
    rows.append(dict(case=c['id'],split=c['split'],family=c['family'],q=c['q'],d=m['Q']['ne'][0],Hq=H,Hkv=G,keys=m['K']['ne'][1],mask=c['maskkind'],complete_output_words=int(answer.size),max_absolute_error=float(error.max()),rms_error=float(np.sqrt(np.mean(error**2))),oracle_sha256=sha(destination),reference_sha256=sha(input_path(folder/'ordinary_reference.bin')),meaning='mathematical FP64 diagnostic only;no tolerance,eligibility orcandidate selection change'))
writecsv(summary_out,'FP64_ORACLE.csv',rows);save(summary_out/'FP64_ORACLE.json',dict(cases=len(rows),all_heads_channels_keys=True,complete_output_words=sum(r['complete_output_words'] for r in rows),maximum_absolute_error=max(r['max_absolute_error'] for r in rows),reference_contract='deployed serial reference remains authoritative;FP64 isnotbyte reference',new_GPU_queries=0,numpy_version=np.__version__,seconds=time.monotonic()-begin,raw_directory=str(out),source_sha256=sha(Path(__file__))))
print('FP64 full tensor oracle',len(rows),'cases',time.monotonic()-begin,'seconds')
