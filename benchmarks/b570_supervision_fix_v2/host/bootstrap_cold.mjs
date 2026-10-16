// The caller is the already-running Node tool service, not a task-owned wrapper.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadWindowsApi} from './bootstrap_native.mjs';
import {publish} from './queue_client.mjs';
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const DESIGN=fileURLToPath(new URL('../',import.meta.url));
export const BASE='C:/hs/b570-supervision-fix-v2-20261016';
export async function writeNew(file,value){const f=await fs.open(file,'wx');try{await f.writeFile(JSON.stringify(value,null,2)+'\n');await f.sync();}finally{await f.close();}}
export async function verifySource(design){
 const freeze=JSON.parse(await fs.readFile(path.join(design,'SOURCE_REVIEW_FREEZE.json')));
 if(freeze.scope!=='source_review_only'||freeze.review_status!=='scoped-clean')throw Error('new source-only review binding required');
 const review=await fs.readFile(path.join(design,'review/FINAL_REVIEW.json')),status=await fs.readFile(path.join(design,'review/FINAL_STATUS.json'));
 if(digest(review)!==freeze.review_report_sha256||digest(status)!==freeze.review_status_sha256||JSON.parse(status).status!=='scoped-clean')throw Error('source review receipt mismatch');
 for(const [name,hash] of Object.entries(freeze.bound_files)){
  if(name.includes('..')||name.includes('\\')||name.includes(':')||name.startsWith('/'))throw Error('noncanonical source member');
  const file=path.join(design,name),s=await fs.lstat(file);if(s.isSymbolicLink()||!s.isFile()||digest(await fs.readFile(file))!==hash)throw Error('reviewed source drift: '+name);
 }
 const files=[];async function walk(p,rel){for(const e of await fs.readdir(p,{withFileTypes:true})){if(e.name==='__pycache__')throw Error('unreviewed bytecode before bootstrap');if(e.isSymbolicLink())throw Error('source alias');if(e.isDirectory())await walk(path.join(p,e.name),rel+e.name+'/');else files.push(rel+e.name);}}
 await walk(path.join(design,'host'),'host/');
 if(JSON.stringify(files.sort())!==JSON.stringify(Object.keys(freeze.bound_files).filter(p=>p.startsWith('host/')).sort()))throw Error('host source set drift');
 return {freeze_sha256:digest(await fs.readFile(path.join(design,'SOURCE_REVIEW_FREEZE.json'))),bound_files:freeze.bound_files};
}
export async function startCold({python,toolBeginNs}){
 if(process.platform!=='win32'||process.arch!=='x64')throw Error('Windows x64 existing Node service required');
 if(path.win32.resolve(DESIGN).toLowerCase()!==path.win32.resolve(BASE,'repo/benchmarks/b570_supervision_fix_v2').toLowerCase())throw Error('wrong new-task source layout');
 if(typeof toolBeginNs!=='bigint'||toolBeginNs>process.hrtime.bigint())throw Error('capture toolBeginNs before task preparation');
 const binding=await verifySource(DESIGN);
 const pythonStat=await fs.lstat(python);if(!pythonStat.isFile()||pythonStat.isSymbolicLink())throw Error('explicit existing CPU Python executable required');
 const pythonHash=digest(await fs.readFile(python));
 await fs.mkdir(path.join(BASE,'task')); // Exclusive cold task; no historical ledger or reset.
 await fs.mkdir(path.join(BASE,'queue'));await fs.mkdir(path.join(BASE,'tmp'));
 await fs.mkdir(path.join(DESIGN,'results'),{recursive:true});
 try{
  const api=await loadWindowsApi(BASE);
  const setupNs=Number(process.hrtime.bigint()-toolBeginNs);if(!Number.isSafeInteger(setupNs)||setupNs>=28800e9)throw Error('preparation exceeded task wall allowance');
  const session=new ColdSession(api,{base:BASE,python,pythonHash,binding,setupNs});
  await session.start();return session;
 }catch(error){await writeNew(path.join(BASE,'task','BOOTSTRAP_START_ERROR.json'),{error:String(error),scope:'Admission/creation failure; inspect actual outer receipts, never infer zero starts'});throw error;}
}
export class ColdSession {
 constructor(api,{base,python,pythonHash,binding,setupNs=0}){this.api=api;this.base=base;this.python=python;this.pythonHash=pythonHash;this.binding=binding;this.setupNs=setupNs;this.process=null;this.errors=[];this.closed=null;this.timer=null;this.busy=false;this.stopAt=null;this.assigned=false;this.next=1;}
 file(name){return path.join(this.base,'task',name);}
 async start(){
  this.begin=this.api.now()-this.setupNs;if(!Number.isSafeInteger(this.begin)||this.begin<0)throw Error('invalid task clock boundary');
  this.observer=this.api.observer();
  const script=path.join(this.base,'repo/benchmarks/b570_supervision_fix_v2/host/broker.py');
  await writeNew(this.file('BOOTSTRAP_INTENT.json'),{schema:1,mode:'cold-win32-v1',task_begin_ns:this.begin,setup_elapsed_ns:this.setupNs,observer:this.observer,python:this.python,python_sha256:this.pythonHash,script,source_review_sha256:this.binding.freeze_sha256,ledger_parts:['task/PROCESS_LEDGER.jsonl'],no_predecessor:true});
  try{
   this.process=this.api.spawnSuspended(this.python,script,this.base);
   this.identity={pid:this.process.pid,...this.api.times(this.process)};
   if(BigInt(this.identity.created_filetime)<=0n||BigInt(this.identity.exit_filetime)!==0n)throw Error('invalid suspended broker identity');
   await writeNew(this.file('BOOTSTRAP_REGISTRY.json'),{schema:1,mode:'cold-win32-v1',task_begin_ns:this.begin,registered_ns:this.api.now(),observer:this.observer,outer_processes:[this.identity],source_review_sha256:this.binding.freeze_sha256,broker_source_sha256:this.binding.bound_files['host/broker.py'],ledger_parts:['task/PROCESS_LEDGER.jsonl']});
   this.api.assign(this.process);this.assigned=true;
   this.api.resume(this.process);this.resumed=true;
   await writeNew(this.file('BOOTSTRAP_RESUMED.json'),{pid:this.process.pid,resumed_ns:this.api.now(),registry_before_resume:true});
  }catch(error){
   this.errors.push(String(error));
   if(this.process){try{this.api.killRoot(this.process);}catch(e){this.errors.push(String(e));}this.stopAt=this.api.now();this.monitor();await this.waitClosed(15000);}
   throw error;
  }
  this.monitor();return this;
 }
 monitor(){if(!this.timer)this.timer=setInterval(()=>{void this.tick();},100);}
 async tick(){
  if(this.busy||this.closed||!this.process)return;this.busy=true;
  try{
   const now=this.api.now();
   if(now-this.begin>=28800e9||this.stopAt!==null&&now-this.stopAt>10e9){this.errors.push('outer deadline forced termination');if(this.assigned)this.api.kill(this.process);else this.api.killRoot(this.process);}
   if(!this.api.exited(this.process))return;
   if(this.assigned&&this.api.active(this.process)!==0){this.errors.push('broker exited with live job descendants');this.api.kill(this.process);return;}
   const times=this.api.times(this.process),exit=this.api.exitCode(this.process);
   if(BigInt(times.exit_filetime)<=BigInt(times.created_filetime))throw Error('missing actual OS exit time');
   if(this.identity&&times.created_filetime!==this.identity.created_filetime)throw Error('retained process identity changed');
   const outer={pid:this.process.pid,...times};
   this.api.release(this.process);
   const receipt={schema:1,mode:'cold-win32-v1',broker_exit_code:exit,task_begin_ns:this.begin,task_end_ns:this.api.now(),outer_processes:[outer],observer:this.observer,job_active_processes:0,handles_closed:true,errors:[...new Set(this.errors)],status:exit===0&&!this.errors.length?'OUTER_CLOSED_SUCCESS':'OUTER_CLOSED_FAILED'};
   clearInterval(this.timer);this.timer=null;
   try{await writeNew(this.file('BOOTSTRAP_CLOSED.json'),receipt);this.closed=receipt;}
   catch(error){this.closed={...receipt,status:'OUTER_CLOSED_FAILED',errors:[...receipt.errors,'closure persistence failed: '+String(error)]};}
  }catch(error){this.errors.push(String(error));try{if(this.assigned)this.api.kill(this.process);else this.api.killRoot(this.process);}catch(e){this.errors.push(String(e));}
   // Preserve diagnostics even if OS observation itself fails; never fabricate closure.
   await fs.writeFile(this.file('BOOTSTRAP_OBSERVER_ERROR.json'),JSON.stringify({errors:[...new Set(this.errors)],closed:false},null,2)+'\n').catch(()=>{});
  }finally{this.busy=false;}
 }
 async ready(){
  if(this.closed||!this.process||this.errors.length)return false;
  try{const r=JSON.parse(await fs.readFile(this.file('READY.json')));return r.pid===this.process.pid&&String(r.created_filetime)===this.identity.created_filetime&&r.mode==='cold-win32-v1'&&r.source_sha256===this.binding.bound_files['host/broker.py'];}
  catch(e){if(e.code==='ENOENT'||e instanceof SyntaxError)return false;throw e;}
 }
 async submit(id,argv,extra={}){if(!await this.ready()||this.stopAt!==null)throw Error('cold broker is not admitted');return publish(this.next++,id,argv,extra);}
 async result(id){if(!/^[A-Za-z0-9_-]+$/.test(id))throw Error('invalid request id');const names=(await fs.readdir(path.join(this.base,'queue'))).filter(n=>n.endsWith('-'+id+'.result.json'));if(names.length>1)throw Error('duplicate request id');return names.length?JSON.parse(await fs.readFile(path.join(this.base,'queue',names[0]))):null;}
 async stop(){if(this.closed)return this.closed;if(this.stopAt===null){this.stopAt=this.api.now();await writeNew(this.file('STOP'),{requested_ns:this.stopAt});}return this.waitClosed(15000);}
 async waitClosed(ms){const deadline=Date.now()+ms;while(!this.closed&&Date.now()<deadline){await this.tick();await new Promise(r=>setTimeout(r,50));}if(!this.closed)throw Error('outer closure not observed; keep session and report incomplete');return this.closed;}
}
