"""Prospective six-feature smooth cost rule; no holdout bytes read during fitting.

Source registered before B0 results. Fit once on complete confirmation; no model
selection/retraining on optional outputs. Prediction is a charged offline phase sum,
not an integrated runtime selector or new decoder implementation.
"""
import argparse,math,time
import numpy as np
from common import V,load,save,sha
from prepare_rtx import root
from collect import utc,git

def features(c):
    q=c['q']-3;k=math.log2(c['keys']/256);g=math.log2(c['Hkv']/8)
    return np.asarray([1,q,k,g,q*k,q*g],dtype=np.float64)
def infer(c,beta,cut):
    if not(c['d']==128 and c['Hq']==32 and c['storage']=='permuted' and c['mask']=='causal' and 2<=c['q']<=4 and 255<=c['keys']<=1025 and 1<=c['Hkv']<=32):return 'QB',None
    y=float(features(c)@beta);return ('QH_C' if y>cut else 'QB'),y

def freeze(analysis):
    r=root();assert not (r/'HOLDOUT_INPUTS.json').exists() and not any(t['optional'] and (r/'attempts'/t['task_id']).exists() for t in load(r/'plan.json')['tasks']),'holdout already opened'
    plan=load(r/'plan.json');a=load(analysis);geom={x['geometry_id']:x for x in a['geometry_summaries'] if x['stage']=='confirm'};training=[]
    for c in plan['cases']:
        if c['realization']!=0 or c['cohort']!='confirmation' or c['q']==1 or c['d']!=128 or c['storage']!='permuted' or c['mask']!='causal':continue
        s=geom[c['geometry_id']]['comparisons'];assert s['QB_QH']['n_blocks']==8 and s['QB_QH_alt']['n_blocks']==8
        target=.5*(math.log(s['QB_QH']['ratio'])+math.log(s['QB_QH_alt']['ratio']));training.append(dict(geometry_id=c['geometry_id'],x=features(c).tolist(),target=target))
    assert len(training)==16
    x=np.array([z['x'] for z in training]);y=np.array([z['target'] for z in training]);ridge=np.eye(6)*.001;ridge[0,0]=0;beta=np.linalg.solve(x.T@x+ridge,x.T@y)
    panel=next(x for x in a['full_panel_summaries'] if x['stage']=='confirm' and x['stratum']=='q>1');noise=max(abs(z) for z in panel['comparisons']['AA']['log_interval']);cut=math.log(1.02)+noise
    predictions={c['case_id']:dict(layout=infer(c,beta,cut)[0],predicted_log_QB_over_QH=infer(c,beta,cut)[1],seed=c['seed'],geometry_id=c['geometry_id']) for c in plan['cases'] if c['cohort']=='holdout'}
    pending=[c for c in plan['cases'] if c['cohort']=='holdout'];start=time.perf_counter_ns()
    for i in range(100000):infer(pending[i%len(pending)],beta,cut)
    lookup=(time.perf_counter_ns()-start)/100000/1000
    save(r/'PREDICTION_FREEZE.json',dict(utc=utc(),commit=git('rev-parse','HEAD'),source_sha256=sha(V/'prediction_rtx.py'),plan_sha256=plan['plan_sha256'],training_analysis_sha256=sha(analysis),features=['1','q-3','log2(keys/256)','log2(Hkv/8)','(q-3)*log2(keys/256)','(q-3)*log2(Hkv/8)'],training=training,ridge=.001,coefficients=beta.tolist(),fallback='QB',QH_choice_log_threshold=cut,fullpanel_AA_log_envelope=noise,predictions=predictions,predictions_before_holdout=True,holdout_bytes_opened=False,lookup_us=lookup,lookup_scope='actual CPU Python infer including features;charged to selected mapping mean;not native integrated selector',metrics=['heldout log-contrast RMSE','direction vs both QB labels','mean/max oracle regret with CPU lookup','fixedPQ/fixedQB/fixedQH;no fasterQB selection','retain wrong predictions and all missing cells'],no_retraining_on_holdout=True))
    print('Frozen holdout predictions',predictions,'lookup_us',lookup,flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--analysis',required=True);args=ap.parse_args();freeze(args.analysis)
