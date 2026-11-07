#!/usr/bin/env python3
"""Recompute the retrospective seven-arm recorded-work audit (CPU only).

Default input is the compact, hashed field projection in the paper. --raw-root,
--archive, or --parts-dir additionally reopens original RECORD.json bytes and
checks their archive-index hashes before reproducing that projection. A compact
projection cannot by itself authenticate its derivation from omitted raw bytes.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path('anc/seven_arm_work_audit')
SOURCE_COMMIT = '85b3f2d6e43ea7d19fb4b0f6827cbd7f492f6fdb'
ARCHIVE_SHA256 = 'add03d38b93dbfcb9695091e9ce0de2cfd6c80ef22f8dfafe12162ced16bf9e4'
INDEX_SHA256 = '91e6bf26c28f6cb4e28837a990936c122236e88389102031232e0fc0eda58cdc'
PLAN_SHA256 = '63c3722bc65ba4f1c9c5ebaca3f7bc866af479b8cdbff344841bc896a40f3797'
SEMANTICS_SHA256 = 'c21401730941b4d44b1650211424a7061dd056278802bedf70f4a9b231c01232'
FAMILIES = ('Qwen', 'SmolLM2', 'Llama')
ARMS = ('R', 'M_GS', 'M_PQ', 'M_QB', 'C_GS', 'C_PQ', 'C_QB')
PAIRS = (('GS', 'PQ'), ('GS', 'QB'), ('PQ', 'QB'))
LOGICAL_FIELDS = (
    'prompt_ids_count', 'output_ids_count', 'proposal_generated', 'proposal_verified',
    'accepted_committed', 'first_mismatch_rejected', 'unexamined_after_mismatch',
    'terminal_discarded', 'unverified_before_verify', 'initial_target_committed',
    'bonus_committed', 'correction_committed', 'fallback_committed', 'verify_cycles',
    'verification_seed_rows', 'rollback_calls', 'accepted_prefix_hist',
    'cycle_progress_hist', 'verification_caller_width_hist', 'attempted_positions',
    'accepted_positions', 'draft_prefill_calls', 'draft_prefill_ids',
    'draft_continuation_caller_calls', 'draft_continuation_caller_rows',
    'target_prefill_calls', 'target_prefill_ids', 'target_continuation_calls',
    'target_continuation_rows', 'target_verification_calls', 'target_replay_calls',
    'target_fallback_calls', 'target_caller_width_hist',
)
DRAFT_PHYSICAL_FIELDS = (
    'draft_continuation_calls', 'draft_continuation_rows', 'draft_proposal_calls',
    'draft_proposal_rows', 'draft_catchup_calls', 'draft_catchup_rows',
)
PHYSICAL_FIELDS = (
    'physical_micrograph_calls', 'physical_micrograph_rows', 'graphs_reused',
    'target_prefill_physical_calls', 'draft_prefill_physical_calls',
    'target_continuation_physical_width_hist', 'target_physical_width_hist',
    'draft_physical_width_hist',
)
METADATA_FIELDS = ('physical_semantics', 'unsupported_replay', 'counter_semantics_sha256')
ALL_WORK_FIELDS = set(LOGICAL_FIELDS + DRAFT_PHYSICAL_FIELDS + PHYSICAL_FIELDS + METADATA_FIELDS)
ENDPOINT_FIELDS = ('ids', 'eog_flags', 'length', 'terminal_id', 'stop_reason', 'cached_tokens', 'truncated')
RECORD_FIELDS = (
    'slot', 'task', 'family', 'condition', 'phase', 'warmup', 'freeze_commit',
    'input_sha256', 'status', 'runtime_identity_verified', 'measurement_mode',
    'observation', 'actual_condition', 'contract_valid', 'source_identity_sha256',
    'workload', 'workload_error', 'study_phase', 'session', 'round', 'position',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def loads(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def json_bytes(obj):
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def csv_bytes(rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def endpoint(record):
    return {key: record['output'][key] for key in ENDPOINT_FIELDS}


def project_record(raw, member_path, expected):
    """Authenticate a raw member; retain only source fields used by this audit."""
    require(len(raw) == expected['bytes'] and sha(raw) == expected['sha256'],
            f'Original record hash/size mismatch: {member_path}')
    record = loads(raw)
    require(record['workload'] == record['response']['hs_closeout']['workload'],
            f'Native/top-level workload mismatch: {member_path}')
    require(record['output']['ids'] == record['response']['tokens'],
            f'Native/top-level output-ID mismatch: {member_path}')
    projection = {key: record[key] for key in RECORD_FIELDS}
    projection['prospective_correction_version'] = record.get('prospective_correction_version')
    projection['output'] = endpoint(record)
    projection['source_member'] = member_path
    projection['source_sha256'] = expected['sha256']
    projection['source_bytes'] = expected['bytes']
    return projection


def hist_count(hist):
    return sum(hist.values())


def hist_rows(hist):
    return sum(int(k) * value for k, value in hist.items())


def validate_record(r):
    w = r['workload']
    require(set(w) == ALL_WORK_FIELDS, f'Unexpected workload schema: {r["slot"]}')
    require(r['status'] == 'COMPLETED' and r['phase'] == 'formal' and
            r['study_phase'] == 'P2' and r['warmup'] is False, 'Nonformal record admitted')
    require(r['measurement_mode'] == 'counts' and r['runtime_identity_verified'] is True and
            r['contract_valid'] is True and r['workload_error'] is None, 'Invalid formal measurement')
    require(r['observation'] == {'phase_timers': False, 'heavy_capture': False,
                                'etw': False, 'added_sync': False}, 'Observation mode changed')
    require(w['unsupported_replay'] is False, 'Unsupported replay admitted')
    require(w['counter_semantics_sha256'] == SEMANTICS_SHA256, 'Counter semantics identity changed')
    require(w['physical_semantics'] == 'actual tokens passed to graph_compute; not hardware occupancy',
            'Physical counter meaning changed')
    o = r['output']
    require(set(o) == set(ENDPOINT_FIELDS), 'Endpoint projection schema changed')
    require(o['length'] == len(o['ids']) == len(o['eog_flags']) == w['output_ids_count'],
            'Output-length conservation failed')
    require(o['length'] > 0 and o['terminal_id'] == o['ids'][-1], 'Terminal-ID mismatch')
    require(o['cached_tokens'] == 0 and o['truncated'] is False, 'Output contract changed')
    require(all(type(x) is int for x in o['ids']) and all(type(x) is bool for x in o['eog_flags']),
            'Invalid native ID/EOG types')
    require((o['stop_reason'] == 'EOG' and o['eog_flags'][-1] and not any(o['eog_flags'][:-1])) or
            (o['stop_reason'] == 'CAP' and not any(o['eog_flags'])), 'Invalid stop/EOG relation')
    for field in LOGICAL_FIELDS + DRAFT_PHYSICAL_FIELDS + PHYSICAL_FIELDS:
        value = w[field]
        if isinstance(value, dict):
            require(all(re.fullmatch(r'\d+', k) and type(v) is int and v >= 0
                        for k, v in value.items()), f'Invalid histogram {field}')
        else:
            require(type(value) is int and value >= 0, f'Invalid counter {field}')
    identities = {
        'proposal destinations': (w['proposal_generated'], sum(w[k] for k in (
            'accepted_committed', 'first_mismatch_rejected', 'unexamined_after_mismatch',
            'terminal_discarded', 'unverified_before_verify'))),
        'verified proposals': (w['proposal_generated'], w['proposal_verified'] + w['unverified_before_verify']),
        'committed output origins': (w['output_ids_count'], sum(w[k] for k in (
            'initial_target_committed', 'accepted_committed', 'bonus_committed',
            'correction_committed', 'fallback_committed'))),
        'prefix cycles': (w['verify_cycles'], hist_count(w['accepted_prefix_hist'])),
        'progress cycles': (w['verify_cycles'], hist_count(w['cycle_progress_hist'])),
        'committed prefix total': (w['accepted_committed'], hist_rows(w['accepted_prefix_hist'])),
        'accepted positions': (w['accepted_committed'], hist_count(w['accepted_positions'])),
        'seed rows': (w['verification_seed_rows'], w['verify_cycles']),
        'verification caller count': (w['verify_cycles'], hist_count(w['verification_caller_width_hist'])),
        'verification caller rows': (w['proposal_verified'] + w['verification_seed_rows'],
                                     hist_rows(w['verification_caller_width_hist'])),
        'draft physical calls': (w['draft_continuation_calls'], w['draft_proposal_calls'] + w['draft_catchup_calls']),
        'draft physical rows': (w['draft_continuation_rows'], w['draft_proposal_rows'] + w['draft_catchup_rows']),
        'draft caller/physical rows': (w['draft_continuation_caller_rows'], w['draft_continuation_rows']),
        'target continuation calls': (w['target_continuation_calls'], w['target_verification_calls'] +
                                      w['target_replay_calls'] + w['target_fallback_calls']),
        'target caller count': (w['target_continuation_calls'], hist_count(w['target_caller_width_hist'])),
        'target caller rows': (w['target_continuation_rows'], hist_rows(w['target_caller_width_hist'])),
        'target physical rows': (w['target_prefill_ids'] + w['target_continuation_rows'], hist_rows(w['target_physical_width_hist'])),
        'draft total physical rows': (w['draft_prefill_ids'] + w['draft_continuation_caller_rows'], hist_rows(w['draft_physical_width_hist'])),
        'total physical rows': (w['physical_micrograph_rows'], hist_rows(w['target_physical_width_hist']) + hist_rows(w['draft_physical_width_hist'])),
        'total physical calls': (w['physical_micrograph_calls'], hist_count(w['target_physical_width_hist']) + hist_count(w['draft_physical_width_hist'])),
        'target prefill/continuation physical calls': (hist_count(w['target_physical_width_hist']), w['target_prefill_physical_calls'] + hist_count(w['target_continuation_physical_width_hist'])),
        'draft prefill/continuation physical calls': (hist_count(w['draft_physical_width_hist']), w['draft_prefill_physical_calls'] + w['draft_continuation_calls']),
    }
    for label, (left, right) in identities.items():
        require(left == right, f'Conservation failed ({label}): {r["slot"]}: {left} != {right}')
    require(w['graphs_reused'] <= w['physical_micrograph_calls'], 'Impossible graph reuse count')
    return len(identities)


def load_inputs(root):
    data = Path(root) / DATA
    receipt = loads((data / 'source_receipt.json').read_bytes())
    require(receipt['source_commit'] == SOURCE_COMMIT and receipt['archive']['sha256'] == ARCHIVE_SHA256,
            'Pinned source identity changed')
    for name, identity in receipt['compact_inputs'].items():
        raw = (data / name).read_bytes()
        require(len(raw) == identity['bytes'] and sha(raw) == identity['sha256'], f'Compact source changed: {name}')
        if 'uncompressed_sha256' in identity:
            expanded = gzip.decompress(raw)
            require(sha(expanded) == identity['uncompressed_sha256'], f'Expanded source changed: {name}')
    index_bytes = gzip.decompress((data / 'archive_index.json.gz').read_bytes())
    plan_bytes = gzip.decompress((data / 'formal_plan.json.gz').read_bytes())
    require(sha(index_bytes) == INDEX_SHA256 and sha(plan_bytes) == PLAN_SHA256,
            'Pinned original archive index or plan changed')
    require(sha((data / 'COUNTER_SEMANTICS.md').read_bytes()) == SEMANTICS_SHA256,
            'Pinned counter-semantics text changed')
    index = loads(index_bytes)['files']
    plan = loads(plan_bytes)
    projections = [loads(line) for line in gzip.decompress((data / 'record_projection.jsonl.gz').read_bytes()).splitlines()]
    record_index = list(csv.DictReader(io.StringIO((data / 'record_index.csv').read_text())))
    require(len(record_index) == 2058 and sum(x['warmup'] == 'True' for x in record_index) == 42,
            'Raw-record/warmup index coverage changed')
    require(len({x['source_member'] for x in record_index}) == len(record_index), 'Duplicate raw index member')
    indexed = {x['source_member']: x for x in record_index}
    require(len(projections) == 2016, 'Formal projection must contain 2016 records')
    for r in projections:
        x = indexed[r['source_member']]
        require(x['warmup'] == 'False' and x['slot'] == r['slot'] and
                x['source_sha256'] == r['source_sha256'] and int(x['source_bytes']) == r['source_bytes'],
                'Projection/raw-index binding mismatch')
        require(index[r['source_member']] == {'bytes': r['source_bytes'], 'sha256': r['source_sha256']},
                'Projection/archive-index hash binding mismatch')
    require(len({r['source_member'] for r in projections}) == 2016, 'Duplicate projected member')
    return projections, plan, receipt, index


def derive(records, plan):
    planned = {}
    for block in plan['blocks']:
        require(block['admitted'] is True, 'Unexpected nonadmitted original block')
        for slot in block['slots']:
            require(slot['slot'] not in planned, 'Duplicate planned slot')
            planned[slot['slot']] = (block, slot)
    require(len(planned) == 2016 and set(planned) == {r['slot'] for r in records},
            'Actual records do not cover the exact original registered slots')
    grouped = defaultdict(dict)
    conservation = 0
    for r in records:
        conservation += validate_record(r)
        block, slot = planned[r['slot']]
        require(r['family'] == block['family'] and r['session'] == block['session'] and
                r['actual_condition'] == block['condition'] and
                r['condition'] == block['condition']['name'], 'Condition/family/session plan mismatch')
        require(all(r[k] == slot[k] for k in ('slot', 'task', 'round', 'position', 'input_sha256')),
                'Task/repeat/input registration mismatch')
        key = (r['family'], r['task'], r['session'], r['round'])
        require(r['condition'] not in grouped[key], 'Duplicate arm within matched block')
        grouped[key][r['condition']] = r
    require(len(grouped) == 288 and all(set(v) == set(ARMS) for v in grouped.values()),
            'Expected 288 complete seven-arm blocks')
    family_rows = {}
    endpoint_checks = endpoint_matches = 0
    pairs = []
    field_differences = defaultdict(Counter)
    for family in FAMILIES:
        keys = sorted(k for k in grouped if k[0] == family)
        require(len(keys) == 96 and len({k[1] for k in keys}) == 12 and
                {k[2] for k in keys} == {0, 1} and {k[3] for k in keys} == {0, 1, 2, 3},
                f'Panel dimensions wrong: {family}')
        fam = {'seven_arm_blocks': len(keys), 'sessions': 2, 'tasks': 12, 'repeats': 4,
               'endpoint_checks_vs_R': 0, 'endpoint_matches_vs_R': 0,
               'M_triples': 0, 'M_logical_equal_triples': 0, 'C_triples': 0, 'C_logical_equal_triples': 0}
        for key in keys:
            arms = grouped[key]
            ref = arms['R']
            for arm in ARMS[1:]:
                endpoint_checks += 1
                fam['endpoint_checks_vs_R'] += 1
                same = endpoint(arms[arm]) == endpoint(ref)
                endpoint_matches += same
                fam['endpoint_matches_vs_R'] += same
            for path in ('M', 'C'):
                fam[path + '_triples'] += 1
                triple_logical = True
                for a, b in PAIRS:
                    left, right = arms[path + '_' + a], arms[path + '_' + b]
                    lw, rw = left['workload'], right['workload']
                    diff = sorted(k for k in ALL_WORK_FIELDS if lw[k] != rw[k])
                    logical_diff = sorted(set(diff) & set(LOGICAL_FIELDS))
                    triple_logical &= not logical_diff
                    tag = path + '_' + a + '/' + path + '_' + b
                    field_differences[tag].update(diff)
                    row = {'family': family, 'task': key[1], 'session': key[2], 'repeat': key[3],
                           'path': path, 'left_arm': left['condition'], 'right_arm': right['condition'],
                           'input_equal': left['input_sha256'] == right['input_sha256'],
                           'endpoint_equal': endpoint(left) == endpoint(right),
                           'logical_equal': not logical_diff,
                           'draft_physical_equal': all(lw[k] == rw[k] for k in DRAFT_PHYSICAL_FIELDS),
                           'all_workload_fields_equal': not diff,
                           'differing_workload_fields': '|'.join(diff),
                           'left_record_sha256': left['source_sha256'], 'right_record_sha256': right['source_sha256']}
                    for k in ('proposal_generated', 'proposal_verified', 'accepted_committed', 'verify_cycles',
                              'target_prefill_ids', 'target_continuation_rows', 'draft_prefill_ids',
                              'draft_continuation_caller_rows', 'rollback_calls', 'physical_micrograph_calls',
                              'physical_micrograph_rows', 'target_prefill_physical_calls', 'graphs_reused'):
                        row['left_' + k], row['right_' + k] = lw[k], rw[k]
                    pairs.append(row)
                fam[path + '_logical_equal_triples'] += bool(triple_logical)
        family_rows[family] = fam
    summary = {
        'schema_version': 1,
        'audit_type': 'Retrospective exact matching of recorded work; no new model executions',
        'status': 'PASS' if all(r['logical_equal'] and r['draft_physical_equal'] and r['input_equal'] and
                              r['endpoint_equal'] for r in pairs) and endpoint_matches == endpoint_checks else 'DIFFERENCES_FOUND',
        'formal_records': len(records), 'warmups_excluded': 42, 'seven_arm_blocks': len(grouped),
        'session_count': 2, 'sessions_are_adjacent_not_independent_dates': True,
        'triple_count': sum(f['M_triples'] + f['C_triples'] for f in family_rows.values()),
        'pairwise_comparisons': len(pairs),
        'logical_equal_pairs': sum(r['logical_equal'] for r in pairs),
        'draft_physical_equal_pairs': sum(r['draft_physical_equal'] for r in pairs),
        'all_workload_fields_equal_pairs': sum(r['all_workload_fields_equal'] for r in pairs),
        'endpoint_checks_vs_matched_R': endpoint_checks, 'endpoint_matches_vs_matched_R': endpoint_matches,
        'endpoint_fields': list(ENDPOINT_FIELDS), 'conservation_identity_checks': conservation,
        'families': family_rows,
        'logical_fields': list(LOGICAL_FIELDS), 'fixed_draft_physical_fields': list(DRAFT_PHYSICAL_FIELDS),
        'physical_fields': list(PHYSICAL_FIELDS), 'metadata_fields': list(METADATA_FIELDS),
        'field_difference_counts': {k: dict(sorted(v.items())) for k, v in sorted(field_differences.items())},
        'prospective_correction_versions': dict(sorted(Counter(str(r['prospective_correction_version']) for r in records).items())),
        'freeze_commits': dict(sorted(Counter(r['freeze_commit'] for r in records).items())),
        'limits': [
            'Counts and histograms do not establish identical per-cycle event order or bitwise KV/logit states.',
            'Physical calls, graph reuse and target physical widths are treatment-dependent and are reported separately.',
            'Matched recorded work does not apportion complete-request time to projections, FFN, attention or instrumentation.',
            'This audit adds no independent sessions and changes no original costs, clocks or statistical weights.',
            'Default verification reproduces the hashed compact projection; original-byte derivation needs a raw input option.',
        ],
    }
    return pairs, summary


def table_bytes(summary):
    lines = [r'\begin{table*}[t]', r'\centering', r'\small',
             r'\begin{tabular}{lrrrr}', r'\toprule',
             r'Family & Matched groups & $M$ work triples & $C$ work triples & Endpoints vs. $R$ \\', r'\midrule']
    for name in FAMILIES:
        f = summary['families'][name]
        label = 'Qwen3' if name == 'Qwen' else name
        lines.append(f'{label} & {f["seven_arm_blocks"]} & {f["M_logical_equal_triples"]}/{f["M_triples"]} & '
                     f'{f["C_logical_equal_triples"]}/{f["C_triples"]} & '
                     f'{f["endpoint_matches_vs_R"]}/{f["endpoint_checks_vs_R"]} ' + r'\\')
    lines += [r'\midrule', f'Total & {summary["seven_arm_blocks"]} & '
              f'{sum(f["M_logical_equal_triples"] for f in summary["families"].values())}/288 & '
              f'{sum(f["C_logical_equal_triples"] for f in summary["families"].values())}/288 & '
              f'{summary["endpoint_matches_vs_matched_R"]}/{summary["endpoint_checks_vs_matched_R"]} ' + r'\\',
              r'\bottomrule', r'\end{tabular}',
              r'\caption{Retrospective audit of all 2,016 formal original seven-arm requests, excluding 42 warmups. '
              r'Each audit group matches family, task, session and repeat across arm-specific workers; each work triple compares GS, PQ and QB '
              r'within the target-only ($M$) or speculative ($C$) path. All three pairings per triple agree '
              r'in the recorded logical-work counters and acceptance/width histograms (1,728 pairings total). '
              r'Endpoint checks compare the complete native token IDs and recorded EOG flags, stop reason and terminal metadata '
              r'with the paired $R$ request. Physical graph calls, widths and reuse are reported separately; '
              r'aggregate counter equality does not establish bitwise state or per-cycle trace equality. '
              r'This adds no sessions and changes no original timings or weights.}',
              r'\label{tab:sevenarmwork}', r'\end{table*}']
    return ('\n'.join(lines) + '\n').encode()


def outputs(root):
    records, plan, _, _ = load_inputs(root)
    pairs, summary = derive(records, plan)
    return {str(DATA / 'pairwise.csv'): csv_bytes(pairs),
            str(DATA / 'summary.json'): json_bytes(summary),
            'tables/seven_arm_work_audit.tex': table_bytes(summary)}


def verify(check, root):
    generated = outputs(root)
    for name, expected in generated.items():
        check('Seven-arm recorded-work reproduction: ' + name, (Path(root) / name).read_bytes() == expected)
    summary = loads(generated[str(DATA / 'summary.json')])
    check('All 2016 original formal records cover 288 complete seven-arm blocks',
          summary['formal_records'] == 2016 and summary['seven_arm_blocks'] == 288)
    check('All 1728 within-path GS/PQ/QB pairs match recorded logical work',
          summary['logical_equal_pairs'] == summary['pairwise_comparisons'] == 1728)
    check('All 1728 non-R endpoints match paired R including full ID/EOG arrays',
          summary['endpoint_matches_vs_matched_R'] == summary['endpoint_checks_vs_matched_R'] == 1728)
    check('All 1728 within-path pairs retain the same fixed-draft physical work',
          summary['draft_physical_equal_pairs'] == 1728)
    check('Retrospective work audit passes without promoting counters to full-state evidence',
          summary['status'] == 'PASS' and summary['session_count'] == 2)
    return {key: summary[key] for key in ('status', 'formal_records', 'seven_arm_blocks',
            'triple_count', 'pairwise_comparisons', 'logical_equal_pairs', 'endpoint_matches_vs_matched_R')}


class SplitArchive(io.RawIOBase):
    def __init__(self, directory, parts):
        self.directory, self.parts = Path(directory), parts
        self.size, self.position = sum(x['bytes'] for x in parts), 0
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        require(self.position >= 0, 'Negative archive seek')
        return self.position
    def read(self, count=-1):
        if count < 0: count = self.size - self.position
        count = min(count, self.size - self.position)
        result, start = bytearray(), 0
        for part in self.parts:
            end = start + part['bytes']
            if self.position < end and count > 0:
                local = self.position - start
                take = min(count, part['bytes'] - local)
                with (self.directory / part['name']).open('rb') as handle:
                    handle.seek(local)
                    data = handle.read(take)
                require(len(data) == take, 'Short archive part')
                result.extend(data)
                self.position += take
                count -= take
            start = end
        return bytes(result)


def verify_originals(root, raw_root=None, archive=None, parts_dir=None):
    records, _, receipt, index = load_inputs(root)
    container = None
    verified_parts = []
    if raw_root:
        def read(name): return (Path(raw_root) / name).read_bytes()
    elif archive:
        digest = hashlib.sha256()
        with Path(archive).open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''): digest.update(chunk)
        require(digest.hexdigest() == receipt['archive']['sha256'], 'Whole original ZIP hash mismatch')
        container = zipfile.ZipFile(archive)
        read = container.read
    else:
        for part in receipt['archive']['parts']:
            path = Path(parts_dir) / part['name']
            if not path.exists(): continue
            raw = path.read_bytes()
            require(len(raw) == part['bytes'] and sha(raw) == part['sha256'], 'Archive-part hash mismatch')
            require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == part['git_blob_sha1'],
                    'Archive-part Git identity mismatch')
            verified_parts.append(part['name'])
        container = zipfile.ZipFile(SplitArchive(parts_dir, receipt['archive']['parts']))
        read = container.read
    checked = 0
    try:
        for expected in records:
            name = expected['source_member']
            actual = project_record(read(name), name, index[name])
            require(actual == expected, f'Compact projection not reproduced from original: {name}')
            checked += 1
    finally:
        if container is not None: container.close()
    return {'original_records_sha256_verified': checked,
            'full_native_response_IDs_and_workload_rechecked': checked,
            'raw_projection_exact_matches': checked, 'archive_parts_verified': verified_parts,
            'whole_archive_sha256_verified': bool(archive)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--write', action='store_true')
    raw = parser.add_mutually_exclusive_group()
    raw.add_argument('--raw-root', type=Path, help='Archive-relative original RECORD.json subtree')
    raw.add_argument('--archive', type=Path, help='Complete original RAW_EVIDENCE ZIP')
    raw.add_argument('--parts-dir', type=Path, help='Original split ZIP parts; 001,007,009 suffice for this audit')
    args = parser.parse_args()
    if args.write:
        for name, content in outputs(args.root).items():
            path = args.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    def check(name, condition): require(condition, name)
    report = verify(check, args.root)
    if args.raw_root or args.archive or args.parts_dir:
        report['original_byte_verification'] = verify_originals(args.root, args.raw_root, args.archive, args.parts_dir)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
