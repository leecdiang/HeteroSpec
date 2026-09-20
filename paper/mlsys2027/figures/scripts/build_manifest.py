#!/usr/bin/env python3
"""Document final artifacts and hashes after independent numerical and visual QA."""
from pathlib import Path
import csv, hashlib, json

HERE=Path(__file__).resolve().parents[1]
SHA='62d1c134b096882c37ce58c1d0ac140236acd9c3'
SPECS={
1:dict(question='What must be qualified and measured before claiming speculative speedup?',claim='Correctness admissibility precedes complete realized-cost accounting; the micro proxy is separate.',
    sources=['paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md','paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md'],tables=[],
    estimator='Conceptual accounting identity at one consistent boundary: S=C/(D_real+R_target+X); costs normalized by T_b.',
    evidence='FRAMEWORK / MECHANISM',correctness='Conceptual gate; no new measured qualification result.',
    caveats='C is all committed output, not accepted draft tokens. No claim of a new theory or that every platform exposes all costs.'),
2:dict(question='Does the physically cheapest target-forward path remain usable after correctness qualification?',claim='Cheap physical target batching may be blocked; serialization alone does not imply exactness.',
    sources=['work/m4/llama_verify_q8_synced.csv','artifacts/windows_verification_mechanism/windows-exact-verification-microbench.json',
    'reports/5070ti/WINDOWS_EXACT_VERIFICATION_COST.csv','reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md',
    'artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/v2_raw.json',
    'artifacts/b570_backend_control/exact-fallback-v1-20260912-222617/exact_fallback/processed/v2_exact.json',
    'analysis/b570_exact_fallback_summary.json','reports/b570/B570_VERIFICATION_MECHANISM.md'],tables=['figure2_micro_cells.csv'],
    estimator='Ratio of median PP2 to median PP1 (7 M4 or 20 RTX/B570 repetitions per cell). Range endpoints span tested contexts; no CI is drawn.',
    evidence='MECHANISM_SUPPORTED for qualified M4/RTX serialized; DIAGNOSTIC for RTX batched and both B570 timing paths.',
    correctness='M4 tested cells exact; RTX batched blocked; RTX serialized exact secondary control; B570 fast 45/90 and serialized 60/90, both globally inadmissible.',
    caveats='Contexts/stacks are not fully matched. V2_micro is not complete R_target or speedup. Formal B570 V2 was NOT RUN; contaminated earlier serialized values are excluded.'),
3:dict(question='Is the observed M4 profitable regime representative across the two frozen workloads?',claim='Representative 24Q remains negative beside separately preregistered positive HumanEval30 fixed-k2.',
    sources=['analysis/m4_confirmatory_prompt_summary.csv','analysis/m4_confirmatory_summary.json','analysis/m4_humaneval_prompt_summary.csv',
    'analysis/m4_humaneval_summary.json','scripts/summarize_m4_confirmatory.py','scripts/summarize_m4_humaneval.py',
    'benchmarks/m4_code_conditioned_30q/preregistration.json'],tables=['figure3_workloads.csv'],
    estimator='Across-prompt GM of within-prompt GMs of 3 paired ratios. 95% prompt bootstrap: 24Q Python RNG seed 20260907, 10,000 draws, sorted indices 249/9749; HumanEval seed 20260910, 100,000 draws, indices 2500/97499. Original input order preserved.',
    evidence='PRIMARY (both workloads)',correctness='24Q 72/72; HumanEval fixed-k2 90/90 exact token-ID pairs.',
    caveats='Not statistically paired between workloads. CIs condition on campaign and omit full session/thermal uncertainty. Exactness is not functional pass@k. No unified-memory causal claim.'),
4:dict(question='Why can isolated NPU drafting look favorable while the qualified realized path is much slower?',claim='The measured OpenVINO state interface incurs large replay-plus-proposal cost; CPU remains target-side dominated.',
    sources=['analysis/358h_draft_device_summary.csv','analysis/358h_draft_device_summary.json','analysis/358h_threshold_input_cpu.json',
    'analysis/358h_threshold_input_npu.json','analysis/358h_phase3_prompt_summary.csv','analysis/358h_phase3_decomposition.csv',
    'analysis/358h_phase3_summary.json','scripts/platform/358h/process_phase1_phase2_results.py','scripts/platform/358h/analyze_phase3_campaign.py',
    'scripts/platform/358h/phase3_heterogeneous_runner.py','reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md'],
    tables=['figure4_isolated.csv','figure4_realized.csv'],
    estimator='A: isolated median steady-state tok/s, n=5, 95% bootstrap CI (10,000 NumPy draws; seed 20260921+context). B: arithmetic mean seconds/request, 90 rows/device; shares are ratio of total component time to total speculative time. Headline speedup: GM of 30 within-prompt median paired ratios, 10,000 NumPy prompt-bootstrap draws, seed 20260919.',
    evidence='PRIMARY Phase-3 outcome + MECHANISM_SUPPORTED decomposition; formal Phase-1 isolated characterization.',
    correctness='CPU and NPU each 90/90 exact in Phase 3. Phase-1 throughput is a separate measurement boundary.',
    caveats='Post-prefill decode, not whole-request latency. Replay/proposal inseparable. Absolute bars preserve total-duration difference. Aggregate ratios differ from prompt-GM speedups. Phase-1 medians/CIs checked against summaries and retained TPOT vectors; separately tracked raw throughput arrays unavailable. No energy or persistent-state intervention claim.'),
5:dict(question='Which correctness/profitability regimes are supported by the tested cases?',claim='Observed regimes differ by path, workload and realized interface, rather than defining a hardware ranking.',
    sources=['paper/notes/CROSS_PLATFORM_MECHANISM.md','paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md','analysis/m4_confirmatory_summary.json',
    'analysis/m4_humaneval_summary.json','reports/5070ti/windows_humaneval_summary.json','reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.csv',
    'reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md','artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/diagnostic_summary.json',
    'analysis/b570_exact_fallback_summary.json','analysis/358h_phase3_summary.json'],tables=['figure5_regimes.csv','figure4_realized.csv'],
    estimator='Categorical classification; no numerical coordinates or CI. 358H percentages use the same total-time denominator as Figure 4.',
    evidence='Mixed, explicitly labeled P/S/M/D; 358H outcome/mechanism labels are P/M.',
    correctness='Five qualified case groups; three blocked groups. RTX serialized group includes two separately exact controls. Neither B570 group is qualified.',
    caveats='Blocked paths have no admissible profitability estimate. Blank cells mean no case shown. Cross-platform hardware/software/workloads co-vary. Mechanism rows are not an exhaustive taxonomy or continuous measure.')}

def table_text(rows,columns):
    def val(v):
        try:return f'{float(v):.9g}'
        except (ValueError,TypeError):return str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']+
                     ['| '+' | '.join(val(r[c]) for c in columns)+' |' for r in rows])

def main():
    lock=json.loads((HERE/'data/source_lock.json').read_text());lockmap={x['path']:x for x in lock}
    allfig=[];lines=['# MLSys 2027 candidate figure manifest','',
        '**Status: PUBLICATION-CANDIDATE** for the five standalone candidates at tested widths; OLD/NEW asset selection and manuscript integration remain pending.','',
        f'Scientific source commit: `{SHA}`. Branch: `paper/mlsys2027-figure-redesign-v0.2`. No manuscript checkpoint was available.','',
        'Figure IDs follow the user request (F2 paths; F3 M4). All 40 source files were verified against exact Git blob IDs and retain SHA256 in `data/source_lock.json`.','',
        'Skills discovered and read in this environment: visualize-data (primary plotting discipline), validate-data (independent per-figure pass), analyze-data-quality (input audit), jupyter-notebooks (audit companion), and PDF (export/render QA). No System Design skill was available. Scientific authority remains the repository.','',
        'Common extraction: `scripts/extract.py`. Common vector renderer: `scripts/plot.py` (`figure1`–`figure5`). Independent numerical pass: `scripts/validate.py --figure N --require-outputs`. Native-size rendering: `scripts/render_qa.py`.','',
        'Typography: embedded STIXGeneral/STIX; white background; no gradients/shadows/vendor colors. PNG files are preview-only. PDF/SVG are authoritative.','']
    hashes=[]
    for i,spec in SPECS.items():
        validation=json.loads((HERE/f'qa/figure{i}_validation.json').read_text());assert validation['status']=='NUMERICAL_PASS'
        render=json.loads((HERE/f'qa/figure{i}_render.json').read_text());assert not render['out_of_bounds_text']
        outputs=[]
        for ext in ('pdf','svg'):
            p=HERE/f'{ext}/figure{i}.{ext}';h=hashlib.sha256(p.read_bytes()).hexdigest()
            outputs.append(dict(path=str(p.relative_to(HERE)),sha256=h));hashes.append((h,str(p.relative_to(HERE))))
        item=dict(figure=i,source_commit=SHA,status='PUBLICATION-CANDIDATE',**spec,
            extraction_script='scripts/extract.py',plot_script=f'scripts/plot.py:figure{i}',
            tested_insertion_width_in=render['width_in'],height_in=render['height_in'],
            grayscale_qa='PASS; qa/VISUAL_QA.md',numerical_qa=validation,outputs=outputs)
        allfig.append(item)
        lines += [f'## Figure {i}','',f"**Question:** {spec['question']}",'',f"**Manuscript claim:** {spec['claim']}",'',
            f"**Evidence class:** {spec['evidence']}",'',f"**Correctness:** {spec['correctness']}",'',
            f"**Estimator / CI:** {spec['estimator']}",'',f"**Caveats:** {spec['caveats']}",'',
            f"**Extraction / rendering:** `scripts/extract.py`; `scripts/plot.py:figure{i}`. Numerical pass: `qa/figure{i}_validation.json`.",'',
            f"**Insertion test:** {render['width_in']:.2f} × {render['height_in']:.2f} in. Color and grayscale PASS; see `qa/VISUAL_QA.md`.",'','### Source files','']
        for src in spec['sources']:
            assert src in lockmap,src
            lines.append(f'- [`{src}`](https://github.com/leecdiang/HeteroSpec/blob/{SHA}/{src})')
        lines+=['','### Plotted values','']
        if not spec['tables']:lines+=['No measured numeric values; symbolic accounting and gate semantics only.','']
        for fn in spec['tables']:
            rows=list(csv.DictReader((HERE/'data'/fn).read_text().splitlines()))
            cols={'figure2_micro_cells.csv':['path','context','pp1_ms','pp2_ms','v2_micro','repetitions','status'],
                'figure3_workloads.csv':['workload','speedup','ci_low','ci_high','prompts','pairs','exact_pairs'],
                'figure4_isolated.csv':['device','context','tokens_s','ci_low','ci_high'],
                'figure4_realized.csv':['device','total_s','draft_s','target_s','residual_s','draft_pct','target_pct','residual_pct','headline_speedup','aggregate_speedup'],
                'figure5_regimes.csv':['case','mechanism','admissibility','profitability','exact','evidence_class']}[fn]
            lines += [f'Full precision and references: [`data/{fn}`](data/{fn}).','',table_text(rows,cols),'']
        lines+=['### Final outputs and SHA256','']
        for o in outputs:lines.append(f"- [{o['path']}]({o['path']}): `{o['sha256']}`")
        lines+=['']
    (HERE/'FIGURE_MANIFEST.md').write_text('\n'.join(lines)+'\n')
    (HERE/'data/figure_manifest.json').write_text(json.dumps(allfig,indent=2)+'\n')
    (HERE/'SHA256SUMS').write_text(''.join(f'{h}  {p}\n' for h,p in hashes))
    print('Manifest built: all five figures, source references, plotted values, estimator/evidence/correctness/caveats, widths, QA, 10 final hashes.')

if __name__=='__main__':main()
