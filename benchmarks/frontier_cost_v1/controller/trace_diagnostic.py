"""Prequential acceptance forecasts on exposed, actually logged k7 actions.

This does not simulate an alternative action, compute latency, or evaluate
counterfactual request trajectories. Repeated sessions are not new requests.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from causal_policy import PastAcceptance

RAW_SHA='53d76c43d4b2fa378855b90f76d9bcb60e509d4086fddd630e3c0f51f6197487'


def diagnose(records_path):
    raw=Path(records_path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=RAW_SHA:raise ValueError('public trace SHA mismatch')
    records=[r for r in json.loads(raw)['records'] if r['kind']=='measurement' and r['session']==0 and r['arm_label']=='LOCAL-loop4-k7']
    if len(records)!=16 or len({r['root'] for r in records})!=16:raise ValueError('fixed logged panel differs')
    history=PastAcceptance();rows=[];errors=[];simple_errors=[];success4=failure4=censored=observed_trials=0
    for request_number,record in enumerate(records):
        if record['receipt']['k']!=7:raise ValueError('logged arm differs')
        for cycle_number,cycle in enumerate(record['receipt']['cycles']):
            # The predictor sees no record/cycle/target-output object.
            probability=math.prod(history.probabilities(7)[:4])
            simple_probability=(1+success4)/(2+success4+failure4)
            event=f'{request_number}:{cycle_number}';history.announce(event,0,8,7)
            accepted=cycle['accepted'];rejected=cycle['rejected']
            matches=tuple(a==b for a,b in zip(cycle['proposals'],cycle['decisions'][:7]))
            if not (len(matches)==7 and 0<=accepted<=7 and all(matches[:accepted])):raise ValueError('logged match prefix differs')
            if rejected and (accepted==7 or matches[accepted]):raise ValueError('logged first rejection differs')
            terminal_after=accepted if cycle['commit_kind']=='accepted' else None
            learned=history.observe(event,matches,terminal_after=terminal_after)
            observed_trials+=len(learned)
            label=True if accepted>=4 else (False if rejected else None)
            if label is None:censored+=1
            else:
                errors.append((probability-int(label))**2);simple_errors.append((simple_probability-int(label))**2)
                if label:success4+=1
                else:failure4+=1
            rows.append({'request_ordinal':request_number,'cycle_ordinal':cycle_number,
                         'predecision_first4_match_probability':probability,'past_only_direct_first4_probability':simple_probability,
                         'observed_first4_match':label,'learned_prefix_trials':len(learned)})
    summary={'schema':'heterospec.causal-forecast-diagnostic.v1','status':'EXPOSED_LOGGED_ACTION_DIAGNOSTIC_ONLY',
             'source_sha256':RAW_SHA,'selection':'Original file order, measured LOCAL-loop4-k7, session0; 16 unique roots.',
             'requests':len(records),'logged_cycles':len(rows),'observed_prefix_trials':observed_trials,
             'first4_labels':{'true':success4,'false':failure4,'censored_terminal_before4':censored},
             'conditional_position_beta_Brier':sum(errors)/len(errors),
             'past_only_direct_first4_beta_Brier':sum(simple_errors)/len(simple_errors),
             'forecast_target':'First four candidate decisions match; this is not the probability of continuing after CAP/EOG.',
             'history_policy':'Predict before current outcome; update true prefix plus first mismatch only; terminal suffix censored.',
             'held_out':False,'counterfactual_actions_executed':0,'costs_imported':0,'new_model_requests':0,'GPU_requests':0,
             'latency_or_speedup_claim':False}
    return summary,rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--records',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():raise ValueError('fresh output required')
    summary,rows=diagnose(a.records);a.output.mkdir(parents=True)
    (a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    (a.output/'FORECASTS.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
