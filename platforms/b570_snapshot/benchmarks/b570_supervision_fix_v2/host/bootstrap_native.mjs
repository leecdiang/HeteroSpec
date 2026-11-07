// CPU Win32 binding loaded into the existing Node service. Never spawns a helper.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {createRequire} from 'node:module';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
export function unpackNative(archive,lock){
 if(archive.length!==lock.tarball_bytes||'sha512-'+crypto.createHash('sha512').update(archive).digest('base64')!==lock.integrity)throw Error('CPU dependency archive identity mismatch');
 const tar=gunzipSync(archive,{maxOutputLength:4*1024*1024});let result=null;
 for(let i=0;i+512<=tar.length;){
  const h=tar.subarray(i,i+512);if(h.every(x=>x===0))break;
  const name=h.subarray(0,100).toString().split('\0')[0],size=parseInt(h.subarray(124,136).toString().replace(/\0/g,'').trim(),8);
  if(!Number.isSafeInteger(size)||size<0||i+512+size>tar.length)throw Error('invalid pinned tar member');
  if(name===lock.member){if(result||![0,48].includes(h[156]))throw Error('ambiguous native member');result=Buffer.from(tar.subarray(i+512,i+512+size));}
  i+=512+Math.ceil(size/512)*512;
 }
 if(!result||result.length!==lock.native_bytes||sha(result)!==lock.native_sha256)throw Error('CPU native member identity mismatch');
 return result;
}
export async function loadWindowsApi(base,environment){
 if(os.platform()!=='win32'||os.arch()!=='x64')throw Error('Existing Windows x64 tool service required; native load must support the pinned Node-API bridge');
 const lock=JSON.parse(await fs.readFile(new URL('./BOOTSTRAP_DEPENDENCY.json',import.meta.url)));
 const dir=path.join(base,'deps');await fs.mkdir(dir); // Fresh only; no reuse or npm invocation.
 const response=await fetch(lock.tarball,{redirect:'error',signal:AbortSignal.timeout(30000)});
 if(!response.ok||Number(response.headers.get('content-length'))>lock.tarball_bytes)throw Error('CPU dependency download failed');
 const chunks=[];let bytes=0;for await(const chunk of response.body){bytes+=chunk.length;if(bytes>lock.tarball_bytes)throw Error('CPU dependency exceeds pinned size');chunks.push(chunk);}
 const archive=Buffer.concat(chunks),native=unpackNative(archive,lock);
 await fs.writeFile(path.join(dir,'koffi.tgz'),archive,{flag:'wx'});
 const file=path.join(dir,'koffi-win32-x64.node');await fs.writeFile(file,native,{flag:'wx'});
 await fs.writeFile(path.join(dir,'DEPENDENCY_RECEIPT.json'),JSON.stringify({...lock,loaded_path:file,downloaded_utc:new Date().toISOString(),installer_children:0},null,2)+'\n',{flag:'wx'});
 const k=createRequire(import.meta.url)(file);if(k.version!==lock.version)throw Error('CPU dependency version mismatch');
 return windowsApi(k,environment);
}
export function windowsApi(k,environment){
 const lib=k.load('C:/Windows/System32/kernel32.dll');
 const FT=k.struct('B570_FT',{low:'uint32_t',high:'uint32_t'});
 const SA=k.struct('B570_SA',{length:'uint32_t',descriptor:'void *',inherit:'int'});
 const SI=k.struct('B570_SI',{cb:'uint32_t',reserved:'void *',desktop:'void *',title:'void *',x:'uint32_t',y:'uint32_t',xs:'uint32_t',ys:'uint32_t',xc:'uint32_t',yc:'uint32_t',fill:'uint32_t',flags:'uint32_t',show:'uint16_t',reservedSize:'uint16_t',reservedBytes:'void *',stdin:'void *',stdout:'void *',stderr:'void *'});
 const EX=k.struct('B570_EX',{si:SI,attributes:'void *'});
 const PI=k.struct('B570_PI',{process:'void *',thread:'void *',pid:'uint32_t',tid:'uint32_t'});
 if(k.sizeof(SI)!==104||k.sizeof(EX)!==112||k.sizeof(PI)!==24||k.sizeof(SA)!==24)throw Error('Win32 x64 ABI layout mismatch');
 const f=signature=>lib.func(signature);
 const error=f('uint32_t __stdcall GetLastError()');
 const need=(ok,name)=>{if(!ok)throw Error(name+': Win32 '+error());};
 const close=f('int __stdcall CloseHandle(void *)');
 const wait=f('uint32_t __stdcall WaitForSingleObject(void *, uint32_t)');
 const terminate=f('int __stdcall TerminateProcess(void *, uint32_t)');
 const jobCreate=f('void * __stdcall CreateJobObjectW(void *, const char16_t *)');
 const jobSet=f('int __stdcall SetInformationJobObject(void *, int, void *, uint32_t)');
 const jobAssign=f('int __stdcall AssignProcessToJobObject(void *, void *)');
 const jobKill=f('int __stdcall TerminateJobObject(void *, uint32_t)');
 const jobQuery=f('int __stdcall QueryInformationJobObject(void *, int, _Out_ void *, uint32_t, void *)');
 const qpc=f('int __stdcall QueryPerformanceCounter(_Out_ int64_t *)');
 const qpf=f('int __stdcall QueryPerformanceFrequency(_Out_ int64_t *)');
 const current=f('void * __stdcall GetCurrentProcess()');
 const pid=f('uint32_t __stdcall GetCurrentProcessId()');
 const times=f('int __stdcall GetProcessTimes(void *, _Out_ B570_FT *, _Out_ B570_FT *, _Out_ B570_FT *, _Out_ B570_FT *)');
 const code=f('int __stdcall GetExitCodeProcess(void *, _Out_ uint32_t *)');
 const resume=f('uint32_t __stdcall ResumeThread(void *)');
 const create=f('int __stdcall CreateProcessW(const char16_t *, _Inout_ uint16_t *, void *, void *, int, uint32_t, void *, const char16_t *, _Inout_ B570_EX *, _Out_ B570_PI *)');
 const createFile=f('void * __stdcall CreateFileW(const char16_t *, uint32_t, uint32_t, B570_SA *, uint32_t, uint32_t, void *)');
 const initAttr=f('int __stdcall InitializeProcThreadAttributeList(void *, uint32_t, uint32_t, _Inout_ size_t *)');
 const updateAttr=f('int __stdcall UpdateProcThreadAttribute(void *, uint32_t, size_t, void *, size_t, void *, void *)');
 const deleteAttr=f('void __stdcall DeleteProcThreadAttributeList(void *)');
 const valid=h=>h&&k.address(h)!==0xffffffffffffffffn;
 function osTimes(h){const a={},b={},c={},d={};need(times(h,a,b,c,d),'GetProcessTimes');const value=x=>((BigInt(x.high)<<32n)|BigInt(x.low)).toString();return {created_filetime:value(a),exit_filetime:value(b),kernel_100ns:value(c),user_100ns:value(d)};}
 function now(){const c=[0n],hz=[0n];need(qpc(c),'QueryPerformanceCounter');need(qpf(hz),'QueryPerformanceFrequency');const n=BigInt(c[0])*1000000000n/BigInt(hz[0]);if(n>BigInt(Number.MAX_SAFE_INTEGER))throw Error('QPC exceeds exact JSON range');return Number(n);}
 return {
  now,observer(){return {pid:pid(),...osTimes(current()),role:'pre-existing Node tool service'};},
  spawnSuspended(python,script,base){
   let job=null,attrs=null,initialized=false;const io=[];
   try{
    job=jobCreate(null,null);need(job,'CreateJobObject');const limits=Buffer.alloc(144);limits.writeUInt32LE(0x2000,16);need(jobSet(job,9,limits,limits.length),'SetInformationJobObject');
    const sa={length:k.sizeof(SA),descriptor:null,inherit:1};
    for(const [name,access,disposition] of [['NUL',0x80000000,3],[path.join(base,'task','BROKER.stdout.log'),0x40000000,1],[path.join(base,'task','BROKER.stderr.log'),0x40000000,1]]){const h=createFile(name,access,1,sa,disposition,128,null);need(valid(h),'CreateFile');io.push(h);}
    const size=[0];initAttr(null,1,0,size);if(!Number.isSafeInteger(size[0])||size[0]<=0||size[0]>65536)throw Error('invalid handle-list size');attrs=Buffer.alloc(size[0]);need(initAttr(attrs,1,0,size),'InitializeProcThreadAttributeList');initialized=true;
    const list=Buffer.alloc(24);k.encode(list,k.array('void *',3),io);need(updateAttr(attrs,0,0x20002,list,24,null,null),'UpdateProcThreadAttribute');
    const command=Buffer.from(quoteArg(python)+' -I -S -B '+quoteArg(script)+'\0','utf16le');
    const env=new Map(Object.entries(environment).filter(([,v])=>v!==undefined).map(([key,v])=>[key.toUpperCase(),v]));
    for(const [key,value] of Object.entries({TEMP:path.join(base,'tmp'),TMP:path.join(base,'tmp'),PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8'}))env.set(key,value);
    const block=Buffer.from([...env].sort(([a],[b])=>a.localeCompare(b)).map(([key,value])=>key+'='+value).join('\0')+'\0\0','utf16le');
    const info={si:{cb:k.sizeof(EX),flags:0x100,stdin:io[0],stdout:io[1],stderr:io[2]},attributes:attrs},p={};
    need(create(python,command,null,null,1,0x08080404,block,base,info,p),'CreateProcessW');
    return {...p,job}; // First success point: caller owns and accounts for the suspended process.
   }catch(e){if(job)close(job);throw e;}
   finally{if(initialized)deleteAttr(attrs);for(const h of io)close(h);}
  },
  assign(p){need(jobAssign(p.job,p.process),'AssignProcessToJobObject');},
  resume(p){if(resume(p.thread)===0xffffffff)throw Error('ResumeThread: '+error());need(close(p.thread),'CloseThread');p.thread=null;},
  times:p=>osTimes(p.process),
  exited(p){const n=wait(p.process,0);if(n===0)return true;if(n===258)return false;throw Error('process wait failed: '+error());},
  exitCode(p){const c=[0];need(code(p.process,c),'GetExitCodeProcess');return c[0];},
  active(p){const b=Buffer.alloc(48);need(jobQuery(p.job,1,b,48,null),'QueryInformationJobObject');return b.readUInt32LE(40);},
  kill(p){need(jobKill(p.job,125),'TerminateJobObject');},
  killRoot(p){need(terminate(p.process,125),'TerminateProcess');},
  release(p){if(p.thread){need(close(p.thread),'CloseThread');p.thread=null;}need(close(p.process),'CloseProcess');need(close(p.job),'CloseJob');}
 };
}
export function quoteArg(value){if(typeof value!=='string'||value.includes('\0'))throw Error('invalid command argument');return '"'+value.replace(/(\\*)"/g,'$1$1\\"').replace(/(\\+)$/,'$1$1')+'"';}
