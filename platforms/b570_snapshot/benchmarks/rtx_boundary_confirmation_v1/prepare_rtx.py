"""CPU-only materialization, exact recipe checks and isolated shared-core builds."""
import argparse,copy,json,math,os,shutil,struct,subprocess,sys,time
from pathlib import Path
import numpy as np
from common import V,load,save,sha
from study import make_plan,validate_plan
ROLES=['Q','K','V','mask'];LAYOUTS=['PQ','QB','QH_C']
def root():return Path(os.environ.get('HETEROSPEC_RUN_ROOT') or load(V/'LOCAL_RUN.json')['root'])
def scalar(counter,seed,salt,realization,mod):
    mask=(1<<64)-1;x=(counter^seed^(salt<<56));x=(x+0x9e3779b97f4a7c15)&mask;x=((x^(x>>30))*0xbf58476d1ce4e5b9)&mask;x=((x^(x>>27))*0x94d049bb133111eb)&mask;x=x^(x>>31)
    z=(x%mod-(mod//2))/32
    return z*(2.0**((x>>12)%9-4)) if realization else z

def values(counter,seed,salt,realization,mod,dtype):
    with np.errstate(over='ignore'):
        x=counter.astype(np.uint64)^np.uint64(seed)^np.uint64(salt<<56);x=x+np.uint64(0x9e3779b97f4a7c15);x=(x^(x>>np.uint64(30)))*np.uint64(0xbf58476d1ce4e5b9);x=(x^(x>>np.uint64(27)))*np.uint64(0x94d049bb133111eb);x=x^(x>>np.uint64(31))
    z=((x%mod).astype(np.int32)-mod//2).astype(np.float32)/32
    if realization:z*=np.exp2(((x>>np.uint64(12))%9).astype(np.int32)-4)
    flat=counter.ravel();out=z.ravel()
    for ix in sorted(set([0,len(flat)-1]+list(np.linspace(0,len(flat)-1,31,dtype=int)))):
        assert out[ix]==scalar(int(flat[ix]),seed,salt,realization,mod),'independent scalar recipe'
    return z.astype(dtype)

def tensor(role,kind,ne,nb):return dict(file=role+'.bin',type=kind,ne=ne,nb=nb,bytes=(4 if kind==0 else 2)+sum((n-1)*b for n,b in zip(ne,nb)))
def binary(path,array):
    with Path(path).open('xb') as f:f.write(array.tobytes())
def materialize(plan,optional=False):
    r=root();s=load(r/'RUN_SPEC.json');base=load(Path('D:/hs120-8a6bde3c-bc24-4f16-9e1e-9950965386d3/RUN_SPEC.json'))['contexts'][0]['metadata'];result={}
    for c in plan['cases']:
        if (c['cohort']=='holdout')!=optional:continue
        if optional:assert (r/'PREDICTION_FREEZE.json').exists(),'holdout unopened until rule frozen'
        d,q,H,g,S=c['d'],c['q'],c['Hq'],c['Hkv'],c['keys'];folder=r/'inputs'/c['case_id'];folder.mkdir(parents=True,exist_ok=False)
        j=np.arange(q,dtype=np.uint64)[:,None,None];h=np.arange(H,dtype=np.uint64)[None,:,None];a=np.arange(d,dtype=np.uint64)[None,None,:]
        Q=values((j*64+h)*256+a,c['seed'],0x51,c['realization'],17,'<f4')
        k=np.arange(S,dtype=np.uint64)[:,None,None];gg=np.arange(g,dtype=np.uint64)[None,:,None]
        K=values((gg*8192+k)*256+a,c['seed'],0x4b,c['realization'],17,'<f2')
        gg=np.arange(g,dtype=np.uint64)[:,None,None];a=np.arange(d,dtype=np.uint64)[None,:,None];k=np.arange(S,dtype=np.uint64)[None,None,:]
        vv=values((gg*256+a)*8192+k,c['seed'],0x56,c['realization'],33,'<f2')
        mask=np.full((q,S),-np.inf,dtype='<f4')
        for j in range(q):
            if c['mask']=='causal':mask[j,:S-q+j+1]=0
            elif c['mask']=='irregular':mask[j,(np.arange(S)+j)%3!=0]=0
            else:mask[j,(S-q+j)%S]=0
        compact=c['storage']=='compact';binary(folder/'Q.bin',Q.transpose(1,0,2).copy() if compact else Q);binary(folder/'K.bin',K);binary(folder/'V.bin',vv);binary(folder/'mask.bin',mask)
        m={name:copy.deepcopy(base[name]) for name in ['native_QK','native_softmax','native_AV']};m['native_softmax']['op_params_bytes'][:4]=list(struct.pack('<f',1/math.sqrt(d)))
        m.update(q_occupancy=q,captured_key_extent=S,phase='synthetic',role='coordinate_hash_v1')
        m['Q']=tensor('Q',0,[d,q,H,1],[4,d*4,d*q*4,d*q*H*4] if compact else [4,d*H*4,d*4,d*q*H*4]);m['K']=tensor('K',1,[d,S,g,1],[2,d*g*2,d*2,d*S*g*2]);m['V']=tensor('V',1,[S,d,g,1],[2,S*2,S*d*2,S*d*g*2]);m['mask']=tensor('mask',0,[S,q,1,1],[4,S*4,S*q*4,S*q*4]);save(folder/'snapshot.json',m)
        serial=[]
        for j in range(q):
            sub=folder/f'serial{j}';sub.mkdir();binary(sub/'Q.bin',Q[j]);binary(sub/'mask.bin',mask[j]);os.link(folder/'K.bin',sub/'K.bin');os.link(folder/'V.bin',sub/'V.bin');one=copy.deepcopy(m);one['q_occupancy']=1;one['Q']=tensor('Q',0,[d,1,H,1],[4,d*H*4,d*4,d*H*4]);one['mask']=tensor('mask',0,[S,1,1,1],[4,S*4,S*4,S*4]);save(sub/'snapshot.json',one);serial.append(str(sub))
        entries=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(folder.iterdir()) if p.is_file()];save(folder/'INPUT.json',entries)
        result[c['case_id']]=dict(c,id=c['case_id'],root=str(folder),metadata=m,serial_roots=serial,input_sha256=sha(folder/'INPUT.json'),inputs=entries,references={l:dict(path=str(folder/'ordinary_reference.bin'),sha256=None) for l in LAYOUTS},visible_keys=[int(np.isfinite(mask[j]).sum()) for j in range(q)])
    save(r/('HOLDOUT_INPUTS.json' if optional else 'INPUTS.json'),result);return result

def build():
    r=root();s=load(r/'RUN_SPEC.json');outputs=[]
    for name,source in [('collector','collector.cpp'),('address_cpu','boundary_cpu.cpp')]:
        cmd=[s['compiler']['path'],'c++','-O3','-DNDEBUG','-D_CRT_SECURE_NO_WARNINGS','-std=c++17','-DGGML_BACKEND_DL','-DGGML_SHARED','-I'+s['ggml_include'],'-I'+s['vendor_include'],str(V/source),str(V/'build/libggml.dll.a'),str(V/'build/libggml-base.dll.a'),'-lpsapi','-lbcrypt','-o',str(V/f'build/{name}.exe')]
        t=time.monotonic();p=subprocess.run(cmd,capture_output=True,timeout=600);record=dict(command=cmd,exit=p.returncode,seconds=time.monotonic()-t,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'),GPU_calls=0,native_sha256=sha(V/f'build/{name}.exe') if p.returncode==0 else None);save(r/f'BUILD_{name}_{len(list(r.glob("BUILD_"+name+"*.json")))}.json',record);assert p.returncode==0,record;outputs.append(record)
    (V/'BUILD.json').write_text(json.dumps(outputs,indent=2),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','build','holdout']);args=ap.parse_args();r=root()
    if args.action=='build':build();return
    if args.action=='holdout':materialize(load(r/'plan.json'),True);return
    plan=make_plan();save(r/'plan.json',plan);s=load(r/'RUN_SPEC.json')
    assert all(sha(Path(s['runtime_directory'])/name)==digest for name,digest in s['numerical_DLLs'].items())
    save(r/'RUNTIME_MANIFEST.json',s['numerical_DLLs']);data=materialize(plan)
    save(V/'INPUT_PREPARATION.json',dict(cases=len(data),plan_sha256=plan['plan_sha256'],recipe='coordinate_hash_v1',scalar_vs_vector_samples_per_operand=33,all_full_operand_bytes_hashed=True,optional_holdout_opened=False,GPU_calls=0,CUDA_loads=0));print('Prepared',len(data),'core inputs; holdout unopened',flush=True)
if __name__=='__main__':main()
