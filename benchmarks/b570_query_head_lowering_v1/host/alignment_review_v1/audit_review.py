"""Pure CPU audit of metadata/byte addresses. No backend initialization or computation."""
import collections
import hashlib
import io
import json
import pathlib
import struct
import subprocess
import sys
import unittest
import zipfile

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'));sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
from common import load,save,sha,modules
from conditions import descriptor,span
import core


def main():
    before=modules();output=ROOT/'host_outputs/alignment_review_v1'
    rows=[json.loads(x) for x in (output/'METADATA.jsonl').read_text().splitlines()]
    assert rows[0]['event']=='MODULES' and rows[-1]['event']=='CLOSE'
    for record in (rows[0],rows[-1]):
        names=[pathlib.Path(p).name.lower() for p in record['modules']]
        assert 'ggml-base.dll' in names
        assert not any(any(x in n for x in ('vulkan','ggml-cpu','igvk','llama','cuda')) for n in names)
    graphs=rows[1:-1];assert len(graphs)==288
    old_manifest=load(ROOT/'host/S1_RAW_MANIFEST.json')
    assert sha(ROOT/'host/S1_RAW.zip')==old_manifest['archive_sha256']
    with zipfile.ZipFile(ROOT/'host/S1_RAW.zip') as z:
        rawname=next(x for x in z.namelist() if x.endswith('/raw.jsonl') and x.startswith('36e61c'))
        census=[json.loads(line) for line in z.read(rawname).splitlines() if json.loads(line)['event']=='CAPABILITY']
    old={(core.sha(r['cell']),r['mode']):r for r in census}
    inputs={core.sha(r['cell']):r for r in load(ROOT/'host/S1_INPUTS.json')}
    seen=set();matches=0;bounds=0;addresses=0;mask_addresses=0;conditions=[];signatures={};first=None
    for row in graphs:
        cell=core.sha(row['cell']);mode=row['mode'];policy=row['policy'];key=cell,mode,policy
        assert key not in seen;seen.add(key)
        tensors={r['ctx_id']:r for r in row['tensors']}
        if policy==0 and mode!='QB4':
            assert len(row['walk'])==len(old[cell,mode]['nodes'])
            for actual,expected in zip(row['walk'],old[cell,mode]['nodes']):
                assert all(actual[k]==expected[k] for k in ('id','op','type','ne','nb','view_offset','op_parameters'))
            matches+=1
        for t in tensors.values():
            size=4 if t['type']=='f32' else 2
            assert span(t['ne'],t['nb'],size)==t['bytes']
            if t['view_root']!=-1:
                root=tensors[t['view_root']]
                assert root['view_root']==-1
                assert t['view_offset']+t['bytes']<=root['bytes']
                bounds+=1
        ops=[tensors[i] for i in row['execution_order'] if tensors[i]['op'] not in ('NONE','VIEW','RESHAPE','PERMUTE','TRANSPOSE')]
        signature=[{k:t[k] for k in ('op','type','ne','nb','op_parameters')} for t in ops]
        if policy==0:signatures[cell,mode]=signature
        else:assert signature==signatures[cell,mode],'candidate changed arithmetic operator metadata'
        g=row['cell']['geometry'];n,q,h,hk=(g[k] for k in ('n','q','h','hk'))
        sourcepath=pathlib.Path(inputs[cell]['path']);assert sha(sourcepath)==inputs[cell]['sha256']
        source=sourcepath.read_bytes();qbytes=source[28:28+128*q*h*4]
        mb=source[-32*n*4:]
        qt=tensors[row['Q']];prefix=32 if policy==0 else 0
        assert qt['view_offset']==prefix
        physical=bytes(prefix)+qbytes
        for j in range(q):
            for head in range(h):
                for d in range(128):
                    pos=qt['view_offset']+d*qt['nb'][0]+j*qt['nb'][1]+head*qt['nb'][2]
                    expect=4*((j*h+head)*128+d)
                    assert physical[pos:pos+4]==qbytes[expect:expect+4]
                    addresses+=1
        root_data={row['mask']:mb}
        for slab in row['mask_slabs']:
            root_data[slab['ctx_id']]=mb[slab['source_offset']:slab['source_offset']+slab['bytes']]
        def mask_at(t,idx):
            if t['op']=='REPEAT':
                src=tensors[t['src'][0]]
                return mask_at(src,[i%d for i,d in zip(idx,src['ne'])])
            root=t['view_root'] if t['view_root']!=-1 else t['ctx_id']
            at=t['view_offset']+sum(i*s for i,s in zip(idx,t['nb']))
            assert at+4<=len(root_data[root])
            return root_data[root][at:at+4]
        probs=[t for t in ops if t['op']=='SOFT_MAX']
        for j in range(q):
            prob=probs[j if mode=='PQ' and q>1 else 0];mt=tensors[prob['src'][1]]
            for head in range(h):
                col=j if mode=='MQ' or q==1 else 0
                folded=head*q+j if mode in ('QH_C','QH_D') and q>1 else head
                batch=j if mode in ('QB4','REPEAT4') and q>1 else 0
                for k in range(n):
                    idx=[k,col,folded%mt['ne'][2],batch%mt['ne'][3]]
                    assert mask_at(mt,idx)==mb[(j*n+k)*4:(j*n+k+1)*4]
                    mask_addresses+=1
        for t in ops:
            if t['op']=='SOFT_MAX':requirement='ZERO_DELTA_GENERIC_PUSH_CONSTANT';allow=True;site='13882 -> 12278 -> 2586/2595 (no softmax specialization)'
            elif t['op']=='MUL_MAT' and t['ne'][1]==1:requirement='ZERO_DELTA_GENERIC_MATVEC';allow=False;site='10263/10265 -> 9831..9833 -> 8301'
            elif t['op']=='MUL_MAT':requirement='MATRIX_PATH_SEPARATE_RAW_DESCRIPTOR_OFFSETS';allow=None;site='10267 -> ggml_vk_mul_mat_q_f16; not the 9833 call'
            elif t['op'] in ('CONT','REPEAT'):requirement='UNARY_ELEMENT_DELTA_PACKED_16_BITS';allow=True;site='13434/13459 -> 12277 -> 12125'
            elif t['op']=='CONCAT':requirement='CONCAT_ELEMENT_DELTA_PACKED_16_8_8_BITS';allow=True;site='13267 -> 12277 -> 12199'
            else:raise AssertionError(t['op'])
            for role,operand in [('dst',t)]+[(f'src{i}',tensors[c]) for i,c in enumerate(t['src'])]:
                size=4 if operand['type']=='f32' else 2
                delta=operand['view_offset'];root=operand['view_root'] if operand['view_root']!=-1 else operand['ctx_id']
                conditions.append(dict(cell_sha256=cell,mode=mode,policy=policy,node=t['ctx_id'],op=t['op'],operand=role,
                    tensor=operand['ctx_id'],root=root,ne=operand['ne'],nb=operand['nb'],root_relative_bytes=delta,
                    element_size=size,span_bytes=operand['bytes'],root_bytes=tensors[root]['bytes'],bounds='PASS',
                    physical_root_offset=None,device_alignment=None,actual_descriptor_alignment='UNKNOWN',
                    offset_formula='O_root + '+str(delta),subbuffer_allow_misalign=allow,effective_requirement=requirement,
                    source_call=site,
                    hypothetical_aligned_root_deltas={str(a):descriptor(delta,a,size)[1] for a in (16,32,64,128,256,4096)}))
        if first is None and policy==0 and mode=='MQ' and q==1 and n==63 and hk==8:
            first=dict(first_executable=ops[0],Q=qt,K=tensors[row['K']],V=tensors[row['V']],mask=tensors[row['mask']],
                       graph_order=[t['op'] for t in ops],source_route='general matvec: K contiguous, no Hadamard hint, dst.ne1=1; 9833 src1=Q',
                       dynamic_trace_confirmed=False)
    assert matches==80
    stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_conditions.py')
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    save(HERE/'CPU_TESTS.json',dict(success=result.wasSuccessful(),methods=result.testsRun,log=stream.getvalue(),
         graphs_metadata_only=288,old_census_metadata_matches=matches,flattened_view_bounds_checked=bounds,
         q_byte_address_checks=addresses,mask_byte_address_checks=mask_addresses,
         arithmetic_node_metadata_preserved_all_policies=True,device_alignment=None,
         GPU_launches=0,device_queries=0,model_requests=0,graph_computes=0,modules_before=before,modules_after=modules()))
    assert result.wasSuccessful()
    save(output/'OFFSET_CONDITIONS.json',dict(scope='All6 representations, all16 cells, original/Q-rebase/Q-rebase+PQ-slab policies. Symbolic addresses; hypothetical alignments are not device measurements.',
         device_alignment=None,physical_root_offsets=None,conditions=conditions))
    save(HERE/'FIRST_GRAPH_STATIC_TRACE.json',first)
    archive=HERE/'CPU_METADATA.zip'
    paths=[output/'CELLS.json',output/'METADATA.jsonl']
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for path in paths:z.write(path,path.name)
    with zipfile.ZipFile(archive) as z:
        for path in paths:assert hashlib.sha256(z.read(path.name)).hexdigest()==sha(path)
    save(HERE/'CPU_METADATA_MANIFEST.json',dict(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
         files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in paths],all_archived_bytes_rehashed=True))
    print(dict(metadata_graphs=288,census_matches=matches,view_bounds=bounds,Q_addresses=addresses,mask_addresses=mask_addresses,
               unit_methods=result.testsRun,success=result.wasSuccessful(),device_queries=0,computes=0))


if __name__=='__main__':main()
