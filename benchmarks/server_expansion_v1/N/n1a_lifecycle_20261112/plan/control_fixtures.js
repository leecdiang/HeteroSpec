'use strict';
// Concrete raw-token caller fixtures, NOT canonical natural conversations.
// IDs were read from frozen N0 TOKENIZER_OUTPUT prompt:68489e5c-978f-4ad7-a849-39a741fb5ae7.
// The four empty-think IDs are exact saved template tokens. No tokenizer runs.
const BASE=Object.freeze([151644,872,198,20195,151645,198,151644,77091,198,151667,271,151668,271]);
const NEXT_USER=Object.freeze([151645,198,151644,872,198,11916,151645,198,151644,77091,198,151667,271,151668,271]);
const SETUP_PENDING=19077,CONTINUATION_PENDING=1802;
const canonicalTrim=BASE.slice(0,-4).concat([SETUP_PENDING],NEXT_USER);
const definitions=[
 ['pending_cap_append',BASE.concat([SETUP_PENDING],NEXT_USER),'DIRECT_APPEND',13,0,'REPLAY_OLD_PENDING_ONCE_AT_CANONICAL_POSITION',null],
 ['empty_think_lcp_trim',canonicalTrim,'LCP_TRIM_REPLAY',9,4,'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX',null],
 ['fully_cached_replay_ownership',BASE.slice(),'LAST_TOKEN_REPLAY',12,1,'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX',null],
 ['trim_unsupported_rebuild',canonicalTrim,'COMMON_FULL_REBUILD',0,13,'DISCARD_OLD_PENDING_WITH_RESET','TRIM_CAPABILITY_UNSUPPORTED'],
 ['trim_pre_mutation_failure_rebuild',canonicalTrim,'COMMON_FULL_REBUILD',0,13,'DISCARD_OLD_PENDING_WITH_RESET','CALLER_INJECTED_TRIM_FAILURE_BEFORE_NATIVE_MUTATION']
];
function fixtures(){return definitions.map(([id,next,mode,keep,trim,pending,fault])=>({
 id,scope:'SCRIPTED_RAW_TOKEN_CALLER_CONTRACT_NOT_NATURAL_CHAT',
 source_token_identity:{saved_tokenizer_output_sha256:'23e812286a06ce6e067eb89648221b4348daeb1d3b5722aab780d09c56288350',
  source_prompt_id:'68489e5c-978f-4ad7-a849-39a741fb5ae7',empty_think_ids:[151667,271,151668,271]},
 requests:[{
  ordinal:0,role:'SETUP',canonical_input_ids:BASE.slice(),response_cap:1,
  generation_mode:'FORCED_NON_EOG_CONTROL_TOKEN_NOT_GREEDY',forced_terminal_id:SETUP_PENDING,
  instructions:['Reset sequence/pending/frontier to empty; no extra forward',
   'Decode every exact setup prompt token; R/oracle q1, strong candidate receives complete legal append',
   'Fence and own the full vocabulary output; preserve a caller-owned copy for the next decode',
   'Record the forced terminal control token as unmaterialized pending; no generation-row decode'],
  expected:{canonical_input_tokens:BASE.length,materialized_head:BASE.length,
   logical_ids:BASE.concat([SETUP_PENDING]),pending:{id:SETUP_PENDING,position:BASE.length},
   generated_decoded_rows:0,model_rows:BASE.length,stop_reason:'CAP'}
 },{
  ordinal:1,role:'CONTINUATION',canonical_input_ids:next.slice(),response_cap:1,
  generation_mode:'FORCED_NON_EOG_CONTROL_TOKEN_NOT_GREEDY',forced_terminal_id:CONTINUATION_PENDING,
  fault_injection:fault,
  instructions:['Resident paths use the same live setup context; cold oracle starts empty and computes its own q1 canonical prefix',
   'Compare token IDs before mutation; apply the declared shared keep/trim/reset rule',
   'Capture actual retained active prefix, invalidate resident old frontier, reconcile pending ownership',
   'Decode the complete exact remaining canonical suffix once; copy the full fresh owned vocabulary output',
   'Record one forced terminal control token pending, without decoding it',
   'After this decode compare the old caller-owned setup output bytes with its pre-decode copy',
   'After both requests reset and emit an empty checkpoint with zero active-KV bytes; no extra forward'],
  expected:{mode,keep,trimmed_resident_rows:trim,pending_policy:pending,
   fresh_replay_ids:next.slice(keep),resident_model_rows:next.length-keep,
   oracle_model_rows:next.length,materialized_head:next.length,
   logical_ids:next.concat([CONTINUATION_PENDING]),pending:{id:CONTINUATION_PENDING,position:next.length},
   generated_decoded_rows:0,stop_reason:'CAP',
   native_trim_failure_tested:false,
   fallback_scope:fault?'Caller policy fallback only; unexpected native errors STOP without retry':null}
 }],
 context_reset:{after_request_ordinal:1,model_rows:0,model_requests:0,
  expected_materialized_head:0,expected_logical_ids:[],expected_pending:null,expected_frontier_valid:false,
  required_empty_checkpoint:true},
 ownership_test:{source_request_ordinal:0,mutation_request_ordinal:1,full_vocabulary_rows:1,
  source_phase:'TERMINAL',source_row_selector:'LAST_REQUESTED_ROW',
  required:'Bind actual source snapshot row/run/context/operation and before/after event receipts around the continuation decode; compare complete raw bytes'},
 contract_note:'Forced tokens construct lifecycle state. They are never claimed to be free-generated, canonical chat output or an EOG observation.'
}));}
module.exports={BASE,NEXT_USER,SETUP_PENDING,CONTINUATION_PENDING,fixtures};
