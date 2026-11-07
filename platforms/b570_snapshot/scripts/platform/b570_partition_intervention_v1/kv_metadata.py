"""Independently parse pinned Qwen3 one-stream checkpoint position/sequence metadata."""
import gzip, json, struct
from pathlib import Path

def verify_metadata(root):
    root=Path(root);errors=[];count=0
    for file in (root/'artifacts/b570_partition_intervention_v1/raw').glob('*/*/record.json'):
        row=json.loads(file.read_text(encoding='utf-8'))
        capture=file.parent/'capture.json'
        if not row['execution_valid'] or not capture.exists():continue
        c=json.loads(capture.read_text(encoding='utf-8'))
        if not c['forked']:continue
        cp=c['checkpoint']
        for logical,obj in row['state_objects'].items():
            count+=1
            with gzip.open(file.parent/obj['compressed'],'rb') as stream:
                archlen=struct.unpack('<I',stream.read(4))[0];arch=stream.read(archlen)
                nstream,ncells=struct.unpack('<II',stream.read(8))
                if arch!=b'qwen3' or nstream!=1 or ncells!=cp['position']:
                    errors.append('serialized model/stream/cell-count mismatch '+str(file)+' '+logical);continue
                positions=[]
                for _ in range(ncells):
                    pos,nseq=struct.unpack('<iI',stream.read(8))
                    seqs=struct.unpack('<'+'i'*nseq,stream.read(4*nseq));positions.append(pos)
                    if seqs!=(0,):errors.append('serialized sequence membership mismatch '+str(file))
                if positions!=list(range(cp['position'])):errors.append('serialized KV positions differ from committed prefix '+str(file))
                v_trans,layers=struct.unpack('<II',stream.read(8))
                if layers!=36 or v_trans!=1:errors.append('serialized frozen Qwen3-8B layer/KV layout mismatch '+str(file))
    return count,errors
