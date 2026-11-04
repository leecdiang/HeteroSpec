from common_calibration import *
import selector,datetime
def main():
    panel=read(ROOT/'common-panel.json');source=read(ROOT/'candidate07/binding.json');source_hash=study.digest(source);records=[]
    proof=read(ROOT/'COMMON_CALIBRATION_QUALIFICATION.json');assert len(proof)==36 and all(all(v for k,v in x.items() if k.endswith('equal')) for x in proof)
    diag=read(ROOT/'RESTORE_AND_APPEND_DIAGNOSTIC.json');assert all(x['vectors_equal'] and x['state_equal'] for x in diag['proof'])
    for s in range(2):
        for i,r in enumerate(panel['calibration']):
            ref=read(ROOT/f'common-r-{i:02}/r0/receipt.json');repeat=read(ROOT/f'common-r-{i:02}/r1/receipt.json');assert ref['output']==repeat['output']
            for arm in study.FIXED:
                for kind in ('warmup','measure'):
                    raw=read(ROOT/f'common-cost-s{s}/i{i:02}'/arm/kind/'receipt.json');assert raw['output']==ref['output'] and raw['final_position']==ref['final_position']
                    records.append(dict(id=r['id'],root_id=r['root_id'],session=s,arm=arm,kind=kind,seconds=raw['service_s'],qualified=True,source_freeze_sha256=source_hash))
    start=datetime.datetime.fromisoformat(read(ROOT/'cal-r-00/launch.json')['start_utc'].replace('Z','+00:00'));end=datetime.datetime.now(datetime.timezone.utc)
    subtotal=sum(read(p)['elapsed_s'] for p in ROOT.glob('*/exit.json'))
    cal=dict(stage='calibration',deployment_id=panel['deployment_id'],panel_sha256=study.digest(panel),source_freeze_sha256=source_hash,calibration_total_seconds=(end-start).total_seconds(),all_native_process_subtotal_seconds=subtotal,cost_window_start_utc=start.isoformat(),cost_window_end_utc=end.isoformat(),cost_scope='full observed calibration campaign elapsed including failed/superseded epochs, source repairs, reconciliation and idle time; all-native subtotal separately includes admission/census/development',records=records)
    put(ROOT/'COMMON_CALIBRATION.json',cal);policy=selector.fit(cal,panel);put(ROOT/'COMMON_POLICY.json',policy)
    source_receipt=dict(status='SOURCE_POLICY_FROZEN_AWAITING_PEER_FREEZE',utc=end.isoformat(),deployment_id=panel['deployment_id'],source=source,source_sha256=source_hash,model_sha256=sha(MODEL),template_sha256=panel['configuration']['template_sha256'],cohort_receipt_sha256=sha(ROOT/'COHORT_RECEIPT.json'),panel_sha256=study.digest(panel),policy_sha256=study.digest(policy),calibration_sha256=study.digest(cal),service='file-backed immutable exact-token prefix replay; file read, map construction, reset, key lookup, native import, one policy lookup, append, greedy, synchronization and response commit inside complete service timer',cache_granule=1,padding=256,capacity=4096,common_heldout_outputs=0,qualification=sha(ROOT/'COMMON_CALIBRATION_QUALIFICATION.json'),restore_and_append_diagnostic=sha(ROOT/'RESTORE_AND_APPEND_DIAGNOSTIC.json'),request_reservations_started=sum(read(p)['requests'] for p in ROOT.glob('*/launch.json')),planned_remaining=1504,hard_tranche=2048)
    source_receipt['native_tokenizer_identity']=read(ROOT/'TOKENIZER_IDENTITY_MATCH.json')
    assert source_receipt['request_reservations_started']+1504<=2048
    put(ROOT/'SOURCE_POLICY_FREEZE.json',source_receipt);print(json.dumps(policy,indent=2))
if __name__=='__main__':main()
