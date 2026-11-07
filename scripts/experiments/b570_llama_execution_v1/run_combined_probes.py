"""Final same-binary q1/q4 controls selected from actual repaired cycles."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha
import host,design
from audit_probe import run as audit

root=Path(sys.argv[1]);epoch=Path(sys.argv[2]);need(read(epoch/'BASELINE_AUDIT.json')['all_reference_equal'],'complete repaired development')
p=epoch/'units/baseline-candidate/native/baseline/i0/C_QB/heavy.json';r=read(p);cycle=next(c['cycle'] for c in r['cycles'] if c['base']<768 and c['base']+4>768)
write(root/'COMBINED_PROBE_SELECTION-00.json',{'source_record_sha256':sha(p),'actual_cycle':cycle,'selection':'actual repaired verification crossing physical key768, no output-index arithmetic'})
slots=[];x=read(epoch/'DEV.json')[0]
for arm,c,trace in [('C_QB',0,False),('C_QB',cycle,False),('C_QB',cycle,True),('C_PQ',0,False),('C_PQ',cycle,False)]:
    label=f'combined-probes-00/{arm}-cycle{c}-'+('trace' if trace else 'control');s=design.slot(x,arm,'heavy','diagnostic',label);s.update(probe_cycle=c,trace=trace,trace_pattern=r'^(l_out|hs_prefix_attention|kqv_out)-0$');slots.append(s)
write(root/'COMBINED_PROBE_SLOTS-00.json',slots);host.execute(epoch,'combined-probes-00',slots);out=root/'COMBINED_PROBE_AUDIT-00.json';audit(epoch,'combined-probes-00',out,epoch)
proof=read(out);need(all(row['bitwise_equal'] for result in proof['results'] for row in result['rows']),'remaining same-state scalar/vector difference')
print('ALL_COMBINED_SAME_STATE_ROWS_BITWISE_EQUAL',flush=True)
