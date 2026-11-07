from final_calibration07 import *
import selector
import datetime
def main():
    p=read(ROOT/'provisional-cohort.json'); census={r['id']:r for r in read(ROOT/'descriptor-census.json')['rows']}
    groups={}
    for name in ('calibration','test'):
        groups[name]=[]
        for r in p[name]:
            c=census[r['id']];calls=c['scenarios']['1'];extra=calls['WB-cut']-calls['QB'];density=extra/calls['QB']
            groups[name].append(dict(id=r['id'],root_id=r['root_id'],selection_bin='zero' if extra==0 else 'low' if density<=.125 else 'high',logical_lcp=c['logical_lcp'],effective_head=c['effective_head'],physical_head=read(ROOT/f'cal-q07-{len(groups[name]):02}/QB-heavy/receipt.json')['physical_dense_head'] if name=='calibration' else None,physical_observed=name=='calibration'))
    panel=dict(schema_version=1,manifest_sha256=sha(ROOT/'tokenize01/tokens.jsonl'),deployment_id='RTX-C4096-exact-lcp-native-template',status='LOCAL_CALIBRATION_BOUND_SHARED_COHORT_UNCONFIRMED',**groups)
    put(ROOT/'local-panel07.json',panel)
    source=read(ROOT/'candidate07/binding.json');source_hash=study.digest(source);records=[]
    total=0
    for path in ROOT.glob('cal-*/exit.json'):total+=read(path)['elapsed_s']
    for s in range(2):
        for i,r in enumerate(panel['calibration']):
            ref=read(ROOT/f'cal-r-{i:02}/r0/receipt.json')
            for arm in study.FIXED:
                for kind in ('warmup','measure'):
                    raw=read(ROOT/f'cal-cost07-s{s}/i{i:02}'/arm/kind/'receipt.json');assert raw['output']==ref['output'] and raw['final_position']==ref['final_position']
                    records.append(dict(id=r['id'],root_id=r['root_id'],session=s,arm=arm,kind=kind,seconds=raw['service_s'],qualified=True,source_freeze_sha256=source_hash))
    start=datetime.datetime.fromisoformat(read(ROOT/'cal-r-00/launch.json')['start_utc'].replace('Z','+00:00'))
    end=datetime.datetime.now(datetime.timezone.utc)
    campaign=(end-start).total_seconds()
    cal=dict(stage='calibration',deployment_id=panel['deployment_id'],panel_sha256=study.digest(panel),source_freeze_sha256=source_hash,calibration_total_seconds=campaign,native_process_subtotal_seconds=total,cost_window_start_utc=start.isoformat(),cost_window_end_utc=end.isoformat(),cost_window='full observed calibration campaign elapsed, including intervening engineering and idle time; native subprocess subtotal reported separately',records=records)
    put(ROOT/'calibration07.json',cal);policy=selector.fit(cal,panel);put(ROOT/'policy07.json',policy)
    put(ROOT/'SOURCE_POLICY_FREEZE07.json',dict(status='LOCAL_SOURCE_POLICY_FROZEN_COMMON_BLIND_GATE_CLOSED',source=source,source_sha256=source_hash,panel_sha256=study.digest(panel),policy_sha256=study.digest(policy),calibration_sha256=study.digest(cal),counterpart_freeze=None,common_heldout_outputs=0,limitations=['shared renderer/cohort/deployment requires B570 attestation','heldout native physical heads and qualification remain unobserved'],cost_includes='all calibration native process wall, original references, both qualification epochs, warmups, timed sessions, imports, prefix construction, model loading'))
    print(policy)
if __name__=='__main__':main()
