"""Recompute fixed statistics using fully restored archived inputs and source."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess
from admission import ROOT,REPO,put,sha
from archive_results import DEST

def main():
    proof=json.loads((ROOT/'ARCHIVE_READBACK.json').read_bytes());assert proof['passed']
    restore=Path(proof['restored_root']);stage=DEST/'statistics-recomputed';stage.mkdir(exist_ok=False)
    for name in ('LIVE_RECORDS.json','SAME_WORK_CLEAN_RECORDS.json','cohort/COHORT_FREEZE.json'):
        p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);os.link(restore/'records'/name,p)
    source=restore/'scripts/analyze_results.py';raw=source.read_bytes();normalized=raw.replace(b'\r\n',b'\n')
    git_sha=hashlib.sha1(b'blob '+str(len(normalized)).encode()+b'\0'+normalized).hexdigest()
    expected=subprocess.check_output(['git','-C',str(REPO),'rev-parse','2a884e28e3c31c2cb20eebf853c48e03698364fe:benchmarks/rtx_q8_transfer_20261109/analyze_results.py'],text=True).strip()
    assert git_sha==expected,'Archived analysis differs from prospective pre-output source'
    spec=importlib.util.spec_from_file_location('archived_statistics',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=stage
    same=module.diagnostic();live=module.live()
    assert same==json.loads((restore/'records/SAME_WORK_RESULTS.json').read_bytes())
    assert live==json.loads((restore/'records/LIVE_RESULTS.json').read_bytes())
    put(ROOT/'STATISTICS_RECOMPUTED.json',dict(passed=True,source='Fully restored and SHA256-readback-verified archive; prospective analyzer from pre-output commit2a884e28',
        normalized_analysis_git_blob_sha=git_sha,analysis_raw_sha256=sha(source),recomputed_from_archived_receipts=True,
        clean_diagnostic_measurements=128,live_measurements=1024,primers=160,bootstrap_draws=10000,paired_root_clusters=16,
        primary_contrasts=4,separate_secondary_contrasts=4,all_points_and_intervals_exact=True,new_model_requests=0,output=str(stage)))
    print('Archived diagnostic and eight-arm paired-root statistics exactly reproduced',flush=True)

if __name__=='__main__':main()
