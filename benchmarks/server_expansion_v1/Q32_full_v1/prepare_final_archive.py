"""Privacy-only AST fix; preserve literal source regexes in the public record."""
from pathlib import Path
import argparse,ast,shutil
from build import sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir();shutil.copy2(a.source/'build.py',a.out/'build.py');source=a.source/'archive.py';tree=ast.parse(source.read_text());changes=[]
 for n in ast.walk(tree):
  if not isinstance(n,ast.Constant)or not isinstance(n.value,str):continue
  if n.value.startswith('/home/[^/'):
   changes.append(dict(old=n.value,new='/home/[A-Za-z0-9_.-]+'));n.value='/home/[A-Za-z0-9_.-]+'
  elif n.value=='export-06':changes.append(dict(old=n.value,new='export-07'));n.value='export-07'
 assert len(changes)==2,changes;code=ast.unparse(ast.fix_missing_locations(tree))+'\n';ast.parse(code);(a.out/'archive.py').write_text(code)
 shutil.copy2(Path(__file__).parent/'replace_archive_waiter.py',a.out/'replace_waiter.py')
 save(a.out/'ADAPTER_BINDING.json',dict(original_archive_sha256=sha(source),new_archive_sha256=sha(a.out/'archive.py'),AST_constant_changes=changes,scope='Privacy-only: redact actual username characters, preserve literal regex syntax and unchanged final fail-closed assertion; fresh export07, no native/qualification change'))
if __name__=='__main__':main()
