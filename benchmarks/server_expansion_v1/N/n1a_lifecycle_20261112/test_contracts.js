'use strict';
// Synthetic contract invariants only. No tokenizer, model or GPU invocation.
const assert=require('assert/strict');
const {QWEN_EOG_IDS,classifyTerminal,reconcile,schedule,prefixLength,validateTokenIDs}=require('./contracts');
const tests=[];
function test(name,fn){tests.push([name,fn]);}

test('all actual Qwen EOG IDs remain actual terminal IDs',()=>{
  assert.deepEqual(QWEN_EOG_IDS,[128247,151643,151645,151662,151663,151664]);
  for(const eog of QWEN_EOG_IDS){
    const r=classifyTerminal([7,eog],'EOG');
    assert.equal(r.pending_id,eog);assert.equal(r.materialized_generated_rows,1);
    assert.equal(r.artificial_EOS_added,false);assert.deepEqual(r.generated_ids,[7,eog]);
  }
  assert.equal(classifyTerminal([151645],'EOG').materialized_generated_rows,0);
});
test('CAP keeps last actual generated token without adding EOS',()=>{
  const r=classifyTerminal(Array(128).fill(7),'CAP');
  assert.equal(r.pending_id,7);assert.equal(r.generated_tokens,128);
  assert.equal(r.materialized_generated_rows,127);assert.equal(r.generated_ids.includes(151645),false);
  assert.equal(classifyTerminal([4],'CAP',{outputCap:1}).pending_id,4);
});
test('stop violations fail instead of inventing EOS or truncating',()=>{
  assert.throws(()=>classifyTerminal([5],'EOG'));
  assert.throws(()=>classifyTerminal([151645,7],'CAP',{outputCap:2}));
  assert.throws(()=>classifyTerminal([7,151645],'CAP',{outputCap:2}));
  assert.throws(()=>classifyTerminal([7],'CAP',{outputCap:2}));
  assert.throws(()=>classifyTerminal(Array(129).fill(7),'CAP'));
});
test('pending token is replayed once at unchanged logical position',()=>{
  const old=[1,2,151645],next=[1,2,151645,3,4];
  const r=reconcile(old,2,next,{pendingId:151645});
  assert.equal(r.mode,'DIRECT_APPEND');assert.equal(r.retained_tokens,2);
  assert.deepEqual(r.append_ids,[151645,3,4]);
  assert.equal(r.pending_disposition,'REPLAY_ONCE_AT_ITS_CANONICAL_POSITION');
  assert.deepEqual(r.reconstructed_canonical_ids,next);
});
test('CAP pending token is not replaced with a synthetic EOG',()=>{
  const r=reconcile([1,2,7],2,[1,2,7,151645,198,4],{pendingId:7});
  assert.equal(r.append_ids[0],7);assert.equal(r.append_ids[1],151645);
  assert.equal(r.pending_disposition,'REPLAY_ONCE_AT_ITS_CANONICAL_POSITION');
});
test('canonical stub mismatch trims/replays while preserving exact canonical input',()=>{
  const old=[1,2,151667,271,151668,271,40,151645];
  const next=[1,2,40,151645,198,4];
  const r=reconcile(old,7,next,{pendingId:151645});
  assert.equal(r.mode,'LCP_TRIM_REPLAY');assert.equal(r.lcp_tokens,2);
  assert.equal(r.retained_tokens,2);assert.equal(r.trim_materialized_rows,5);
  assert.deepEqual(r.append_ids,next.slice(2));assert.deepEqual(r.reconstructed_canonical_ids,next);
  assert.equal(r.pending_disposition,'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX');
});
test('matching token value after earlier mismatch does not preserve old pending identity',()=>{
  const r=reconcile([1,9,151645],2,[1,8,151645,4],{pendingId:151645});
  assert.equal(r.lcp_tokens,1);
  assert.equal(r.pending_disposition,'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX');
});
test('unsupported trim and declared trim failure use common full rebuild',()=>{
  for(const options of [{trimSupported:false},{trimSucceeded:false},{cacheValid:false}]){
    const r=reconcile([1,2,3],3,[1,7,8],options);
    assert.equal(r.mode,'FULL_REBUILD');assert.equal(r.retained_tokens,0);
    assert.deepEqual(r.append_ids,[1,7,8]);assert.deepEqual(r.actions[0],{operation:'COMMON_RESET_AND_CLEAR_TOKEN_STATE'});
  }
});
test('pending mismatch without cached suffix never trims an unmaterialized token',()=>{
  const r=reconcile([1,2,9],2,[1,2,8,4],{pendingId:9,trimSupported:false});
  assert.equal(r.mode,'LCP_TRIM_REPLAY');assert.equal(r.trim_materialized_rows,0);
  assert.deepEqual(r.append_ids,[8,4]);
});
test('fully materialized identical or shorter prompt forces final token re-evaluation',()=>{
  for(const next of [[1,2,3],[1,2]]){
    const r=reconcile([1,2,3],3,next);
    assert.equal(r.mode,'LCP_TRIM_REPLAY');assert.equal(r.retained_tokens,next.length-1);
    assert.equal(r.fresh_last_token_replay,true);assert.deepEqual(r.append_ids,[next.at(-1)]);
    assert.equal(r.can_sample_before_execution,false);assert.equal(r.output_ownership_verified,false);
  }
  const one=reconcile([1],1,[1]);assert.equal(one.retained_tokens,0);assert.deepEqual(one.append_ids,[1]);
});
test('identical logical prompt with pending terminal decodes pending once instead of stale sampling',()=>{
  const r=reconcile([1,2,3],2,[1,2,3],{pendingId:3});
  assert.equal(r.mode,'DIRECT_APPEND');assert.equal(r.fresh_last_token_replay,false);
  assert.deepEqual(r.append_ids,[3]);assert.equal(r.can_sample_before_execution,false);
});
test('capacity refusal never emits state-mutating actions',()=>{
  const r=reconcile([1,2],2,Array(3970).fill(1));
  assert.equal(r.mode,'UNSUPPORTED_CAPACITY');assert.deepEqual(r.actions,[]);
  assert.equal(r.pending_disposition,'DO_NOT_MUTATE');assert.equal(r.predicted_execution_head,null);
  assert.equal(reconcile([],0,Array(3969).fill(1)).capacity_required_worst_case,4096);
});
test('invalid logical state, tokens, booleans and empty frontier input fail',()=>{
  const cases=[()=>reconcile([1],2,[1]),()=>reconcile([1,2,3],1,[1]),
    ()=>reconcile([1,2],1,[1,2],{pendingId:null}),()=>reconcile([1],1,[]),
    ()=>reconcile([true],1,[1]),()=>reconcile([1],1,[NaN]),
    ()=>reconcile([1],1,[1],{trimSupported:1}),()=>reconcile([1],1,[1],{capacity:0})];
  for(const f of cases)assert.throws(f);
});
test('every exported token entry rejects holes and invalid IDs, including inherited array slots',()=>{
  const inherited=new Array(2);inherited[0]=1;
  Object.setPrototypeOf(inherited,Object.assign(Object.create(Array.prototype),{1:2}));
  const invalid=[Array(1),[1,,3],inherited,[undefined],[null],[-1],[1.5],[NaN],[Infinity],
    [Number.MAX_SAFE_INTEGER+1],[true],['1']];
  for(const bad of invalid){
    assert.throws(()=>validateTokenIDs(bad));
    assert.throws(()=>prefixLength(bad,[1]));assert.throws(()=>prefixLength([1],bad));
    assert.throws(()=>reconcile(bad,0,[1]));assert.throws(()=>reconcile([],0,bad));
    assert.throws(()=>classifyTerminal(bad,'CAP',{outputCap:bad.length}));
    assert.throws(()=>classifyTerminal([1],'CAP',{outputCap:1,eogIds:bad}));
  }
  const own=[1,2];Object.setPrototypeOf(own,Object.assign(Object.create(Array.prototype),{1:999}));
  assert.deepEqual(validateTokenIDs(own),[1,2]);
});
test('vocabulary binding validates every token and optional bound before prefix traversal',()=>{
  assert.deepEqual(validateTokenIDs([0,12],{n_vocab:13}),[0,12]);
  assert.deepEqual(validateTokenIDs([Number.MAX_SAFE_INTEGER]),[Number.MAX_SAFE_INTEGER]);
  for(const n_vocab of [null,0,-1,1.5,'13',Infinity,Number.MAX_SAFE_INTEGER+1]){
    assert.throws(()=>validateTokenIDs([],{n_vocab}));
    assert.throws(()=>prefixLength([],[],{n_vocab}));
  }
  assert.throws(()=>validateTokenIDs([13],{n_vocab:13}));
  assert.throws(()=>prefixLength([1,5],[2,3],{n_vocab:5}));
  assert.throws(()=>prefixLength([1],[1,5],{n_vocab:5}));
  const r=reconcile([10,11],1,[10,11,12],{n_vocab:13,pendingId:11});
  assert.deepEqual(r.append_ids,[11,12]);assert.equal(r.append_rows,2);
  assert.throws(()=>reconcile([10,11],1,[10,11,13],{n_vocab:13}));
  assert.throws(()=>reconcile([10,13],1,[10,11],{n_vocab:13}));
  assert.throws(()=>reconcile([10],1,[10,11],{n_vocab:13,pendingId:undefined}));
  assert.throws(()=>reconcile([10],1,[10,11],{n_vocab:13,pendingId:13}));
  assert.equal(classifyTerminal([1,3],'EOG',{eogIds:[3],n_vocab:4}).pending_id,3);
  assert.throws(()=>classifyTerminal([1,4],'CAP',{outputCap:2,eogIds:[3],n_vocab:4}));
  assert.throws(()=>classifyTerminal([1,3],'EOG',{eogIds:[4],n_vocab:4}));
});
test('pure planner never changes caller arrays or claims native observations',()=>{
  const old=Object.freeze([1,2,3]),next=Object.freeze([1,7,8]);
  const r=reconcile(old,3,next);
  assert.deepEqual(old,[1,2,3]);assert.deepEqual(next,[1,7,8]);
  assert.equal(r.native_head,null);assert.equal(r.actual_trim_result,null);
  assert.equal(r.model_forwards,0);assert.equal(r.actual_KV_frontier_equivalence,'NOT_QUALIFIED');
  assert.equal(r.actions.at(-1).operation,'FENCE_AND_COPY_FULL_REQUESTED_FRONTIER_TO_CALLER_OWNERSHIP');
});
test('retained geometry205/84 distinguishes strong rechunk from LOCALouter',()=>{
  const g=schedule(205,84);
  assert.deepEqual(g.whole_fixed.calls.map(x=>x.width),[32,19,13,20]);
  assert.deepEqual(g.whole_rechunk.calls.map(x=>x.width),[32,19,32,1]);
  assert.deepEqual(g.local_outer.calls.map(x=>x.width),[32,32,20]);
  assert.equal(g.local_outer.calls[1].envelope_is_not_attention_work,true);
  assert.equal(g.native_head,null);assert.equal(g.native_kernel_dispatches,null);
});
test('dense ordered geometry exhaustively conserves rows and attention work',()=>{
  let cases=0;
  for(const p of [16,32,64])for(const q of [1,2,4,8,16])for(let h=0;h<2*p;h++)for(const a of [0,1,3,8,17,31,65,129]){
    const g=schedule(h,a,{q,padding:p,capacity:512});
    for(const key of ['whole_fixed','whole_rechunk','local_outer','local_inner'])assert.equal(g[key].token_rows,a);
    assert.equal(g.whole_fixed.predicted_padded_attention_work,g.whole_rechunk.predicted_padded_attention_work);
    assert.equal(g.local_inner.predicted_padded_attention_work,g.whole_rechunk.predicted_padded_attention_work);
    assert(g.whole_rechunk.call_count<=Math.ceil(a/q)+1);cases++;
  }
  assert.equal(cases,8960);
});
test('geometry capacity, zero-width tails and non-divisible q are explicit',()=>{
  const g=schedule(4095,2);assert.equal(g.status,'UNSUPPORTED_CAPACITY');assert.equal(g.whole_rechunk,null);
  assert.equal(schedule(4096,0).local_outer.call_count,0);
  assert.equal(schedule(13,21,{q:3,padding:16,capacity:64}).whole_rechunk.divisible_padding_bound_applicable,false);
  for(const args of [[true,1],[-1,1],[0,1,{q:0}],[0,1,{padding:15,capacity:64}]])assert.throws(()=>schedule(...args));
});

let failures=0;for(const [name,fn]of tests){try{fn();process.stdout.write('PASS '+name+'\n');}catch(error){failures++;process.stderr.write('FAIL '+name+'\n'+error.stack+'\n');}}
process.stdout.write(JSON.stringify({tests:tests.length,failures,model_forwards:0,GPU_requests:0,tokenizer_calls:0,scope:'Synthetic CPU token/cache-plan and geometry tests, not native qualification'})+'\n');
if(failures)process.exitCode=1;
