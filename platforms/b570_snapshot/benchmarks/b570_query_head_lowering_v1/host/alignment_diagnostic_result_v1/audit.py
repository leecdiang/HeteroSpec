"""Read-only reconstruction of seven completed diagnostic attempts; no launches."""
import collections
import hashlib
import json
import math
import pathlib
import struct
import subprocess
import sys
import zipfile

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REVIEW=ROOT/'host/alignment_review_v1'
RUN=ROOT/'host_outputs/alignment_review_v1/DIAGNOSTIC_RUN'
sys.path.insert(0,str(ROOT/'host'));sys.path.insert(0,str(ROOT));sys.path.insert(0,str(REVIEW))
from common import load,save,sha,modules
from conditions import descriptor
from run_diagnostic import expected_assertion
import core

F0='7a99f5b8e1c06051a6c916e5999201304bd6724ba0a49228f95d765e1b45ce3e'


def events(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def f32(path):
    b=path.read_bytes();assert b and len(b)%4==0
    assert all(math.isfinite(x[0]) for x in struct.iter_unpack('<f',b))
    return b


def comparison(left,right):
    assert len(left)==len(right) and len(left)%4==0 and left
    maximum=0.;ulp=0;mismatches=0
    def order(bits):return 0x80000000-(bits&0x7fffffff) if bits>>31 else 0x80000000+(bits&0x7fffffff)
    for i in range(0,len(left),4):
        a,b=struct.unpack('<f',left[i:i+4])[0],struct.unpack('<f',right[i:i+4])[0]
        assert math.isfinite(a) and math.isfinite(b)
        maximum=max(maximum,abs(a-b));mismatches+=left[i:i+4]!=right[i:i+4]
        u,v=struct.unpack('<I',left[i:i+4])[0],struct.unpack('<I',right[i:i+4])[0]
        ulp=max(ulp,abs(order(u)-order(v)))
    return dict(elements=len(left)//4,bitwise_equal=left==right,bit_mismatches=mismatches,
                max_abs_finite=maximum,max_ulp_finite=ulp,nonfinite_pairs=0)


def logical_stage(slot,stage,extent):
    """Return j,h,element order for complete PQ/QH stage files, without graph execution."""
    q=slot['cell']['geometry']['q'];h=slot['cell']['geometry']['h'];dest=RUN/slot['id']/'vectors'
    result=bytearray()
    parts=[f32(dest/f'{stage}-{i}.f32') for i in range(q if slot['mode']=='PQ' else 1)]
    for j in range(q):
        for head in range(h):
            data=parts[j] if slot['mode']=='PQ' else parts[0]
            start=(head if slot['mode']=='PQ' else head*q+j)*extent*4
            result.extend(data[start:start+extent*4])
    assert len(result)==q*h*extent*4
    return bytes(result)


def main():
    before=modules()
    assert sha(REVIEW/'DIAGNOSTIC_F0.json')==F0
    f0=load(REVIEW/'DIAGNOSTIC_F0.json')
    for name,digest in f0['sources'].items():assert sha(ROOT/name)==digest,name
    for item in [f0['executable']]+f0['dependencies']+f0['driver_files']:assert sha(item['path'])==item['sha256']
    assert sha(REVIEW/'DIAGNOSTIC_PLAN.json')==f0['plan_sha256']
    slots=load(REVIEW/'DIAGNOSTIC_PLAN.json')['slots'];assert len(slots)==7
    close=load(RUN/'CLOSEOUT.json');ledger=events(RUN/'LEDGER.jsonl')
    assert close['status']=='DIAGNOSTIC_COMPLETE_PENDING_ANALYSIS' and close['error'] is None
    assert close['attempts']==7 and not close['unstarted']
    attempts=[x for x in ledger if x['event']=='ATTEMPT']
    outcomes=[x for x in ledger if x['event']=='OUTCOME']
    assert [x['slot'] for x in attempts]==[s['id'] for s in slots]
    assert [x['index'] for x in attempts]==list(range(7))
    assert len(outcomes)==7 and len(close['outcomes'])==7
    assert len({x['slot'] for x in attempts})==7
    physical=[];supports=[];identities=[];processes=[];vectors=[];owned=0.
    references={}
    for index,(s,attempt) in enumerate(zip(slots,attempts)):
        assert sha(s['input'])==s['input_sha256']
        folder=RUN/s['id'];raw=events(folder/'raw.jsonl');life=load(folder/'LIFECYCLE.json')
        request=load(folder/'REQUEST.wire')
        assert request==attempt['request'] and request['F0_sha256']==F0
        assert raw[0]['event']=='HOST_START' and raw[0]['pid']==life['pid'] and raw[0]['request']==request
        assert life['raw_sha256']==sha(folder/'raw.jsonl') and life['request_sha256']==sha(folder/'REQUEST.wire')
        assert life['stop'] is None
        expected_modules={pathlib.Path(x['path']).name.lower():x['sha256'] for x in f0['dependencies']}
        numerical={pathlib.Path(x['path']).name.lower():x['sha256'] for x in life['actual_runtime_modules']
                   if pathlib.Path(x['path']).name.lower().startswith(('ggml','llama'))}
        assert numerical==expected_modules
        gate=next(x for x in raw if x['event']=='AWAIT_RUNTIME_GATE')
        assert {x.lower() for x in gate['modules']}=={x['path'].lower() for x in life['actual_runtime_modules']}
        for item in life['actual_runtime_modules']:assert sha(item['path'])==item['sha256']
        device=next(x for x in raw if x['event']=='DEVICE');assert 'B570' in device['description'] and device['backend_name']=='Vulkan0'
        layout=next(x for x in raw if x['event']=='PHYSICAL_LAYOUT');a=layout['minStorageBufferOffsetAlignment'];assert a==64
        ts=layout['tensors'];by_id={t['ctx_id']:t for t in ts};assert len(ts)==len(by_id)
        for t in ts:
            assert t['device_matches'] and t['buffer_name']=='Vulkan0'
            assert 0<=t['buffer_relative_offset'] and t['buffer_relative_offset']+t['bytes']<=t['buffer_bytes']
            if t['view_root']!=-1:
                root=by_id[t['view_root']];assert root['view_root']==-1
                assert root['buffer_relative_offset']+t['view_offset']==t['buffer_relative_offset']
                assert t['view_offset']+t['bytes']<=root['bytes']
            else:assert t['buffer_relative_offset']%a==0
        physical.append(dict(index=index,slot=s['id'],actual_alignment=a,tensors=ts,
            meaning='Actual buffer-relative offsets and sizes, not VRAM physical addresses or native stack evidence'))
        caps=next(x for x in raw if x['event']=='PRECOMPUTE_CAPABILITY')['nodes']
        compute=[x for x in caps if x['executable']];assert compute and all(x['supports_op'] is True for x in compute)
        assignment=next(x for x in raw if x['event']=='ASSIGNMENT_BEFORE_COMPUTE')['nodes']
        assert {n['id'] for n in compute}=={n['id'] for n in assignment}
        assert all(n['device_matches'] and n['direct_execution_backend']=='Vulkan0' for n in assignment)
        supports.append(dict(index=index,slot=s['id'],nodes=caps,assignment_before_compute=assignment))
        counts=collections.Counter(x['event'] for x in raw)
        assert counts['GRAPH_START']==life['graph_start_events']==1
        q,n,h,hk=(s['cell']['geometry'][k] for k in ('q','n','h','hk'))
        data=pathlib.Path(s['input']).read_bytes();cursor=28;payload=[]
        assert struct.unpack('<7i',data[:28])==(q,n,h,hk,1,0,0)
        for size in (128*q*h*4,128*n*hk*2,128*n*hk*2,32*n*4):
            payload.append(data[cursor:cursor+size]);cursor+=size
        assert cursor==len(data)
        payload[0]=bytes(s['q_offset_bytes'])+payload[0]
        slab_ids=[]
        if s['relocate_pq_mask']:
            mask=payload[3]
            payload.extend(mask[j*n*4:(j+1)*n*4] for j in range(q))
            slab_ids=[t['ctx_id'] for t in ts if t['op']=='NONE' and t['ne']==[n,1,1,1]]
            assert len(slab_ids)==q
        for i,b in enumerate(payload):
            bp=folder/f'vectors/input-{i}.before.bin';ap=folder/f'vectors/input-{i}.after.bin'
            assert bp.read_bytes()==b
            if index in (0,2):assert not ap.exists()
            else:assert ap.read_bytes()==b
            identities.append(dict(index=index,input=i,source_sha256=hashlib.sha256(b).hexdigest(),before_sha256=sha(bp),
                                   after_sha256=sha(ap) if ap.exists() else None))
        q_tensor=by_id[1];q_desc,q_delta=descriptor(q_tensor['buffer_relative_offset'],a,4)
        mask_views=[dict(ctx_id=t['ctx_id'],root=t['view_root'],root_relative_bytes=t['view_offset'],
                        buffer_relative_bytes=t['buffer_relative_offset'],descriptor_bytes=descriptor(t['buffer_relative_offset'],a,4)[0],
                        delta=descriptor(t['buffer_relative_offset'],a,4)[1]) for t in ts if t['op']=='VIEW' and t['ne']==[n,1,1,1]]
        if index in (0,2):
            classification=expected_assertion(index,folder,request)
            assert classification['classification']=='EXPECTED_NEGATIVE_LAYOUT_ASSERTION'
            assert life['returncode']==3221226505 and counts['GRAPH_RETURN']==counts['GRAPH_OUTPUT']==0
            assert not list((folder/'vectors').glob('*.f32')) and raw[-1]['event']=='GRAPH_START'
        else:
            assert life['returncode']==0 and counts['GRAPH_RETURN']==counts['GRAPH_OUTPUT']==1
            assert next(x for x in raw if x['event']=='GRAPH_RETURN')['status']==0 and raw[-1]['event']=='CLOSE'
            output=next(x for x in raw if x['event']=='GRAPH_OUTPUT')
            assert output['input_bytes_unchanged'] and output['final']['ne']==[128*h,q,1,1]
            expected_files=set()
            for part in output['stages']:
                for prefix,key in (('qk','QK'),('sm','softmax'),('av','AV')):
                    name=f'{prefix}-{part["part"]}.f32';expected_files.add(name);p=folder/'vectors'/name;b=f32(p)
                    count=math.prod(part[key]['ne']);assert len(b)==count*4
                    vectors.append(dict(index=index,file=name,elements=count,sha256=sha(p),all_finite=True))
            expected_files.add('final.f32');b=f32(folder/'vectors/final.f32');assert len(b)==128*h*q*4
            assert {p.name for p in (folder/'vectors').glob('*.f32')}==expected_files
            vectors.append(dict(index=index,file='final.f32',elements=len(b)//4,sha256=sha(folder/'vectors/final.f32'),all_finite=True))
            references[index]=s
            classification=dict(classification='COMPLETE_NUMERICAL_GRAPH')
        assert close['outcomes'][index]['classification']==classification['classification']
        samples=life['watchdog_samples'];assert samples and all(x['RSS'] is not None for x in samples)
        assert max(x['gap_ms'] for x in samples)<=1000 and max(x['RSS'] for x in samples)<=8*1024**3
        assert min(x['host_available'] for x in samples)>=8*1024**3 and min(x['disk_free'] for x in samples)>=4*1024**3
        assert life['owned_wall_s']<=60;owned+=life['owned_wall_s']
        checkpoints=[x for x in raw if x['event']=='MEMORY_CHECKPOINT']
        assert all(x['backend_reported_free_bytes']>=512*1024**2 and not x['continuous_residency'] for x in checkpoints)
        roots=[t for t in ts if t['view_root']==-1]
        slab_bytes=sum(by_id[i]['bytes'] for i in slab_ids)
        slab_rounded=sum((by_id[i]['bytes']+a-1)//a*a for i in slab_ids)
        processes.append(dict(index=index,slot=s['id'],mode=s['mode'],q=q,K=n,H=h,Hkv=hk,pid=life['pid'],
            classification=classification['classification'],returncode=life['returncode'],owned_wall_s=life['owned_wall_s'],
            support_nodes_true=len(compute),graph_start=counts['GRAPH_START'],graph_return=counts['GRAPH_RETURN'],
            output_available=counts['GRAPH_OUTPUT']==1,actual_alignment=a,Q_root_relative=q_tensor['view_offset'],
            Q_buffer_relative=q_tensor['buffer_relative_offset'],Q_descriptor_offset=q_desc,Q_delta=q_delta,
            mask_views=mask_views,independent_mask_slab_ids=slab_ids,
            extra_PQ_mask_logical_storage_bytes=slab_bytes,extra_PQ_mask_CPU_materialized_bytes=slab_bytes,
            extra_PQ_mask_API_upload_bytes=slab_bytes,extra_PQ_mask_allocator_rounded_bytes=slab_rounded,
            extra_mask_before_after_API_readback_bytes=2*slab_bytes if index not in (0,2) else None,
            allocated_root_payload_bytes=sum(t['bytes'] for t in roots),
            per_tensor_reported_buffer_extents=sorted({t['buffer_bytes'] for t in ts}),
            exact_unique_backing_buffer_count=None,DRAM_upload_traffic=None,
            observer_max_actual_gap_ms=max(x['gap_ms'] for x in samples),peak_sampled_RSS=max(x['RSS'] for x in samples),
            memory_checkpoints=checkpoints,native_stack_captured=False))
    assert abs(owned-close['owned_wall_s'])<1e-8 and owned<420
    pairs=[]
    for left,right in ((3,4),(5,6)):
        ls,rs=references[left],references[right];assert ls['cell']==rs['cell']
        n=ls['cell']['geometry']['n']
        stages={name:comparison(logical_stage(ls,name,extent),logical_stage(rs,name,extent))
                for name,extent in (('qk',n),('sm',n),('av',128))}
        final=comparison(f32(RUN/ls['id']/'vectors/final.f32'),f32(RUN/rs['id']/'vectors/final.f32'))
        pairs.append(dict(K=n,q=2,H=8,Hkv=2,PQ_slot=left,QH_C_slot=right,stages_j_h_element_order=stages,
                          final_original_order=final,scope='Two fixed synthetic dyadic/causal operands, no tolerance or natural endpoint claim'))
    original=load(ROOT/'host_outputs/S1_RUN/CLOSEOUT.json')
    assert original['attempts']==2 and len(original['unstarted'])==159 and abs(original['owned_wall_s']-5.109)<1e-8
    assert sha(ROOT/'host/S1_F0.json')==f0['original_S1_F0_sha256']
    assert sha(ROOT/'host/S1_RESULT.json')==f0['original_S1_result_sha256']
    assert sha(ROOT/'host/S1_RAW.zip')==load(ROOT/'host/S1_RAW_MANIFEST.json')['archive_sha256']
    git='C:/hs/pr108-tools/git/cmd/git.exe';repo=ROOT.parents[1]
    assert subprocess.check_output([git,'-C',str(repo),'rev-parse','HEAD'],text=True).strip()=='47ea26a3f406372eb4956955e6b973ef6874b3ad'
    assert not subprocess.check_output([git,'-C',str(repo),'diff','--name-only','HEAD'],text=True).strip()
    files=[dict(path=p.relative_to(RUN).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(RUN.rglob('*')) if p.is_file()]
    raw_bytes=sum(x['bytes'] for x in files);assert raw_bytes<128*1024**2
    archive=HERE/'DIAGNOSTIC_RAW.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(RUN/f['path'],f['path'])
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())=={f['path'] for f in files}
        for f in files:
            digest=hashlib.sha256();size=0
            with z.open(f['path']) as stream:
                while data:=stream.read(1024*1024):digest.update(data);size+=len(data)
            assert digest.hexdigest()==f['sha256'] and size==f['bytes']
    save(HERE/'RAW_MANIFEST.json',dict(F0_sha256=F0,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,raw_bytes=raw_bytes,files=files))
    save(HERE/'RESTORE_RECEIPT.json',dict(archive_sha256=sha(archive),files=len(files),bytes=raw_bytes,
         all_archived_bytes_independently_streamed_and_rehashed=True,new_GPU_launches=0))
    save(HERE/'PHYSICAL_LAYOUTS.json',physical)
    save(HERE/'COMPLETE_SUPPORT_AND_ASSIGNMENT.json',supports)
    save(HERE/'INPUT_IDENTITY.json',identities)
    save(HERE/'FULL_VECTOR_RESULTS.json',dict(pairs=pairs,complete_vectors=vectors))
    save(HERE/'RESULT.json',dict(status='ALIGNMENT_DIAGNOSTIC_EXECUTED_AND_AUDITED',F0_sha256=F0,
         attempts=7,graph_calls=7,completed_numerical_graphs=5,failed_graphs=2,expected_negative_failures=2,unexpected_failures=0,unstarted=0,
         owned_wall_s=owned,raw_bytes=raw_bytes,compressed_raw_bytes=archive.stat().st_size,raw_files=len(files),
         processes=processes,pairs=pairs,max_actual_gap_ms=max(p['observer_max_actual_gap_ms'] for p in processes),
         peak_sampled_worker_RSS=max(p['peak_sampled_RSS'] for p in processes),
         numerical_candidate='QH_C unchanged',Q0_common_q1_success=True,PQ_independent_mask_success=True,
         q1_two_layout_full_vector_comparison='NOT_APPLICABLE: original +32 layout failed; its missing output remains missing',
         dynamic_faulting_callsite_confirmed=False,actual_alignment_bytes=64,
         original_S1_attempts=2,original_S1_owned_seconds=original['owned_wall_s'],original_S1_unstarted=159,
         original_review_source_F0_input_binary_and_raw_unchanged=True,
         model_requests=0,extra_probes=0,warmups=0,retries=0,eighth_attempt=False,
         S2='NOT_ADMITTED_UNSTARTED',S3='NOT_ADMITTED_UNSTARTED',
         end_to_end_speedup=None,shader_timing=None,DRAM=None,cache=None,XMX=None,residency=None,PPA=None,
         next_panel='A separately approved finite operator numerical panel may be proposed; this diagnostic is not broad numerical qualification or an S2/S3 gate',
         modules_before=before,modules_after=modules()))
    print(json.dumps(dict(attempts=7,completed=5,expected_failed=2,unstarted=0,owned_seconds=owned,raw_bytes=raw_bytes,
                         archive_bytes=archive.stat().st_size,pairs=pairs)))


if __name__=='__main__':main()
