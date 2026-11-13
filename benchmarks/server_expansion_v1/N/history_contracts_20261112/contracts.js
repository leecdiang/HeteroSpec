'use strict';
// Pure CPU token/state plans. No model, tokenizer, native context or GPU call.
// Token-prefix equality is not numerical KV/frontier equivalence.

const QWEN_EOG_IDS = Object.freeze([128247,151643,151645,151662,151663,151664]);

function need(value,message) { if (!value) throw new Error(message); }
function integer(name,value,minimum=0) {
  need(Number.isSafeInteger(value) && value>=minimum,name+' must be a safe integer >= '+minimum);
}
function ids(name,value) {
  need(Array.isArray(value),name+' must be an array');
  value.forEach(x=>integer(name+' token',x));
  return value.slice();
}
function same(a,b) { return a.length===b.length && a.every((x,i)=>x===b[i]); }
function prefixLength(a,b) {
  let n=0; while(n<a.length && n<b.length && a[n]===b[n]) n++;
  return n;
}

function classifyTerminal(generatedIDs,stopReason,{outputCap=128,eogIds=QWEN_EOG_IDS}={}) {
  const generated=ids('generatedIDs',generatedIDs),eogs=ids('eogIds',eogIds);
  integer('outputCap',outputCap,1);
  need(generated.length>0 && generated.length<=outputCap,'Generated token count outside declared cap');
  need(stopReason==='EOG' || stopReason==='CAP','Explicit EOG or CAP reason required');
  const isEog=generated.map(x=>eogs.includes(x));
  need(!isEog.slice(0,-1).some(Boolean),'A native producer cannot continue beyond an earlier EOG');
  if(stopReason==='EOG') need(isEog.at(-1),'EOG stop needs an actual terminal EOG token');
  else {
    need(generated.length===outputCap,'CAP stop must reach the unchanged cap');
    need(!isEog.some(Boolean),'EOG takes precedence over CAP at the terminal position');
  }
  return {
    status:'CPU_DECLARED_TERMINAL_SEQUENCE_VALID',stop_reason:stopReason,
    generated_ids:generated,terminal_token:generated.at(-1),pending_id:generated.at(-1),
    generated_tokens:generated.length,materialized_generated_rows:generated.length-1,
    artificial_EOS_added:false,EOG_token_observed_in_actual_generation:null,
    scope:'Checks caller-supplied IDs/reason only; no greedy generation or native pending state is observed'
  };
}

function reconcile(oldLogicalIDs,materializedHead,nextCanonicalIDs,options={}) {
  const old=ids('oldLogicalIDs',oldLogicalIDs),next=ids('nextCanonicalIDs',nextCanonicalIDs);
  const {capacity=4096,outputCap=128,trimSupported=true,cacheValid=true}=options;
  integer('materializedHead',materializedHead); integer('capacity',capacity,1); integer('outputCap',outputCap,1);
  need(typeof trimSupported==='boolean' && typeof cacheValid==='boolean','Capability/cache flags must be explicit booleans');
  need(next.length>0,'An empty canonical prompt has no defined fresh frontier');
  need(materializedHead<=capacity,'Declared materialized cache exceeds capacity');
  need(materializedHead<=old.length && old.length-materializedHead<=1,'Only zero or one declared pending token is supported');
  const pending=old.length>materializedHead ? old.at(-1) : null;
  if(Object.hasOwn(options,'pendingId')) need(options.pendingId===pending,'Declared pending ID disagrees with logical/materialized history');
  if(Object.hasOwn(options,'trimSucceeded')) need(typeof options.trimSucceeded==='boolean','trimSucceeded must be boolean if provided');
  const lcp=prefixLength(old,next),fullPrefix=lcp===old.length && next.length>=old.length;
  const base={
    schema:'heterospec.N.cpu.canonical-cache-reconciliation.v1',
    old_logical_tokens:old.length,materialized_head_input:materializedHead,pending_id_input:pending,
    next_canonical_tokens:next.length,lcp_tokens:lcp,whole_logical_history_is_prefix:fullPrefix,
    capacity,output_cap:outputCap,capacity_required_worst_case:next.length+outputCap-1,
    head_source:'CPU_DECLARED_TOKEN_HISTORY_NOT_NATIVE_OBSERVATION',native_head:null,
    actual_context_identity:null,actual_trim_result:null,actual_KV_frontier_equivalence:'NOT_QUALIFIED',
    output_ownership_verified:false,can_sample_before_execution:false,
    frontier_requirement:'Successful suffix decode, final fence and caller-owned full requested vector required',
    model_forwards:0,GPU_requests:0,context_creations:0
  };
  if(base.capacity_required_worst_case>capacity) return {
    ...base,mode:'UNSUPPORTED_CAPACITY',reason:'Canonical prompt plus unchanged response cap does not fit',
    retained_tokens:null,predicted_execution_head:null,append_ids:null,append_rows:null,
    trim_materialized_rows:null,pending_disposition:'DO_NOT_MUTATE',
    fresh_last_token_replay:false,actions:[],not_dropped_from_denominator:true
  };

  let keep=Math.min(lcp,materializedHead),forcedLast=false,reason='Token-LCP reconciliation before any mutation';
  // If the whole canonical prompt is materialized, re-evaluate one token to
  // obtain a fresh owned output; never sample the removed/old suffix frontier.
  if(keep===next.length) { keep=next.length-1; forcedLast=true; }
  let mode=fullPrefix && keep===materializedHead ? 'DIRECT_APPEND' : 'LCP_TRIM_REPLAY';
  let trimRows=materializedHead-keep;
  if(!cacheValid) { mode='FULL_REBUILD';reason='Declared cache is invalid'; }
  else if(trimRows>0 && !trimSupported) { mode='FULL_REBUILD';reason='Required suffix trim is not supported'; }
  else if(trimRows>0 && options.trimSucceeded===false) { mode='FULL_REBUILD';reason='Declared trim failure requires common full rebuild'; }
  if(mode==='FULL_REBUILD') { keep=0;trimRows=materializedHead;forcedLast=false; }
  const suffix=next.slice(keep),reconstructed=old.slice(0,keep).concat(suffix);
  need(suffix.length>0,'Every admitted plan must produce a fresh frontier by decoding at least one token');
  need(same(reconstructed,next),'Reconciliation changed canonical token input');
  let pendingDisposition='NONE';
  if(pending!==null) {
    if(mode==='FULL_REBUILD') pendingDisposition='DISCARD_WITH_CACHE_AND_REBUILD_CANONICAL_INPUT';
    else if(lcp>materializedHead && materializedHead>=keep)
      pendingDisposition='REPLAY_ONCE_AT_ITS_CANONICAL_POSITION';
    else pendingDisposition='DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX';
  }
  const actions=[];
  if(mode==='FULL_REBUILD') actions.push({operation:'COMMON_RESET_AND_CLEAR_TOKEN_STATE'});
  else if(trimRows>0) actions.push({operation:'TRIM_SEQ0_SUFFIX',from_position:keep,to_end:true});
  if(pending!==null) actions.push({operation:'RECONCILE_PENDING_OWNERSHIP',disposition:pendingDisposition});
  actions.push({operation:'DECODE_EXACT_CANONICAL_SUFFIX',position:keep,ids:suffix.slice(),requested_output_rows:[suffix.length-1]});
  actions.push({operation:'FENCE_AND_COPY_FULL_REQUESTED_FRONTIER_TO_CALLER_OWNERSHIP'});
  return {
    ...base,mode,reason,initial_prefill:old.length===0,
    retained_tokens:keep,predicted_execution_head:keep,append_ids:suffix,append_rows:suffix.length,
    trim_materialized_rows:trimRows,fresh_last_token_replay:forcedLast,
    pending_disposition:pendingDisposition,reconstructed_canonical_ids:reconstructed,
    canonical_token_input_preserved:true,context_reused_if_execution_qualifies:mode!=='FULL_REBUILD',
    action_kind:'CPU_PLAN_ONLY_NOT_EXECUTED',actions,
    limitation:'Exact token reconstruction does not certify cache bytes, numerical reference outputs, placement or native runtime support'
  };
}

function geometryCall(position,width,padding) {
  return {position,width,predicted_attention_extent:Math.ceil((position+width)/padding)*padding};
}
function split(position,width,padding) {
  const groups=[];let done=0;
  while(done<width) {
    const n=Math.min(width-done,padding-(position+done)%padding);
    groups.push(geometryCall(position+done,n,padding));done+=n;
  }
  return groups;
}
function summary(calls) {
  return {calls,call_count:calls.length,token_rows:calls.reduce((s,x)=>s+x.width,0),
    predicted_padded_attention_work:calls.reduce((s,x)=>s+x.width*x.predicted_attention_extent,0)};
}
function partitions(calls) { return calls.map(x=>[x.position,x.width]); }
function schedule(head,append,{q=32,padding=256,capacity=4096}={}) {
  for(const [n,v,min]of [['head',head,0],['append',append,0],['q',q,1],['padding',padding,1],['capacity',capacity,1]])integer(n,v,min);
  need(capacity%padding===0,'Declared dense capacity must be divisible by padding');
  const admitted=head<=capacity && append<=capacity-head;
  const base={schema:'heterospec.N.cpu.predicted-ordered-geometry.v1',
    status:admitted?'PREDICTED_HEAD_REQUIRES_NATIVE_CHECK':'UNSUPPORTED_CAPACITY',
    head,append,q,padding,capacity,capacity_admitted:admitted,
    native_head:null,native_kernel_dispatches:null,actual_physical_extent:null,
    source:'Declared dense token geometry only',not_dropped_from_denominator:true,
    arithmetic_equivalence:'NOT_ESTABLISHED',performance_prediction:'NOT_ESTABLISHED'};
  if(!admitted) return {...base,whole_fixed:null,whole_rechunk:null,local_outer:null,local_inner:null,comparisons:null};
  const outer=[],inner=[],fixed=[],rechunk=[];let done=0;
  while(done<append) {
    const n=Math.min(q,append-done),p=head+done,groups=split(p,n,padding);
    outer.push({position:p,width:n,predicted_graph_extent_envelope:Math.ceil((p+n)/padding)*padding,
      envelope_is_not_attention_work:true,attention_groups:groups.map(x=>({...x}))});
    fixed.push(...groups.map(x=>({...x})));inner.push(...groups.map(x=>({...x})));done+=n;
  }
  done=0;
  while(done<append) {
    const p=head+done,n=Math.min(q,append-done,padding-p%padding);
    rechunk.push(geometryCall(p,n,padding));done+=n;
  }
  const f=summary(fixed),r=summary(rechunk),i=summary(inner);
  need(f.token_rows===append && r.token_rows===append && i.token_rows===append,'Geometry token conservation');
  need(f.predicted_padded_attention_work===r.predicted_padded_attention_work && r.predicted_padded_attention_work===i.predicted_padded_attention_work,'Per-token padded attention work differs');
  const bound=Math.ceil(append/q)+1;
  if(padding%q===0)need(rechunk.length<=bound,'Rechunk bound violated');
  const partitionEqual=(a,b)=>JSON.stringify(partitions(a))===JSON.stringify(partitions(b));
  return {...base,
    whole_fixed:f,
    whole_rechunk:{...r,divisible_padding_bound_applicable:padding%q===0,
      divisible_padding_call_bound:padding%q===0?bound:null},
    local_outer:{calls:outer,call_count:outer.length,projection_call_count:outer.length,token_rows:append,
      predicted_padded_attention_work:i.predicted_padded_attention_work,
      attention_group_count:inner.length,native_kernel_dispatches:null,
      count_scope:'Outer projection-group calls, not CUDA launches'},
    local_inner:i,
    comparisons:{whole_fixed_vs_rechunk_identical_ordered_partition:partitionEqual(fixed,rechunk),
      whole_rechunk_vs_local_outer_identical_ordered_partition:partitionEqual(rechunk,outer),
      whole_rechunk_vs_local_inner_identical_ordered_partition:partitionEqual(rechunk,inner),
      whole_fixed_vs_local_inner_identical_ordered_partition:partitionEqual(fixed,inner),
      projection_partition_distinct:!partitionEqual(rechunk,outer),
      rechunk_extra_graph_calls_over_local_projection:rechunk.length-outer.length,
      local_extra_attention_groups_over_rechunk:inner.length-rechunk.length,
      predicted_padded_attention_work_equal:true}}
  ;
}

module.exports={QWEN_EOG_IDS,classifyTerminal,reconcile,schedule,prefixLength};
