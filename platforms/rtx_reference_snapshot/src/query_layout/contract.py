"""Pure address/phase/cache contract; no inference or backend-support assertion."""
from dataclasses import dataclass
from itertools import product
import json
MAX=(1<<63)-1

def integer(value, *, positive=False):
    if type(value) is not int or value < (1 if positive else 0) or value > MAX:
        raise ValueError("expected bounded nonnegative integer")
    return value

@dataclass(frozen=True)
class View:
    shape: tuple[int,int,int,int]
    strides: tuple[int,int,int,int]
    backing_bytes: int
    item_bytes: int=4
    offset: int=0
    def __post_init__(self):
        if len(self.shape)!=4 or len(self.strides)!=4: raise ValueError("four axes required")
        for n in self.shape: integer(n,positive=True)
        for n in self.strides: integer(n)
        integer(self.item_bytes,positive=True);integer(self.backing_bytes,positive=True);integer(self.offset)
        end=self.offset+self.item_bytes+sum((n-1)*s for n,s in zip(self.shape,self.strides))
        if end>MAX or end>self.backing_bytes: raise ValueError("view exceeds backing allocation")
    def address(self, index):
        if len(index)!=4: raise ValueError("four indices required")
        for i,n in zip(index,self.shape):
            integer(i)
            if i>=n: raise ValueError("index out of range")
        return self.offset+sum(i*s for i,s in zip(index,self.strides))

def lift(query: View, mask: View):
    d,q,h,b=query.shape;n,m,b2,b3=mask.shape
    if b!=1 or q>4 or (m,b2,b3)!=(q,1,1):
        raise ValueError("this helper covers single-stream, q<=4, exact query/mask extent")
    def mapped(v,shape):
        a,c,e,_=v.strides
        return View(shape,(a,c,e,c),v.backing_bytes,v.item_bytes,v.offset)
    return mapped(query,(d,1,h,q)),mapped(mask,(n,1,1,q))

def phase_active(mask:int,role:str,phase:str)->bool:
    integer(mask)
    if mask>15 or role not in ('target','draft') or phase not in ('prefill','continuation'):
        raise ValueError("invalid phase policy")
    bit={('target','prefill'):1,('target','continuation'):2,('draft','prefill'):4,('draft','continuation'):8}[role,phase]
    return bool(mask&bit)

def graph_key(*,reference:str,state_recipe:str,role:str,phase:str,layout:str,signature:tuple):
    if not reference or not state_recipe or layout not in ('MQ','PQ','QB','GS'):
        raise ValueError("explicit reference, producer recipe and layout required")
    phase_active(3,role,phase)
    return (reference,state_recipe,role,phase,layout,signature)

if __name__=='__main__':
    q=View((4,3,2,1),(4,16,48,96),96)
    m=View((5,3,1,1),(4,20,60,60),60)
    qq,mm=lift(q,m)
    count=sum(q.address((i,j,a,0))==qq.address((i,0,a,j)) for i,j,a in product(range(4),range(3),range(2)))
    print(json.dumps({'status':'CPU_ADDRESS_EXAMPLE','query_addresses_equal':count,'expected':24,'query_shape':qq.shape,'mask_shape':mm.shape,'backend_support':'UNRESOLVED','new_native_executions':0}))
