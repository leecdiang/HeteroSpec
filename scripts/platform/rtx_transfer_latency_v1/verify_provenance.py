"""Post-execution independent provenance extension; never used to run inference.

Added after completion to check source-head attribution not covered by the
pre-execution scientific verifiers. Neither runner nor aggregator is imported.
"""
import argparse, json
from pathlib import Path
from verify_common import read, meta, require, sha, package_checks

def check(root, arm, asset_root=None):
    metadata=meta(root); freeze=read(metadata/'runtime_freeze.json')
    ack=read(metadata/'chronology/joint_freeze.json')
    require(ack['commit']==ack['remote_ref'],'joint source remote acknowledgement differs')
    names=('harness_qualification','discovery_H1') if arm=='prediction' else ('formal',)
    allruns=[]; phases=[]
    for name in names:
        p=read(root/name/'records.json');phases.append(p)
        require(p['status']=='COMPLETE' and p['execution_head']==ack['commit'],'unexpected phase source head')
        require(p['freeze_sha256']==sha(metadata/'runtime_freeze.json'),'runtime freeze digest differs')
        require(ack['remote_ack_utc']<p['started_utc'],'execution preceded remote freeze')
        for r in p['runs']:
            require(r['source_head']==p['execution_head'],'run source differs from phase source')
            require(r['llama_commit']=='0cae43063cf15170e91a2ff4d034da0ecef4a1b2','upstream source differs')
            require(p['started_utc']<=r['started_utc']<r['ended_utc']<=p['ended_utc'],'run is outside phase interval')
        allruns.extend(p['runs'])
    for a,b in zip(allruns,allruns[1:]):require(a['ended_utc']<=b['started_utc'],'inference intervals overlap')
    require(len(allruns)==(162 if arm=='prediction' else 180),'actual per-arm execution coverage differs')
    r0=read(metadata/'R0_REVIEW.json')
    require(r0['status']=='PASS' and len(r0['runs'])==28 and r0['cap_probe']['status']=='PASS','joint R0 coverage differs')
    require(r0['hook_probe']['PASS'],'timer overhead gate failed')
    require(read(metadata/'IMMUTABILITY_CHECK.json')['status']=='PASS','old-file immutability audit failed')
    driver=read(metadata/'DRIVER_BYTE_OBSERVATIONS.json');require(driver['status']=='PASS','driver-byte observation differs')
    old={f['path']:f['sha256'] for f in driver['before']['files']}
    new={f['path']:f['sha256'] for f in driver['after']['files']}
    require(old==new,'driver modules changed during campaign')
    close=read(metadata/'CLOSEOUT.json')
    require(driver['before']['captured_utc']<close['A_first_discovery_utc']<close['B_first_timed_run_utc'],'driver observation not before scientific execution')
    require(driver['after']['captured_utc']>close['execution_ended_utc'],'driver rehash not after execution')
    require(close['prediction_status']=='MECHANISM_NOT_ISOLATED' and close['counts']['A_reserved_formal']==0,'reserved stop provenance differs')
    if arm=='prediction':
        require(sha(root/'exposure_inventory.json')==read(metadata/'RESERVED_SET.json')['full_audit_sha256'],'full exposure inventory digest differs')
        require(not (root/'reserved_live').exists() and not (root/'reserved_prediction').exists(),'reserved inference at stop')
    if asset_root:
        for path,h in new.items():require(sha(path)==h,'current driver module bytes differ')
    result={'status':'PASS','role':'post-execution supplementary provenance verification','arm':arm,'run_source_heads_checked':len(allruns),'execution_commit':ack['commit'],'source_freeze_commit':freeze['source_commit'],'chronology_and_nonoverlap_checked':True,'R0_count_checked':28,'driver_observation_consistency_checked':True}
    result.update(package_checks(root,metadata,arm,asset_root))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--arm',required=True,choices=['prediction','latency']);p.add_argument('--asset-root',type=Path);a=p.parse_args()
    print(json.dumps(check(a.root,a.arm,a.asset_root),indent=2))
