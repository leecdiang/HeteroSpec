"""Preserve superseded CPU-only candidate and bind complete resource sampling."""
import datetime
from common import V,load,save,pin,sha

def main():
    # The first authenticated CPU candidate is preserved as an engineering record,
    # including its already-pushed archive. No GPU authorization ever existed.
    source=(V/'publish_cpu.py').read_text()
    source=source.replace('delivery/raw','delivery/cpu-final').replace('cpu_raw/publication','cpu_raw/publication_final').replace('hs116-s1b-exact-r2-cpu-fresh','hs116-s1b-exact-r2-cpu-final-fresh')
    source=source.replace("if folder=='cpu_raw' and 'publication' in p.relative_to(V/folder).parts:continue","if folder=='cpu_raw' and any(x in p.relative_to(V/folder).parts for x in ['publication','publication_final']):continue")
    q=V/'publish_cpu_final.py';assert not q.exists();q.write_text(source,encoding='utf-8')
    d=V/'preparation_candidates/resource_guard_revision';d.mkdir(exist_ok=False)
    f=load(V/'F0.json')
    for name in ['F0.json','AUTHENTICATED_F0.json','REMOTE_F0_BYTES.json','CENSUS_EXACT_AUTHENTICATED.json','REMOTE_ARCHIVE_VERIFIED.json','CPU_CAPSULE_PACKAGED.json','FRESH_CPU_AUDIT.json']:
        (V/name).rename(d/name)
    f.update(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),repair_source_parent_commit='5e2f2ab618b56a54be0767dc2b6ccecb56fcd7a2',superseded_CPU_candidate=pin(d/'F0.json'),superseded_CPU_remote_verification=pin(d/'REMOTE_ARCHIVE_VERIFIED.json'))
    f['monitor_contract']['qualified_sample']='Actual private/Job memory + directly completed controller/disk resource checks + log/process errors + deadline guard; monotonic timestamp after checks;exact journal fsync. No stale resource-thread status substituted.'
    f['CPU_tests']['CPU_RESOURCE_GUARD_TESTS.json']=pin(V/'CPU_RESOURCE_GUARD_TESTS.json')
    files={r['path']:r for r in f['files']}
    for p in list(V.iterdir())+list(d.iterdir()):
        if p.is_file() and p.suffix in {'.py','.h','.cpp','.exe','.json','.md'} and p.name!='F0.json':files[str(p)]=pin(p)
    files[str(d/'F0.json')]=pin(d/'F0.json')
    f['files']=sorted(files.values(),key=lambda r:r['path'])
    f['source_roles']={p.name:sha(p) for p in V.iterdir() if p.suffix in {'.py','.h','.cpp'}}
    save(V/'F0.json',f)
    print('FINAL complete-resource F0',sha(V/'F0.json'),'canonical/execution stable,old candidate preserved,GPU0')
if __name__=='__main__':main()
