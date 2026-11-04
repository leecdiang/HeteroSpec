"""Compare trusted finite full-vector captures; never infer unseen equivalence.
Runtime/device identifiers are provenance claims, not authenticated proofs.
"""
from pathlib import Path
import argparse,json,hashlib,re
ARMS=('frozen_reference','graph_tiles','backend_loop4','packed')
def compare(manifest,root):
    if manifest.get('status')!='executed':raise ValueError('no executed captures')
    provenance=manifest['provenance']
    for key in ('model_sha256','device_uuid','driver','toolkit','reference_binary_sha256'):
        if not isinstance(provenance.get(key),str) or not provenance[key]:raise ValueError('missing provenance '+key)
    for key in ('model_sha256','reference_binary_sha256'):
        if not re.fullmatch('[0-9a-f]{64}',provenance[key]):raise ValueError('invalid hash pin '+key)
    if provenance.get('backend')!='cuda':raise ValueError('CUDA qualification cannot use CPU captures')
    pins=provenance.get('runtime_binary_sha256',{})
    if set(pins)!=set(ARMS) or any(not isinstance(v,str) or not re.fullmatch('[0-9a-f]{64}',v) for v in pins.values()):raise ValueError('missing predeclared arm binary pins')
    if pins['frozen_reference']!=provenance['reference_binary_sha256']:raise ValueError('reference pin conflict')
    if not manifest['cases']:raise ValueError('empty cases')
    result=[];seen=set()
    for case in manifest['cases']:
        identity=case['id']
        if identity in seen:raise ValueError('duplicate case')
        seen.add(identity);q=case['q'];vocab=case['vocab'];steps=case['continuation_steps']
        if type(q)!=int or not 1<=q<=32 or type(vocab)!=int or vocab<=0 or type(steps)!=int or steps<1:raise ValueError('invalid output geometry')
        captures=case['arms']
        if set(captures)!=set(ARMS):raise ValueError('all four comparison arms required')
        loaded={}
        sizes={'logits_f32':q*vocab*4,'continuation_logits_f32':steps*vocab*4,'continuation_tokens_i32':steps*4}
        for arm in ARMS:
            entry=captures[arm]
            if not re.fullmatch('[0-9a-f]{64}',entry.get('runtime_binary_sha256','')):raise ValueError('missing runtime pin')
            if entry['runtime_binary_sha256']!=pins[arm]:raise ValueError('capture uses unexpected arm binary')
            if arm=='frozen_reference' and entry['runtime_binary_sha256']!=provenance['reference_binary_sha256']:raise ValueError('wrong frozen reference binary')
            if type(entry.get('returncode'))!=int or type(entry.get('fallbacks'))!=int or entry['returncode']!=0 or entry['fallbacks']!=0:raise ValueError('failed or fallback capture cannot qualify')
            if arm=='backend_loop4' and q>4 and (type(entry.get('observed_marked_nodes'))!=int or entry['observed_marked_nodes']<1):raise ValueError('backend loop never executed')
            values={}
            for field in ('input_bytes','logits_f32','kv_state_bytes','continuation_logits_f32','continuation_tokens_i32'):
                path=(root/entry[field]).resolve()
                if not path.is_relative_to(root.resolve()):raise ValueError('capture escapes root')
                data=path.read_bytes()
                if not data or (field in sizes and len(data)!=sizes[field]):raise ValueError('missing/truncated '+field)
                values[field]=data
            loaded[arm]=values
        reference=loaded['frozen_reference'];mismatches=[]
        for arm in ARMS[1:]:
            for field,data in loaded[arm].items():
                if data!=reference[field]:mismatches.append({'arm':arm,'field':field})
        result.append({'id':identity,'equal':not mismatches,'mismatches':mismatches,
            'reference_sha256':{field:hashlib.sha256(data).hexdigest() for field,data in reference.items()}})
    return {'status':'FINITE_CAPTURE_EQUAL' if all(x['equal'] for x in result) else 'REJECTED_MISMATCH',
        'claim_scope':'only supplied exact cases; not proof, throughput result or automatic qualification registration','cases':result}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=compare(json.loads(a.manifest.read_text()),a.manifest.parent);a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
