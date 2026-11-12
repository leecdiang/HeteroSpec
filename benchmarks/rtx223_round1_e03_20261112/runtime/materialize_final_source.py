"""Reconstruct isolated final source from verified original core and compact delta."""
from pathlib import Path
import argparse,hashlib,json,os,shutil

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--old-core',required=True,type=Path);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--delta',type=Path,default=HERE/'delta-v2');args=parser.parse_args()
def normal_absolute(path,strict=False):
    resolved=path.resolve(strict=strict)
    text=str(resolved)
    if os.name=='nt':
        if text.startswith('\\\\?\\UNC\\'):text='\\\\'+text[8:]
        elif text.startswith('\\\\?\\'):text=text[4:]
    return Path(text)

def extended(path):
    # Only called after normal absolute paths pass the target-scope checks.
    if os.name!='nt':return path
    text=str(path)
    if text.startswith('\\\\?\\'):return path
    return Path('\\\\?\\UNC\\'+text[2:]) if text.startswith('\\\\') else Path('\\\\?\\'+text)

old=normal_absolute(args.old_core,strict=True);out=normal_absolute(args.out);delta=normal_absolute(args.delta,strict=True)
if out==old or out.is_relative_to(old):raise RuntimeError('fresh output outside old source required')
old_io,out_io,delta_io=map(extended,(old,out,delta))
if out_io.exists():raise RuntimeError('fresh output outside old source required')
origin=json.loads((delta_io/'ORIGIN_MANIFEST.json').read_bytes());mapping=json.loads((delta_io/'OVERRIDES.json').read_bytes())

def relative(name):
    path=Path(name)
    if not name or path.is_absolute() or path.drive or '..' in path.parts:raise RuntimeError('unsafe manifest member path')
    return path
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in origin['files'].items():
    p=old_io/relative(name)
    if not p.is_file() or digest(p)!=h:raise RuntimeError('original member differs: '+name)
for item in mapping['overrides']:
    p=delta_io/relative(item['delta_relative_path'])
    if not p.is_file() or digest(p)!=item['sha256']:raise RuntimeError('delta member differs')
out_io.mkdir(parents=True,exist_ok=False)
for name in origin['files']:
    member=relative(name);dest=out_io/member;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old_io/member,dest)
for item in mapping['overrides']:
    dest=out_io/relative(item['target_relative_path']);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(delta_io/relative(item['delta_relative_path']),dest)
final={**origin['files'],**{item['target_relative_path']:item['sha256'] for item in mapping['overrides']}}
if any(digest(out_io/relative(name))!=h for name,h in final.items()):raise RuntimeError('reconstruction verification failed')
print(json.dumps({'status':'SOURCE_RECONSTRUCTED_AND_HASHED','out':str(out),'files':len(final),'Windows_extended_paths':os.name=='nt','model_requests':0,'GPU_launches':0,'qualification':'NOT_RUN'}))
