"""Strided F32/F16 output comparison with explicitly source-reviewed token axes.
A difference is an observed frontier, not automatically the first causal operator.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, struct
from pathlib import Path
from common import *


def logical_column(root,node,axis,column):
    integer(axis,0,3,'token axis');ne=node['ne'];nb=node['nb']
    need(len(ne)==len(nb)==4,'four-dimensional descriptor')
    for n in ne:integer(n,1,10000000,'extent')
    for s in nb:integer(s,0,2**63-1,'stride')
    integer(column,0,ne[axis]-1,'logical token column')
    dtype=node['type'];need(dtype in ('f32','f16'),'unsupported dtype requires explicit decoder')
    size,fmt=(4,'<f') if dtype=='f32' else (2,'<e')
    need(math.prod(ne)<=50_000_000,'oversized logical tensor')
    p=safe(root,node['file']);need(p.stat().st_size==node['bytes'] and sha(p)==node['sha256'],'trace artifact differs')
    raw=p.read_bytes();out=bytearray();values=[]
    axes=[i for i in range(4) if i!=axis]
    for index in itertools.product(*(range(ne[i]) for i in reversed(axes))):
        pos=column*nb[axis]+sum(j*nb[a] for a,j in zip(reversed(axes),index))
        need(pos+size<=len(raw),'strided view exceeds captured allocation')
        scalar=raw[pos:pos+size];v=struct.unpack(fmt,scalar)[0];need(math.isfinite(v),'nonfinite captured output')
        out.extend(scalar);values.append(v)
    return bytes(out),values,[ne[i] for i in axes]


def row_prefix(node,column,chunk_offset):
    """chunk_offset must be bound to a reviewed native microbatch mapping."""
    integer(chunk_offset,0,1023,'microbatch offset')
    ids=node['caller_prefix_ids'];call=node['call_ids']
    need(hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()==node['caller_prefix_sha256'],'caller prefix hash')
    integer(column+chunk_offset,0,len(call)-1,'row in caller')
    return ids+call[:chunk_offset+column+1]


def compare(root,alignment):
    need(alignment.get('mapping_review_sha256') and len(alignment['mapping_review_sha256'])==64,'source-reviewed alignment receipt missing')
    need(alignment.get('mode')=='observed_output_frontier','not a causal certification')
    out=[]
    for pair in alignment['pairs']:
        ends=[]
        for key in ('left','right'):
            x=pair[key];manifest=read(safe(root,x['manifest']));node=manifest['snapshots'][x['index']]
            data,v,shape=logical_column(safe(root,x['manifest']).parent,node,x['token_axis'],x['column'])
            prefix=row_prefix(node,x['column'],x['microbatch_offset'])
            ends.append((data,v,shape,prefix,node))
        a,b=ends
        need(a[3]==b[3],'different logical natural/teacher prefixes cannot localize a numeric frontier')
        need(a[2]==b[2] and a[4]['type']==b[4]['type'],'logical output geometry/type mismatch')
        need(a[4].get('layer')==b[4].get('layer'),'different layer')
        need(pair.get('semantic_stage'),'stage alignment must be explicit')
        out.append({'semantic_stage':pair['semantic_stage'],'layer':a[4].get('layer'),
            'prefix_tokens':len(a[3]),'byte_equal':a[0]==b[0],
            'different_scalars':sum(x!=y for x,y in zip(a[1],b[1])),
            'max_abs':max((abs(x-y) for x,y in zip(a[1],b[1])),default=0),
            'left_sha256':hashlib.sha256(a[0]).hexdigest(),'right_sha256':hashlib.sha256(b[0]).hexdigest(),
            'left_backend':a[4].get('compute_backend'),'right_backend':b[4].get('compute_backend')})
    return {'status':'OBSERVED_COMPARISON_COMPLETE','comparisons':out,'matched_rows':len(out),
        'earliest_causal_operator':'NOT_ESTABLISHED_BY_SPARSE_OUTPUT_CAPTURE',
        'same_operand_replay':'NOT_CLAIMED; upstream states can differ despite identical token prefixes',
        'native_requests_added':0}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--alignment',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();save(a.out,compare(a.root,read(a.alignment)),True)
