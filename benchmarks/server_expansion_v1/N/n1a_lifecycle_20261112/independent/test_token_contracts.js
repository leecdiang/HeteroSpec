'use strict';
// Positive and negative tests execute exactly the pure functions imported by
// independentcheck.js. Candidate comparisons below are additional cross-checks.
const assert=require('node:assert/strict');
const checker=require('./token_contracts.js');
const candidate=require('../contracts.js');
const tests=[];
function test(name,body){tests.push([name,body]);}
test('checker B counts canonical suffix from materialized head, including pending',()=>{
  const b=checker.appendOnlyRepair([10,11],1,[10,11,12],{n_vocab:13});
  assert.equal(b.compatible,true);assert.equal(b.lcp,2);
  assert.deepEqual(b.replay_ids,[11,12]);assert.equal(b.replayed_rows,2);
  assert.equal(b.pending_id,11);assert.equal(b.requires_frontier_refresh,false);
});
test('checker actual initial, full-prefix and partial-prefix paths have independent expected answers',()=>{
  const cases=[
    {old:[],m:0,next:[10,11],prefix:0,compatible:true,append:[10,11],retain:0,replay:[10,11]},
    {old:[10,11],m:2,next:[10,11,12],prefix:2,compatible:true,append:[12],retain:2,replay:[12]},
    {old:[10,11],m:1,next:[10,11,12],prefix:2,compatible:true,append:[11,12],retain:1,replay:[11,12]},
    {old:[10,11,12],m:2,next:[10,13,14],prefix:1,compatible:false,append:null,retain:1,replay:[13,14]},
    {old:[10,11,12],m:3,next:[10,11],prefix:2,compatible:false,append:null,retain:1,replay:[11]},
    {old:[10,11],m:1,next:[10,11],prefix:2,compatible:true,append:[11],retain:1,replay:[11]},
    {old:[10,11],m:2,next:[10,11],prefix:2,compatible:true,append:[],retain:1,replay:[11]}
  ];
  for(const c of cases){
    const b=checker.appendOnlyRepair(c.old,c.m,c.next,{n_vocab:20});
    const r=checker.canonicalRepair(c.old,c.m,c.next,{n_vocab:20});
    assert.equal(checker.prefixLength(c.old,c.next,{n_vocab:20}),c.prefix);
    assert.equal(b.lcp,c.prefix);assert.equal(b.compatible,c.compatible);
    assert.deepEqual(b.replay_ids,c.append);assert.equal(b.replayed_rows,c.append===null?null:c.append.length);
    assert.equal(r.retain,c.retain);assert.deepEqual(r.replay_ids,c.replay);
    assert.deepEqual(r.reconstructed_ids,c.next);
    assert.equal(r.can_sample_before_execution,false);assert.equal(b.can_sample_before_execution,false);
    const p=candidate.reconcile(c.old,c.m,c.next,{n_vocab:20,outputCap:1});
    assert.equal(p.lcp_tokens,r.lcp);assert.equal(p.retained_tokens,r.retain);
    assert.deepEqual(p.append_ids,r.replay_ids);assert.equal(p.pending_disposition,r.pending_disposition);
  }
});
test('checker distinguishes zero new append from required owned-frontier refresh',()=>{
  const b=checker.appendOnlyRepair([10,11],2,[10,11]);
  assert.equal(b.replayed_rows,0);assert.equal(b.requires_frontier_refresh,true);
  const r=checker.canonicalRepair([10,11],2,[10,11]);
  assert.equal(r.fresh_last_token_replay,true);assert.equal(r.trimmed_rows,1);
  assert.deepEqual(r.replay_ids,[11]);assert.equal(r.can_sample_before_execution,false);
});
test('independent checker validators reject sparse/inherited/undefined and every invalid integer class',()=>{
  const inherited=new Array(1);Object.setPrototypeOf(inherited,Object.assign(Object.create(Array.prototype),{0:1}));
  const badInputs=[Array(1),[1,,3],inherited,[undefined],[null],[-1],[2.5],[NaN],[Infinity],
    [Number.MAX_SAFE_INTEGER+1],[true],['1']];
  for(const bad of badInputs){
    assert.throws(()=>checker.validateTokenIDs(bad));
    assert.throws(()=>checker.prefixLength(bad,[1]));assert.throws(()=>checker.prefixLength([1],bad));
    assert.throws(()=>checker.canonicalRepair(bad,0,[1]));assert.throws(()=>checker.canonicalRepair([],0,bad));
    assert.throws(()=>checker.appendOnlyRepair(bad,0,[1]));assert.throws(()=>checker.appendOnlyRepair([],0,bad));
  }
});
test('bound vocabulary and logical-state failures are rejected in actual checker helpers',()=>{
  assert.deepEqual(checker.validateTokenIDs([0,12],{n_vocab:13}),[0,12]);
  for(const n_vocab of [null,0,-1,1.5,'13',Infinity,Number.MAX_SAFE_INTEGER+1]){
    assert.throws(()=>checker.validateTokenIDs([],{n_vocab}));
    assert.throws(()=>checker.prefixLength([],[],{n_vocab}));
  }
  for(const f of [
    ()=>checker.prefixLength([1,5],[2,3],{n_vocab:5}),
    ()=>checker.appendOnlyRepair([1,2],0,[1,2,3]),
    ()=>checker.canonicalRepair([1],2,[1]),
    ()=>checker.canonicalRepair([1],1,[]),
    ()=>checker.canonicalRepair([1,2],1,[1,2],{pendingId:1}),
    ()=>checker.canonicalRepair([1,2],1,[1,2],{pendingId:undefined}),
    ()=>checker.canonicalRepair([1,2],1,[1,2],{n_vocab:2}),
    ()=>checker.appendOnlyRepair([1,2],1,[1,3],{n_vocab:3})
  ])assert.throws(f);
});
test('independent valid plans preserve frozen caller inputs and do not create native observations',()=>{
  const old=Object.freeze([10,11]),next=Object.freeze([10,11,12]);
  const r=checker.canonicalRepair(old,1,next,{pendingId:11,n_vocab:13});
  assert.deepEqual(old,[10,11]);assert.deepEqual(next,[10,11,12]);
  assert.deepEqual(r.reconstructed_ids,next);assert.equal(r.can_sample_before_execution,false);
});
let failures=0;
for(const [name,body]of tests){try{body();console.log('PASS '+name);}catch(error){failures++;console.error('FAIL '+name+'\n'+error.stack);}}
console.log(JSON.stringify({tests:tests.length,failures,model_forwards:0,GPU_requests:0,tokenizer_calls:0,native_contexts:0,scope:'Actual independent checker-helper branch tests and candidate cross-checks'}));
if(failures)process.exitCode=1;
