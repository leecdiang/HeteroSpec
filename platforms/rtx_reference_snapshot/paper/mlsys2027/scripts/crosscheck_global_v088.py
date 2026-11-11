#!/usr/bin/env python3
"""Independent NumPy derivation from retained original B QPC endpoints."""
import hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3];E=ROOT/'paper/mlsys2027/evidence'
def main():
    source=E/'RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/B-formal.ORIGINAL_RECORDS.json'
    original=json.loads(source.read_text())['runs']
    derived=json.loads((E/'GLOBAL_ANALYSIS_V088.json').read_text())
    assert len(original)==171 and all(r['status']=='VALID' for r in original)
    descriptors={};max_difference=0
    for c,want in derived['distribution'].items():
        tasks={r['task_id'] for r in original if r['condition']==c};assert len(tasks)==19
        medians=[]
        for task in sorted(tasks):
            rr=[r for r in original if r['task_id']==task and r['condition']==c]
            assert sorted(r['repetition'] for r in rr)==[1,2,3]
            seconds=np.asarray([(r['timer']['end_qpc']-r['timer']['start_qpc'])/r['timer']['frequency'] for r in rr])
            assert all(abs(s-r['timer']['milliseconds']/1000)<1e-12 for s,r in zip(seconds,rr))
            medians.append(float(np.median(seconds)))
        vv=np.quantile(medians,[0,.25,.5,.75,1],method='linear')
        got=dict(zip(['min_s','q25_s','median_s','q75_s','max_s'],map(float,vv)))
        max_difference=max(max_difference,max(abs(v-want[k]) for k,v in got.items()))
        descriptors[c]=got
    assert max_difference<1e-12,max_difference
    report={'status':'PASS','original_records_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rows':171,'independent_implementation':'NumPy median/linear quantile from original end_qpc minus start_qpc; no use of global-analysis helper','descriptors':descriptors,'max_absolute_difference_s':max_difference,'scope':'CPU retained-record check, not new native execution or raw-log re-download'}
    (E/'GLOBAL_ANALYSIS_V088_QA.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='descriptors'}))
if __name__=='__main__':main()
