"""Read GGUF metadata, not CUDA. Class coverage is not numerical eligibility."""
import argparse
from collections import defaultdict
from pathlib import Path
import struct
from support import fresh, need


def inventory(path):
    with Path(path).open('rb') as f:
        def rd(fmt):
            n=struct.calcsize('<'+fmt)
            b=f.read(n)
            need(len(b)==n,'Truncated GGUF')
            return struct.unpack('<'+fmt,b)[0]
        def string():
            return f.read(rd('Q')).decode('utf8')
        def skip(t):
            sizes={0:1,1:1,2:2,3:2,4:4,5:4,6:4,7:1,10:8,11:8,12:8}
            if t in sizes:
                f.seek(sizes[t],1)
            elif t==8:
                f.seek(rd('Q'),1)
            elif t==9:
                kind,n=rd('I'),rd('Q')
                for _ in range(n):
                    skip(kind)
            else:
                raise ValueError('Unknown GGUF type')
        need(f.read(4)==b'GGUF' and rd('I')==3,'Fixed GGUFv3')
        count,metadata=rd('Q'),rd('Q')
        alignment=32
        for _ in range(metadata):
            key=string();kind=rd('I')
            if key=='general.alignment':
                need(kind==4,'GGUF alignment encoding');alignment=rd('I')
                need(1<=alignment<=4096 and alignment&(alignment-1)==0,'GGUF alignment')
            else:skip(kind)
        tensors=[]
        for _ in range(count):
            name=string()
            dims=[rd('Q')for _ in range(rd('I'))]
            kind,offset=rd('I'),rd('Q')
            if kind in (12,14):
                tensors.append(dict(name=name,type='Q4_K'if kind==12 else'Q6_K',
                                    dimensions=dims,gguf_offset=offset,
                                    excluded_cpu_embedding=name=='token_embd.weight'))
        data_offset=(f.tell()+alignment-1)//alignment*alignment
        for t in tensors:t['file_offset']=data_offset+t['gguf_offset']
    groups=defaultdict(list)
    for t in tensors:
        if not t['excluded_cpu_embedding']:
            groups[(t['type'],tuple(t['dimensions']))].append(t['name'])
    def order(name):
        return (int(name.split('.')[1]) if name.startswith('blk.') else 999,name)
    classes=[dict(type=typ,dimensions=list(dims),tensors=sorted(names,key=order),
                  first_tensor=sorted(names,key=order)[0],raw_activation='NOT_YET_BOUND',
                  independent_gold_and_quantized_bytes='NOT_YET_BOUND')
             for (typ,dims),names in sorted(groups.items())]
    return dict(status='CPU_METADATA_ONLY_NOT_F0',tensor_count=count,tensors=tensors,
                classes=classes,candidate_q=[1,3,4,7,20,30,31,32],
                gold_columns_per_class=[32,4],
                required_new_scalar_gold_lower_bound=len(classes)*36,
                minimum_gold_plus_S2_plus_reserve=len(classes)*36+72+16,
                candidate_and_bridge_requests_not_included_in_lower_bound=True,
                eligibility='NOT_RUN')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    fresh(a.out,inventory(a.model))


if __name__=='__main__':
    main()
