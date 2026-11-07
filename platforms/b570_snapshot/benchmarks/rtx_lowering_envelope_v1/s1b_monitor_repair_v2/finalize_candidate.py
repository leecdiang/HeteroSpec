"""Finalize unapproved CPU candidate after delivery dependency audit; preserve first candidate."""
import datetime
from common import V,load,save,sha,pin

def main():
    old=V/'F0.json';f=load(old);d=V/'preparation_candidates';d.mkdir(exist_ok=False)
    old.rename(d/'F0-first-CPU-candidate.json')
    f['preparation_candidate_history']=pin(d/'F0-first-CPU-candidate.json')
    f['recorded_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    files={r['path']:r for r in f['files']}
    for p in V.iterdir():
        if p.is_file() and p.suffix in {'.py','.h','.cpp','.exe','.json','.md'} and p.name!='F0.json':files[str(p)]=pin(p)
    files[str(d/'F0-first-CPU-candidate.json')]=pin(d/'F0-first-CPU-candidate.json')
    f['files']=sorted(files.values(),key=lambda r:r['path'])
    f['source_roles']={p.name:sha(p) for p in V.iterdir() if p.suffix in {'.py','.h','.cpp'}}
    f['CPU_tests']['CPU_POST_FREEZE_TESTS.json']=pin(V/'CPU_POST_FREEZE_TESTS.json')
    save(old,f);print('FINAL CPU F0',sha(old),'candidate retained;GPU0')
if __name__=='__main__':main()
