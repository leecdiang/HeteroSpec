'use strict';
// Pure CPU required-coverage graph. It cannot attest that a native writer,
// context lifecycle, cold construction or GPU operation really happened.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {isDeepStrictEqual}=require('node:util');
const {validateManifest,PATHS}=require('./manifest.js');
const {parseJSON,validateSnapshot,compareManifest}=require('./raw_compare.js');
const PHASES=Object.freeze(['POST_RECONCILE','POST_APPEND','TERMINAL']);
function need(b,m){if(!b)throw Error(m);}
function digest(value){return crypto.createHash('sha256').update(JSON.stringify(value)+'\n').digest('hex');}
function dense(a){need(Array.isArray(a),'array required');for(let i=0;i<a.length;i++)need(Object.hasOwn(a,i),'sparse/inherited array entry');return a;}
function peer(id,p){const s=id.split('/');s[1]=p;return s.join('/');}
function binding(operation_id,phase){return{operation_id,phase};}
function expectedGraph(proposal){
 validateManifest(proposal);const checks=[],reference=proposal.operations.filter(o=>o.path==='RESIDENT_R');
 for(const op of reference)for(const p of PATHS.slice(1))for(const phase of PHASES)
  checks.push({id:`aligned/${peer(op.id,p)}/${phase}`,scope:'ALIGNED_STATE',bindings:{left:binding(op.id,phase),right:binding(peer(op.id,p),phase)}});
 for(const p of PATHS)for(const op of reference.filter(o=>o.turn===0)){
  const setup=peer(op.id,p),tail=setup.slice(0,-1)+'1';
  if(p!=='COLD_CANONICAL_ORACLE')checks.push({id:`retention/${setup}`,scope:'PREFIX_RETENTION',bindings:{previous:binding(setup,'TERMINAL'),current:binding(tail,'POST_RECONCILE')}});
  checks.push({id:`ownership/${setup}`,scope:'OWNED_VECTOR_STABILITY',bindings:{source:{...binding(setup,'TERMINAL'),row_selector:'LAST_REQUESTED_ROW'},mutation_operation_id:tail}});
  checks.push({id:`reset/${tail}`,scope:'RESET_EMPTY_CHECK',bindings:{capture:binding(tail,'RESET')}});
 }
 const counts={};for(const c of checks)counts[c.scope]=(counts[c.scope]||0)+1;
 need(checks.length===261&&counts.ALIGNED_STATE===162&&counts.PREFIX_RETENTION===27&&counts.OWNED_VECTOR_STABILITY===36&&counts.RESET_EMPTY_CHECK===36,'coverage derivation error');
 return{schema:'hs.N1a.required-coverage.v1',status:'REQUIRED_GRAPH_FROZEN_NOT_EXECUTED',proposal_normalized_sha256:digest(proposal),
  counts,checks,model_forwards:0,GPU_contexts_created:0,placement_actions:0,
  native_qualification:'NOT_ESTABLISHED',admission_authorized:false,
  cold_scope:'Nine cold sessions are excluded from prior-KV retention. Their freshly built prefix is checked against R through ALIGNED_STATE; truthful empty-start/q1 work receipts remain a native admission requirement.'};
}
function validateListedCoverage(proposal,submitted){
 const graph=expectedGraph(proposal);need(submitted.schema==='hs.N1a.raw-comparisons.v1','comparison manifest schema');
 need(submitted.required_graph_sha256===digest(graph),'required graph binding differs');
 need(typeof submitted.run_id==='string'&&submitted.run_id,'run identity absent');
 dense(submitted.comparisons);need(submitted.comparisons.length===261,'missing/extra required comparison');
 const expected=new Map(graph.checks.map(x=>[x.id,x])),seen=new Set(),captures=new Map();
 function receipt(d){need(d&&typeof d.file==='string'&&d.file&&typeof d.sha256==='string'&&/^[0-9a-f]{64}$/.test(d.sha256),'missing/bad lifecycle receipt descriptor');}
 function capture(d,b){
  need(d&&d.operation_id===b.operation_id&&d.phase===b.phase,'comparison capture is cross-operation or wrong phase');
  need(d.run_id===submitted.run_id,'capture run differs from comparison run');
  for(const n of ['file','sha256','executable_sha256'])need(typeof d[n]==='string'&&d[n],'missing capture descriptor');
  need(/^[0-9a-f]{64}$/.test(d.sha256)&&/^[0-9a-f]{64}$/.test(d.executable_sha256),'invalid capture digest');
  const key=b.operation_id+'::'+b.phase;
  if(captures.has(key))need(isDeepStrictEqual(captures.get(key),d),'different source captures selected for the same operation/phase');else captures.set(key,d);
 }
 for(const c of submitted.comparisons){need(!seen.has(c.id),'duplicate comparison ID');seen.add(c.id);const e=expected.get(c.id);need(e,'unknown comparison ID');
  need(c.scope===e.scope&&isDeepStrictEqual(c.bindings,e.bindings),'comparison scope or semantic bindings relabeled');
  if(c.scope==='ALIGNED_STATE'){capture(c.left,e.bindings.left);capture(c.right,e.bindings.right);}
  else if(c.scope==='PREFIX_RETENTION'){capture(c.previous,e.bindings.previous);capture(c.current,e.bindings.current);receipt(c.transition_receipt);}
  else if(c.scope==='OWNED_VECTOR_STABILITY'){
   need(c.origin&&c.origin.next_operation_id===e.bindings.mutation_operation_id,'ownership mutation operation differs');
   capture(c.origin.snapshot,e.bindings.source);need(Number.isInteger(c.origin.requested_row_index)&&c.origin.requested_row_index>=0,'ownership source row absent');
   need(typeof c.origin.ownership_id==='string'&&c.origin.ownership_id&&Number.isInteger(c.origin.vector_position)&&c.origin.vector_position>=0,'ownership source identity/coordinate absent');
   receipt(c.before_event);receipt(c.after_event);receipt(c.mutation_receipt);
  }else capture(c.capture,e.bindings.capture);
 }
 need(seen.size===expected.size,'required comparisons omitted');
 return{status:'COMPLETE_PROVIDED_BINDINGS_ONLY',required_checks:261,counts:graph.counts,unique_captures:captures.size,
  graph_sha256:digest(graph),comparison_manifest_normalized_sha256:digest(submitted),native_qualification:'NOT_ESTABLISHED',admission_authorized:false};
}
function loadBound(root,d){
 need(typeof d.file==='string'&&!path.isAbsolute(d.file)&&!d.file.includes('\\')&&!d.file.split('/').some(x=>!x||x==='.'||x==='..'),'unsafe capture path');
 const p=path.resolve(root,d.file),actual=fs.realpathSync(p),base=fs.realpathSync(root);
 need(actual.startsWith(base+path.sep)&&!fs.lstatSync(p).isSymbolicLink(),'capture path outside root/symlink');
 const bytes=fs.readFileSync(p);need(crypto.createHash('sha256').update(bytes).digest('hex')===d.sha256,'snapshot transport digest differs');
 const s=validateSnapshot(parseJSON(bytes.toString('utf8')));
 need(s.operation_id===d.operation_id&&s.phase===d.phase&&s.run_id===d.run_id&&s.provenance.executable_sha256===d.executable_sha256,'actual capture header differs from frozen descriptor');return s;
}
function validateActualHeaders(root,proposal,submitted){
 validateListedCoverage(proposal,submitted);const operations=new Map(proposal.operations.map(o=>[o.id,o])),seen=new Map(),contexts=new Map();
 function actual(d){const key=d.operation_id+'::'+d.phase;if(seen.has(key))return seen.get(key);
  const s=loadBound(root,d),op=operations.get(d.operation_id);need(op,'capture operation is not planned');
  need(s.path_kind===(op.path==='COLD_CANONICAL_ORACLE'?'COLD_ORACLE':'RESIDENT'),'actual path kind relabeled');
  need(s.cohort===(op.control?'SCRIPTED_CONTROL':'NATURAL'),'actual natural/control cohort relabeled');
  const worker=op.path+'/'+(op.control?'CONTROL':'NATURAL');
  if(contexts.has(worker))need(contexts.get(worker)===s.context_id,'context recreated within the same registered worker');else contexts.set(worker,s.context_id);
  seen.set(key,s);return s;
 }
 for(const c of submitted.comparisons){
  if(c.scope==='ALIGNED_STATE'){actual(c.left);actual(c.right);}
  else if(c.scope==='PREFIX_RETENTION'){actual(c.previous);actual(c.current);}
  else if(c.scope==='OWNED_VECTOR_STABILITY'){const s=actual(c.origin.snapshot);need(c.origin.requested_row_index===s.requested_vector_positions.length-1&&c.origin.vector_position===s.requested_vector_positions.at(-1),'ownership must use exactly the last setup terminal frontier row');}
  else actual(c.capture);
 }
 need(contexts.size===8&&new Set(contexts.values()).size===8,'independent workers share/reuse a context identity');
 return{status:'COMPLETE_PROVIDED_HEADER_BINDINGS_ONLY',actual_header_files:seen.size,registered_worker_contexts:contexts.size,
  limitation:'Header consistency is not proof that native state, cold construction or registered work actually happened.'};
}
function validateResults(proposal,submitted,report){
 const coverage=validateListedCoverage(proposal,submitted);
 need(report.schema==='hs.N1a.raw-comparison-report.v1'&&report.scope==='CPU_REPLAY_OF_PROVIDED_RAW_BYTES_NOT_INDEPENDENT_GPU_EXECUTION','raw replay report schema/scope');
 need(report.comparison_manifest_normalized_sha256===digest(submitted),'raw results not bound to supplied comparison manifest');
 dense(report.results);need(report.results.length===261,'missing/extra raw result');const ids=new Set(submitted.comparisons.map(c=>c.id)),seen=new Set();
 const inputs=new Map(submitted.comparisons.map(c=>[c.id,c]));
 for(const r of report.results){need(ids.has(r.id)&&!seen.has(r.id),'unknown/duplicate result');seen.add(r.id);need(['PASS','STATE_FAIL','NUMERIC_FAIL','CONTRACT_CONFLICT','INVALID_CAPTURE'].includes(r.status),'unknown result status');
  need(r.input_scope===inputs.get(r.id).scope&&isDeepStrictEqual(r.bindings,inputs.get(r.id).bindings),'raw result scope/pair bindings differ');}
 const allPass=report.results.every(r=>r.status==='PASS');need(report.status===(allPass?'PASS':'FAIL'),'aggregate raw status disagrees');
 return{...coverage,raw_replay_status:report.status,
  native_qualification:'NOT_ESTABLISHED_PROVIDED_BYTES_AND_RECEIPTS_ONLY',admission_authorized:false};
}
function verifyProvidedRaw(root,proposal,submitted){
 const header_check=validateActualHeaders(root,proposal,submitted),report=compareManifest(root,submitted);
 const inputs=new Map(submitted.comparisons.map(c=>[c.id,c]));for(const r of report.results){r.input_scope=inputs.get(r.id).scope;r.bindings=inputs.get(r.id).bindings;}
 report.comparison_manifest_normalized_sha256=digest(submitted);
 return{schema:'hs.N1a.complete-provided-replay.v1',coverage:validateResults(proposal,submitted,report),header_check,report,
  actual_GPU_execution:'NOT_PERFORMED_BY_THIS_REPLAY',admission_authorized:false};
}
module.exports={expectedGraph,validateListedCoverage,validateActualHeaders,validateResults,verifyProvidedRaw,digest};
if(require.main===module){const mode=process.argv[2],proposal=parseJSON(fs.readFileSync(process.argv[3],'utf8'));
 if(mode==='expected'){fs.writeFileSync(process.argv[4],JSON.stringify(expectedGraph(proposal),null,2)+'\n',{flag:'wx'});console.log('REQUIRED261_GRAPH_WRITTEN_NOT_EXECUTED');}
 else if(mode==='verify'){const p=path.resolve(process.argv[4]),m=parseJSON(fs.readFileSync(p,'utf8')),r=verifyProvidedRaw(path.dirname(p),proposal,m);
  fs.writeFileSync(process.argv[5],JSON.stringify(r,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(r.coverage));if(r.report.status!=='PASS')process.exitCode=1;}
 else throw Error('Usage: node coverage.js expected PROPOSAL.json FRESH_GRAPH.json | verify PROPOSAL.json CAPTURE_COMPARISONS.json FRESH_REPLAY.json');
}
