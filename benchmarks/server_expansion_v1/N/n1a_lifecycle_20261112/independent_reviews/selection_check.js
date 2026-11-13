'use strict';
// Independent read-only source-tree/hash selection review. Imports no selector,
// candidate, tokenizer, native or geometry implementation.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
if(process.argv.length!==6)throw Error('Usage: node selection_check.js N0_DIR COMPARISON_DIR EPISODE_DIR FRESH_OUTPUT_DIR');
const [n0,comparison,episodes,out]=process.argv.slice(2).map(p=>path.resolve(p));
const inputs=[['N0',n0,['MESSAGES.json','CORPUS.json','FOUR_DEVELOPMENT_SOURCE_INPUTS.json']],['comparison',comparison,['TURN_COMPARISON.json']],['episodes',episodes,['POLICY.json','SELECTION_REPORT.json','ALL_ROOT_CANDIDATES.json','FOUR_EPISODES.json']]];
const identity=f=>{const b=fs.readFileSync(f);return {bytes:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex')}};
const read=(dir,name)=>JSON.parse(fs.readFileSync(path.join(dir,name),'utf8'));
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const before={};for(const [label,dir,names]of inputs)for(const name of names)before[label+'/'+name]=identity(path.join(dir,name));
let checks=0;const failures=[];
function check(ok,label){checks++;if(!ok)failures.push(label);}
function eq(a,b,label){check(JSON.stringify(a)===JSON.stringify(b),label);}
const raw=read(n0,'MESSAGES.json'),corpus=read(n0,'CORPUS.json'),dev=read(n0,'FOUR_DEVELOPMENT_SOURCE_INPUTS.json');
const prior=read(comparison,'TURN_COMPARISON.json'),policy=read(episodes,'POLICY.json'),report=read(episodes,'SELECTION_REPORT.json');
const allSaved=read(episodes,'ALL_ROOT_CANDIDATES.json'),selectedSaved=read(episodes,'FOUR_EPISODES.json');
const map=new Map();for(const m of raw){check(!map.has(m.message_id),'unique raw message '+m.message_id);map.set(m.message_id,m);}
const childCount=new Map(raw.map(m=>[m.message_id,0]));
for(const m of raw)if(m.parent_id!==null){check(map.has(m.parent_id),'parent exists '+m.message_id);childCount.set(m.parent_id,childCount.get(m.parent_id)+1);}
function chainFor(m){const chain=[],seen=new Set();while(m){check(!seen.has(m.message_id),'acyclic '+m.message_id);if(seen.has(m.message_id))break;seen.add(m.message_id);chain.push(m);m=m.parent_id===null?null:map.get(m.parent_id);}return chain.reverse();}
const paths=raw.filter(m=>childCount.get(m.message_id)===0).map(m=>{const chain=chainFor(m);check(chain.every((v,i)=>v.role===(i%2===0?'prompter':'assistant')),'alternating path '+m.message_id);return {root:chain[0].message_id,leaf:m.message_id,chain,users:chain.filter(v=>v.role==='prompter').map(v=>v.message_id)};});
const byLeaf=new Map(corpus.root_to_leaf_paths.map(p=>[p.leaf_message_id,p]));
eq(byLeaf.size,paths.length,'all raw leaf paths represented once');
for(const p of paths){const saved=byLeaf.get(p.leaf);check(!!saved,'raw path saved '+p.leaf);if(saved){eq(saved.message_ids,p.chain.map(v=>v.message_id),'raw exact source path '+p.leaf);eq(saved.user_message_ids,p.users,'raw source user sequence '+p.leaf);eq(saved.root,p.root,'raw path root '+p.leaf);}}
eq(policy.episode_user_turns,2,'exactly two user turns frozen');
eq(policy.root_rank_seed,'N1a-source-coverage-v1:root:','declared root seed');
eq(policy.leaf_rank_seed,'N1a-source-coverage-v1:leaf:','declared leaf seed');
const roots=raw.filter(m=>m.parent_id===null).map(m=>m.message_id).sort();
// Phase one fixes every eligible leaf and first two user IDs before prior
// geometry or necessary supplied-history compatibility is inspected.
const fixed=roots.map(root=>{const eligible=paths.filter(p=>p.root===root&&p.users.length>=2).map(p=>({...p,rank:sha(policy.leaf_rank_seed+p.leaf)})).sort((a,b)=>a.rank.localeCompare(b.rank)||a.leaf.localeCompare(b.leaf));return {root,eligible,chosen:eligible[0]||null};});
const priorMap=new Map(prior.map(r=>[r.message_id,r]));
const expected=fixed.map(({root,eligible,chosen:p})=>{
  if(!p)return {root,status:'NO_TWO_USER_TURN_SOURCE_PATH',not_dropped_from_denominator:true};
  const row=priorMap.get(p.users[1]);check(!!row,'prior second user row exists '+root);
  return {root,leaf:p.leaf,path_id:byLeaf.get(p.leaf).path_id,leaf_rank:p.rank,root_rank:sha(policy.root_rank_seed+root),user_message_ids:p.users.slice(0,2),source_paths_with_two_turns:eligible.length,status:row.provided_native_cap_and_stop_compatible?'NECESSARY_PROVIDED_HISTORY_COMPATIBLE':'PROVIDED_HISTORY_CAP_OR_STOP_INCOMPATIBLE',source_predicted_second_turn:{head:row.C.predicted_head,append:row.C.replayed_suffix_rows,partition_distinct:row.C.geometry.comparisons.projection_partition_distinct,actual_native_head:null,actual_free_generation_compatibility:null},not_dropped_from_denominator:true};
});
eq(expected,allSaved,'every root choice/hash/prior-row diagnostic matches independently reconstructed selection');
const eligible=expected.filter(r=>r.status==='NECESSARY_PROVIDED_HISTORY_COMPATIBLE');
const ranked=eligible.slice().sort((a,b)=>a.root_rank.localeCompare(b.root_rank)||a.root.localeCompare(b.root));
const chosen=[];for(const difference of [false,true])chosen.push(...ranked.filter(r=>r.source_predicted_second_turn.partition_distinct===difference).slice(0,2));
chosen.sort((a,b)=>a.root_rank.localeCompare(b.root_rank)||a.root.localeCompare(b.root));
const expectedSelected=chosen.map(r=>({...r,coverage_stratum:r.source_predicted_second_turn.partition_distinct?'PREDICTED_DIFFERENCE':'PREDICTED_NO_DIFFERENCE',users:r.user_message_ids.map(id=>({message_id:id,role:'user',content:map.get(id).text})),assistant_history_policy:'Future R generates its own responses; source supplied bodies are prediction provenance only',native_state:'NOT_RUN'}));
eq(selectedSaved,expectedSelected,'all four episode contents/category/hash ranks frozen exactly');
check(new Set(chosen.map(v=>v.root)).size===4,'four distinct roots');
const counts={source_roots:roots.length,source_paths:paths.length,source_messages:raw.length,source_turns:raw.filter(v=>v.role==='prompter').length,no_two_user_path:fixed.filter(v=>!v.chosen).length,fixed_path_necessary_incompatible:expected.filter(v=>v.status==='PROVIDED_HISTORY_CAP_OR_STOP_INCOMPATIBLE').length,eligible_fixed_path_roots:eligible.length,eligible_predicted_difference:eligible.filter(v=>v.source_predicted_second_turn.partition_distinct).length,eligible_predicted_no_difference:eligible.filter(v=>!v.source_predicted_second_turn.partition_distinct).length,selected:chosen.length,selected_predicted_difference:chosen.filter(v=>v.source_predicted_second_turn.partition_distinct).length,selected_predicted_no_difference:chosen.filter(v=>!v.source_predicted_second_turn.partition_distinct).length};
for(const [k,v]of Object.entries(counts))eq(report[k],v,'denominator '+k);
check(counts.no_two_user_path+counts.fixed_path_necessary_incompatible+counts.eligible_fixed_path_roots===counts.source_roots,'complete root denominator accounting');
for(const [name,wanted]of Object.entries(report.source_input_identities)){const got=before[(name==='TURN_COMPARISON.json'?'comparison/':'N0/')+name];eq(got,wanted,'frozen episode source identity '+name);}
const oldDev=dev.map(d=>({root:d.root,leaf:d.leaf,user_message_ids:d.user_message_ids,prior_prediction:d.user_message_ids.map(id=>{const r=priorMap.get(id);return {message_id:id,head:r.C.predicted_head,append:r.C.replayed_suffix_rows,difference:r.C.geometry.comparisons.projection_partition_distinct,necessary_provided_compatibility:r.provided_native_cap_and_stop_compatible};})}));
check(oldDev.every(d=>d.prior_prediction.every(p=>p.difference===false)),'all original four development episodes remain no-difference predictions');
const privacy=[];
for(const name of ['POLICY.json','SELECTION_REPORT.json','ALL_ROOT_CANDIDATES.json','FOUR_EPISODES.json']){
  const text=fs.readFileSync(path.join(episodes,name),'utf8');
  for(const [label,pattern]of [['absolute private home path',/\/(?:home|Users)\//],['private IPv4 address',/\b(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)\b/],['credential assignment',/\b(?:password|passwd|token|secret)\s*[:=]\s*["'][^"']{3,}/i]])if(pattern.test(text))privacy.push({file:name,kind:label});
}
eq(privacy,[],'episode packet does not expose host paths/private addresses/credential assignments');
for(const [label,dir,names]of inputs)for(const name of names)eq(identity(path.join(dir,name)),before[label+'/'+name],'source unchanged '+label+'/'+name);
const output={status:failures.length?'FAIL':'PASS',checks,failures,method:'Raw ancestry and source-only per-root leaf hash rank fixed before any lookup of immutable prior geometry; no selector/candidate implementation imports.',input_identities:before,denominators:{...counts,source_paths_with_at_least_two_user_turns:paths.filter(p=>p.users.length>=2).length},selected:expectedSelected.map(r=>({root:r.root,leaf:r.leaf,user_message_ids:r.user_message_ids,stratum:r.coverage_stratum,predicted_second_turn:r.source_predicted_second_turn})),original_four_development_episodes:oldDev,privacy_findings:privacy,scope:['Two-per-stratum development coverage is explicitly selected on prior predicted geometry after a source-only leaf choice. It is not representative sampling, natural frequency estimation, confirmation, or N2 admission.','Necessary supplied-history cap/stop compatibility filters provenance fixtures only. It neither establishes native producer compatibility nor predicts actual free-generation head, output, stop, prefix or grouping. These remain unobserved.','No chosen path or user message may be replaced after future R output. Source supplied assistant bodies are not the future generated responses.','All roots/path choices and incompatible/no-two-turn denominators are preserved; no token offset, padding, template, latency or acceptance search was performed.'],execution:{model_forwards:0,tokenizer_calls:0,native_contexts:0,GPU_contexts:0,placement_actions:0}};
fs.mkdirSync(out,{recursive:true});const file=path.join(out,'SELECTION_REVIEW.json');fs.writeFileSync(file,JSON.stringify(output,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:output.status,checks,failures,denominators:output.denominators,selected:output.selected,privacy_findings:privacy},null,2));if(failures.length)process.exitCode=1;
