"""Versioned dense F16 sequence reader; a format reader, not a numeric oracle.
No trained-model profile is preapproved. The host must pin the actual serializer,
model layer order, stream convention and round-trip sentinels before using one.
"""
from __future__ import annotations
import struct
from .common import need,digest,hexsha

def parse(raw:bytes,positions:list[int],profile:dict)->tuple[bytes,dict]:
    need(profile['format']=='dense_seq_f16_v1','unknown writer profile')
    for k in ('writer_sha256','target_model_sha256','layer_map_source_sha256'):hexsha(profile[k],k)
    need(profile.get('host_writer_reviewed') is True,'profile has not been checked against actual writer')
    need(positions and positions==list(range(len(positions))),'only dense seq0 prefixes supported')
    need(len(positions)<=profile['capacity'],'prefix exceeds admitted capacity')
    layers=profile['layers'];need(isinstance(layers,list) and layers,'no active layers')
    need(len({x['id'] for x in layers})==len(layers),'duplicate layer identity')
    for l in layers:
        for k in ('k_elements','v_elements'):need(type(l[k]) is int and l[k]>0,'layer shape')
    i=0;n=len(positions)
    def rd(fmt):
        nonlocal i
        size=struct.calcsize('<'+fmt);need(i+size<=len(raw),'truncated header')
        v=struct.unpack_from('<'+fmt,raw,i);i+=size;return v[0] if len(v)==1 else v
    def take(nbytes):
        nonlocal i
        need(type(nbytes) is int and 0<=nbytes<=len(raw)-i,'truncated active tensor')
        b=raw[i:i+nbytes];i+=nbytes;return b
    need(rd('I')==0xaf143cd8,'state magic/endianness')
    need(rd('i')==0 and rd('I')==1 and rd('I')==n,'sequence/stream/active count')
    for pos in positions:need(rd('i')==pos and rd('I')==1 and rd('i')==0,'position/sequence mapping')
    trans=rd('I');need(trans in (0,1),'V layout');need(rd('I')==len(layers),'layer count')
    ks=[];vs=[]
    for l in layers:
        need(rd('i')==1,'K not F16');size=2*l['k_elements'];need(rd('Q')==size,'K row size');ks.append(take(n*size))
    for l in layers:
        need(rd('i')==1,'V not F16');size=2*l['v_elements']
        if not trans:need(rd('Q')==size,'V row size');vs.append(take(n*size))
        else:
            need(rd('I')==2 and rd('I')==l['v_elements'],'V element layout')
            b=take(n*size)
            try:
                import numpy as np
                out=np.frombuffer(b,dtype='<u2').reshape(l['v_elements'],n).T.copy().tobytes()
            except ImportError:
                out=bytearray(n*size)
                for t in range(n):
                    for c in range(l['v_elements']):out[t*size+2*c:t*size+2*c+2]=b[(c*n+t)*2:(c*n+t)*2+2]
            vs.append(bytes(out))
    need(i==len(raw),'trailing bytes; register different actual format rather than ignoring them')
    out=bytearray()
    for t in range(n):
        for j,l in enumerate(layers):
            a=2*l['k_elements'];b=2*l['v_elements'];out+=ks[j][t*a:(t+1)*a];out+=vs[j][t*b:(t+1)*b]
    return bytes(out),{'active_layout_sha256':digest({'layers':layers,'order':'token/layer/K,V/raw-f16-le'}),
        'bytes_per_token':sum(2*(l['k_elements']+l['v_elements']) for l in layers),
        'profile_sha256':digest(profile),'positions':positions,'raw_v_transposed':bool(trans),
        'tokens_not_encoded_in_state':True,'excludes':'inactive padding; allocator/graph state; independent frontier logits; draft state',
        'scope':'syntactic extraction only; independent expected payload comparison still required'}
