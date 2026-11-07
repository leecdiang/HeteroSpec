"""Read-only reconstruction of all formal paired slots; no native execution."""
from host import *
sys.path.insert(0,str(HERE.parents[1]/'tpds_prefix_reuse_v1'))
import study,statistics,math
def main(root):
    panel=read(root/'common-panel.json');schedule=read(root/'main-schedule.json');policy=read(root/'COMMON_POLICY.json');freeze=read(root/'SOURCE_POLICY_FREEZE.json')
    proof=read(root/'MAIN_QUALIFICATION.json');assert len(proof)==160 and all(all(v for k,v in x.items() if k.endswith('equal')) for x in proof)
    byid={r['id']:i for i,r in enumerate(panel['test'])};records=[]
    oracle=sha(root/'oracle02/worker.exe') if (root/'oracle02/worker.exe').exists() else read(root/'oracle02/binding.json')['exe']
    for slot in schedule['records']:
        i=byid[slot['id']];s=slot['session'];arm=slot['arm'];kind=slot['kind'];p=root/f'main-cost-s{s}/i{i:02}'/arm/kind/'receipt.json';raw=read(p);ref=read(root/f'main-r-{i:02}/r0/receipt.json')
        expected=arm if arm!='AUTO' else policy['bins'][panel['test'][i]['selection_bin']]['arm']
        assert raw['arm']==expected and raw['output']==ref['output'] and raw['final_position']==ref['final_position']
        launch=read(root/f'main-cost-s{s}/launch.json');assert launch['exe']==freeze['source']['exe'] and launch['source']==freeze['source']['source']
        records.append({**{k:slot[k] for k in ('id','root_id','session','arm','kind')},'seconds':raw['service_s'],'qualified':True,'actual_output_sha256':study.digest(raw['output']),'expected_output_sha256':study.digest(ref['output']),'source_freeze_sha256':sha(root/'SOURCE_POLICY_FREEZE.json'),'oracle_sha256':oracle})
    normalized=dict(schema_version=1,stage='main',deployment_id=panel['deployment_id'],panel_sha256=study.digest(panel),source_freeze_sha256=sha(root/'SOURCE_POLICY_FREEZE.json'),oracle_sha256=oracle,selector_sha256=study.digest(policy),records=records)
    result=study.analyze(normalized,panel)
    put(root/'results.json',normalized);put(root/'analysis.json',result)
    costs={}
    for arm in study.ARMS:
        values=[r['seconds'] for r in records if r['kind']=='measure' and r['arm']==arm]
        costs[arm]=dict(geomean_seconds=math.exp(statistics.mean(map(math.log,values))),arithmetic_mean_seconds=statistics.mean(values),median_seconds=statistics.median(values),descriptive_p95_seconds=study.quantile(values,.95))
    ledger=[]
    for p in sorted(root.glob('*/launch.json')):
        ledger.append(dict(path=p.parent.name,launch=read(p),exit=read(p.parent/'exit.json') if (p.parent/'exit.json').exists() else None,failure=read(p.parent/'failure.json') if (p.parent/'failure.json').exists() else None))
    put(root/'FINAL_ACCOUNTING.json',dict(entries=ledger,requests_reserved_started=sum(x['launch']['requests'] for x in ledger),zero_forward_started=sum(x['launch']['admissions'] for x in ledger),native_wall_seconds=sum(x['exit']['elapsed_s'] for x in ledger if x['exit']),calibration=read(root/'COMMON_CALIBRATION.json')['calibration_total_seconds'],main_warmup_seconds=sum(r['seconds'] for r in records if r['kind']=='warmup'),main_measure_seconds=sum(r['seconds'] for r in records if r['kind']=='measure'),costs=costs,scope='single RTX host, four sessions on one date; no cross-date or GPU-population inference'))
    print(json.dumps(result,indent=2));print(json.dumps(costs,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT)
