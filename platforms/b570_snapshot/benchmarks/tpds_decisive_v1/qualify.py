"""Finite raw-byte comparison. Not hardware attestation or an equivalence proof.
A host adapter supplies native captures; this code does not fabricate/relabel them.
"""
from __future__ import annotations
import argparse,struct
from pathlib import Path
from common import need,read,digest,hexsha,check_blob,equal_files,write_new
from trace import reconstruct

BOUND=('reference_identity_sha256','target_model_sha256','producer_sha256','lifecycle_sha256','input_sha256','cap','vocab','active_kv_bytes_per_token')

def checked_vector(root:Path,spec:dict,n:int)->tuple[Path,int]:
    p=check_blob(root,spec,expected=4*n);best=None;maximum=None;idx=0
    import math
    with p.open('rb') as f:
        while chunk:=f.read(65536):
            need(len(chunk)%4==0,'unaligned f32 payload')
            for (x,) in struct.iter_unpack('<f',chunk):
                need(math.isfinite(x),'nonfinite target logit')
                if maximum is None or x>maximum:maximum=x;best=idx
                idx+=1
    need(idx==n and best is not None,'vocabulary mismatch');return p,best

def qualify(candidate_path:Path,free_path:Path,forced_path:Path)->dict:
    c,f,r=map(read,(candidate_path,free_path,forced_path));roots=[p.parent for p in (candidate_path,free_path,forced_path)]
    need(c['role']=='candidate' and f['role']=='free_reference' and r['role']=='forced_reference','role mismatch')
    need(len({z['invocation_id'] for z in (c,f,r)})==3,'candidate/reference process identity reused')
    need(f.get('received_forced_tape') is False,'free reference contaminated by candidate tape')
    need(f.get('autonomous') is True,'free reference is not autonomous')
    for z in (c,f,r):
        need(z.get('execution')=='NATIVE' and z.get('completed') is True,'incomplete/non-native capture')
        need(z.get('reference_bridge_passed') is True,'historical reference bridge not passed')
        need(z.get('fallback_count')==0,'unreported numerical fallback')
        for k in BOUND:
            need(z['binding'][k]==f['binding'][k],'comparison binding drift: '+k)
        for k in ('reference_identity_sha256','target_model_sha256','producer_sha256','lifecycle_sha256','input_sha256'):
            hexsha(z['binding'][k],k)
    n=f['binding']['vocab'];bp=f['binding']['active_kv_bytes_per_token']
    need(type(n) is int and n>1 and type(bp) is int and bp>0,'native geometry missing')
    derived=reconstruct(c['trace']);gold=reconstruct(f['trace'])
    need(c['trace']['prompt_ids']==f['trace']['prompt_ids'],'prompt drift')
    need(c['trace']['cap']==f['binding']['cap']==f['trace']['cap'],'trace cap drift')
    need(c['trace']['vocab']==n==f['trace']['vocab'],'trace vocab drift')
    need(c['trace']['eog_ids']==f['trace']['eog_ids'],'EOG predicate drift')
    need(digest(c['trace']['prompt_ids'])==c['binding']['input_sha256'],'input token binding')
    need(derived['tokens']==gold['tokens'] and derived['stop_reason']==gold['stop_reason'],'autonomous endpoint mismatch')
    def index(rows):
        out={}
        for x in rows:
            key=digest(x['prefix']);need(key not in out,'duplicate reference prefix');out[key]=x
        return out
    bank=index(r['prefixes']);freevec=index(f['vectors']);cv=c['vectors']
    need(len(cv)==len(derived['vector_uses']),'missing/extra actual target vectors')
    compared=0
    for a,use in zip(cv,derived['vector_uses']):
        need(a['prefix']==use['prefix'] and a['key']==use['key'],'actual vector provenance mismatch')
        key=digest(use['prefix']);need(key in bank,'missing forced path')
        ap,decision=checked_vector(roots[0],a['blob'],n)
        rp,_=checked_vector(roots[2],bank[key]['frontier'],n)
        need(decision==use['decision'],'journal argmax differs from native vector')
        need(equal_files(ap,rp),'target vector differs from independent forced reference');compared+=1
    # Independently validate the free trajectory's actual native values as well.
    for use in gold['vector_uses']:
        key=digest(use['prefix']);need(key in freevec and key in bank,'free trajectory vector missing')
        fp,d=checked_vector(roots[1],freevec[key]['blob'],n)
        rp,_=checked_vector(roots[2],bank[key]['frontier'],n)
        need(d==use['decision'] and equal_files(fp,rp),'autonomous reference vector mismatch')
    states=c['states'];need(len(states)==len(derived['states']),'missing commit-state snapshots')
    for s,want in zip(states,derived['states']):
        for k in ('prefix','unmaterialized_suffix','next_pending','terminal','branch','output_count'):
            need(s[k]==want[k],'state frontier error: '+k)
        key=want['prefix_sha256'];need(key in bank,'missing state reference prefix')
        expected=bp*len(want['prefix'])
        ap=check_blob(roots[0],s['active_kv'],expected=expected)
        rp=check_blob(roots[2],bank[key]['active_kv'],expected=expected)
        need(s['active_layout_sha256']==bank[key]['active_layout_sha256'],'active KV layout/layer identity differs')
        hexsha(s['active_layout_sha256'])
        need(equal_files(ap,rp),'committed active target KV differs')
        fp,_=checked_vector(roots[0],s['frontier'],n);rf,_=checked_vector(roots[2],bank[key]['frontier'],n)
        need(equal_files(fp,rf),'retained-prefix frontier differs (last-logit API may be stale)')
    return {'status':'FINITE_NATIVE_CAPTURE_MATCH','contract':'T','vector_uses':compared,
            'states':len(states),'candidate':digest(c),'free_reference':digest(f),'forced_reference':digest(r),
            'hidden_padding_proof':False,'runtime_authentication':False,'universal_guarantee':False,
            'gpu_performance_claim':False,'note':'Native origin is host-supplied; inspect source/bridge receipts. This checker verifies bytes and transcript consistency.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('free',type=Path);p.add_argument('forced',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    write_new(a.out,qualify(a.candidate,a.free,a.forced))
if __name__=='__main__':main()
