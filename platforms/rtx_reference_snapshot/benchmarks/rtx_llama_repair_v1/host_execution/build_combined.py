"""Bind one combined structural policy to each family's original source capsule."""
import argparse
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    import json
    c=json.loads(a.config.read_text())
    sys.path.insert(0,str(Path(c['repo'])/'scripts/experiments/rtx_llama_repair_v1'))
    from lr_common import read,save,file_hash,need,once,STUDY
    import parent,native_stage
    snapshot=Path(c['parent_snapshot']);native,_,_=parent.load(snapshot)
    stage=Path(c['stage']);native.stage(c['repo'],stage,0,True)
    worker=stage/'worker.cpp';before=worker.read_text()
    if c['family']=='Llama':
        spec=importlib.util.spec_from_file_location('fresh_capture',snapshot/'diagnostics/fresh_capture.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        worker.write_text(native_stage.adapt(before,module.fix),encoding='utf-8',newline='\n')
        for name in ('llama_probe.hpp','cycle_contract.hpp'):
            shutil.copyfile(Path(c['repo'])/'scripts/experiments/rtx_llama_repair_v1'/name,stage/name)
    else:
        need(c['family']=='Qwen','registered family')
        worker.write_text(once(before,'slot.at("study_id")=="rtx_reference_repair_v1"','slot.at("study_id")=="'+STUDY+'"'),encoding='utf-8',newline='\n')
    extension=Path(__file__).with_name('prefix_extent.py')
    shutil.copyfile(extension,stage/'prefix_extent.py')
    (stage/'candidate_extension.py').write_text('import prefix_extent\ndef apply(source,code):\n    r=prefix_extent.apply(source,code)\n    r["qwen_norm_offload_fix"]=True\n    r["policy"]= "Physical prefix extent grouping plus pinned PR159 head-norm offload preference"\n    return r\n')
    builder=stage/'build_native.py';text=builder.read_text()
    if c['family']=='Llama':
        text=once(text,'for name in ("repair_runtime.hpp", "repair_boundary.hpp", "repair_mm.hpp"):',
                  'for name in ("repair_runtime.hpp", "repair_boundary.hpp", "repair_mm.hpp", "llama_probe.hpp", "cycle_contract.hpp"):')
    text=once(text,'        report["repair_spec"] = repair_spec',
              '        import candidate_extension\n        report["candidate_extension"] = candidate_extension.apply(source, code)\n        report["repair_spec"] = repair_spec')
    builder.write_text(text,encoding='utf-8',newline='\n')
    old=read(c['original_build_receipt'])
    need(file_hash(c['source_archive'])==old['source_zip_sha256'],'original source capsule')
    manifest=stage/'NUMERICAL_DLLS.json';save(manifest,{'numerical_DLL_sha256':old['numerical_modules']},exclusive=True)
    save(stage/'COMBINED_ADAPTATION.json',{'family':c['family'],'source_variant':c['variant'],
        'parent_commit':parent.BASE if hasattr(parent,'BASE') else '38b3d3d3929dc958e6a2a7e0bdc8abd61ff38ab1',
        'prefix_source_sha256':file_hash(extension),'worker_sha256':file_hash(worker),'native_requests':0,
        'policy':'Causal physical prefix extent; retain independently established head-norm offload preference'},exclusive=True)
    cmd=[sys.executable,'-B',str(builder),'--variant',c['variant'],'--archive',c['source_archive'],
         '--out',c['out'],'--dll-manifest',str(manifest),'--dll-dir',c['dll_dir']]
    for tool in ('zig','cmake','ninja'):cmd+=['--'+tool,old['tools'][tool]['path']]
    cmd+=['--jobs','4','--command-timeout','7200']
    save(stage/'BUILD_COMMAND.json',{'argv':cmd,'model_requests':0},exclusive=True)
    subprocess.run(cmd,check=True)
    save(Path(c['out'])/'LLAMA_SOURCE_BINDING.json',{'source_variant':c['variant'],'family':c['family'],
        'stage':str(stage.resolve()),'files':{str(p.resolve()):file_hash(p) for p in stage.iterdir() if p.is_file()}},exclusive=True)
    print(c['out'])


if __name__=='__main__':main()
