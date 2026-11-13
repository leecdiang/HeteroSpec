"""Bind the prospectively reserved evidence volume without resetting calibration charges."""
import json
from pathlib import Path
import runner as r

HERE=Path(__file__).resolve().parent

def main():
    binding=r.read(HERE/'STORAGE_BINDING.json')
    config=r.read(HERE/'F0B_EXECUTION.json')
    r.require(config['run_root']==binding['original_calibration_root'],'unexpected pre-binding root')
    root=Path(binding['workspace_run_root'])
    r.require(not (root/'EXECUTION.lock').exists() and not (root/'runs/E1').exists(),'E1 already started')
    r.require(len(list((root/'ledger').glob('*.json')))==binding['ledger_events_copied'],'calibration ledger changed')
    r.require(r.shutil_disk_free(root)>80*1024**3,'64 GiB storage plus16 GiB free reserve unavailable')
    config['run_root']=str(root)
    config['budget']['storage_bytes']=binding['prospective_study_storage_ceiling_bytes']
    config['budget']['minimum_free_bytes']=binding['prospective_minimum_free_bytes']
    config['storage_binding_sha256']=r.sha(HERE/'STORAGE_BINDING.json')
    config['mandatory_pre_E2_gate']={'source':'verify_complete_capture.py','source_sha256':r.sha(HERE/'verify_complete_capture.py'),
        'criterion':'Exactly one full vector for every successfully decoded native logits_mask row, including rejected rows; execute after E1 and before any E2 worker'}
    config['calibration_origin_preserved']=binding['original_calibration_root']
    config['files'].append({'path':str((HERE/'STORAGE_BINDING.json').resolve()),'bytes':(HERE/'STORAGE_BINDING.json').stat().st_size,'sha256':r.sha(HERE/'STORAGE_BINDING.json')})
    for name in ['E1_ADMISSION_CHECKS.md','CALIBRATION_ROW_COMPLETENESS_FINAL.json']:
        path=HERE/name;config['files'].append({'path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':r.sha(path)})
    config['files'].extend(r.read(HERE/'CPU_READOUT_DEPENDENCY.json')['files'])
    for name,original in config['inherited_public_files'].items():
        actual=root/name
        r.require(r.sha(actual)==r.sha(Path(original)),'transported runtime contract differs')
        config['files'].append({'path':str(actual.resolve()),'bytes':actual.stat().st_size,'sha256':r.sha(actual)})
    # This is still an uncommitted prospective registration, not scientific raw data.
    (HERE/'F0B_EXECUTION.json').write_bytes((json.dumps(config,ensure_ascii=False,indent=2)+'\n').encode())
    print('Evidence storage bound; 48 requests /24 workers remain charged; no replay')

if __name__=='__main__':main()
