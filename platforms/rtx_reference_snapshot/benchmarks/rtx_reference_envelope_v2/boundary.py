"""R1 prespecified12+12 logical fixtures,two value realizations,serial q1 reference.

Independent synthetic cohort; never fills historical slots or extends W1 admission.
Prepare/build only after core T1; run is serial and bounded to one hour.
"""
import argparse,copy,datetime,json,math,os,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
from common import V,load,save,sha
from lifecycle import Child
from run import root,env,helper,runtime_locks,telemetry,quiet,guard,dedup,git
LAYOUTS=['PQ','QB','QH_C']
def tensor(name,kind,ne,nb):return dict(file=name+'.bin',type=kind,ne=ne,nb=nb,bytes=(4 if kind==0 else 2)+sum((a-1)*b for a,b in zip(ne,nb)))
def binary(p,array):
    with Path(p).open('xb') as f:f.write(array.tobytes())
def prepare():
    r=root()/'R1';r.mkdir(exist_ok=False);s=load(root()/'RUN_SPEC.json');fixtures=[]
    lengths={'development':[128,129,256,257,1024,4096],'holdout':[127,255,258,1023,1025,4095]}
    for split in ['development','holdout']:
        for i in range(12):
            model=['Qwen','SmolLM2','Llama'][i%3];base=copy.deepcopy(next(c for c in s['contexts'] if c['family']==model)['metadata']);D=base['Q']['ne'][0];H=32;Hkv=base['K']['ne'][2];q=[1,2,3,4][i%4];S=lengths[split][i] if i<6 else 256 if split=='development' else 257
            category='length_q' if i<6 else 'GQA' if i<9 else 'stride_mask'
            if category=='GQA':Hkv=[1,8,32][i-6]
            maskkind='causal' if i<10 else 'irregular' if i==10 else 'single_visible';compact=i==9
            logical_id=f'{split}-{i:02d}';
            for realization in range(2):
                case_id=logical_id+f'-v{realization}';folder=r/'inputs'/case_id;folder.mkdir(parents=True);seed=20261018+(0 if split=='development' else 1000)+i*2+realization;rng=np.random.default_rng(seed)
                # All heads/channels/keys present. Exact dyadic operands,including
                # signed cancellation values; F16 conversion is part of contract.
                Q=(rng.integers(-8,9,size=(q,H,D)).astype(np.float32)/32);K=(rng.integers(-8,9,size=(S,Hkv,D)).astype(np.float16)/32).astype('<f2');values=(rng.integers(-16,17,size=(Hkv,D,S)).astype(np.float16)/32).astype('<f2')
                if realization:Q[:,:,::2]*=-1;values[:,::2,:]*=-1
                mask=np.full((q,S),-np.inf,dtype='<f4')
                for j in range(q):
                    if maskkind=='causal':mask[j,:S-q+j+1]=0
                    elif maskkind=='irregular':mask[j,(np.arange(S)+j)%3!=0]=0
                    else:mask[j,(S-q+j)%S]=0
                binary(folder/'Q.bin',Q.transpose(1,0,2).copy() if compact else Q);binary(folder/'K.bin',K);binary(folder/'V.bin',values);binary(folder/'mask.bin',mask)
                m={name:dict(op_params_bytes=base[name]['op_params_bytes']) for name in ['native_QK','native_softmax','native_AV']};m.update(q_occupancy=q,captured_key_extent=S,phase='synthetic',role='synthetic_full_geometry')
                m['Q']=tensor('Q',0,[D,q,H,1],[4,D*4,D*q*4,D*q*H*4] if compact else [4,D*H*4,D*4,D*q*H*4]);m['K']=tensor('K',1,[D,S,Hkv,1],[2,D*Hkv*2,D*2,D*S*Hkv*2]);m['V']=tensor('V',1,[S,D,Hkv,1],[2,S*2,S*D*2,S*D*Hkv*2]);m['mask']=tensor('mask',0,[S,q,1,1],[4,S*4,S*q*4,S*q*4]);save(folder/'snapshot.json',m)
                serial=[]
                for j in range(q):
                    sub=folder/f'serial{j}';sub.mkdir();binary(sub/'Q.bin',Q[j]);binary(sub/'mask.bin',mask[j]);os.link(folder/'K.bin',sub/'K.bin');os.link(folder/'V.bin',sub/'V.bin');one=copy.deepcopy(m);one['q_occupancy']=1;one['Q']=tensor('Q',0,[D,1,H,1],[4,D*H*4,D*4,D*H*4]);one['mask']=tensor('mask',0,[S,1,1,1],[4,S*4,S*4,S*4]);save(sub/'snapshot.json',one);serial.append(str(sub))
                c=dict(id=case_id,logical_fixture=logical_id,split=split,realization=realization,seed=seed,category=category,family=model,phase='synthetic',q=q,layer=None,root=str(folder),metadata=m,maskkind=maskkind,compact_Q=compact,serial_roots=serial,inputs=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(folder.iterdir()) if p.is_file()],references={l:dict(path=str(folder/'ordinary_reference.bin'),sha256=None) for l in LAYOUTS})
                fixtures.append(c)
    # New host differs only in explicit independent-reference capture semantics.
    source=(V/'native.cpp').read_text();old='auto expected=bytes(context["references"][layout]["path"].get<std::string>());';assert source.count(old)==1
    early='std::string layout=job.at("layout"),life=job.at("lifecycle");';assert source.count(early)==1
    source=source.replace(early,early+'bool requested_capture=job.value("capture_reference",false);if(requested_capture)hs113::require(context.at("q")==1&&layout=="PQ"&&job.at("stage")=="R1_REFERENCE"&&job.at("warmups")==0&&job.at("calls")==1,"capture restricted to independent serial reference");')
    source=source.replace(old,'bool capture=requested_capture;auto expected=capture?std::vector<unsigned char>(ggml_nbytes(g.result.ordinary)):bytes(context["references"][layout]["path"].get<std::string>());').replace('bool eq=ordinary==expected;','bool eq=capture||ordinary==expected;').replace('call["ordinary_exact"]=eq;','call["ordinary_exact"]=capture?J(nullptr):J(eq);').replace('write(out/"RECORD.json",record);','if(capture&&success&&input_equal&&host_equal)record["status"]="REFERENCE_CAPTURE";record["reference_capture"]=capture;write(out/"RECORD.json",record);').replace('return record["status"]=="QUALIFIED"?0:3;','return (record["status"]=="QUALIFIED"||record["status"]=="REFERENCE_CAPTURE")?0:3;')
    (V/'boundary_native.cpp').write_text(source,encoding='utf-8')
    build=load(V/'BUILD.json')['command'];build[build.index(str(V/'native.cpp'))]=str(V/'boundary_native.cpp');build[-1]=str(V/'build/boundary.exe');t=time.monotonic();p=subprocess.run(build,capture_output=True,timeout=600);save(V/'R1_BUILD.json',dict(command=build,exit=p.returncode,seconds=time.monotonic()-t,stderr=p.stderr.decode(errors='replace'),source_sha256=sha(V/'boundary_native.cpp'),GPU_calls=0));assert p.returncode==0
    # Selector is frozen from completed core T1 before ANY synthetic output.
    estimates={}
    for p in sorted((root()/'attempts').glob('*/JOB.json')):
        j=load(p)
        if j['stage']!='T1':continue
        rr=load(p.parent/'native/RECORD.json');b=j['block'];ended=load(root()/f'T1_BLOCK_{b}_ENDED.json')
        if rr['status']!='QUALIFIED' or not ended['environment_qualified']:continue
        times=[(x['sync_return']-x['begin'])*1e6/rr['QPC_frequency'] for x in rr['calls'] if not x['warmup']];estimates.setdefault((j['context']['q'],j['layout']),[]).append(sum(times)/len(times))
    selector={str(q):'QB' if q==1 else min(LAYOUTS,key=lambda l:sum(estimates[q,l])/len(estimates[q,l])) for q in range(1,5)}
    # Explicit pure-Python lookup overhead,charged to selector cost estimates.
    start=time.perf_counter_ns()
    for i in range(100000):selected=selector[str(i%4+1)]
    overhead=(time.perf_counter_ns()-start)/100000/1000
    counts=dict(logical_fixtures=24,data_realizations=48,serial_reference_hosts=2*sum(c['q'] for c in fixtures),qualification_hosts=48*3*2,qualification_calls=48*3*2*34,cost_hosts=48*3,cost_calls=48*3*38)
    plan=dict(fixtures=fixtures,counts=counts,native_sha256=sha(V/'build/boundary.exe'),derived_from_native_sha256=sha(V/'native.cpp'),semantics='single-query serial reference,twice independently;exact bytes;new synthetic cohort',qualification='two processes per mapping,2warmup+32calls',cost='one independent38call host per data realization/layout,8warmup+30;descriptive2value repetitions,not6blocks',selector=selector,selector_lookup_overhead_us=overhead,selection_training='coreT1 only;frozen before all synthetic outputs;no development adaptation',stage_limit_seconds=3600,original_72_fixture_design='bounded12+12logical prefix;twelve remaining per split UNSTARTED',GPU_calls_during_prepare=0)
    inputs={str(p):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (r/'inputs').rglob('*') if p.is_file()};save(r/'INPUT_MANIFEST.json',inputs);plan['input_manifest_sha256']=sha(r/'INPUT_MANIFEST.json')
    save(r/'PLAN.json',plan);save(V/'R1_PLAN_SUMMARY.json',{k:v for k,v in plan.items() if k!='fixtures'});print(counts,selector)
def execute(s,c,layout,mode,index,capture=False):
    guard(s);r=root()/'R1';d=r/'attempts'/f'{index:04d}';d.mkdir(parents=True,exist_ok=False);warm,calls=(0,1) if capture else (2,32) if mode=='qualify' else (8,30)
    pinned=load(r/'INPUT_MANIFEST.json')
    for name in ['snapshot.json','Q.bin','K.bin','V.bin','mask.bin']:
        p=Path(c['root'])/name;assert sha(p)==pinned[str(p)]['sha256'],'synthetic input drift'
    if not capture:
        assert all(sha(row['path'])==row['sha256'] for row in c['references'].values()),'new serial reference identity'
    job=dict(spec=str(root()/'RUN_SPEC.json'),execution_id=s['execution_id'],stage='R1_REFERENCE' if capture else 'R1',context=c,layout=layout,lifecycle='persistent_inputs',warmups=warm,calls=calls,capture_reference=capture);save(d/'JOB.json',job);worker=Child(helper());err=None
    try:worker.run([str(V/'build/boundary.exe'),'--gpu',str(d/'JOB.json'),str(d/'native')],d/'host',120,env(s),s['host_RAM_bytes'],lambda:guard(s),log_cap=65536)
    except BaseException as e:err=repr(e)
    finally:worker.terminate()
    life=load(d/'host.LIFETIME.json');assert not load(d/'host.JOB_EVENTS.json')['errors'],'unsafe cleanup';n=d/'native';dedup(n)
    if not (n/'RECORD.json').exists():
        error=load(n/'NATIVE_ERROR.json');assert error['reason']=='node unsupported','unknown execution failure;stop GPU';save(d/'ENDED.json',dict(mode=mode,status='UNSUPPORTED',error=error,exit=life['exit_code']));return None,d
    rr=load(n/'RECORD.json');assert life['exit_code'] in [0,3];assert rr['input_after_equal'] and rr['host_input_unchanged'],'input mutation;stop affected stage'
    graph=load(n/'GRAPH.json');assert all(x['CUDA_owned'] for x in graph['addresses']) and graph['actual_device']=='CUDA0' and len(rr['plugin_core_IAT'])==41
    if not capture:
        expected=Path(c['references'][layout]['path']).read_bytes()
        for row in rr['calls']:assert ((n/f'ordinary_{row["index"]}.bin').read_bytes()==expected)==row['ordinary_exact'],'independent CPU output check'
    assert all(x['compute_status']==x['sync_status']==0 and x['finite'] for x in rr['calls'])
    save(d/'ENDED.json',dict(mode=mode,status=rr['status'],exit=life['exit_code'],error=err,actual_calls=len(rr['calls'])));return rr,d
def run():
    r=root()/'R1';plan=load(r/'PLAN.json');s=load(root()/'RUN_SPEC.json');assert not (root()/'WORKER.lock').exists(),'one GPU worker only';save(r/'STARTED.json',dict(pid=os.getpid(),epoch=time.time()));assert not git('status','--porcelain','--untracked-files=no','--','benchmarks/rtx_reference_envelope_v2')
    save(r/'FREEZE.json',dict(commit=git('rev-parse','HEAD'),plan_sha256=sha(r/'PLAN.json'),native_sha256=sha(V/'build/boundary.exe'),source_sha256=sha(V/'boundary_native.cpp'),original_inputs_untouched=True));assert sha(V/'build/boundary.exe')==plan['native_sha256'];handles=runtime_locks(s);begin=time.monotonic();index=0;eligibility={};refs=[];records=[]
    def check():assert time.monotonic()-begin<3600,'R1 stage ceiling';guard(s)
    for c in plan['fixtures']:
        check();sample=telemetry(s,'R1/'+c['id']);assert sample.get('safe_memory',True),'device memory margin';parts=[]
        for j,serialroot in enumerate(c['serial_roots']):
            one=copy.deepcopy(c);one.update(id=c['id']+f'/serial{j}',root=serialroot,q=1,metadata=load(Path(serialroot)/'snapshot.json'));values=[]
            for rep in range(2):
                check();rr,d=execute(s,one,'PQ','reference',index,True);index+=1;assert rr and rr['status']=='REFERENCE_CAPTURE';values.append((d/'native/ordinary_0.bin').read_bytes())
            assert values[0]==values[1],'serial independent reference differs';parts.append(values[0])
        reference=b''.join(parts);path=Path(c['root'])/'ordinary_reference.bin'
        with path.open('xb') as f:f.write(reference)
        if c['maskkind']=='single_visible':
            D=c['metadata']['Q']['ne'][0];H=32;Hkv=c['metadata']['K']['ne'][2];S=c['metadata']['K']['ne'][1];v=np.fromfile(Path(c['root'])/'V.bin',dtype='<f2').reshape(Hkv,D,S);out=[]
            # Ordered FP32 zero-initialized AV,including signed-zero behavior;
            # do not assume selecting a -0 input must emit -0 after a dot sum.
            for j in range(c['q']):
                acc=np.zeros((H,D),dtype='<f4');selected=(S-c['q']+j)%S
                for k in range(S):acc=np.float32(acc+np.float32(v[np.arange(H)//(H//Hkv),:,k].astype('<f4')*np.float32(k==selected)))
                out.append(acc)
            oracle=np.stack(out).tobytes();assert oracle==reference,'independent full single-key oracle mismatch'
        for l in LAYOUTS:c['references'][l]['sha256']=sha(path)
        refs.append(dict(case=c['id'],reference_sha256=sha(path),bytes=len(reference),q1_reference_processes=2*c['q'],single_key_oracle=c['maskkind']=='single_visible'))
        for l in LAYOUTS:
            good=True
            for rep in range(2):
                check();rr,d=execute(s,c,l,'qualify',index);index+=1;good&=bool(rr and rr['status']=='QUALIFIED');records.append(dict(case=c['id'],split=c['split'],layout=l,mode='qualify',directory=str(d),eligible=bool(rr and rr['status']=='QUALIFIED')))
                if not good:break
            eligibility[c['id'],l]=good
        print('R1 numerical',c['id'],index,'hosts',flush=True)
    save(r/'REFERENCES.json',refs)
    for split in ['development','holdout']:
        quiet(s,'R1/'+split)
        for c in plan['fixtures']:
            if c['split']!=split:continue
            for l in LAYOUTS:
                if not eligibility[c['id'],l]:continue
                check();rr,d=execute(s,c,l,'cost',index);index+=1;records.append(dict(case=c['id'],split=split,layout=l,mode='cost',directory=str(d),eligible=bool(rr and rr['status']=='QUALIFIED')))
        post=telemetry(s,'R1/'+split+'/post');save(r/(split+'_ENVIRONMENT.json'),dict(qualified=post.get('quiet',False),post=post))
    save(r/'ENDED.json',dict(status='COMPLETE' if all(eligibility.values()) else 'PARTIAL',hosts=index,seconds=time.monotonic()-begin,eligible_cells=sum(eligibility.values()),planned_cells=144,records=records));print('R1 done',index,flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);args=ap.parse_args();{'prepare':prepare,'run':run}[args.action]()
