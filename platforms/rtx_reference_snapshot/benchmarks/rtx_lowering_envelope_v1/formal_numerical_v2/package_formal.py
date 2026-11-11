"""Future complete scientific raw packaging and fresh CPU reconstruction only."""
import argparse,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath
from common import V,load,save,sha
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--fresh-restore',type=Path);a=ap.parse_args();f0=load(V/'F0.json');root=Path(f0['execution_root']);s=f0['budget']['storage']
    out=V/'formal_delivery'
    if not a.fresh_restore:
        assert (root/'NUMERICAL_ENDED.json').exists() or (root/'CENSUS_ENDED.json').exists() or (root/'CENSUS_WATCHDOG_STOP.json').exists() or (root/'NUMERICAL_WATCHDOG_STOP.json').exists()
        out.mkdir(exist_ok=False);files={'raw/'+p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
        names=['F0.json','PLAN.json','BUDGET.json','REFERENCE_INDEX.json','CPU_GRAPH_EXPECTED.json','ABI_EXPORTS.json','common.py','analyzer.py','raw_math.py','run_formal.py','lifecycle.py','cpu_job.py','native_formal.cpp','formal_gate.h','core_gate.h','hs113_graph.h','lowering113_formal.exe','libggml.dll.a','libggml-base.dll.a','LINK_IDENTITY.json','CPU_NATIVE_TESTS.json','CPU_ANALYZER_TESTS_release.json','CPU_EXTRA_TESTS_release.json','CPU_LIFECYCLE_TESTS_release.json','AUTHENTICATED_F0.json','REMOTE_F0_BYTES.json']
        files.update({'frozen/'+n:V/n for n in names});assert len(files)<=s['archive_max_entries']
        assert all(len(n.encode())<=s['archive_name_UTF8_bytes_max'] for n in files)
        members=[]
        with zipfile.ZipFile(out/'RAW_FORMAL_V2.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for name,p in sorted(files.items()):z.write(p,name);members.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
        assert (out/'RAW_FORMAL_V2.zip').stat().st_size<=s['archive_upper_bound_bytes']
        save(out/'MANIFEST.json',dict(sha256=sha(out/'RAW_FORMAL_V2.zip'),bytes=(out/'RAW_FORMAL_V2.zip').stat().st_size,members=members,
            full_actual_readback_bytes_recoverable=True,no_DLL_model_recompilation_or_republication=True,no_GPU_queries_or_native_starts_in_packaging=True))
        print('Full new raw sealed; authenticate remote ZIP/manifest before fresh CPU restoration');return
    # The caller supplies a new directory after authenticating the remote ZIP.
    # No second live raw copy or a third archive copy is created here.
    manifest=load(out/'MANIFEST.json');assert sha(out/'RAW_FORMAL_V2.zip')==manifest['sha256'];dest=a.fresh_restore;dest.mkdir(exist_ok=False)
    with zipfile.ZipFile(out/'RAW_FORMAL_V2.zip') as z:
        assert len(z.namelist())==len(set(z.namelist()))==len(manifest['members'])
        for name in z.namelist():
            p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name
        z.extractall(dest)
    for m in manifest['members']:assert sha(dest/m['path'])==m['sha256'] and (dest/m['path']).stat().st_size==m['bytes']
    command=[sys.executable,'-B',str(dest/'frozen/analyzer.py'),'--root',str(dest/'raw'),'--output',str(dest/'RECOMPUTED.json')]
    result=subprocess.run(command,capture_output=True,timeout=180);save(dest/'CPU_REANALYSIS.json',dict(command=command,exit_code=result.returncode,stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace'),new_GPU_starts=0))
    assert result.returncode==0
    if (dest/'raw/ANALYSIS.json').exists():assert (dest/'RECOMPUTED.json').read_bytes()==(dest/'raw/ANALYSIS.json').read_bytes()
    save(out/'FRESH_RESTORE.json',dict(status='PASS',destination=str(dest),members_verified=len(manifest['members']),additional_native_GPU_model_starts=0,formal_F0_sha256=sha(V/'F0.json')))
    print('Fresh CPU reconstruction complete; no additional GPU admission')
if __name__=='__main__':main()
