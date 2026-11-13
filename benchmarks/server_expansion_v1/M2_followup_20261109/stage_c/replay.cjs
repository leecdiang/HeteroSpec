// Model-free archive replay. Full numerical state requalification is not claimed.
const fs=require('fs'),path=require('path'),zlib=require('zlib'),crypto=require('crypto'),{isDeepStrictEqual:eq}=require('util');
const [bundle,out]=process.argv.slice(2);if(!bundle||!out)throw Error('Usage: node replay.cjs BUNDLE FRESH_OUT');fs.mkdirSync(out);
const read=n=>JSON.parse(fs.readFileSync(path.join(bundle,n))),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=read('BUNDLE.json'),b=fs.readFileSync(path.join(bundle,manifest.file));if(b.length!==manifest.bytes||hash(b)!==manifest.sha256)throw Error('Bundle bytes');
const index=new Map(read('TEXT_INDEX.json').files.map(x=>[x.path,x])),records=new Map();
for(const line of zlib.gunzipSync(b).toString().trimEnd().split('\n')){const x=JSON.parse(line),bytes=Buffer.from(x.text),m=index.get(x.path);if(!m||records.has(x.path)||bytes.length!==m.public_bytes||hash(bytes)!==m.public_sha256)throw Error('Text bytes');records.set(x.path,x.text);}
if(records.size!==index.size||records.size!==manifest.records)throw Error('Text count');const json=n=>JSON.parse(records.get(n));
const plan=json('work/PLAN.private.json'),result=json('work/RESULTS.json'),complete=json('work/NATIVE_COMPLETE.json'),bindings=json('work/BINDINGS_PUBLIC.json'),admission=json('work/ADMISSION_PUBLIC.json');
if(!complete.passed||plan.length!==8||result.observations.length!==16||result.workers.length!==8||admission.requests.total!==16)throw Error('Incomplete profile');
for(const [name,h]of Object.entries(json('work/SOURCE_FREEZE.private.json')))if(index.get('source/'+name).raw_sha256!==h)throw Error('Executed source binding');
const ledger=records.get('work/ledger.jsonl').trim().split('\n').map(x=>JSON.parse(x)),reservations=ledger.filter(x=>x.event==='RESERVE');
if(reservations.length!==8||reservations.reduce((s,x)=>s+x.requests,0)!==16||reservations.reduce((s,x)=>s+x.rows,0)!==4128||ledger.filter(x=>x.event==='FAILED').length)throw Error('Reservation reconciliation');
const summary=[],phase=[];let nativeRows=0;const processCosts={processes:8,adapter_inclusive_s:0,native_worker_wall_s:0,host_wrapper_wall_s:0},memory=[];
for(const cell of plan){
 const base='work/runs/'+cell.id,jobName='work/jobs/'+path.posix.basename(cell.job),job=json(jobName),native=json(base+'/native/result.json'),launch=json(base+'/launch.json'),host=json(base+'/HOST.json');
 if(index.get(jobName).raw_sha256!==cell.job_sha256||launch.job_sha256!==cell.job_sha256||launch.build_sha256!==bindings.cores[cell.core].build_sha256||native.projection!==cell.core||host.status!=='COMPLETE'||native.status!=='COMPLETE'||native.draft_calls!==0||native.requests.length!==2)throw Error('Native identity');
 if(!eq(json(base+'/LOADED_MODULES.json'),cell.expected_module_map))throw Error('Qualified module identity');
 const pair=[];
 for(const item of job.diagnostics){
  const r=json(base+'/native/'+item.name+'/receipt.json'),record=result.observations.find(x=>x.cell===cell.id&&x.tag===item.name),width=cell.execution==='q8'?8:4;
  if(!record||!eq(record.receipt,r)||!eq(r.output_sha256,cell.expected_output_sha256)||r.output_vectors!==8||r.output_floats!==8*151936||!eq(r.ids,item.ids)||r.capture!==false)throw Error('Full output/receipt bridge');
  if(r.position!==cell.position||r.execution!==cell.execution||!eq(r.physical_width_histogram,{[String(width)]:8/width})||r.executions.length!==8/width||!eq(r.final_bounds,{min:0,max:cell.position+7}))throw Error('Physical work');
  if(r.online_state_imports||r.online_state_exports||r.online_heavy_captures)throw Error('Online capture');
  r.executions.forEach((e,j)=>{if(e.position!==cell.position+j*width||e.width!==width||e.active_cells!==e.position+width||!eq(e.requested_rows,Array.from({length:width},(_,i)=>i)))throw Error('Mask/position');});
  nativeRows+=8;pair.push(r);
 }
 const first=pair[0],follow=pair[1],row={cell:cell.id,core:cell.core,position:cell.position,execution:cell.execution,first_use_s:first.operation_s,follow_up_s:follow.operation_s,first_over_follow:first.operation_s/follow.operation_s,first_graphs:[first.graph_built,first.graph_reused],follow_graphs:[follow.graph_built,follow.graph_reused]};
 if(!eq(row,result.summary.find(x=>x.cell===cell.id)))throw Error('Summary arithmetic');summary.push(row);
 phase.push({cell:cell.id,operation_delta_s:first.operation_s-follow.operation_s,VERIFY_host_delta_s:first.phase_seconds.VERIFY-follow.phase_seconds.VERIFY,output_copy_delta_s:first.output_copy_s-follow.output_copy_s,planning_delta_s:first.planning_s-follow.planning_s});
 const worker=result.workers.find(x=>x.id===cell.id);if(!eq(worker.HOST,host))throw Error('Worker cost identity');processCosts.adapter_inclusive_s+=worker.adapter_inclusive_s;processCosts.native_worker_wall_s+=host.worker_wall_s;processCosts.host_wrapper_wall_s+=host.wrapper_wall_s;
 const samples=records.get(base+'/resources.jsonl');if(samples)for(const line of samples.trim().split('\n'))if(line){const x=JSON.parse(line);memory.push(Number(x.gpu['memory.total'])-Number(x.gpu['memory.free']));}
}
const contrasts=[];for(const core of ['loop4','packed'])for(const position of [248,252]){const a=summary.find(x=>x.core===core&&x.position===position&&x.execution==='q4pair'),b=summary.find(x=>x.core===core&&x.position===position&&x.execution==='q8');contrasts.push({core,position,first_q8_over_q4pair:b.first_use_s/a.first_use_s,follow_up_q8_over_q4pair:b.follow_up_s/a.follow_up_s});}
const costs=read('COSTS.json');if(nativeRows!==128||costs.Stage_C_requests!==16||costs.cumulative_requests!==1909||costs.cumulative_reserved_rows!==3053954)throw Error('Cumulative budget');
const diagnosis={status:'COMPLETE_16_REQUEST_HOST_PHASE_PROFILE',summary,contrasts,phase_deltas:phase,process_costs:processCosts,actual_target_rows:128,draft_rows:0,new_reference_requests:0,budget:{cumulative_requests:1909,remaining_requests:139,cumulative_reserved_rows:3053954,remaining_rows:4946046},max_sampled_total_minus_free_MiB:Math.max(...memory),memory_scope:'2s sampled selected-device lower bound, not precise per-process peak',
 limits:['One first-use/follow-up observation per cell; no steady-state convergence or population inference','VERIFY is a host boundary, not CUDA kernel timing; no attribution of every internal first-use expense','B full-vector/active-KV proofs reused with exact binaries/modules/operands; new C clean requests check all8 vector hashes and bounds, without new online full-KV export','No live draft/acceptance/pending/EOG/rollback comparison; no candidate optimization or D/E panel']};
fs.writeFileSync(path.join(out,'DIAGNOSIS.json'),JSON.stringify(diagnosis,null,2)+'\n');
fs.writeFileSync(path.join(out,'CHECKED.json'),JSON.stringify({passed:true,records:records.size,profile_operations:16,actual_target_rows:128,exact_native_receipts:true,source_bundle_sha256:manifest.sha256,new_native_requests:0,scope:'Public/exported byte and saved-counter/statistic reconciliation, not GPU numerical requalification'},null,2)+'\n');
console.log(JSON.stringify({passed:true,contrasts,processCosts}));
