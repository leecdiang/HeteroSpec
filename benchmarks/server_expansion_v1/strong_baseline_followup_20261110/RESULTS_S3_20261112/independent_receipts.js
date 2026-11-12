// Saved-data reconstruction only. No Python, GPU, model executable or network.
// node independent_receipts.js RESTORED_ARCHIVE FRESH_OUTPUT [ORIGINAL_STUDY_ROOT]
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const root=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]),originalRoot=process.argv[4];
assert(!fs.existsSync(out),'Fresh output required');fs.mkdirSync(out);
const read=n=>JSON.parse(fs.readFileSync(path.join(root,n),'utf8'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const canon=x=>JSON.stringify(sort(x));
function sort(x){if(Array.isArray(x))return x.map(sort);if(x&&typeof x==='object')return Object.fromEntries(Object.keys(x).sort().map(k=>[k,sort(x[k])]));return x;}
const equal=(a,b)=>assert.deepEqual(a,b);
const close=(a,b)=>assert(Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=1e-12*Math.max(1,Math.abs(a),Math.abs(b)),`${a} != ${b}`);
const sum=(xs)=>xs.reduce((a,b)=>a+b,0);
const restored=x=>originalRoot?JSON.parse(JSON.stringify(x).replaceAll('${HS_ROOT}',originalRoot)):x;
const write=(n,x)=>fs.writeFileSync(path.join(out,n),JSON.stringify(x,null,2)+'\n',{flag:'wx'});
// The public archive INDEX is the byte authority for public-only replay.
// Original-path-dependent commitments are separate optional host-side checks.
const publicIndex=read('INDEX.json');let publicPayloadsVerified=0,publicPayloadBytes=0;const seenPublic=new Set();
for(const e of publicIndex.files){const p=path.resolve(root,e.path);assert(p.startsWith(root+path.sep)&&!seenPublic.has(e.path));seenPublic.add(e.path);assert(fs.lstatSync(p).isFile()&&!fs.lstatSync(p).isSymbolicLink());const raw=fs.readFileSync(p);assert.equal(raw.length,e.bytes);assert.equal(hash(raw),e.sha256);publicPayloadsVerified++;publicPayloadBytes+=raw.length;}
const manifest=read('data/FROZEN_MANIFEST.json'),roots=read('data/ROOTS.json').inputs,cert=read('data/S3_QUALIFICATION_CERTIFICATE.private.json');
assert.equal(roots.length,12);roots.forEach((r,i)=>{assert.equal(r.slot,i);assert.equal(r.domain,i<6?'code':'math');assert.equal(r.cap,128);assert(r.prompt_ids.length>=1&&r.prompt_ids.length<=192);});
assert.equal(new Set(roots.map(x=>x.id)).size,12);assert.equal(cert.status,'ALL_NEW_ROOT_AND_FRONTEND_GATES_PASSED');
assert.equal(cert.logical_operations,135);assert.equal(cert.workers,66);assert.equal(cert.repeated_pristine_R_requests,24);assert.equal(cert.old_boundary_heavy_clean_requests,36);assert.equal(cert.new_root_bridge_calibration_requests,75);
assert.equal(manifest.workers.length,210);assert.equal(manifest.planned_requests,423);assert.equal(manifest.failure_reserve,16);

// Complete journal, independently reconstructed without importing a ledger reader.
const approval=read('data/BUDGET_APPROVAL.json'),inherit=read('data/INHERITANCE.json');
const ledgerRaw=fs.readFileSync(path.join(root,'data/FINAL_GLOBAL_LEDGER.jsonl'));
const prefix=fs.readFileSync(path.join(root,'data/ORIGINAL32B_S1_S2_PREFIX.jsonl'));
assert(ledgerRaw.subarray(0,prefix.length).equals(prefix));assert.equal(prefix.length,approval.predecessor_prefix_bytes);assert.equal(hash(prefix),approval.predecessor_prefix_sha256);
const prefixEvents=prefix.toString().trim().split('\n').length,previousApproval=hash(canon(approval.predecessor_approval)),currentApproval=hash(canon(approval));
let parent='0'.repeat(64),requests=inherit.requests,reservedRows=inherit.reserved_rows;const states=new Map(),reserves=new Map(),failures=[],events=[];
const transitions={START:'RESERVE',COMPLETE:'START',FAILED:'START',CANCELLED_NO_LAUNCH:'RESERVE'};
for(const [i,line]of ledgerRaw.toString().trim().split('\n').entries()){
 const e=JSON.parse(line),eventHash=e.event_sha256;delete e.event_sha256;
 assert.equal(e.parent_sha256,parent);assert.equal(hash(canon(e)),eventHash);parent=eventHash;
 assert.equal(e.approval_sha256,i<prefixEvents?previousApproval:currentApproval);assert.equal(e.inheritance_sha256,inherit.ledger_sha256);
 const op=e.operation_id;if(e.kind==='RESERVE'){assert(!states.has(op));assert(Number.isSafeInteger(e.reserved_rows)&&e.reserved_rows>=0);reserves.set(op,e);requests++;reservedRows+=e.reserved_rows;}
 else {assert.equal(states.get(op),transitions[e.kind]);if(e.kind==='FAILED')failures.push(e);}
 states.set(op,e.kind);events.push(e);
}
const s3=[...reserves].filter(([k])=>k.startsWith('s3-v1-')),qual=manifest.workers.filter(w=>w.stage==='qualification'),formal=manifest.workers.filter(w=>w.stage==='formal');
assert.equal(requests,1796);assert.equal(reservedRows,771465);assert.equal(s3.length,423);assert.equal(qual.length,66);assert.equal(formal.length,144);
assert.equal(approval.phase_request_ceiling,439);assert.equal(approval.request_ceiling,1812);assert(requests<=approval.request_ceiling&&reservedRows<=approval.row_ceiling);
const expectedOps=new Map(manifest.workers.flatMap(w=>w.operations.map(op=>[op.operation_id,{...op,worker:w.worker_id,stage:w.stage}])));
assert.equal(expectedOps.size,423);let qualOps=0,formalOps=0,s3Rows=0;
for(const [id,e]of s3){const op=expectedOps.get(id);assert(op);assert.equal(states.get(id),'COMPLETE');assert.equal(e.worker,op.worker);assert.equal(e.reserved_rows,op.reserved_rows);s3Rows+=e.reserved_rows;op.stage==='formal'?formalOps++:qualOps++;}
assert.equal(qualOps,135);assert.equal(formalOps,288);assert.equal(s3Rows,93753);assert.equal(failures.length,4);assert.equal(failures.filter(x=>x.operation_id.startsWith('s3-v1-')).length,0);
const admission=read('data/ADMISSION.private.json'),formalAdmission=read('data/ADMISSION_FORMAL_DERIVED.private.json');
const launchAudit=[],allReceipts=[];let qualificationCaller=0,formalCaller=0,previousLaunch=0;
for(const w of manifest.workers){
 const base='data/'+(w.stage==='formal'?'S3':'S3_QUAL')+'/workers/'+w.worker_id+'/',job=read(base+'JOB.json'),worker=read(base+'WORKER.json'),host=read(base+'HOST.json'),launch=read(base+'LAUNCH.private.json'),native=read(base+'native/result.json'),config=w.stage==='formal'?formalAdmission:admission;
 equal(worker,w);assert.equal(host.status,'COMPLETE');assert.equal(host.returncode,0);assert.equal(host.reason,null);assert.equal(native.status,'COMPLETE');assert.equal(job.inputs.length,w.operations.length);
 const utc=Date.parse(launch.utc);assert(utc>=Date.parse(config.allocation_start_utc)&&utc<=Date.parse(config.last_new_worker_utc));assert(Date.parse(config.allocation_end_utc)-utc>=1000*(config.worker_timeout_s+60));assert(utc>=previousLaunch);previousLaunch=utc;
 equal(launch.boot_id,config.boot_id);assert.equal(launch.launch_begin_monotonic_ns,host.launch_begin_monotonic_ns);assert(Number.isSafeInteger(launch.pid)&&/^\d+$/.test(launch.start_ticks));
 const binary=config.executables[w.kind==='pristine-model-services'?'R':'model'];equal(launch.executable_sha256,binary.sha256);assert(launch.argv.includes(binary.path));assert(launch.argv.includes(config.executables.guard.path));
 if(originalRoot){assert.equal(hash(canon(restored(job))),w.job_sha256);const actualBytes=fs.readFileSync(path.join(root,base+'JOB.json'),'utf8').replaceAll('${HS_ROOT}',originalRoot);assert.equal(hash(actualBytes),launch.job_sha256);}
 equal(native.requests,job.inputs.map(x=>({name:x.name,record:x.name+'/receipt.json'})));
 for(let i=0;i<w.operations.length;i++){
  const op=w.operations[i],entry=job.inputs[i],r=read(base+'native/'+entry.name+'/receipt.json'),reserve=reserves.get(op.operation_id);assert(reserve);assert.equal(reserve.job_sha256,launch.job_sha256);assert.equal(reserve.manifest_sha256,cert.manifest_sha256);assert.equal(op.ordinal,i);
  assert(Array.isArray(r.ids)&&r.ids.length>0&&r.ids.length<=entry.input.cap);assert.equal(r.eog.length,r.ids.length);
  if(w.kind==='pristine-model-services'){assert.equal(r.heavy,true);assert.equal(r.cap,entry.input.cap);assert.equal(r.pending_id,r.ids.at(-1));assert.equal(r.pending_position,entry.input.prompt_ids.length+r.ids.length-1);assert.equal(r.materialized_tokens,r.pending_position);}
  else {equal(native.native_capability,job.capability_request);equal(r.prompt_ids,entry.input.prompt_ids);assert.equal(r.capture,entry.capture);assert.equal(r.draft_enabled,false);assert.equal(r.draft_calls,0);assert.equal(r.k,0);assert.equal(r.target_output_reserve,32);assert.equal(r.S3_service.initial_reset_included,true);}
  allReceipts.push({operation_id:op.operation_id,stage:w.stage,worker_id:w.worker_id,entry_name:entry.name,capture:entry.capture,generated_tokens:r.ids.length,sha256:hash(fs.readFileSync(path.join(root,base+'native/'+entry.name+'/receipt.json')))});
 }
 if(w.stage==='formal')formalCaller+=host.caller_s;else qualificationCaller+=host.caller_s;
 launchAudit.push({worker_id:w.worker_id,stage:w.stage,utc:launch.utc,inside_registered_window:true,boot_matches_admission:true,ELF_sha256:launch.executable_sha256});
}
assert.equal(allReceipts.length,423);assert.equal(launchAudit.length,210);assert.equal(new Set(allReceipts.map(x=>x.operation_id)).size,423);
function localExecutionFile(original){const marker='/execution/';assert(original.includes(marker));return 'data/'+original.split(marker)[1];}
let comparisonsVerified=0;
for(const item of cert.comparison_files){const rel=localExecutionFile(item.path);assert(seenPublic.has(rel));if(originalRoot){const raw=fs.readFileSync(path.join(root,rel),'utf8');assert.equal(hash(raw.replaceAll('${HS_ROOT}',originalRoot)),item.sha256);comparisonsVerified++;}}
assert.equal(cert.comparison_files.length,66);assert.equal(comparisonsVerified,originalRoot?66:0);
const oracle=read('data/NEW_ROOT_ORACLES_FROZEN.private.json');assert.equal(oracle.status,'ALL24_REPEATED_PRISTINE_R_REQUESTS_PASSED_AND_ORACLES_FROZEN');assert.equal(oracle.inventories.length,24);assert.equal(oracle.repeated_checks.length,12);
for(const item of oracle.repeated_checks){const rel=localExecutionFile(item.path);assert(seenPublic.has(rel));if(originalRoot){const raw=fs.readFileSync(path.join(root,rel),'utf8');assert.equal(hash(raw.replaceAll('${HS_ROOT}',originalRoot)),item.sha256);}}
assert.equal(hash(fs.readFileSync(path.join(root,'data/FROZEN_MANIFEST.json'))),cert.manifest_sha256);
assert.equal(hash(fs.readFileSync(path.join(root,'data/ROOTS.json'))),cert.roots_sha256);
if(originalRoot){for(const [file,expected]of [['data/NEW_ROOT_ORACLES_FROZEN.private.json',cert.new_root_oracles_sha256],['data/S3_QUALIFICATION_CERTIFICATE.private.json',formalAdmission.S3_certificate_sha256]])assert.equal(hash(fs.readFileSync(path.join(root,file),'utf8').replaceAll('${HS_ROOT}',originalRoot)),expected);}

// Read all original worker metadata and receipts. Statistics below do not use
// S3_ROWS.json or S3_ANALYSIS.json until their independent calculation is done.
const rows=[],workerCosts=[],references=[],roundData=[];const numericInventory=new Map(read('INDEX.json').withheld_numeric_payloads.map(x=>[x.logical_id,x]));
const rdata=slot=>`data/S3_QUAL/workers/s3-v1-R-root${String(slot).padStart(2,'0')}-repeat0/native/new-root${String(slot).padStart(2,'0')}/receipt.json`;
for(let i=0;i<12;i++){
 const r=read(rdata(i)),second=read(rdata(i).replace('repeat0','repeat1'));
 for(const k of ['ids','eog','cap','pending_id','pending_position','materialized_tokens','terminal_kind'])equal(r[k],second[k]);
 assert.equal(r.pending_id,r.ids.at(-1));assert.equal(r.pending_position,roots[i].prompt_ids.length+r.ids.length-1);assert.equal(r.materialized_tokens,r.pending_position);
 references.push(r);
}
let lastNativeEnd=0;const orders=['GBC BCG CGB GCB','BCG CGB GBC CBG','CGB GBC BCG BGC','GCB CBG BGC GBC','CBG BGC GCB BCG','BGC GCB CBG CGB'].map(x=>x.split(' '));let fi=0;
for(let round=0;round<4;round++)for(let ri=0;ri<12;ri++){
 const slot=(ri+3*round)%12;
 for(const arm of orders[slot%6][round]){
  const w=formal[fi++];assert.equal(w.arm,arm);assert.equal(w.slot,slot);assert.equal(w.block,round);
  const base='data/S3/workers/'+w.worker_id+'/',actualWorker=read(base+'WORKER.json'),job=read(base+'JOB.json'),host=read(base+'HOST.json'),result=read(base+'native/result.json');
  equal(actualWorker,w);assert.equal(host.status,'COMPLETE');assert.equal(host.returncode,0);assert.equal(host.reason,null);assert.equal(result.status,'COMPLETE');
  const expectedRuntime=job.capability_request;equal(result.native_capability,expectedRuntime);assert.equal(expectedRuntime.arm,arm);
  for(const [k,v]of Object.entries({greedy:true,k:0,draft:false,cuda_graphs:false,flash_attention:false,n_ctx:1024,n_ubatch:32,output_reserve:32,threads:2,native_planner:'SIMPLE',lowering:'WHOLE',kv_K:'f16',kv_V:'f16'}))equal(expectedRuntime[k],v);
  for(const [k,v]of Object.entries({k:0,draft:false,cuda_graphs:false,flash_attention:false,n_ctx:1024,n_ubatch:32,output_reserve:32,target_output_reserve:32,threads:2,lowering:'WHOLE',residency:'target_only'}))equal(job[k],v);
  equal(result.requests,[{name:'warm',record:'warm/receipt.json'},{name:'measured',record:'measured/receipt.json'}]);assert.equal(job.inputs.length,2);
  if(originalRoot)assert.equal(hash(canon(restored(job))),w.job_sha256,'Original canonical job binding');
  const runtime={...job};delete runtime.inputs;
  const durations=[];let warm;
  for(let ordinal=0;ordinal<2;ordinal++){
   const role=ordinal?'measured':'warm',entry=job.inputs[ordinal],r=read(base+'native/'+role+'/receipt.json'),tape=read(base+'native/'+role+'/semantic-tape.json'),x=r.S3_service;
   assert.equal(entry.name,role);assert.equal(entry.capture,false);assert.equal(entry.input.id,roots[slot].id);equal(entry.input.prompt_ids,roots[slot].prompt_ids);assert.equal(entry.input.cap,128);
   const ref=references[slot],n=entry.input.prompt_ids.length,count=r.ids.length,materialized=n+count-1;
   equal(r.prompt_ids,entry.input.prompt_ids);equal(r.ids,ref.ids);equal(r.eog,ref.eog);assert.equal(r.stop_reason,ref.terminal_kind);assert.equal(r.terminal_id,r.ids.at(-1));
   equal(r.endpoint.ids,r.ids);equal(r.endpoint.eog,r.eog);assert.equal(r.endpoint.length,count);assert.equal(r.endpoint.stop_reason,r.stop_reason);assert.equal(r.endpoint.terminal_id,r.terminal_id);
   assert(count>=1&&count<=128);assert.equal(r.length,count);assert(['CAP','EOG'].includes(r.stop_reason));
   assert.equal(r.eog.length,count);r.ids.forEach((id,i)=>assert.equal(r.eog[i],result.eog_ids.includes(id)));
   if(r.stop_reason==='CAP')assert.equal(count,128);else assert.equal(r.eog.at(-1),true);assert(!r.eog.slice(0,-1).some(Boolean));
   equal(r.target_final_kv,{min:0,max:materialized-1});assert.equal(ref.pending_position,materialized);
   for(const k of ['capture','draft_enabled'])assert.equal(r[k],false);for(const k of ['draft_calls','k','online_reference_replays','online_state_exports','online_state_imports','online_context_creates'])assert.equal(r[k],0);
   equal(r.observed_API_calls_within_service,{context_creates:0,heavy_captures:0,state_exports:0,state_imports:0});assert.equal(r.observer_mode,'counts');assert.equal(r.target_output_reserve,32);
   assert.equal(x.clock,'CLOCK_MONOTONIC');assert.equal(x.unit,'s');for(const k of ['start_ns','reset_end_ns','fence_ns','owned_ready_ns','end_ns'])assert(Number.isSafeInteger(x[k])&&x[k]>0);
   assert(x.start_ns>=lastNativeEnd&&x.reset_end_ns>=x.start_ns&&x.fence_ns>=x.reset_end_ns&&x.end_ns>=x.fence_ns&&x.owned_ready_ns>=x.start_ns&&x.owned_ready_ns<=x.end_ns);lastNativeEnd=x.end_ns;
   assert(host.launch_begin_monotonic_ns<=x.start_ns&&x.end_ns<=host.exit_observed_monotonic_ns);
   close(x.elapsed_s,(x.end_ns-x.start_ns)/1e9);close(x.reset_s,(x.reset_end_ns-x.start_ns)/1e9);
   assert.equal(x.empty_after_reset_min,-1);assert.equal(x.empty_after_reset_max,-1);assert.equal(x.initial_reset_included,true);assert.equal(x.all_required_outputs_owned,true);assert.equal(x.post_service_receipt_state_export_serialization_excluded,true);assert.equal(x.stop_separate_s,null);
   const widths=[];for(let i=0;i<n;i+=32)widths.push(Math.min(32,n-i));for(let i=1;i<count;i++)widths.push(1);equal(r.executions.map(e=>e.width),widths);equal(r.phase_executions,r.executions);assert.equal(r.target_calls,widths.length);
   const histogram={};let pos=0;for(const e of r.executions){assert.equal(e.position,pos);assert.equal(e.active_cells,pos+e.width);assert.equal(e.phase,pos<n?'PREFILL':'ORDINARY');equal(e.requested_rows,pos+e.width<n?[]:pos<n?[n-1]:[0]);const ext=Array.from({length:e.width},(_,j)=>Math.max(256,Math.ceil((pos+j+1)/256)*256));equal(e.expected_extents,ext);assert.equal(e.actual_attention_extent,Math.max(...ext));histogram[String(e.width)]=(histogram[String(e.width)]||0)+1;pos+=e.width;}
   assert.equal(pos,materialized);equal(histogram,r.target_physical_width_hist);
   equal(tape,{executions:r.executions,ids:r.ids,prompt_ids:r.prompt_ids,stop_reason:r.stop_reason,target_final_kv:r.target_final_kv});assert.equal(hash(canon(tape)),r.semantic_tape_sha256);assert.equal(r.semantic_tape_sha256,cert.qualified_tapes[slot+'/'+arm]);
   const work=r.application_work;assert.equal(work.opaque_library_internal_launches,null);for(const [k,v]of Object.entries(work))if(k!=='opaque_library_internal_launches')assert(Number.isSafeInteger(v)&&v>=0);
   assert.equal(work.backend_loop_entries>0,arm==='B'&&n>1);assert(work.scalar_dot_columns>0&&work.scalar_dot_dispatches>0&&work.quant_calls>0&&work.quant_rows>=work.quant_calls&&work.kernel_application_launch_calls>0);
   const terminal=numericInventory.get(base+'native/'+role+'/post-service-terminal/frontier.f32');assert(terminal&&terminal.bytes===151936*4);
   const row={operation_id:w.operations[ordinal].operation_id,worker_id:w.worker_id,arm,slot,block:round,ordinal,role,phase:'S3',unit:'s',elapsed_s:x.elapsed_s,start_ns:x.start_ns,end_ns:x.end_ns,fence_ns:x.fence_ns,owned_ready_ns:x.owned_ready_ns,input_sha256:hash(canon(entry.input)),config_sha256:originalRoot?hash(canon(restored(runtime))):null,output_sha256:terminal.sha256,q:count,output_rows:count,all_outputs_owned:true,callback_continues:true,tokens:r.ids,generated_tokens:count,stop_reason:r.stop_reason.toLowerCase(),work_counters:work,actual_physical_width_histogram:r.target_physical_width_hist,reset_s:x.reset_s,prefill_s:r.target_phases.PREFILL||0,decode_s:r.target_phases.ORDINARY||0,planning_s:r.planning_s,owned_output_copy_s:r.output_copy_s,stop_separate_s:null,receipt_sha256:hash(fs.readFileSync(path.join(root,base+'native/'+role+'/receipt.json'))),semantic_tape_sha256:r.semantic_tape_sha256};
   if(warm){equal(row.tokens,warm.tokens);assert.equal(row.output_sha256,warm.output_sha256);assert.equal(row.semantic_tape_sha256,warm.semantic_tape_sha256);}else warm=row;
   rows.push(row);durations.push(x.elapsed_s);
  }
  workerCosts.push({worker_id:w.worker_id,arm,slot,round,caller_s:host.caller_s,launch_to_exit_observation_s:host.launch_to_exit_observation_s,model_load_s:result.model_load_s,pool_setup_s:result.pool_setup_s,warm_s:durations[0],measured_s:durations[1]});
 }
}
assert.equal(rows.length,288);assert.equal(fi,144);

// CPython-compatible MT19937 implemented independently in JavaScript.
class RNG{constructor(seed){this.mt=new Uint32Array(624);this.mt[0]=19650218;for(let i=1;i<624;i++)this.mt[i]=(Math.imul(1812433253,this.mt[i-1]^(this.mt[i-1]>>>30))+i)>>>0;let i=1;for(let k=0;k<624;k++){this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1664525))+seed)>>>0;if(++i>=624){this.mt[0]=this.mt[623];i=1;}}for(let k=0;k<623;k++){this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1566083941))-i)>>>0;if(++i>=624){this.mt[0]=this.mt[623];i=1;}}this.mt[0]=0x80000000;this.i=624;}next(){if(this.i>=624){for(let i=0;i<624;i++){const y=(this.mt[i]&0x80000000)|(this.mt[(i+1)%624]&0x7fffffff);this.mt[i]=(this.mt[(i+397)%624]^(y>>>1)^((y&1)?0x9908b0df:0))>>>0;}this.i=0;}let y=this.mt[this.i++];y^=y>>>11;y^=(y<<7)&0x9d2c5680;y^=(y<<15)&0xefc60000;y^=y>>>18;return y>>>0;}six(){let x;do{x=this.next()>>>29;}while(x>=6);return x;}}
const test=new RNG(20261110);equal(Array.from({length:24},()=>test.six()),[2,5,1,4,5,5,3,5,5,2,2,1,4,2,1,2,4,4,3,4,1,2,5,4]);
const pct=(xs,p)=>{const x=(xs.length-1)*p,lo=Math.floor(x),hi=Math.ceil(x);return xs[lo]+(xs[hi]-xs[lo])*(x-lo);};
const measured=rows.filter(x=>x.role==='measured'),lookup=new Map(measured.map(x=>[`${x.slot}/${x.block}/${x.arm}`,x.elapsed_s]));
const totals=Object.fromEntries(['G','B','C'].map(a=>[a,sum(measured.filter(x=>x.arm===a).map(x=>x.elapsed_s))]));
const contrasts=[];
for(const [candidate,baseline,confidence]of [['C','B',.95],['B','G',.975],['C','G',.975]]){
 const perRoot=[];for(let s=0;s<12;s++){const pairs=[];for(let b=0;b<4;b++)pairs.push({round:b,numerator_s:lookup.get(`${s}/${b}/${candidate}`),denominator_s:lookup.get(`${s}/${b}/${baseline}`)});const log=sum(pairs.map(x=>Math.log(x.numerator_s/x.denominator_s)))/4;perRoot.push({slot:s,id:roots[s].id,domain:roots[s].domain,prompt_tokens:roots[s].prompt_ids.length,generated_tokens:references[s].ids.length,stop_reason:references[s].terminal_kind,ratio:Math.exp(log),log_ratio:log,rounds:pairs.map(x=>({...x,ratio:x.numerator_s/x.denominator_s}))});}
 const rng=new RNG(20261110),bs=[];for(let i=0;i<20000;i++){let c=0,m=0;for(let j=0;j<6;j++)c+=perRoot[rng.six()].log_ratio;for(let j=0;j<6;j++)m+=perRoot[6+rng.six()].log_ratio;bs.push(Math.exp((c/6+m/6)/2));}bs.sort((a,b)=>a-b);const tail=(1-confidence)/2;
 const med=perRoot.map(x=>x.ratio).sort((a,b)=>a-b);contrasts.push({candidate,baseline,denominator_arm:baseline,ratio:Math.exp(sum(perRoot.map(x=>x.log_ratio))/12),confidence,interval:[pct(bs,tail),pct(bs,1-tail)],ratio_of_totals:totals[candidate]/totals[baseline],numerator_total_s:totals[candidate],denominator_total_s:totals[baseline],median_root_ratio:(med[5]+med[6])/2,per_root:perRoot});
}
// Only now compare independently reconstructed results with prior converters.
const savedRows=new Map(read('data/S3_ROWS.json').map(x=>[x.operation_id,x]));assert.equal(savedRows.size,288);
for(const row of rows){const s=savedRows.get(row.operation_id);assert(s);for(const [k,v]of Object.entries(row)){if(['receipt_sha256','semantic_tape_sha256'].includes(k)||v===null&&k==='config_sha256')continue;if(typeof v==='number')close(v,s[k]);else equal(v,s[k]);}}
const saved=read('data/S3_ANALYSIS.json');for(const c of contrasts){const s=saved.contrasts.find(x=>x.candidate===c.candidate&&x.baseline===c.baseline);close(c.ratio,s.ratio);close(c.ratio_of_totals,s.total_ratio);c.interval.forEach((v,i)=>close(v,s.interval[i]));c.per_root.forEach(x=>close(x.ratio,s.per_root_ratio[String(x.slot)]));}
const byArm={};for(const a of ['G','B','C']){const rr=measured.filter(x=>x.arm===a),wc=workerCosts.filter(x=>x.arm===a);byArm[a]={measured_requests:48,warm_requests:48,measured_service_s:totals[a],warm_service_s:sum(rows.filter(x=>x.arm===a&&x.role==='warm').map(x=>x.elapsed_s)),full_worker_caller_s:sum(wc.map(x=>x.caller_s)),observed_launch_to_exit_s:sum(wc.map(x=>x.launch_to_exit_observation_s)),model_load_s:sum(wc.map(x=>x.model_load_s)),pool_setup_s:sum(wc.map(x=>x.pool_setup_s)),measured_reset_s:sum(rr.map(x=>x.reset_s)),measured_prefill_s:sum(rr.map(x=>x.prefill_s)),measured_decode_s:sum(rr.map(x=>x.decode_s)),measured_planning_s:sum(rr.map(x=>x.planning_s)),measured_owned_output_copy_s:sum(rr.map(x=>x.owned_output_copy_s)),measured_service_less_reset_prefill_decode_s:sum(rr.map(x=>x.elapsed_s-x.reset_s-x.prefill_s-x.decode_s)),work_counters:Object.fromEntries(Object.keys(rr[0].work_counters).map(k=>[k,k==='opaque_library_internal_launches'?null:sum(rr.map(x=>x.work_counters[k]))]))};}
const report={status:'INDEPENDENT_RAW_RECEIPT_RECONSTRUCTION_AND_LEDGER_PASSED',GPU_requests:0,inputs:'144 original WORKER/JOB/HOST/native results and288 raw request receipts; S3_ROWS/S3_ANALYSIS read only after reconstruction',workers:144,formal_requests:288,qualification_requests:135,total_stage_requests:423,reset_seconds_vs_ns_checked:288,semantic_hashes_and_qualified_tapes_checked:288,all_expected_receipts_present:true,roots:12,domains:{code:6,math:6},bootstrap:{unit:'whole_root_with_all_four_rounds',strata:[6,6],replicates:20000,seed:20261110,percentile:'linear_R7'},contrasts,ledger:{sha256:hash(ledgerRaw),events:events.length,chain_tip_sha256:parent,prefix_sha256:hash(prefix),global_requests:requests,global_reserved_rows:reservedRows,original_inheritance_requests:inherit.requests,original_inheritance_rows:inherit.reserved_rows,S3_reserved_rows:s3Rows,S3_requests:423,S3_qualification_requests:qualOps,S3_formal_requests:formalOps,S3_failures:0,all_recorded_new_journal_failures:failures,scope_of_failures:'Four S1 failures in this journal; original514 historical ledger only committed here, its internal failures are not reconstructed from this artifact',unused_failure_reserve:16,phase_ceiling:439,global_ceiling:1812},same_panel_costs:{by_arm:byArm,formal_caller_s:sum(workerCosts.map(x=>x.caller_s)),formal_model_load_s:sum(workerCosts.map(x=>x.model_load_s)),formal_pool_setup_s:sum(workerCosts.map(x=>x.pool_setup_s)),caveats:['Full caller contains startup/hash/load/warm/request/export/exit and polling; do not add its nested costs again','Phase/copy/planning clocks are not automatically disjoint; source boundary audit is required before any additive cost stack','stop has no separately measured interval; unassigned remainder is not a named optimization target','No S2 or other experiment cost is included']},limitations:['Saved public text reconstruction is not a GPU rerun or an independent repeat of heavy raw-vector/KV numeric comparisons','Terminal output_sha256 comes from archived private-numeric inventory, not locally available binary payload','Clean/formal checks bind qualified semantic tape and terminal full frontier/KV, not repeated every-step raw numerical captures','Original job/config hashes use only inversion of declared study-root path sanitization when explicitly provided','Original514 historical requests are inherited by full ledger SHA; this artifact does not contain that ledger full internals']};
report.public_payload_integrity={status:'ALL_INDEXED_PUBLIC_FILE_BYTES_VERIFIED',files:publicPayloadsVerified,bytes:publicPayloadBytes};
report.original_path_dependent_hashes={mode:originalRoot?'OPTIONAL_HOST_ROOT_INVERSION_VERIFIED':'UNAVAILABLE_PUBLIC_SANITIZED_BYTES_ONLY',checks_verified:originalRoot?788:0,checks_unavailable:originalRoot?0:788,categories:{canonical_job210:210,raw_job210:210,formal_runtime288:288,comparison66_repeatedR12_oracle_certificate2:80},limitation:'Public INDEX hashes are always verified. Reconstructing original path-containing job/runtime/proof hashes additionally requires the original study-root mapping; public-only mode does not claim that host-side check.'};
report.all_stage_audit={workers:210,qualification_workers:66,formal_workers:144,original_receipts:allReceipts.length,all210_HOST_native_outcomes:'COMPLETE_EXIT0',all210_LAUNCH_windows:'Within originally registered allocation and last-worker timestamps with timeout+60 seconds available',all210_LAUNCH_boot_and_binary_identities:'Matched historical admission; does not assert any current process or GPU authorization',qualification_comparison_file_original_hashes_verified:comparisonsVerified,repeated_R_comparison_files_original_hashes_verified:originalRoot?12:0,qualification_certificate_and_oracle_original_hashes_verified:!!originalRoot,original_job_and_config_path_substitution:originalRoot?'Only declared study-root substitution inverted in memory; private root never emitted':'Not attempted in public-only mode',qualification_full_worker_caller_s:qualificationCaller,formal_full_worker_caller_s:formalCaller,total210_full_worker_caller_s:qualificationCaller+formalCaller,original_complete_controller_phase_wall_s:read('data/STATE.json').caller_s};
report.all_roots_terminal='All12 naturally reached fixed cap128; no root replacement or EOG padding. Native EOG boundaries are covered by the separately recorded old qualification fixtures, not natural S3 terminations.';
write('RECONSTRUCTED_ROWS.json',rows);write('WORKER_COSTS.json',workerCosts);write('INDEPENDENT_REPORT.json',report);
write('ALL423_RECEIPT_INVENTORY.json',allReceipts);write('ALL210_LAUNCH_AUDIT.json',launchAudit);
const csv=['slot,id,domain,prompt_tokens,generated_tokens,stop_reason,CB,BG,CG',...contrasts[0].per_root.map((r,i)=>[r.slot,r.id,r.domain,r.prompt_tokens,r.generated_tokens,r.stop_reason,...contrasts.map(c=>c.per_root[i].ratio)].join(','))].join('\n')+'\n';fs.writeFileSync(path.join(out,'PER_ROOT.csv'),csv,{flag:'wx'});
console.log(JSON.stringify({status:report.status,contrasts:contrasts.map(c=>({comparison:c.candidate+'/'+c.baseline,ratio:c.ratio,CI:c.interval,total_ratio:c.ratio_of_totals})),requests,reservedRows,formal_caller_s:report.same_panel_costs.formal_caller_s}));
