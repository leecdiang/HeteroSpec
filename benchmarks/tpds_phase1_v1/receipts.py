"""Small host adapters for saved receipts, build inputs and branch dispositions.

No subprocess launch, cloud purchase, source patching or auto-stopping peer work.
Reuse each platform's existing supervisor and immutable request ledger.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from design import require, write_new


def signature(events):
    """A comparison aid, NOT an equivalence proof from counts/labels.

    The host normalizes actual trace events into these fields and keeps raw logs.
    Durations and output values intentionally do not enter structural signatures.
    """
    keys=('operator','phase','shape','stride','dispatch','placement','group_rows','extent','output_mask','copies','graph_reuse')
    require(events and all(set(e)==set(keys) for e in events),'Complete normalized native events required')
    raw=json.dumps(events,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def natural_decision(evidence):
    required={'four_arms_qualified','distinct_mechanism','unanswered_natural_question','source_review','trace_review','numerical_failure','engineering_open','budget_available'}
    require(set(evidence)==required,'Explicit branch facts required')
    require(all(type(evidence[k]) is bool for k in required),'Boolean facts required')
    if evidence['numerical_failure']:
        return 'REPAIR_DEVELOPMENT_VERSION_KEEP_ORACLE'
    if evidence['engineering_open']:
        return 'CONTINUE_HOST_INTEGRATION'
    if not evidence['budget_available']:
        return 'CLOSE_BRANCH_RESOURCE_LIMIT'
    if not evidence['four_arms_qualified']:
        return 'CONTINUE_QUALIFICATION_OR_DOCUMENT_STRUCTURAL_COUPLING'
    if not (evidence['source_review'] and evidence['trace_review']):
        return 'COMPLETE_NATIVE_ALIAS_REVIEW'
    if evidence['distinct_mechanism'] and evidence['unanswered_natural_question']:
        return 'FREEZE_NEW_R1_NATURAL_PANEL'
    return 'CLOSE_R1_NATURAL_ONLY_CONTINUE_R2_AND_PORTABILITY'


def normalize_receipt(path, slot, reference_id, qualified):
    r=json.loads(Path(path).read_text())
    t=r.get('service_seconds')
    require(type(t) in (int,float) and math.isfinite(t) and t>0,'Missing native service_seconds')
    require(type(qualified) is bool and isinstance(reference_id,str) and reference_id,'Explicit qualification binding required')
    return dict(slot_id=slot,status='COMPLETE',qualified=qualified,service_s=t,reference_id=reference_id,
                native_receipt_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def saved_costs(path):
    """PR190 published result records; never materialize a full KV archive."""
    j=json.loads(Path(path).read_text());out={}
    for family,f in j['families'].items():
        out[family]={}
        for name,a in f['arms'].items():
            rows=a['rows']; require(rows,'Missing published request rows')
            terms={k:[] for k in ('service_s','planning_s','output_copy_s','reset_s','teardown_s','other_service_s')}
            target={};draft={}
            for r in rows:
                for key in terms: terms[key].append(r.get(key))
                for key,value in r.get('target_phases',{}).items():target[key]=target.get(key,0.)+value
                for key,value in r.get('draft_phases',{}).items():draft[key]=draft.get(key,0.)+value
            totals={k:None if any(v is None for v in values) else math.fsum(values) for k,values in terms.items()}
            out[family][name]=dict(requests=len(rows),totals=totals,target_phases_s=target,draft_phases_s=draft,
                note='Host envelopes; missing fields remain null. No device-time attribution from activity counts.')
    return out


def source_bundle(manifest, output):
    """Export explicit source/build recipe inputs, never weights or private secrets."""
    import zipfile
    root=Path(manifest['root']).resolve();output=Path(output)
    require(not output.exists(),'Do not overwrite a bundle')
    files={}
    for relative,expected in manifest['files'].items():
        rel=Path(relative);p=root/rel
        require(not rel.is_absolute() and '..' not in rel.parts and not p.is_symlink() and p.resolve().is_relative_to(root),'Unsafe bundle path')
        require(p.suffix.lower() not in ('.gguf','.dll','.exe','.bin','.key','.pem') and p.name not in ('.env','credentials'),'Not a source-only input')
        raw=p.read_bytes();require(hashlib.sha256(raw).hexdigest()==expected,'Bundle source hash mismatch')
        files[relative]=raw
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,11,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw)
    return dict(files=len(files),bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                status='SOURCE_BUNDLE_ONLY_BUILD_NOT_RUN')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('task',choices=['saved-costs','decision','source-bundle'])
    p.add_argument('input',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    j=None if a.task=='saved-costs' else json.loads(a.input.read_text())
    if a.task=='source-bundle':print(json.dumps(source_bundle(j,a.out)))
    else: write_new(a.out,saved_costs(a.input) if a.task=='saved-costs' else {'R1_natural':natural_decision(j)})
if __name__=='__main__': main()
