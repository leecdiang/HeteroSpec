// Independent saved-data census verification. No Python, tokenizer, model,
// networking, GPU or frozen experiment module is invoked.
// node verify_saved_census.js CENSUS_DIRECTORY FRESH_REPORT_DIRECTORY
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const base=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
assert(!fs.existsSync(out),'Fresh independent report directory required');fs.mkdirSync(out);
const read=name=>JSON.parse(fs.readFileSync(path.join(base,name),'utf8'));
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const sort=x=>Array.isArray(x)?x.map(sort):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,sort(x[k])])):x;
const canonical=x=>JSON.stringify(sort(x));
const count=xs=>{const c={};for(const x of xs)c[x]=(c[x]||0)+1;return c;};
const sum=xs=>xs.reduce((a,b)=>a+b,0),equal=(a,b,msg)=>assert.deepEqual(a,b,msg);
const write=(name,value)=>fs.writeFileSync(path.join(out,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
let began=Date.now();
try {
 const spec=read('SPEC.json');assert.equal(spec.GPU_authorized,false);assert.equal(spec.model_forward_authorized,false);
 assert.equal(spec.history_origin||'provided_conversation','provided_conversation');
 const assets=[];
 for(const [name,expected]of [['MESSAGES.json',spec.messages_sha256],['chat_template.jinja',spec.chat_template_sha256]]){
  const bytes=fs.readFileSync(path.join(base,name));assert.equal(hash(bytes),expected,name+' exact saved-byte binding');assets.push({file:name,bytes:bytes.length,sha256:expected,verified:true});
 }
 const sourceChecks=[];
 for(const [name,expected]of Object.entries(spec.source_files)){
  const relative=fs.existsSync(path.join(base,'source',name))?'source/'+name:name;
  const filename=path.join(base,relative);if(fs.existsSync(filename)){
   const bytes=fs.readFileSync(filename);assert.equal(hash(bytes),expected,'Frozen source '+name);sourceChecks.push({file:relative,sha256:expected,verified:true});
  }else sourceChecks.push({file:name,sha256:expected,verified:false,reason:'FROZEN_SOURCE_BYTES_NOT_PRESENT_IN_THIS_SAVED_PACKET'});
 }
 const assetDir=fs.existsSync(path.join(base,'assets'))?'assets/':'';
 const parquets=fs.readdirSync(path.join(base,assetDir)).filter(n=>n.endsWith('.parquet')).map(n=>assetDir+n);
 if(parquets.length){assert.equal(parquets.length,1,'One fixed source parquet expected');const b=fs.readFileSync(path.join(base,parquets[0]));assert.equal(b.length,spec.source.bytes);assert.equal(hash(b),spec.source.sha256);assets.push({file:parquets[0],bytes:b.length,sha256:hash(b),verified:true});}
 else assets.push({file:'FIXED_SOURCE_PARQUET',bytes:spec.source.bytes,sha256:spec.source.sha256,verified:false,reason:'SOURCE_PARQUET_NOT_PRESENT_LOCALLY'});
 for(const [file,expected,bytesExpected]of [['assets/README.md','68483ac2fcc2f3f7779f453352363827678070ef35b6d746ccb2ca6958540fff',10168],['assets/LICENSE','c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4',11357]]){
  if(fs.existsSync(path.join(base,file))){const b=fs.readFileSync(path.join(base,file));assert.equal(b.length,bytesExpected);assert.equal(hash(b),expected);assets.push({file,bytes:b.length,sha256:expected,verified:true});}
  else assets.push({file,bytes:bytesExpected,sha256:expected,verified:false,reason:'FIXED_LICENSE_OR_CARD_NOT_PRESENT_LOCALLY'});
 }
 for(const [file,digest]of [['MODEL_GGUF',spec.model.sha256],['VOCABULARY_EXECUTABLE',spec.tokenizer_executable_sha256]])assets.push({file,sha256:digest,verified:false,reason:'EXTERNAL_EXECUTION_VERIFIED_SPEC_BINDING; LARGE_ASSET_NOT_INDEPENDENTLY_REHASHED_IN_THIS_SAVED_PACKET'});
 const vocabSource='VOCABULARY_SOURCE.cpp';
 if(fs.existsSync(path.join(base,vocabSource))){const b=fs.readFileSync(path.join(base,vocabSource));assert.equal(hash(b),spec.tokenizer_source_sha256);assets.push({file:vocabSource,bytes:b.length,sha256:spec.tokenizer_source_sha256,verified:true});}
 else assets.push({file:vocabSource,sha256:spec.tokenizer_source_sha256,verified:false,reason:'VOCABULARY_SOURCE_NOT_PRESENT_LOCALLY'});

 // Rebuild all tree paths directly from raw message rows, before reading corpus
 // or converted turn outcomes. Actual bound data must satisfy its declared
 // schema; unsupported handling is tested separately in the CPU corpus tests.
 const raw=read('MESSAGES.json');assert.equal(raw.length,spec.source.messages);
 const index=new Map();for(let i=0;i<raw.length;i++){
  const r=raw[i];assert(r&&typeof r==='object');assert.equal(typeof r.message_id,'string');assert(!index.has(r.message_id),'Duplicate source ID');
  assert.equal(typeof r.message_tree_id,'string');assert(['prompter','assistant'].includes(r.role));assert.equal(typeof r.text,'string');
  assert(r.parent_id===null||typeof r.parent_id==='string');index.set(r.message_id,{...r,source_index:i});
 }
 const chains=new Map(),children=new Map();
 for(const r of raw)if(r.parent_id!==null){assert(index.has(r.parent_id),'Source orphan');children.set(r.parent_id,(children.get(r.parent_id)||0)+1);}
 for(const r of raw){let node=index.get(r.message_id),seen=new Set(),chain=[];
  while(node){assert(!seen.has(node.message_id),'Source cycle');seen.add(node.message_id);chain.push(node);node=node.parent_id===null?null:index.get(node.parent_id);}
  chain.reverse();const root=chain[0].message_id;
  chain.forEach((x,i)=>{assert.equal(x.message_tree_id,root);assert.equal(x.role,i%2?'assistant':'prompter');});chains.set(r.message_id,chain);
 }
 const users=raw.filter(x=>x.role==='prompter'),roots=[...new Set(raw.map(x=>x.message_tree_id))].sort();
 const paths=raw.filter(x=>!children.has(x.message_id)).map(leaf=>{
  const chain=chains.get(leaf.message_id),message_ids=chain.map(x=>x.message_id),root=chain[0].message_id;
  const identity={leaf_source_index:index.get(leaf.message_id).source_index,root,message_ids};
  return {path_id:hash(canonical(identity)),root,leaf_message_id:leaf.message_id,message_ids,
   user_message_ids:chain.filter(x=>x.role==='prompter').map(x=>x.message_id),terminal_role:leaf.role};
 });
 const independentCounts={source_message_rows:raw.length,supported_message_rows:raw.length,unsupported_message_rows:0,
  declared_root_ids:roots.length,resolved_root_ids:roots.length,root_records:roots.length,user_source_rows:users.length,
  supported_unique_user_turns:users.length,unsupported_user_source_rows:0,leaf_paths:paths.length,
  supported_assistant_ending_paths:paths.filter(x=>x.terminal_role==='assistant').length,
  supported_dangling_user_paths:paths.filter(x=>x.terminal_role==='prompter').length,unsupported_leaf_paths:0,
  path_expanded_user_turn_occurrences:sum(paths.map(x=>x.user_message_ids.length)),pathless_source_rows:0};

 // A separately implemented normal form of the actual, hash-pinned Qwen
 // template for the declared tools=None/basic role contract. No Jinja call.
 assert.equal(spec.renderer.tools,null);assert.equal(spec.renderer.add_generation_prompt,true);assert.equal(spec.renderer.enable_thinking,false);
 const trimLeft=s=>s.replace(/^\n+/,''),trimRight=s=>s.replace(/\n+$/,''),trimBoth=s=>s.replace(/^\n+|\n+$/g,'');
 function render(chain){
  let lastQuery=chain.length-1;
  for(let i=chain.length-1;i>=0;i--)if(chain[i].role==='prompter'&&!(chain[i].text.includes('<tool_response>')&&chain[i].text.includes('</tool_response>'))){lastQuery=i;break;}
  let text='';for(let i=0;i<chain.length;i++){
   const msg=chain[i];if(msg.role==='prompter')text+='<|im_start|>user\n'+msg.text+'<|im_end|>\n';
   else {let content=msg.text,reasoning='';if(content.includes('</think>')){content=trimLeft(msg.text.split('</think>').at(-1));reasoning=trimLeft(trimRight(msg.text.split('</think>')[0]).split('<think>').at(-1));}
    text+='<|im_start|>assistant\n';
    if(i>lastQuery&&(i===chain.length-1||reasoning))text+='<think>\n'+trimBoth(reasoning)+'\n</think>\n\n'+trimLeft(content);else text+=content;
    text+='<|im_end|>\n';
   }
  }
  return text+'<|im_start|>assistant\n<think>\n\n</think>\n\n';
 }
 const inputs=fs.readFileSync(path.join(base,'TOKENIZER_INPUT.jsonl'),'utf8').trim().split('\n').map(JSON.parse),inputMap=new Map();
 for(const q of inputs){assert(!inputMap.has(q.task_id));assert.equal(q.add_special,false);inputMap.set(q.task_id,q);}
 const expectedTaskIds=[];for(const r of users){const id='prompt:'+r.message_id;expectedTaskIds.push(id);equal(inputMap.get(id).formatted_prompt,render(chains.get(r.message_id)),'Independently rendered prompt '+r.message_id);}
 for(const r of raw)if(r.role==='assistant'&&r.text){const id='body:'+r.message_id;expectedTaskIds.push(id);equal(inputMap.get(id).formatted_prompt,r.text,'Verbatim assistant body');}
 equal([...inputMap.keys()].sort(),expectedTaskIds.sort());
 const tokenLines=fs.readFileSync(path.join(base,'TOKENIZER_OUTPUT.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
 const vocabs=tokenLines.filter(x=>x.event==='vocabulary');assert.equal(vocabs.length,1);const vocab=vocabs[0];
 assert.equal(vocab.vocab_only,true);assert.equal(vocab.forward_calls,0);assert.equal(vocab.context_creations,0);assert.equal(vocab.add_bos,false);assert.equal(vocab.add_eos,false);assert(vocab.eog.includes(spec.provided_history_eog_id));
 vocab.tokens.forEach((x,i)=>assert.equal(x.id,i));
 const tokens=new Map();for(const r of tokenLines.filter(x=>x.event!=='vocabulary')){
  assert(inputMap.has(r.task_id));assert(!tokens.has(r.task_id));assert.equal(r.vocab_only,true);assert.equal(r.forward_calls,0);assert.equal(r.add_special,false);
  assert(Array.isArray(r.prompt_ids));r.prompt_ids.forEach(x=>assert(Number.isSafeInteger(x)&&x>=0&&x<vocab.tokens.length));
  equal(r.native_detokenized_prompt,inputMap.get(r.task_id).formatted_prompt,'Native detokenization roundtrip');
  equal(r.native_raw_piece_prompt,inputMap.get(r.task_id).formatted_prompt,'Native raw-piece roundtrip');tokens.set(r.task_id,r.prompt_ids);
 }
 equal([...tokens.keys()].sort(),[...inputMap.keys()].sort());for(const r of raw)if(r.role==='assistant'&&!r.text)tokens.set('body:'+r.message_id,[]);

 // Direct per-token construction, independent of the Python schedule module.
 // Fixed and LOCAL inner partitions inherit q outer groups; strong rechunk
 // restarts q groups after every padding boundary.
 const q=spec.q,P=spec.padding,C=spec.context,cap=spec.cap;assert.equal(q,32);assert.equal(P,256);assert.equal(C,4096);assert.equal(cap,128);
 function segment(pos,width){return {position:pos,width,predicted_attention_extent:P*Math.ceil((pos+width)/P)};}
 function inner(pos,width){const result=[];let start=pos;for(let j=1;j<=width;j++)if(j===width||Math.floor((pos+j-1)/P)!==Math.floor((pos+j)/P)){result.push(segment(start,pos+j-start));start=pos+j;}return result;}
 function geometry(head,append){
  const outer=[],fixed=[];for(let at=head;at<head+append;at+=q){const width=Math.min(q,head+append-at),groups=inner(at,width);outer.push({position:at,width,predicted_graph_extent_envelope:P*Math.ceil((at+width)/P),attention_groups:groups});fixed.push(...groups);}
  const rechunk=[];let at=head;while(at<head+append){const width=Math.min(q,head+append-at,P-at%P);rechunk.push(segment(at,width));at+=width;}
  const summary=x=>({call_count:x.length,token_rows:sum(x.map(y=>y.width)),predicted_padded_attention_work:sum(x.map(y=>y.width*y.predicted_attention_extent))});
  const f=summary(fixed),r=summary(rechunk),bound=Math.ceil(append/q)+1;
  assert.equal(f.token_rows,append);assert.equal(r.token_rows,append);assert.equal(f.predicted_padded_attention_work,r.predicted_padded_attention_work);if(P%q===0)assert(rechunk.length<=bound);
  const partition=x=>x.map(y=>[y.position,y.width]);
  return {outer,fixed,rechunk,localInner:fixed,fixedSummary:f,rechunkSummary:r,partitionDistinct:canonical(partition(rechunk))!==canonical(partition(outer)),bound};
 }
 const independent=[];for(const user of users){
  const chain=chains.get(user.message_id),ids=tokens.get('prompt:'+user.message_id),initial=chain.length===1,n=ids.length;
  const prior=chain.slice(0,-1).filter(x=>x.role==='assistant');let prev=[],lcp=0,prefix=true,firstDifference=null;
  if(!initial){const reply=tokens.get('body:'+chain.at(-2).message_id),previousPrompt=tokens.get('prompt:'+chain.at(-3).message_id);prev=[...previousPrompt,...reply,spec.provided_history_eog_id];while(lcp<Math.min(prev.length,ids.length)&&prev[lcp]===ids[lcp])lcp++;prefix=ids.length>=prev.length&&lcp===prev.length;
   if(!prefix){const stub=[151667,271,151668,271];firstDifference={token_index:lcp,old_token_id:prev[lcp]??null,new_token_id:ids[lcp]??null,
    previous_prompt_tokens:previousPrompt.length,previous_prompt_ends_empty_think_stub:canonical(previousPrompt.slice(-4))===canonical(stub),
    difference_at_previous_prompt_empty_think_start:lcp===previousPrompt.length-4,
    old_token_is_think_start:prev[lcp]===151667,new_token_is_think_start:ids[lcp]===151667};}
  }
  const head=initial||!prefix?0:prev.length-1,append=n-head,admitted=n+cap-1<=C;
  const oldOverCap=prior.some(x=>tokens.get('body:'+x.message_id).length>cap),embeddedEOG=prior.some(x=>tokens.get('body:'+x.message_id).some(i=>vocab.eog.includes(i)));
  const completeOverCap=prior.some(x=>tokens.get('body:'+x.message_id).length+1>cap);
  const lifecycle=initial?'INITIAL_PREFILL':prefix?'PREFIX_REUSABLE_PREDICTION':'COMMON_REBUILD_REQUIRED';
  independent.push({message_id:user.message_id,root:chain[0].message_id,turn:(chain.length-1)/2,initial,prompt_ids:ids,prompt_tokens:n,
   prefix:initial?null:prefix,lcp:initial?null:lcp,previous:initial?null:prev.length,pending:initial?null:prev.at(-1),head,append,admitted,lifecycle,status:admitted?lifecycle:'UNSUPPORTED_CAPACITY',
   oldOverCap,embeddedEOG,completeOverCap,bodyExactlyCap:prior.some(x=>tokens.get('body:'+x.message_id).length===cap),
   nativeCapCompatibleHypothesis:!completeOverCap&&!embeddedEOG,firstDifference,geometry:admitted?geometry(head,append):null});
 }

 // Only after independently constructing histories, schedules and dimensions
 // read the saved implementation's converted rows/corpus/report.
 const savedCorpus=read('CORPUS.json');equal(savedCorpus.raw_messages,raw);equal(savedCorpus.counts,independentCounts);
 assert.equal(savedCorpus.message_records.length,raw.length);for(const r of savedCorpus.message_records){const chain=chains.get(r.message_id);assert.equal(r.status,'SUPPORTED');equal(r.issues,[]);equal(r.chain_to_node,chain.map(x=>x.message_id));equal(r.chain_source_indices,chain.map(x=>x.source_index));assert.equal(r.root,chain[0].message_id);}
 equal(savedCorpus.pathless_source_indices,[]);assert.equal(savedCorpus.root_to_leaf_paths.length,paths.length);
 paths.forEach((p,i)=>{const s=savedCorpus.root_to_leaf_paths[i];for(const k of ['path_id','root','leaf_message_id','message_ids','user_message_ids','terminal_role'])equal(s[k],p[k]);assert.equal(s.status,'SUPPORTED');assert.equal(s.independent_root_unit,false);});
 const savedRows=read('TURN_CENSUS.json');assert.equal(savedRows.length,independent.length);const rowMap=new Map(savedRows.map(x=>[x.message_id,x]));assert.equal(rowMap.size,independent.length);
 const totalCalls={whole_fixed:0,whole_rechunk:0,local_outer:0,local_inner:0};
 for(const r of independent){const s=rowMap.get(r.message_id);assert(s);
  equal(s.root,r.root);equal(s.turn,r.turn);equal(s.status,r.status);assert.equal(s.native_head,null);assert.equal(s.head_observed,false);assert.equal(s.head_source,'token_geometry_prediction');assert.equal(s.history_origin,'provided_conversation');assert.equal(s.not_dropped_from_denominator,true);assert.equal(s.causal_native_or_performance_claim,false);
  equal(s.prompt_ids,r.prompt_ids);assert.equal(s.prompt_tokens,r.prompt_tokens);assert.equal(s.prompt_sha256,hash(canonical(r.prompt_ids)));assert.equal(s.formatted_prompt_sha256,hash(inputMap.get('prompt:'+r.message_id).formatted_prompt));
  equal(s.prefix_reusable,r.prefix);equal(s.token_prefix_lcp,r.lcp);equal(s.previous_provided_chain_tokens,r.previous);equal(s.predicted_pending_id,r.pending);
  assert.equal(s.predicted_head_before_pending,r.initial?0:r.previous-1);assert.equal(s.predicted_execution_head,r.head);assert.equal(s.predicted_append_rows,r.append);assert.equal(s.common_rebuild_rows,!r.initial&&!r.prefix?r.prompt_tokens:0);
  assert.equal(s.provided_history_has_response_over_cap128,r.oldOverCap);assert.equal(s.provided_history_has_embedded_eog,r.embeddedEOG);assert.equal(s.capacity_admitted,r.admitted);assert.equal(s.capacity_required_worst_case,r.prompt_tokens+127);assert.equal(s.lifecycle_if_capacity_admitted,r.lifecycle);
  if(!r.admitted){assert.equal(s.geometry,null);continue;}const g=s.geometry,x=r.geometry;
  for(const [k,v]of Object.entries({head:r.head,append:r.append,q,padding:P,capacity:C,head_observed:false,native_head:null,capacity_admitted:true,not_performance_or_numerical_evidence:true}))equal(g[k],v);
  equal(g.whole_fixed.calls,x.fixed);equal(g.whole_rechunk.calls,x.rechunk);equal(g.local_inner.calls,x.localInner);
  equal(g.local_outer.calls.map(({extent_scope,...rest})=>rest),x.outer);
  for(const [key,summary]of [['whole_fixed',x.fixedSummary],['whole_rechunk',x.rechunkSummary],['local_inner',x.fixedSummary]])for(const [k,v]of Object.entries(summary))equal(g[key][k],v);
  assert.equal(g.local_outer.call_count,x.outer.length);assert.equal(g.local_outer.projection_call_count,x.outer.length);assert.equal(g.local_outer.token_rows,r.append);assert.equal(g.local_outer.attention_group_count,x.fixed.length);assert.equal(g.local_outer.split_outer_calls,x.outer.filter(y=>y.attention_groups.length>1).length);assert.equal(g.local_outer.predicted_padded_attention_work,x.fixedSummary.predicted_padded_attention_work);assert.equal(g.local_outer.native_kernel_dispatches,null);
  assert.equal(g.whole_rechunk.divisible_padding_call_bound,x.bound);assert.equal(g.comparisons.projection_partition_distinct,x.partitionDistinct);assert.equal(g.comparisons.predicted_padded_attention_work_equal,true);
  const part=a=>a.map(y=>[y.position,y.width]),same=(a,b)=>canonical(part(a))===canonical(part(b));
  for(const [k,v]of Object.entries({whole_fixed_vs_rechunk_identical_ordered_partition:same(x.fixed,x.rechunk),whole_rechunk_vs_local_outer_identical_ordered_partition:same(x.rechunk,x.outer),whole_rechunk_vs_local_inner_identical_ordered_partition:same(x.rechunk,x.localInner),whole_fixed_vs_local_inner_identical_ordered_partition:true,whole_fixed_extra_graph_calls_over_rechunk:x.fixed.length-x.rechunk.length,rechunk_extra_graph_calls_over_local_projection:x.rechunk.length-x.outer.length,local_extra_attention_groups_over_rechunk:x.fixed.length-x.rechunk.length}))equal(g.comparisons[k],v);
  for(const k of Object.keys(totalCalls))totalCalls[k]+=g[k].call_count;
 }
 const report=read('CENSUS_REPORT.json'),statuses=count(independent.map(x=>x.status));
 const expanded=count(paths.flatMap(p=>p.user_message_ids.map(id=>independent.find(x=>x.message_id===id).status)));
 const admitted=independent.filter(x=>x.admitted),noninitial=independent.filter(x=>!x.initial),distinct=admitted.filter(x=>x.geometry.partitionDistinct);
 const metrics={message_count:raw.length,unique_user_turns:users.length,unique_turn_status_counts:statuses,path_expanded_turn_status_counts:expanded,noninitial_unique_turns:noninitial.length,true_token_prefix_reusable_predictions:noninitial.filter(x=>x.prefix).length,canonical_prefix_mismatch_predictions:noninitial.filter(x=>!x.prefix).length,history_contains_response_over_cap128_turns:independent.filter(x=>x.oldOverCap).length,capacity_unsupported_turns:independent.filter(x=>!x.admitted).length,admitted_geometry_turns:admitted.length,distinct_strong_rechunk_vs_LOCAL_projection_partitions:distinct.length,all_admitted_predicted_attention_work_equal:true,unique_admitted_total_rows:sum(admitted.map(x=>x.append)),total_predicted_calls:totalCalls};
 for(const [k,v]of Object.entries(metrics))equal(report[k],v,'Independent census metric '+k);equal(report.source_counts,independentCounts);
 for(const k of ['model_forward_calls','GPU_requests','model_context_creations','native_head_observations'])assert.equal(report[k],0);
 for(const k of ['source','model','renderer','chat_template_sha256','tokenizer_executable_sha256'])equal(report[k],spec[k]);
 assert.equal(report.decision,distinct.length?'UNRESOLVED_STRUCTURAL_QUESTION_REQUIRES_NEW_GPU_ADMISSION':'NO_DISTINCT_CUT_OPPORTUNITY_UNDER_FROZEN_PROVIDED_HISTORY_CONTRACT_STOP_GPU_PANEL');
 const eligibleRoots=new Map();for(const p of paths)if(p.terminal_role==='assistant'&&p.user_message_ids.length>=2){if(!eligibleRoots.has(p.root))eligibleRoots.set(p.root,[]);eligibleRoots.get(p.root).push(p);}
 const chosen=[...eligibleRoots.keys()].sort((a,b)=>{const x=hash('N200-dev-v1:'+a),y=hash('N200-dev-v1:'+b);return x<y?-1:x>y?1:0;}).slice(0,4);
 const dev=read('FOUR_DEVELOPMENT_SOURCE_INPUTS.json');assert.equal(dev.length,chosen.length);
 chosen.forEach((root,i)=>{const p=eligibleRoots.get(root).sort((a,b)=>a.leaf_message_id<b.leaf_message_id?-1:1)[0];equal(dev[i].root,root);equal(dev[i].leaf,p.leaf_message_id);equal(dev[i].user_message_ids,p.user_message_ids.slice(0,4));assert.equal(dev[i].source_only_max_turns,4);});

 const compatible=independent.filter(x=>x.nativeCapCompatibleHypothesis),compatibleLater=compatible.filter(x=>!x.initial),compatibleGeometry=compatible.filter(x=>x.admitted);
 const differences=noninitial.filter(x=>x.firstDifference).map(x=>x.firstDifference);
 const tokenHistogram=(values)=>Object.entries(count(values.map(x=>String(x)))).map(([id,n])=>({token_id:id==='null'?null:Number(id),saved_vocabulary_text:id==='null'?null:vocab.tokens[Number(id)].text,count:n})).sort((a,b)=>b.count-a.count||a.token_id-b.token_id);
 const prefixDiagnostics={status:'SAVED_TOKEN_PREFIX_FIRST_DIFFERENCE_DIAGNOSTIC',noninitial_mismatches:differences.length,
  previous_generation_prompt_has_empty_think_stub:differences.filter(x=>x.previous_prompt_ends_empty_think_stub).length,
  first_difference_at_stub_start:differences.filter(x=>x.difference_at_previous_prompt_empty_think_start).length,
  old_token_is_think_start:differences.filter(x=>x.old_token_is_think_start).length,new_token_is_think_start:differences.filter(x=>x.new_token_is_think_start).length,
  old_token_histogram:tokenHistogram(differences.map(x=>x.old_token_id)),new_token_histogram:tokenHistogram(differences.map(x=>x.new_token_id)),
  all_prompts_independently_re_rendered:true,
  interpretation:'Under the exact pinned basic-role renderer, old generation prompts include the empty-thinking stub, whereas canonical past-assistant rendering omits it. First-token differences are saved tokenization observations of that declared provided-history contract, not native cache-head observations or a general resident impossibility theorem.'};
 const supplemental={status:'SUPPLEMENTAL_SAVED_DATA_CAP_COMPATIBILITY_NOT_A_NEW_SELECTION',cap,provided_EOG_counts_toward_generated_tokens:true,
  old_frozen_over128_body_flag_turns:independent.filter(x=>x.oldOverCap).length,
  complete_body_plus_EOG_over128_turns:independent.filter(x=>x.completeOverCap).length,
  additional_incompatible_turns_missed_by_old_body_only_flag:independent.filter(x=>x.completeOverCap&&!x.oldOverCap).length,
  history_has_body_exactly128_turns:independent.filter(x=>x.bodyExactlyCap).length,
  history_has_embedded_EOG_turns:independent.filter(x=>x.embeddedEOG).length,
  hypothetical_length_and_stop_compatible_turns:compatible.length,compatible_noninitial_turns:compatibleLater.length,
  compatible_noninitial_prefix_reusable:compatibleLater.filter(x=>x.prefix).length,compatible_noninitial_prefix_mismatches:compatibleLater.filter(x=>!x.prefix).length,
  compatible_admitted_geometry_turns:compatibleGeometry.length,compatible_distinct_rechunk_LOCAL_partitions:compatibleGeometry.filter(x=>x.geometry.partitionDistinct).length,
  compatible_total_predicted_rows:sum(compatibleGeometry.map(x=>x.append)),
  limits:'Necessary length/EOG compatibility of supplied histories only; not a native greedy-producer proof, not a new selected cohort, and not a GPU/performance/numerical result. Original flags/data are preserved.'};
 const inputsAudited=['SPEC.json','MESSAGES.json','chat_template.jinja','CORPUS.json','TURN_CENSUS.json','CENSUS_REPORT.json','TOKENIZER_INPUT.jsonl','TOKENIZER_OUTPUT.jsonl','FOUR_DEVELOPMENT_SOURCE_INPUTS.json'].map(file=>{const b=fs.readFileSync(path.join(base,file));return {file,bytes:b.length,sha256:hash(b)};});
 const final={status:'INDEPENDENT_SAVED_TOKENIZER_TREE_PREFIX_GEOMETRY_CENSUS_PASSED',GPU_requests:0,model_forward_calls:0,new_tokenizer_calls:0,new_model_contexts:0,
  checks:{raw_source_messages:raw.length,roots:roots.length,paths:paths.length,independently_rendered_prompts:users.length,tokenizer_queries:inputs.length,native_token_roundtrips:tokens.size,
   reconstructed_turns:independent.length,frozen_metric_fields:Object.keys(metrics).length,development_roots_checked:dev.length,all_original_rows_preserved:true},
  metrics,source_counts:independentCounts,supplemental_cap_compatibility:supplemental,prefix_first_difference:prefixDiagnostics,asset_checks:assets,frozen_source_checks:sourceChecks,inputs:inputsAudited,caller_s:(Date.now()-began)/1000,
  limitations:['Replays saved native token IDs and independently renders the pinned basic-role template; it does not independently rerun tokenization or execute a model.',
   'Supplied assistant bodies and appended EOG are a declared hypothetical teacher-forced history; actual native heads and sequential greedy outputs remain unknown.',
   'Zero distinct partitions is restricted to this fixed canonical-template/provided-history/common-rebuild contract, not all legal resident append policies.',
   'Predicted dense extent/launch-group work is not native arithmetic equivalence, CUDA dispatch count, speed, placement, state qualification or free-session performance.']};
 write('SUPPLEMENTAL_CAP_COMPATIBILITY.json',supplemental);write('INDEPENDENT_VERIFICATION.json',final);
 write('PREFIX_FIRST_DIFFERENCE.json',prefixDiagnostics);
 write('PER_TURN_INDEPENDENT_SUMMARY.json',independent.map(x=>({message_id:x.message_id,root:x.root,turn:x.turn,status:x.status,prompt_tokens:x.prompt_tokens,prefix:x.prefix,lcp:x.lcp,head:x.head,append:x.append,admitted:x.admitted,oldOverCap:x.oldOverCap,completeBodyPlusEOGOverCap:x.completeOverCap,embeddedEOG:x.embeddedEOG,nativeCapCompatibleHypothesis:x.nativeCapCompatibleHypothesis,projectionPartitionDistinct:x.geometry?x.geometry.partitionDistinct:null,first_difference:x.firstDifference})));
 console.log(JSON.stringify({status:final.status,metrics,supplemental_cap_compatibility:supplemental,caller_s:final.caller_s}));
} catch(error){write('FAILURE.json',{status:'INDEPENDENT_CENSUS_VERIFICATION_FAILED',reason:String(error),GPU_requests:0,caller_s:(Date.now()-began)/1000});throw error;}
