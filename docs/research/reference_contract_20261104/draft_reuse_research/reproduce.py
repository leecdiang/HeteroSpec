#!/usr/bin/env python3
"""CPU-only QB overlap ceiling with GS/PQ negative controls.

Default: recompute from the published, SHA-bound compact source projection.
Optional --archives DIR: reconstruct projection from both original release ZIPs,
checking archive/member hashes and all 672 formal records before comparison.
Writes only stdout or an explicitly named output outside the evidence files.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import statistics
import zipfile

HERE = Path(__file__).resolve().parent
ARMS = {'R', 'M_GS', 'C_GS', 'M_PQ', 'C_PQ', 'M_QB', 'C_QB'}
SCOPES = ('GS', 'PQ', 'QB')

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def encode(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()

def extract(archives, manifest):
    groups = collections.defaultdict(dict)
    seen = set()
    memory = []
    for item in manifest['archives']:
        path = archives / item['filename']
        data = path.read_bytes()
        require(sha(data) == item['sha256'], 'Archive hash mismatch: ' + path.name)
        with zipfile.ZipFile(path) as archive:
            require(archive.testzip() is None, 'ZIP CRC failure: ' + path.name)
            for member in sorted(archive.namelist()):
                if not member.endswith(('/off.json', '/PROVISIONED.json')):
                    continue
                raw = archive.read(member)
                obj = json.loads(raw)
                if member.endswith('/PROVISIONED.json'):
                    memory.append({'archive': path.name, 'member': member, 'sha256': sha(raw), 'family': obj['family'], 'memory_after_provisioning': obj['memory_after_provisioning']})
                    continue
                slot = obj.get('slot', {})
                if slot.get('stage') != 'formal':
                    continue
                require(slot['slot_id'] not in seen, 'Duplicate slot')
                seen.add(slot['slot_id'])
                require(slot['observer'] == 'off' and not obj['capture'], 'Unexpected observer/capture')
                key = (slot['family'], slot['date_slot'], slot['session_slot'], slot['input_id'])
                require(obj['arm'] not in groups[key], 'Duplicate arm')
                groups[key][obj['arm']] = (obj, {'archive': path.name, 'member': member, 'sha256': sha(raw)})
    require(len(seen) == 672 and len(groups) == 96, 'Incomplete source records')
    rows = []
    for key, arms in sorted(groups.items()):
        require(set(arms) == ARMS, 'Missing/unexpected arms')
        require(len({json.dumps(v[0]['endpoint'], sort_keys=True) for v in arms.values()}) == 1, 'Different endpoints within block')
        for scope in SCOPES:
            m, ms = arms['M_' + scope]
            c, cs = arms['C_' + scope]
            rows.append({'key': list(key), 'scope': scope, 'M': m['service_seconds'], 'C': c['service_seconds'], 'M_target_prefill': m['target_phases']['PREFILL'], 'C_target_prefill': c['target_phases']['PREFILL'], 'C_draft_prefill': c['draft_phases']['PREFILL'], 'M_source': ms, 'C_source': cs})
    return {'schema': 1, 'source_formal_records': 672, 'input_session_blocks': 96, 'paired_scope_records': 288, 'rows': rows, 'memory': memory}

def summarize(projection):
    rows = projection['rows']
    require(len(rows) == 288, 'Projection row count')
    require(len({tuple(r['key']) + (r['scope'],) for r in rows}) == 288, 'Duplicate projection row')
    summaries = []
    for scope in SCOPES:
        for family in ('Qwen', 'SmolLM2'):
            rr = [r for r in rows if r['scope'] == scope and r['key'][0] == family]
            require(len(rr) == 48, 'Incomplete scope/family')
            losing = [r for r in rr if r['C'] > r['M']]
            residual = lambda r: (r['M'] - r['M_target_prefill']) - (r['C'] - r['C_target_prefill'] - r['C_draft_prefill'])
            overlap = lambda r: min(r['C_target_prefill'], r['C_draft_prefill'])
            summaries.append({'scope': scope, 'family': family, 'n': len(rr), 'losers': len(losing), 'losers_positive_nonprefill_residual': sum(residual(r) > 0 for r in losing), 'losers_negative_nonprefill_residual': sum(residual(r) < 0 for r in losing), 'losers_still_losing_after_full_draft_prefill_deletion': sum(r['C'] - r['C_draft_prefill'] > r['M'] for r in losing), 'ideal_overlap_remaining_losers': sum(r['C'] - overlap(r) > r['M'] for r in rr), 'mean_target_prefill_s': statistics.mean(r['C_target_prefill'] for r in rr), 'mean_draft_prefill_s': statistics.mean(r['C_draft_prefill'] for r in rr), 'sum_C_over_M': sum(r['C'] for r in rr) / sum(r['M'] for r in rr), 'sum_ideal_overlap_over_M': sum(r['C'] - overlap(r) for r in rr) / sum(r['M'] for r in rr)})
    return {'scope': 'QB-only 56-loss finding; GS/PQ are explicit negative controls. Same 12 exposed inputs repeated across four sessions per family, not 96 independent workloads.', 'warning': 'Host accounting sensitivity only. Perfect overlap of unchanged sequential phases, zero contention/overhead, fixed target-only M. NOT GPU concurrency, measured acceleration, or a prediction against fairly cached target-only. Neither arithmetic residual nor synchronized host phase is exclusive GPU kernel time.', 'formula': 'residual=(M-M_target_prefill)-(C-C_target_prefill-C_draft_prefill); ideal_overlap_cost=C-min(C_target_prefill,C_draft_prefill)', 'source_formal_records': projection['source_formal_records'], 'input_session_blocks': projection['input_session_blocks'], 'scope_pairs': len(rows), 'summary': summaries, 'memory': projection['memory']}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', type=Path, help='Optional directory containing both pinned release ZIPs, to independently reconstruct and check the projection')
    parser.add_argument('--output', type=Path, help='Optional new result path; default is stdout')
    args = parser.parse_args()
    manifest_path = HERE / 'SOURCE_MANIFEST.json'
    projection_path = HERE / 'source_projection.json'
    manifest = json.loads(manifest_path.read_text())
    raw = projection_path.read_bytes()
    require(sha(raw) == manifest['projection_sha256'], 'Projection SHA256 mismatch')
    projection = json.loads(raw)
    if args.archives:
        rebuilt = extract(args.archives, manifest)
        require(encode(rebuilt) == raw, 'Source projection differs from original ZIPs')
    result = summarize(projection)
    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        reserved = {p.resolve() for p in HERE.iterdir() if p.is_file()}
        require(args.output.resolve() not in reserved, 'Refusing to overwrite published evidence/source')
        args.output.write_text(text)
    else:
        print(text, end='')

if __name__ == '__main__':
    main()
