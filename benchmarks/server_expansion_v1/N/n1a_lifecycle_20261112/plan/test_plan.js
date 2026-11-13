'use strict';
// Meaningful CPU preparation tests; all tensor bytes below are synthetic.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const {makeManifest,validateManifest,storage,FIRST_PROMPTS}=require('./manifest.js');
const {compareTensor,compareManifest,validateSnapshot,parseJSON,half}=require('./raw_compare.js');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex'),clone=x=>JSON.parse(JSON.stringify(x));
const root=fs.mkdtempSync(path.join(os.tmpdir(),'N1a-CPU-synthetic-'));
test.after(()=>fs.rmSync(root,{recursive:true,force:true}));
function tensor(name,bytes,dtype,shape,axes){fs.writeFileSync(path.join(root,name),bytes,{flag:'wx'});return{file:name,bytes:bytes.length,sha256:hash(bytes),dtype,shape,axes};}
const episodes=Object.keys(FIRST_PROMPTS).map(root=>({root,user_message_ids:[root,FIRST_PROMPTS[root].second_user_message_id]}));
test('operation graph counts every setup, continuation and oracle request, and keeps class budgets separate',()=>{
 const m=makeManifest(episodes),r=validateManifest(m);assert.equal(r.planned_requests,72);assert.equal(r.request_ceiling,76);assert.equal(r.rows_ceiling,85738);
 assert.equal(m.operations.filter(x=>!x.control).reduce((n,x)=>n+x.decoded_rows_max,0),68728);assert.equal(m.operations.filter(x=>x.control).reduce((n,x)=>n+x.decoded_rows_max,0),626);
 assert.equal(m.operations.filter(x=>x.role==='CHARGED_SETUP_TURN').length,36);assert.equal(m.operations.filter(x=>x.class==='NATURAL_FREE').length,24);
 assert.throws(()=>validateManifest(m,{requireAdmission:true}),/NOT_ADMITTED/);
});
test('missing or duplicated operation, quota mutation and changed control set fail closed',()=>{
 for(const mutate of [m=>m.operations.pop(),m=>m.operations[1].id=m.operations[0].id,m=>m.accounting.request_ceiling=60,m=>m.controls.pop(),m=>m.operations[0].source_user_message_id='favorable-replacement',m=>m.operations[0].path='REPEAT_RESIDENT_R',m=>m.operations[0].producer_mode='CANONICAL_INPUT_ORACLE_REPLAY']){const m=clone(makeManifest(episodes));mutate(m);assert.throws(()=>validateManifest(m));}
});
test('storage includes three active-prefix snapshot ceilings plus archive, restore and reserves',()=>{
 const s=storage();assert.equal(s.bytes_per_request_max,1897404416);assert.equal(s.raw_bytes_max,144202735616);assert.equal(s.free_bytes_required,551473155769);
 assert.equal(s.snapshots_per_request_max,3);assert.equal(s.profile_status,'CONDITIONAL_WRITER_BOUND_NOT_PROVEN');
});
test('JSON duplicate keys and malformed/trailing content are rejected',()=>{
 for(const s of ['{"shape":[],"shape":[1]}','{"a":{"x":1,"x":2}}','{"x":1}z','[1,]','{"x":01}'])assert.throws(()=>parseJSON(s));
 assert.deepEqual(parseJSON('{"a":[1,{"b":"escaped\\\"key"}]}'),{a:[1,{b:'escaped"key'}]});
});
test('full raw-byte equality, not digest equality alone, passes finite F16/F32 tensors',()=>{
 const b=Buffer.alloc(12);[1,0,-2].forEach((x,i)=>b.writeFloatLE(x,i*4));
 const a=tensor('equal32-a',b,'F32LE',[1,3],['row','vocabulary']),c=tensor('equal32-b',b,'F32LE',[1,3],['row','vocabulary']);
 const r=compareTensor(root,a,c);assert.equal(r.status,'PASS');assert.equal(r.bytes_compared,12);assert.equal(r.scalars_compared,3);assert.equal(r.hash_only_numerical_pass,false);
 const h=Buffer.from([0,0x3c,0,0xbc]),p=tensor('equal16-a',h,'F16LE',[1,2],['position','dimension']),q=tensor('equal16-b',h,'F16LE',[1,2],['position','dimension']);assert.equal(compareTensor(root,p,q).status,'PASS');assert.equal(half(0x3c00),1);
});
test('single scalar mismatch reports exact coordinate beyond stream chunk boundary',()=>{
 const a=Buffer.alloc(1048580),b=Buffer.from(a);b.writeFloatLE(2,1048576);
 const p=tensor('boundary-a',a,'F32LE',[262145],['vocabulary']),q=tensor('boundary-b',b,'F32LE',[262145],['vocabulary']);
 const r=compareTensor(root,p,q);assert.equal(r.status,'NUMERIC_FAIL');assert.equal(r.first_difference.byte_offset,1048576);assert.equal(r.first_difference.coordinate.vocabulary,262144);assert.equal(r.max_absolute_difference,2);assert.equal(r.bit_different_scalars,1);
});
test('positive and negative zero fail strict bytes even when numerical delta is zero',()=>{
 const a=Buffer.alloc(4),b=Buffer.alloc(4);b.writeFloatLE(-0,0);
 const p=tensor('signedzero-a',a,'F32LE',[1],['row']),q=tensor('signedzero-b',b,'F32LE',[1],['row']);const r=compareTensor(root,p,q);assert.equal(r.status,'NUMERIC_FAIL');assert.equal(r.max_absolute_difference,0);
});
test('identical NaN/Infinity is not a numerical pass',()=>{
 for(const [suffix,b,dtype]of [['nan32',Buffer.from([0,0,0xc0,0x7f]),'F32LE'],['inf16',Buffer.from([0,0x7c]),'F16LE']]){
  const p=tensor(suffix+'-a',b,dtype,[1],['row']),q=tensor(suffix+'-b',b,dtype,[1],['row']);const r=compareTensor(root,p,q);assert.equal(r.status,'NUMERIC_FAIL');assert(r.first_nonfinite);assert.equal(r.bit_different_scalars,0);
 }
});
test('transport mismatch, truncation, shape mismatch and outside paths fail closed',()=>{
 const b=Buffer.alloc(4),p=tensor('bad-a',b,'F32LE',[1],['row']),q=tensor('bad-b',b,'F32LE',[1],['row']);
 assert.throws(()=>compareTensor(root,p,{...q,sha256:'0'.repeat(64)}),/transport/);
 assert.throws(()=>compareTensor(root,p,{...q,bytes:8}),/shape/);
 assert.throws(()=>compareTensor(root,p,{...q,file:'../outside'}),/unsafe/);
 assert.equal(compareTensor(root,p,{...q,shape:[1,1],axes:['a','b']}).status,'CONTRACT_CONFLICT');
 fs.appendFileSync(path.join(root,q.file),Buffer.alloc(4));assert.throws(()=>compareTensor(root,p,q),/length/);
});
let captureCount=0;
function snapshot(phase='POST_APPEND'){
 const no=++captureCount,id='snapshot-'+no,head=phase==='RESET'?0:1,postTrim=phase==='POST_RECONCILE',term=phase==='TERMINAL';
 const vecRows=phase==='RESET'||postTrim?0:1;
 const kv=Buffer.alloc(36*8*head*128*2),vb=Buffer.alloc(vecRows*151936*4);
 const s={schema:'hs.N1a.raw-state.v1',run_id:'synthetic-run',operation_id:'synthetic-operation',context_id:id,path_kind:'RESIDENT',phase,
  cohort:'SCRIPTED_CONTROL',execution_mode:'SCRIPTED_STATE_CONTROL',event_ordinal:10,
  identity:Object.fromEntries(['contract_sha256','model_sha256','tokenizer_sha256','template_sha256','producer_sha256'].map(x=>[x,'a'.repeat(64)])),
  provenance:{executable_sha256:'b'.repeat(64),capture_writer_sha256:'c'.repeat(64)},
  canonical_ids:head?[100]:[],materialized_ids:head?[100]:[],logical_ids:head?(term?[100,101]:[100]):[],generated_ids:term?[101]:[],head,
  pending:term?{id:101,position:1}:null,frontier:{valid:head>0&&!postTrim,position:head>0&&!postTrim?0:null,owned:head>0&&!postTrim},
  requested_vector_positions:vecRows?[0]:[],owned_vector_ids:vecRows?[id+'-owned-row']:[],generation_cap:1,stop_reason:term?'CAP':null,tensors:{}};
 s.tensors.active_k=tensor(id+'-k',kv,'F16LE',[36,8,head,128],['layer','kv_head','position','dimension']);
 s.tensors.active_v=tensor(id+'-v',kv,'F16LE',[36,8,head,128],['layer','kv_head','position','dimension']);
 s.tensors.vectors=tensor(id+'-vec',vb,'F32LE',[vecRows,151936],['requested_row','vocabulary']);
 return s;
}
function desc(s){const file='capture-'+(++captureCount)+'.json',b=Buffer.from(JSON.stringify(s));fs.writeFileSync(path.join(root,file),b,{flag:'wx'});return{file,sha256:hash(b),run_id:s.run_id,operation_id:s.operation_id,executable_sha256:s.provenance.executable_sha256};}
function compare(a,b){return compareManifest(root,{schema:'hs.N1a.raw-comparisons.v1',comparisons:[{id:'synthetic-pair',scope:'ALIGNED_STATE',left:desc(a),right:desc(b)}]}).results[0];}
test('aligned postappend and terminal capture compare every active layer/head and full vocabulary',()=>{
 for(const phase of ['POST_APPEND','TERMINAL','RESET']){const a=snapshot(phase),b=snapshot(phase);validateSnapshot(a);assert.equal(compare(a,b).status,'PASS');}
});
test('wrong producer/canonical input is contract conflict, not GPU/numerical failure',()=>{
 const a=snapshot(),b=snapshot();b.identity.producer_sha256='d'.repeat(64);assert.equal(compare(a,b).status,'CONTRACT_CONFLICT');
});
test('metadata JSON object key order does not change the semantic comparison contract',()=>{
 const a=snapshot(),b=snapshot();b.identity=Object.fromEntries(Object.entries(b.identity).reverse());assert.equal(compare(a,b).status,'PASS');
});
test('different terminal sampled token is state failure under same input contract',()=>{
 const a=snapshot('TERMINAL'),b=snapshot('TERMINAL');b.generated_ids=[102];b.logical_ids=[100,102];b.pending.id=102;assert.equal(compare(a,b).status,'STATE_FAIL');
});
test('cold q1 prefix alignment compares active KV but never claims invalid resident frontier equivalence',()=>{
 const a=snapshot('POST_RECONCILE'),b=snapshot('POST_RECONCILE');b.path_kind='COLD_ORACLE';b.execution_mode='SCRIPTED_CONTROL_ORACLE';b.frontier={valid:true,position:0,owned:true};
 b.requested_vector_positions=[0];b.owned_vector_ids=['cold-prefix-owned'];b.tensors.vectors=tensor('cold-prefix-extra-vector',Buffer.alloc(151936*4),'F32LE',[1,151936],['requested_row','vocabulary']);
 const r=compare(a,b);assert.equal(r.status,'PASS');assert.match(r.scope,/ACTIVE_KV_ONLY/);assert.equal(r.tensors.vectors,undefined);
});
test('unmaterialized pending terminal token, complete output mask and EOG precedence are checked',()=>{
 for(const mutate of [s=>s.head=2,s=>s.pending.position=0,s=>s.requested_vector_positions=[],s=>s.generated_ids=[151645],s=>s.frontier.owned=false]){const s=snapshot('TERMINAL');mutate(s);assert.throws(()=>validateSnapshot(s));}
});
function jsonDesc(name,value){const b=Buffer.from(JSON.stringify(value));fs.writeFileSync(path.join(root,name),b,{flag:'wx'});return{file:name,sha256:hash(b)};}
function ownershipCase(suffix,mutateAfter=false){
 const s=snapshot(),originSnapshot=desc(s),id=s.owned_vector_ids[0],next='continuation-'+suffix;
 const a=Buffer.alloc(151936*4),b=Buffer.from(a);if(mutateAfter)b.writeFloatLE(1,151935*4);
 const p=tensor('ownership-'+suffix+'-a',a,'F32LE',[1,151936],['requested_row','vocabulary']),q=tensor('ownership-'+suffix+'-b',b,'F32LE',[1,151936],['requested_row','vocabulary']);
 const origin={snapshot:originSnapshot,ownership_id:id,requested_row_index:0,vector_position:0,next_operation_id:next};
 const e={schema:'hs.N1a.owned-vector-event.v1',run_id:s.run_id,context_id:s.context_id,source_operation_id:s.operation_id,next_operation_id:next,
  source_snapshot_sha256:originSnapshot.sha256,source_requested_row_index:0,source_vector_position:0,ownership_id:id,caller_owned:true,capture_writer_sha256:s.provenance.capture_writer_sha256};
 const before_event=jsonDesc('owned-before-'+suffix+'.json',{...e,phase:'BEFORE_NEXT_MUTATION',event_ordinal:11,tensor:p});
 const after_event=jsonDesc('owned-after-'+suffix+'.json',{...e,phase:'AFTER_NEXT_MUTATION',event_ordinal:14,tensor:q});
 const mutation_receipt=jsonDesc('mutation-'+suffix+'.json',{schema:'hs.N1a.mutation-receipt.v1',run_id:s.run_id,context_id:s.context_id,source_operation_id:s.operation_id,operation_id:next,
  begin_event_ordinal:12,end_event_ordinal:13,actual_decode_calls:1,actual_model_rows:1,status:'COMPLETE'});
 return{id:'owned-copy-'+suffix,scope:'OWNED_VECTOR_STABILITY',origin,before_event,after_event,mutation_receipt};
}
test('ownership check binds source full row/run/context to actual before/decode/after receipts',()=>{
 const c=ownershipCase('valid');const r=compareManifest(root,{schema:'hs.N1a.raw-comparisons.v1',comparisons:[c]});assert.equal(r.status,'PASS');assert.equal(r.results[0].source_row_bytes_compared,151936*4);
});
test('owned-vector before/after byte mutation fails stability check',()=>{
 const c=ownershipCase('mutated',true),r=compareManifest(root,{schema:'hs.N1a.raw-comparisons.v1',comparisons:[c]});assert.equal(r.status,'FAIL');assert.equal(r.results[0].first_difference.coordinate.vocabulary,151935);
});
test('unbound arbitrary or empty raw tensor cannot pass ownership qualification',()=>{
 const p=tensor('ownership-unbound',Buffer.alloc(0),'F32LE',[0,151936],['requested_row','vocabulary']);
 const r=compareManifest(root,{schema:'hs.N1a.raw-comparisons.v1',comparisons:[{id:'unbound',scope:'OWNED_VECTOR_STABILITY',origin:{ownership_id:'arbitrary'},left:p,right:p}]});assert.equal(r.results[0].status,'INVALID_CAPTURE');
});
test('prototype-filled sparse token and coordinate arrays are rejected',()=>{
 const s=snapshot(),arr=new Array(1);Object.setPrototypeOf(arr,{0:100,[Symbol.iterator]:Array.prototype[Symbol.iterator]});s.canonical_ids=arr;assert.throws(()=>validateSnapshot(s),/sparse\/inherited/);
 const r=snapshot();delete r.requested_vector_positions[0];Object.setPrototypeOf(r.requested_vector_positions,{0:0,[Symbol.iterator]:Array.prototype[Symbol.iterator]});assert.throws(()=>validateSnapshot(r),/sparse\/inherited/);
});
test('each fixed raw-token control counts setup plus pending/cap continuation and empty reset',()=>{
 const {fixtures}=require('./control_fixtures.js');for(const f of fixtures()){
  assert.equal(f.requests.length,2);assert.equal(f.requests[0].expected.generated_decoded_rows,0);assert.equal(f.requests[1].expected.generated_decoded_rows,0);
  assert.equal(f.requests[1].expected.materialized_head,f.requests[1].canonical_input_ids.length);assert.equal(f.context_reset.model_requests,0);
  assert.equal(f.requests[1].expected.fresh_replay_ids.length,f.requests[1].canonical_input_ids.length-f.requests[1].expected.keep);
  const old=f.requests[0].expected.logical_ids,next=f.requests[1].canonical_input_ids;let lcp=0;while(lcp<old.length&&lcp<next.length&&old[lcp]===next[lcp])lcp++;
  let keep=Math.min(lcp,f.requests[0].expected.materialized_head);if(keep===next.length)keep--;
  if(f.requests[1].fault_injection)keep=0;assert.equal(keep,f.requests[1].expected.keep);
 }
});
function retentionCase(suffix,mutated=false){
 const old=snapshot('TERMINAL'),next=snapshot('POST_RECONCILE');next.context_id=old.context_id;next.operation_id='continuation-'+suffix;next.event_ordinal=20;next.canonical_ids=[100,101,102];
 if(mutated){const p=path.join(root,next.tensors.active_k.file),b=fs.readFileSync(p);b.writeUInt16LE(0x3c00,b.length-2);fs.writeFileSync(p,b);next.tensors.active_k.sha256=hash(b);}
 const previous=desc(old),current=desc(next),receipt={schema:'hs.N1a.reconcile-receipt.v1',run_id:old.run_id,context_id:old.context_id,source_operation_id:old.operation_id,operation_id:next.operation_id,
  previous_snapshot_sha256:previous.sha256,current_snapshot_sha256:current.sha256,mode:'DIRECT_APPEND',fallback_reason:null,actual_head_before:1,actual_keep:1,actual_model_rows_before_append:0,old_frontier_invalidated:true,
  old_pending_id:101,pending_disposition:'REPLAY_OLD_PENDING_ONCE_AT_CANONICAL_POSITION'};
 return{id:'retained-prefix-'+suffix,scope:'PREFIX_RETENTION',previous,current,transition_receipt:jsonDesc('reconcile-'+suffix+'.json',receipt)};
}
test('same live-context retained KV is compared to prior terminal prefix with pending replay rule',()=>{
 const c=retentionCase('good'),r=compareManifest(root,{schema:'hs.N1a.raw-comparisons.v1',comparisons:[c]});assert.equal(r.status,'PASS');assert.equal(r.results[0].keep,1);assert.equal(r.results[0].tensors.active_k.bytes_compared,36*8*128*2);
});
test('retained prefix difference reports last layer/KVhead/position/dimension',()=>{
 const c=retentionCase('bad',true),r=compareManifest(root,{schema:'hs.N1a.raw-comparisons.v1',comparisons:[c]});assert.equal(r.status,'FAIL');assert.deepEqual(r.results[0].tensors.active_k.first_difference.coordinate,{layer:35,kv_head:7,position:0,dimension:127});
});
test('reset verifies empty metadata and zero-length raw files, not an additional forward',()=>{
 const s=snapshot('RESET'),r=compareManifest(root,{schema:'hs.N1a.raw-comparisons.v1',comparisons:[{id:'reset',scope:'RESET_EMPTY_CHECK',capture:desc(s)}]});assert.equal(r.status,'PASS');assert.equal(r.results[0].head,0);assert.equal(r.results[0].tensors.active_k.bytes_compared,0);
});
