#!/usr/bin/env python3
"""Author-package consistency checks. NOT an independent audit of native raw archives."""
from __future__ import annotations
import csv,json,math,re
from pathlib import Path

def main() -> None:
    root=Path(__file__).resolve().parents[1]; tests=[]
    def check(name: str, condition: bool) -> None:
        tests.append({'check':name,'pass':bool(condition)})
        if not condition: raise AssertionError(name)
    rows=list(csv.DictReader((root/'data/rtx_repair_cost.csv').open()))
    allregs=json.loads((root/'data/task_regressions.json').read_text())
    table={(r['family'],r['comparison']):r for r in rows}
    pairs={'M_PQ/M_QB','C_PQ/C_QB','M_GS/M_QB','C_GS/C_QB','M_QB/C_QB','R/M_QB','R/C_QB'}
    families={'Qwen3','SmolLM2','Llama'}
    check('21_unique_reported_repair_comparisons',len(rows)==len(table)==21)
    check('complete_3_by_7_grid',set(table)=={(f,p) for f in families for p in pairs})
    for r in rows:
        name=r['family']+'/'+r['comparison']; value=float(r['ratio']); n=int(r['tasks']); k=int(r['regressed_tasks'])
        check(name+'_positive_finite_ratio',math.isfinite(value) and value>0)
        check(name+'_qualified_finite_panel',r['qualified']=='True' and n==12 and 0<=k<=n)
        rr=allregs['regressions'][r['family']][r['comparison']]
        check(name+'_regression_names_and_denominator',len(rr)==k and len(set(rr))==k and set(rr)<=set(allregs['panel']))
    for f in families:
        t=lambda p:float(table[f,p]['ratio'])
        check(f+'_rounded_ratio_identity',abs(t('R/M_QB')*t('M_QB/C_QB')-t('R/C_QB'))<3e-6)
        check(f+'_all_repair_aggregate_ratios_above_parity',all(t(p)>1 for p in list(pairs) if p.startswith(('M_PQ','C_PQ','M_GS','C_GS'))))
    extract=json.loads((root/'data/rtx_repair_report_extract.json').read_text())
    source_rows=extract['comparisons']
    check('report_extract_has_pinned_source',extract['source_blob_sha']=='4d77a2743a8521fb9be130bbc3061c87902a4cd4' and '3235d44c26edd92db33e574094c26af8e29d2452' in extract['source_url'])
    check('report_extract_complete_21_grid',len(source_rows)==21 and {(r['family'],r['pair']) for r in source_rows}==set(table))
    session_table={(r['family'],r['comparison']):r for r in csv.DictReader((root/'data/rtx_repair_sessions.csv').open())}
    check('six_PQ_QB_session_pairs',len(session_table)==6 and set(session_table)=={(f,p) for f in families for p in ('M_PQ/M_QB','C_PQ/C_QB')})
    for r in source_rows:
        name=r['family']+'/'+r['pair']; effects=r['task_effects']
        check(name+'_report_task_medians_complete',r['qualified'] and len(effects)==12 and len({e['task'] for e in effects})==12 and all(len(e[k])==2 and all(math.isfinite(v) and v>0 for v in e[k]) for e in effects for k in ('left_session_median_ms','right_session_median_ms')))
        sessions=[math.exp(sum(math.log(e['left_session_median_ms'][s]/e['right_session_median_ms'][s]) for e in effects)/len(effects)) for s in (0,1)]
        for si,value in enumerate(sessions):
            check(name+f'_session_{si}_recomputed_from_task_medians',abs(value-r['session_ratios'][si])<1e-12)
        aggregate=math.sqrt(sessions[0]*sessions[1])
        check(name+'_aggregate_recomputed_from_report_medians',abs(aggregate-r['cost_ratio'])<1e-12 and abs(aggregate-float(table[r['family'],r['pair']]['ratio']))<=5e-7)
        key=(r['family'],r['pair'])
        if key in session_table:
            sr=session_table[key]
            check(name+'_session_table_rounding',all(abs(sessions[i]-float(sr[k]))<=5e-7 for i,k in enumerate(('first_session','second_session'))))
    for f in ('Qwen3','Llama'):
        r=session_table[f,'M_PQ/M_QB']
        check(f+'_target_only_session_reversal',float(r['first_session'])<1<float(r['second_session']))
    check('all_speculative_PQ_QB_sessions_favor_QB',all(float(session_table[f,'C_PQ/C_QB'][s])>1 for f in families for s in ('first_session','second_session')))
    check('SmolLM2_increment_negative',float(table['SmolLM2','M_QB/C_QB']['ratio'])<1)
    check('Qwen_Llama_increment_positive',all(float(table[f,'M_QB/C_QB']['ratio'])>1 for f in ['Qwen3','Llama']))
    check('formal_repair_count_2016',3*7*12*2*4==2016)
    check('confirmation_count_3600',3*5*24*2*5==3600)
    check('CUDA_replay_calls_216',3*4*2*3*3==216)
    check('B570_final_whole_count_133',21+38+18+16+40==133)
    check('B570_cross_count_40',2*4*3+2*4*2==40)
    check('B570_shams_16',4*2*2==16)
    check('B570_qualified_plus_failed_40',32+8==40)
    history=list(csv.DictReader((root/'data/historical_disposition.csv').open()))
    check('all_28_legacy_groups_have_unique_destinations',{r['legacy_id'] for r in history}=={f'E{i:02}' for i in range(1,29)} and len(history)==28 and all(r['new_destination'] for r in history))
    bib=(root/'references.bib').read_text()
    bibkeys=set(re.findall(r'@\w+\{([^,]+),',bib))
    text='\n'.join(p.read_text() for folder in ('sections','supplement') for p in (root/folder).glob('*.tex'))
    cites={key.strip() for group in re.findall(r'\\cite(?:\[[^]]*\])?\{([^}]+)\}',text) for key in group.split(',')}
    check('all_citations_resolve_in_bib',cites<=bibkeys)
    check('no_whitespace_in_citation_keys',all(not re.search(r'\s',k) for k in cites))
    check('five_vector_figures_present',all((root/'figures'/f'{s}.tex').exists() for s in ['design','numeric','cost','partition','state']))
    # Presence checks are editorial reminders, not semantic validation of claims.
    # See provenance/REVISION_CLAIM_REVIEW_20261014.txt for manual scope review.
    check('kernel_schedule_coverage_disclosed','Exact Vulkan shader' in text and 'kernel scheduling was unavailable' in text)
    check('driver_freeze_limitation_preserved','after the P1A/P1B' in text and 'driver' in text)
    check('failed_scale_controls_preserved','eight scale/MUL' in text and 'excluded' in text)
    check('initial_logits_negative_control_preserved','token1271' in text or 'token 1271' in text)
    check('stock_reference_failure_preserved','original stock gate' in text and '0.727927' in text)
    check('no_new_GPU_execution_claim',json.loads((root/'data/evidence_scope.json').read_text())['new_GPU_runs']==0)
    report={'status':'PASS_REPORTED_VALUE_AND_MANUSCRIPT_CONSISTENCY','checks':len(tests),'tests':tests,'scope':'Checks authored reported-value tables, independently recomputes 21 aggregate and 42 session ratios from pinned report task/session medians, and checks count arithmetic and manuscript limits. Does NOT rerun native raw/CAS audits or any GPU model.','GPU_runs':0}
    (root/'provenance/REPORTED_DATA_CHECKS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(tests)} reported-value/manuscript consistency checks passed; no GPU or raw-archive audit performed.')
if __name__=='__main__': main()
