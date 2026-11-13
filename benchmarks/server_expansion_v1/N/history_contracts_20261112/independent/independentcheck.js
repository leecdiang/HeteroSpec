'use strict';
// Independent saved-token replay: this file imports no experiment or tokenizer code.
// It performs no model, native adapter, placement or GPU operations.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const base = path.resolve(process.argv[2] || path.join(__dirname, '..'));
const n0 = path.resolve(process.argv[3] || path.join(base, '..', 'N0'));
const out = path.resolve(process.argv[4] || path.join(base, 'independent', 'CHECK_01'));
const saved = path.join(base, 'COMPARISON_01');
let assertions = 0;
const failures = [];
function check(ok, what) { assertions++; if (!ok) failures.push(what); }
function eq(a, b, what) { check(JSON.stringify(a) === JSON.stringify(b), what); }
function read(dir, name) { return JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8')); }
function identity(file) { const b = fs.readFileSync(file); return { bytes: b.length, sha256: crypto.createHash('sha256').update(b).digest('hex') }; }
const before = {};
// Explicit dependencies only: unrelated local notes are not public replay inputs.
const inputFiles = [
  [n0, ['SPEC.json','CORPUS.json','TURN_CENSUS.json','CENSUS_REPORT.json',
    'TOKENIZER_OUTPUT.jsonl','FOUR_DEVELOPMENT_SOURCE_INPUTS.json',
    'MESSAGES.json','chat_template.jinja']],
  [saved, ['FREEZE.json','REPORT.json','TURN_COMPARISON.json','PER_ROOT.json']]
];
for (const [dir,names] of inputFiles) for (const name of names) {
  const file = path.join(dir, name); before[file] = identity(file);
}
const freeze = read(saved, 'FREEZE.json');
const expectedReport = read(saved, 'REPORT.json');
const savedRows = read(saved, 'TURN_COMPARISON.json');
const savedRoots = read(saved, 'PER_ROOT.json');
const raw = read(n0, 'MESSAGES.json');
const corpus = read(n0, 'CORPUS.json');
const oldRows = read(n0, 'TURN_CENSUS.json');
const oldReport = read(n0, 'CENSUS_REPORT.json');
const spec = read(n0, 'SPEC.json');
const tokenizerLines = fs.readFileSync(path.join(n0, 'TOKENIZER_OUTPUT.jsonl'), 'utf8').trim().split('\n').map(JSON.parse);
const vocab = tokenizerLines[0];
const eog = new Set(vocab.eog);
eq([...eog].sort((a,b) => a-b), [128247,151643,151645,151662,151663,151664], 'all six EOG IDs');
eq(vocab.eos, 151645, 'provided EOG metadata');
check(vocab.vocab_only && vocab.forward_calls === 0 && vocab.context_creations === 0, 'original vocabulary zero-forward provenance');
const ids = new Map();
for (const row of tokenizerLines.slice(1)) {
  check(!ids.has(row.task_id), `unique tokenizer query ${row.task_id}`);
  check(row.vocab_only && row.forward_calls === 0 && row.add_special === false, `saved tokenizer provenance ${row.task_id}`);
  ids.set(row.task_id, row.prompt_ids);
}
// Validate the immutable freeze identities independently, including input bytes.
for (const [name, wanted] of Object.entries(freeze.inputs)) eq(identity(path.join(n0, name)), wanted, `frozen input identity ${name}`);
eq(identity(path.join(n0, 'chat_template.jinja')).sha256, freeze.template_sha256, 'frozen template identity');
eq(identity(path.join(n0, 'MESSAGES.json')).sha256, spec.messages_sha256, 'raw source identity from original spec');
eq(freeze.model, spec.model, 'same saved model identity');

// Resolve the corpus tree afresh from the original raw records, not corpus.py.
const byId = new Map();
for (const m of raw) { check(!byId.has(m.message_id), `unique raw message ${m.message_id}`); byId.set(m.message_id, m); }
const children = new Map(raw.map(m => [m.message_id, []]));
for (const m of raw) if (m.parent_id !== null) {
  check(byId.has(m.parent_id), `parent exists ${m.message_id}`);
  if (byId.has(m.parent_id)) children.get(m.parent_id).push(m.message_id);
}
function ancestry(m) {
  const result = [], seen = new Set();
  while (m) {
    check(!seen.has(m.message_id), `acyclic ancestry ${m.message_id}`);
    if (seen.has(m.message_id)) break;
    seen.add(m.message_id); result.push(m); m = m.parent_id === null ? null : byId.get(m.parent_id);
  }
  return result.reverse();
}
const chains = new Map();
for (const m of raw) {
  const chain = ancestry(m); chains.set(m.message_id, chain);
  check(chain[0].role === 'prompter', `user root ${m.message_id}`);
  check(chain.every((v,i) => v.role === (i % 2 === 0 ? 'prompter' : 'assistant')), `alternating roles ${m.message_id}`);
  check(chain.every(v => v.message_tree_id === chain[0].message_id), `declared/resolved root ${m.message_id}`);
}
const roots = raw.filter(m => m.parent_id === null);
const user = raw.filter(m => m.role === 'prompter');
const leaves = raw.filter(m => children.get(m.message_id).length === 0);
const covered = new Set(leaves.flatMap(m => chains.get(m.message_id).map(v => v.message_id)));
const counts = {
  source_message_rows: raw.length, supported_message_rows: raw.length, unsupported_message_rows: 0,
  declared_root_ids: new Set(raw.map(m => m.message_tree_id)).size, resolved_root_ids: roots.length, root_records: roots.length,
  user_source_rows: user.length, supported_unique_user_turns: user.length, unsupported_user_source_rows: 0,
  leaf_paths: leaves.length, supported_assistant_ending_paths: leaves.filter(m => m.role === 'assistant').length,
  supported_dangling_user_paths: leaves.filter(m => m.role === 'prompter').length, unsupported_leaf_paths: 0,
  path_expanded_user_turn_occurrences: leaves.reduce((s,m) => s + chains.get(m.message_id).filter(v => v.role === 'prompter').length,0),
  pathless_source_rows: raw.length-covered.size
};
eq(counts, corpus.counts, 'fresh raw-tree counts versus frozen census');
eq(counts, expectedReport.source_counts, 'fresh raw-tree counts versus comparison');
check(ids.size === raw.length, 'all original tokenizer queries accounted for');
eq(savedRows.map(v => v.message_id), user.map(v => v.message_id), 'comparison covers exactly the original ordered unique user rows');
eq(oldRows.map(v => v.message_id), user.map(v => v.message_id), 'frozen original ordered unique user rows');
const oldById = new Map(oldRows.map(v => [v.message_id,v]));
const savedById = new Map(savedRows.map(v => [v.message_id,v]));

// Independent dense geometry. The word "work" denotes token*extent, not time.
const q = 32, padding = 256, capacity = 4096, cap = 128;
function extent(end) { return padding * Math.ceil(end/padding); }
function atBoundary(p) { return padding - p % padding; }
function pieces(p, width) {
  const a=[]; for (let remaining=width; remaining>0;) { const w=Math.min(remaining,atBoundary(p)); a.push([p,w,extent(p+w)]); p+=w; remaining-=w; } return a;
}
function geometry(h, a) {
  const outer=[], inner=[], rechunk=[];
  for (let p=h; p<h+a;) { const w=Math.min(q,h+a-p); const groups=pieces(p,w); outer.push({p,w,envelope:extent(p+w),groups}); inner.push(...groups); p+=w; }
  for (let p=h; p<h+a;) { const w=Math.min(q,h+a-p,atBoundary(p)); rechunk.push([p,w,extent(p+w)]); p+=w; }
  const work = calls => calls.reduce((s,[,w,e]) => s+w*e,0);
  const partition = calls => calls.map(v => v.slice(0,2));
  const outerPartition=outer.map(v=>[v.p,v.w]);
  return {h,a,outer,inner,rechunk,work:work(inner),rechunkWork:work(rechunk),distinct:JSON.stringify(partition(rechunk))!==JSON.stringify(outerPartition)};
}
function auditGeometry(g, x, tag) {
  eq([g.head,g.append,g.q,g.padding,g.capacity], [x.h,x.a,q,padding,capacity], `${tag} geometry inputs`);
  check(g.native_head === null && g.native_kernel_dispatches === null && g.actual_physical_extent === null, `${tag} no native observation`);
  eq(g.capacity_admitted, x.h+x.a<=capacity, `${tag} geometry capacity`);
  for (const [name,wanted] of [['whole_fixed',x.inner],['whole_rechunk',x.rechunk],['local_inner',x.inner]]) {
    const s=g[name];
    eq(s.calls.map(v=>[v.position,v.width,v.predicted_attention_extent]), wanted, `${tag} ${name} every ordered call`);
    eq(s.call_count,wanted.length, `${tag} ${name} count`);
    eq(s.token_rows,x.a,`${tag} ${name} rows`);
    eq(s.predicted_padded_attention_work,x.work, `${tag} ${name} work`);
  }
  const s=g.local_outer;
  eq(s.calls.map(v=>({p:v.position,w:v.width,envelope:v.predicted_graph_extent_envelope,groups:v.attention_groups.map(t=>[t.position,t.width,t.predicted_attention_extent])})),x.outer,`${tag} local outer every ordered call/group`);
  check(s.calls.every(v=>v.envelope_is_not_attention_work===true),`${tag} local envelope disclaimer`);
  eq([s.call_count,s.projection_call_count,s.token_rows,s.predicted_padded_attention_work,s.attention_group_count], [x.outer.length,x.outer.length,x.a,x.work,x.inner.length],`${tag} local aggregate geometry`);
  eq(g.comparisons.projection_partition_distinct,x.distinct,`${tag} distinct projection partition`);
  const partition = a => a.map(v=>v.slice(0,2));
  const identical = (a,b) => JSON.stringify(a)===JSON.stringify(b);
  eq(g.comparisons.whole_fixed_vs_rechunk_identical_ordered_partition,identical(partition(x.inner),partition(x.rechunk)),`${tag} fixed/rechunk partition equality`);
  eq(g.comparisons.whole_rechunk_vs_local_outer_identical_ordered_partition,!x.distinct,`${tag} rechunk/outer partition equality`);
  eq(g.comparisons.whole_rechunk_vs_local_inner_identical_ordered_partition,identical(partition(x.rechunk),partition(x.inner)),`${tag} rechunk/inner partition equality`);
  eq(g.comparisons.whole_fixed_vs_local_inner_identical_ordered_partition,true,`${tag} fixed/inner partition equality`);
  eq(g.comparisons.rechunk_extra_graph_calls_over_local_projection,x.rechunk.length-x.outer.length,`${tag} extra rechunk calls`);
  eq(g.comparisons.local_extra_attention_groups_over_rechunk,x.inner.length-x.rechunk.length,`${tag} extra inner groups`);
  eq(g.comparisons.predicted_padded_attention_work_equal,x.work===x.rechunkWork,`${tag} work equality`);
  check(x.rechunk.length<=Math.ceil(x.a/q)+1,`${tag} applicable divisible-padding call bound`);
}
function lcp(a,b) { let n=0; while(n<Math.min(a.length,b.length)&&a[n]===b[n])n++; return n; }
const records=[];
for (const m of user) {
  const chain=chains.get(m.message_id), turn=(chain.length-1)/2, initial=turn===0;
  const row=savedById.get(m.message_id), a=oldById.get(m.message_id);
  const prompt=ids.get('prompt:'+m.message_id);
  check(Array.isArray(prompt),`saved canonical prompt ${m.message_id}`);
  eq(a.prompt_ids,prompt,`frozen A exact canonical token IDs ${m.message_id}`);
  const previousUser=initial?null:chain[chain.length-3];
  const assistant=initial?null:chain[chain.length-2];
  const old=initial?[]:[...ids.get('prompt:'+previousUser.message_id),...ids.get('body:'+assistant.message_id),151645];
  const head=initial?0:old.length-1;
  const common=lcp(old,prompt);
  let retain=Math.min(common,head);
  if(retain===prompt.length && prompt.length>0) retain--;
  const suffix=prompt.slice(retain);
  const full=old.length>0 && common===old.length;
  const priorBodies=chain.filter(v=>v.role==='assistant').map(v=>ids.get('body:'+v.message_id));
  const over=priorBodies.some(v=>v.length+1>cap);
  const embedded=priorBodies.some(v=>v.some(t=>eog.has(t)));
  const oldOver=priorBodies.some(v=>v.length>cap);
  const compatible=!over&&!embedded;
  const g=geometry(retain,suffix.length);
  const tag=m.message_id;
  eq([row.root,row.turn,row.next_canonical_tokens,row.materialized_head_prediction,row.pending_token_prediction], [chain[0].message_id,turn,prompt.length,head,initial?null:151645],`${tag} identity/input/head/pending`);
  eq([row.provided_native_cap_and_stop_compatible,row.prior_body_plus_supplied_EOG_over128,row.prior_embedded_EOG],[compatible,over,embedded],`${tag} necessary cap/stop diagnostics`);
  eq(row.A,{scope:'REUSED_FROZEN_A_RECORD_NOT_RERUN',status:a.status,prefix_reusable:a.prefix_reusable,predicted_head:a.predicted_execution_head,predicted_append_rows:a.predicted_append_rows,whole_rechunk_calls:a.geometry.whole_rechunk.call_count,LOCAL_outer_calls:a.geometry.local_outer.call_count},`${tag} reused exact frozen A reference`);
  eq([row.B.unchanged_canonical_input_compatible,row.B.later_full_prefix_preserved,row.B.predicted_old_head,row.B.valid_canonical_append_rows], [initial||full,initial?null:full,head,initial?prompt.length:full?prompt.length-old.length:null],`${tag} B incompatible append-only diagnostic`);
  eq(row.B.geometry_for_incompatible_contract,null,`${tag} B does not invent geometry`);
  eq([row.C.lcp_tokens,row.C.retained_tokens,row.C.predicted_head,row.C.replayed_suffix_rows,row.C.trimmed_materialized_rows],[common,retain,retain,suffix.length,head-retain],`${tag} bounded LCP repair`);
  eq(row.C.canonical_suffix_ids,suffix,`${tag} exact C canonical suffix`);
  const reconstructed=[...old.slice(0,retain),...suffix];
  eq(reconstructed,prompt,`${tag} independently reconstructed exact canonical input`);
  eq(row.C.canonical_input_reconstruction_equal,true,`${tag} declared reconstruction`);
  eq(row.C.old_full_logical_history_prefix,full,`${tag} old full prefix`);
  eq(row.C.mode,initial?'INITIAL_PREFILL':'LCP_TRIM_REPLAY',`${tag} C mode in this data`);
  eq(row.C.pending_disposition,initial?'NONE':'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX',`${tag} pending disposal`);
  check(initial || common<head,`${tag} pending is outside this reused prefix`);
  check(suffix.length>0,`${tag} suffix refreshes frontier before sampling`);
  eq([row.native_head,row.B.native_head,row.C.native_head,row.C.actual_context_identity],[null,null,null,null],`${tag} native unobserved`);
  check(row.C.reference_result_equivalence==='NOT_QUALIFIED',`${tag} no byte/state qualification claimed`);
  auditGeometry(row.C.geometry,g,tag);
  records.push({root:chain[0].message_id,message_id:tag,turn,initial,promptRows:prompt.length,oldLogicalRows:old.length,head,common,retain,append:suffix.length,full,over,embedded,oldOver,compatible,capacityOK:prompt.length+cap-1<=capacity,g});
}

function aggregate(rows) {
  const z={turns:rows.length,initial:0,later:0,A_later_full_prefix_reusable:0,B_later_canonical_compatible:0,B_later_canonical_incompatible:0,C_old_full_history_prefix_reusable:0,C_later_nonempty_retained_prefix:0,C_canonical_token_reconstructions_equal:rows.length,C_source_conditional_distinct_rechunk_LOCAL_partitions:0,C_retained_prefix_token_occurrences:0,A_full_prompt_rows:0,C_replayed_suffix_rows:0,C_predicted_whole_rechunk_calls:0,C_predicted_LOCAL_outer_calls:0,C_predicted_LOCAL_inner_attention_groups:0,C_extra_whole_rechunk_calls:0,C_all_predicted_attention_work_equal:true,capacity_unsupported:0,actual_native_heads:0,actual_compatible_free_generation_histories:0};
  for(const r of rows){z[r.initial?'initial':'later']++;if(!r.initial){z.A_later_full_prefix_reusable+=Number(oldById.get(r.message_id).prefix_reusable===true);z.B_later_canonical_compatible+=Number(r.full);z.B_later_canonical_incompatible+=Number(!r.full);z.C_old_full_history_prefix_reusable+=Number(r.full);z.C_later_nonempty_retained_prefix+=Number(r.retain>0);}z.C_source_conditional_distinct_rechunk_LOCAL_partitions+=Number(r.g.distinct);z.C_retained_prefix_token_occurrences+=r.retain;z.A_full_prompt_rows+=r.promptRows;z.C_replayed_suffix_rows+=r.append;z.C_predicted_whole_rechunk_calls+=r.g.rechunk.length;z.C_predicted_LOCAL_outer_calls+=r.g.outer.length;z.C_predicted_LOCAL_inner_attention_groups+=r.g.inner.length;z.C_extra_whole_rechunk_calls+=r.g.rechunk.length-r.g.outer.length;z.C_all_predicted_attention_work_equal&&=r.g.work===r.g.rechunkWork;z.capacity_unsupported+=Number(!r.capacityOK);}
  return z;
}
const all=aggregate(records), compatible=records.filter(v=>v.compatible), later=records.filter(v=>!v.initial), compatibleLater=compatible.filter(v=>!v.initial);
eq(all,expectedReport.all_provided_histories,'all-history aggregate independent replay');
eq(aggregate(compatible),expectedReport.necessary_cap_stop_compatible_diagnostic,'necessary cap/stop diagnostic aggregate independent replay');
eq(records.filter(v=>!v.compatible).length,expectedReport.overcap_or_stop_incompatible_histories,'new incompatibility denominator');
const rootSet=new Set(records.filter(v=>v.g.distinct).map(v=>v.root));
eq(rootSet.size,expectedReport.C_distinct_roots,'all-history distinct roots');
const rootStats=roots.map(root=>({root:root.message_id,...aggregate(records.filter(v=>v.root===root.message_id))}));
eq(rootStats,savedRoots,'every independently reconstructed per-root aggregate');
eq(expectedReport.A_frozen_result_reference,{turns:oldRows.length,mismatches:oldReport.canonical_prefix_mismatch_predictions,decision:oldReport.decision},'A unchanged frozen decision/reference');
check(expectedReport.model_forwards===0&&expectedReport.GPU_contexts_created===0&&expectedReport.placement_actions===0&&expectedReport.new_tokenizer_calls===0&&expectedReport.N0_rerun===false,'comparison explicitly no execution');

function extrema(rows) {
  const r={turns:rows.length};
  for(const [label,key] of [['retained_head','retain'],['replayed_append','append'],['canonical_prompt','promptRows'],['prior_materialized_head','head']]) r[label]={min:Math.min(...rows.map(v=>v[key])),max:Math.max(...rows.map(v=>v[key]))};
  r.distinct_turns=rows.filter(v=>v.g.distinct).length;
  r.distinct_roots=new Set(rows.filter(v=>v.g.distinct).map(v=>v.root)).size;
  return r;
}
const changedCompatibility=records.filter(v=>v.over!==v.oldOver).map(v=>({root:v.root,message_id:v.message_id,turn:v.turn,old_body_only_over128:v.oldOver,new_body_plus_EOG_over128:v.over,all_prior_body_lengths:chains.get(v.message_id).filter(m=>m.role==='assistant').map(m=>ids.get('body:'+m.message_id).length)}));
const compatibility={new_incompatible:records.filter(v=>!v.compatible).length,old_body_only_overcap:records.filter(v=>v.oldOver).length,new_body_plus_EOG_overcap:records.filter(v=>v.over).length,embedded_EOG:records.filter(v=>v.embedded).length,changed_cap_flag_turns:changedCompatibility};
eq(compatibility.old_body_only_overcap,oldReport.history_contains_response_over_cap128_turns,'original body-only over-cap diagnostic');
check(compatibility.new_incompatible===616 && compatibility.old_body_only_overcap===614 && changedCompatibility.length===2,'exact cap128 plus hypothetical EOG correction');
const emptyThink=[151667,271,151668,271];
let firstDifferenceAtPreviousEmptyThink=0;
for(const r of later){const chain=chains.get(r.message_id);const previousPrompt=ids.get('prompt:'+chain[chain.length-3].message_id);eq(previousPrompt.slice(-4),emptyThink,`prior frozen empty-think suffix ${r.message_id}`);if(r.common===previousPrompt.length-4)firstDifferenceAtPreviousEmptyThink++;}
eq(firstDifferenceAtPreviousEmptyThink,later.length,'all supplied-history prefix mismatches occur at prior empty-think stub start');
// Verify every observed input remains byte-identical. The report is written elsewhere.
for(const [file,wanted] of Object.entries(before))eq(identity(file),wanted,`read-only original/comparison retained ${path.basename(file)}`);
const publicIdentities=Object.fromEntries(Object.entries(before).map(([file,id])=>[`${path.dirname(file)===n0?'N0':'comparison'}/${path.basename(file)}`,id]));
const report={schema:'heterospec.N.history-contracts.independent.saved-token-replay.v1',status:failures.length?'FAIL':'PASS',assertions,failures,method:'Standalone Node implementation using raw source ancestry and immutable saved vocabulary/token IDs only; imports no predecessor or candidate comparison/contract/geometry code.',execution:{model_forwards:0,GPU_contexts:0,placement_actions:0,new_tokenizer_calls:0,native_adapter_calls:0,N0_rerun:false},input_identities:publicIdentities,source_counts:counts,all_provided_histories:all,necessary_cap_stop_compatible_diagnostic:aggregate(compatible),extrema:{all:extrema(records),all_later:extrema(later),necessary_compatible:extrema(compatible),necessary_compatible_later:extrema(compatibleLater),necessary_compatible_distinct:extrema(compatibleLater.filter(v=>v.g.distinct))},compatible_distinct_roots:new Set(compatibleLater.filter(v=>v.g.distinct).map(v=>v.root)).size,compatibility_correction:compatibility,first_difference:{later_turns:later.length,at_prior_empty_think_start:firstDifferenceAtPreviousEmptyThink,prior_suffix_ids:emptyThink},limits:['Supplied-history body IDs plus a hypothetical provided EOG are not observed generation, pending tokens, stop reasons, heads or teacher-forced native replay. Necessary cap/stop compatibility is not sufficient for actual greedy/free-generation compatibility.','The compatible-history diagnostic is an accounting sensitivity view, not a selected experimental cohort. No unfavorable source row was dropped from the primary denominator.','Common token-LCP reuse versus full rebuild is shared by all C arms and is not a LOCAL benefit. Remaining LOCAL opportunity is only ordered predicted graph/projection partition and call differences, with equal predicted padded attention work.','Upstream source-supported trim/replay is a proposed integration in the N worker, not a deployed/qualified resident service. Exact canonical reconstruction does not prove full vectors, active KV/frontier, pending, EOG or state equivalence.','No latency, speedup, physical kernel dispatch or arithmetic-equivalence result is inferred. The 38 compatible distinct turns alone do not establish a meaningful performance opportunity.']};
fs.mkdirSync(out,{recursive:true});
const reportFile=path.join(out,'INDEPENDENT_REPORT.json');
if(fs.existsSync(reportFile))throw new Error('Refusing to overwrite existing check output: '+reportFile);
fs.writeFileSync(reportFile,JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(out,'PER_TURN_REPLAY.json'),JSON.stringify(records.map(({g,...r})=>({...r,whole_rechunk_calls:g.rechunk.length,LOCAL_outer_calls:g.outer.length,LOCAL_inner_groups:g.inner.length,distinct_partition:g.distinct,predicted_attention_work:g.work})),null,2)+'\n');
console.log(JSON.stringify({status:report.status,assertions,failures,all,compatible:aggregate(compatible),extrema:report.extrema,compatible_distinct_roots:report.compatible_distinct_roots,compatibility},null,2));
process.exitCode=failures.length?1:0;
