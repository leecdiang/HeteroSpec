import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
async function member(base,name){
 if(typeof name!=='string'||!name||name.includes('\\')||name.includes(':')||name.startsWith('/')||name.split('/').some(x=>!x||x==='.'||x==='..'))throw Error('noncanonical evidence member');
 const root=path.resolve(base),p=path.join(root,name);
 for(let q=p;q!==root;q=path.dirname(q))if((await fs.lstat(q)).isSymbolicLink())throw Error('evidence alias');
 return fs.readFile(p);
}
export async function evidencePrefix(base,raw){
 const manifest=await member(base,raw.input_manifest_path);
 if(hash(manifest)!==raw.input_manifest_sha256)throw Error('selected input manifest changed');
 const p=raw.ledger_prefix,entries=JSON.parse(manifest).members.filter(r=>r.path===p.path);
 if(entries.length!==1||entries[0].sha256!==p.sha256||entries[0].bytes!==p.bytes)throw Error('ledger prefix absent from selected manifest');
 const bytes=await member(base,p.path);
 if(bytes.length!==p.bytes||hash(bytes)!==p.sha256||bytes.length===0||bytes.at(-1)!==10)throw Error('invalid selected ledger prefix');
 return bytes;
}
export async function tailBinding(base,raw,closing,auditBytes){
 try{
  if(closing.raw_audit_sha256!==hash(auditBytes)||closing.input_manifest_sha256!==raw.input_manifest_sha256||JSON.stringify(closing.ledger_prefix)!==JSON.stringify(raw.ledger_prefix))return false;
  const prefix=await evidencePrefix(base,raw),parts=[];
  const names=['task/PROCESS_LEDGER.jsonl','task/PROCESS_LEDGER_v2.jsonl'];
  if(closing.ledger_parts?.length!==names.length)return false;
  for(let i=0;i<names.length;i++){const r=closing.ledger_parts[i],bytes=await member(base,names[i]);if(r.path!==names[i]||r.sha256!==hash(bytes))return false;parts.push(bytes);}
  if(!Buffer.concat(parts).subarray(0,prefix.length).equals(prefix))return false;
  const counts=['task_child_starts','outer_container_starts_separately'];
  if(!counts.every(k=>Number.isSafeInteger(closing[k])&&closing[k]>=0)||closing.task_child_starts+closing.outer_container_starts_separately>3000)return false;
  if(!['task_child_lifetime_sum_seconds','charged_process_lifetime_seconds','engineering_wall_seconds','closing_delivery_reserve_bytes'].every(k=>Number.isFinite(closing[k])&&closing[k]>=0))return false;
  return closing.charged_process_lifetime_seconds>=closing.task_child_lifetime_sum_seconds&&closing.charged_process_lifetime_seconds<=43200&&closing.engineering_wall_seconds<=28800&&Number.isSafeInteger(closing.storage?.allocation_upper_bytes)&&closing.storage.allocation_upper_bytes>=0&&closing.closing_delivery_reserve_bytes>=64*1024**2&&closing.storage.allocation_upper_bytes+closing.closing_delivery_reserve_bytes<=1073741824;
 }catch{return false;}
}
