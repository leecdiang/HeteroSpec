"""Full-error analysis is deferred; every online rejection must remain intact."""
import copy,struct
from pathlib import Path
from common import V,load,save,blob
import analyzer as A

def main():
    p=load(V/'PLAN.json');refs=load(V/'REFERENCE_INDEX.json');count=0;neg=0
    for d in p['descriptors']:
        meta,ref=A.reference_values(d['id'],V/'reference_cas',refs)
        for layout in A.LAYOUTS:
            for repeat in (0,1):
                slot=next(s for s in p['numerical_slots'] if (s['descriptor'],s['layout'],s['repeat'])==(d['id'],layout,repeat))
                hist={s:blob(V/'reference_cas',refs[d['id']]['historical'][layout+'-r'+str(repeat)+'/'+s]) for s in A.STAGES[:-1]} if layout in ('PQ','QB') else None
                values=dict(ref)
                if hist:values.update(hist);values['ordinary']=A.restore(values['AV'],meta)
                if d['q']>1 and layout.startswith('QH'):
                    values['QK']=struct.pack('<f',struct.unpack('<f',values['QK'][:4])[0]+.125)+values['QK'][4:]
                previous=values if repeat else None
                full=A.verify_numeric(slot,meta,values,ref,hist,previous)
                fast=A.verify_numeric(slot,meta,values,ref,hist,previous,True)
                assert full['status']==fast['status'] and full['repeatability']==fast['repeatability']
                assert full['vs_original_MQ']['first_divergence_operator']==fast['vs_original_MQ']['first_divergence_operator']
                bad=dict(values);bad['QK']=struct.pack('<I',0x7fc00001)+values['QK'][4:]
                try:A.verify_numeric(slot,meta,bad,ref,hist,previous,True)
                except AssertionError:neg+=1
                else:raise AssertionError('fast nonfinite accepted')
                count+=1
    save(V/'CPU_FAST_CONTROLS.json',dict(status='PASS',full_vs_online_control_cases=count,nonfinite_rejections=neg,
        complete_bytes_remain_required=True,expensive_max_error_ULP_deferred_to_offline_only=True,fixtures='Real frozen reference bytes and explicitly synthetic finite QH differences; no new CUDA results',GPU_queries=0,graph_computes=0))
    print('PASS240 full/online control parity and240 nonfinite rejections')
if __name__=='__main__':main()
