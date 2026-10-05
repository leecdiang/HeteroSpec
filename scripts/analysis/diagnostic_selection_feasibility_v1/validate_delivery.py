"""CPU-only roundtrip, immutable source and additive delivery checks."""
import datetime,subprocess,sys
from audit import ROOT,DOC,load,save,sha,PIN

def main():
    source=load(DOC/'SOURCE_BINDINGS.json');assert len(source['files'])==48
    for e in source['files']:
        b=subprocess.check_output(['git','show',PIN+':'+e['path']],cwd=ROOT)
        assert len(b)==e['bytes'] and sha(b)==e['sha256'],e['path']
    names=['RECOMPUTED.json','TASK_ACTIONS.csv'];before={n:(DOC/n).read_bytes() for n in names}
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/analysis/diagnostic_selection_feasibility_v1/audit.py'),'--from-inputs'],cwd=ROOT,check=True)
    assert all((DOC/n).read_bytes()==b for n,b in before.items()),'compact/source modes differ'
    assert load(DOC/'TEST_RESULTS.json')['status']=='PASS' and load(DOC/'TEST_RESULTS.json')['tests_run']==10
    allowed=('benchmarks/diagnostic_selection_feasibility_v1/','scripts/analysis/diagnostic_selection_feasibility_v1/')
    staged=subprocess.check_output(['git','diff','--cached','--name-status',PIN],cwd=ROOT,text=True).splitlines()
    assert all(x.startswith('A\t') and x.split('\t')[1].startswith(allowed) for x in staged),'inherited index tree altered'
    script_root=ROOT/'scripts/analysis/diagnostic_selection_feasibility_v1'
    for directory in (DOC,script_root):
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                b=p.read_bytes();p.write_bytes(b.replace(b'\r\n',b'\n'))
    receipt={'status':'PASS','source_commit':PIN,'pinned_source_files_byte_checked':48,
             'source_and_compact_input_tables_byte_equal':names,'meaningful_tests':10,'policy_revisions':{'P1':0,'P2':0},
             'new_inference_runs':0,'gpu_forwards':0,'decision':'NO_GO_NEW_METHOD',
             'staged_tree_relative_to_pin':'Authorized additions only; inherited entries preserved',
             'scope':'CPU checks and content preservation, not independent authentication of prior machine execution.'}
    save(DOC/'DELIVERY_VALIDATION.json',receipt)
    manifest_path=DOC/'ARTIFACT_MANIFEST.json'
    entries=[]
    for directory in (DOC,script_root):
        for p in sorted(directory.rglob('*')):
            if p.is_file() and p!=manifest_path and '__pycache__' not in p.parts:
                b=p.read_bytes();entries.append({'path':p.relative_to(ROOT).as_posix(),'bytes':len(b),'sha256':sha(b)})
    save(manifest_path,{'self_excluded':manifest_path.relative_to(ROOT).as_posix(),'source_commit':PIN,'files':entries,'no_inherited_archive_duplicated':True})
    print('PASS delivery:',len(entries),'new inventory files; source/input byte roundtrip,48 source identities and10 tests')

if __name__=='__main__':main()
