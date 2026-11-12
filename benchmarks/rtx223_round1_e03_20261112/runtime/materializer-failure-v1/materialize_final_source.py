"""Reconstruct isolated final source from verified original core and compact delta."""
from pathlib import Path
import argparse,hashlib,json,shutil

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--old-core',required=True,type=Path);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--delta',type=Path,default=HERE/'delta');args=parser.parse_args()
old=args.old_core.resolve(strict=True);out=args.out.resolve();delta=args.delta.resolve(strict=True)
if out.exists() or out==old or out.is_relative_to(old):raise RuntimeError('fresh output outside old source required')
origin=json.loads((delta/'ORIGIN_MANIFEST.json').read_bytes());mapping=json.loads((delta/'OVERRIDES.json').read_bytes())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in origin['files'].items():
    p=old/name
    if not p.is_file() or digest(p)!=h:raise RuntimeError('original member differs: '+name)
for item in mapping['overrides']:
    p=delta/item['delta_relative_path']
    if not p.is_file() or digest(p)!=item['sha256']:raise RuntimeError('delta member differs')
out.mkdir(parents=True,exist_ok=False)
for name in origin['files']:
    dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/name,dest)
for item in mapping['overrides']:
    dest=out/item['target_relative_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(delta/item['delta_relative_path'],dest)
final={**origin['files'],**{item['target_relative_path']:item['sha256'] for item in mapping['overrides']}}
if any(digest(out/name)!=h for name,h in final.items()):raise RuntimeError('reconstruction verification failed')
print(json.dumps({'status':'SOURCE_RECONSTRUCTED_AND_HASHED','out':str(out),'files':len(final),'model_requests':0,'GPU_launches':0,'qualification':'NOT_RUN'}))
