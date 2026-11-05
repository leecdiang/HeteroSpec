"""Per-lane readiness; one blocked platform/lane never suppresses another result.
Checks evidence links and scope, not truth or remote attestation.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from common import need,read,write_new,hexsha

def evaluate(r:dict)->dict:
    need(r['platform'] in ('rtx','b570'),'platform');out={}
    for lane,v in r['lanes'].items():
        blocking=[]
        for name in ('old_reference_available','old_reference_stable','observer_bridge_passed','actual_native_build_passed',
                     'resource_admission_passed','module_inventory_recorded','numerical_qualification_passed'):
            if v.get(name) is not True:blocking.append(name)
        if lane=='operator' and v.get('backend_loop4_executed') is not True:blocking.append('backend_loop4_executed')
        if lane=='draft' and r['platform']=='b570' and v.get('caller_only_control_present') is not True:blocking.append('caller_only_control_present')
        if lane=='draft' and v.get('target_contract')!='T':blocking.append('target_contract_T')
        for name in ('reference_identity_sha256','source_freeze_sha256','implementation_sha256'):
            try:hexsha(v.get(name),name)
            except ValueError:blocking.append(name)
        out[lane]={'status':'READY_FOR_FROZEN_CONFIRMATION' if not blocking else 'DEVELOPMENT_ONLY',
                   'blocking':blocking,'instruction':'repair local engineering or record scoped negative result; no inherited numerical pass'}
    return {'platform':r['platform'],'lanes':out,'cross_platform_barrier':False,
            'evidence_loss':'Reconstructed CPU runs have new identities; unavailable receipts cannot satisfy a gate.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('out',type=Path);a=p.parse_args();write_new(a.out,evaluate(read(a.input)))
