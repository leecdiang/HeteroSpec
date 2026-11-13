'use strict';
// Development coverage only, no tokenizer/native/model call. Never selects an
// offset within a path or changes text, padding, reference or previous result.
// node freeze_episodes.js ORIGINAL_N0_DIR PR225_COMPARISON_DIR FRESH_OUT
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const [n0,prior,out]=process.argv.slice(2);assert(n0&&prior&&out);assert(!fs.existsSync(out));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=(d,n)=>JSON.parse(fs.readFileSync(path.join(d,n),'utf8'));
const corpus=read(n0,'CORPUS.json'),raw=read(n0,'MESSAGES.json'),rows=read(prior,'TURN_COMPARISON.json');
const byID=new Map(raw.map(r=>[r.message_id,r])),byTurn=new Map(rows.map(r=>[r.message_id,r]));
assert.equal(raw.length,4401);assert.equal(corpus.roots.length,518);assert.equal(rows.length,1645);
const policy={id:'N1a-source-coverage-v1',episode_user_turns:2,root_rank_seed:'N1a-source-coverage-v1:root:',leaf_rank_seed:'N1a-source-coverage-v1:leaf:',
 rule:'Each original root: rank all source paths with at least two user turns by SHA256(seed+leafID), choose first before consulting any geometry. Keep its first two user turns exactly. Mark original necessary cap/stop incompatibility without replacing the path. For the explicit development-coverage strata only, select the first two eligible distinct roots by root hash for predicted difference and no difference. Preserve every root/path denominator, no latency/offset/template/padding/token search.',
 coverage:'Provided-history predictions only. Actual FREE_R responses/head/partition may differ; never replace a chosen episode after native output. Two roots per stratum is coverage, not representative statistical sampling or N2 eligibility.',
 forbidden:['offset/padding changes','speed or acceptance search','replacing a selected path after inspecting geometry','using supplied assistant bodies as future generated response','adaptive re-selection after R'],
 origin:'PR224 complete source cohort and PR225 immutable supplied-token predictions; neither census is re-executed'};
const candidates=[];
for(const {root}of corpus.roots){
 const paths=corpus.root_to_leaf_paths.filter(p=>p.root===root&&p.status==='SUPPORTED'&&p.user_message_ids.length>=2)
  .map(p=>({p,rank:sha(policy.leaf_rank_seed+p.leaf_message_id)})).sort((a,b)=>a.rank.localeCompare(b.rank));
 if(!paths.length){candidates.push({root,status:'NO_TWO_USER_TURN_SOURCE_PATH',not_dropped_from_denominator:true});continue;}
 const picked=paths[0],ids=picked.p.user_message_ids.slice(0,2),r=byTurn.get(ids[1]);assert(r);
 candidates.push({root,leaf:picked.p.leaf_message_id,path_id:picked.p.path_id,leaf_rank:picked.rank,root_rank:sha(policy.root_rank_seed+root),user_message_ids:ids,
  source_paths_with_two_turns:paths.length,status:r.provided_native_cap_and_stop_compatible?'NECESSARY_PROVIDED_HISTORY_COMPATIBLE':'PROVIDED_HISTORY_CAP_OR_STOP_INCOMPATIBLE',
  source_predicted_second_turn:{head:r.C.predicted_head,append:r.C.replayed_suffix_rows,partition_distinct:r.C.geometry.comparisons.projection_partition_distinct,actual_native_head:null,actual_free_generation_compatibility:null},not_dropped_from_denominator:true});
}
const eligible=candidates.filter(x=>x.status==='NECESSARY_PROVIDED_HISTORY_COMPATIBLE');
const selected=[];
for(const distinct of [false,true]){const ranked=eligible.filter(x=>x.source_predicted_second_turn.partition_distinct===distinct).sort((a,b)=>a.root_rank.localeCompare(b.root_rank));assert(ranked.length>=2,'Coverage unavailable; stop rather than alter path/offset');for(const r of ranked.slice(0,2))selected.push({...r,coverage_stratum:distinct?'PREDICTED_DIFFERENCE':'PREDICTED_NO_DIFFERENCE',users:r.user_message_ids.map(id=>({message_id:id,role:'user',content:byID.get(id).text})),assistant_history_policy:'Future R generates its own responses; source supplied bodies are prediction provenance only',native_state:'NOT_RUN'});}
assert.equal(new Set(selected.map(x=>x.root)).size,4);
fs.mkdirSync(out);
const write=(n,x)=>fs.writeFileSync(path.join(out,n),JSON.stringify(x,null,2)+'\n',{flag:'wx'});
write('POLICY.json',policy);write('ALL_ROOT_CANDIDATES.json',candidates);write('FOUR_EPISODES.json',selected);
const count=status=>candidates.filter(x=>x.status===status).length;
write('SELECTION_REPORT.json',{status:'FOUR_CPU_DEVELOPMENT_EPISODES_FROZEN_NOT_NATIVE',source_roots:518,source_paths:2241,source_messages:4401,source_turns:1645,
 no_two_user_path:count('NO_TWO_USER_TURN_SOURCE_PATH'),fixed_path_necessary_incompatible:count('PROVIDED_HISTORY_CAP_OR_STOP_INCOMPATIBLE'),eligible_fixed_path_roots:eligible.length,
 eligible_predicted_difference:eligible.filter(x=>x.source_predicted_second_turn.partition_distinct).length,eligible_predicted_no_difference:eligible.filter(x=>!x.source_predicted_second_turn.partition_distinct).length,
 selected:4,selected_predicted_difference:2,selected_predicted_no_difference:2,mode:'EXPOSED_SOURCE_COVERAGE_NOT_CONFIRMATION_OR_FREE_GENERATION',
 source_input_identities:Object.fromEntries([[n0,'CORPUS.json'],[n0,'MESSAGES.json'],[prior,'TURN_COMPARISON.json']].map(([d,n])=>{const b=fs.readFileSync(path.join(d,n));return[n,{bytes:b.length,sha256:sha(b)}];})),
 forwards:0,GPU_contexts:0,tokenizer_calls:0,placement_actions:0});
console.log(JSON.stringify({status:'FROZEN',selected:selected.map(r=>({root:r.root,stratum:r.coverage_stratum,head:r.source_predicted_second_turn.head,append:r.source_predicted_second_turn.append}))}));
