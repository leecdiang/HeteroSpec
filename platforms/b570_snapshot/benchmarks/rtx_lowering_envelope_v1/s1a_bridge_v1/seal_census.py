"""CPU-only seal of an actually ended Bridge census; not an author approval."""
import shutil,zipfile
from pathlib import Path
from common import V,load,save,sha
import analyzer as A

def main():
    f0=load(V/'F0.json');p=load(V/'PLAN.json');root=Path(f0['execution_root']);d=root/'census';n=d/'native'
    assert load(root/'CENSUS_ENDED.json')['status']=='COMPLETE'
    r=load(n/'CENSUS.json');assert r['pid']==A.process_identity(d,'native',f0,240)[0]
    A.process_identity(d,'readiness',f0);A.verify_modules(n,r,f0,load(d/'MODULE_FILES.json'))
    expected={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_GRAPH_EXPECTED.json')}
    decision=A.census_decision(r,expected,p);assert decision==load(root/'CENSUS_DECISION.json')
    out=V/'census_delivery';out.mkdir(exist_ok=False)
    shutil.copyfile(n/'CENSUS.json',out/'CENSUS.json');shutil.copyfile(root/'CENSUS_DECISION.json',out/'DECISION.json')
    files=[x for x in d.rglob('*') if x.is_file()]+[x for x in root.iterdir() if x.is_file()]
    manifest={x.relative_to(root).as_posix():dict(bytes=x.stat().st_size,sha256=sha(x)) for x in files}
    with zipfile.ZipFile(out/'RECEIPTS.zip','x',zipfile.ZIP_DEFLATED) as z:
        for x in files:z.write(x,x.relative_to(root).as_posix())
    save(out/'MANIFEST.json',dict(F0_sha256=sha(V/'F0.json'),census_sha256=sha(out/'CENSUS.json'),decision_sha256=sha(out/'DECISION.json'),files=manifest,
        graph_computes=0,numerical_authorization=False,numerical_technical_condition=decision['numerical_admitted'],immutable_CAS='Selected complete reference blobs remain registered by F0 and will appear in whole raw archive; no duplicate old experiment archive'))
    print('Census CPU seal complete. Commit/push/authenticate exact census+decision; wait for separate numerical approval.')
if __name__=='__main__':main()
