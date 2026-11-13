'use strict';
// Tests below use invented metadata only, and never call a native library or
// claim the synthetic status objects certify any native/GPU result.
const test=require('node:test'),assert=require('node:assert/strict');
const {makeManifest,FIRST_PROMPTS}=require('./manifest.js');
const {expectedGraph,validateListedCoverage,validateActualHeaders,validateResults,digest}=require('./coverage.js');
const clone=x=>JSON.parse(JSON.stringify(x));
const proposal=makeManifest(Object.keys(FIRST_PROMPTS).map(root=>({root,user_message_ids:[root,FIRST_PROMPTS[root].second_user_message_id]})));
function submitted(){
 const graph=expectedGraph(proposal),run_id='SYNTHETIC_METADATA_TEST_NO_NATIVE_RUN';
 const descriptor=b=>({operation_id:b.operation_id,phase:b.phase,run_id,
  file:'synthetic/'+digest([b.operation_id,b.phase])+'.json',sha256:'a'.repeat(64),executable_sha256:'b'.repeat(64)});
 const receipt=id=>({file:'synthetic/receipt-'+digest(id)+'.json',sha256:'c'.repeat(64)});
 const comparisons=graph.checks.map(e=>{const c={id:e.id,scope:e.scope,bindings:clone(e.bindings)};
  if(e.scope==='ALIGNED_STATE'){c.left=descriptor(e.bindings.left);c.right=descriptor(e.bindings.right);}
  else if(e.scope==='PREFIX_RETENTION'){c.previous=descriptor(e.bindings.previous);c.current=descriptor(e.bindings.current);c.transition_receipt=receipt(e.id);}
  else if(e.scope==='OWNED_VECTOR_STABILITY'){
   c.origin={snapshot:descriptor(e.bindings.source),next_operation_id:e.bindings.mutation_operation_id,
    requested_row_index:0,vector_position:0,ownership_id:'SYNTHETIC_OWNED_ID_NO_NATIVE_COPY'};
   c.before_event=receipt(e.id+'before');c.after_event=receipt(e.id+'after');c.mutation_receipt=receipt(e.id+'mutation');
  }else c.capture=descriptor(e.bindings.capture);return c;});
 return{schema:'hs.N1a.raw-comparisons.v1',required_graph_sha256:digest(graph),run_id,comparisons};
}
function syntheticReport(s){return{schema:'hs.N1a.raw-comparison-report.v1',scope:'CPU_REPLAY_OF_PROVIDED_RAW_BYTES_NOT_INDEPENDENT_GPU_EXECUTION',
 comparison_manifest_normalized_sha256:digest(s),status:'PASS',
 results:s.comparisons.map(c=>({id:c.id,input_scope:c.scope,bindings:clone(c.bindings),status:'PASS'}))};}
test('261 required checks exclude cold prior-KV retention and bind terminal last frontier ownership',()=>{
 const g=expectedGraph(proposal);assert.deepEqual(g.counts,{ALIGNED_STATE:162,PREFIX_RETENTION:27,OWNED_VECTOR_STABILITY:36,RESET_EMPTY_CHECK:36});
 assert.equal(g.checks.length,261);assert.equal(new Set(g.checks.map(c=>c.id)).size,261);
 for(const c of g.checks.filter(c=>c.scope==='PREFIX_RETENTION'))assert(!c.bindings.previous.operation_id.includes('/COLD_CANONICAL_ORACLE/'));
 for(const c of g.checks.filter(c=>c.scope==='OWNED_VECTOR_STABILITY')){assert.equal(c.bindings.source.phase,'TERMINAL');assert.equal(c.bindings.source.row_selector,'LAST_REQUESTED_ROW');}
 assert.equal(g.admission_authorized,false);assert.equal(g.model_forwards,0);
});
test('complete listed metadata bindings are a prep result, never native qualification or approval',()=>{
 const s=submitted(),r=validateListedCoverage(proposal,s);assert.equal(r.status,'COMPLETE_PROVIDED_BINDINGS_ONLY');assert.equal(r.required_checks,261);assert.equal(r.unique_captures,252);
 assert.equal(r.native_qualification,'NOT_ESTABLISHED');assert.equal(r.admission_authorized,false);
});
test('one missing or duplicated check is rejected, including a duplicate hiding a missing entry',()=>{
 const a=submitted();a.comparisons.pop();assert.throws(()=>validateListedCoverage(proposal,a),/missing\/extra/);
 const b=submitted();b.comparisons[b.comparisons.length-1]=clone(b.comparisons[0]);assert.throws(()=>validateListedCoverage(proposal,b),/duplicate/);
});
test('relabelled scope, cross-operation/path/phase and nonterminal ownership source are rejected',()=>{
 for(const mutate of [s=>s.comparisons[0].scope='RESET_EMPTY_CHECK',s=>s.comparisons[0].left.operation_id=s.comparisons[0].right.operation_id,
  s=>s.comparisons[0].left.phase='TERMINAL',s=>s.comparisons[0].bindings.right.operation_id='different-path',
  s=>s.comparisons.find(c=>c.scope==='OWNED_VECTOR_STABILITY').origin.snapshot.phase='POST_APPEND']){
  const s=submitted();mutate(s);assert.throws(()=>validateListedCoverage(proposal,s));
 }
});
test('the same reference operation/phase cannot be replaced by a different capture in another pair',()=>{
 const s=submitted(),first=s.comparisons[0],same=s.comparisons.find((c,i)=>i>0&&c.scope==='ALIGNED_STATE'&&c.left.operation_id===first.left.operation_id&&c.left.phase===first.left.phase);
 same.left.sha256='d'.repeat(64);assert.throws(()=>validateListedCoverage(proposal,s),/different source captures/);
});
test('results require every frozen ID, typed scope and semantic pair bindings',()=>{
 const s=submitted(),r=syntheticReport(s),v=validateResults(proposal,s,r);assert.equal(v.raw_replay_status,'PASS');assert.equal(v.admission_authorized,false);assert.match(v.native_qualification,/NOT_ESTABLISHED/);
 for(const mutate of [r=>r.results.pop(),r=>r.results[1].id=r.results[0].id,r=>r.results[0].input_scope='PREFIX_RETENTION',r=>r.results[0].bindings.left.operation_id='other',r=>r.comparison_manifest_normalized_sha256='0'.repeat(64)]){
  const bad=syntheticReport(s);mutate(bad);assert.throws(()=>validateResults(proposal,s,bad));
 }
 const failed=syntheticReport(s);failed.results[0].status='NUMERIC_FAIL';failed.status='FAIL';assert.equal(validateResults(proposal,s,failed).raw_replay_status,'FAIL');
});
test('synthetic complete metadata cannot pass actual-header/raw verification without real files',()=>{
 assert.throws(()=>validateActualHeaders('/tmp',proposal,submitted()));
});
