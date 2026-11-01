"""Strided F32/F16/BF16 comparisons and same-prefix trace inspection.
Diagnostic tolerances never change endpoint qualification.
"""
from __future__ import annotations
import argparse
import itertools
import math
from pathlib import Path
import struct
from common import need, read, save, file_hash, confined

FORMATS={'f32':('<f',4),'f16':('<e',2),'bf16':(None,2)}

def scalar(payload,kind,offset):
    fmt,n=FORMATS[kind];need(offset>=0 and offset+n<=len(payload),'tensor address outside capture')
    b=payload[offset:offset+n]
    value=struct.unpack(fmt,b)[0] if fmt else struct.unpack('<f',b'\0\0'+b)[0]
    return b,value

def logical_values(payload,meta,row=None,axis=1):
    kind=meta['type'];need(kind in FORMATS,'unsupported captured scalar type')
    shape=meta['ne'];strides=meta['nb'];need(len(shape)==len(strides)==4,'4D descriptor')
    need(all(type(n) is int and n>0 for n in shape),'shape')
    need(all(type(n) is int and n>=0 for n in strides),'strides')
    need(math.prod(shape)<=16*1024*1024,'tensor comparison element ceiling')
    need(type(axis) is int and 0<=axis<4,'axis')
    if row is not None:need(type(row) is int and 0<=row<shape[axis],'row index')
    indices=[range(n) if row is None or i!=axis else [row] for i,n in enumerate(shape)]
    # axis0 varies fastest. Padding bytes are not compared as logical values.
    for rev in itertools.product(*reversed(indices)):
        index=tuple(reversed(rev));offset=sum(i*s for i,s in zip(index,strides))
        yield index,*scalar(payload,kind,offset)

def compare(a,ma,b,mb,left_row=None,right_row=None,axis=1):
    sa=list(ma['ne']);sb=list(mb['ne'])
    if left_row is not None:sa[axis]=1
    if right_row is not None:sb[axis]=1
    if sa!=sb or ma['type']!=mb['type']:
        return {'status':'NOT_COMPARABLE','reason':'shape/type differ; supply an explicit logical row map'}
    n=bad=nonfinite=0;maximum=0.;first=None
    for la,lb in zip(logical_values(a,ma,left_row,axis),logical_values(b,mb,right_row,axis),strict=True):
        n+=1
        if la[1]!=lb[1]:
            bad+=1
            if first is None:first={'left':list(la[0]),'right':list(lb[0])}
        if not math.isfinite(la[2]) or not math.isfinite(lb[2]):
            nonfinite+=1
        else:maximum=max(maximum,abs(la[2]-lb[2]))
    return {'status':'COMPARED','elements':n,'different_elements':bad,'first_different_index':first,
            'max_absolute_finite_difference':maximum,'nonfinite_pairs':nonfinite,
            'bitwise_equal':bad==0,'scope':'Captured outputs only; not a root-cause proof'}

def load_capture(root,item):
    p=confined(root,item['file']);need(p.stat().st_size==item['bytes'],'capture length')
    need(file_hash(p)==item['sha256'],'capture digest');return p.read_bytes()

def first_trace_difference(left,right):
    left=Path(left);right=Path(right)
    def lines(p):
        import json
        return [json.loads(s) for s in (p/'trace/INDEX.jsonl').read_text().splitlines() if s]
    a=lines(left);b=lines(right)
    key=lambda r:(r['phase'],r['call_index'],r['name'],r['occurrence'])
    amap={key(r):r for r in a};bmap={key(r):r for r in b}
    need(len(amap)==len(a) and len(bmap)==len(b),'duplicate trace coordinates')
    result=[]
    for k,la in amap.items():
        if k not in bmap:result.append({'key':k,'status':'MISSING_RIGHT'});continue
        lb=bmap[k]
        if la['caller_first_position']!=lb['caller_first_position'] or la['caller_rows']!=lb['caller_rows']:
            result.append({'key':k,'status':'NOT_COMPARABLE','reason':'caller geometry differs; explicit alignment needed'});continue
        c=compare(load_capture(left,la),la,load_capture(right,lb),lb);c['key']=k
        result.append(c)
    for k in bmap.keys()-amap.keys():result.append({'key':k,'status':'MISSING_LEFT'})
    first=next((r for r in result if r.get('status')=='COMPARED' and not r['bitwise_equal']),None)
    return {'first_observed_mismatch':first,'comparisons':result,
      'scope':'First comparable captured checkpoint, not earliest global divergence or causal localization. Same-prefix/state controls are separately required.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('left',type=Path);p.add_argument('right',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();save(a.out,first_trace_difference(a.left,a.right),exclusive=True)
