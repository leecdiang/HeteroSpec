"""Restore original member paths from downloaded object ZIPs, without GPU use."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def need(value,message):
    if not value:raise ValueError(message)

def safe(root, relative):
    need(isinstance(relative,str) and relative and '\\' not in relative and ':' not in relative,'unsafe archive path')
    p=Path(relative)
    need(not p.is_absolute() and '..' not in p.parts,'unsafe archive path')
    result=(root/p).resolve()
    need(result.is_relative_to(root.resolve()),'archive path escapes destination')
    return result

def restore(download, index, expected_index_sha, output):
    need(sha(index)==expected_index_sha,'index differs from committed digest')
    spec=json.loads(index.read_text(encoding='utf-8'))
    manifest_path=download/'completed-through-day0.OBJECT_MEMBERS.json'
    need(sha(manifest_path)==spec['members_manifest']['sha256'],'manifest hash differs')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    need(not output.exists(),'fresh output required; refusing overwrite')
    output.mkdir(parents=True);objects=output/'.objects';objects.mkdir()
    expected={x['sha256']:x for x in manifest['objects']};seen=set()
    for part in spec['parts']:
        archive=download/Path(part['path']).name
        need(archive.stat().st_size==part['bytes'] and sha(archive)==part['sha256'],'part hash differs')
        with zipfile.ZipFile(archive) as z:
            need(z.namelist()==['objects/'+h for h in part['objects']],'unexpected object inventory')
            for h in part['objects']:
                need(re.fullmatch('[0-9a-f]{64}',h) and h in expected and h not in seen,'invalid/duplicate object')
                target=objects/h
                with z.open('objects/'+h) as source,target.open('xb') as dest:shutil.copyfileobj(source,dest)
                need(target.stat().st_size==expected[h]['bytes'] and sha(target)==h,'object digest differs')
                seen.add(h)
    need(seen==set(expected),'incomplete downloaded object set')
    restored=set()
    for member in manifest['members']:
        relative=member['snapshot']+'/'+member['path'];target=safe(output,relative)
        need(relative not in restored and member['sha256'] in seen,'duplicate/missing member')
        target.parent.mkdir(parents=True,exist_ok=True)
        with (objects/member['sha256']).open('rb') as source,target.open('xb') as dest:shutil.copyfileobj(source,dest)
        need(target.stat().st_size==member['bytes'] and sha(target)==member['sha256'],'restored member differs')
        restored.add(relative)
    return {'status':'ALL_ORIGINAL_PATHS_RESTORED_AND_HASH_VERIFIED','members':len(restored),'objects':len(seen)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--download',type=Path,required=True);p.add_argument('--index',type=Path,required=True);p.add_argument('--index-sha256',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(restore(a.download.resolve(),a.index.resolve(),a.index_sha256,a.out.resolve()),indent=2))
