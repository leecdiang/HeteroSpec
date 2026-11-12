// Zero GPU saved-receipt cost audit. No component times from other panels.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const root=process.argv[2],out=process.argv[3];assert(root&&out&&!fs.existsSync(out));
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p)));
const groups={},workers=fs.readdirSync(path.join(root,'data/S3/workers')).sort();assert.equal(workers.length,144);
for(const worker of workers){
 const base='data/S3/workers/'+worker,arm=read(base+'/WORKER.json').arm;assert('GBC'.includes(arm));
 groups[arm]??={workers:0,warm_service_s:0,measured:{requests:0,service_s:0,reset_s:0,prefill_s:0,decode_s:0,planning_s:0,owned_host_output_copy_s:0,residual_unpartitioned_s:0},host_caller_s:0,launch_to_exit_observation_s:0,cumulative_native_main_to_measured_ready_s:0,model_load_s:0,pool_setup_s:0};
 const g=groups[arm];g.workers++;const h=read(base+'/HOST.json');assert.equal(h.status,'COMPLETE');const processResult=read(base+'/native/result.json');g.model_load_s+=processResult.model_load_s;g.pool_setup_s+=processResult.pool_setup_s;
 g.host_caller_s+=h.caller_s;g.launch_to_exit_observation_s+=h.launch_to_exit_observation_s;
 for(const role of ['warm','measured']){
  const r=read(base+'/native/'+role+'/receipt.json');assert.equal(r.capture,false);const endpoint=r.S3_service;
  assert(Math.abs(endpoint.reset_s-(endpoint.reset_end_ns-endpoint.start_ns)/1e9)<1e-12);
  assert.equal(endpoint.initial_reset_included,true);assert.equal(endpoint.stop_separate_s,null);
  if(role==='warm'){g.warm_service_s+=endpoint.elapsed_s;continue;}
  const m=g.measured;m.requests++;m.service_s+=endpoint.elapsed_s;m.reset_s+=endpoint.reset_s;m.prefill_s+=r.target_phases.PREFILL??0;m.decode_s+=r.target_phases.ORDINARY??0;m.planning_s+=r.planning_s;m.owned_host_output_copy_s+=r.output_copy_s;
  const rest=endpoint.elapsed_s-endpoint.reset_s-(r.target_phases.PREFILL??0)-(r.target_phases.ORDINARY??0)-r.planning_s-r.output_copy_s;assert(rest>=0);m.residual_unpartitioned_s+=rest;
  g.cumulative_native_main_to_measured_ready_s+=r.phase1_main_to_result_s;
 }
}
const report={status:'SAME_PANEL_RECEIPT_COST_AUDIT_COMPLETE',new_GPU_requests:0,groups,
 primary_scope:'Reset-inclusive resident clean request; warm service distinct from measured service',
 sibling_intervals:['reset_s','prefill_s','decode_s','planning_s','owned_host_output_copy_s'],
 parent_interval:'S3_service',nested_subsets:['first_call_plan_s inside planning_s','backend quantization/kernel/copy/synchronization inside prefill/decode; counters are not durations'],
 unmeasured_residual:'Sampling full finite logits and greedy argmax, commit/EOG/cap, batch/output allocation and setup, physical metadata/counters, final sync gaps and timer overhead are not individually partitioned',
 exclusions:['Model load/context provision occurs before service, with their own recorded timers in native result.json','Terminal full state export and semantic-tape/receipt serialization occur after service','Exact native lifetime is not measured: launch_to_exit_observation_s and exit_observed_monotonic_ns are filled after post-exit module/budget validation, beyond polling','phase1_main_to_result_s for measured is cumulative from process start, including warm request and earlier post-service work'],
 limitations:['No S2 operator-time stack is combined with these service times','Same-panel phase differences are descriptive and do not isolate quantization vs scalar dot vs launch costs','Single warm per fresh process is prescribed, not general steady-state evidence','Host caller totals include warm plus measured plus checks; do not add them to service sums']};
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));
