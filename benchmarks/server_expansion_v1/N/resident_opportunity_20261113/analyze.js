'use strict';
// Read only previously frozen text/tokens/counters. No tokenizer/model/native run.
const fs=require('fs'),path=require('path'),zlib=require('zlib'),crypto=require('crypto'),assert=require('assert/strict');
const base=path.resolve(__dirname,'..'),out=path.resolve(process.argv[2]||path.join(__dirname,'RESULTS'));
assert(!fs.existsSync(out),'fresh analysis output only');
fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function members(rel,names) {
  const b=zlib.gunzipSync(fs.readFileSync(path.join(base,rel))),r={};
  for(let i=0;i+512<=b.length;) {
    const h=b.subarray(i,i+512);
    if(h.every(x=>!x)) break;
    const n=h.subarray(0,100).toString().split('\0')[0];
    const sz=parseInt(h.subarray(124,136).toString().replace(/\0/g,'').trim()||'0',8);
    if(names(n)) r[n]=Buffer.from(b.subarray(i+512,i+512+sz));
    i+=512+Math.ceil(sz/512)*512;
  }
  return r;
}
const n0=members('successor_20261112/N0_TEXT_PACKET.tar.gz',n=>['CORPUS.json','SPEC.json','TOKENIZER_OUTPUT.jsonl','chat_template.jinja'].includes(n));
const h=members('history_contracts_20261112/HISTORY_TEXT_PACKET.tar.gz',n=>n==='COMPARISON_01/TURN_COMPARISON.json');
const free=members('free_service_retry_20261113/EVIDENCE/PUBLIC_TEXT_PACKET.tar.gz',n=>n.endsWith('/EPISODE.json')||n==='successor/STATE.json'||n==='original/MANIFEST.json');
assert.equal(sha(n0['chat_template.jinja']),'57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361');
assert.equal(sha(n0['TOKENIZER_OUTPUT.jsonl']),'23e812286a06ce6e067eb89648221b4348daeb1d3b5722aab780d09c56288350');
const corpus=JSON.parse(n0['CORPUS.json']),rows=JSON.parse(h['COMPARISON_01/TURN_COMPARISON.json']),tokens=new Map();
for(const line of n0['TOKENIZER_OUTPUT.jsonl'].toString().trim().split('\n')) {
  const x=JSON.parse(line);
  if(x.task_id) {
    assert.equal(x.forward_calls,0);
    assert.equal(x.vocab_only,true);
    tokens.set(x.task_id,x.prompt_ids);
  }
}
const cmp=new Map(rows.map(x=>[x.message_id,x]));
function prefix(a,b) {
  let i=0;
  while(i<Math.min(a.length,b.length)&&a[i]===b[i]) i++;
  return i;
}
function tileCount(calls,tile=4,splitExtents=false) {
  let sum=0;
  for(const g of calls) {
    if(!splitExtents) {
      sum+=Math.ceil(g.width/tile);
      continue;
    }
    let start=0;
    for(let i=1;i<=g.width;i++) {
      if(i===g.width||g.expected_extents[i]!==g.expected_extents[start]) {
        sum+=Math.ceil((i-start)/tile);
        start=i;
      }
    }
  }
  return sum;
}
const freeManifest=JSON.parse(free['original/MANIFEST.json']);
const freeRows=[],actualPlans=[];
for(const [name,bytes]of Object.entries(free)){
 if(!name.endsWith('/EPISODE.json'))continue;
  const e=JSON.parse(bytes);
 if(name.startsWith('original/R/')){
  const [a,b]=e.requests,q0=a.prompt.canonical_ids,q1=b.prompt.canonical_ids,y=a.consumer.sampled_ids,k=prefix(a.logical_ids,q1),stub=[151667,271,151668,271];
  assert.equal(k,b.retained);
  assert.deepEqual(q0.slice(-4),stub);
  assert.equal(k,q0.length-4);
  assert.equal(a.native_head_after,q0.length+y.length-1);
  assert(!y.some(x=>freeManifest.EOG_ids.includes(x)));
  assert.equal(a.consumer.stop,'CAP');
  const bodyEnd=q1.indexOf(151645,k),canonicalBody=q1.slice(k,bodyEnd),pieceBytes=Buffer.from(a.consumer.parser_input_hex,'hex'),content=Buffer.from(a.consumer.client_message.content,'utf8');
  assert(pieceBytes.equals(content));
  assert.deepEqual(canonicalBody,y,'these fixed free cases retain exact body tokenization');
  assert.equal(a.consumer.history_after.at(-1).content,a.consumer.client_message.content);
  assert.deepEqual(b.prompt.history,a.consumer.history_after.concat(freeManifest.cases.find(x=>x.id===e.case).users[1]));
  freeRows.push({case:e.case,
    source:name,
    initial_tokens:q0.length,
    sampled_tokens:y.length,
    materialized_head:a.native_head_after,
    logical_head:a.logical_ids.length,
    pending_id:a.pending,
    pending_position:a.native_head_after,
    stop:a.consumer.stop,
    LCP:k,
    trimmed_KV_rows:a.native_head_after-k,
    trimmed_prompt_stub_rows:4,
    trimmed_materialized_sample_rows:y.length-1,
    retained_sampled_assistant_KV_rows:0,
    first_difference:{position_zero_based:k,
    old_token:q0[k],
    new_token:q1[k],
    old_ids:a.logical_ids.slice(k,k+12),
    new_ids:q1.slice(k,k+12)},
    canonical_assistant_body_tokens:canonicalBody.length,
    canonical_body_same_tokenization:JSON.stringify(canonicalBody)===JSON.stringify(y),
    body_token_first_difference:prefix(canonicalBody,y),
    sample_piece_bytes_equal_client_content:true,
    wire_finish_reason:JSON.parse(a.consumer.wire_response_json).choices[0].finish_reason,
    canonical_closure_id:q1[bodyEnd],
    canonical_closure_position:bodyEnd,
    old_pending_reused_at_old_position:false,
    next_input_tokens:q1.length,
    next_retained:k,
    next_suffix_rows:q1.length-k,
    continuation_materializations:b.consumer.sampled_ids.length-1,
    second_request_total_rows:b.rows,
    common_cold_second_request_rows:q1.length+b.consumer.sampled_ids.length-1,
    initial_prompt_tail:a.prompt.prompt_utf8.slice(-70),
    body_start:a.consumer.client_message.content.slice(0,110)});
 }
 if(e.stage==='HEAVY'){
  const p=e.dispatch.plan,physical=e.dispatch.physical;
  assert.equal(p.length,physical.length);
  // Positions overlap between turns after trim; bind each plan to its actual request.
  for(let i=0;i<p.length;i++){assert.equal(p[i].position,physical[i].position);
  assert.equal(p[i].width,physical[i].API_width);}
  const t1=e.requests[1],t1Suffix=p.filter((g,i)=>physical[i].request===t1.id&&g.position<t1.prompt.canonical_ids.length&&g.phase==='ORDINARY');
  assert.equal(t1Suffix.reduce((s,g)=>s+g.width,0),t1.prompt.canonical_ids.length-t1.retained);
  actualPlans.push({case:e.case,
    arm:e.arm,
    source:name,
    actual_rows:e.dispatch.physical_rows,
    actual_physical_decode_calls:e.dispatch.physical_calls,
    observed_loop4_named_node_callbacks:e.dispatch.loop4_marked_nodes,
    observed_selected_GPU_node_callbacks:e.dispatch.GPU_nodes,
    append_calls:t1Suffix.map(g=>({position:g.position,
    width:g.width,
    expected_extents:g.expected_extents})),
    source_derived_append_projection_4_column_groups:tileCount(t1Suffix),
    source_derived_append_attention_4_query_tiles:tileCount(t1Suffix,4,true),
    note:'Physical decode counts and graph callbacks are observed. Four-column/query tiles are source-derived from observed plans, not measured CUDA kernel launch counts.'});
 }
}
freeRows.sort((a,b)=>a.case.localeCompare(b.case));actualPlans.sort((a,b)=>a.case.localeCompare(b.case)||b.arm.localeCompare(a.arm));
function canonicalAssistantSpans(q,keep) {
  const spans=[];
  for(let i=0;i<keep-1;i++) {
    if(q[i]!==151644||q[i+1]!==77091) continue;
    const end=q.indexOf(151645,i+2);
    if(end<0||end>=keep) continue;
    assert([198,271].includes(q[i+2]),'unexpected role/body newline token; do not assume a span');
    spans.push({
      start:i,
      end_exclusive:end+1,
      body_start:i+3,
      body_end_exclusive:end,
      canonical_message_token_rows:end+1-i,
      body_interior_token_rows:end-i-3
    });
    i=end;
  }
  return spans;
}
const native233=members('bounded_lifecycle_20261113/EVIDENCE/PUBLIC_TEXT_PACKET.tar.gz',n=>/^initial\/R\/C[01]-(initial-prompt|old|trimmed|Q)-state\.json$/.test(n));
const old233=JSON.parse(fs.readFileSync(path.join(base,'bounded_lifecycle_20261113/MANIFEST.json')));
const supplied233=old233.cases.map(c=>({case:c.id,
    scope:'PROVIDED_TOKEN_REPLAY_NOT_FREE_GENERATION',
    initial_prompt_tokens:c.initial_prompt_ids.length,
    forced_body_tokens:c.provided_assistant_ids.length,
    materialized_head:c.old_materialized_ids.length,
    pending_id:c.pending,
    LCP:c.predicted_retained_head,
    trimmed_KV_rows:c.old_materialized_ids.length-c.predicted_retained_head,
    old_first_difference_ids:c.old_logical_ids.slice(c.predicted_retained_head,c.predicted_retained_head+8),
    new_first_difference_ids:c.canonical_next_ids.slice(c.predicted_retained_head,c.predicted_retained_head+8),
    new_input_tokens:c.canonical_next_ids.length,
    shared_initial_stub:[151667,271,151668,271]}));
for(const c of supplied233){const names=['initial-prompt','old','trimmed','Q'];c.reused_native_state_receipts=names.map(n=>{const member='initial/R/'+c.case+'-'+n+'-state.json',b=native233[member],j=JSON.parse(b);
  return{member,
    head:j.head,
    sha256:sha(b)};});
  assert.deepEqual(c.reused_native_state_receipts.map(x=>x.head),[c.initial_prompt_tokens,c.materialized_head,c.LCP,c.new_input_tokens]);}
const census=[];
for(const turn of corpus.user_turns){
 const r=cmp.get(turn.message_id),q=tokens.get('prompt:'+turn.message_id);
  assert(r);
  assert.equal(q.length,r.next_canonical_tokens);
 const oldPrompt=turn.turn_index?tokens.get('prompt:'+turn.chain_to_node.at(-3)):[];
 const keep=r.C.retained_tokens,hasLiteralMarkers=turn.messages.some(m=>/<\|im_(?:start|end)\|>/.test(m.content));
  let spans=[];
 if(!hasLiteralMarkers){spans=canonicalAssistantSpans(oldPrompt,keep);
  assert.equal(spans.length,Math.max(0,turn.turn_index-1));}
 if(turn.turn_index)assert.equal(keep,oldPrompt.length-4);
 const g=r.C.geometry,w=g.whole_rechunk,l=g.local_outer,extra=w.call_count-l.call_count;
 assert(extra>=0&&extra<=1);
  assert.equal(w.token_rows,l.token_rows);
  assert.equal(w.predicted_padded_attention_work,l.predicted_padded_attention_work);
 census.push({root:turn.root,
    message_id:turn.message_id,
    turn_index:turn.turn_index,
    necessary_supplied_EOG_128_contract:r.provided_native_cap_and_stop_compatible,
    scope:'SAVED_SUPPLIED_HISTORY_CPU_PREDICTION_NOT_FREE_OR_NATIVE',
    literal_delimiter_unsupported_for_span_assignment:hasLiteralMarkers,
    retained:keep,
    older_canonical_assistant_messages_kept:hasLiteralMarkers?null:spans.length,
    older_canonical_assistant_message_rows:hasLiteralMarkers?null:spans.reduce((s,x)=>s+x.canonical_message_token_rows,0),
    older_canonical_assistant_body_interior_rows:hasLiteralMarkers?null:spans.reduce((s,x)=>s+x.body_interior_token_rows,0),spans,
    latest_sampled_assistant_KV_retained_prediction:0,
    append_rows:r.C.replayed_suffix_rows,
    W_outer_calls:w.call_count,
    L_outer_calls:l.call_count,
    extra_calls:extra,
    projection_4column_group_proxy_W:w.calls.reduce((s,g)=>s+Math.ceil(g.width/4),0),
    projection_4column_group_proxy_L:l.calls.reduce((s,g)=>s+Math.ceil(g.width/4),0),
    attention_4query_tile_proxy_W:w.calls.reduce((s,g)=>s+Math.ceil(g.width/4),0),
    attention_4query_tile_proxy_L:g.local_inner.calls.reduce((s,g)=>s+Math.ceil(g.width/4),0),
    partition_distinct:g.comparisons.projection_partition_distinct,
    attention_work_equal:true});
}
function summarize(rs){const later=rs.filter(x=>x.turn_index>0),third=later.filter(x=>x.turn_index>=2);
  return{turns:rs.length,
    initial:rs.length-later.length,
    later:later.length,
    third_or_later:third.length,
    roots:new Set(rs.map(x=>x.root)).size,
    span_assignment_unsupported:rs.filter(x=>x.literal_delimiter_unsupported_for_span_assignment).length,
    older_canonical_assistant_prefix_present:rs.filter(x=>x.older_canonical_assistant_messages_kept>0).length,
    older_assistant_body_interior_rows:rs.reduce((s,x)=>s+(x.older_canonical_assistant_body_interior_rows||0),0),
    same_contract_projection_partition_differences:rs.filter(x=>x.partition_distinct).length,
    outer_call_saving_predictions:rs.filter(x=>x.extra_calls>0).length,
    projection_group_opportunity_predictions:rs.filter(x=>x.projection_4column_group_proxy_W>x.projection_4column_group_proxy_L).length,
    outer_or_projection_group_opportunity_predictions:rs.filter(x=>x.extra_calls>0||x.projection_4column_group_proxy_W>x.projection_4column_group_proxy_L).length,
    attention_extra_tile_predictions:rs.filter(x=>x.attention_4query_tile_proxy_L>x.attention_4query_tile_proxy_W).length,
    roots_with_count_opportunity:new Set(rs.filter(x=>x.extra_calls>0).map(x=>x.root)).size,
    W_calls:rs.reduce((s,x)=>s+x.W_outer_calls,0),
    L_calls:rs.reduce((s,x)=>s+x.L_outer_calls,0),
    token_rows:rs.reduce((s,x)=>s+x.append_rows,0),
    source_derived_intermediate_projection_4column_groups_W:rs.reduce((s,x)=>s+x.projection_4column_group_proxy_W,0),
    source_derived_intermediate_projection_4column_groups_L:rs.reduce((s,x)=>s+x.projection_4column_group_proxy_L,0),
    source_derived_attention_4query_tiles_W:rs.reduce((s,x)=>s+x.attention_4query_tile_proxy_W,0),
    source_derived_attention_4query_tiles_L:rs.reduce((s,x)=>s+x.attention_4query_tile_proxy_L,0),
    attention_work_equal:true,
    latest_generated_assistant_KV_retention_native_observations:0};}
const short=census.filter(r=>r.necessary_supplied_EOG_128_contract),samples=[];
for(const [category,pred]of [['first_older_assistant_prefix',r=>r.turn_index>=2&&r.older_canonical_assistant_body_interior_rows>0],['first_short_supplied_older_assistant_prefix',r=>r.necessary_supplied_EOG_128_contract&&r.turn_index>=2&&r.older_canonical_assistant_body_interior_rows>0],['first_short_supplied_count_opportunity',r=>r.necessary_supplied_EOG_128_contract&&r.extra_calls>0]]){const r=census.find(pred);
  if(r){let t=corpus.user_turns.find(t=>t.message_id===r.message_id);samples.push({category,
    selection:'first matching source-order node; no offset/speed/output search',...r,
    user_message_ids:t.chain_to_node.filter((_,i)=>i%2===0),
    messages:t.messages});}}
const result={status:'CPU_EXISTING_EVIDENCE_ROOT_CAUSE_AND_OPPORTUNITY_REVIEW',
    parent_236:'6597489d01d0fa1fb17dce8bf6cade2c53e3a463',
    parent_233:'4fc07500fbf4b8ac18fa5490eb53bf9c98b54845',
    supplied_history_233:supplied233,
    actual_free_cases:freeRows,
    actual_candidate_work:actualPlans,
    saved_public_corpus:{all:summarize(census),
    short_supplied_body_plus_synthetic_EOG_subset:summarize(short),
    filter_caution:'The inherited <=128 body+synthetic-EOG diagnostic is not a free-CAP eligibility rate. It is necessary only for that supplied-EOG replay contract; actual free CAP128 histories need not satisfy it.',
    native_heads_observed:0,
    generated_histories_added:0},
    new_model_requests:0,
    new_rows:0,
    new_deployments:0,
    new_contexts:0,
    new_tokenizer_calls:0,
    N0_rerun:false};
for(const [n,j]of [['REPORT.json',result],['SOURCE_ORDER_EXAMPLES.json',samples]])fs.writeFileSync(path.join(out,n),JSON.stringify(j,null,2)+'\n',{flag:'wx'});
const cols=['root','message_id','turn_index','necessary_supplied_EOG_128_contract','retained','older_canonical_assistant_messages_kept','older_canonical_assistant_body_interior_rows','append_rows','W_outer_calls','L_outer_calls','extra_calls','partition_distinct','projection_4column_group_proxy_W','projection_4column_group_proxy_L','attention_4query_tile_proxy_W','attention_4query_tile_proxy_L'];
fs.writeFileSync(path.join(out,'TURN_OPPORTUNITIES.csv'),cols.join(',')+'\n'+census.map(r=>cols.map(c=>String(r[c])).join(',')).join('\n')+'\n',{flag:'wx'});
const choice=samples.find(x=>x.category==='first_short_supplied_count_opportunity'),Q=tokens.get('prompt:'+choice.message_id);
  assert.equal(Q.length,choice.retained+choice.append_rows);
fs.writeFileSync(path.join(out,'MINIMAL_AB_FIXTURE.json'),JSON.stringify({status:'DESIGN_ONLY_NOT_APPROVED',
    selection:choice.selection,
    source_revision:'fdf72ae0827c1cda404aff25b6603abec9e3399b',
    root:choice.root,
    message_id:choice.message_id,
    provided_history_only:true,
    head:choice.retained,
    append:choice.append_rows,
    canonical_ids:Q,
    prefix_ids:Q.slice(0,choice.retained),
    append_ids:Q.slice(choice.retained),
    canonical_ids_json_sha256:sha(Buffer.from(JSON.stringify(Q))),
    requests:8,
    rows_per_request:Q.length,
    total_rows:8*Q.length,
    model_deployments:3,
    generation:false,
    new_GPU_authorization:false},null,2)+'\n',{flag:'wx'});
fs.writeFileSync(path.join(out,'chat_template.jinja'),n0['chat_template.jinja'],{flag:'wx'});
const usedFreeNames=[...freeRows,...actualPlans].map(x=>x.source).concat('original/MANIFEST.json');
const freeIndex=JSON.parse(fs.readFileSync(path.join(base,'free_service_retry_20261113/EVIDENCE/PUBLIC_TEXT_INDEX.json')));
for(const name of usedFreeNames) assert.equal(sha(free[name]),freeIndex.find(x=>x.file===name).sha256);
fs.writeFileSync(path.join(out,'INPUT_IDENTITIES.json'),JSON.stringify({model_SHA256:JSON.parse(n0['SPEC.json']).model.sha256,
    template_SHA256:sha(n0['chat_template.jinja']),
    inputs:[...usedFreeNames.map(name=>({packet:'PR236_PUBLIC_TEXT_PACKET',name,bytes:free[name].length,sha256:sha(free[name])})),...Object.entries(n0).map(([name,b])=>({packet:'N0_TEXT_PACKET',name,
    bytes:b.length,
    sha256:sha(b)})),...Object.entries(h).map(([name,b])=>({packet:'HISTORY_TEXT_PACKET',name,
    bytes:b.length,
    sha256:sha(b)})),...Object.entries(native233).map(([name,b])=>({packet:'PR233_PUBLIC_TEXT_PACKET',name,
    bytes:b.length,
    sha256:sha(b)}))],
    cost_proxy_caution:'4-column counts apply to a fully consumed intermediate projection and source query tiling, not all tensors/layers, full FLOPs, CUDA launches or measured service cost. Requested-output pruning remains unchanged.',
    checks:'Only consumed evidence and relevant source identity; no historical-tree sweep'},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result,null,2));
