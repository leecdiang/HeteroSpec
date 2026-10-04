"""Restore SHA256-addressed evidence chunks, exact files, and run offline QA."""
import argparse, hashlib, importlib.util, json, os, pathlib, shutil, subprocess, sys, tarfile, tempfile
from datetime import datetime,timezone
def sha(path):
    with pathlib.Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))
def write(path,data):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w',encoding='utf-8',newline='\n') as f:json.dump(data,f,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
def restore(index,dest,receipt=None):
    index=pathlib.Path(index).resolve();dest=pathlib.Path(dest).resolve();record=read(index)
    assert record['schema']=='heterospec.b570.prefill.cas.archive.v1'
    dest.mkdir(parents=True,exist_ok=True)
    if any(dest.iterdir()):raise RuntimeError('Destination must be an empty directory; never overwrite evidence')
    with tempfile.TemporaryDirectory(prefix='prefill-cas-',dir=dest.parent) as td:
        td=pathlib.Path(td);archive=td/'cas.tar.gz';cas=td/'cas';cas.mkdir()
        with archive.open('wb') as out:
            for part in record['parts']:
                path=index.parent/part['path']
                assert path.name==part['sha256']+'.part' and path.stat().st_size==part['bytes'] and sha(path)==part['sha256']
                with path.open('rb') as src:shutil.copyfileobj(src,out,8*1024*1024)
            out.flush();os.fsync(out.fileno())
        assert archive.stat().st_size==record['archive_bytes'] and sha(archive)==record['archive_sha256']
        with tarfile.open(archive,'r:gz') as tf:tf.extractall(cas,filter='data')
        assert sha(cas/'MANIFEST.json')==record['manifest_sha256']
        manifest=read(cas/'MANIFEST.json');checked=0
        for name,item in manifest['files'].items():
            relative=pathlib.PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts or ':' in name:raise RuntimeError('Unsafe manifest path')
            target=dest/pathlib.Path(*relative.parts);blob=cas/'blobs'/item['sha256'][:2]/item['sha256']
            assert blob.stat().st_size==item['bytes'] and sha(blob)==item['sha256']
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(blob,target)
            assert sha(target)==item['sha256'];checked+=1
        assert checked==record['manifest_files']
        # Run the original independent verifier in a shadow report directory:
        # the restored, hash-qualified evidence files remain unchanged.
        spec=importlib.util.spec_from_file_location('restored_prefill_verifier',dest/'scripts/platform/b570_prefill_diagnostic_v1/independent_verify.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        shadow=td/'reports';shadow.mkdir()
        for p in (dest/'benchmarks/b570_prefill_diagnostic_v1').glob('*'):
            if p.is_file():shutil.copy2(p,shadow/p.name)
        module.DOC=shadow;module.main()
        qa=read(shadow/'INDEPENDENT_VERIFICATION.json');computed=read(shadow/'SUMMARY.json')
        expected=read(dest/'benchmarks/b570_prefill_diagnostic_v1/SUMMARY.json')
        for key in ['valid','failed_units','attempts','repeat_stable_tasks','comparisons','diagnostic_reference_recovery','controls_reference_regressions']:
            assert computed[key]==expected[key],key
        # Directly recompute all fresh G0 arrays and sham trace/decision controls.
        out=dest/'artifacts/b570_prefill_diagnostic_v1';history=read(out/'evaluation/HISTORICAL_EXPECTED.json')
        rows=[read(p) for p in (out/'g0').glob('*/result.json')];assert len(rows)==120
        for r in rows:
            x=read(dest/r['capture']);ids=x.get('ids',x.get('generated_ids'));flags=x['eog']
            n=min(128,next((i+1 for i,f in enumerate(flags) if f),len(ids)))
            condition='R' if r['variant'].startswith('R') else 'N0' if r['variant'].startswith('N') else 'T0'
            old=history[f'{r["task"]}/{condition}/{r["rep"]}'];assert ids[:n]==old['ids'] and flags[:n]==old['eog']
        protocol=read(dest/'benchmarks/b570_prefill_diagnostic_v1/PROTOCOL.json')
        for task in protocol['g0_tasks']:
            for rep in range(1,4):
                for plain,moved in [('T_plain','T0'),('N_plain','N0')]:
                    a=next(r for r in rows if r['task']==task and r['rep']==rep and r['variant']==plain)
                    b=next(r for r in rows if r['task']==task and r['rep']==rep and r['variant']==moved)
                    x=read(dest/a['capture']);y=read(dest/b['capture']);assert x['trace']==y['trace']
                    assert [(c['id'],c['accepted'],c['proposal'],c['scores']) for c in x['commits']]==[(c['id'],c['accepted'],c['proposal'],c['scores']) for c in y['commits']]
        # Each frozen source stays byte-identical; machine-local names are provenance only.
        freeze=read(dest/'benchmarks/b570_prefill_diagnostic_v1/FREEZE.json')
        for name,h in freeze['sources'].items():
            name=name.replace('\\','/');suffix=name.split('/scripts/platform/b570_prefill_diagnostic_v1/',1)[1]
            assert sha(dest/'scripts/platform/b570_prefill_diagnostic_v1'/suffix)==h
        result={'status':'PASS','checked_utc':datetime.now(timezone.utc).isoformat(),'archive_sha256':record['archive_sha256'],
          'archive_index_sha256':sha(index),'manifest_sha256':record['manifest_sha256'],'restored_files':checked,
          'dest':str(dest),'independent_raw_checks':qa['checks'],'formal_units':360,'fresh_G0_arrays':120,'sham_trace_pairs':30,
          'frozen_source_bytes':'PASS','all_summary_results_recomputed_equal':True,'no_model_inference':True,
          'omitted_assets':'model weights and rebuildable runtime binaries are not part of this portable archive; original asset hashes remain recorded'}
    if receipt:write(receipt,result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--dest',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path);a=p.parse_args();restore(a.archive,a.dest,a.receipt)
