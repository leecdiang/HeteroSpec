"""Lossless CPU fixture roundtrip and malformed archive rejections."""
import hashlib,json,zipfile
from pathlib import Path
from common import V,save
from evidence import ESSENTIAL,package,restore

def main():
    d=V/'cpu_tests/evidence_final';d.mkdir(parents=True,exist_ok=False);root=d/'raw';root.mkdir();(root/'retained-failure').write_bytes(b'CPU_FIXTURE_FAILED_AND_UNSTARTED\x00')
    frozen=d/'fixture-frozen';frozen.mkdir()
    for n in ESSENTIAL:(frozen/n).write_bytes(b'CPU_FIXTURE_NOT_GPU_AUTHORIZED')
    archive=d/'CPU.zip';p=package(root,archive,frozen);r=restore(archive,d/'fresh')
    assert (d/'fresh/raw/retained-failure').read_bytes()==(root/'retained-failure').read_bytes()
    cases=[]
    for label,name,digest in [('traversal','../escape','a'*64),('hash','raw/retained','0'*64),('absolute','D:/escape','a'*64),('duplicate','raw/a',hashlib.sha256(b'x').hexdigest())]:
        zpath=d/(label+'.zip')
        with zipfile.ZipFile(zpath,'x') as z:
            z.writestr(name,b'x')
            if label=='duplicate':z.writestr(name,b'x')
            z.writestr('MANIFEST.json',json.dumps({name:dict(bytes=1,sha256=digest)}))
        rejected=False
        try:restore(zpath,d/(label+'_retained'))
        except AssertionError:rejected=True
        assert rejected;cases.append(label)
    save(V/'CPU_EVIDENCE_TESTS_final.json',dict(status='PASS',actual_CPU_package=p,actual_fresh_restore=r,negative_archive_rejections=cases,old_archive_copies_created=0,new_GPU_activity=0))
    print('PASS lossless CPU package/restore and4 actual malformed archive rejections')
if __name__=='__main__':main()
