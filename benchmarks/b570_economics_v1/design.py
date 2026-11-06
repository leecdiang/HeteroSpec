"""Outcome-free schedules and explicit early research decisions. No GPU calls."""
from pathlib import Path
import argparse, hashlib, json, math
ARMS=('S_M','L_M','S_D1','L_D1','S_D4','L_D4')
PAIR_ORDER=(0,1,5,2,4,3)  # even-n Williams balanced carryover order

def schedule(roots, lane='joint'):
    if not roots or len(set(roots))!=len(roots):raise ValueError('Distinct roots required')
    arms=ARMS if lane=='joint' else ('S_M','L_M') if lane=='target' else None
    if arms is None:raise ValueError('Unknown confirmation lane')
    n=len(arms);order=PAIR_ORDER if n==6 else (0,1);slots=[]
    for session in range(n):
        # Rotate roots to avoid an invariant earliest/late root position.
        rs=roots[session%len(roots):]+roots[:session%len(roots)]
        for ri,root in enumerate(rs):
            for period,k in enumerate(order):
                arm=arms[(k+session)%n]
                for kind in ('warmup','measure'):
                    identity=f'{lane}/{session}/{root}/{arm}/{kind}'
                    slots.append(dict(slot=hashlib.sha256(identity.encode()).hexdigest()[:24],
                        root_id=root,session=session,period=period,arm=arm,kind=kind))
    return {'lane':lane,'arms':list(arms),'sessions':n,'roots':roots,'slots':slots,
            'all_controls_retained':True,'GPU_execution':'NOT_RUN'}

def choose_roots(pool, excluded, count, salt):
    # Tokenization/eligibility must precede this function. Never pass a speed filter.
    roots=sorted(set(pool)-set(excluded),key=lambda r:hashlib.sha256((salt+'\0'+r).encode()).hexdigest())
    if count<1 or len(roots)<count:raise ValueError('Insufficient unseen eligible roots; do not pad')
    return roots[:count]

def gate(quality,clean_ratios,diagnostic,total_ratio=None,meaningful_target_capability=False):
    """Development-only continuation decision, not significance or paper acceptance.
    clean_ratios are BEST_M / D for all fixed exposed roots, never cherry-picked.
    """
    if quality is not True:return {'action':'REPAIR_OR_SCOPE_CLOSE','reason':'reference compatibility is unresolved'}
    if not clean_ratios:return {'action':'NEED_BOUNDED_CLEAN_PILOT','reason':'no service evidence'}
    if any(not math.isfinite(x) or x<=0 for x in clean_ratios):raise ValueError('Bad ratios')
    if total_ratio is None or not math.isfinite(total_ratio) or total_ratio<=0:
        raise ValueError('Complete-service pilot total ratio is required')
    gm=math.exp(sum(map(math.log,clean_ratios))/len(clean_ratios))
    if total_ratio>1 and gm>1 and sum(x>1 for x in clean_ratios)>len(clean_ratios)/2:
        return {'action':'FREEZE_JOINT_CONFIRMATION','development_gm':gm,
                'reason':'provisional complete-service opportunity; this is not a confirmed gain'}
    if meaningful_target_capability:
        return {'action':'FREEZE_TARGET_ONLY_CONFIRMATION','development_gm':gm,
                'reason':'target method remains useful; do not present drafting as successful'}
    return {'action':'CLOSE_SPECULATION_AND_REPORT','development_gm':gm,
            'reason':'no complete-service opportunity; identify paid bottleneck before any new mechanism',
            'diagnostic':diagnostic}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--roots',type=Path,required=True);p.add_argument('--lane',choices=('joint','target'),default='joint')
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=schedule(json.loads(a.roots.read_text()),a.lane)
    with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
