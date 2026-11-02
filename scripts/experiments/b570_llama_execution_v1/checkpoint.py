"""Publish compact progress evidence while retaining immutable raw attempts."""
from pathlib import Path
import json,shutil,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,sha,utc
import budget
root=Path(sys.argv[1]);repo=Path(sys.argv[2]);out=repo/'benchmarks/b570_llama_companion_v1/host_execution'
names=['TRACE_CONTROL_AUDIT-00.json','LAYER_TRACE-cycle0.json','LAYER_TRACE-cycle9.json','OPERATOR_TRACE_CONTROL-00.json','OPERATOR_FRONTIER-00.json','Q8_REPLAY_AUDIT-00.json','Q8_REPLAY_DISPATCH_AUDIT-00.json','DISPATCH_NATIVE_CONTROL-00.json','Q8_INTERVENTION_AUDIT-00.json']
for name in names:shutil.copyfile(root/name,out/name)
status={'status':'NATIVE_DEVELOPMENT_IN_PROGRESS','utc':utc(),'local_work_root':str(root.resolve()),'source_pr':161,'result_pr':163,'historical_requests_audited':54,'historical_vectors_audited':5916,'completed_baseline_requests':36,'completed_probe_trace_requests':7,'original_own_path_operator_calls':15,'dispatch_observer_operator_calls':15,'activation_intervention_operator_calls':15,'controlled_first_projection_difference':'Layer0 Qcur MUL_MAT, before RoPE; actual q1 F32 activation vs q4 Q8_1 activation dispatch','intervention_result':'All15 calls pass; q4 Q/K/V outputs equal original q1 concatenation; no model repair claim yet','structural_candidate':'candidate-reference-q8-01; explicit F32 contract; compiled, full-model qualification pending','ledger':budget.totals(root/'research/LEDGER.jsonl'),'repair_qualified':False,'confirmation_run':False,'remote_new_evidence_delivery_complete':False,'rtx_pr160_modified':False}
(out/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
if not (root/'ENGINEERING-02.json').exists():
    write(root/'ENGINEERING-02.json',{'utc':utc(),'events':[{'kind':'source-extension encoding','attempt':'candidate-reference-q8-00','error':'Windows GBK decoding of UTF-8 source failed before build/forward','recovery':'Explicit UTF-8; fresh candidate-reference-q8-01; failed extension and staged source retained','new_model_requests':0},{'kind':'old Qwen zero-forward capacity','attempt':'qwen-baseline-00/admission','error':'512MiB device reserve with original all-GPU Qwen contexts','recovery':'Prospectively registered separate128MiB Qwen validation reserve; both Q8 models and original placement retained; same-build zero-forward admission passes with minimum429780992 bytes','Llama_reserve_unchanged':True,'new_model_requests':0},{'kind':'Git automatic maintenance','process':33236,'recovery':'Stopped only identified automatic pack subprocess; all subsequent Git mutations disable automatic maintenance','scientific_artifacts_deleted':False}]})
shutil.copyfile(root/'ENGINEERING-02.json',out/'ENGINEERING-02.json')
