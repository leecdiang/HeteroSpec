import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import crypto from 'node:crypto';
import {writeFinal} from '../host/write_final.mjs';
import {auditClosure} from '../host/closure_audit.mjs';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
async function fixture(){
 const base=await fs.mkdtemp(os.tmpdir()+'/b570-gate-');
 const dir=base+'/repo/benchmarks/b570_supervision_fix_v2';
 await fs.mkdir(dir+'/host',{recursive:true});await fs.mkdir(dir+'/results');await fs.mkdir(base+'/task');
 const put=async(p,o)=>fs.writeFile(p,JSON.stringify(o));
 const names=Array.from({length:19},(_,i)=>'case'+i);
 await put(dir+'/ACCEPTANCE.json',{cases:names.map(id=>({id}))});
 const bound={};
 for(const n of ['host/raw_audit.py','BUDGET.json','PROTOCOL.md','EVIDENCE.md','UPSTREAM.json','check_receipts.py'])await fs.writeFile(dir+'/'+n,'fixture');
 for(const n of ['host/raw_audit.py','ACCEPTANCE.json','BUDGET.json','PROTOCOL.md','EVIDENCE.md','UPSTREAM.json','check_receipts.py'])bound[n]=hash(await fs.readFile(dir+'/'+n));
 const review={status:'FINAL_IMPLEMENTATION_REVIEW_PASS',covered_files:bound};
 await put(dir+'/results/REVIEW_STATUS.json',review);
 await put(dir+'/results/CONFIRMATION_FREEZE.json',{bound_files:bound,review_status_sha256:hash(await fs.readFile(dir+'/results/REVIEW_STATUS.json'))});
 const frozen=hash(await fs.readFile(dir+'/results/CONFIRMATION_FREEZE.json'));
 await put(dir+'/results/REMOTE_FREEZE.json',{freeze_sha256:frozen});
 const cases=[names,[...names].reverse(),[...names].sort((a,b)=>hash(a).localeCompare(hash(b)))].flatMap((ns,round)=>ns.map(case_id=>({round,case_id,status:'PASS'})));
 const raw={cases,confirmation_unstarted:[],confirmation_status:'RAW_CONFIRMATION_PASS',manifest_valid:true,process_ledger_valid:true,problems:[],input_manifest_sha256:'manifest',forbidden_counts:Object.fromEntries(['GPU_queries','GPU_initializations','model_file_reads','model_requests','graph_computes','scientific_native_starts'].map(k=>[k,0])),confirmation_receipts:cases.map(r=>({...r,freeze_sha256:frozen}))};
 const prefix=Buffer.from(JSON.stringify({seq:1,kind:'BROKER_ARMED'})+'\n');
 await fs.writeFile(base+'/task/prefix.jsonl',prefix);await fs.writeFile(base+'/task/PROCESS_LEDGER.jsonl',Buffer.concat([prefix,Buffer.from(JSON.stringify({seq:2,kind:'BROKER_CLOSING'})+'\n')]));
 raw.ledger_prefix={path:'task/prefix.jsonl',bytes:prefix.length,sha256:hash(prefix)};raw.input_manifest_path='input-manifest.json';
 await put(base+'/input-manifest.json',{members:[raw.ledger_prefix]});raw.input_manifest_sha256=hash(await fs.readFile(base+'/input-manifest.json'));
 await put(base+'/task/BOOTSTRAP_REGISTRY.json',{mode:'cold-win32-v1',ledger_parts:['task/PROCESS_LEDGER.jsonl'],task_begin_ns:0,outer_processes:[{pid:1,created_filetime:'10000000'}]});
 await put(base+'/task/BOOTSTRAP_CLOSED.json',{mode:'cold-win32-v1',status:'OUTER_CLOSED_SUCCESS',handles_closed:true,job_active_processes:0,errors:[],task_begin_ns:0,broker_exit_code:0,task_end_ns:2000000000,outer_processes:[{pid:1,created_filetime:'10000000',exit_filetime:'30000000'}]});
 await put(base+'/audit.json',raw);const digest=hash(await fs.readFile(base+'/audit.json'));
 const restore={status:'REMOTE_RESTORE_RECOMPUTATION_MATCH',byte_identical:true,expected_report_sha256:digest,recomputed_report_sha256:digest,embedded_manifest_sha256:'archive-manifest',input_manifest_sha256:raw.input_manifest_sha256,freeze_sha256:frozen,packaged_bound_files:bound,packaged_auditor_sha256:bound['host/raw_audit.py']};
 await put(dir+'/results/REMOTE_RESTORE.json',restore);
 await put(dir+'/results/ARCHIVE.json',{raw_audit_sha256:digest,manifest_sha256:'archive-manifest',auditor_sha256:bound['host/raw_audit.py']});
 return {base,dir,put,raw,restore,closing:await auditClosure(base,{exit_code:0},'audit.json',{write:false})};
}
async function gate(t,change,expected){const f=await fixture();t.after(()=>fs.rm(f.base,{recursive:true,force:true}));await change(f);const r=await writeFinal(f.base,'audit.json',f.closing,'fixture-commit');assert.equal(r.status,expected);}
test('complete synthetic bindings can reach READY',t=>gate(t,async()=>{},'ENGINEERING_READY'));
test('restored different report cannot qualify current audit',t=>gate(t,async f=>{f.raw.extra='changed';await f.put(f.base+'/audit.json',f.raw)},'ENGINEERING_BLOCKED'));
test('missing bootstrap blocks even a declared tail PASS',t=>gate(t,async f=>{f.closing.bootstrap_missing_fields=['unobserved']},'ENGINEERING_BLOCKED'));
test('unlisted source file invalidates review',t=>gate(t,async f=>fs.writeFile(f.dir+'/host/extra.py','new'),'ENGINEERING_BLOCKED'));
test('changed source invalidates review',t=>gate(t,async f=>fs.writeFile(f.dir+'/host/raw_audit.py','changed'),'ENGINEERING_BLOCKED'));
test('wrong restored freeze blocks',t=>gate(t,async f=>{f.restore.freeze_sha256='other';await f.put(f.dir+'/results/REMOTE_RESTORE.json',f.restore)},'ENGINEERING_BLOCKED'));
test('duplicate confirmation row blocks',t=>gate(t,async f=>{f.raw.cases[1]=f.raw.cases[0];await f.put(f.base+'/audit.json',f.raw)},'ENGINEERING_BLOCKED'));
test('missing forbidden counter blocks',t=>gate(t,async f=>{delete f.raw.forbidden_counts.GPU_queries;await f.put(f.base+'/audit.json',f.raw)},'ENGINEERING_BLOCKED'));
async function tailFixture(t,bootstrap=true){const f=await fixture();t.after(()=>fs.rm(f.base,{recursive:true,force:true}));await fs.writeFile(f.base+'/task/PROCESS_LEDGER.jsonl',JSON.stringify({seq:1,kind:'BROKER_ARMED'})+'\n'+JSON.stringify({seq:2,kind:'BROKER_CLOSING'})+'\n');const proc={pid:1,created_filetime:'10000000'};if(!bootstrap)await fs.unlink(f.base+'/task/BOOTSTRAP_REGISTRY.json');if(bootstrap)await f.put(f.base+'/task/BOOTSTRAP_REGISTRY.json',{mode:'cold-win32-v1',ledger_parts:['task/PROCESS_LEDGER.jsonl'],task_begin_ns:0,outer_processes:[proc]});await f.put(f.base+'/task/BOOTSTRAP_CLOSED.json',{mode:'cold-win32-v1',status:'OUTER_CLOSED_SUCCESS',handles_closed:true,job_active_processes:0,errors:[],task_begin_ns:0,broker_exit_code:0,task_end_ns:2000000000,outer_processes:[{...proc,exit_filetime:'30000000'}]});return f;}
test('actual complete outer identity receipts can pass tail',async t=>{const f=await tailFixture(t);const r=await auditClosure(f.base,{exit_code:0},'audit.json');assert.equal(r.status,'TAIL_AUDIT_PASS');assert.equal(r.charged_process_lifetime_seconds,2)});
test('absent bootstrap observations fail tail',async t=>{const f=await tailFixture(t,false);const r=await auditClosure(f.base,{exit_code:0},'audit.json');assert.equal(r.status,'TAIL_AUDIT_FAILED');assert.equal(r.charged_process_lifetime_seconds,null)});

test('matching archive and restore with unreviewed auditor still blocks',t=>gate(t,async f=>{f.restore.packaged_auditor_sha256='unreviewed';await f.put(f.dir+'/results/REMOTE_RESTORE.json',f.restore);const a=JSON.parse(await fs.readFile(f.dir+'/results/ARCHIVE.json'));a.auditor_sha256='unreviewed';await f.put(f.dir+'/results/ARCHIVE.json',a)},'ENGINEERING_BLOCKED'));

test('tail from other raw report cannot qualify',t=>gate(t,async f=>{f.closing.raw_audit_sha256='other'},'ENGINEERING_BLOCKED'));
test('tail ledger without exact selected prefix cannot qualify',t=>gate(t,async f=>{await fs.writeFile(f.base+'/task/PROCESS_LEDGER.jsonl','other\n')},'ENGINEERING_BLOCKED'));
test('tail without budget fields cannot qualify',t=>gate(t,async f=>{delete f.closing.charged_process_lifetime_seconds},'ENGINEERING_BLOCKED'));
