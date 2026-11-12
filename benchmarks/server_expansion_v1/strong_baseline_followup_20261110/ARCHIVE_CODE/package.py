"""Lossless text packaging for full F1 readback; no numeric/timing code changes.

Every logical file is in the strict archive index. Public transport consists of
ASCII base64 parts, so the unchanged final text-archive writer can retain them.
Admission follows full anonymous part readback AND full logical member replay.
"""
import argparse
import base64
import json
from pathlib import Path
import shutil
import sys
import time


def prepare(implementation,configuration,root,tree,output,archive):
    sys.path.insert(0,str(implementation))
    from archive import create,replay
    from freeze_cpu import PREFIX,public_text
    from host import utc
    from support import fresh,need,read,sha
    from terminal_guard import terminal_phase
    c=read(configuration)
    with terminal_phase(c,{'S1_PASSED_WAITING_F1_PUBLIC_READBACK'}):
        need(not output.exists() and not archive.exists(),'Fresh package only')
        output.mkdir(parents=True);started=time.monotonic()
        # Include the superseded failure, including full controller/native logs
        # and caller costs. Old paths, source, outputs and journal stay intact.
        manifest=read(c['manifest'])
        if manifest.get('continuation'):
            previous=read(manifest['continuation']['prior_configuration']);old=Path(previous['output_root'])
            with terminal_phase(previous,{'S1_STOPPED'}):
                selected=[old/'STATE.json',old/'R_ORACLE_CONTENT_FREEZE.json']
                selected+=sorted(old.glob('workers/*/HOST.json'))
                for path in old.glob('workers/*/HOST.json'):
                    if read(path)['status']!='COMPLETE':
                        selected += [path.parent/name for name in ('JOB.json','WORKER.json','stdout.log','stderr.log')]
                for name in ('s1.stdout.log','s1.stderr.log'):
                    p=old.parents[1]/'logs'/name
                    if p.is_file():selected.append(p)
                commitments=[]
                for path in selected:
                    relative=path.relative_to(old)if path.is_relative_to(old)else Path('controller')/path.name
                    target=tree/'F1_DATA/previous-epoch-01'/relative
                    need(not target.exists(),'Historical evidence must never be overwritten')
                    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(public_text(path.read_text(),root))
                    commitments.append(dict(path=str(relative),raw_sha256=sha(path),public_sha256=sha(target)))
                fresh(tree/'F1_DATA/previous-epoch-01/TRANSFORM_COMMITMENTS.json',commitments)
        selection=dict(schema='hs.strong.public-selection.v1',terminal_status='COMPLETE',
             files=[dict(path=p.relative_to(tree).as_posix(),sha256=sha(p),bytes=p.stat().st_size,
                         payload_kind='utf8-text',public_review='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS')
                    for p in sorted(tree.rglob('*'))if p.is_file()])
        result=create(tree,selection,archive)
        local=replay(archive,output.parent/(output.name+'-local-member-replay'),result['archive_sha256'])
        # These exact original metadata bytes are also directly published for
        # the unchanged F1 admit function. No statistical or native source moves.
        for name in ('QUALIFIED_BINDINGS.json','CALLER_CLASSES.json','REGISTRATION.json','S2_COMPLETE_WORKERS.json'):
            p=tree/'F1_DATA'/name;q=output/'F1_DATA'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
        source=Path(__file__);destination=output/'ARCHIVE_CODE/package.py';destination.parent.mkdir()
        need(public_text(source.read_text(),root)==source.read_text(),'Public source must remain byte-identical')
        destination.write_bytes(source.read_bytes())
        parts=[]
        with archive.open('rb')as stream:
            for i in range(10000):
                value=stream.read(384*1024)
                if not value:break
                name='F1_ARCHIVE/part-'+str(i).zfill(4)+'.b64';path=output/name;path.parent.mkdir(exist_ok=True)
                path.write_bytes(base64.b64encode(value)+b'\n')
                parts.append(dict(path=name,bytes=path.stat().st_size,sha256=sha(path),decoded_bytes=len(value)))
        fresh(output/'F1_ARCHIVE/PACKAGE.json',dict(schema='hs.strong.lossless-text-package.v1',
             original_logical_F1_index_sha256=sha(tree/'F1_INDEX.json'),
             complete_logical_files=selection['files'],ordered_parts=parts,archive=result,
             local_full_member_replay=local,registered_utc=utc(),prepare_caller_s=time.monotonic()-started,
             source_epoch='Offline packaging adapter only; original S1/S2 code, oracle, qualification and statistics unchanged',
             public_readback_required='Every published ASCII part byte plus decoded archive SHA and every logical member SHA/size'))
        files=[dict(path=p.relative_to(output).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
               for p in sorted(output.rglob('*'))if p.is_file()]
        fresh(output/'F1_INDEX.json',dict(schema='hs.strong.public-freeze-index.v1',prefix=PREFIX,files=files,
             logical_files_transport='Lossless indexed archive parts; full decoded member replay required before S2'))
        print(json.dumps(dict(status='PACKAGED_LOCAL_REPLAY_PASSED_REMOTE_READBACK_PENDING',
                             logical_files=len(selection['files']),published_files=len(files)+1,**result)))


def verify_members(implementation,cache,proof_path,output,report):
    sys.path.insert(0,str(implementation))
    from archive import replay
    from host import verify_public_readback
    from support import fresh,need,read,sha,write,safe_relative
    proof=read(proof_path);verify_public_readback(proof)
    need(proof.get('anonymous')is True,'Actual anonymous public transport proof required')
    need(proof['index_name']=='F1_INDEX.json','Actual F1 public readback required')
    need(not output.exists(),'Fresh restored member directory')
    package=read(cache/'F1_ARCHIVE/PACKAGE.json');archive=output.parent/(output.name+'.tar.gz')
    need(not archive.exists(),'Never overwrite a reconstructed archive')
    with archive.open('xb')as stream:
        for part in package['ordered_parts']:
            p=cache/safe_relative(part['path']);need(sha(p)==part['sha256']and p.stat().st_size==part['bytes'],'Public part differs')
            raw=base64.b64decode(p.read_bytes().strip(),validate=True)
            need(len(raw)==part['decoded_bytes'],'Decoded complete fragment length');stream.write(raw)
    need(sha(archive)==package['archive']['archive_sha256']and archive.stat().st_size==package['archive']['archive_bytes'],
         'Reassembled whole archive differs')
    result=replay(archive,output,package['archive']['archive_sha256'])
    need(result['files']==len(package['complete_logical_files']),'Complete logical archive file count differs')
    for item in package['complete_logical_files']:
        p=output/safe_relative(item['path'])
        need(sha(p)==item['sha256']and p.stat().st_size==item['bytes'],'Full logical file readback differs')
    result.update(status='COMPLETE_ANONYMOUS_PART_AND_LOGICAL_MEMBER_READBACK_PASSED',
                  immutable_commit=proof['commit'],logical_files=len(package['complete_logical_files']),
                  archive_sha256=sha(archive),source='Only actual downloaded immutable public part bytes')
    fresh(report,result)
    proof['complete_archive_member_readback']=dict(report=str(report),sha256=sha(report),**result)
    write(proof_path,proof)
    print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('prepare')
    for name in ('implementation','configuration','root','tree','out','archive'):a.add_argument('--'+name,type=Path,required=True)
    b=sub.add_parser('verify-members')
    for name in ('implementation','cache','proof','out','report'):b.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.implementation,a.configuration,a.root,a.tree,a.out,a.archive)
    else:verify_members(a.implementation,a.cache,a.proof,a.out,a.report)
