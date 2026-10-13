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
    check('no_unqualified_kernel_schedule_theorem','not a' in text and 'Exact Vulkan shader' in text and 'kernel scheduling was unavailable' in text)
    check('driver_freeze_limitation_preserved','after the P1A/P1B' in text and 'not fully compliant' in text)
    check('failed_scale_controls_preserved','eight scale/MUL' in text and 'excluded' in text)
    check('initial_logits_negative_control_preserved','token1271' in text or 'token 1271' in text)
    check('stock_reference_failure_preserved','original stock gate' in text and 'failed' in text)
    check('no_new_GPU_execution_claim',json.loads((root/'data/evidence_scope.json').read_text())['new_GPU_runs']==0)
    report={'status':'PASS_REPORTED_VALUE_AND_MANUSCRIPT_CONSISTENCY','checks':len(tests),'tests':tests,'scope':'Checks authored reported-value tables, count arithmetic, rounded ratio identities and explicit manuscript limits. Does NOT rerun native raw/CAS audits or any GPU model.','GPU_runs':0}
    (root/'provenance/REPORTED_DATA_CHECKS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(tests)} reported-value/manuscript consistency checks passed; no GPU or raw-archive audit performed.')
if __name__=='__main__': main()
