"""Prospective role-specific receipt review; no monitoring process or device API."""
import argparse, collections, copy, datetime, pathlib
from common import ROOT, load, save, sha, modules

def review(memory, role, contract):
    samples=memory['samples'];times=[datetime.datetime.fromisoformat(x['timestamp_utc']) for x in samples]
    gaps=[(b-a).total_seconds()*1000 for a,b in zip(times,times[1:])]
    periodic=[x for x in samples if x['point']=='SAFETY_PERIODIC']
    observed='periodic' if periodic else 'checkpoints'
    errors=[]
    if not gaps or min(gaps)<0:errors.append('missing/nonmonotonic actual timestamps')
    if contract['role_mode'][role]!=observed:errors.append('runtime role sampling mode contradicts declared contract')
    if observed=='periodic':
        if contract.get('nominal_period_ms') is None:errors.append('periodic contract has no nominal period')
        if contract.get('max_gap_ms') is None or contract.get('loss_timeout_ms') is None:errors.append('periodic jitter/loss limits not frozen')
        if gaps and contract.get('max_gap_ms') is not None and max(gaps)>contract['max_gap_ms']:errors.append('observed interval exceeds prospective maximum gap')
    elif contract.get('require_periodic_for_all'):errors.append('checkpoint runtime cannot satisfy universal periodic coverage')
    return dict(role=role,observed_mode=observed,declared_mode=contract['role_mode'][role],
                receipt_requested_period_ms=memory['requested_period_ms'],
                requested_field_not_used_as_observed_cadence=True,
                samples=len(samples),periodic_samples=len(periodic),points=dict(collections.Counter(x['point'] for x in samples)),
                observed_gaps_ms=gaps,observed_max_gap_ms=max(gaps) if gaps else None,
                errors=errors,eligible=not errors)

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True);a=p.parse_args();before=modules()
    source=a.old;plan=load(source/'p0/PLAN_P1.json');rows=[];first=None
    # Example limits are prospective, explicitly not a repair of the old F0.
    future=dict(role_mode={'old':'checkpoints','new':'periodic'},nominal_period_ms=100,max_gap_ms=250,loss_timeout_ms=1000,require_periodic_for_all=False)
    old_claim=dict(future,role_mode={'old':'periodic','new':'periodic'},require_periodic_for_all=True)
    for s in plan['slots']:
        d=source/'_host/run'/s['slot'];path=d/(s['slot']+('.trace.json' if s['mode']=='diagnostic' else '.memory.json'))
        if not path.exists():continue
        x=load(path);m=x['memory'] if s['mode']=='diagnostic' else x
        role=load(d/'LAUNCH.json')['runtime_role'];r=review(m,role,future)
        row=dict(slot=s['slot'],arm=s['arm'],mode=s['mode'],raw_path=path.relative_to(source).as_posix(),raw_sha256=sha(path),review=r)
        rows.append(row)
        if s['arm']=='R' and first is None:first=(m,s,role)
    m,s,role=first
    negatives=[]
    for requested in (None,5,100):
        fake=copy.deepcopy(m);fake['requested_period_ms']=requested;r=review(fake,role,old_claim)
        assert not r['eligible'];negatives.append(dict(requested_field=requested,actual_samples_unchanged=True,review=r))
    assert all(not review(load(source/'_host/run'/x['slot']/(x['slot']+'.memory.json')),'old',old_claim)['eligible'] for x in plan['slots'] if x['arm']=='R')
    save(ROOT/'MONITOR_TESTS.json',dict(scope='Prospective role semantics only; example limits are not approved execution F0 and do not retroqualify historical requests.',
         example_prospective_contract=future,old_universal_claim=old_claim,receipts=rows,negatives=negatives,
         first_R_slot=s['slot'],candidate_stage_allowed_after_first_R_under_old_claim=False,
         source_anchors=[dict(path='native/worker.cpp',line=105,sha256=sha(source/'native/worker.cpp'),property='new unconditional periodic thread100ms; stop requested field reports null(counts) or5(heavy), not actual cadence'),
                         dict(path='_host/pr97/baseline/pr92_restore/native/worker.cpp',sha256=sha(source/'_host/pr97/baseline/pr92_restore/native/worker.cpp'),property='original start uses heavy guard; registered counts is checkpoints')],
         modules_before=before,modules_after=modules(),gpu_starts=0))
    print(dict(receipts=len(rows),requested_field_negatives=len(negatives),first_R_blocks_candidates=True,
               periodic=sum(x['review']['observed_mode']=='periodic' for x in rows),checkpoint=sum(x['review']['observed_mode']=='checkpoints' for x in rows)))

if __name__=='__main__':main()
