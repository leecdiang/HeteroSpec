"""Copy only unchanged numerical build products into a fresh frontend epoch."""
from pathlib import Path
import argparse,shutil
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--from-build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--verify-existing',action='store_true');a=p.parse_args()
 if not a.verify_existing:a.out.mkdir()
 records=[]
 for role in('loop4','packed'):
  old=a.from_build/role;dest=a.out/role;binding=read(old/'CORE_BINDING.json');assert sha(old/'libllama.a')==binding['new_archive_sha256']
  for path,h in binding['compiled_graph_dependencies'].items():assert sha(path)==h
  if not a.verify_existing:
   dest.mkdir();shutil.copytree(old/'source',dest/'source')
   for name in('libllama.a','CORE_BINDING.json','llama-graph.cpp.o','graph.d'):shutil.copy2(old/name,dest/name)
  for name in('libllama.a','CORE_BINDING.json','llama-graph.cpp.o','graph.d'):assert sha(dest/name)==sha(old/name)
  source={str(p.relative_to(old/'source')):sha(p)for p in(old/'source').rglob('*')if p.is_file()}
  for name,h in source.items():assert sha(dest/'source'/name)==h
  records.append(dict(role=role,archive_sha256=sha(dest/'libllama.a'),original_core_binding_sha256=sha(old/'CORE_BINDING.json'),copied_source_files=len(source),numerical_source_or_object_modified=False))
 if not a.verify_existing:shutil.copy2(a.from_build/'CORES_COMPLETE.json',a.out/'CORES_COMPLETE.json')
 save(a.out/'SEEDED_CORE_PROVENANCE.json',dict(passed=True,mode='Retrospective exact identity verification after recorded copy'if a.verify_existing else'Fresh copy before frontend compile',records=records,original_compiled_dependency_closure_verified=True))
if __name__=='__main__':main()
