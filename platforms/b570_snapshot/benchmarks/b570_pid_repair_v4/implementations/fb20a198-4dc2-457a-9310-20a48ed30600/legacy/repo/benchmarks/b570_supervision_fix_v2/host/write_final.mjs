// Final status from real raw, final review, frozen authentication and recovery.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {tailBinding} from './tail_binding.mjs';
import {exactJson} from './closure_audit.mjs';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
export async function writeFinal(base,auditPath,closing,archiveCommit) {
  const dir=base+'/repo/benchmarks/b570_supervision_fix_v2';
  const read=async p=>exactJson(await fs.readFile(p,'utf8'));
  const auditBytes=await fs.readFile(base+'/'+auditPath);
  const raw=exactJson(auditBytes.toString('utf8')),review=await read(dir+'/results/REVIEW_STATUS.json');
  const freeze=await read(dir+'/results/CONFIRMATION_FREEZE.json'),remote=await read(dir+'/results/REMOTE_FREEZE.json');
  const restore=await read(dir+'/results/REMOTE_RESTORE.json');
  const rows=raw.cases.filter(r=>r.round>=0),missing=raw.confirmation_unstarted;
  const cases=JSON.parse(await fs.readFile(dir+'/ACCEPTANCE.json','utf8')).cases.map(r=>r.id);
  const expected=[cases,[...cases].reverse(),[...cases].sort((a,b)=>hash(a).localeCompare(hash(b)))].flatMap((names,round)=>names.map(name=>round+':'+name));
  const actual=rows.map(r=>r.round+':'+r.case_id);
  const archive=await read(dir+'/results/ARCHIVE.json');
  const conditions={all_57:rows.length===57&&JSON.stringify(actual)===JSON.stringify(expected)&&rows.every(r=>r.status==='PASS')&&missing.length===0,raw_reconstruction:raw.confirmation_status==='RAW_CONFIRMATION_PASS'&&raw.manifest_valid&&raw.process_ledger_valid&&raw.problems.length===0,review:review.status==='FINAL_IMPLEMENTATION_REVIEW_PASS',remote_freeze:remote.freeze_sha256===hash(await fs.readFile(dir+'/results/CONFIRMATION_FREEZE.json')),restored:restore.status==='REMOTE_RESTORE_RECOMPUTATION_MATCH'&&restore.byte_identical&&restore.expected_report_sha256===hash(auditBytes)&&restore.recomputed_report_sha256===hash(auditBytes)&&archive.raw_audit_sha256===hash(auditBytes)&&restore.embedded_manifest_sha256===archive.manifest_sha256&&restore.input_manifest_sha256===raw.input_manifest_sha256&&restore.freeze_sha256===remote.freeze_sha256&&archive.auditor_sha256===restore.packaged_auditor_sha256,final_tail:closing.status==='TAIL_AUDIT_PASS'&&Array.isArray(closing.bootstrap_missing_fields)&&closing.bootstrap_missing_fields.length===0&&Array.isArray(closing.errors)&&closing.errors.length===0};
  conditions.final_tail=conditions.final_tail&&await tailBinding(base,raw,closing,auditBytes);
  const forbidden=['GPU_queries','GPU_initializations','model_file_reads','model_requests','graph_computes','scientific_native_starts'];
  conditions.forbidden_zero=forbidden.every(k=>raw.forbidden_counts?.[k]===0);
  conditions.review=conditions.review&&Object.keys(freeze.bound_files??{}).length>0&&freeze.review_status_sha256===hash(await fs.readFile(dir+'/results/REVIEW_STATUS.json'));
  conditions.receipts=Array.isArray(raw.confirmation_receipts)&&raw.confirmation_receipts.length===57&&raw.confirmation_receipts.every((r,i)=>r.round+':'+r.case_id===expected[i]&&r.freeze_sha256===remote.freeze_sha256);
  const current=[];
  async function collect(p,prefix){for(const e of await fs.readdir(p,{withFileTypes:true})){if(e.name==='__pycache__')continue;if(e.isSymbolicLink())throw Error('source alias');const rel=prefix+e.name;if(e.isDirectory())await collect(p+'/'+e.name,rel+'/');else current.push(rel);}}
  await collect(dir+'/host','host/');
  for(const name of ['ACCEPTANCE.json','BUDGET.json','PROTOCOL.md','EVIDENCE.md','UPSTREAM.json','check_receipts.py'])current.push(name);
  conditions.packaged_source=restore.packaged_auditor_sha256===freeze.bound_files?.['host/raw_audit.py']&&JSON.stringify(Object.keys(restore.packaged_bound_files??{}).sort())===JSON.stringify(Object.keys(freeze.bound_files??{}).sort())&&Object.entries(freeze.bound_files??{}).every(([p,digest])=>restore.packaged_bound_files?.[p]===digest);
  conditions.source_set=JSON.stringify([...current].sort())===JSON.stringify(Object.keys(freeze.bound_files??{}).sort());
  for(const [p,digest] of Object.entries(freeze.bound_files))if(hash(await fs.readFile(dir+'/'+p))!==digest||review.covered_files[p]!==digest)conditions.review=false;
  const status=Object.values(conditions).every(Boolean)?'ENGINEERING_READY':'ENGINEERING_BLOCKED';
  const matrix=[];
  for(const cid of JSON.parse(await fs.readFile(dir+'/ACCEPTANCE.json','utf8')).cases.map(r=>r.id))matrix.push('|'+cid+'|'+[0,1,2].map(round=>rows.find(r=>r.round===round&&r.case_id===cid)?.status||'UNSTARTED').join('|')+'|');
  const budget={...closing,forbidden_counts:raw.forbidden_counts,scope:'CPU source/command/module evidence; not an operating-system-wide claim about unrelated apps',overlapping_lifetimes:'Process lifetime sum includes distinct overlapping containers; engineering wall is not their sum'};
  await fs.writeFile(dir+'/results/BUDGET_ACTUAL.json',JSON.stringify(budget,null,2)+'\n',{flag:'wx'});
  await fs.writeFile(dir+'/results/RECEIPTS.json',JSON.stringify({freeze_sha256:remote.freeze_sha256,receipts:raw.confirmation_receipts},null,2)+'\n',{flag:'wx'});
  const text=`# ${status}\n\nIndependent supervision repair only. This result does not change PR115 or PR117, authorize GPU work, or establish paper evidence.\n\n|case|listed|reversed|SHA256 order|\n|---|---|---|---|\n${matrix.join('\n')}\n\nCurrent audit SHA256: ${hash(auditBytes)}. Restored audit SHA256: ${restore.recomputed_report_sha256}. Archive commit: ${archiveCommit}.\n\nConditions: ${JSON.stringify(conditions)}\n`;
  await fs.writeFile(dir+'/results/RESULT.md',text,{flag:'wx'});
  await fs.writeFile(dir+'/results/ENGINEERING_EVIDENCE.md','# CPU engineering evidence only\n\n'+status+' for the frozen CPU supervision matrix. No paper numerical or cost evidence is created. No GPU, model, actor, S1–S3 or scientific execution occurred. Historical failures and bootstrap/closing limitations remain explicit in RESULT and TASK_CLOSING.\n',{flag:'wx'});
  return {status,conditions,budget,rows:rows.length,missing:missing.length};
}
