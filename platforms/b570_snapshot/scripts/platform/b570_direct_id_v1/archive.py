"""Create a portable, content-addressed direct-ID evidence archive."""
import argparse,hashlib,json,shutil,subprocess,sys,tarfile
from pathlib import Path

def hashfile(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--r0',type=Path,required=True)
    a=ap.parse_args();repo=Path.cwd();protocol=repo/'benchmarks/b570_direct_id_v1';root=a.root.resolve()
    validation=protocol/'INDEPENDENT_VALIDATION.json'
    subprocess.run([sys.executable,str(repo/'scripts/platform/b570_direct_id_v1/verify.py'),
        '--root',str(root),'--protocol',str(protocol/'protocol_v1.json'),'--analysis',str(protocol/'FORMAL_ANALYSIS.json'),'--output',str(validation)],check=True)
    stage=repo/'work/b570_direct_id_v1/bundle'
    if stage.exists():raise RuntimeError('Bundle staging directory already exists; preserve previous archive attempts')
    stage.mkdir(parents=True)
    result=json.loads((protocol/'FORMAL_ANALYSIS.json').read_text(encoding='utf-8'))
    closed='# B570 direct-ID replication v1 closeout\n\n'
    closed+='The new direct-ID study is complete. Historical B570 results remain unchanged.\n\n'
    for c,x in result['paths'].items():closed+=f"- {c}: {x['qualification']}; {x['exact_pairs']}/90 pairs; {x['wholly_exact_prompts']}/30 prompts.\n"
    closed+='\nIndependent validator: PASS. Executions: 270/270. The content-addressed archive hash is recorded in artifacts/b570_direct_id_v1/ARCHIVE.json.\n\n'
    closed+='Parameter changes after formal start: NO. Manuscript/figure edits: NO. Energy study: NO. Result-driven search: NO. No further B570 experiments are scheduled. Integration requires joint review with the independent RTX arm.\n'
    (protocol/'CLOSEOUT.md').write_text(closed,encoding='utf-8')
    shutil.copytree(root,stage/'formal');shutil.copytree(a.r0,stage/'R0')
    shutil.copytree(protocol,stage/'protocol')
    shutil.copytree(repo/'scripts/platform/b570_direct_id_v1',stage/'runner',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copy2(repo/'work/b570_direct_id_v1/build.log',stage/'build.log')
    # R0 commands have machine-local paths. Preserve bytes as observational raw evidence,
    # but the new formal command records and publication manifests are portable.
    entries=[]
    for p in sorted(stage.rglob('*')):
        if p.is_file():entries.append({'path':p.relative_to(stage).as_posix(),'size':p.stat().st_size,'sha256':hashfile(p)})
    manifest={'schema':'heterospec.b570.direct_id.bundle.v1','files':entries,
      'upstream_commit':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2','starting_main':'483c4cbd6cd72ae1cdcdbba4534a62fc1786f885',
      'exclusions':['model weights','runtime binaries','historical B570 archives','energy telemetry'],'classification':'New direct-ID replication; R0 excluded from formal inference'}
    (stage/'SHA256_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    subprocess.run([sys.executable,str(stage/'runner/verify.py'),'--root',str(stage/'formal'),
        '--protocol',str(stage/'protocol/protocol_v1.json'),'--analysis',str(stage/'protocol/FORMAL_ANALYSIS.json'),
        '--manifest',str(stage/'SHA256_MANIFEST.json')],check=True)
    out=repo/'artifacts/b570_direct_id_v1';out.mkdir(parents=True,exist_ok=True)
    temp=out/'b570_direct_id_v1_evidence.tar.gz'
    with tarfile.open(temp,'w:gz') as tf:tf.add(stage,arcname='b570_direct_id_v1')
    digest=hashfile(temp);dest=out/(digest+'.tar.gz');temp.rename(dest)
    metadata={'schema':'heterospec.b570.direct_id.content_addressed_archive.v1','archive':dest.name,
       'archive_sha256':digest,'size':dest.stat().st_size,'payload_files':len(entries),
       'verification':'PASS','verifier':'scripts/platform/b570_direct_id_v1/verify.py',
       'instructions':'Extract archive; run: python b570_direct_id_v1/runner/verify.py --root b570_direct_id_v1/formal --protocol b570_direct_id_v1/protocol/protocol_v1.json --analysis b570_direct_id_v1/protocol/FORMAL_ANALYSIS.json --manifest b570_direct_id_v1/SHA256_MANIFEST.json'}
    (out/'ARCHIVE.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(stage/'SHA256_MANIFEST.json',out/'SHA256_MANIFEST.json')
    print(json.dumps(metadata,indent=2))

if __name__=='__main__':main()
