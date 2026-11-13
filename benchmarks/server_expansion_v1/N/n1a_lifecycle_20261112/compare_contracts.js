'use strict';
// Successor CPU comparison. A is reused saved evidence, never rerun. No model,
// tokenizer, context, GPU, native executable or network is invoked.
// node compare_contracts.js N0_SAVED_DIRECTORY FRESH_OUTPUT_DIRECTORY
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const {reconcile,schedule,prefixLength,QWEN_EOG_IDS,validateTokenIDs}=require('./contracts.js');
const source=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
assert(!fs.existsSync(out),'Fresh successor output; preserve all old results');fs.mkdirSync(out);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=n=>JSON.parse(fs.readFileSync(path.join(source,n),'utf8'));
const write=(n,v)=>fs.writeFileSync(path.join(out,n),JSON.stringify(v,null,2)+'\n',{flag:'wx'});
const inputs={};
for(const n of ['SPEC.json','CORPUS.json','TURN_CENSUS.json','CENSUS_REPORT.json','TOKENIZER_OUTPUT.jsonl','FOUR_DEVELOPMENT_SOURCE_INPUTS.json']){
 const b=fs.readFileSync(path.join(source,n));inputs[n]={bytes:b.length,sha256:sha(b)};
}
assert.equal(inputs['SPEC.json'].sha256,'c78c2c0b259c9fb94986588cd253b891942c9dec4aa48fd8d58c4de12ef55ab8');
assert.equal(inputs['TURN_CENSUS.json'].sha256,'06125c3380292e51b4dd15c0a9d9b803fa9aed7b734ac53cfcc586d81a5bb7b4');
assert.equal(inputs['TOKENIZER_OUTPUT.jsonl'].sha256,'23e812286a06ce6e067eb89648221b4348daeb1d3b5722aab780d09c56288350');
const spec=read('SPEC.json'),corpus=read('CORPUS.json'),aRows=read('TURN_CENSUS.json'),aReport=read('CENSUS_REPORT.json');
assert.equal(spec.GPU_authorized,false);assert.equal(spec.model_forward_authorized,false);
const tokens=new Map();let vocab;
for(const l of fs.readFileSync(path.join(source,'TOKENIZER_OUTPUT.jsonl'),'utf8').trim().split('\n')){
 const r=JSON.parse(l);assert.equal(r.vocab_only,true);assert.equal(r.forward_calls,0);
 if(r.event==='vocabulary')vocab=r;else{assert(!tokens.has(r.task_id));tokens.set(r.task_id,r.prompt_ids);}
}
assert.deepEqual([...vocab.eog].sort((a,b)=>a-b),QWEN_EOG_IDS);assert.equal(vocab.context_creations,0);
const n_vocab=vocab.tokens.length;
validateTokenIDs(vocab.eog,{n_vocab,label:'bound vocabulary EOG IDs'});
for(const [task,values] of tokens)tokens.set(task,validateTokenIDs(values,{n_vocab,label:task}));
const aMap=new Map(aRows.map(r=>[r.message_id,r]));assert.equal(aMap.size,1645);
const freeze={schema:'heterospec.N.history-contract-cpu.v1',predecessor_PR:224,predecessor_head:'8be5f9acf3139356ecd95f065964373c7c83ffde',
 inputs,model:spec.model,template_sha256:spec.chat_template_sha256,tokenizer_executable_sha256:spec.tokenizer_executable_sha256,
 source_universe:'Exactly the same complete4401-message518-root OASST validation subset; no sample/offset/template search',
 A:'Frozen canonical provided-history plus full common rebuild; saved rows/metrics reused without executing old census',
 B:'Raw logical-output-token retention as append-only history; not implemented in current worker and incompatible with unchanged canonical next input when full history is not a prefix. No invented suffix or favorable geometry.',
 C:'Source-supported upstream token-LCP suffix repair, not deployed/qualified N integration. Bound retain by materialized head, trim tail, discard/reconcile pending, decode exact canonical suffix. If fully cached, replay last token to refresh owned frontier. All R/candidates share this new repair rule and full cost.',
 history_mode:'SUPPLIED_HISTORY_SAVED_TOKENS_ONLY; body tokens and providedEOG are hypothetical, not actual greedy output',
 C_failure_policy:'Invalid cache/unsupported or failed trim -> identical full canonical reset/rebuild, fully charged; no favorable per-arm fallback. Empty next prompt unsupported.',
 q:32,padding:256,capacity:4096,response_cap:128,native_head_observations:0,
 all_model_forward_calls:0,GPU_actions:0,placement_actions:0,model_context_creations:0,new_tokenizer_calls:0,
 source_support:'Pinned upstream server token-LCP+seq_rm; current experiment has trim primitive but resets each request. Exact numerical/state equivalence still requires independent sequential R.',
 no_latency_acceptance_or_5pct_selection:true};
write('FREEZE.json',freeze);
const rows=[];
for(const turn of corpus.user_turns){
 const a=aMap.get(turn.message_id);assert(a);assert.equal(turn.status,'SUPPORTED');
 const next=tokens.get('prompt:'+turn.message_id);assert(next);assert.deepEqual(next,a.prompt_ids);
 let old=[],long=false,embedded=false;
 for(const mid of turn.chain_to_node.slice(0,-1)){
  const body=tokens.get('body:'+mid);if(body){long ||= body.length+1>128;embedded ||= body.some(id=>QWEN_EOG_IDS.includes(id));}
 }
 if(turn.turn_index>0){const chain=turn.chain_to_node;old=tokens.get('prompt:'+chain.at(-3)).concat(tokens.get('body:'+chain.at(-2)),[spec.provided_history_eog_id]);}
 const mat=old.length?old.length-1:0,lcp=prefixLength(old,next,{n_vocab});
 if(old.length)assert.equal(lcp,a.token_prefix_lcp);
 const plan=reconcile(old,mat,next,{capacity:4096,outputCap:128,pendingId:old.length?old.at(-1):null,cacheValid:true,trimSupported:true,n_vocab});
 assert.notEqual(plan.mode,'UNSUPPORTED_CAPACITY');assert.deepEqual(plan.reconstructed_canonical_ids,next);
 const g=schedule(plan.predicted_execution_head,plan.append_rows);
 const fullPrefix=old.length>0&&lcp===old.length;
 const canonicalB=old.length===0||fullPrefix;
 rows.push({root:turn.root,message_id:turn.message_id,turn:turn.turn_index,
  history_origin:'SUPPLIED_HISTORY_HYPOTHETICAL_EOG_NOT_FREE_GENERATION',native_head:null,
  provided_native_cap_and_stop_compatible:!long&&!embedded,
  prior_body_plus_supplied_EOG_over128:long,prior_embedded_EOG:embedded,
  next_canonical_tokens:next.length,materialized_head_prediction:mat,pending_token_prediction:old.length?old.at(-1):null,
  A:{scope:'REUSED_FROZEN_A_RECORD_NOT_RERUN',status:a.status,prefix_reusable:a.prefix_reusable,
   predicted_head:a.predicted_execution_head,predicted_append_rows:a.predicted_append_rows,
   whole_rechunk_calls:a.geometry.whole_rechunk.call_count,LOCAL_outer_calls:a.geometry.local_outer.call_count},
  B:{implementation:'NOT_IMPLEMENTED_AS_RAW_TOKEN_HISTORY_IN_CURRENT_WORKER',
   unchanged_canonical_input_compatible:canonicalB,later_full_prefix_preserved:old.length?fullPrefix:null,
   status:old.length?(canonicalB?'SOURCE_SUPPORT_STILL_REQUIRED':'INCOMPATIBLE_WITH_UNCHANGED_CANONICAL_INPUT'):'INITIAL_INPUT_ONLY',
   predicted_old_head:mat,valid_canonical_append_rows:old.length&&!canonicalB?null:next.length-mat,
   native_head:null,geometry_for_incompatible_contract:null},
  C:{implementation:'SOURCE_SUPPORTED_INTEGRATION_CANDIDATE_NOT_DEPLOYED_OR_QUALIFIED',
   mode:old.length?plan.mode:'INITIAL_PREFILL',lcp_tokens:plan.lcp_tokens,
   retained_tokens:plan.retained_tokens,predicted_head:plan.predicted_execution_head,
   replayed_suffix_rows:plan.append_rows,trimmed_materialized_rows:plan.trim_materialized_rows,
   canonical_suffix_ids:plan.append_ids,canonical_input_reconstruction_equal:true,
   old_full_logical_history_prefix:fullPrefix,pending_disposition:plan.pending_disposition,
   frontier_after_trim:'INVALID_UNTIL_NONEMPTY_SUFFIX_DECODE_AND_OWNED_OUTPUT',
   reference_result_equivalence:'NOT_QUALIFIED',actual_context_identity:null,native_head:null,geometry:g}});
}
assert.equal(rows.length,1645);
function summary(all){const later=all.filter(r=>r.turn>0);const sum=(fn)=>all.reduce((s,r)=>s+fn(r),0);
 return{turns:all.length,initial:all.length-later.length,later:later.length,
  A_later_full_prefix_reusable:later.filter(r=>r.A.prefix_reusable).length,
  B_later_canonical_compatible:later.filter(r=>r.B.unchanged_canonical_input_compatible).length,
  B_later_canonical_incompatible:later.filter(r=>!r.B.unchanged_canonical_input_compatible).length,
  C_old_full_history_prefix_reusable:later.filter(r=>r.C.old_full_logical_history_prefix).length,
  C_later_nonempty_retained_prefix:later.filter(r=>r.C.retained_tokens>0).length,
  C_canonical_token_reconstructions_equal:all.filter(r=>r.C.canonical_input_reconstruction_equal).length,
  C_source_conditional_distinct_rechunk_LOCAL_partitions:sum(r=>+r.C.geometry.comparisons.projection_partition_distinct),
  C_retained_prefix_token_occurrences:sum(r=>r.C.retained_tokens),A_full_prompt_rows:sum(r=>r.A.predicted_append_rows),
  C_replayed_suffix_rows:sum(r=>r.C.replayed_suffix_rows),
  C_predicted_whole_rechunk_calls:sum(r=>r.C.geometry.whole_rechunk.call_count),
  C_predicted_LOCAL_outer_calls:sum(r=>r.C.geometry.local_outer.call_count),
  C_predicted_LOCAL_inner_attention_groups:sum(r=>r.C.geometry.local_inner.call_count),
  C_extra_whole_rechunk_calls:sum(r=>r.C.geometry.comparisons.rechunk_extra_graph_calls_over_local_projection),
  C_all_predicted_attention_work_equal:all.every(r=>r.C.geometry.comparisons.predicted_padded_attention_work_equal),
  capacity_unsupported:0,actual_native_heads:0,actual_compatible_free_generation_histories:0};}
const rootCounts={};for(const r of rows){if(!rootCounts[r.root])rootCounts[r.root]=[];rootCounts[r.root].push(r);}
const report={status:'CPU_HISTORY_CONTRACT_COMPARISON_COMPLETE_NOT_NATIVE_QUALIFIED',
 model_forwards:0,GPU_contexts_created:0,placement_actions:0,new_tokenizer_calls:0,N0_rerun:false,
 source_counts:corpus.counts,all_provided_histories:summary(rows),
 necessary_cap_stop_compatible_diagnostic:summary(rows.filter(r=>r.provided_native_cap_and_stop_compatible)),
 overcap_or_stop_incompatible_histories:rows.filter(r=>!r.provided_native_cap_and_stop_compatible).length,
 C_distinct_roots:new Set(rows.filter(r=>r.C.geometry.comparisons.projection_partition_distinct).map(r=>r.root)).size,
 C_primary_opportunity_scope:'Ordered projection/whole-graph partition and calls only; predicted per-token padded attention work is equal. No performance or arithmetic-equivalence claim.',
 common_cache_reuse_is_not_LOCAL_benefit:true,
 A_frozen_result_reference:{turns:aReport.unique_user_turns,mismatches:aReport.canonical_prefix_mismatch_predictions,decision:aReport.decision},
 B:'Not canonically equivalent; no replacement reference or theoretical append matching used to declare eligibility',
 C:'A source-backed LCP integration question remains. Current HeteroSpec worker has no implemented sequential turn adapter. Design N1 only; no execution approved.',
 producer_scope:'Supplied history predictions, not measured heads/teacher-forced native replay/actual free generation',
 statistical_unit:'Roots/whole episodes for any future inference; these are complete corpus descriptions, no confidence intervals or independent-turn inference'};
write('TURN_COMPARISON.json',rows);write('REPORT.json',report);
write('PER_ROOT.json',Object.entries(rootCounts).map(([root,r])=>({root,...summary(r)})));
console.log(JSON.stringify(report));
