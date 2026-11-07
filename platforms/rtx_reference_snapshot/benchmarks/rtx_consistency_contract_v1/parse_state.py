"""Pinned b10839 Qwen3/F16 state reader; reject unsupported layouts."""
import array, hashlib, struct
from pathlib import Path

class State:
    def __init__(self,path):
        self.data=Path(path).read_bytes();self.offset=0
        n=self.scalar('I');self.arch=self.take(n).decode('ascii');assert self.arch=='qwen3'
        assert self.scalar('I')==1,'Only one KV stream supported'
        self.cells=self.scalar('I');assert 0<self.cells<=4096
        self.positions=[]
        for _ in range(self.cells):
            p=self.scalar('i');ns=self.scalar('I');seq=[self.scalar('i') for _ in range(ns)]
            assert seq==[0];self.positions.append(p)
        assert len(set(self.positions))==self.cells
        self.v_trans=self.scalar('I');assert self.v_trans in [0,1]
        self.layers=self.scalar('I');assert self.layers==36
        self.slices=[]
        for layer in range(self.layers):
            kind=self.scalar('i');row=self.scalar('Q');assert kind==1 and row==2048
            start=self.offset;self.take(row*self.cells)
            self.slices.append({'layer':layer,'kind':'K','offset':start,'bytes':row*self.cells,'row_bytes':row,'transposed':False})
        for layer in range(self.layers):
            kind=self.scalar('i');assert kind==1
            if self.v_trans:
                el=self.scalar('I');width=self.scalar('I');assert el==2 and width==1024
                row=el*width
            else:row=self.scalar('Q');assert row==2048
            start=self.offset;self.take(row*self.cells)
            self.slices.append({'layer':layer,'kind':'V','offset':start,'bytes':row*self.cells,'row_bytes':row,'transposed':bool(self.v_trans)})
        assert self.offset==len(self.data),'Unexpected trailing state bytes'
    def scalar(self,fmt):
        v=struct.unpack_from('<'+fmt,self.data,self.offset)[0];self.offset+=struct.calcsize('<'+fmt);return v
    def take(self,n):
        assert self.offset+n<=len(self.data)
        b=self.data[self.offset:self.offset+n];self.offset+=n;return b
    def tensor(self,s):return self.data[s['offset']:s['offset']+s['bytes']]
    def rows(self,s):
        b=self.tensor(s)
        if s['transposed']:
            a=array.array('H',b);return [a[i::self.cells].tobytes() for i in range(self.cells)]
        return [b[i*s['row_bytes']:(i+1)*s['row_bytes']] for i in range(self.cells)]

def compare(a,b,prompt_count):
    assert a.arch==b.arch and a.positions==b.positions and a.slices==b.slices
    result=[]
    for sa,sb in zip(a.slices,b.slices):
        ba=a.tensor(sa);bb=b.tensor(sb)
        differing=[]
        if ba!=bb:differing=[a.positions[i] for i,(ra,rb) in enumerate(zip(a.rows(sa),b.rows(sb))) if ra!=rb]
        result.append({**sa,'a_sha256':hashlib.sha256(ba).hexdigest(),'b_sha256':hashlib.sha256(bb).hexdigest(),
                       'different_positions':differing,'prompt_different_positions':[p for p in differing if p<prompt_count]})
    return {'positions':a.positions,'layers':a.layers,'v_transposed':bool(a.v_trans),'tensors':result,
            'prompt_kv_equal':not any(x['prompt_different_positions'] for x in result),
            'different_tensor_count':sum(bool(x['different_positions']) for x in result),
            'first_different_position':min((p for x in result for p in x['different_positions']),default=None)}
