"""Stage and invoke the inherited authenticated Windows build. Does not run a model."""
import argparse
from pathlib import Path
import subprocess
import sys
from common import need,read,save,file_hash
from native import stage

def build(config):
    c=read(config);out=Path(c['out']);staged=out.parent/(out.name+'_source_adapter')
    stage(c['repo'],staged,c.get('rowwise_roles',0),c.get('stable_norm_offload',False))
    old=read(c['parent_build']);manifest=staged/'NUMERICAL_DLLS.json'
    save(manifest,{'numerical_DLL_sha256':old['numerical_modules']},exclusive=True)
    cmd=[sys.executable,'-B',str(staged/'build_native.py'),'--variant','original',
         '--archive',c['source_archive'],'--out',str(out),'--dll-manifest',str(manifest),'--dll-dir',c['dll_dir']]
    for n in ('zig','cmake','ninja'):cmd+=['--'+n,c.get(n,old['tools'][n]['path'])]
    cmd+=['--jobs',str(c.get('jobs',4)),'--command-timeout',str(c.get('command_timeout',3600))]
    subprocess.run(cmd,check=True)
    result=read(out/'BUILD.json');need(result['status']=='BUILT_NOT_QUALIFIED','build did not complete')
    return {'build':str(out/'BUILD.json'),'worker':str(out/'bin/rtx-scope-transfer.exe'),
            'sha256':result['executable_sha256'],'status':'BUILT_NOT_NATIVE_QUALIFIED'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
    a=p.parse_args();print(build(a.config))
