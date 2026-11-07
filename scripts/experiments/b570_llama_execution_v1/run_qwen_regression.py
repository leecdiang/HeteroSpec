"""Complete all four historical Qwen inputs after same-build admission."""
from pathlib import Path
import sys
from qwen_host import run
build,repo,root,out=map(Path,sys.argv[1:]);out=out.resolve()
if not (out/'admission').exists():run(build,repo,root,out/'admission','admit',0)
for i in range(4):run(build,repo,root,out/f'input-{i}','qual',i)
