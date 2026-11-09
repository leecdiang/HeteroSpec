// Recompute diagnosis and complete recorded costs from exported native records.
// Node built-ins only; no model, CUDA or native worker is executed.
const fs=require('fs'),path=require('path'),zlib=require('zlib'),crypto=require('crypto');
const [bundle,out]=process.argv.slice(2);if(!bundle||!out)throw Error('Usage: node analyze_saved.cjs BUNDLE_DIR FRESH_OUT');
fs.mkdirSync(out);const read=n=>JSON.parse(fs.readFileSync(path.join(bundle,n)));const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=read('BUNDLE.json'),bytes=fs.readFileSync(path.join(bundle,manifest.file));if(bytes.length!==manifest.bytes||hash(bytes)!==manifest.sha256)throw Error('Bundle identity');
const index=new Map(read('TEXT_INDEX.json').files.map(x=>[x.path,x])),records=new Map();
for(const line of zlib.gunzipSync(bytes).toString().trimEnd().split('\n')){const x=JSON.parse(line),b=Buffer.from(x.text),m=index.get(x.path);if(!m||b.length!==m.public_bytes||hash(b)!==m.public_sha256||records.has(x.path))throw Error('Text identity');records.set(x.path,x.text);}
if(records.size!==index.size)throw Error('Record completeness');const json=n=>JSON.parse(records.get(n));
const prefix='pr210-stage-b-20261109-05',result=json(prefix+'/RESULTS.json'),qualification=json(prefix+'/QUALIFIED.json'),costs=read('COSTS.json');
if(!qualification.passed||qualification.cells.length!==32)throw Error('Qualification incomplete');
const paired=[];for(const core of ['loop4','packed'])for(const position of [248,252])for(const round of [0,1]){
 const cells=result.rows.filter(x=>x.kind==='measurement'&&x.core===core&&x.position===position&&x.round===round);if(cells.length!==2)throw Error('Missing pair');
 const a=cells.find(x=>x.execution==='q4pair'),b=cells.find(x=>x.execution==='q8');
 for(const x of cells){const raw=json(prefix+'/runs/'+x.worker+'/native/'+x.name+'/receipt.json');for(const [k,v]of Object.entries(raw))if(JSON.stringify(x[k])!==JSON.stringify(v))throw Error('Receipt/table identity');}
 paired.push({core,position,round,request_order:round===0?['q4pair','q8']:['q8','q4pair'],prior_cell_primer_in_this_process:round===0,
  q4pair_s:a.operation_s,q8_s:b.operation_s,q8_over_q4pair:b.operation_s/a.operation_s,
  q4pair_verify_s:a.phase_seconds.VERIFY,q8_verify_s:b.phase_seconds.VERIFY,
  q4pair_output_copy_s:a.output_copy_s,q8_output_copy_s:b.output_copy_s,
  q4pair_graphs:[a.graph_built,a.graph_reused],q8_graphs:[b.graph_built,b.graph_reused]});
}
const workers=costs.Stage_B_worker_records.map(w=>{const base=w.epoch+'/runs/'+w.name,host=json(base+'/HOST.json'),native=json(base+'/native/result.json');
 return {...w,native_worker_wall_s:host.worker_wall_s,host_wrapper_wall_s:host.wrapper_wall_s,native_setup_s:native.setup_s??null,group:w.core==='reference'?'reference':w.name.startsWith('timing-')?'timing':'qualification'};});
const sum=(xs,f)=>xs.reduce((s,x)=>s+(x[f]||0),0),groups={};for(const group of ['reference','qualification','timing']){const xs=workers.filter(x=>x.group===group);groups[group]={processes:xs.length,adapter_inclusive_wall_s:sum(xs,'wall_s'),native_worker_wall_s:sum(xs,'native_worker_wall_s'),host_wrapper_wall_s:sum(xs,'host_wrapper_wall_s')};}
const physical={reference_rows:0,qualification_rows:0,timing_rows:0,qualification_operations:0,timing_operations:0};
for(const w of workers){const base=w.epoch+'/runs/'+w.name,native=json(base+'/native/result.json');if(w.group==='reference'){
 for(const request of native.requests){const r=json(base+'/native/'+request.record);physical.reference_rows+=r.materialized_tokens;}
 for(const c of native.cases)physical.reference_rows+=c.materialized_tokens;
 }else for(const request of native.requests){const r=json(base+'/native/'+request.record);const rows=Object.entries(r.physical_width_histogram).reduce((s,[k,v])=>s+Number(k)*v,0);physical[w.group+'_rows']+=rows;physical[w.group+'_operations']++;}}
if(workers.length!==27||physical.qualification_operations!==32||physical.timing_operations!==24)throw Error('Complete physical process/operation accounting');
physical.total_target_rows=physical.reference_rows+physical.qualification_rows+physical.timing_rows;physical.draft_rows=0;
const measurement=result.rows.filter(x=>x.kind==='measurement'),primer=result.rows.filter(x=>x.kind==='primer');
const operationCosts=xs=>({operations:xs.length,operation_s:sum(xs,'operation_s'),snapshot_read_s:sum(xs,'snapshot_disk_read_s'),restore_and_frontier_copy_s:sum(xs,'restore_and_frontier_copy_s'),nested_output_copy_s:sum(xs,'output_copy_s'),nested_planning_s:sum(xs,'planning_s')});
const publicResources=read('RESOURCE_CHECKED.json'),samples=publicResources.records.flatMap(x=>x.samples);
const memory={sample_period_s:2,scope:'Selected-device total-minus-free; sampled lower bound, not exact per-process peak',by_group:{}};
for(const group of ['reference','qualification','timing']){const xs=[];for(const w of workers.filter(x=>x.group===group)){const text=records.get(w.epoch+'/runs/'+w.name+'/resources.jsonl');if(text)for(const line of text.trim().split('\n'))if(line)xs.push(JSON.parse(line));}memory.by_group[group]={samples:xs.length,max_sampled_total_minus_free_MiB:Math.max(...xs.map(x=>Number(x.gpu['memory.total'])-Number(x.gpu['memory.free']))),min_sampled_free_MiB:Math.min(...xs.map(x=>Number(x.gpu['memory.free'])))};}
const failures=[];for(const [name,text]of records)if(name.includes('STOPPED-')||name.endsWith('RETROSPECTIVE_PREPARE_FAILURE.json')||name.endsWith('SUPERVISOR_FAILURE.private.json')||name.endsWith('RECORD_ADAPTER_NOT_ADMITTED.json')){try{failures.push({path:name,...JSON.parse(text)});}catch{}}
const diagnosis={schema:'heterospec.pr210.stage-B.diagnosis.v1',status:'STAGE_B_COMPLETE_WITH_STARTUP_ORDER_LIMITATION',qualification_cells:32,measurement_requests:16,primers:8,
 paired_by_round:paired,prespecified_two_round_rollup:result.contrasts,
 actual_dispatch:qualification.cells.map(x=>({core:x.core,origin:x.origin,position:x.position,execution:x.execution,physical_histogram:x.physical_histogram,packed_nodes:x.dispatch.packed_nodes,loop4_nodes:x.dispatch.loop4_nodes,scope:x.dispatch.scope})),
 interpretation:'Round0 has one primer per cell and q4pair then q8. Round1 restarts each block process, has no further primer and runs q8 first. Startup/use state and request order are aliased; the sign reverses. Neither round splitting nor pooled totals identify steady-state physical-width efficiency or a live-service effect.',
 stop_decision:{Stage_C:'NOT_RUN',Stage_D:'NOT_RUN',Stage_E:'NOT_RUN',Q32:'NOT_RUN',candidate_optimization:false,reason:'No cleanly attributed removable hotspot is established by these diagnostics. Preserve the limited old k3 recommendation; no claim that q8 inherently loses or wins. A future matched-warmth/persistent-process diagnostic needs separate registration, not selective repetition here.'},
 worker_cost_groups:groups,actual_physical_work:physical,measurement_costs:operationCosts(measurement),primer_costs:operationCosts(primer),
 sampled_memory:memory,
 budget:{requests:costs.cumulative_requests,ceiling_requests:costs.request_ceiling,remaining_requests:costs.remaining_requests,reserved_rows:costs.cumulative_conservative_rows,ceiling_rows:costs.row_ceiling,remaining_rows:costs.remaining_rows,Stage_B_requests:67,Stage_B_reserved_rows:28695},
 resource_observer:{samples:samples.length,selected_GPU_foreign_process_samples:samples.filter(x=>x.selected_GPU_foreign_processes>0).length,event_samples:samples.filter(x=>x.event_kinds.length>0).length,scope:publicResources.limitations},
 qualification_scope:'All8 vectors and initial/final active KV/frontier for32 equal-work cells. Clean timing checks all8 output hashes and bounds, without online KV export. This is not new live EOG/cap/rollback qualification.',
 failures,raw_capture_files:costs.raw_binary_files,raw_capture_bytes:costs.raw_binary_bytes,
 cost_limitations:'Adapter, host wrapper, native process, setup, restore and operation clocks overlap. Do not add categories into a purported kernel time or service speedup. Total CPU use and GPU energy/kernel time were not independently instrumented.'};
fs.writeFileSync(path.join(out,'DIAGNOSIS.json'),JSON.stringify(diagnosis,null,2)+'\n');
fs.writeFileSync(path.join(out,'ANALYSIS_CHECKED.json'),JSON.stringify({passed:true,text_records_verified:records.size,worker_records_reconciled:workers.length,source_bundle_sha256:manifest.sha256,new_native_requests:0,scope:'Saved-record byte/physical/cost/statistic reconciliation only'},null,2)+'\n');
console.log(JSON.stringify({passed:true,groups,physical,budget:diagnosis.budget,resource:diagnosis.resource_observer,measurement:diagnosis.measurement_costs}));
