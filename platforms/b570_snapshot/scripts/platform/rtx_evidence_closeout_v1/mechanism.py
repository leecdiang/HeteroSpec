"""CPU-only workload accounting and prospective conditional cost model. No inference."""
from __future__ import annotations
import argparse, collections, math, statistics
from pathlib import Path
import closeout

def features(design):
    width = 4 if design['platform'] == 'RTX' else 2
    return ['target_prefill_ids', 'draft_prefill_ids', 'draft_continuation_rows',
            'reconcile_output_ids', 'rollback_calls', 'request_channel'] + [
                'target_continuation_calls_w' + str(w) for w in range(1, width + 1)]

def valid_units(units, design):
    assert set(units) == set(features(design)), 'missing or unsupported feature basis'
    assert all(type(v) is int and v >= 0 for v in units.values())
    assert units['request_channel'] == 1 and units['target_prefill_ids'] > 0
    return True

def sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)

def workload_metrics(work, output_length):
    names = ['prompt_ids_count', 'output_ids_count', 'proposal_generated', 'proposal_verified',
             'accepted_committed', 'first_mismatch_rejected', 'unexamined_after_mismatch',
             'terminal_discarded', 'unverified_before_verify', 'initial_target_committed',
             'bonus_committed', 'correction_committed', 'fallback_committed', 'verify_cycles',
             'verification_seed_rows', 'draft_continuation_calls', 'draft_continuation_rows',
             'rollback_calls']
    assert all(type(work[n]) is int and work[n] >= 0 for n in names)
    assert sha(work['counter_semantics_sha256'])
    assert work['prompt_ids_count'] > 0 and work['output_ids_count'] == output_length > 0
    p, v, a = (work[n] for n in ('proposal_generated', 'proposal_verified', 'accepted_committed'))
    assert a <= v <= p
    assert p == sum(work[n] for n in ('accepted_committed', 'first_mismatch_rejected',
                    'unexamined_after_mismatch', 'terminal_discarded', 'unverified_before_verify'))
    assert output_length == sum(work[n] for n in ('initial_target_committed', 'accepted_committed',
                    'bonus_committed', 'correction_committed', 'fallback_committed'))
    for name in ('accepted_prefix_hist', 'cycle_progress_hist', 'verification_caller_width_hist'):
        assert isinstance(work[name], dict)
        assert all(str(int(k)) == k and int(k) >= 0 and type(z) is int and z >= 0
                   for k, z in work[name].items())
        assert sum(work[name].values()) == work['verify_cycles']
    assert sum(int(k)*z for k,z in work['accepted_prefix_hist'].items()) == a
    assert sum(int(k)*z for k,z in work['cycle_progress_hist'].items()) == (
        a + work['bonus_committed'] + work['correction_committed'])
    assert sum(int(k)*z for k,z in work['verification_caller_width_hist'].items()) == (
        v + work['verification_seed_rows'])
    assert work['draft_continuation_rows'] >= work['draft_continuation_calls']
    j=work['verify_cycles']
    return {'acceptance_per_generated': a/p if p else None,
            'acceptance_per_verified': a/v if v else None,
            'draft_rows_per_output': work['draft_continuation_rows']/output_length,
            'verified_rows_per_output': (v+work['verification_seed_rows'])/output_length,
            'progress_per_cycle': (a+work['bonus_committed']+work['correction_committed'])/j if j else None,
            'unused_proposal_fraction': (p-a)/p if p else None}

def calibrate(design, export):
    """Coefficients only from the exact six exposed lite tasks, never confirmation."""
    closeout.validate(design)
    cfg=design['mechanism']; names=features(design); rows=export['rows']
    expected={(f,c,t) for f in design['families'] for c in cfg['profile_arms']
              for t in cfg['calibration_task_ids']}
    assert len(rows) == len(expected)
    keys=set(); coefficients={}; sources={}
    for r in rows:
        key=(r['family'],r['condition'],r['task'])
        assert key in expected and key not in keys, 'unregistered or duplicate calibration input'
        keys.add(key)
        assert r['phase']=='exposed_profile' and r['profile_mode']=='lite', 'no formal/heavy fitting'
        assert r['actual_no_added_sync'] is True and r['completed_wall_partition'] is True
        assert r['on_off_raw_equal'] is True
        assert sha(r['source_identity_sha256']) and sha(r['raw_evidence_sha256'])
        valid_units(r['feature_units'],design)
        spans=r['component_ms']; assert set(spans)==set(names)
        assert all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in spans.values())
        assert math.isfinite(r['wall_ms']) and r['wall_ms']>0
        assert abs(sum(spans.values())-r['wall_ms']) <= max(0.05,0.001*r['wall_ms']), 'wall spans do not close'
        assert all(r['feature_units'][n]>0 or spans[n]==0 for n in names), 'cost with zero work'
    assert keys==expected
    for family in design['families']:
        identity={r['source_identity_sha256'] for r in rows if r['family']==family}
        assert len(identity)==1, 'runtime/model identity drift in calibration'
        sources[family]=next(iter(identity)); coefficients[family]={}
        for condition in cfg['profile_arms']:
            rr=[r for r in rows if r['family']==family and r['condition']==condition]
            rates={}
            for n in names:
                units=sum(r['feature_units'][n] for r in rr)
                rates[n]=sum(r['component_ms'][n] for r in rr)/units if units else None
            coefficients[family][condition]=rates
    return {'status':'COEFFICIENTS_REQUIRE_F0B_SEAL','design_sha256':closeout.digest(design),
            'calibration_sha256':closeout.digest(export),'calibration_task_ids':cfg['calibration_task_ids'],
            'source_identity_sha256':sources,'coefficients_ms_per_unit':coefficients,
            'coefficient_scope':'conditional on actual measured work; finite exposed calibration; not online prediction',
            'timing_scope':'lite completed spans calibrated; counts-only wall validated; observer transfer remains in residuals',
            'calibration_profile_mode':'lite','validation_profile_mode':'counts',
            'fit_on_confirmation':False,'native_evidence_verification':'REQUIRES_INDEPENDENT_RAW_AND_SOURCE_VERIFIER'}

def predict(design, model, record):
    if model['status']!='COEFFICIENTS_REQUIRE_F0B_SEAL':
        return {'status':'MODEL_TIMING_UNAVAILABLE','predicted_wall_ms':None}
    if record.get('source_identity_sha256')!=model['source_identity_sha256'].get(record['family']):
        return {'status':'IDENTITY_MISMATCH','predicted_wall_ms':None}
    if record['condition'] not in design['mechanism']['profile_arms']:
        return {'status':'ARM_OUTSIDE_MODEL','predicted_wall_ms':None}
    try:
        units=record['feature_units']; valid_units(units,design)
        metrics=workload_metrics(record['workload'],record['output']['length'])
        assert units['target_prefill_ids']==record['workload']['prompt_ids_count']
        assert units['draft_continuation_rows']==record['workload']['draft_continuation_rows']
        assert units['rollback_calls']==record['workload']['rollback_calls']
        assert units['reconcile_output_ids']==record['output']['length']
        condition=next(c for c in design['conditions'] if c['name']==record['condition'])
        work=record['workload']
        assert work['verification_seed_rows']==work['verify_cycles']
        assert all(0 < int(w) <= condition['maximum_k']+1 for w in work['verification_caller_width_hist'])
        assert all(units['target_continuation_calls_w'+w] >= count
                   for w,count in work['verification_caller_width_hist'].items())
        assert work['draft_continuation_calls']==work['draft_continuation_rows']  # fixed draft UB1
        if condition['spec']:
            assert units['draft_prefill_ids']==work['prompt_ids_count']
        else:
            assert units['draft_prefill_ids']==work['proposal_generated']==work['verify_cycles']==0
    except (AssertionError,KeyError,TypeError,ValueError,StopIteration):
        return {'status':'WORKLOAD_MISSING_OR_INVALID','predicted_wall_ms':None}
    rates=model['coefficients_ms_per_unit'][record['family']][record['condition']]
    unsupported=[n for n,z in units.items() if z and rates[n] is None]
    if unsupported:
        return {'status':'UNSUPPORTED_SHAPE','features':unsupported,'predicted_wall_ms':None}
    parts={n:units[n]*rates[n] if rates[n] is not None else 0.0 for n in units}
    return {'status':'PREDICTED','predicted_wall_ms':sum(parts.values()),
            'predicted_component_ms':parts,'workload_metrics':metrics}

def validate_model(design,model):
    assert model['design_sha256']==closeout.digest(design)
    assert model['fit_on_confirmation'] is False
    assert model['calibration_task_ids']==design['mechanism']['calibration_task_ids']
    if model['status']=='MODEL_TIMING_UNAVAILABLE':
        assert model.get('reason')
        return
    assert model['status']=='COEFFICIENTS_REQUIRE_F0B_SEAL'
    assert model['calibration_profile_mode']=='lite' and model['validation_profile_mode']=='counts'
    assert sha(model['calibration_sha256'])
    assert set(model['coefficients_ms_per_unit'])==set(design['families'])
    assert set(model['source_identity_sha256'])==set(design['families'])
    for f in design['families']:
        assert sha(model['source_identity_sha256'][f])
        cc=model['coefficients_ms_per_unit'][f]
        assert set(cc)==set(design['mechanism']['profile_arms'])
        for rates in cc.values():
            assert set(rates)==set(features(design))
            assert all(z is None or (type(z) in (int,float) and math.isfinite(z) and z>=0)
                       for z in rates.values())

def analyse(design,plan,inputs,records,freeze,model,residency=None):
    # Primary science remains independent of missing supplemental counters/models.
    primary=closeout.analyse(design,plan,inputs,records,freeze,residency)
    validate_model(design,model)
    assert freeze['model_sha256']==closeout.digest(model) and freeze['model_frozen_before_first_formal'] is True
    assert not (set(model['calibration_task_ids']) & {t['id'] for t in inputs['tasks']}), 'calibration leakage'
    cfg=design['mechanism']; arms=cfg['profile_arms']; predicted={}; medians={}; details=[]
    rows=[r for r in records if r['status']=='COMPLETED']
    for r in rows:
        pr=predict(design,model,r); predicted[r['slot']]=pr
        details.append({'slot':r['slot'],'family':r['family'],'condition':r['condition'],
                        'task':r['task'],'session':r['session'],'round':r['round'],
                        'measured_wall_ms':r['wall_ms'],**pr})
    matrix=[]; domains=[]
    for f in design['families']:
        for t in inputs['tasks']:
            for sess in range(2):
                for arm in arms:
                    rr=[r for r in rows if r['family']==f and r['task']==t['id'] and
                        r['session']==sess and r['condition']==arm]
                    pp=[predicted[r['slot']]['predicted_wall_ms'] for r in rr]
                    actual=statistics.median(r['wall_ms'] for r in rr) if len(rr)==5 else None
                    estimate=statistics.median(pp) if len(pp)==5 and all(z is not None for z in pp) else None
                    medians[(f,t['id'],sess,arm)]=(actual,estimate)
                    matrix.append({'family':f,'domain':t['domain'],'task':t['id'],'session':sess,
                                   'condition':arm,'measured_wall_ms':actual,'predicted_wall_ms':estimate})
        for domain in ('MBPP','GSM8K'):
            panel=[p for p in matrix if p['family']==f and p['domain']==domain]
            expected=12*2*len(arms)
            covered=[p for p in panel if p['measured_wall_ms'] is not None and p['predicted_wall_ms'] is not None]
            complete=len(panel)==len(covered)==expected
            qualified=all(primary['families'][f]['qualification'][a]['request_cost_qualified'] for a in arms)
            errors=[p['predicted_wall_ms']-p['measured_wall_ms'] for p in covered]
            mape=statistics.mean(abs(e)/p['measured_wall_ms'] for e,p in zip(errors,covered)) if complete else None
            directions=[]
            tids=[t['id'] for t in inputs['tasks'] if t['domain']==domain]
            for base in (cfg['matched_arm'],'R_prod'):
                cases=[]; correct=0; informative=0; gaps_complete=True
                for tid in tids:
                    for sess in range(2):
                        a,pa=medians[(f,tid,sess,base)]; c,pc=medians[(f,tid,sess,cfg['candidate_arm'])]
                        case={'task':tid,'session':sess,'measured_gap_ms':a-c if a is not None and c is not None else None,
                              'predicted_gap_ms':pa-pc if pa is not None and pc is not None else None}
                        if None in (a,pa,c,pc):
                            case['status']='INCOMPLETE'; gaps_complete=False
                        elif abs(a-c)<=cfg['direction_deadband_fraction']*a:
                            case['status']='NEAR_BREAK_EVEN'
                        else:
                            case['status']='INFORMATIVE'; informative+=1
                            correct+=((a-c)*(pa-pc)>0)
                        cases.append(case)
                accuracy=correct/informative if gaps_complete and informative else None
                status='INCOMPLETE' if not gaps_complete else ('INSUFFICIENT_DIRECTION_CASES'
                       if informative<cfg['minimum_informative_task_sessions'] else
                       ('PASS' if accuracy>=cfg['min_direction_accuracy'] else 'FAIL'))
                directions.append({'comparison':base+'/'+cfg['candidate_arm'],'status':status,
                                   'expected':24,'informative':informative,'correct':correct,
                                   'direction_accuracy':accuracy,'cases':cases})
            domains.append({'family':f,'domain':domain,'expected':expected,'covered':len(covered),
                            'status':'INCOMPLETE' if not complete else ('EVIDENCE_NOT_QUALIFIED' if not qualified else
                            ('PASS' if mape<=cfg['max_validation_mape'] and all(z['status']=='PASS' for z in directions) else 'FAIL_OR_INSUFFICIENT')),
                            'MAE_ms':statistics.mean(abs(e) for e in errors) if complete else None,
                            'MAPE':mape,'signed_residual_ms':statistics.mean(errors) if complete else None,
                            'directions':directions,
                            'qualification_scope':'observed request cost; does not certify physical residency',
                            'observer_transfer':'lite calibration to counts-only confirmation; inspect exposed paired overhead'})
    return {'primary_cost_and_output':primary,'model_validation':domains,'task_session_matrix':matrix,
            'per_request_predictions':details,'model_sha256':closeout.digest(model),
            'unexecuted_or_failed_slots':primary['unexecuted_slots']+[r['slot'] for r in records if r['status']!='COMPLETED'],
            'interpretation':'conditional measured-work model; no refit, causal attribution, cross-date or online decision claim'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--design',required=True)
    sub=p.add_subparsers(dest='action',required=True)
    c=sub.add_parser('calibrate');c.add_argument('--calibration',required=True);c.add_argument('--out',required=True)
    a=sub.add_parser('analyse')
    for arg in ('plan','inputs','records','freeze','model','out'):a.add_argument('--'+arg,required=True)
    a.add_argument('--residency')
    args=p.parse_args();d=closeout.read(args.design)
    if args.action=='calibrate':result=calibrate(d,closeout.read(args.calibration))
    else:result=analyse(d,*(closeout.read(getattr(args,arg)) for arg in ('plan','inputs','records','freeze','model')),
                        closeout.read(args.residency) if args.residency else None)
    import json
    Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'CPU_COMPLETE','output':args.out}))

if __name__=='__main__':main()
