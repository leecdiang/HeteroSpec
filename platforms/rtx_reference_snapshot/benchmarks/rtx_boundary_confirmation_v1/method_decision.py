"""Prospective A/A-only method choice; no candidate mapping timing is consulted."""
import math,statistics
from common import load,save,sha,V
from prepare_rtx import root

def decide(analysis):
    r=root();rule=load(r/'METHOD_SELECTION_RULE.json');a=load(analysis);by={}
    for method in ['H0','H1']:
        rows=[x for x in a['case_summaries'] if x['stage']=='aa_pilot' and x['method']==method]
        assert len(rows)==8 and all(x['comparisons']['AA']['n_blocks']==6 for x in rows),'pilot incomplete'
        endpoints=[max(abs(z) for z in x['comparisons']['AA']['log_interval']) for x in rows]
        by[method]=dict(anchor_log_envelopes=endpoints,median_absolute_log_envelope=statistics.median(endpoints),maximum_absolute_log_envelope=max(endpoints),approximate_median_ratio_scale=math.exp(statistics.median(endpoints))-1)
    q=load(r/'QUALIFICATION.json');assert all(q.values()),'method qualification gap'
    passed=by['H1']['median_absolute_log_envelope']<=max(math.log(1.10),1.5*by['H0']['median_absolute_log_envelope'])
    save(r/'METHOD_DECISION.json',dict(selected_method='H1' if passed else 'HOLD',selection_script_sha256=sha(V/'method_decision.py'),rule_registration=load(r/'METHOD_RULE_REGISTRATION.json'),samples=30,warmups=8,selection_rule=rule,method_evidence=by,pilot_plan_sha256=load(r/'plan.json')['plan_sha256'],policy_sha256=load(r/'FREEZE.json')['policy_sha256'],host_sha256=load(r/'FREEZE.json')['native_sha256'],reason='buffered H1 qualified; bounded A/A variation supports method use' if passed else 'H1 exceeds prospective noise/feasibility guard; no confirmation started',not_a_resolution_certificate='A/A interval envelope reported per anchor;no 2% certification or kernel timing claim',candidate_results_consulted=False))
    print('METHOD', 'H1' if passed else 'HOLD', by,flush=True)
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('analysis');args=ap.parse_args();decide(args.analysis)
