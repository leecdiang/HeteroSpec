"""Export retained CPU-only preparation versions/failures, never native payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main(study_root,namespace,implementation,out):
    sys.path.insert(0,str(implementation/'execution_s3_v1'))
    sys.path.append(str(implementation/'execution_v1'))
    from public_text import transform
    import archive
    if out.exists():raise ValueError('Fresh CPU history directory required')
    out.mkdir(parents=True);inventory=[];withheld=[];sources=[]
    roots=sorted(p for p in namespace.iterdir()if p.is_dir()and p.name.startswith(('sb217-b2-','sb217-s3-source-','sb217-s3-cpu-')))
    prefixes=('CPU_','PREPAR','REUSE','RECOMPUTED','EXECUTOR_CPU','SCHEDULING_ADAPTER','NATIVE_GUARD_ADAPTER','HARDWARE_DRIVER_BINDING')
    for root in roots:
        sources.append(root.name)
        for path in sorted(root.rglob('*')):
            if not path.is_file()or path.is_symlink()or '__pycache__'in path.parts:continue
            rel=path.relative_to(root);parts=rel.parts
            code=(parts[0]=='source'or parts[0].startswith('final-source-'))and path.suffix in ('.py','.md','.c','.cpp','.h','.hpp')
            receipt=(len(parts)==1 or(len(parts)==2 and parts[0]=='prepared'))and path.name.startswith(prefixes)
            model=rel==Path('model/BUILD.json')
            if not(code or receipt or model):continue
            raw=path.read_bytes();item=dict(path=root.name+'/'+str(rel),original_sha256=hashlib.sha256(raw).hexdigest(),original_bytes=len(raw))
            try:value=transform(raw.decode('utf8'),study_root)
            except (UnicodeDecodeError,ValueError)as error:
                withheld.append(dict(item,publicly_available=False,reason=str(error),original_retained_private=True));continue
            target=out/item['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_text(value)
            inventory.append(dict(item,public_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),public_bytes=target.stat().st_size))
    note=dict(status='CPU_PREPARATION_HISTORY_RETAINED',native_GPU_requests_in_this_export=0,source_work_epochs=sources,
        files=inventory,withheld=withheld,
        limitations=['Earliest B2 source01 direct unittest failure stdout/stderr was returned through the tool rather than saved to a server file; source retained, no GPU execution',
                     'CPU caller times are reported where recorded; missing early manual preparation timings are unavailable, never filled with zero',
                     'This is CPU preparation history; current S3 native work and formal timing are excluded, not interrupted'],
        known_zero_GPU_fixes=['B2 total1728 versus candidate352 capture inventory distinction',
             'B2 KV profile36 target layers rather than32', 'B2 archive-test path and expected exception adapters',
             'S3 synthetic private-address literal rejected by publication privacy fixture; original source retained',
             'S3 actual NVML memory.free gate corrected and refrozen before first S3 request'])
    (out/'CPU_HISTORY.json').write_text(json.dumps(note,indent=2)+'\n')
    selection=dict(schema='hs.strong.public-selection.v1',terminal_status='COMPLETE',files=[],private_literals=[str(study_root),str(Path.home())])
    for path in out.rglob('*'):
        if path.is_file():selection['files'].append(dict(path=str(path.relative_to(out)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
             bytes=path.stat().st_size,payload_kind='utf8-text',public_review='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS'))
    result=archive.create(out,selection,out.parent/(out.name+'.tar.gz'))
    local=archive.replay(out.parent/(out.name+'.tar.gz'),out.parent/(out.name+'-LOCAL-REPLAY'),result['archive_sha256'])
    report=dict(archive=result,local_replay=local,files=len(inventory),withheld=len(withheld),source_epochs=len(sources))
    (out.parent/(out.name+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('study-root','namespace','implementation','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();main(a.study_root,a.namespace,a.implementation,a.out)
