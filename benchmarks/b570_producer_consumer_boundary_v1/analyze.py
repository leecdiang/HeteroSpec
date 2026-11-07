"""Re-audit native evidence, then emit the complete fixed-denominator matrix."""
import argparse
import csv
from pathlib import Path
import work_package as wp

def main():
    ap=argparse.ArgumentParser()
    for n in ['plan','records','payload-root','reference-root','out']:ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    plan=wp.read(a.plan);records=wp.load_records(a.records)
    control=wp.audit_controls(plan,records,a.reference_root,a.payload_root)
    audit=wp.audit_records(plan,records,a.payload_root,control)
    wp.write_new(a.out/'CONTROL_AUDIT.json',control);wp.write_new(a.out/'CPU_AUDIT.json',audit)
    rows={r['slot_id']:r for r in records};errors={e['slot_id'] for e in audit['errors']}
    def usable(slot):
        return slot and slot['slot_id'] in rows and rows[slot['slot_id']]['status'] in wp.COMPLETE and slot['slot_id'] not in errors
    matrix=[]
    for index in range(8):
        subset=[s for s in plan['slots'] if s['stage']=='B1' and s['input_index']==index]
        def find(producer,consumer,route,observer):
            return next((s for s in subset if (s['producer'],s['consumer'],s['route'],s['observer'])==(producer,consumer,route,observer)),None)
        rslot=find('P1','C1','strict_reference','off')
        p1=find('P1','C1','natural','heavy');p4=find('P4T','C1','natural','heavy')
        state_equal=wp.boundary_signature(rows[p1['slot_id']])==wp.boundary_signature(rows[p4['slot_id']]) if usable(p1) and usable(p4) else None
        reference_qualified=(rows[p1['slot_id']]['endpoint']==rows[rslot['slot_id']]['endpoint']) if usable(p1) and usable(rslot) else None
        for producer in ['P1','P4T']:
            donor=find(producer,'C1','natural','heavy');sham=find(producer,'C1','resumed','heavy')
            for consumer in ['C1','PQ','QB']:
                slot=donor if consumer=='C1' else find(producer,consumer,'resumed','heavy')
                row=rows.get(slot['slot_id'],{})
                qualified=audit['b0_qualified'] and usable(slot) and usable(donor) and usable(sham)
                matrix.append(dict(input_index=index,input_id=slot['input_id'],producer=producer,consumer=consumer,
                    status=row.get('status','MISSING'),contract_qualified=bool(qualified),
                    strict_reference_equal=(row['endpoint']==rows[rslot['slot_id']]['endpoint']) if qualified and usable(rslot) else None,
                    producer_conditioned_equal=(row['endpoint']==rows[donor['slot_id']]['endpoint']) if qualified else None,
                    p1_reference_qualified=reference_qualified,producer_boundary_equal=state_equal,
                    length=row.get('endpoint',{}).get('length'),stop_reason=row.get('endpoint',{}).get('stop_reason'),
                    scope=plan['claim_scope'],performance_eligible=False))
    wp.write_new(a.out/'MATRIX.json',matrix)
    with (a.out/'MATRIX.csv').open('x',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(matrix[0]));writer.writeheader();writer.writerows(matrix)
    wp.write_new(a.out/'SUMMARY.json',dict(status=audit['status'],b0_qualified=audit['b0_qualified'],counts=audit['counts'],
        expected_inputs=8,expected_scientific_cells=48,qualified_scientific_cells=sum(r['contract_qualified'] for r in matrix),
        source_records_sha256=wp.sha_file(a.records),plan_sha256=wp.digest(plan),
        errors=audit['errors'],claim_scope=plan['claim_scope'],performance_claims=False))
    print(audit['status'],'B0',audit['b0_qualified'],'qualified cells',sum(r['contract_qualified'] for r in matrix))

if __name__=='__main__':main()
