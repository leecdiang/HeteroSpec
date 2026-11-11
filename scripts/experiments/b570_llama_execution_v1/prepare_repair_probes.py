"""Select actual repaired cycles for common-state and extended-attention controls."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha
import host,design
root=Path(sys.argv[1]).resolve();baseline=root/'reference-q8-epoch-00'
need(read(baseline/'BASELINE_AUDIT.json')['all_reference_equal'],'development before followup')
p=baseline/'units/baseline-candidate/native/baseline/i0/C_QB/heavy.json';r=read(p)
boundary=next(c['cycle'] for c in r['cycles'] if c['base']+4>768)
write(root/'REPAIR_PROBE_SELECTION-00.json',{'source_record_sha256':sha(p),'cycles':[0,boundary],'selection':'cycle0 key768 and first actual verify batch crossing to physical key1024; no output-index division'})
c=read(root/'host-reference-q8-00.json');c['candidate_build']=str(root/'attention-observer-build-01/WORKER_BUILD.json');c['policy']['purpose']='Same numerical repair, observer-only real attention operands and q1/q4 controls'
write(root/'host-attention-00.json',c);host.prepare(root/'host-attention-00.json',root/'attention-epoch-00')
slots=[];x=read(baseline/'DEV.json')[0]
for arm,cycle,trace in [('C_QB',0,True),('C_QB',boundary,True),('C_QB',boundary,False),('C_PQ',0,False),('C_PQ',boundary,False)]:
    label=f'repair-probes-00/{arm}-cycle{cycle}-'+('trace' if trace else 'control')
    s=design.slot(x,arm,'heavy','diagnostic',label);s.update(probe_cycle=cycle,trace=trace,trace_pattern=r'^(hs_qb_(qk|prob|av|final)|kq|kq_soft_max|kqv|kqv_out)-0$');slots.append(s)
write(root/'REPAIR_PROBE_SLOTS-00.json',slots)
c=read(root/'host-reference-q8-00.json');c['reference_q8']=False;c['policy']['purpose']='Ablation: same repaired executable and DLLs, explicit reference projection contract disabled'
write(root/'host-ablation-00.json',c);host.prepare(root/'host-ablation-00.json',root/'ablation-epoch-00')
