"""Authenticate all ordered parts, merged archive, and the extracted offline inventory."""
import argparse,hashlib,json,subprocess,sys,tarfile
from pathlib import Path

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(index,output):
    index=Path(index).resolve();output=Path(output).resolve();m=json.loads(index.read_text(encoding='utf-8'))
    assert m['schema']=='RTX_H2_V2.multipart' and m['parts'],'unsupported parts manifest'
    output.mkdir(parents=True,exist_ok=False);merged=output/'complete.tar.gz';total=0;checked=[]
    with merged.open('xb') as dest:
        for ordinal,row in enumerate(m['parts'],1):
            assert row['ordinal']==ordinal and Path(row['name']).name==row['name'],'invalid part order/name'
            path=index.parent/row['name'];assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'part hash/length mismatch'
            with path.open('rb') as src:
                while chunk:=src.read(1024*1024):dest.write(chunk)
            total+=row['bytes'];checked.append(row['name'])
    assert total==m['bytes'] and sha(merged)==m['sha256'],'complete concatenation hash/length mismatch'
    evidence=output/'evidence';evidence.mkdir()
    with tarfile.open(merged) as archive:archive.extractall(evidence,filter='data')
    entry=evidence/'frozen_source/scripts/platform/rtx_independent_proposal_replay_v2/offline.py'
    p=subprocess.run([sys.executable,'-B',str(entry),str(evidence)],capture_output=True,check=False)
    (output/'offline.stdout.log').write_bytes(p.stdout);(output/'offline.stderr.log').write_bytes(p.stderr)
    assert p.returncode==0,p.stderr.decode('utf-8',errors='replace')
    result={'status':'PASS','verified_parts':checked,'archive_sha256':m['sha256'],'merged_bytes':total,'fresh_directory':True,'bytecode_disabled':True,'independent_offline_result':json.loads(p.stdout)}
    (output/'RECONSTRUCTION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('index',type=Path);p.add_argument('output',type=Path);a=p.parse_args();main(a.index,a.output)
