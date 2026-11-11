"""Bind an observer-only worker to byte-identical parent numerical libraries."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,sha,need
from host import code_identity

def bind(parent,helper,source,out):
    p=read(parent);h=read(helper);expected={Path(f['path']).name:f['sha256'] for f in p['files'] if Path(f['path']).suffix=='.dll'}
    actual={Path(f['path']).name:f['sha256'] for f in h['files'] if Path(f['path']).suffix=='.dll'}
    need(actual==expected,'observer changed numerical libraries')
    p.update(executable=h['executable'],files=h['files'],supervisor=h['supervisor'],supervisor_sha256=h['supervisor_sha256'],authoring_files=code_identity(),parent_build_sha256=sha(parent),observer_helper_sha256=sha(helper),observer_source_receipt_sha256=sha(source),numerical_libraries_unchanged=True)
    write(out,p)

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for k in ('parent','helper','source','out'):a.add_argument('--'+k,required=True)
    p=a.parse_args();bind(p.parent,p.helper,p.source,p.out)
