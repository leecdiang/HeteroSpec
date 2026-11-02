"""Parameterize the executed metadata4 Llama adapter; baseline has no new numerical fix."""
from __future__ import annotations
import argparse, importlib.util, shutil, sys
from lr_common import *
import parent
HERE=Path(__file__).resolve().parent

def adapt(worker,fresh_fix):
    worker=once(worker,'need(family=="Qwen","dense14b uses original Qwen source cohort");',
      'need(family=="Llama","Llama mechanism repair profile");')
    worker=once(worker,'slot.at("study_id")=="rtx_reference_repair_v1"','slot.at("study_id")=="'+STUDY+'"')
    worker=once(worker,'        if(admission_only){\n            result["producer_allocation_probes"]=json::array();',
      '        if(admission_only){\n            Pair fresh_capacity;\n            if(!resident_life)provision(fresh_capacity,t,d,arm_spec("C_QB"),root/"fresh_capacity");\n            result["producer_allocation_probes"]=json::array();')
    worker=once(worker,'need(resident_life && residents.size()==3,"admission requires three registered dense14b pools");',
      'need(!resident_life && family=="Llama","fresh Llama capacity probe required");')
    worker=fresh_fix(worker)
    worker=once(worker,'struct Pair {','#include "llama_probe.hpp"\nstruct Pair {')
    worker=once(worker,'hs_repair::configure(slot,root/id);','hs_repair::configure(slot,root/id);\n            hs_llama_probe::configure(slot,root/id);')
    worker=once(worker,'        target->decode(verify,base,true,"VERIFY");',
      '        hs_llama_probe::before(*target,t,verify,base,cycle,int(ids.size()));\n        target->decode(verify,base,true,"VERIFY");')
    anchor='        int accepted=0;bool rejected=false;std::string last;'
    worker=once(worker,anchor,'        hs_llama_probe::after(*target,cycle,k+1);\n'+anchor)
    worker=once(worker,'    r["service_seconds"]=since(start)-state_capture_seconds;',
      '    r["llama_diagnostic"]=hs_llama_probe::finish();\n    if(hs_llama_probe::opt.mode!="off")r["qualification_eligible"]=false;\n    r["service_seconds"]=since(start)-state_capture_seconds;')
    return worker

def stage(repo,snapshot,out,roles=0,extension=None):
    native,_,_=parent.load(snapshot);out=Path(out)
    native.stage(repo,out,roles,False) # Do NOT assume the Qwen head-norm fix repairs Llama.
    spec=importlib.util.spec_from_file_location('pr159_fresh_capture',Path(snapshot)/'diagnostics/fresh_capture.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    p=out/'worker.cpp';old=p.read_text();new=adapt(old,module.fix);p.write_text(new,encoding='utf-8',newline='\n')
    for name in ('llama_probe.hpp','cycle_contract.hpp'):shutil.copyfile(HERE/name,out/name)
    build=out/'build_native.py';s=build.read_text()
    s=once(s,'for name in ("repair_runtime.hpp", "repair_boundary.hpp", "repair_mm.hpp"):',
      'for name in ("repair_runtime.hpp", "repair_boundary.hpp", "repair_mm.hpp", "llama_probe.hpp", "cycle_contract.hpp"):')
    if extension:
        extension=Path(extension).resolve();need(extension.is_file(),'candidate extension missing')
        shutil.copyfile(extension,out/'candidate_extension.py')
        s=once(s,'        report["repair_spec"] = repair_spec',
          '        import candidate_extension\n        report["candidate_extension"] = candidate_extension.apply(source, code)\n        report["repair_spec"] = repair_spec')
    build.write_text(s,encoding='utf-8',newline='\n')
    save(out/'LLAMA_ADAPTATION.json',{'status':'STAGED_NOT_COMPILED_OR_NUMERICALLY_VALIDATED','base':BASE,
      'family':'Llama','source_variant':'metadata4','before_sha256':sha(old.encode()),'after_sha256':file_hash(p),
      'diagnostic_only_same_state_probes':True,'qwen_offload_fix_enabled':False,
      'rowwise_roles':roles,'extension_sha256':file_hash(extension) if extension else None,
      'files':{p.name:file_hash(p) for p in out.iterdir() if p.is_file()},'native_requests':0},exclusive=True)
    return out

def build(config):
    c=read(config);snap=Path(c['parent_snapshot'])
    if not snap.exists():parent.materialize(c['repo'],snap)
    staged=stage(c['repo'],snap,c['stage'],c.get('rowwise_roles',0),c.get('extension'))
    old=read(c['original_build_receipt']);ident=json.loads(git_read(c['repo'],HISTORY,DIAG+'EXECUTION_IDENTITY.json'))['families']['Llama']
    need(file_hash(c['source_archive'])==ident['source_zip_sha256'],'metadata4 source capsule mismatch')
    need(old['numerical_modules']==ident['numerical_modules'],'old build/DLL cohort mismatch')
    manifest=staged/'NUMERICAL_DLLS.json';save(manifest,{'numerical_DLL_sha256':ident['numerical_modules']},exclusive=True)
    cmd=[sys.executable,'-B',str(staged/'build_native.py'),'--variant','metadata4','--archive',c['source_archive'],
      '--out',c['out'],'--dll-manifest',str(manifest),'--dll-dir',c['dll_dir']]
    for key in ('zig','cmake','ninja'):cmd+=['--'+key,c.get(key) or old['tools'][key]['path']]
    cmd+=['--jobs',str(c.get('jobs',4)),'--command-timeout',str(c.get('build_timeout_seconds',7200))]
    save(staged/'BUILD_COMMAND.json',{'argv':cmd,'native_model_requests':0},exclusive=True);subprocess.run(cmd,check=True)
    # Bind all introduced headers and extension, not only worker.cpp/libllama.a.
    receipt=Path(c['out'])/'LLAMA_SOURCE_BINDING.json'
    save(receipt,{'source_variant':'metadata4','parent_commit':BASE,'stage_manifest_sha256':file_hash(staged/'LLAMA_ADAPTATION.json'),
      'stage':str(staged.resolve()),'files':{str(p.resolve()):file_hash(p) for p in staged.iterdir() if p.is_file()}},exclusive=True)
    return c['out']

if __name__=='__main__':
    import sys
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();print(build(a.config))
