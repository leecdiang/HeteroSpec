"""Build the complete experiment destinations and CSV claim map, CPU only."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]
# The original 28-row planning ledger is preserved, including all negative arms.
DESTINATIONS=[
 ('S1 S6.1/S6.2; preserved historical table/source records','Historical contracts, opposite M4 workloads, unchanged estimator/energy boundaries'),
 ('S1 S6.2/S6.7; historical proxy lookup and threshold JSON','All context cells and favorable eligibility predictions kept separate from integrated costs'),
 ('Main §6.5; S1 S6.6','540 requests, direct-ID gate, policy construction, timer and metadata recovery'),
 ('Main §6.5; S1 S6.6, Table S11','All family estimates, two-action factor/latency distinction and original/secondary streams'),
 ('S1 S6.3','270 runs;60/90 and78/90 strict ID gates versus historical45/90 and60/90 text counts'),
 ('Main §4.5; S1 S2.1','36/36 discovery,72/72 prediction,60/72 reference and all four first divergences'),
 ('Main §4.3; S1 S2.3; preserved historical derived appendix','72 runs,195 immediate events,18 downstream runs/six tasks; later UB128 policy explicit'),
 ('Main §4.5; S1 S2.1','24/36 H1 failure, zero reserved inference and H2 absent in that original study'),
 ('Main §4.5; S1 S2.1','Later completed H2/native and R-only/native72/72; not an online repair'),
 ('S1 S6.3','V1 transport stop, separate completed V2 qualification and independently measured latency arm'),
 ('S1 S6.4','126 valid prefixes, two failures,448 unreached; no complete formal speed/CI'),
 ('Main §6.5; S1 S2.1/S6.4','Prediction closure,51/57 blocked batching,57/57 qualified serial negative cost and host amendment'),
 ('S1 S2.2; Main §4 context','Prefill plus first-pending/sample/state handoff; four repairs and20 controls'),
 ('Main §4.1; S1 S2.2','/15 repairs,/25 regresses, /304 output changes despite persistent failure'),
 ('Main §4.5; S1 S2.5','171 fresh arrays,strict U2=N1 bridge, no state-equivalence or speed claim'),
 ('Main §4.5; S1 S2.5','114/114 and72/144 acquisition equivalents; abstention and unknown counterfactuals'),
 ('S1 S6.5','Four-probe positive plus expanded failures;300 formal/48 warmup; own FA/UB references'),
 ('Main §4.2/§5.1, Figures1/2; S1 S2.4/S3.1','Natural donor/fork/sham counts, null probes and actual graph/source controls'),
 ('S1 S3.3, Table S2; Main implementation rationale','Serial/per-query/query-batch positives and negatives; strict matched costs kept separate'),
 ('Main §5.2/§5.3, Figure3; S1 S3.2','All16 masks,passing3/7/11/15 and failed extra-generation gate'),
 ('Main §5.4/§6.1/§6.2, Tables3/Figures4/5; S1 S4.1','384-row qualification,paid R/M/C,seven request regressions,round2 reversal and timer/source audit'),
 ('Main §5.4; S1 S4.2','/229 width failures,/18 outside-panel failure,natural EOS state witness and actual max261'),
 ('Main §6.3; S1 S4.3, Table S6','Qualified fixed-UB wider draft loses; cohorts and separate capture/cost counts retained'),
 ('Main §6.2; S1 S4.4','Finite serial reset/order check; no concurrency or wider-draft resident qualification'),
 ('Main §5.5; S1 S5.1','1,456 core completed normative closeout; old local positive,unused-input andUB2 failures'),
 ('Main §4.4/§5.5/§6.4, Figure2; S1 S2.4/S5.2/S5.3','Whole-recipe crosses,identical columns,private API implementation and raw/endpoint distinction'),
 ('Main §6.4, Table4; S1 S5.4, Table S8','119/120,15 vs14 complete pairs,all three timers,suffix costs andold-N1 per-round reversal'),
 ('Main §6.5; S1 S6.7, Table S12','Actual stateful costs,component accounting,prompt/pooled floors andblocked persistent candidate')
]


def main():
    text=(ROOT/'provenance/PLANNING_EVIDENCE_LEDGER.md').read_text()
    rr=[[c.strip() for c in line.split('|')[1:-1]] for line in text.splitlines() if line.startswith('|')][2:]
    assert len(rr)==len(DESTINATIONS)==28
    entries=[]
    for i,(r,(dest,role)) in enumerate(zip(rr,DESTINATIONS),1):
        assert len(r)==4
        entries.append(dict(id=f'E{i:02d}',original_group=r[0],original_key_facts=r[1],
                            original_destination=r[2],original_sources=r[3],v014_destination=dest,
                            v014_role=role,original_evidence_preserved=True))
    (ROOT/'EXPERIMENT_DESTINATIONS.json').write_text(json.dumps(dict(baseline_commit='00ea8f7c3a49b900bf5f21a95876e9a3a6dd610f',
        original_groups=28,covered_groups=len(entries),unassigned_groups=0,entries=entries),ensure_ascii=False,indent=2)+'\n')
    out=['# Complete experiment destinations, v0.14.0','',
         'All **28** original planning-ledger groups are assigned below. The full JSON retains the original facts, destinations and actual source paths. S1 labels use section names/numbers from the supplementary PDF; source records remain available even when a result is historical. No contract or task panel is pooled across campaigns.','',
         '| ID | Original experiment group | New destination | Preserved evidence and role |','|---|---|---|---|']
    for e in entries:out.append('| '+ ' | '.join(e[k] for k in ['id','original_group','v014_destination','v014_role'])+' |')
    (ROOT/'EXPERIMENT_DESTINATIONS.md').write_text('\n'.join(out)+'\n')
    claims=[[c.strip() for c in line.split('|')[1:-1]] for line in (ROOT/'CLAIM_EVIDENCE.md').read_text().splitlines() if line.startswith('|')][2:]
    assert len(claims)==26
    with (ROOT/'CLAIM_EVIDENCE.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['claim_id','claim_and_location','actual_evidence','revision_check_scope','scientific_boundary']);writer.writerows(claims)
    print(json.dumps(dict(experiment_groups=28,covered=28,claims=26,missing=0)))


if __name__=='__main__':main()
