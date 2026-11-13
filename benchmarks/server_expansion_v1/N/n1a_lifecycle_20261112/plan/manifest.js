'use strict';
// CPU-only operation-graph and resource proposal. No native/GPU imports.
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const {fixtures}=require('./control_fixtures.js');
const PATHS=Object.freeze(['RESIDENT_R','REPEAT_RESIDENT_R','COLD_CANONICAL_ORACLE','STRONG_WHOLE_RECHUNK_LOOP4']);
const GATES=Object.freeze({
 RESIDENT_R:'EXPLICIT_GPU_ADMISSION_AND_CPU_PRODUCER_CONTRACT_PASS',
 REPEAT_RESIDENT_R:'ALL18_RESIDENT_R_REQUESTS_AND_REFERENCE_FREEZE_COMPLETE',
 COLD_CANONICAL_ORACLE:'ALL18_REPEAT_R_FULL_VECTOR_ACTIVE_KV_PENDING_AND_RESET_PASS',
 STRONG_WHOLE_RECHUNK_LOOP4:'ALL18_COLD_CANONICAL_ORACLE_STRICT_VECTOR_ACTIVE_KV_SEMANTIC_BRIDGE_PASS'
});
const FIRST_PROMPTS=Object.freeze({
 '330fc1cf-53dd-4d67-8201-2782df947dd5':{second_user_message_id:'b23c5984-720f-4e0c-907d-a0f33127c944',tokens:92,ids_sha256:'9e18b22385c7b247bd13cf2937145a30a8a9aef3b205a8dedcdfe383dfb469ab'},
 '5edbd199-3e8f-450d-b204-e8e8b06d80d4':{second_user_message_id:'cc53a054-b83c-4510-a368-65787eadc128',tokens:63,ids_sha256:'82a592eb7ba7fd6f8b323ad60dfafd5a83882a615db2be2c720de99991ec4c4b'},
 '889c27c2-1673-409b-a05a-7bf53d8ab0df':{second_user_message_id:'4de57064-e6bc-45ff-a85b-c58d1a6f0985',tokens:27,ids_sha256:'4b24ef5aee4197730155c62b3992eae229257c057fd20bb5ba8b160e69d37233'},
 '9e9e8057-8769-42e1-ab20-97b54275cfe9':{second_user_message_id:'790f0c74-d400-4ac6-9328-8e17f05bc62f',tokens:108,ids_sha256:'0e557b95eb211a36c8b9e7248941d75e32ac8dff6e8d0f1771614884dd7f78d8'}
});
const CONTROLS=Object.freeze([
 {id:'pending_cap_append',contract:'SCRIPTED_RAW_TOKEN_CONTROL',purpose:'One forced non-EOG CAP1 token remains pending; a direct-prefix continuation materializes it exactly once. This is not a claim about a natural canonical-chat continuation.'},
 {id:'empty_think_lcp_trim',contract:'SCRIPTED_RAW_TOKEN_CONTROL',purpose:'The old empty-think sequence is absent from the next canonical fixture; compare LCP suffix rebuild and invalid frontier handling.'},
 {id:'fully_cached_replay_ownership',contract:'SCRIPTED_RAW_TOKEN_CONTROL',purpose:'A wholly cached next input backs up one token for a fresh owned frontier; old output copies survive subsequent decode.'},
 {id:'trim_unsupported_rebuild',contract:'SCRIPTED_RAW_TOKEN_CONTROL',purpose:'Predeclared unsupported trim capability causes one common full canonical rebuild, before any second forward.'},
 {id:'trim_pre_mutation_failure_rebuild',contract:'SCRIPTED_RAW_TOKEN_CONTROL',purpose:'Caller-injected no-mutation trim failure exercises common fallback. It is not evidence about arbitrary native API failures.'}
]);
function safe(n,min=0){assert(Number.isSafeInteger(n)&&n>=min,'unsafe/noninteger bound');return n;}
function storage(maxRequests=76){
 safe(maxRequests,1);const MiB=1024**2,GiB=1024**3,kv=603979776,v=151936*4;
 const snapshot=kv+MiB,per=3*snapshot+132*v+2*MiB,raw=maxRequests*per;
 const archive=Math.ceil(raw*1.02)+16*MiB;
 return{profile_status:'CONDITIONAL_WRITER_BOUND_NOT_PROVEN',active_KV_C4096_F16_bytes:kv,
  snapshot_bytes_max:snapshot,snapshots_per_request_max:3,
  vocabulary:151936,requested_and_owned_full_F32_rows_max:132,
  packed_text_bytes_per_request_max:2*MiB,bytes_per_request_max:per,
  raw_bytes_max:raw,archive_bytes_max:archive,strict_restore_bytes_max:raw,
  archive_payload_files_per_request_max:32,archive_header_allowance_bytes:16*MiB,
  build_text_allowance_bytes:8*GiB,protected_free_space_bytes:100*GiB,
  free_bytes_required:raw+archive+raw+8*GiB+100*GiB};
}
function makeManifest(episodes){
 assert(Array.isArray(episodes)&&episodes.length===4,'exactly four frozen development episodes');
 for(const e of episodes)assert(FIRST_PROMPTS[e.root]&&Array.isArray(e.user_message_ids)&&e.user_message_ids.length===2&&e.user_message_ids[0]===e.root,'frozen root with two source user turns');
 for(const e of episodes)assert.equal(e.user_message_ids[1],FIRST_PROMPTS[e.root].second_user_message_id,'frozen second user message replaced');
 assert.equal(new Set(episodes.map(e=>e.root)).size,4,'four unique frozen roots');
 const operations=[];
 const add=(id,cls,path,episode,turn,control=null)=>{const fixture=control?fixtures().find(f=>f.id===control):null;
  const rows=control?(turn===0?fixture.requests[0].expected.model_rows:path==='COLD_CANONICAL_ORACLE'?fixture.requests[1].expected.oracle_model_rows:fixture.requests[1].expected.resident_model_rows):turn===0?FIRST_PROMPTS[episodes[episode].root].tokens+127:4096;
  operations.push({id,class:cls,path,episode,turn,control,dependency_gate:GATES[path],
  role:turn===0?'CHARGED_SETUP_TURN':'CHARGED_CONTINUATION_TURN',
  source_root:control?null:episodes[episode].root,
  source_user_message_id:control?null:episodes[episode].user_message_ids[turn],
  exact_control_token_fixture:control?control:null,
  context_policy:path==='COLD_CANONICAL_ORACLE'?'EMPTY_EACH_TURN_BUILD_OWN_STATE_Q1':'SAME_CONTEXT_FOR_BOTH_TURNS_RESET_BETWEEN_EPISODES',
  prefix_alignment:path==='COLD_CANONICAL_ORACLE'?'Decode canonical[0:resident_R_keep] with original q1 arithmetic, then canonical suffix; never restore R capture':'Actual native materialized prefix and canonical LCP bounded by head',
  request_budget:1,decoded_rows_max:rows,absolute_per_request_row_ceiling:4096,
  actual_native_rows:null,row_reservation_scope:'Canonical append or one canonical full rebuild + generated decodes excluding final pending; stop after any post-forward error',
  capture_phases:['POST_RECONCILE','POST_APPEND','TERMINAL'],
  response_cap:control?1:128,
  producer_mode:control?'SCRIPTED_STATE_CONTROL':path==='COLD_CANONICAL_ORACLE'?'CANONICAL_INPUT_ORACLE_REPLAY':'FREE_SEQUENTIAL',
  reference_inputs:path==='COLD_CANONICAL_ORACLE'?'R-produced exact canonical IDs; empty cache per turn, never restored from R state':'Own producer; compare against R expectations, do not force R output tokens',
  failure_policy:'STOP_ON_POST_FORWARD_ERROR_NO_AUTOMATIC_RETRY'});};
 for(const path of PATHS){
  for(let e=0;e<episodes.length;e++)for(let turn=0;turn<2;turn++)
   add(`natural/${path}/${e}/${turn}`,path==='COLD_CANONICAL_ORACLE'?'NATURAL_CANONICAL_ORACLE':'NATURAL_FREE',path,e,turn);
  for(let c=0;c<CONTROLS.length;c++)for(let turn=0;turn<2;turn++)
   add(`control/${path}/${CONTROLS[c].id}/${turn}`,path==='COLD_CANONICAL_ORACLE'?'SCRIPTED_CONTROL_ORACLE':'SCRIPTED_CONTROL_RESIDENT',path,c,turn,CONTROLS[c].id);
 }
 return{schema:'hs.N1a.lifecycle.proposal.v1',status:'CPU_PREPARATION_NOT_ADMITTED',
  execution_authorized:false,GPU_contexts_created:0,placement_actions_executed:0,model_forwards:0,
  producer:'Pinned modern-server parser/render, actual GGUF template, enable_thinking=false; exact binding pending CPU bridge',
  capacity:4096,KV_dtype:'F16',natural_response_cap:128,greedy:true,draft:false,
  paths:PATHS,dependency_gates:GATES,source_episodes:episodes,first_prompt_bindings:FIRST_PROMPTS,
  gate_policy:'Complete all18 requests and full raw qualification for each path before the next. Any contract/vector/KV/state mismatch stops the attempt; no candidate before the cold canonical bridge passes.',
  first_prompt_binding_rule:'SHA256 of UTF8(JSON.stringify(tokenIDs)+newline), saved N0 vocabulary tokenizer IDs. Actual pinned producer CPU bridge must match before these row reservations can be admitted.',
  controls:CONTROLS,control_token_fixtures:fixtures(),
  freezes:{producer_cpu_bridge_sha256:null,
   model_sha256:'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6',
   template_sha256:'57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361',tokenizer_sha256:null,
   operation_source_sha256:null,reference_executable_sha256:null,candidate_executable_sha256:null,
   actual_control_token_fixtures_sha256:crypto.createHash('sha256').update(JSON.stringify(fixtures())+'\n').digest('hex'),capture_profile_proof_sha256:null},
  window:{GPU_UUID:null,start_UTC:null,last_worker_start_UTC:null,native_end_UTC:null,delivery_UTC:null,
   proposed_total_seconds:18000,native_worker_timeout_seconds:600,placement_timeout_seconds:120,
   native_workers:8,placement_preflight_probes:2,worker_deployment_placements:8,placement_actions_proposed:10,
   resource_checks_and_gaps_seconds:1800,CPU_comparison_seconds:3600,export_restore_seconds:5400,
   clarification:'Hard watchdog proposal, not a measured GPU completion forecast. Absolute approved times remain unset.'},
  accounting:{planned_requests:72,failed_request_reserve:4,request_ceiling:76,
   planned_rows_ceiling:69354,aggregate_rows_ceiling:85738,
   class_requests:{NATURAL_FREE:24,NATURAL_CANONICAL_ORACLE:8,SCRIPTED_CONTROL_RESIDENT:30,SCRIPTED_CONTROL_ORACLE:10},
   allowance_status:'PROPOSED_NOT_APPROVED',quota_transfers:false,automatic_retries:false,
   failure_reserve_use:'Reserved consumption only; no automatic replacement/retry/diagnostic authorization'},
  storage:storage(),operations,
  memory:{one_native_worker_at_a_time:true,worker_RSS_hard_cap_bytes:24*1024**3,
   protected_system_available_bytes:24*1024**3,required_available_RAM_bytes:48*1024**3,
   raw_compare_stream_chunk_bytes:1024**2,single_layer_GPU_to_CPU_copy_bytes_max:32*1024**2,
   minimum_free_VRAM_bytes:2*1024**3,
   status:'PROPOSED_ENFORCED_CAPS_NOT_MEASURED_WORKSPACE_OR_ADMISSION',
   no_multiple_full_KV_in_RAM:true,no_context_recreation_for_cold_oracle_turns:true},
  admission_gaps:['Exact producer bridge and genuine parser/template CPU binding',
   'Native implementation of exact scripted controls and independently checked operation/receipt graph',
   'Separate C4096 sequential reference and strong rechunk native implementation/build',
   'Writer raw-state canonical layout and capture upper-bound proof',
   'Explicit finite per-class GPU request/row/placement approval',
   'Current allocated UUID, quiet window, RAM/VRAM/disk and controller lock approval'],
  N1b_authorized:false,N2_authorized:false,performance_claim_authorized:false};
}
function validateManifest(m,{requireAdmission=false}={}){
 assert.equal(m.schema,'hs.N1a.lifecycle.proposal.v1');assert.deepEqual(m.paths,PATHS);
 assert.deepEqual(m.dependency_gates,GATES);
 assert.equal(m.capacity,4096);assert.equal(m.KV_dtype,'F16');assert.equal(m.natural_response_cap,128);
 assert.equal(m.greedy,true);assert.equal(m.draft,false);
 assert.equal(m.source_episodes.length,4);assert.equal(m.controls.length,5);assert.equal(m.operations.length,72);
 assert.deepEqual(m.controls.map(x=>x.id),CONTROLS.map(x=>x.id));
 assert.deepEqual(m.control_token_fixtures,fixtures());
 assert.deepEqual(m.first_prompt_bindings,FIRST_PROMPTS);
 assert.deepEqual(m.operations,makeManifest(m.source_episodes).operations,'operation identity/path/mode/source/context instruction graph changed');
 assert.deepEqual(m.memory,makeManifest(m.source_episodes).memory,'RAM/VRAM/streaming safety proposal changed');
 const seen=new Set(),counts={};
 for(const x of m.operations){assert(!seen.has(x.id),'duplicate operation');seen.add(x.id);
  assert(PATHS.includes(x.path));safe(x.episode);assert(x.turn===0||x.turn===1);
  assert.equal(x.request_budget,1);safe(x.decoded_rows_max,1);assert(x.decoded_rows_max<=4096);assert.equal(x.absolute_per_request_row_ceiling,4096);
  assert.equal(x.role,x.turn===0?'CHARGED_SETUP_TURN':'CHARGED_CONTINUATION_TURN');
  if(x.control){assert.equal(x.source_root,null);assert.equal(x.source_user_message_id,null);assert(CONTROLS.some(c=>c.id===x.control));}
  else{assert.equal(x.source_root,m.source_episodes[x.episode].root);assert.equal(x.source_user_message_id,m.source_episodes[x.episode].user_message_ids[x.turn]);}
  assert.deepEqual(x.capture_phases,['POST_RECONCILE','POST_APPEND','TERMINAL']);
  assert.equal(x.response_cap,x.control?1:128);
  const expected=x.control?(x.path==='COLD_CANONICAL_ORACLE'?'SCRIPTED_CONTROL_ORACLE':'SCRIPTED_CONTROL_RESIDENT'):(x.path==='COLD_CANONICAL_ORACLE'?'NATURAL_CANONICAL_ORACLE':'NATURAL_FREE');
  assert.equal(x.class,expected);counts[x.class]=(counts[x.class]||0)+1;
  assert.equal(x.failure_policy,'STOP_ON_POST_FORWARD_ERROR_NO_AUTOMATIC_RETRY');
 }
 // Do not accept a superficially correct count with a duplicated/missing turn.
 for(const p of PATHS){for(let e=0;e<4;e++)for(let t=0;t<2;t++)assert(seen.has(`natural/${p}/${e}/${t}`));
  for(const c of CONTROLS)for(let t=0;t<2;t++)assert(seen.has(`control/${p}/${c.id}/${t}`));}
 assert.deepEqual(counts,m.accounting.class_requests);assert.equal(m.accounting.planned_requests,72);
 assert.equal(m.accounting.failed_request_reserve,4);assert.equal(m.accounting.request_ceiling,76);
 assert.equal(m.operations.reduce((n,x)=>n+x.decoded_rows_max,0),69354);
 assert.equal(m.accounting.planned_rows_ceiling,69354);assert.equal(m.accounting.aggregate_rows_ceiling,85738);
 assert.equal(m.accounting.automatic_retries,false);assert.equal(m.accounting.quota_transfers,false);
 assert.deepEqual(m.storage,storage());assert.equal(m.N1b_authorized,false);assert.equal(m.N2_authorized,false);
 assert.equal(m.window.placement_actions_proposed,10);assert.equal(m.window.worker_deployment_placements,m.window.native_workers);
 assert.equal(m.window.placement_preflight_probes,2);
 const nativeSeconds=m.window.native_workers*m.window.native_worker_timeout_seconds+
  m.window.placement_preflight_probes*m.window.placement_timeout_seconds+
  m.window.resource_checks_and_gaps_seconds;
 assert(nativeSeconds<=7200,'native/resource watchdog envelope exceeds two hours');
 assert(nativeSeconds+m.window.CPU_comparison_seconds+m.window.export_restore_seconds<=m.window.proposed_total_seconds);
 if(requireAdmission){
  // This prep validator deliberately cannot authorize a model operation. Even a
  // forged true flag cannot turn a CPU proposal into a native admission receipt.
  throw new Error('NOT_ADMITTED: implement and independently audit a successor admission validator; this CPU proposal never authorizes native execution');
 }
 assert.equal(m.execution_authorized,false);assert.equal(m.status,'CPU_PREPARATION_NOT_ADMITTED');
 return{status:'CPU_OPERATION_GRAPH_VALIDATED_NOT_ADMITTED',planned_requests:72,request_ceiling:76,
  rows_ceiling:85738,placement_actions_proposed:10,actual_model_forwards:0,actual_GPU_contexts:0};
}
module.exports={PATHS,CONTROLS,FIRST_PROMPTS,GATES,makeManifest,validateManifest,storage};
if(require.main===module){
 const fs=require('node:fs');const mode=process.argv[2];
 if(mode==='create'){const episodes=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
  const value=makeManifest(episodes);validateManifest(value);
  fs.writeFileSync(process.argv[4],JSON.stringify(value,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({status:'UNAPPROVED_PROPOSAL_WRITTEN',...value.accounting,storage:value.storage}));
 }else if(mode==='validate'){console.log(JSON.stringify(validateManifest(JSON.parse(fs.readFileSync(process.argv[3],'utf8')),{requireAdmission:process.argv.includes('--require-admission')})));}
 else throw new Error('Usage: node manifest.js create EPISODES.json FRESH_PROPOSAL.json | validate PROPOSAL.json [--require-admission]');
}
