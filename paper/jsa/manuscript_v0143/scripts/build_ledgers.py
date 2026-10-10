"""Build the v0.14.3 experiment destinations and CSV claim map, CPU only.

Original planning facts and source paths are retained verbatim. Editorial roles
are separate from those facts and do not alter campaign denominators.
"""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]
# The original 28-row planning ledger is preserved, including all negative arms.
DESTINATIONS=[
 ('S1 S6.1/S6.2; preserved historical table/source records','Historical contracts, opposite M4 workloads, unchanged estimator/energy boundaries'),
 ('S1 S6.2/S6.7; historical proxy lookup and threshold JSON','All context cells and favorable eligibility predictions kept separate from integrated costs'),
 ('Main §6.5; S1 S6.6','540 requests, direct-ID gate, policy construction, timer and metadata recovery'),
 ('Main §6.5; S1 S6.6, table label tab:m4_strata','All family estimates, two-action factor/latency distinction and original/secondary streams'),
 ('S1 S6.3','270 runs;60/90 and78/90 strict ID gates versus historical45/90 and60/90 text counts'),
 ('Main §4.5; S1 S2.1','36/36 discovery,72/72 prediction,60/72 reference and all four first divergences'),
 ('Main §4.3; S1 S2.3; preserved historical derived appendix','72 runs,195 immediate events,18 downstream runs/six tasks; later UB128 policy explicit'),
 ('Main §4.5; S1 S2.1','24/36 H1 failure, zero reserved inference and H2 absent in that original study'),
 ('Main §4.5; S1 S2.1','Later completed H2/native and R-only/native72/72; not an online repair'),
 ('S1 S6.3','V1 transport stop, separate completed V2 qualification and independently measured latency arm'),
 ('S1 S6.4','126 valid prefixes, two failures,448 unreached; no complete formal speed/CI'),
 ('Main §6.5; S1 S2.1/S6.4','Prediction closure,51/57 blocked batching,57/57 qualified serial negative cost and host amendment'),
 ('S1 S2.2 (Controlled prefill and continuation interventions)','Prefill plus first-pending/sample/state handoff; four repairs and20 controls'),
 ('Main §4.1; S1 S2.2','/15 repairs,/25 regresses, /304 output changes despite persistent failure'),
 ('Main §4.5; S1 S2.5','171 fresh arrays,strict U2=N1 bridge, no state-equivalence or speed claim'),
 ('Main §4.5; S1 S2.5','114/114 and72/144 acquisition equivalents; abstention and unknown counterfactuals'),
 ('S1 S6.5','Four-probe positive plus expanded failures;300 formal/48 warmup; own FA/UB references'),
 ('Main §4.2/§5.1, Figures1/2; S1 S2.4/S3.1','Natural donor/fork/sham counts, null probes and actual graph/source controls'),
 ('Main §5.1 implementation rationale; S1 S3.3 (Implementation variants and paid-boundary changes)','Serial/per-query/query-batch positives and negatives; strict matched costs kept separate'),
 ('Main §5.2/§5.3, Figure3; S1 S3.2','All16 masks,passing3/7/11/15 and failed extra-generation gate'),
 ('Main §5.4/§6.1/§6.2, tab:rtx_cost and Figures4/5; S1 S4.1, tab:rtx_all, tab:rtx_task_generation, tab:rtx_task_request','384-row qualification,paid R/M/C,seven request regressions,round2 reversal and timer/source audit'),
 ('Main §5.4; S1 S4.2','/229 width failures,/18 outside-panel failure,natural EOS state witness and actual max261'),
 ('Main §6.3; S1 S4.3, table label tab:fixed_ub','Qualified fixed-UB wider draft loses; cohorts and separate capture/cost counts retained'),
 ('Main §6.2; S1 S4.4','Finite serial reset/order check; no concurrency or wider-draft resident qualification'),
 ('Main §5.5; S1 S5.1','1,456 core completed normative closeout; old local positive,unused-input andUB2 failures'),
 ('Main §4.4/§5.5/§6.4, Figure2; S1 S2.4/S5.2/S5.3','Whole-recipe crosses,identical columns,private API implementation and raw/endpoint distinction'),
 ('Main §6.4, table label tab:b570_cost; S1 S5.3/S5.4, tab:b570_qualification and tab:b570_task_cost','119/120,15 vs14 complete pairs,all three timers,suffix costs andold-N1 per-round reversal'),
 ('Main §6.5; S1 S6.7, table label tab:358h_accounting','Actual stateful costs,component accounting,prompt/pooled floors andblocked persistent candidate')
]

DISPOSITION_LABELS = {
 'main-core': '主文核心证据',
 'main-brief-supplement-detail': '主文简述、补充详述',
 'supplement-boundary-history-reproducibility': '补充材料中的边界、历史或复现证据',
}
MAIN_CORE = {7, 14, 18, 20, 21, 22, 23, 26, 27}
MAIN_BRIEF = {3, 4, 6, 8, 9, 12, 15, 16, 19, 24, 25, 28}

# Readable source navigation accompanies the stable PDF section references.
SUPPLEMENT_FILES = {
 1: 'supplement/06_history.tex', 2: 'supplement/06_history.tex',
 3: 'supplement/06_history.tex', 4: 'supplement/06_history.tex',
 5: 'supplement/06_history.tex', 6: 'supplement/02_diagnosis.tex',
 7: 'supplement/02_diagnosis.tex', 8: 'supplement/02_diagnosis.tex',
 9: 'supplement/02_diagnosis.tex', 10: 'supplement/06_history.tex',
 11: 'supplement/06_history.tex', 12: 'supplement/02_diagnosis.tex; supplement/06_history.tex',
 13: 'supplement/02_diagnosis.tex', 14: 'supplement/02_diagnosis.tex',
 15: 'supplement/02_diagnosis.tex', 16: 'supplement/02_diagnosis.tex',
 17: 'supplement/06_history.tex', 18: 'supplement/02_diagnosis.tex; supplement/03_implementation.tex',
 19: 'supplement/03_implementation.tex', 20: 'supplement/03_implementation.tex',
 21: 'supplement/04_rtx_cost.tex', 22: 'supplement/04_rtx_cost.tex',
 23: 'supplement/04_rtx_cost.tex', 24: 'supplement/04_rtx_cost.tex',
 25: 'supplement/05_b570.tex', 26: 'supplement/02_diagnosis.tex; supplement/05_b570.tex',
 27: 'supplement/05_b570.tex', 28: 'supplement/06_history.tex',
}


def main():
    text=(ROOT/'provenance/PLANNING_EVIDENCE_LEDGER.md').read_text()
    rr=[[c.strip() for c in line.split('|')[1:-1]] for line in text.splitlines() if line.startswith('|')][2:]
    assert len(rr)==len(DESTINATIONS)==28
    entries=[]
    for i,(r,(dest,role)) in enumerate(zip(rr,DESTINATIONS),1):
        assert len(r)==4
        disposition='main-core' if i in MAIN_CORE else 'main-brief-supplement-detail' if i in MAIN_BRIEF else 'supplement-boundary-history-reproducibility'
        entries.append(dict(id=f'E{i:02d}',original_group=r[0],original_key_facts=r[1],
                            original_destination=r[2],original_sources=r[3],v0141_destination=dest,
                            v0141_role=role,v0141_disposition=disposition,
                            v0141_disposition_label=DISPOSITION_LABELS[disposition],
                            supplementary_source=SUPPLEMENT_FILES[i],original_evidence_preserved=True))
    (ROOT/'EXPERIMENT_DESTINATIONS.json').write_text(json.dumps(dict(revision='v0.14.3',
        manuscript_baseline_commit='f7d2a863265e6d619d3582d702e57cec1cfa9be2',
        manuscript_baseline_pr=73,
        ledger_schema_note='v0141-prefixed entry fields are retained for checker compatibility; locations apply to v0.14.3',
        planning_baseline_commit='00ea8f7c3a49b900bf5f21a95876e9a3a6dd610f',
        original_groups=28,covered_groups=len(entries),unassigned_groups=0,entries=entries),ensure_ascii=False,indent=2)+'\n')
    out=['# Complete experiment destinations, v0.14.3','',
         'All **28** original planning-ledger groups are assigned below. The three explicit editorial dispositions state each group\'s role in this revision. The full JSON retains original facts and actual source paths, while the source-navigation column identifies the detailed supplement. S1 S2.1 means supplementary section S2, subsection 1; TeX table labels remain stable if pagination changes. No contract, task panel or missing result is pooled or repaired across campaigns.','',
         '| ID | Original experiment group | v0.14.3 disposition | New destination | Preserved evidence and role | Supplement source |','|---|---|---|---|---|---|']
    for e in entries:out.append('| '+ ' | '.join(e[k] for k in ['id','original_group','v0141_disposition_label','v0141_destination','v0141_role','supplementary_source'])+' |')
    (ROOT/'EXPERIMENT_DESTINATIONS.md').write_text('\n'.join(out)+'\n')
    claims=[[c.strip() for c in line.split('|')[1:-1]] for line in (ROOT/'CLAIM_EVIDENCE.md').read_text().splitlines() if line.startswith('|')][2:]
    assert len(claims)==26
    with (ROOT/'CLAIM_EVIDENCE.csv').open('w',newline='') as f:
        assert all(len(c)==7 for c in claims)
        writer=csv.writer(f);writer.writerow(['claim_id','claim_and_location','actual_evidence','revision_check_scope','scientific_boundary','v0141_disposition','detailed_destination']);writer.writerows(claims)
    print(json.dumps(dict(experiment_groups=28,covered=28,claims=26,missing=0)))


if __name__=='__main__':main()
