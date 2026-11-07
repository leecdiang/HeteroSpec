"""Small calibration-only selector. No native execution; no held-out fitting.
The host must bind the produced JSON to its source/deployment execution freeze.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import argparse
import json
import math
from pathlib import Path
import statistics
from typing import Any
import study

TIE_ORDER=('WB-rechunk','WB-cut','QB')

def fit(calibration: dict[str, Any], panel: dict[str, Any]) -> dict[str, Any]:
    study.check_panel(panel)
    study.require(calibration.get('stage')=='calibration','calibration stage required')
    study.require(calibration.get('panel_sha256')==study.digest(panel),'panel hash mismatch')
    study.require(calibration.get('deployment_id')==panel['deployment_id'],'deployment mismatch')
    study.sha(calibration.get('source_freeze_sha256'),'calibration source')
    byid={r['id']:r for r in panel['calibration']}
    expected={(i,s,a,k) for i in byid for s in range(2) for a in study.FIXED for k in ('warmup','measure')}
    seen={};rows=calibration.get('records',[])
    for r in rows:
        key=(r['id'],r['session'],r['arm'],r['kind'])
        study.require(key in expected and key not in seen,'duplicate, extra or held-out calibration row')
        study.require(r.get('root_id')==byid[r['id']]['root_id'],'calibration root mismatch')
        study.require(r.get('qualified') is True,'unqualified calibration row')
        study.require(r.get('source_freeze_sha256')==calibration['source_freeze_sha256'],'calibration source drift')
        t=r.get('seconds')
        study.require(type(t) in (float,int) and math.isfinite(t) and t>0,'invalid calibration seconds')
        seen[key]=r
    study.require(set(seen)==expected,'incomplete calibration; do not fit passing subset')
    logs={i:{a:statistics.mean(math.log(seen[i,s,a,'measure']['seconds']) for s in range(2))
             for a in study.FIXED} for i in byid}
    def best(ids):
        means={a:statistics.mean(logs[i][a] for i in ids) for a in study.FIXED}
        winner=min(TIE_ORDER,key=lambda a:means[a])
        return winner,means
    global_arm,gm=best(list(byid));bins={}
    for label in ('zero','low','high'):
        ids=[i for i,r in byid.items() if r['selection_bin']==label]
        choice=global_arm; improvement=None
        if len(ids)>=4:
            local,lm=best(ids);improvement=1-math.exp(lm[local]-lm[global_arm])
            if improvement>=.02:choice=local
        bins[label]={'roots':len(ids),'arm':choice,'within_calibration_time_reduction_vs_global':improvement}
    seconds=calibration.get('calibration_total_seconds')
    study.require(type(seconds) in (float,int) and math.isfinite(seconds) and seconds>0,'measured calibration total cost required')
    return {'schema_version':1,'status':'CALIBRATION_FROZEN_NOT_TESTED','deployment_id':panel['deployment_id'],
            'panel_sha256':study.digest(panel),'source_freeze_sha256':calibration['source_freeze_sha256'],
            'calibration_input_ids':sorted(byid),'global_fixed_arm':global_arm,'bins':bins,
            'calibration_total_seconds':seconds,'lookup_cost_seconds':None,
            'decision_inputs':['deployment_id','old_WB_extra_call_density'],
            'warning':'No native qualification or useful policy gain follows from this fit.'}

def choose(policy: dict[str,Any], deployment_id: str, *, extra_calls: int, qb_calls: int) -> str:
    study.require(deployment_id==policy['deployment_id'],'selector deployment drift')
    study.integer(extra_calls,'extra calls',0);study.integer(qb_calls,'QB calls',1)
    density=extra_calls/qb_calls
    label='zero' if extra_calls==0 else 'low' if density<=.125 else 'high'
    arm=policy['bins'][label]['arm']
    study.require(arm in study.FIXED,'invalid frozen selector arm')
    return arm

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('calibration',type=Path);p.add_argument('panel',type=Path)
    a=p.parse_args()
    try:
        result=fit(json.loads(a.calibration.read_text()),json.loads(a.panel.read_text()))
        print(json.dumps(result,indent=2,allow_nan=False))
    except (ValueError,TypeError,KeyError) as e:raise SystemExit('REFUSED: '+str(e))
