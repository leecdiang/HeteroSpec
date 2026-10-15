"""Offline AV-only counterfactual INPUT preparation; no host implementation/start."""
import hashlib
import struct
from legacy import HERE,OLD,ROOT,load,save,sha,need
from reference import decode

def main():
    dest=HERE/'av_proposal_inputs';dest.mkdir(exist_ok=False)
    review=load(HERE/'OFFLINE_REVIEW.json');item=next(i for i in load(OLD/'INPUTS.json') if tuple(i['cell']['geometry'][k] for k in ('q','n','hk'))==(2,63,8))
    slot=next(x['slot'] for x in review['actual_AV_descriptors'] if x['slot']['input_id']==item['id'] and x['slot']['mode']=='PQ' and x['slot']['repeat']==0)
    raw=ROOT/'host_outputs/supervised_numerical_v3/b570-supervised-numerical-v3-20261015-01'/slot['id']
    prob=(raw/'normalized/softmax.f32').read_bytes();rounded=b''.join(struct.pack('<f',struct.unpack('<e',struct.pack('<e',x[0]))[0]) for x in struct.iter_unpack('<f',prob))
    v=decode(__import__('pathlib').Path(item['path']).read_bytes())['raw'][2]
    records=[]
    for name,b in (('V.f16',v),('probability.f32',prob),('probability_F16_rounded_back_F32.f32',rounded)):
        path=dest/name;path.write_bytes(b);records.append(dict(path=str(path),bytes=len(b),sha256=sha(path)))
    save(HERE/'AV_F0_PROPOSAL.json',dict(status='PROPOSAL_ONLY_NOT_EXECUTABLE_NOT_AUTHORIZED',run_id_suggestion='b570-av-only-counterfactual-proposal-20261016-01',
        original_input=item,source_v3_slot=slot,inputs=records,source_review_sha256=sha(HERE/'OFFLINE_REVIEW.json'),
        census_hosts=1,census_descriptions=3,numerical_hosts=6,graph_calls=6,independent_repeats=2,
        conditions=[dict(id='A',AV_shape=[128,2,8,1],src1_shape=[63,2,8,1],probability='original F32',V='shared original F16',precision='inherited default'),
            dict(id='B',AV_shape=[128,1,16,1],src1_shape=[63,1,16,1],probability='same F32 bytes logically permuted into r=h*2+j; CPU materialization charged',V='shared original F16',precision='inherited default'),
            dict(id='C',AV_shape=[128,1,16,1],src1_shape=[63,1,16,1],probability='F32 value first rounded to F16 then exactly stored back to F32, then same folded mapping as B',V='shared original F16',precision='inherited default')],
        question='B versus C isolates probability operand rounding at the same matvec geometry. A versus B combines source-selected matmat/matvec and reduction effects. A versus C tests whether operand rounding alone suffices; mismatch does not identify an accumulator or hardware tree.',
        output='Complete logical AV output only. QK and softmax are frozen input evidence, not executed. Two new processes per condition, no retry/warmup/model/probe.',
        proposed_engineering_seconds=180,proposed_per_host_seconds=60,proposed_artifact_bytes=256*1024**2,
        executable=None,executable_sha256=None,entry=None,
        prerequisites=['Separate CPU-only AV host implementation/serializer/input ownership and complete vector tests','Complete source/binary/driver/supervisor binding and exact executable F0','Separate author GPU approval; not included in v4 69 hosts'],
        shader_changes=False,new_GPU_hosts=0,device_queries=0,graph_computes=0))
    print(dict(counterfactual_inputs=records,GPU_started=0,executable_F0=False))

if __name__=='__main__':main()
