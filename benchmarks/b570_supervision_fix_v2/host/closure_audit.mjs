// Final raw tail audit in the existing tool service: no new child after closure.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {evidencePrefix} from './tail_binding.mjs';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
// Preserve exact FILETIME integers; JSON.parse alone loses their low bits.
export function exactJson(text) {
  let out='',quoted=false,escaped=false;
  for(let i=0;i<text.length;) {
    const c=text[i];
    if(quoted){out+=c;i++;if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c==='"')quoted=false;continue;}
    if(c==='"'){quoted=true;out+=c;i++;continue;}
    if(c==='-' || /[0-9]/.test(c)) {
      const m=text.slice(i).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);
      if(m){const n=m[0];out+=/^-?\d+$/.test(n)&&(BigInt(n)>9007199254740991n||BigInt(n)<-9007199254740991n)?JSON.stringify(n):n;i+=n.length;continue;}
    }
    out+=c;i++;
  }
  return JSON.parse(out.replace(/^\uFEFF/,''));
}
async function inventory(root) {
  let bytes=0,files=0,dirs=0;
  async function visit(p){for(const e of await fs.readdir(p,{withFileTypes:true})){const q=path.join(p,e.name);if(e.isSymbolicLink())throw Error('unexpected reparse in task storage');if(e.isDirectory()){dirs++;bytes+=4096;await visit(q);}else{const s=await fs.stat(q);files++;bytes+=Math.ceil(s.size/4096)*4096+1024;}}}
  await visit(root);return {allocation_upper_bytes:bytes,files,directories:dirs};
}
export async function auditClosure(base,toolExit,auditPath,{write=true}={}) {
  const first=await fs.readFile(base+'/task/PROCESS_LEDGER.jsonl');
  const second=await fs.readFile(base+'/task/PROCESS_LEDGER_v2.jsonl');
  const rows=exactJson('['+Buffer.concat([first,second]).toString().trim().split('\n').join(',')+']');
  const starts=new Map(),ends=new Map(),errors=[];let lastSeq=0,life=0;
  for(const r of rows){
    if(r.seq<=lastSeq)errors.push('nonmonotonic ledger sequence');lastSeq=r.seq;
    if(r.kind==='PROCESS_CREATE'){
      const key=r.pid+':'+r.created_filetime;if(starts.has(key))errors.push('duplicate process identity');starts.set(key,r);
      if(!r.command_sha256)errors.push('missing command identity');
      if(r.role==='descendant'&&![...starts.values()].some(p=>p.pid===r.parent_pid&&p.at_ns<=r.at_ns))errors.push('unknown descendant parent');
    }
    if(r.kind==='PROCESS_CLOSED'){
      const key=r.pid+':'+r.created_filetime;if(!starts.has(key)||ends.has(key))errors.push('invalid process closure');ends.set(key,r);
      const delta=BigInt(r.exit_filetime)-BigInt(r.created_filetime);if(delta<0n)errors.push('reversed OS lifetime');
      const seconds=Number(delta)/1e7;life+=seconds;if(Math.abs(seconds-r.lifetime_seconds)>1e-6)errors.push('incorrect lifetime accounting');
    }
    if(r.kind==='FORBIDDEN_MODULE')errors.push('forbidden GPU module observed');
  }
  for(const key of starts.keys())if(!ends.has(key))errors.push('unclosed task child '+key);
  const auditBytes=await fs.readFile(base+'/'+auditPath),raw=exactJson(auditBytes.toString('utf8'));
  try{const prefix=await evidencePrefix(base,raw);if(!Buffer.concat([first,second]).subarray(0,prefix.length).equals(prefix))errors.push('final ledger does not extend selected audit prefix');}catch(e){errors.push('selected raw prefix binding: '+e.message);}
  const close=exactJson(await fs.readFile(base+'/task/BOOTSTRAP_V2_CLOSED.json','utf8'));
  if(close.broker_exit_code!==0||toolExit.exit_code!==0)errors.push('outer closure failed');
  const missing=[];let bootstrap=null;
  try{bootstrap=exactJson(await fs.readFile(base+'/task/BOOTSTRAP_REGISTRY.json','utf8'));}
  catch(e){missing.push('Prospective bootstrap registry unavailable');}
  const observed=close.outer_processes??[];
  const expected=bootstrap?.outer_processes??[];
  if(!expected.length)missing.push('No prospective outer-process identities');
  let outerLife=0;const outerSeen=new Set();
  for(const required of expected){
    const key=required.pid+':'+required.created_filetime;
    if(outerSeen.has(key)||starts.has(key)){errors.push('duplicate outer identity');continue;}
    outerSeen.add(key);
    const found=observed.filter(r=>r.pid===required.pid&&String(r.created_filetime)===String(required.created_filetime));
    if(found.length!==1||found[0].exit_filetime==null){missing.push('Missing outer OS closure '+key);continue;}
    const delta=BigInt(found[0].exit_filetime)-BigInt(required.created_filetime);
    if(delta<0n){errors.push('reversed outer lifetime');continue;}
    outerLife+=Number(delta)/1e7;
  }
  if(observed.length!==expected.length)errors.push('unexpected outer-process receipt set');
  const firstArmed=rows.find(r=>r.kind==='BROKER_ARMED');const last=rows.at(-1);
  if(!firstArmed||last?.kind!=='BROKER_CLOSING')errors.push('missing final ledger boundaries');
  const start=bootstrap?.task_begin_ns,end=close.task_end_ns;
  let wall=null;
  if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||end<start)missing.push('Missing exact task wall boundaries');
  else wall=(end-start)/1e9;
  const storage=await inventory(base);const chargedLife=life+outerLife;
  if(missing.length)errors.push('incomplete bootstrap/task accounting');
  if(starts.size+outerSeen.size>3000||chargedLife>43200||(wall!==null&&wall>28800)||storage.allocation_upper_bytes+64*1024**2>1073741824)errors.push('task budget exceeded');
  const result={schema:3,raw_audit_sha256:hash(auditBytes),input_manifest_sha256:raw.input_manifest_sha256,ledger_prefix:raw.ledger_prefix,status:errors.length?'TAIL_AUDIT_FAILED':'TAIL_AUDIT_PASS',errors,task_child_starts:starts.size,
    task_child_lifetime_sum_seconds:life,outer_container_starts_separately:outerSeen.size,
    charged_process_lifetime_seconds:missing.length?null:chargedLife,engineering_wall_seconds:wall,
    storage,closing_delivery_reserve_bytes:64*1024**2,
    ledger_parts:[{path:'task/PROCESS_LEDGER.jsonl',sha256:hash(first)},{path:'task/PROCESS_LEDGER_v2.jsonl',sha256:hash(second)}],
    closing_tool_receipt:toolExit,bootstrap_missing_fields:missing,
    scope:'Only actual once-per-process OS lifetimes. Missing observations are failures, never fixed allowances.'};
  if(write)await fs.writeFile(base+'/repo/benchmarks/b570_supervision_fix_v2/results/TASK_CLOSING.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  return result;
}
