"""Read bounded GGUF v2/v3 metadata/tensor descriptors, not tensor values.

No GPU allocation. A type/shape inventory is NOT numerical or dispatch eligibility.
GGUF enum/source: ggml-org/llama.cpp at 0cae43063cf15170e91a2ff4d034da0ecef4a1b2.
"""
from __future__ import annotations
import argparse, collections, io, math, struct
from pathlib import Path
from experiment import require, save, sha
SCALAR={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
TYPE_NAMES={0:'F32',1:'F16',2:'Q4_0',3:'Q4_1',6:'Q5_0',7:'Q5_1',8:'Q8_0',9:'Q8_1',10:'Q2_K',11:'Q3_K',12:'Q4_K',13:'Q5_K',14:'Q6_K',15:'Q8_K',30:'BF16'}


class Reader:
    def __init__(self,f):
        self.f=f; self.size=f.seek(0,2);f.seek(0);self.work=0
    def raw(self,n):
        require(0<=n<=64*1024**2 and self.f.tell()+n<=self.size, 'Truncated/oversized GGUF field')
        value=self.f.read(n);require(len(value)==n,'Truncated');return value
    def num(self,fmt):return struct.unpack('<'+fmt,self.raw(struct.calcsize('<'+fmt)))[0]
    def string(self,keep=True):
        n=self.num('Q');require(n<=16*1024**2,'Oversized string')
        value=self.raw(n)
        return value.decode('utf8',errors='strict') if keep else None
    def value(self,typ,keep=True,depth=0):
        self.work+=1;require(self.work<=4000000 and depth<=2,'Metadata work bound')
        if typ in SCALAR:return self.num(SCALAR[typ])
        if typ==8:return self.string(keep)
        if typ==9:
            sub=self.num('I');count=self.num('Q');require(count<=2000000 and sub!=9,'Unsupported/oversized nested array')
            vals=[]
            for _ in range(count):
                v=self.value(sub,keep and count<=32,depth+1)
                if keep and count<=32:vals.append(v)
            return vals if keep and count<=32 else {'element_type':sub,'count':count,'values':'NOT_LOADED'}
        raise ValueError('Unknown GGUF metadata type')


def parse(f):
    r=Reader(f);require(r.raw(4)==b'GGUF','Not GGUF');version=r.num('I');require(version in (2,3),'Only GGUF2/3')
    nt,nm=r.num('Q'),r.num('Q');require(nt<=100000 and nm<=100000,'Header counts')
    meta={};keys=set()
    for _ in range(nm):
        key=r.string();require(key not in keys,'Duplicate metadata');keys.add(key);typ=r.num('I')
        keep=(key.startswith('general.') or any(x in key for x in ('.block_count','.embedding_length','.attention.','.context_length','.rope.')))
        v=r.value(typ,keep)
        if keep:meta[key]=v
    tensors=[];names=set();counts=collections.Counter()
    for _ in range(nt):
        name=r.string();require(name not in names,'Duplicate tensor');names.add(name);nd=r.num('I');require(1<=nd<=4,'Tensor rank')
        dims=[r.num('Q') for _ in range(nd)];require(all(0<d<=2**32 for d in dims),'Invalid dimensions')
        typ=r.num('I');offset=r.num('Q');require(offset<r.size,'Tensor offset outside file')
        counts[str(typ)]+=1;tensors.append(dict(name=name,shape=dims,type=typ,type_name=TYPE_NAMES.get(typ,'UNKNOWN_'+str(typ)),relative_offset=offset))
    alignment=meta.get('general.alignment',32);require(type(alignment) is int and 0<alignment<=65536 and alignment&(alignment-1)==0,'Alignment')
    start=(f.tell()+alignment-1)//alignment*alignment
    require(start<=r.size and all(start+t['relative_offset']<r.size for t in tensors),'Tensor data boundary')
    return dict(version=version,file_bytes=r.size,metadata=meta,tensor_count=nt,tensor_type_counts=dict(counts),tensors=tensors,
                tensor_data_offset=start,weight_data_read=False,dispatch_or_numeric_qualification='NOT_ESTABLISHED')


def kv_bytes(meta,context):
    arch=meta['general.architecture'];layers=meta[arch+'.block_count'];heads=meta[arch+'.attention.head_count_kv']
    qheads=meta[arch+'.attention.head_count'];emb=meta[arch+'.embedding_length']
    kd=meta.get(arch+'.attention.key_length',emb//qheads);vd=meta.get(arch+'.attention.value_length',kd)
    require(all(type(v) is int and v>0 for v in (context,layers,heads,kd,vd)), 'Dense KV geometry')
    return layers*context*heads*(kd+vd)*2


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('gguf');p.add_argument('out');p.add_argument('--hash',action='store_true');a=p.parse_args()
    with open(a.gguf,'rb') as f:result=parse(f)
    result['sha256']=sha(a.gguf) if a.hash else None;save(a.out,result)
