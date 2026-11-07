"""Bounded GGUF v2/v3 metadata inspection; does not load tensor weights or generate."""
from __future__ import annotations
import argparse, collections, json, struct
from pathlib import Path
from common import need, file_hash, TARGET_SHA256
FIXED={0:('B',1),1:('b',1),2:('H',2),3:('h',2),4:('I',4),5:('i',4),6:('f',4),7:('?',1),10:('Q',8),11:('q',8),12:('d',8)}

def inspect(path):
    size=Path(path).stat().st_size
    with Path(path).open('rb') as f:
        def take(n):
            need(0<=n<=64*1024*1024, 'metadata read limit'); b=f.read(n)
            need(len(b)==n,'truncated GGUF'); return b
        def num(fmt): return struct.unpack('<'+fmt,take(struct.calcsize('<'+fmt)))[0]
        def text(keep=True):
            n=num('Q'); need(n<=16*1024*1024 and f.tell()+n<=size,'GGUF string bound')
            if keep:return take(n).decode('utf-8')
            f.seek(n,1); return None
        def value(t,keep=True):
            if t in FIXED:
                x=num(FIXED[t][0]); return x if keep else None
            if t==8:return text(keep)
            if t==9:
                typ,n=num('I'),num('Q'); need(n<=2000000 and typ!=9,'GGUF array bound')
                if typ in FIXED:
                    count=n*FIXED[typ][1]; need(f.tell()+count<=size,'GGUF array size')
                    f.seek(count,1)
                else:
                    need(typ==8,'unknown GGUF array type')
                    for _ in range(n): text(False)
                return {'element_type':typ,'length':n}
            raise ValueError('unknown GGUF type')
        need(take(4)==b'GGUF','not GGUF');version=num('I');need(version in (2,3),'unsupported GGUF')
        nt,nm=num('Q'),num('Q');need(nt<=200000 and nm<=100000,'metadata bounds')
        meta={}
        for _ in range(nm):
            key=text();need(key not in meta,'duplicate GGUF metadata');typ=num('I')
            keep=key.startswith(('general.','qwen3.')) or key in ('tokenizer.ggml.tokens','tokenizer.chat_template','tokenizer.ggml.model')
            v=value(typ,keep)
            if keep:meta[key]=v
        types=collections.Counter();q8_matrix_count=0
        for _ in range(nt):
            name=text();nd=num('I');need(1<=nd<=4,'tensor rank')
            dims=[num('Q') for _ in range(nd)];typ=num('I');num('Q');types[typ]+=1
            if nd>=2 and name.startswith('blk.') and typ==8:q8_matrix_count+=1
        return {'version':version,'bytes':size,'metadata':meta,'tensor_types':dict(types),
                'q8_block_matrices':q8_matrix_count,'metadata_end':f.tell()}

def target_contract(info):
    m=info['metadata']
    for k,v in {'general.architecture':'qwen3','qwen3.block_count':40,
                'qwen3.embedding_length':5120,'qwen3.attention.head_count':40,
                'qwen3.attention.head_count_kv':8}.items():
        need(m.get(k)==v, 'unexpected target '+k)
    need(m.get('general.file_type')==7 and info['q8_block_matrices']>0,'target is not Q8_0')
    need(m.get('tokenizer.ggml.tokens',{}).get('length')==151936,'target vocabulary size')
    return info

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('model',type=Path)
    ap.add_argument('--target',action='store_true');ap.add_argument('--hash',action='store_true')
    a=ap.parse_args();x=inspect(a.model)
    if a.target:target_contract(x)
    if a.hash:
        x['sha256']=file_hash(a.model)
        if a.target:need(x['sha256']==TARGET_SHA256,'official target bytes differ')
    print(json.dumps(x,indent=2))
