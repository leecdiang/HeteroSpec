#!/usr/bin/env python3
"""Add read-only terminal journal evidence to the exact published CPU fixture."""
import argparse,pathlib,hashlib,json
p=argparse.ArgumentParser();p.add_argument('--fixture',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
b=a.fixture.read_bytes();pin='9dbcfdbcb6299b0a679a0966e9d76fc2891838cf6ae4c42f842289d59e841715'
if hashlib.sha256(b).hexdigest()!=pin:raise ValueError('unexpected published fixture')
s=b.decode();anchor=' Ctx state_oracle(m,1);'
addon=''' const bool unmaterialized_emitted=!last_already_consumed;
 need(!unmaterialized_emitted || pending==output.back(),"unmaterialized output differs from local pending");
 auto accounted_output=history; if(unmaterialized_emitted)accounted_output.push_back(output.back());
 auto full_emitted_prefix=prompt;full_emitted_prefix.insert(full_emitted_prefix.end(),output.begin(),output.end());
 need(accounted_output==full_emitted_prefix,"emitted prefix not accounted for by KV and optional pending");
 const std::string terminal_kind=rows.empty()?"initial":rows.back().at("last").get<std::string>();
 const auto frontier_reference=oracle(m,expected_history);
 const bool stored_last_logits_match=same(target.logits(),frontier_reference);
 const int frontier_logit_row=rows.empty()?-1:rows.back().at("accepted").get<int>();
 const bool frontier_row_matches=same(target.logits(frontier_logit_row),frontier_reference);
 need(frontier_row_matches,"selected frontier row differs from scalar prefix");
 J terminal_evidence={{"done",done},{"terminal_kind",terminal_kind},
   {"emitted_last",output.back()},{"materialized_next_position",base},
   {"target_kv_max",llama_memory_seq_pos_max(llama_get_memory(target.c),0)},
   {"draft_kv_max",llama_memory_seq_pos_max(llama_get_memory(draft.c),0)},
   {"local_pending_variable",pending},
   {"unmaterialized_output_token",unmaterialized_emitted?J(output.back()):J(nullptr)},
   {"unmaterialized_output_position",unmaterialized_emitted?J(base):J(nullptr)},
   {"last_output_materialized",last_already_consumed},
   {"legacy_pending_field",rows.empty()?J("ABSENT_INITIAL_STOP"):rows.back().at("pending")},
   {"stored_last_logits_match_materialized_frontier",stored_last_logits_match},
   {"frontier_logit_row",frontier_logit_row},{"frontier_row_matches_scalar_prefix",frontier_row_matches},
   {"accounted_output_matches_full_emitted_prefix",true},
   {"resume_supported",false}};
'''
if s.count(anchor)!=1:raise ValueError('state anchor changed')
s=s.replace(anchor,addon+anchor)
old=' return {{"draft_ubatch",dub}'
if s.count(old)!=1:raise ValueError('return anchor changed')
s=s.replace(old,' return {{"terminal_materialization_evidence",terminal_evidence},{"draft_ubatch",dub}')
a.output.mkdir(parents=True,exist_ok=False);data=s.encode();(a.output/'terminal_probe.cpp').write_bytes(data)
(a.output/'PROBE_SOURCE.json').write_text(json.dumps({'base_fixture_sha256':pin,'probe_sha256':hashlib.sha256(data).hexdigest(),'changes':'Read-only observation of target/draft plus fresh scalar diagnostic replay; no change to target/draft decode, trim, acceptance or parameters.'},indent=2)+'\n')
