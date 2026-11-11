import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from native_adapter import ROOT,RUNS,sha,put
from qualify_host import QUAL

summary=json.loads((ROOT/'O-SERVICE-QUALIFICATION.json').read_bytes());rows=[]
assert summary['status']=='FINITE_NATIVE_CAPTURE_MATCH' and len(summary['proofs'])==12
for entry in summary['proofs']:
    ix,arm=entry['root'],entry['arm'];row=dict(root=ix,arm=arm)
    proof=QUAL/('O-root'+str(ix))/(arm+'-QUALIFICATION.json');assert json.loads(proof.read_bytes())==entry['proof']
    row['qualification_sha256']=sha(proof)
    for stage in ('development','priming'):
        candidates=[p for p in RUNS.glob('O-'+stage+'-'+arm+'-root'+str(ix)+'*') if (p/'exit.json').exists() and json.loads((p/'exit.json').read_bytes())['status']=='COMPLETE']
        assert len(candidates)==1,(stage,ix,arm,candidates)
        p=candidates[0];row[stage]=str(p);row[stage+'_modules_sha256']=sha(p/'ACTUAL_MODULES.json')
        row[stage+'_job_sha256']=sha(p/'job.json');row[stage+'_receipt_sha256']=sha(p/'session-result.json')
    rows.append(row)
put(ROOT/'O-SERVICE-RUNTIME-BINDING.json',dict(proofs=rows,qualification_sha256=sha(ROOT/'O-SERVICE-QUALIFICATION.json'),scope='Offline provenance binding to actual completed GPU qualifications; not a new qualification or readiness substitute'))
