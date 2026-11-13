'use strict';
// CPU preparation only. Reads actual raw tensor bytes; never invokes a native
// library, GPU, tokenizer, model or context. Digests are transport checks only.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {isDeepStrictEqual}=require('node:util');
const EOG=Object.freeze([128247,151643,151645,151662,151663,151664]);
const PHASES=Object.freeze(['POST_RECONCILE','POST_APPEND','TERMINAL','RESET']);
function need(b,s){if(!b)throw new Error(s);}
function int(n,min=0){need(Number.isSafeInteger(n)&&n>=min,'invalid integer');return n;}
function dense(a){need(Array.isArray(a),'dense array required');for(let i=0;i<a.length;i++)need(Object.hasOwn(a,i),'sparse/inherited array entry');return a;}
function arrayIds(a){dense(a);for(const x of a)need(Number.isSafeInteger(x)&&x>=0&&x<151936,'invalid token ID');return a;}
function equal(a,b){return isDeepStrictEqual(a,b);}
function sha(b){return crypto.createHash('sha256').update(b).digest('hex');}
function hashString(s){need(typeof s==='string'&&/^[0-9a-f]{64}$/.test(s),'invalid SHA256');return s;}
function relative(root,name){
 need(typeof name==='string'&&name&&!path.isAbsolute(name)&&!name.includes('\\')&&!name.split('/').some(x=>!x||x==='.'||x==='..'),'unsafe capture path');
 const target=path.resolve(root,name),r=fs.realpathSync(root),actual=fs.realpathSync(target);
 need(actual.startsWith(r+path.sep)&&!fs.lstatSync(target).isSymbolicLink(),'capture outside root/symlink');
 need(fs.statSync(target).isFile(),'capture is not a file');return target;
}
// Reject duplicate JSON members as well as malformed JSON. JSON.parse alone
// would silently replace a previous shape/filename/provenance declaration.
function parseJSON(text){
 let i=0;const space=()=>{while(/\s/.test(text[i]||'')&&i<text.length)i++;};
 const string=()=>{const begin=i;need(text[i++]==='"','expected string');let escaped=false;
  for(;i<text.length;i++){const c=text[i];if(!escaped&&c==='"'){i++;return JSON.parse(text.slice(begin,i));}if(!escaped&&c==='\\')escaped=true;else escaped=false;}throw Error('unterminated string');};
 function value(){space();if(text[i]==='{'){i++;space();const seen=new Set();if(text[i]==='}'){i++;return;}
   for(;;){space();const k=string();need(!seen.has(k),'duplicate JSON member');seen.add(k);space();need(text[i++]===':','expected colon');value();space();const c=text[i++];if(c==='}')return;need(c===',','expected comma');}}
  if(text[i]==='['){i++;space();if(text[i]===']'){i++;return;}for(;;){value();space();const c=text[i++];if(c===']')return;need(c===',','expected array comma');}}
  if(text[i]==='"'){string();return;}
  const m=/^(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)/.exec(text.slice(i));need(m,'invalid JSON value');i+=m[0].length;
 }
 value();space();need(i===text.length,'trailing JSON');return JSON.parse(text);
}
function fileJSON(root,name){const p=relative(root,name),bytes=fs.readFileSync(p);return{value:parseJSON(bytes.toString('utf8')),sha256:sha(bytes),bytes:bytes.length};}
function half(n){const sign=n&0x8000?-1:1,e=(n>>10)&31,m=n&1023;
 return e===31?(m?NaN:sign*Infinity):e===0?sign*m*2**-24:sign*(1+m/1024)*2**(e-15);}
function coordinate(index,shape,axes){const out={};for(let j=shape.length-1;j>=0;j--){out[axes[j]]=index%shape[j];index=Math.floor(index/shape[j]);}return out;}
function tensorDescription(t){
 need(t&&typeof t==='object','missing tensor');need(t.dtype==='F16LE'||t.dtype==='F32LE','unsupported exact dtype/endianness');
 dense(t.shape);dense(t.axes);need(t.shape.length===t.axes.length&&t.shape.length>0,'tensor dimensions/axes');
 need(new Set(t.axes).size===t.axes.length&&t.axes.every(x=>typeof x==='string'&&x),'duplicate/invalid axes');
 let elements=1;for(const n of t.shape){int(n);elements*=n;int(elements);}
 const scalar=t.dtype==='F16LE'?2:4,bytes=elements*scalar;int(bytes);
 need(t.bytes===bytes,'tensor byte count disagrees with declared shape');hashString(t.sha256);
 return{elements,scalar,bytes};
}
function compareTensor(root,left,right){
 const dl=tensorDescription(left),dr=tensorDescription(right);
 if(!equal([left.dtype,left.shape,left.axes],[right.dtype,right.shape,right.axes]))return{status:'CONTRACT_CONFLICT',reason:'tensor coordinates/dtype/shape differ'};
 const lp=relative(root,left.file),rp=relative(root,right.file);
 need(fs.statSync(lp).size===dl.bytes&&fs.statSync(rp).size===dr.bytes,'raw tensor file length mismatch');
 const lf=fs.openSync(lp,'r'),rf=fs.openSync(rp,'r'),lh=crypto.createHash('sha256'),rh=crypto.createHash('sha256');
 const lb=Buffer.alloc(1024*1024),rb=Buffer.alloc(lb.length);let first=null,firstNonfinite=null,bitDifferentScalars=0,bytesCompared=0,maxAbs=0;
 try{for(let off=0;off<dl.bytes;off+=lb.length){const n=Math.min(lb.length,dl.bytes-off);
   need(fs.readSync(lf,lb,0,n,off)===n&&fs.readSync(rf,rb,0,n,off)===n,'short raw tensor read');lh.update(lb.subarray(0,n));rh.update(rb.subarray(0,n));
   for(let j=0;j<n;j+=dl.scalar){const ix=(off+j)/dl.scalar,ab=dl.scalar===2?lb.readUInt16LE(j):lb.readUInt32LE(j),bb=dl.scalar===2?rb.readUInt16LE(j):rb.readUInt32LE(j);
    const badA=dl.scalar===2?(ab&0x7c00)===0x7c00:(ab&0x7f800000)===0x7f800000,badB=dl.scalar===2?(bb&0x7c00)===0x7c00:(bb&0x7f800000)===0x7f800000;
    if(ab!==bb||badA||badB){const a=dl.scalar===2?half(ab):lb.readFloatLE(j),b=dl.scalar===2?half(bb):rb.readFloatLE(j);
     if((badA||badB)&&!firstNonfinite)firstNonfinite={scalar_index:ix,coordinate:coordinate(ix,left.shape,left.axes),left_value:String(a),right_value:String(b)};
     if(ab!==bb){bitDifferentScalars++;if(!first)first={scalar_index:ix,byte_offset:off+j,coordinate:coordinate(ix,left.shape,left.axes),left_hex:lb.subarray(j,j+dl.scalar).toString('hex'),right_hex:rb.subarray(j,j+dl.scalar).toString('hex'),left_value:Number.isFinite(a)?a:String(a),right_value:Number.isFinite(b)?b:String(b)};}
     if(!badA&&!badB)maxAbs=Math.max(maxAbs,Math.abs(a-b));
    }
   }bytesCompared+=n;
  }}finally{fs.closeSync(lf);fs.closeSync(rf);}
 const actualLeft=lh.digest('hex'),actualRight=rh.digest('hex');
 need(actualLeft===left.sha256&&actualRight===right.sha256,'raw tensor transport SHA256 mismatch');
 return{status:first||firstNonfinite?'NUMERIC_FAIL':'PASS',comparison:'STRICT_FULL_RAW_BYTES_AND_FINITE_VALUES_NO_TOLERANCE',
  bytes_compared:bytesCompared,scalars_compared:dl.elements,bit_different_scalars:bitDifferentScalars,
  first_difference:first,first_nonfinite:firstNonfinite,max_absolute_difference:maxAbs,
  left_transport_sha256:actualLeft,right_transport_sha256:actualRight,
  hash_only_numerical_pass:false};
}
function validateSnapshot(s){
 need(s.schema==='hs.N1a.raw-state.v1','unknown raw state schema');need(PHASES.includes(s.phase),'unknown snapshot phase');
 need(s.path_kind==='RESIDENT'||s.path_kind==='COLD_ORACLE','unknown path kind');
 need(s.cohort==='NATURAL'||s.cohort==='SCRIPTED_CONTROL','natural/control cohort absent');
 const modes=s.cohort==='NATURAL'?['FREE_SEQUENTIAL','CANONICAL_INPUT_ORACLE_REPLAY']:['SCRIPTED_STATE_CONTROL','SCRIPTED_CONTROL_ORACLE'];
 need(s.execution_mode===modes[s.path_kind==='RESIDENT'?0:1],'native free/forced/oracle mode mismatch');
 need(s.generation_cap===(s.cohort==='NATURAL'?128:1),'cohort cap changed');
 for(const n of ['run_id','operation_id','context_id'])need(typeof s[n]==='string'&&s[n],'missing capture identity');
 for(const n of ['contract_sha256','model_sha256','tokenizer_sha256','template_sha256','producer_sha256'])hashString(s.identity[n]);
 for(const n of ['executable_sha256','capture_writer_sha256'])hashString(s.provenance[n]);
 arrayIds(s.canonical_ids);arrayIds(s.materialized_ids);arrayIds(s.logical_ids);arrayIds(s.generated_ids);
 if(s.phase!=='RESET')need(s.canonical_ids.length>0&&s.canonical_ids.length+s.generation_cap-1<=4096,'canonical input plus unchanged output reserve exceeds C4096');
 int(s.head);need(s.head<=4096&&s.head===s.materialized_ids.length,'invalid actual materialized head');
 need(s.logical_ids.length-s.head===0||s.logical_ids.length-s.head===1,'zero/one pending token required');
 need(equal(s.logical_ids.slice(0,s.head),s.materialized_ids),'logical/materialized prefix differs');
 if(s.logical_ids.length===s.head)need(s.pending===null,'spurious pending token');
 else need(s.pending&&s.pending.id===s.logical_ids.at(-1)&&s.pending.position===s.head,'pending identity/position mismatch');
 need(s.frontier&&typeof s.frontier.valid==='boolean'&&typeof s.frontier.owned==='boolean','frontier flags absent');
 dense(s.requested_vector_positions);need(s.requested_vector_positions.every(x=>Number.isInteger(x)&&x>=0&&x<s.head),'requested-vector coordinate invalid');
 dense(s.owned_vector_ids);need(s.owned_vector_ids.length===s.requested_vector_positions.length&&new Set(s.owned_vector_ids).size===s.owned_vector_ids.length&&s.owned_vector_ids.every(x=>typeof x==='string'&&x),'owned vector source IDs absent/duplicated');
 if(s.frontier.valid)need(s.head>0&&s.frontier.position===s.head-1&&s.frontier.owned===true,'stale/unowned valid frontier');
 else need(s.frontier.position===null,'invalid frontier must have no valid position');
 if(s.phase==='POST_RECONCILE'){
  need(equal(s.materialized_ids,s.canonical_ids.slice(0,s.head))&&s.generated_ids.length===0&&s.pending===null,'invalid reconciled prefix');
  if(s.path_kind==='RESIDENT')need(!s.frontier.valid&&s.requested_vector_positions.length===0,'resident post-trim frontier must be invalid');
  else need(equal(s.requested_vector_positions,s.frontier.valid?[s.head-1]:[]),'cold-prefix frontier output mask');
 }else if(s.phase==='POST_APPEND'){
  need(equal(s.canonical_ids,s.materialized_ids)&&equal(s.logical_ids,s.canonical_ids)&&s.generated_ids.length===0&&s.frontier.valid,'postappend canonical state mismatch');
  need(equal(s.requested_vector_positions,[s.head-1]),'postappend complete frontier row required');
 }else if(s.phase==='TERMINAL'){
  need(s.generation_cap===1||s.generation_cap===128,'undeclared cap');need(s.generated_ids.length>0&&s.generated_ids.length<=s.generation_cap,'terminal generation length');
  need(equal(s.logical_ids,s.canonical_ids.concat(s.generated_ids))&&s.pending!==null,'terminal logical history/pending mismatch');
  const mask=s.generated_ids.map((_,i)=>s.canonical_ids.length-1+i);
  need(equal(s.requested_vector_positions,mask),'all sampling vocabulary rows must be captured');
  need(s.frontier.valid,'terminal sampling frontier missing');
  need(!s.generated_ids.slice(0,-1).some(x=>EOG.includes(x)),'continued after earlier EOG');
  if(s.stop_reason==='EOG')need(EOG.includes(s.generated_ids.at(-1)),'terminal EOG predicate');
  else need(s.stop_reason==='CAP'&&s.generated_ids.length===s.generation_cap&&!s.generated_ids.some(x=>EOG.includes(x)),'CAP reason/count/EOG precedence');
 }else need(s.head===0&&s.logical_ids.length===0&&s.canonical_ids.length===0&&s.generated_ids.length===0&&s.pending===null&&!s.frontier.valid&&s.requested_vector_positions.length===0,'reset not empty');
 const kvshape=[36,8,s.head,128],kvaxes=['layer','kv_head','position','dimension'];
 for(const n of ['active_k','active_v']){const t=s.tensors[n];tensorDescription(t);need(t.dtype==='F16LE'&&equal(t.shape,kvshape)&&equal(t.axes,kvaxes),'active KV must cover all layers/heads/active positions');}
 const v=s.tensors.vectors;tensorDescription(v);need(v.dtype==='F32LE'&&equal(v.shape,[s.requested_vector_positions.length,151936])&&equal(v.axes,['requested_row','vocabulary']),'full requested vocabulary rows required');
 return s;
}
function readSnapshotDescriptor(root,d){const r=fileJSON(root,d.file);need(r.sha256===hashString(d.sha256),'snapshot transport SHA mismatch');
  const s=validateSnapshot(r.value);need(s.run_id===d.run_id&&s.operation_id===d.operation_id,'snapshot belongs to different run/operation');
  need(s.provenance.executable_sha256===hashString(d.executable_sha256),'executable identity differs');return s;}
function compareSnapshots(root,leftDesc,rightDesc){
 const a=readSnapshotDescriptor(root,leftDesc),b=readSnapshotDescriptor(root,rightDesc);
 if(!equal(a.identity,b.identity)||a.phase!==b.phase||a.cohort!==b.cohort||!equal(a.canonical_ids,b.canonical_ids))return{status:'CONTRACT_CONFLICT',reason:'cohort/producer/model/tokenizer/template/canonical IDs/phase differ; no numerical conclusion'};
 if(!equal([a.materialized_ids,a.logical_ids,a.generated_ids,a.head,a.pending,a.stop_reason,a.generation_cap],
           [b.materialized_ids,b.logical_ids,b.generated_ids,b.head,b.pending,b.stop_reason,b.generation_cap]))return{status:'STATE_FAIL',reason:'matching input contract produced different tokens/materialized state/pending/stop'};
 if(a.phase!=='POST_RECONCILE'&&!equal(a.requested_vector_positions,b.requested_vector_positions))return{status:'STATE_FAIL',reason:'complete requested output mask differs'};
 if(a.phase!=='POST_RECONCILE'&&!equal(a.frontier,b.frontier))return{status:'STATE_FAIL',reason:'frontier/ownership state mismatch'};
 // At this specifically named alignment cold q1 has just computed the kept
 // canonical prefix, whereas resident trim invalidates its old frontier. Only
 // the actual aligned active KV is comparable; never pretend logits match.
 const names=a.phase==='POST_RECONCILE'?['active_k','active_v']:['active_k','active_v','vectors'];
 const tensors={};for(const n of names)tensors[n]=compareTensor(root,a.tensors[n],b.tensors[n]);
 return{status:Object.values(tensors).every(x=>x.status==='PASS')?'PASS':'NUMERIC_FAIL',phase:a.phase,
  scope:a.phase==='POST_RECONCILE'?'ALIGNED_ACTIVE_KV_ONLY_INVALID_RESIDENT_FRONTIER_NOT_COMPARED':'ALL_ACTIVE_KV_AND_COMPLETE_REQUESTED_VOCABULARY_ROWS',
  head:a.head,tensors};
}
function compareOwnership(root,c){
 const o=c.origin;need(o&&typeof o.ownership_id==='string'&&o.ownership_id,'ownership origin binding absent');
 const source=readSnapshotDescriptor(root,o.snapshot);int(source.event_ordinal);
 int(o.requested_row_index);need(o.requested_row_index<source.requested_vector_positions.length,'ownership source row absent');
 need(source.frontier.valid&&source.frontier.owned&&source.owned_vector_ids[o.requested_row_index]===o.ownership_id,'ownership ID is not bound to actual owned source row');
 need(o.vector_position===source.requested_vector_positions[o.requested_row_index],'ownership source coordinate differs');
 need(typeof o.next_operation_id==='string'&&o.next_operation_id&&o.next_operation_id!==source.operation_id,'next mutation operation absent');
 function event(d,phase){const r=fileJSON(root,d.file);need(r.sha256===hashString(d.sha256),'ownership event transport SHA mismatch');const e=r.value;
  need(e.schema==='hs.N1a.owned-vector-event.v1'&&e.phase===phase,'ownership lifecycle event schema/phase');
  need(e.run_id===source.run_id&&e.context_id===source.context_id&&e.source_operation_id===source.operation_id&&e.next_operation_id===o.next_operation_id,'ownership event run/context/operation mismatch');
  need(e.source_snapshot_sha256===o.snapshot.sha256&&e.source_requested_row_index===o.requested_row_index&&e.source_vector_position===o.vector_position&&e.ownership_id===o.ownership_id,'ownership event source-row binding mismatch');
  need(e.caller_owned===true&&e.capture_writer_sha256===source.provenance.capture_writer_sha256,'ownership event writer/copy identity');int(e.event_ordinal);
  tensorDescription(e.tensor);need(e.tensor.dtype==='F32LE'&&equal(e.tensor.shape,[1,151936])&&equal(e.tensor.axes,['requested_row','vocabulary']),'owned full vocabulary row absent');return e;}
 const before=event(c.before_event,'BEFORE_NEXT_MUTATION'),after=event(c.after_event,'AFTER_NEXT_MUTATION');
 const mr=fileJSON(root,c.mutation_receipt.file);need(mr.sha256===hashString(c.mutation_receipt.sha256),'mutation receipt transport SHA mismatch');const m=mr.value;
 need(m.schema==='hs.N1a.mutation-receipt.v1'&&m.run_id===source.run_id&&m.context_id===source.context_id&&m.operation_id===o.next_operation_id&&m.source_operation_id===source.operation_id,'mutation lifecycle identity mismatch');
 int(m.begin_event_ordinal);int(m.end_event_ordinal);int(m.actual_decode_calls,1);int(m.actual_model_rows,1);need(m.actual_model_rows<=4096&&m.status==='COMPLETE','mutation did not complete a bounded actual decode');
 need(source.event_ordinal<before.event_ordinal&&before.event_ordinal<m.begin_event_ordinal&&m.begin_event_ordinal<=m.end_event_ordinal&&m.end_event_ordinal<after.event_ordinal,'ownership before/decode/after event ordering invalid');
 const sourceTensor=source.tensors.vectors,td=tensorDescription(sourceTensor),sp=relative(root,sourceTensor.file);
 need(fs.statSync(sp).size===td.bytes,'source tensor length mismatch');
 const h=crypto.createHash('sha256'),fd=fs.openSync(sp,'r'),chunk=Buffer.alloc(1024*1024);
 let row;try{for(let off=0;off<td.bytes;off+=chunk.length){const n=Math.min(chunk.length,td.bytes-off);need(fs.readSync(fd,chunk,0,n,off)===n,'short ownership source read');h.update(chunk.subarray(0,n));}
  row=Buffer.alloc(151936*4);need(fs.readSync(fd,row,0,row.length,o.requested_row_index*row.length)===row.length,'short ownership source row');}finally{fs.closeSync(fd);}
 need(h.digest('hex')===sourceTensor.sha256,'ownership source transport SHA mismatch');
 const result=compareTensor(root,before.tensor,after.tensor),beforeBytes=fs.readFileSync(relative(root,before.tensor.file));
 if(!row.equals(beforeBytes))return{status:'NUMERIC_FAIL',reason:'owned before-copy differs from the complete actual source snapshot row',source_row_bytes_compared:row.length,before_after:result};
 return{...result,scope:'COMPLETE_SOURCE_ROW_AND_SAME_OWNERSHIP_BEFORE_AFTER_PROVIDED_DECODE_RECEIPTS',source_row_bytes_compared:row.length,
  ownership_id:o.ownership_id,source_operation_id:source.operation_id,next_operation_id:o.next_operation_id,
  limitation:'Checks delivered raw bytes and bound lifecycle receipts; native writer/receipt truth still requires independent source and integration audit'};
}
function hashFileActual(p){const h=crypto.createHash('sha256'),fd=fs.openSync(p,'r'),b=Buffer.alloc(1024*1024);try{for(let n;(n=fs.readSync(fd,b,0,b.length,null));)h.update(b.subarray(0,n));}finally{fs.closeSync(fd);}return h.digest('hex');}
function compareRetainedKV(root,a,b,oldHead,keep){
 const ad=tensorDescription(a),bd=tensorDescription(b),ap=relative(root,a.file),bp=relative(root,b.file);
 need(fs.statSync(ap).size===ad.bytes&&fs.statSync(bp).size===bd.bytes,'retained KV raw length mismatch');
 need(hashFileActual(ap)===a.sha256&&hashFileActual(bp)===b.sha256,'retained KV transport SHA mismatch');
 const af=fs.openSync(ap,'r'),bf=fs.openSync(bp,'r'),ab=Buffer.alloc(1024*1024),bb=Buffer.alloc(ab.length);
 let bytes=0,first=null,nonfinite=null,diff=0,maxAbs=0;
 try{for(let layer=0;layer<36;layer++)for(let head=0;head<8;head++){
  const prefixBytes=keep*128*2,aStart=(layer*8+head)*oldHead*128*2,bStart=(layer*8+head)*keep*128*2;
  for(let off=0;off<prefixBytes;off+=ab.length){const n=Math.min(ab.length,prefixBytes-off);
   need(fs.readSync(af,ab,0,n,aStart+off)===n&&fs.readSync(bf,bb,0,n,bStart+off)===n,'short retained prefix read');
   for(let j=0;j<n;j+=2){const av=ab.readUInt16LE(j),bv=bb.readUInt16LE(j),badA=(av&0x7c00)===0x7c00,badB=(bv&0x7c00)===0x7c00;
    if(av!==bv||badA||badB){const x=half(av),y=half(bv),coordinate={layer,kv_head:head,position:Math.floor((off+j)/256),dimension:((off+j)/2)%128};
     if((badA||badB)&&!nonfinite)nonfinite={coordinate,left_value:String(x),right_value:String(y)};
     if(av!==bv){diff++;if(!first)first={coordinate,left_hex:ab.subarray(j,j+2).toString('hex'),right_hex:bb.subarray(j,j+2).toString('hex'),left_value:Number.isFinite(x)?x:String(x),right_value:Number.isFinite(y)?y:String(y)};}
     if(!badA&&!badB)maxAbs=Math.max(maxAbs,Math.abs(x-y));
    }
   }bytes+=n;
  }
 }}finally{fs.closeSync(af);fs.closeSync(bf);}
 return{status:first||nonfinite?'NUMERIC_FAIL':'PASS',bytes_compared:bytes,retained_positions:keep,
  first_difference:first,first_nonfinite:nonfinite,bit_different_scalars:diff,max_absolute_difference:maxAbs,
  layout:'All36layers x8KVheads x retainedpositions x128dimensions, F16LE; original source head stride respected',
  hash_only_numerical_pass:false};
}
function comparePrefixRetention(root,c){
 const old=readSnapshotDescriptor(root,c.previous),next=readSnapshotDescriptor(root,c.current);
 need(old.phase==='TERMINAL'&&next.phase==='POST_RECONCILE'&&old.path_kind==='RESIDENT'&&next.path_kind==='RESIDENT','retention requires prior terminal and same live resident next-turn reconciliation');
 if(!equal(old.identity,next.identity)||old.run_id!==next.run_id||old.context_id!==next.context_id||old.cohort!==next.cohort)return{status:'CONTRACT_CONFLICT',reason:'retention is not same producer/live context/cohort'};
 const rr=fileJSON(root,c.transition_receipt.file);need(rr.sha256===hashString(c.transition_receipt.sha256),'reconcile receipt SHA mismatch');const r=rr.value;
 need(r.schema==='hs.N1a.reconcile-receipt.v1'&&r.run_id===old.run_id&&r.context_id===old.context_id&&r.source_operation_id===old.operation_id&&r.operation_id===next.operation_id,'reconcile receipt identity mismatch');
 need(r.previous_snapshot_sha256===c.previous.sha256&&r.current_snapshot_sha256===c.current.sha256,'reconcile receipt snapshot binding mismatch');
 int(old.event_ordinal);int(next.event_ordinal);need(old.event_ordinal<next.event_ordinal,'reconcile event order invalid');
 let lcp=0;while(lcp<old.logical_ids.length&&lcp<next.canonical_ids.length&&old.logical_ids[lcp]===next.canonical_ids[lcp])lcp++;
 let keep=Math.min(lcp,old.head);const replay=keep===next.canonical_ids.length;if(replay)keep--;
 need(next.canonical_ids.length>0,'empty next canonical input unsupported');
 let expected='LCP_TRIM_REPLAY';if(lcp===old.logical_ids.length&&keep===old.head)expected='DIRECT_APPEND';if(replay)expected='LAST_TOKEN_REPLAY';
 if(r.fallback_reason!==null){need(old.head>keep,'trim fallback when no tail trim was required');need(r.fallback_reason==='TRIM_CAPABILITY_UNSUPPORTED'||r.fallback_reason==='CALLER_INJECTED_TRIM_FAILURE_BEFORE_NATIVE_MUTATION','unapproved native-failure retry');keep=0;expected='COMMON_FULL_REBUILD';}
 need(r.mode===expected&&r.actual_head_before===old.head&&r.actual_keep===keep&&next.head===keep&&r.actual_model_rows_before_append===0&&r.old_frontier_invalidated===true,'reconcile rule/head/frontier differs from exact token policy');
 need(equal(next.materialized_ids,old.materialized_ids.slice(0,keep)),'retained token prefix changed');
 const pending=old.pending===null?'NONE':expected==='COMMON_FULL_REBUILD'?'DISCARD_OLD_PENDING_WITH_RESET':lcp>old.head?'REPLAY_OLD_PENDING_ONCE_AT_CANONICAL_POSITION':'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX';
 need(r.old_pending_id===(old.pending?old.pending.id:null)&&r.pending_disposition===pending,'old pending token was not reconciled by the shared rule');
 const tensors={};for(const n of ['active_k','active_v'])tensors[n]=compareRetainedKV(root,old.tensors[n],next.tensors[n],old.head,keep);
 return{status:Object.values(tensors).every(x=>x.status==='PASS')?'PASS':'NUMERIC_FAIL',scope:'SAME_CONTEXT_PRIOR_TERMINAL_TO_NEXT_RETAINED_ACTIVE_PREFIX_RAW_BYTES_ONLY',
  keep,token_lcp:lcp,mode:expected,frontier_equivalence:'NOT_CLAIMED_OLD_FRONTIER_INVALIDATED',tensors};
}
function resetCheck(root,d){const s=readSnapshotDescriptor(root,d);need(s.phase==='RESET','reset checkpoint phase required');const tensors={};
 for(const n of ['active_k','active_v','vectors']){const t=s.tensors[n],td=tensorDescription(t),p=relative(root,t.file);
  need(td.bytes===0&&fs.statSync(p).size===0,'reset raw file must actually be empty');
  need(hashFileActual(p)===t.sha256,'reset empty-file transport SHA mismatch');
  tensors[n]={status:'EMPTY_FILE_VERIFIED',bytes_compared:0,
   comparison:'ACTUAL_ZERO_LENGTH_FILE_AND_EMPTY_STATE_METADATA_NOT_A_SELF_PAIR_NUMERICAL_PROOF'};}
 return{status:'PASS',scope:'EMPTY_RESET_METADATA_AND_ZERO_LENGTH_RAW_FILES_NO_FORWARD',head:0,tensors};}
function compareManifest(root,m){
 need(m.schema==='hs.N1a.raw-comparisons.v1'&&Array.isArray(m.comparisons)&&m.comparisons.length>0,'comparison manifest absent');
 const ids=new Set(),results=[];
 for(const c of m.comparisons){need(typeof c.id==='string'&&c.id&&!ids.has(c.id),'duplicate comparison ID');ids.add(c.id);
  try{let result;if(c.scope==='ALIGNED_STATE')result=compareSnapshots(root,c.left,c.right);
   else if(c.scope==='OWNED_VECTOR_STABILITY')result=compareOwnership(root,c);
   else if(c.scope==='PREFIX_RETENTION')result=comparePrefixRetention(root,c);
   else{need(c.scope==='RESET_EMPTY_CHECK','unknown comparison scope');result=resetCheck(root,c.capture);}
   results.push({id:c.id,...result});
  }catch(e){results.push({id:c.id,status:'INVALID_CAPTURE',reason:e.message});}
 }
 return{schema:'hs.N1a.raw-comparison-report.v1',status:results.every(x=>x.status==='PASS')?'PASS':'FAIL',
  scope:'CPU_REPLAY_OF_PROVIDED_RAW_BYTES_NOT_INDEPENDENT_GPU_EXECUTION',hash_only_numerical_pass:false,
  qualification_coverage:'ONLY_LISTED_PROVIDED_PAIRS_NO_NATIVE_COMPLETENESS_OR_ADMISSION_CERTIFICATE',
  model_forwards:0,GPU_contexts_created:0,placement_actions:0,results};
}
module.exports={parseJSON,validateSnapshot,compareTensor,compareSnapshots,compareManifest,compareOwnership,comparePrefixRetention,half,coordinate};
if(require.main===module){const mp=path.resolve(process.argv[2]),out=process.argv[3];need(mp&&out,'Usage: node raw_compare.js CAPTURE_COMPARISONS.json FRESH_REPORT.json');
 const r=compareManifest(path.dirname(mp),parseJSON(fs.readFileSync(mp,'utf8')));fs.writeFileSync(out,JSON.stringify(r,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:r.status,comparisons:r.results.length,scope:r.scope}));if(r.status!=='PASS')process.exitCode=1;}
