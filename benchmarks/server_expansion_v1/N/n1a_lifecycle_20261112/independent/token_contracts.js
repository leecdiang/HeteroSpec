'use strict';
// Independent CPU checker primitives. No candidate, tokenizer or native imports.
function requireValue(ok,message) { if(!ok) throw new Error(message); }
function safeNatural(value,label) {
  requireValue(Number.isSafeInteger(value)&&value>=0,label+' must be a nonnegative safe integer');
}
function validateTokenIDs(value,{n_vocab,label='tokenIDs'}={}) {
  requireValue(Array.isArray(value),label+' must be an array');
  if(n_vocab!==undefined) {
    safeNatural(n_vocab,'n_vocab');requireValue(n_vocab>0,'n_vocab must be positive');
  }
  const result=[];
  for(let index=0;index<value.length;index++) {
    requireValue(Object.hasOwn(value,index),label+' has a missing own token at '+index);
    const token=value[index];safeNatural(token,label+'['+index+']');
    if(n_vocab!==undefined)requireValue(token<n_vocab,label+'['+index+'] exceeds the vocabulary bound');
    result.push(token);
  }
  return result;
}
function prefixLength(left,right,options={}) {
  const a=validateTokenIDs(left,{...options,label:'leftIDs'});
  const b=validateTokenIDs(right,{...options,label:'rightIDs'});
  let common=0;while(common<a.length&&common<b.length&&a[common]===b[common])common++;
  return common;
}
function canonicalRepair(oldLogicalIDs,materializedHead,nextCanonicalIDs,options={}) {
  const old=validateTokenIDs(oldLogicalIDs,{...options,label:'oldLogicalIDs'});
  const next=validateTokenIDs(nextCanonicalIDs,{...options,label:'nextCanonicalIDs'});
  safeNatural(materializedHead,'materializedHead');
  requireValue(materializedHead<=old.length&&old.length-materializedHead<=1,'Only zero or one pending token may be declared');
  requireValue(next.length>0,'Canonical input must contain a frontier token');
  const pending=materializedHead<old.length?old[materializedHead]:null;
  if(Object.hasOwn(options,'pendingId')) {
    if(options.pendingId!==null)validateTokenIDs([options.pendingId],{...options,label:'pendingId'});
    requireValue(options.pendingId===pending,'Pending declaration differs from logical history');
  }
  const common=prefixLength(old,next,options);
  let retain=Math.min(common,materializedHead);
  const freshLast=retain===next.length;
  if(freshLast)retain--;
  const replay=next.slice(retain);
  const reconstructed=old.slice(0,retain).concat(replay);
  requireValue(reconstructed.length===next.length&&reconstructed.every((v,i)=>v===next[i]),'Canonical reconstruction failed');
  const pendingDisposition=pending===null?'NONE':common>materializedHead?'REPLAY_ONCE_AT_ITS_CANONICAL_POSITION':'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX';
  return {lcp:common,retain,replay_ids:replay,replayed_rows:replay.length,
    trimmed_rows:materializedHead-retain,logical_prefix:common===old.length,
    pending_id:pending,pending_disposition:pendingDisposition,
    fresh_last_token_replay:freshLast,reconstructed_ids:reconstructed,
    can_sample_before_execution:false};
}
function appendOnlyRepair(oldLogicalIDs,materializedHead,nextCanonicalIDs,options={}) {
  const old=validateTokenIDs(oldLogicalIDs,{...options,label:'oldLogicalIDs'});
  const next=validateTokenIDs(nextCanonicalIDs,{...options,label:'nextCanonicalIDs'});
  // canonicalRepair validates state and terminal ownership but does not supply B
  // with a repaired prefix: B remains strictly whole-logical-prefix compatible.
  const repaired=canonicalRepair(old,materializedHead,next,options);
  const compatible=repaired.logical_prefix;
  const append=compatible?next.slice(materializedHead):null;
  return {compatible,lcp:repaired.lcp,materialized_head:materializedHead,
    replay_ids:append,replayed_rows:append===null?null:append.length,
    pending_id:repaired.pending_id,
    requires_frontier_refresh:compatible&&append.length===0,
    can_sample_before_execution:false};
}
module.exports={validateTokenIDs,prefixLength,canonicalRepair,appendOnlyRepair};
