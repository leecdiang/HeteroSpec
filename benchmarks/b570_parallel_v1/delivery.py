"""Reuse the authenticated, byte-verified PR165 archive format under a new release tag."""
from paths import *
import shutil,importlib.util
PACK=ROOT.parent/'b570-parallel-evidence-v1'
REMOTE=ROOT.parent/'b570-parallel-readback-v1'
TAG='b570-reference-parallel-v1-evidence-20261103'
def make():
    repo=ROOT/'repro';repo.mkdir(exist_ok=True)
    known={'object_archive.py':'0728aba717ec92da7a669893469d3ccff21e9b9674c7aca379236e4a2c156163','recover_release.py':'40c2b79bf8c165dce368f8703d0f89ea5e2442d9f9af998144a8614e321d9bbe','publish_delivery.py':'1747d64270dfa22057c8e6831b3e2431f2e434105b750e234e61a852e1f9df15'}
    for name,h in known.items():
        p=PR165/'repro'/name;assert sha(p)==h
        s=p.read_text(encoding='utf-8')
        if name=='object_archive.py':
            s=once(s,'b570-qwen-transfer-native-evidence','b570-parallel-native-evidence')
        if name=='publish_delivery.py':
            s=s.replace('B570 Qwen structural transfer evidence','B570 physical-prefix parallelism evidence').replace('B570 PR165','B570 PR169')
            s=once(s,"'recompute.py','README.md'","'recompute.py','verify_raw.py','contrast.py','README.md'")
        (repo/name).write_text(s,encoding='utf-8',newline='\n')
    # Every native unit, checkpoint, vector, failure and log remains under its
    # original relative path. We exclude only regenerable intermediate builds.
    for p in HERE.iterdir():
        if p.is_file():shutil.copyfile(p,repo/p.name)
    sys.path.insert(0,str(repo))
    import object_archive
    assert (ROOT/'NATURAL_COST.json').is_file() and (ROOT/'FREEZE.json').is_file()
    object_archive.pack(ROOT,PACK)
    for name in ('object_archive.py','recompute.py','contrast.py','verify_raw.py','README.md'):shutil.copyfile(repo/name,PACK/name)
    object_archive.verify(PACK)
def publish(commit):
    sys.path.insert(0,str(ROOT/'repro'))
    import publish_delivery
    publish_delivery.run(PACK,REMOTE,TAG,commit)
if __name__=='__main__':
    if sys.argv[1]=='pack':make()
    elif sys.argv[1]=='publish':publish(sys.argv[2])
