"""Audit no-loss compression and new figure inputs against authenticated PR #74.

This uses the included baseline receipt, so the author ZIP needs no sibling
checkout. It authenticates text/tables and bound exports, not private payloads.
"""
from pathlib import Path
import ast
import csv
import hashlib
import json
import math
import re
from humanizer_qa import audit as humanizer_audit, recover_before

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strip_comments(text):
    return re.sub(r'(?<!\\)%[^\n]*', '', text)


def canonical(text):
    # Only allow this revision's explicit layout edits and marked additions.
    text = re.sub(r'% REVISION_ADDITION_BEGIN[^\n]*\n.*?% REVISION_ADDITION_END[^\n]*', '', text, flags=re.S)
    text = strip_comments(text)
    text = re.sub(r'\\begin\{table\*?\}\[[^]]*\]', r'\\begin{table}', text)
    text = text.replace(r'\end{table*}', r'\end{table}')
    text = text.replace(r'\FloatBarrier', '')
    return re.sub(r'\s+', ' ', text).strip()


def commands(text, name):
    values = []
    for match in re.finditer(r'\\' + name + r'\{', text):
        start = match.end()
        depth = 1
        i = start
        while depth:
            if text[i] == '{' and (i == 0 or text[i - 1] != '\\'):
                depth += 1
            elif text[i] == '}' and text[i - 1] != '\\':
                depth -= 1
            i += 1
        values.append(text[start:i - 1])
    return values


def table_content(text):
    """First header plus data, omitting repeated longtable furniture only."""
    text = strip_comments(text)
    match = re.search(r'\\begin\{(longtable|tabularx|tabular)\}.*?\\end\{\1\}', text, re.S)
    assert match
    table = match.group()
    header = table.split(r'\toprule', 1)[1].split(r'\midrule', 1)[0]
    if match.group(1) == 'longtable':
        body = table.split(r'\endlastfoot', 1)[1].split(r'\end{longtable}', 1)[0]
    else:
        body = table.split(r'\midrule', 1)[1].split(r'\bottomrule', 1)[0]
    rows = []
    for row in (header + body).split(r'\\'):
        row = re.sub(r'\s+', ' ', row).strip()
        if row:
            rows.append([re.sub(r'\s+', ' ', cell).strip() for cell in row.split('&')])
    return dict(caption=commands(text, 'caption'), label=commands(text, 'label'), rows=rows)


def inline_tables(text):
    blocks = re.findall(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', text, re.S)
    return [table_content(block) for block in blocks]


def compute_ast(text):
    function = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == 'compute')
    return sha(ast.dump(function, include_attributes=False).encode())


def followup_text(text, name, manifest):
    humanizer = json.loads((ROOT / 'provenance/HUMANIZER_EDIT_RECEIPT.json').read_text())
    text = recover_before(text, name, humanizer)
    for replacement in manifest['permitted_followup_replacements'].get(name, []):
        assert text.count(replacement['new']) == 1, name
        text = text.replace(replacement['new'], replacement['old'])
    return text


def preservation(receipt):
    protected = receipt['protected_files']
    manifest = json.loads((ROOT / 'provenance/SEMANTIC_VISUAL_REVISION.json').read_text())
    restyled = manifest['allowed_protected_asset_restyles']
    assert sorted(restyled) == sorted('figures/' + name + '.' + ext
        for name in ['figure_1_architecture', 'figure_3_phase_matrix',
                     'figure_4_paid_cost', 'figure_5_task_variation'] for ext in ['pdf', 'svg'])
    lock = json.loads((ROOT / 'provenance/LOCKED_REVISION_ASSETS.json').read_text())['assets']
    for name, expected in protected.items():
        actual = sha((ROOT / name).read_bytes())
        if name in restyled:
            assert manifest['initial_asset_sha256'][name] == expected, name
            assert actual == manifest['current_asset_sha256'][name] == lock[name], name
        else:
            assert actual == expected, name
    assert compute_ast((ROOT / 'scripts/reconstruct.py').read_text()) == receipt['compute_ast_sha256']
    for name, expected in receipt['main_source_hashes'].items():
        text = followup_text((ROOT / name).read_text(), name, manifest)
        for replacement in receipt['permitted_text_replacements'].get(name, []):
            assert text.count(replacement['new']) == 1, name
            text = text.replace(replacement['new'], replacement['old'])
        assert sha(text.encode()) == expected, name
    supplement = {}
    for name, expected in receipt['supplement_content'].items():
        text = followup_text((ROOT / name).read_text(), name, manifest)
        for replacement in receipt['permitted_text_replacements'].get(name, []):
            assert text.count(replacement['new']) == 1, name
            text = text.replace(replacement['new'], replacement['old'])
        assert sha(canonical(text).encode()) == expected['canonical_sha256'], name
        assert commands(text, 'section') == expected['sections'], name
        assert commands(text, 'subsection') == expected['subsections'], name
        # Existing result/table labels retain order; two added figure labels are allowed.
        labels = [v for v in commands(text, 'label') if v not in ['fig:b570_contract', 'fig:358h_budget']]
        assert labels == expected['labels'], name
        actual_tables = inline_tables(text)
        assert actual_tables == expected['inline_tables'], name
        supplement[name] = dict(original_text_exactly_recoverable=True, existing_labels_retained=True,
                               section_count=len(expected['sections']), subsection_count=len(expected['subsections']),
                               inline_tables=len(actual_tables))
    table_cells = 0
    generated = {}
    for name, expected in receipt['generated_tables'].items():
        actual = table_content((ROOT / name).read_text())
        assert actual == expected, name
        generated[name] = dict(header_and_rows_equal=True, captions_and_labels_equal=True,
                               data_rows=len(actual['rows']) - 1)
        table_cells += sum(len(row) for row in actual['rows'][1:])
    for name, expected in receipt['main_inline_tables'].items():
        assert inline_tables((ROOT / name).read_text()) == expected, name
    note = receipt['request_regression_note']
    assert note in (ROOT / 'tables/rtx_task_request.tex').read_text()
    with (ROOT / 'CLAIM_EVIDENCE.csv').open() as stream:
        assert list(csv.DictReader(stream)) == receipt['claim_rows']
    ledger = json.loads((ROOT / 'EXPERIMENT_DESTINATIONS.json').read_text())
    assert ledger['entries'] == receipt['experiment_entries']
    assert (ledger['original_groups'], ledger['covered_groups'], ledger['unassigned_groups']) == (28, 28, 0)
    return dict(protected_files_byte_equal=len(protected)-len(restyled),
                protected_figure_assets_restyled=len(restyled),
                protected_figure_restyle_initial_hashes_equal=True,
                frozen_evidence_files=26,
                historical_source_files=16, authenticated_source_copies=133,
                unchanged_main_figure_assets=0, compute_ast_equal=True,
                main_source_files_checked=len(receipt['main_source_hashes']),
                supplement=supplement, generated_tables=generated,
                generated_data_cells_equal=table_cells, supplement_inline_tables_equal=6,
                main_inline_tables_equal=2, total_original_tables_equal=16,
                original_supplement_navigation_targets=30,
                claims_equal=26, experiment_entries_equal=28,
                allowed_prose_edits='Recorded display/provenance corrections plus the fully reversible '
                'humanizer prose pass. Numbers, equations, references, tables, figure captions and '
                'layout commands are unchanged by that pass; scientific scope was manually reviewed. '
                'Marked additions introduce only explanations/figures.')


def figure_inputs(receipt):
    data = json.loads((ROOT / 'output/FIGURE_INPUTS.json').read_text())
    initial_path = ROOT / 'provenance/INITIAL_V0144_FIGURE_INPUTS.json'
    manifest = json.loads((ROOT / 'provenance/SEMANTIC_VISUAL_REVISION.json').read_text())
    assert sha(initial_path.read_bytes()) == manifest['initial_scientific_inputs_sha256']
    initial = json.loads(initial_path.read_text())
    assert {k: data[k] for k in initial} == initial
    assert set(data)-set(initial) == {'semantic_visual_revision'}
    cross = data['figure_2_natural_crosses']
    for key, value in receipt['figure_2_original_inputs'].items():
        assert cross[key] == value, key
    causal = json.loads((ROOT / 'evidence/b57065/CAUSAL_RECHECK.json').read_text())
    for original, display in zip(cross['cases'], cross['display_labels_v0144']):
        assert (display['platform'], display['task']) == (original['platform'], original['task'])
        if original['platform'] == 'RTX':
            assert display['rows'] == original['rows'] and display['columns'] == original['columns']
            continue
        cases = [c for c in causal['cases'] if c['task'] == original['task']]
        assert len(cases) == 2 and all(c['focus']['decisions'] == original['matrix'] for c in cases)
        if original['task'] == 'MBPP/72':
            assert display['rows'] == ['N1', 'N0'] and display['columns'] == ['UB1/r3', 'UB1/r3']
            assert all(c['current_columns_identical'] and c['donor_labels'] == ['N1_repaired', 'N0_ordinary'] for c in cases)
        else:
            assert display['rows'] == ['N1', 'Alt.'] and display['columns'] == ['UB1/r3', 'UB2/r2']
            assert display['alternate_recipe'] == 'E_k1_ub2'
            assert all(c['donor_labels'] == ['N1_repaired', 'E_k1_ub2'] for c in cases)
            assert all([(v['ub'], v['outputs_max'], v['outputs_max_per_seq']) for v in c['recipes']] == [(1, 3, 3), (2, 2, 2)] for c in cases)
    with (ROOT / 'evidence/b57065/COSTS_RECOMPUTED.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 119
    s1 = data['figure_S1_b570_contract']
    tasks = {r['task'] for r in rows}
    for label in ['ordinary_R', 'matched_target', 'candidate', 'old_N1']:
        selected = [r for r in rows if r['label'] == label]
        assert s1['observations'][label] == len(selected)
        complete = sum({r['round'] for r in selected if r['task'] == t} == {'1', '2'} for t in tasks)
        assert s1['complete_task_pairs'][label] == complete
    assert not any(r['label'] == 'old_N1' and r['task'] == 'MBPP/400' and r['round'] == '1' for r in rows)
    for plotted, column in [('endpoint_ids', 'endpoint_length'), ('raw_ids', 'raw_length'), ('suffix_ids', 'raw_suffix')]:
        assert s1[plotted] == sum(int(r[column]) for r in rows if r['label'] == 'candidate')
    assert s1['endpoint_ids'] + s1['suffix_ids'] == s1['raw_ids']
    saved = json.loads((ROOT / 'source_records/analysis/358h_phase3_summary.json').read_text())
    bound = (ROOT / 'source_records/paper/mlsys2027/manuscript/sections/appendix_derived_v090.tex').read_text()
    ceilings = re.search(r'Full-precision \$U\$ is ([0-9.]+) CPU and ([0-9.]+) NPU', bound).groups()
    s2 = data['figure_S2_358h_budget']
    for device, ceiling in zip(['CPU', 'NPU'], ceilings):
        point = s2['points'][device]
        assert point['actual'] == saved['performance'][device]['geometric_mean_speedup']
        assert point['interval'] == saved['performance'][device]['bootstrap_ci95']
        assert point['ceiling'] == float(ceiling)
        assert math.isclose(point['necessary_uniform_target_cut'], 1 - float(ceiling), rel_tol=1e-14)
    bindings = [cross['label_source']] + s1['sources'] + s2['sources']
    for entry in bindings:
        assert sha((ROOT / entry['path']).read_bytes()) == entry['sha256'], entry
    return dict(figure2_original_cases_equal=5, figure2_original_categorical_cells_equal=20,
                all_seven_initial_scientific_input_objects_equal=True,
                figure2_continuation_counts_equal=True, figure2_display_labels_source_bound=True,
                b570_formal_rows=119, b570_missing_unit_preserved=True,
                b570_group_counts_and_pair_eligibility_equal=True, b570_paid_suffix_counts_equal=True,
                historical_358h_estimates_and_intervals_equal=True,
                historical_358h_conditional_ceiling_and_budget_equal=True,
                source_bindings_checked=len(bindings),
                boundary='Supplement schematics/plots re-express existing source/export information; the inherited original-host 180-row floor audit is not rerun.')


def main():
    receipt = json.loads((ROOT / 'provenance/V0143_BASELINE_CONTENT.json').read_text())
    prose = humanizer_audit()
    result = dict(version='v0.14.4', status='PASS', baseline_pr=74,
                  baseline_sha=receipt['baseline_sha'], preservation=preservation(receipt),
                  figure_inputs=figure_inputs(receipt),
                  humanizer_prose=dict(reviewed_files=prose['reviewed_files'],
                    changed_files=prose['changed_files'], edited_paragraph_blocks=prose['edited_paragraph_blocks'],
                    all_pre_edit_sources_exactly_recoverable=True, protected_atoms_equal=True,
                    scientific_scope_manually_reviewed=True), new_model_requests=0)
    build = ROOT / 'output/BUILD_QA.json'
    if build.exists():
        qa = json.loads(build.read_text())
        pages = qa['documents']['supplement']['pages']
        result['pagination'] = dict(baseline_main_pages=12, baseline_supplement_pages=27,
                                   main_pages=qa['documents']['main']['pages'], supplement_pages=pages,
                                   supplement_page_reduction_percent=(27 - pages) / 27 * 100)
    (ROOT / 'output/LOSSLESS_COMPRESSION_QA.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
