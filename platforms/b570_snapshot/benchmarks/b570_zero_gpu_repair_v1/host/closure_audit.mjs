// Final raw tail audit in the existing tool service: no new child after closure.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
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
export async function auditClosure(base,toolExit) {
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
  const close=exactJson(await fs.readFile(base+'/task/BOOTSTRAP_V2_CLOSED.json','utf8'));
  if(close.broker_exit_code!==0||toolExit.exit_code!==0)errors.push('outer closure failed');
  const broker2Life=Number(BigInt(close.broker_exit_FILETIME)-BigInt(close.broker_creation_FILETIME))/1e7;
  const firstArmed=rows.find(r=>r.kind==='BROKER_ARMED');const firstStop=rows.find(r=>r.kind==='BROKER_STOP');
  const last=rows.at(-1);if(last.kind!=='BROKER_CLOSING')errors.push('missing final ledger close');
  const broker1Upper=(firstStop.at_ns-firstArmed.at_ns)/1e9+30;
  const wrapper2Upper=broker2Life+60; // setup/closing reserve, expressly not an OS exit timestamp
  const engineeringUpper=(last.at_ns-firstArmed.at_ns)/1e9+900; // conservative initial protocol/bootstrap reserve
  const storage=await inventory(base);
  const chargedLife=life+broker1Upper+broker2Life+wrapper2Upper;
  if(starts.size+4>3000||chargedLife>43200||engineeringUpper>28800||storage.allocation_upper_bytes+64*1024**2>1073741824)errors.push('task budget exceeded');
  const result={schema:1,status:errors.length?'TAIL_AUDIT_FAILED':'TAIL_AUDIT_PASS',errors,task_child_starts:starts.size,task_child_lifetime_sum_seconds:life,outer_container_starts_separately:4,broker1_lifetime_upper_seconds:broker1Upper,broker2_actual_OS_lifetime_seconds:broker2Life,wrapper2_lifetime_upper_seconds:wrapper2Upper,charged_process_lifetime_upper_seconds:chargedLife,engineering_wall_observed_seconds:(last.at_ns-firstArmed.at_ns)/1e9,engineering_wall_upper_seconds:engineeringUpper,bootstrap_engineering_reserve_seconds:900,storage,closing_delivery_reserve_bytes:64*1024**2,ledger_parts:[{path:'task/PROCESS_LEDGER.jsonl',sha256:hash(first)},{path:'task/PROCESS_LEDGER_v2.jsonl',sha256:hash(second)}],closing_tool_receipt:toolExit,bootstrap_missing_fields:['Initial bootstrap outer shell creation/exit OS times','Failed broker1 OS exit FILETIME','Wrapper2 own future OS exit FILETIME; external tool exit receipt supplied'],scope:'All post-arm task commands and debug-observed descendants, exactly once. Explicit initial/rebootstrap wrappers are outside debug-child scope, separately charged conservatively. No missing OS timestamp is fabricated. Final remote connector actions create no local task children.'};
  await fs.writeFile(base+'/repo/benchmarks/b570_zero_gpu_repair_v1/results/TASK_CLOSING.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  return result;
}
