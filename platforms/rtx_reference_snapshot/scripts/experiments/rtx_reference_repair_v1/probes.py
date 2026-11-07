"""Generate aligned-prefix diagnostic plans and check trace/no-trace controls."""
from __future__ import annotations
import argparse, copy
from pathlib import Path
from common import *
from plan import trace_slot

def first_difference(a,b):
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y:return i
    return None if len(a)==len(b) else min(len(a),len(b))

def make_probes(bundle,input_id,index,out,pattern=None):
    panel=read(bundle/'DEV.json');refs=read(bundle/'DEV_REFERENCES.json')
    chosen=[i for i,x in enumerate(panel['inputs']) if x['id']==input_id];need(len(chosen)==1,'unknown development input')
    i=chosen[0];tokens=refs[input_id]['ids'];need(0<=index<len(tokens),'prediction index')
    slots=[]
    for arm,producer in [('R','native'),('M_PQ','native'),('M_QB','native'),('M_QB','reference')]:
        s=trace_slot(panel,i,arm,producer,tokens,index)
        if index==0:s['repair']['trace']['phases']=['PREFILL'];s['repair']['trace']['min_call_position']=0
        if pattern:s['repair']['trace']['name_regex']=pattern
        a=copy.deepcopy(s);a['slot_id']+='/control';a['repair']['trace']['mode']='off';slots.append(a)
        s['slot_id']+='/trace';slots.append(s)
    save(out,slots,exclusive=True);return slots

def audit_probe_pairs(native_root,slots):
    root=Path(native_root);pairs=[]
    need(len(slots)%2==0,'probe pairs')
    for a,b in zip(slots[::2],slots[1::2]):
        need(a['repair']['teacher_tokens']==b['repair']['teacher_tokens'],'probe prefix changed')
        ra=read(confined(root,a['slot_id']+'.json'));rb=read(confined(root,b['slot_id']+'.json'))
        fa=confined(root,a['slot_id']);fb=confined(root,b['slot_id'])
        hashes=lambda p:{f.relative_to(p).as_posix():file_hash(f) for f in sorted((p/'target').glob('*.f32'))}
        state=lambda p:file_hash(p/'target_final.state')
        same=ra['endpoint']==rb['endpoint'] and hashes(fa)==hashes(fb) and state(fa)==state(fb)
        pairs.append({'control':a['slot_id'],'trace':b['slot_id'],'same_prefix':True,
          'endpoint_vectors_state_equal':same,'eligible_for_localization':same})
    return {'status':'OBSERVER_CONTROLS_PASS' if all(p['eligible_for_localization'] for p in pairs) else 'OBSERVER_CONTAMINATION',
            'pairs':pairs,'scope':'Same-prefix trace/no-trace control; not cross-arm state equivalence or earliest-cause proof.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='cmd',required=True)
    a=sp.add_parser('make');a.add_argument('--bundle',type=Path,required=True);a.add_argument('--input',required=True);a.add_argument('--index',type=int,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--pattern')
    a=sp.add_parser('audit');a.add_argument('--root',type=Path,required=True);a.add_argument('--slots',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='make':print(len(make_probes(a.bundle,a.input,a.index,a.out,a.pattern)))
    else:save(a.out,audit_probe_pairs(a.root,read(a.slots)),exclusive=True)
