"""Independently reconstruct replay correspondence and reduction-length effects."""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
from prepare_attention_replay import packed


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--unit',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();unit=a.unit
    receipt=json.loads((unit/'RECEIPT.json').read_text());assert receipt['success'] and receipt['active_processes_after_wait']==0
    manifest=json.loads((unit/'MANIFEST.json').read_text());native=json.loads((unit/'native/RESULT.json').read_text())
    cases={c['name']:c for c in manifest['cases']};rows=[];by={}
    for r in native['results']:
        c=cases[r['case']];path=unit/'native'/r['file'];values=array.array('f',path.read_bytes())
        assert path.stat().st_size==r['bytes']==4*math.prod(r['ne']) and all(math.isfinite(x) for x in values)
        for inp in c['inputs']:assert sha(inp['file'])==inp['sha256']
        if c.get('expected_file'):assert sha(c['expected_file'])==c['expected_sha256']
        h=sha(path);row=dict(r,sha256=h,kind=c['kind'],expected_equal=h==c['expected_sha256'] if c.get('expected_sha256') else None)
        rows.append(row);key=(r['case'],r['repetition']);assert key not in by;by[key]=row
    assert set(by)=={(name,rep) for name in cases for rep in (0,1)}
    repeat=all(by[name,0]['sha256']==by[name,1]['sha256'] for name in cases)
    own=all(r['expected_equal'] for r in rows if r['kind']=='own_path')
    def bits(desc,shape=None):return packed(Path(desc['file']).read_bytes(),desc,shape)
    scalar=cases['scalar_kqv_0'];batch=cases['batch_kqv_0']
    extent=scalar['inputs'][1]['ne'][0]
    checkpoint=json.loads((Path(manifest['source_checkpoint'])/'CHECKPOINT.json').read_text())
    visible=checkpoint['base']+1
    qks=cases['scalar_kq_0'];qkb=cases['batch_kq_0']
    probs_equal=bits(scalar['inputs'][1])==bits(batch['inputs'][1],[extent,1,32,1])
    kshape=qks['inputs'][0]['ne'].copy();kshape[1]=visible
    vshape=scalar['inputs'][0]['ne'].copy();vshape[0]=visible
    invariant={
        'query_bits_equal':bits(qks['inputs'][1])==bits(qkb['inputs'][1]),
        'visible_K_bits_equal':bits(qks['inputs'][0],kshape)==bits(qkb['inputs'][0],kshape),
        'visible_V_bits_equal':bits(scalar['inputs'][0],vshape)==bits(batch['inputs'][0],vshape),
        'visible_raw_QK_bits_equal':bits(cases['scalar_kq_soft_max_0']['inputs'][0],[visible,1,32,1])==bits(cases['batch_kq_soft_max_0']['inputs'][0],[visible,1,32,1]),
        'probability_prefix_bits_equal':probs_equal}
    for side,case in [('scalar',scalar),('batch',batch)]:
        desc=case['inputs'][1];vals=array.array('f',bits(desc));length=desc['ne'][0]
        invariant[side+'_masked_tail_exact_zero']=all(x==0.0 for h in range(32) for x in vals[h*length+visible:(h+1)*length])
    equal=lambda left,right:by[left,0]['sha256']==by[right,0]['sha256']
    interventions={
        'crop_softmax_matches_scalar':by['batch_softmax_crop768',0]['expected_equal'],
        'pad_softmax_matches_batch':by['scalar_softmax_pad1024',0]['expected_equal'],
        'crop_V_with_scalar_prob_matches_scalar':by['batch_V_crop_scalar_prob',0]['expected_equal'],
        'pad_scalar_prob_on_full_V_matches_batch':equal('batch_V_scalar_prob_pad1024','batch_kqv_0'),
        'crop_batch_prob_on_scalar_V_matches_scalar':equal('scalar_V_batch_prob_crop768','scalar_kqv_0'),
        'different_extent_outputs_differ':not equal('scalar_kqv_0','batch_kqv_0')}
    passed=own and repeat and all(invariant.values()) and all(interventions.values())
    result={'status':'NATIVE_EXTENT_MECHANISM_RECONSTRUCTED' if passed else 'REPLAY_REVIEW_INCOMPLETE',
            'own_path_all_equal':own,'all_repetitions_equal':repeat,'invariants':invariant,'interventions':interventions,'rows':rows,
            'source_hashes':{str(unit/name):sha(unit/name) for name in ('MANIFEST.json','BUILD.json','RECEIPT.json','native/RESULT.json')},
            'scope':'Captured first C_PQ row at cycle 8. Same valid inputs/probabilities, CUDA V-by-probability reduction length changes output bits. No universal kernel or model claim.'}
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print(result['status'])


if __name__=='__main__':main()
