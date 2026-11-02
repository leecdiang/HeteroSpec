"""Pin and supervise real-operand operator experiments in the shared ledger."""
from pathlib import Path
import argparse, os, shutil, subprocess, sys, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,sha,need,utc
import budget

def build(parent,source,out):
    parent=Path(parent); b=read(parent); out=Path(out).resolve();need(not out.exists(),'fresh build')
    src=out/'source';src.mkdir(parents=True);source=Path(source).resolve();shutil.copyfile(source,src/source.name)
    upstream=Path(b['source']['root']); original=upstream.parent.parent/'build'
    libs=[original/f'runtime/ggml/src/Release/{n}.lib' for n in ('ggml','ggml-base')]+[original/'runtime/src/Release/llama.lib']
    need(all(p.exists() for p in libs),'original import libraries')
    cm='cmake_minimum_required(VERSION 3.20)\nproject(operator_replay LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 17)\n'
    cm+=f'add_executable(operator_replay {source.name})\n'
    cm+='target_compile_options(operator_replay PRIVATE /O2 /W4 /fp:precise /utf-8)\n'
    cm+='target_compile_definitions(operator_replay PRIVATE LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED)\n'
    cm+='target_include_directories(operator_replay PRIVATE '+ ' '.join('"'+(upstream/p).as_posix()+'"' for p in ('include','ggml/include','vendor'))+' "'+source.parent.as_posix()+'")\n'
    cm+='target_link_libraries(operator_replay PRIVATE '+' '.join('"'+p.as_posix()+'"' for p in libs)+')\n'
    (src/'CMakeLists.txt').write_text(cm)
    commands=[['C:/Program Files/CMake/bin/cmake.exe','-S',str(src),'-B',str(out/'build'),'-G','Visual Studio 17 2022','-A','x64'],['C:/Program Files/CMake/bin/cmake.exe','--build',str(out/'build'),'--config','Release','--parallel','4']]
    write(out/'COMMANDS.json',{'argv':commands,'parent_sha256':sha(parent),'source_sha256':sha(source),'utc':utc()})
    for i,c in enumerate(commands):
        with (out/f'command-{i}.log').open('xb') as log:subprocess.run(c,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
    exe=out/'build/Release/operator_replay.exe';files=[exe]
    for f in b['files']:
        p=Path(f['path'])
        if p.suffix=='.dll':
            need(sha(p)==f['sha256'],'parent DLL drift');dest=exe.parent/p.name;shutil.copyfile(p,dest);files.append(dest)
    write(out/'BUILD.json',{'executable':str(exe),'files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files], 'supervisor':b['supervisor'],'supervisor_sha256':sha(b['supervisor']),'parent_sha256':sha(parent),'parent_path':str(parent.resolve()),'source_sha256':sha(source)})

def run(build,config,out,root,lock,limit):
    b=read(build);config=Path(config).resolve();out=Path(out).resolve();root=Path(root);lock=Path(lock)
    need(not out.exists(),'fresh attempt');need(sha(b['supervisor'])==b['supervisor_sha256'],'supervisor drift')
    inputs=read(config);fixtures=inputs['fixtures']
    need(sha(inputs['target_model'])==inputs['target_sha256'],'model content drift')
    need(sha(inputs['certificate_path'])==inputs['certificate_sha256'],'observer certificate drift')
    for f in fixtures:
        for k,h in f['hashes'].items():need(sha(f[k])==h,'captured operand drift')
    out.mkdir(parents=True);write(lock,{'pid':os.getpid(),'attempt':str(out),'utc':utc()})
    started=False;cleaned=False;success=False;begin=time.monotonic();actual=0
    try:
        budget.reserve(root/'LEDGER.jsonl',str(out),0,len(fixtures),limit);started=True
        write(out/'FILES.json',{'files':b['files']});shutil.copyfile(config,out/'CONFIG.json')
        command=[sys.executable,'-B',b['supervisor'],'--manifest',str(out/'FILES.json'),'--receipt',str(out/'SUPERVISOR.json'),'--limit',str(limit),'--minimum-free-bytes',str(20*1024**3),b['executable'],str(config),str(out/'native')]
        write(out/'COMMAND.json',{'argv':command,'build_sha256':sha(build),'config_sha256':sha(config),'utc':utc()})
        p=subprocess.run(command,timeout=limit+180)
        r=read(out/'SUPERVISOR.json');cleaned=r.get('job_accounting',{}).get('active_processes')==0
        n=read(out/'native/result.json');actual=len(n.get('rows',[]))
        need(cleaned and p.returncode==0 and n['normal_cleanup_returned'],'supervision/native failure')
        loaded={Path(x['path']).name.lower():x['sha256'] for x in r['loaded_module_hashes']}
        for f in b['files']:
            name=Path(f['path']).name.lower()
            if name in loaded:need(loaded[name]==f['sha256'],'loaded library drift')
        need('ggml-vulkan.dll' in loaded,'native Vulkan unobserved')
        need(actual==len(fixtures) and n['status']==inputs.get('expected_status','OWN_PATH_REPLAY_PASS'),'registered replay expectation mismatch');success=True
    finally:
        if (out/'SUPERVISOR.json').exists():cleaned=read(out/'SUPERVISOR.json').get('job_accounting',{}).get('active_processes')==0
        if (out/'native/result.json').exists():actual=len(read(out/'native/result.json').get('rows',[]))
        seconds=time.monotonic()-begin
        write(out/'RECEIPT.json',{'success':success,'cleanup_verified':cleaned,'operator_calls':actual,'completed_model_requests':0,'owned_seconds':seconds})
        if started and cleaned:budget.append(root/'LEDGER.jsonl',{'event':'END','attempt':str(out),'completed_model_requests':0,'operator_calls':actual,'seconds':seconds,'success':success})
        if not started or cleaned:lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('build');a.add_argument('--parent',required=True);a.add_argument('--source',required=True);a.add_argument('--out',required=True)
    a=sub.add_parser('run');a.add_argument('--build',required=True);a.add_argument('--config',required=True);a.add_argument('--out',required=True);a.add_argument('--root',required=True);a.add_argument('--lock',required=True);a.add_argument('--limit',type=int,default=1200)
    a=p.parse_args()
    if a.command=='build':build(a.parent,a.source,a.out)
    else:run(a.build,a.config,a.out,a.root,a.lock,a.limit)
