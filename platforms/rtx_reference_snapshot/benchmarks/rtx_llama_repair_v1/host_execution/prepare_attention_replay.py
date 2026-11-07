"""Bind actual layer-0 operands and explicit extent-only counterfactuals."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct


def sha(b):
    return hashlib.sha256(b).hexdigest()


def payload(root, meta):
    b = (root/meta['file']).read_bytes()
    assert len(b)==meta['bytes'] and sha(b)==meta['sha256']
    return b


def packed(data, meta, shape=None):
    shape = shape or meta['ne']
    size = {'f32':4,'f16':2}[meta['type']]
    output = bytearray()
    for reverse in itertools.product(*[range(n) for n in reversed(shape)]):
        index = tuple(reversed(reverse))
        offset = sum(i*s for i,s in zip(index,meta['nb']))
        output.extend(data[offset:offset+size])
    assert len(output)==size*__import__('math').prod(shape)
    return bytes(output)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    checkpoint=json.loads((a.checkpoint/'CHECKPOINT.json').read_text())
    assert checkpoint['same_policy_own_path_vectors_equal'] and checkpoint['cycle']==8
    captures={};cases=[]
    def descriptor(root,meta):
        payload(root,meta)
        return {**{k:meta[k] for k in ('type','ne','nb','bytes','sha256')},'file':str((root/meta['file']).resolve())}
    for side in ('scalar','batch'):
        root=a.checkpoint/side
        rows=[json.loads(l) for l in (root/'trace/INDEX.jsonl').read_text().splitlines()]
        chosen={}
        for name in ('kq-0','kq_soft_max-0','kqv-0'):
            matches=[r for r in rows if r['name']==name and r['caller_first_position']==checkpoint['base']]
            assert matches
            chosen[name]=min(matches,key=lambda r:r['occurrence'])
        captures[side]=(root,chosen)
        for name,meta in chosen.items():
            if meta['op']=='MUL_MAT':
                assert [i['source_index'] for i in meta['operator_inputs']]==[0,1]
                inputs=[descriptor(root,i) for i in meta['operator_inputs']]
            else:
                assert meta['op']=='SOFT_MAX' and [i['source_index'] for i in meta['operator_inputs']]==[1]
                inputs=[descriptor(root,chosen['kq-0']),descriptor(root,meta['operator_inputs'][0])]
            assert meta['ne'][1:]==[1,32,1], 'This first replay is the actual per-query path, not an inferred QB axis map'
            cases.append({'name':side+'_'+name.replace('-','_'),'kind':'own_path','op':meta['op'],
                          'backend':meta['scheduler_backend'],'op_params_i32':meta['op_params_i32'],'inputs':inputs,
                          'expected_file':str((root/meta['file']).resolve()),'expected_sha256':meta['sha256']})
    own={c['name']:c for c in cases}
    def write_input(name,meta,data,shape):
        size={'f32':4,'f16':2}[meta['type']];nb=[size]
        for n in shape[:-1]:nb.append(nb[-1]*n)
        path=a.out/(name+'.bin');path.write_bytes(data)
        assert len(data)==__import__('math').prod(shape)*size
        return {'file':str(path.resolve()),'type':meta['type'],'ne':shape,'nb':nb,'bytes':len(data),'sha256':sha(data)}
    def crop(desc,n,axis=0):
        shape=desc['ne'].copy();shape[axis]=n
        return write_input('crop_'+str(len(list(a.out.glob('*.bin')))),desc,packed(Path(desc['file']).read_bytes(),desc,shape),shape)
    def add(name,source,inputs,expected=None):
        item={k:source[k] for k in ('op','backend','op_params_i32')}
        item.update(name=name,kind='extent_or_operand_intervention',inputs=inputs)
        if expected:item.update(expected_file=expected['expected_file'],expected_sha256=expected['expected_sha256'])
        cases.append(item)
    sq,bq=own['scalar_kq_0'],own['batch_kq_0']
    ss,bs=own['scalar_kq_soft_max_0'],own['batch_kq_soft_max_0']
    sv,bv=own['scalar_kqv_0'],own['batch_kqv_0']
    assert sq['inputs'][0]['ne'][1]==768 and bq['inputs'][0]['ne'][1]==1024
    def content(desc,shape=None):return packed(Path(desc['file']).read_bytes(),desc,shape)
    q_equal=content(sq['inputs'][1])==content(bq['inputs'][1])
    visible=checkpoint['base']+1
    sa=sq['inputs'][0]['ne'].copy();sa[1]=visible
    ba=bq['inputs'][0]['ne'].copy();ba[1]=visible
    k_equal=content(sq['inputs'][0],sa)==content(bq['inputs'][0],ba)
    raw_equal=content(ss['inputs'][0])==content(bs['inputs'][0],[768,1,32,1])
    add('batch_softmax_crop768',bs,[crop(x,768) for x in bs['inputs']],ss)
    padded=[]
    for i,desc in enumerate(ss['inputs']):
        data=content(desc);columns=__import__('math').prod(desc['ne'][1:]);result=bytearray()
        for col in range(columns):
            result.extend(data[col*768*4:(col+1)*768*4]);result.extend(struct.pack('<f',0.0 if i==0 else float('-inf'))*256)
        shape=desc['ne'].copy();shape[0]=1024
        padded.append(write_input('scalar_softmax_pad_'+str(i),desc,bytes(result),shape))
    add('scalar_softmax_pad1024',ss,padded,bs)
    add('batch_V_crop_scalar_prob',sv,[crop(bv['inputs'][0],768),sv['inputs'][1]],sv)
    probs=content(sv['inputs'][1]);padded_probs=b''.join(probs[i*768*4:(i+1)*768*4]+b'\0'*(256*4) for i in range(32))
    pp=write_input('scalar_prob_pad1024',sv['inputs'][1],padded_probs,[1024,1,32,1])
    add('batch_V_scalar_prob_pad1024',bv,[bv['inputs'][0],pp])
    add('scalar_V_batch_prob_crop768',sv,[sv['inputs'][0],crop(bv['inputs'][1],768)])
    manifest={'cases':cases,'source_checkpoint':str(a.checkpoint),'source_checkpoint_sha256':sha((a.checkpoint/'CHECKPOINT.json').read_bytes()),
              'comparisons':{'query_logical_bits_equal':q_equal,'visible_K_logical_bits_equal':k_equal,'raw_QK_first768_equal':raw_equal},
              'scope':'First query of actual C_PQ replay at the captured candidate checkpoint; inputs and extents are interventions, not substituted model outputs.',
              'operator_replays_planned':2*len(cases),'model_requests':0}
    (a.out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    print(manifest['comparisons'],'replays',manifest['operator_replays_planned'])


if __name__=='__main__':
    main()
