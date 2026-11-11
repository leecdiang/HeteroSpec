"""Packaged portable CPU8 raw reconstruction. Never loads native or GPU modules."""
import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);p.add_argument('--manifest',required=True);p.add_argument('--tool-binding',required=True);p.add_argument('--output',required=True)
a=p.parse_args();root=Path(a.root).resolve();out=Path(a.output).resolve()
if out==root or root in out.parents:raise ValueError('recomputation output must be outside sealed root')
from verify_cpu8 import audit
data=(json.dumps(audit(root,a.run,a.manifest,a.tool_binding,relocated=True,mode="reconstruct"),sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
with out.open('xb') as f:f.write(data)
sys.stdout.buffer.write(data);sys.stdout.buffer.flush()
