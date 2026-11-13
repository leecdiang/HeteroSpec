"""Independent CPU audit of captured decision-vector ownership and mask geometry."""
import array
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import numpy as np


def audit_worker(worker,layers,recover_append_offsets=False):
    worker=Path(worker);capture=worker/'capture'
    events=[json.loads(line) for line in (capture/'observer.jsonl').read_bytes().splitlines()]
    native=[json.loads(line) for line in (worker/'trace.jsonl').read_bytes().splitlines()]
    decodes=[event for event in native if event.get('event')=='decode']
    vector_file=(capture/'logits.f32').open('rb');mask_file=(capture/'masks.bin').open('rb')
    ownership={};vectors=[];geometry=[];next_vector=0;next_mask=0;offset_errors=0
    for event in events:
        if event['event']=='decision_vector':
            offset=event['offset'];size=event['floats']*4
            if offset!=next_vector:
                if not recover_append_offsets:raise ValueError('noncontiguous/duplicate vector bytes')
                offset_errors+=1;offset=next_vector
            vector_file.seek(offset);data=vector_file.read(size)
            if len(data)!=size:raise ValueError('truncated vector')
            integers=np.frombuffer(data,dtype='<u4')
            if np.any((integers & np.uint32(0x7f800000))==np.uint32(0x7f800000)):raise ValueError('nonfinite raw logits')
            key=(event['decode_id'],event['row'])
            if key in ownership:raise ValueError('duplicate vector owner')
            ownership[key]=event
            decode=decodes[event['decode_id']-1]
            if (event['role'],event['input_id'],event['position'])!=(decode['role'],decode['tokens'][event['row']],decode['positions'][event['row']]):
                raise ValueError('vector does not own its native prefix/row')
            vectors.append({'role':event['role'],'decode_id':event['decode_id'],'row':event['row'],'position':event['position'],'sha256':hashlib.sha256(data).hexdigest()})
            next_vector+=size
        elif event['event']=='sample_owner':
            row=event['row']
            if row<0:
                available=sorted(r for d,r in ownership if d==event['decode_id'])
                if not available:raise ValueError('sample has no pending logit owner')
                row=available[row]
            if (event['decode_id'],row) not in ownership:raise ValueError('sample consumed an uncaptured logit row')
        elif event['event']=='geometry':
            if event['mask_offset']!=next_mask:
                if not recover_append_offsets:raise ValueError('noncontiguous/duplicate mask bytes')
                offset_errors+=1
            mask_file.seek(next_mask);data=mask_file.read(event['mask_bytes']);next_mask+=len(data)
            if len(data)!=event['mask_bytes']:raise ValueError('truncated mask')
            mask=event['mask'];shape=mask['ne'];strides=mask['nb'];fmt='<f' if mask['type']=='f32' else '<e' if mask['type']=='f16' else None
            if fmt is None:raise ValueError('unsupported mask type')
            dtype='<u4' if mask['type']=='f32' else '<u2'
            words=np.ndarray(tuple(reversed(shape)),dtype=dtype,buffer=data,strides=tuple(reversed(strides)))
            exponent=np.uint32(0x7f800000) if mask['type']=='f32' else np.uint16(0x7c00)
            mantissa=np.uint32(0x007fffff) if mask['type']=='f32' else np.uint16(0x03ff)
            special=(words & exponent)==exponent
            if np.any(special & ((words & mantissa)!=0)):raise ValueError('NaN mask')
            visible=np.count_nonzero(~special,axis=-1).ravel().tolist()
            if visible!=event['visible_keys']:raise ValueError('raw visible-key reconstruction differs')
            if max(visible)>event['physical_key_extent']:raise ValueError('visible keys exceed physical key extent')
            if event['q_occupied']!=event['Q']['ne'][1]*event['Q']['ne'][3]:raise ValueError('occupied q differs')
            geometry.append(event)
    if vector_file.read(1) or mask_file.read(1):raise ValueError('unaccounted raw bytes')
    vector_file.close();mask_file.close()
    if not set(layers)<={event['layer'] for event in geometry}:raise ValueError('required target layers absent')
    commits=[event['id'] for event in native if event.get('event')=='committed_token']
    records=[json.loads(path.read_bytes()) for path in (worker/'requests').glob('*/RECORD.json')]
    captures=[record for record in records if record['mode']=='heavy']
    if len(captures)!=1 or commits!=captures[0]['output']['ids']:raise ValueError('native committed sequence differs from endpoint')
    return {'status':'APPEND_STREAM_RECOVERED_METADATA_FAILURE' if offset_errors else 'PASS_RAW_OWNERSHIP_AND_GEOMETRY',
            'offset_metadata_errors':offset_errors,'append_order_reconstruction':recover_append_offsets,
            'vectors':len(vectors),'geometry_records':len(geometry),
            'first_middle_last_layers':list(layers),'raw_logit_bytes':next_vector,'raw_mask_bytes':next_mask,
            'q_gt_one_verification':any(event['phase']=='continuation' and event['q_occupied']>1 for event in geometry),
            'maximum_visible_keys':max(max(event['visible_keys']) for event in geometry),
            'rejected_rows_retained':True,'committed_output_ids':len(commits)}


if __name__=='__main__':
    print(json.dumps(audit_worker(sys.argv[1],[int(x) for x in sys.argv[2].split(',')]),indent=2))
