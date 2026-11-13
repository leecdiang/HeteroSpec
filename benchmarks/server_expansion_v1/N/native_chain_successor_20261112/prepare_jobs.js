'use strict';
// Pure CPU, finite job templates. Does not open a socket, create a ledger,
// initialize any backend/model/context, or start a native worker.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const {validateManifest}=require('../n1a_lifecycle_20261112/plan/manifest.js');
const PARENT='87ea17971642f65468678cee8477505b9956611a';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function prepare(proposal,n0){
 validateManifest(proposal);assert.equal(sha(Buffer.from(JSON.stringify(proposal,null,2)+'\n')),'bf00a976a5f5385bd818bd58bdfcaa575e49f9548fee615320ed9b1d86194892','whole frozen #226 proposal identity');
 const tokenBytes=fs.readFileSync(path.join(n0,'TOKENIZER_OUTPUT.jsonl'));assert.equal(sha(tokenBytes),'23e812286a06ce6e067eb89648221b4348daeb1d3b5722aab780d09c56288350','exact saved tokenizer input');
 const tokens=new Map();for(const line of tokenBytes.toString('utf8').trim().split('\n')){const r=JSON.parse(line);if(r.task_id)tokens.set(r.task_id,r.prompt_ids);}
 const cfg={schema:'hs.N1chain.execution-template.v1',status:'CPU_TEMPLATE_NOT_ADMITTED',parent_PR226:PARENT,
  execution_authorized:false,model_forwards:0,request_limit:76,row_limit:85738,
  planned_requests:72,planned_rows:69354,failure_reserve_requests:4,failure_reserve_rows:16384,
  initializations:{backend_inits:10,models:10,model_contexts:10,placements:10},
  counts_scope:'Two preflight deployments and eight worker deployments; loader placement reserved before exec, worker verifies same reservation without charging twice',
  role_order:['RESIDENT_R','REPEAT_RESIDENT_R','COLD_CANONICAL_ORACLE','STRONG_WHOLE_RECHUNK_LOOP4'],
  stage_gate:'Repeat R then strict cold canonical bridge must pass full raw comparisons before any of eighteen strong requests; identity/alignment conflict stops before numerical claim',
  request_rows:Object.fromEntries(proposal.operations.map(o=>[o.id,o.decoded_rows_max])),
  global_accounting:{ledger:'ONE_CANONICAL_GLOBAL_LEDGER_FOR_THIS_SUCCESSOR',mode:'CPU_MOCK_ONLY_IMPLEMENTATION_TESTED_NOT_NATIVE_AUTHORITY',socket_path:null,manifest_sha256:null,
   launch_clients:[],worker_clients:[],no_worker_local_ledger:true,no_existing_STATE_restart:true,no_reconnect_retry:true},
  jobs:[],late_bindings:['Explicit finite GPU approval; current concrete ProductionGate cannot admit execution','Allocated GPU UUID and exact CUDA_VISIBLE_DEVICES equality','Absolute quiet window, last-worker cutoff, safety and memory enforcement','Frozen own executable/source/writer/producer digests','Original modules and loaded-library identity certificate','Single global broker manifest fingerprint and protected socket','Actual resident R canonical/retained-head/full-raw certificate for subsequent stages'],
  no_old_budget_borrowing:true,N1b:false,N2:false,performance:false};
 const control=new Map(proposal.control_token_fixtures.map(c=>[c.id,c]));
 for(const role of cfg.role_order)for(const cohort of ['NATURAL','CONTROL']){
  const worker=role+'/'+cohort,placement='deploy/'+worker,episodes=[];
  const ops=proposal.operations.filter(o=>o.path===role&&Boolean(o.control)===(cohort==='CONTROL'));
  const ids=[...new Set(ops.map(o=>o.episode))];
  for(const e of ids){const pair=ops.filter(o=>o.episode===e).sort((a,b)=>a.turn-b.turn);assert.equal(pair.length,2);
   episodes.push({episode_id:cohort==='NATURAL'?proposal.source_episodes[e].root:pair[0].control,
    kind:cohort==='NATURAL'?'NATURAL_FIXED_USER_CONTINUATION':'SCRIPTED_RAW_TOKEN_CONTROL',
    operations:pair.map(op=>{
     const x={id:op.id,cap:op.response_cap,reserved_rows:op.decoded_rows_max};
     if(op.control){const c=control.get(op.control),r=c.requests[op.turn];x.canonical_ids=r.canonical_input_ids;x.forced_terminal_ids=[r.forced_terminal_id];
      if(r.fault_injection)x.caller_fault=r.fault_injection==='TRIM_CAPABILITY_UNSUPPORTED'?'UNSUPPORTED_BEFORE_CALL':'FAILED_BEFORE_MUTATION';
      x.reference_retained_head=op.turn===0?0:r.expected.keep;
     }else{x.user=proposal.source_episodes[e].users[op.turn];x.user={role:'user',content:x.user.content};
      if(op.turn===0)x.expected_canonical_ids=tokens.get('prompt:'+proposal.source_episodes[e].root);
      if(role==='COLD_CANONICAL_ORACLE'){x.canonical_ids=null;x.reference_retained_head=null;x.unresolved='ACTUAL_R_CERTIFICATE_REQUIRED_NOT_SUPPLIED_HISTORY';}
      else if(role!=='RESIDENT_R')x.expected_canonical_ids=op.turn===0?x.expected_canonical_ids:null;
     }return x;
    })});
  }
  const caps=Object.fromEntries(ops.map(o=>[o.id,o.response_cap])),faults={};for(const e of episodes)for(const op of e.operations)if(op.caller_fault)faults[op.id]=op.caller_fault;
  const job={schema:'hs.N1chain.native-job-template.v1',execution_authorized:false,run_id:null,worker_id:worker,role,placement_id:placement,gpu_uuid:null,
   model_path:null,identity:{contract_sha256:null,model_sha256:'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6',tokenizer_sha256:null,template_sha256:'57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361',producer_sha256:null},
   source_sha256:null,writer_sha256:null,executable_sha256:null,capture_root:null,accounting_socket:null,accounting_manifest_sha256:null,
   operation_caps:caps,operation_faults:faults,episodes};
  cfg.jobs.push(job);
  cfg.global_accounting.launch_clients.push({id:'launch/'+worker,role:'LAUNCH_ONLY',request_ids:[],deployment_ids:[placement]});
  cfg.global_accounting.worker_clients.push({id:worker,role:'WORKER',request_ids:ops.map(o=>o.id),deployment_ids:[placement]});
 }
 cfg.preflight_templates=['R','loop4'].map((role,i)=>({id:'preflight/'+role,placement_id:'preflight/'+role,model_requests:0,rows:0,backend_inits:1,model_loads:1,contexts:1,
  resource_probe_status:'NOT_IMPLEMENTED_AS_LIVE_GPU_PROBE_NOT_RUN',native_factory_compiled:true,requirements:'Separate approval, pre-exec placement reservation, same exact model/C4096/F16 profile; never use a forward as an initialization test',source_binary:role,timeout_seconds:120}));
 assert.equal(cfg.jobs.length,8);assert.equal(cfg.jobs.reduce((s,j)=>s+j.episodes.reduce((n,e)=>n+e.operations.length,0),0),72);
 assert.equal(Object.values(cfg.request_rows).reduce((s,n)=>s+n,0),69354);
 return cfg;
}
if(require.main===module){const [p,n0,out]=process.argv.slice(2);assert(p&&n0&&out,'node prepare_jobs.js PROPOSAL N0_RESTORE FRESH_OUTPUT');const b=fs.readFileSync(p),result=prepare(JSON.parse(b),n0);result.proposal_bytes_sha256=sha(b);fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:result.status,workers:8,requests:72,rows:69354,approval:false}));}
module.exports={prepare};
