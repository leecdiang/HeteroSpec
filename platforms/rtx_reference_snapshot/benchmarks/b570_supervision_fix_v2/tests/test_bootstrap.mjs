import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import sync from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {auditClosure} from '../host/closure_audit.mjs';
import {ColdSession} from '../host/bootstrap_cold.mjs';
import {quoteArg,unpackNative} from '../host/bootstrap_native.mjs';
async function setup(t,options={}){
 const base=await fs.mkdtemp(path.join(os.tmpdir(),'b570-cold-'));await fs.mkdir(path.join(base,'task'));const events=[];
 const state={exited:false,active:0,clock:1000000000,created:'134000000000000001'};
 const api={now:()=>++state.clock,observer:()=>({pid:1,created_filetime:'133000000000000000'}),spawnSuspended(){events.push('create-suspended');if(options.createFail)throw Error('create failure');return {pid:2};},times(){events.push('times');return {created_filetime:state.created,exit_filetime:state.exited?'134000000000100001':'0'};},assign(){events.push('assign');if(options.assignFail)throw Error('assignment failure');},resume(){events.push('resume');assert.ok(sync.existsSync(path.join(base,'task/BOOTSTRAP_REGISTRY.json')));if(options.resumeFail)throw Error('resume failure');sync.writeFileSync(path.join(base,'task/READY.json'),JSON.stringify({pid:2,created_filetime:state.created,mode:'cold-win32-v1',source_sha256:'reviewed'}));},exited:()=>state.exited,active:()=>state.active,exitCode:()=>options.exitCode??0,kill(){events.push('kill-job');state.exited=true;state.active=0;},killRoot(){events.push('kill-root');state.exited=true;},release(){events.push('release');}};
 const session=new ColdSession(api,{base,python:'python.exe',pythonHash:'sha',binding:{freeze_sha256:'freeze',bound_files:{'host/broker.py':'reviewed'}}});
 t.after(async()=>{if(session.timer)clearInterval(session.timer);await fs.rm(base,{recursive:true,force:true});});
 return {base,events,state,session};
}
test('cold create is suspended, registered before resume, ready without predecessor',async t=>{const f=await setup(t);await f.session.start();assert.equal(await f.session.ready(),true);assert.equal(sync.existsSync(path.join(f.base,'task/PROCESS_LEDGER_v2.jsonl')),false);assert.deepEqual(f.events.slice(0,4),['create-suspended','times','assign','resume']);});
test('actual exit is read before handles release and closure receipt',async t=>{const f=await setup(t);await f.session.start();f.state.exited=true;await f.session.tick();const r=JSON.parse(await fs.readFile(path.join(f.base,'task/BOOTSTRAP_CLOSED.json')));assert.equal(r.status,'OUTER_CLOSED_SUCCESS');assert.equal(r.outer_processes[0].exit_filetime,'134000000000100001');assert.equal(f.events.at(-1),'release');});
test('resume failure still terminates and accounts for created process',async t=>{const f=await setup(t,{resumeFail:true});await assert.rejects(f.session.start(),/resume failure/);assert.ok(f.events.includes('kill-root'));assert.equal(f.session.closed.status,'OUTER_CLOSED_FAILED');assert.equal(f.session.closed.outer_processes.length,1);});
test('assignment failure closes suspended root without a job membership assumption',async t=>{const f=await setup(t,{assignFail:true});await assert.rejects(f.session.start(),/assignment/);assert.ok(f.events.includes('kill-root'));assert.equal(f.session.closed.status,'OUTER_CLOSED_FAILED');});
test('create failure never invents process identity or closure',async t=>{const f=await setup(t,{createFail:true});await assert.rejects(f.session.start(),/create failure/);assert.equal(f.session.process,null);assert.equal(sync.existsSync(path.join(f.base,'task/BOOTSTRAP_REGISTRY.json')),false);});
test('unexpected broker exit is failed even with observed closure',async t=>{const f=await setup(t,{exitCode:2});await f.session.start();f.state.exited=true;await f.session.tick();assert.equal(f.session.closed.status,'OUTER_CLOSED_FAILED');});
test('live descendants are killed and cannot produce successful outer closure',async t=>{const f=await setup(t);await f.session.start();f.state.exited=true;f.state.active=1;await f.session.tick();await f.session.tick();assert.ok(f.events.includes('kill-job'));assert.equal(f.session.closed.status,'OUTER_CLOSED_FAILED');});
test('closure persistence failure cannot become successful returned receipt',async t=>{const f=await setup(t);await f.session.start();await fs.writeFile(path.join(f.base,'task/BOOTSTRAP_CLOSED.json'),'preserved');f.state.exited=true;await f.session.tick();assert.equal(f.session.closed.status,'OUTER_CLOSED_FAILED');assert.equal(await fs.readFile(path.join(f.base,'task/BOOTSTRAP_CLOSED.json'),'utf8'),'preserved');});
test('outer deadline kills job and rejects success',async t=>{const f=await setup(t);await f.session.start();f.state.clock+=28801e9;await f.session.tick();assert.ok(f.events.includes('kill-job'));assert.equal(f.session.closed.status,'OUTER_CLOSED_FAILED');});
test('Win32 arguments quote embedded quotes and trailing backslashes',()=>{assert.equal(quoteArg('C:\\a b\\'),'"C:\\a b\\\\"');assert.equal(quoteArg('a"b'),'"a\\"b"');assert.throws(()=>quoteArg('a\0b'));});
function archive(){const data=Buffer.from('native fixture'),h=Buffer.alloc(512);h.write('package/win32_x64/koffi.node');h.write(data.length.toString(8).padStart(11,'0')+'\0',124);h[156]=48;const bytes=gzipSync(Buffer.concat([h,data,Buffer.alloc(512-data.length),Buffer.alloc(1024)]));return {bytes,lock:{tarball_bytes:bytes.length,integrity:'sha512-'+crypto.createHash('sha512').update(bytes).digest('base64'),member:'package/win32_x64/koffi.node',native_bytes:data.length,native_sha256:crypto.createHash('sha256').update(data).digest('hex')}};}
test('pinned dependency can be extracted without installer child',()=>{const a=archive();assert.equal(unpackNative(a.bytes,a.lock).toString(),'native fixture');});
test('archive or native hash drift is refused before loading code',()=>{const a=archive();assert.throws(()=>unpackNative(Buffer.from('changed'),a.lock));assert.throws(()=>unpackNative(a.bytes,{...a.lock,native_sha256:'other'}));});

test('real ColdSession.stop receipt passes closure auditor; substituted receipts fail',async t=>{
 const f=await setup(t);await f.session.start();
 const prefix=Buffer.from(JSON.stringify({seq:1,kind:'BROKER_ARMED'})+'\n');
 await fs.writeFile(path.join(f.base,'task/prefix.jsonl'),prefix);
 await fs.writeFile(path.join(f.base,'task/PROCESS_LEDGER.jsonl'),Buffer.concat([prefix,Buffer.from(JSON.stringify({seq:2,kind:'BROKER_CLOSING'})+'\n')]));
 const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
 const ledger_prefix={path:'task/prefix.jsonl',bytes:prefix.length,sha256:hash(prefix)};
 const manifest=Buffer.from(JSON.stringify({members:[ledger_prefix]}));await fs.writeFile(path.join(f.base,'input.json'),manifest);
 await fs.writeFile(path.join(f.base,'audit.json'),JSON.stringify({ledger_prefix,input_manifest_path:'input.json',input_manifest_sha256:hash(manifest)}));
 f.state.exited=true;const closed=await f.session.stop();
 assert.equal((await auditClosure(f.base,closed,'audit.json',{write:false})).status,'TAIL_AUDIT_PASS');
 assert.equal((await auditClosure(f.base,{exit_code:0},'audit.json',{write:false})).status,'TAIL_AUDIT_FAILED');
 assert.equal((await auditClosure(f.base,{...closed,task_end_ns:closed.task_end_ns+1},'audit.json',{write:false})).status,'TAIL_AUDIT_FAILED');
});
