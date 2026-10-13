"""CPU-only delivery repair; preserves frozen GPU code and failed delivery bytes."""
from common95 import *
import shutil
CODE=Path(__file__).parent

def main():
    assert not (LOCAL/'RESULT_PR.json').exists()
    result=read(LOCAL/'INDEPENDENT_RESULTS.json')
    assert result['status']=='PASS_INDEPENDENT_AUDIT'
    assert result['counts']['formal_completed']==2016 and result['counts']['formal_missing']==0
    for phase in ['F0A','F0B','F0A_V02','F0B_V02']:
        for name,h in read(PUB/(phase+'.json'))['payload_sha256'].items():assert sha(REPO/name)==h
    retained=Path('D:/hsc95-delivery-failure-v03').resolve()
    assert retained==Path('D:/hsc95-delivery-failure-v03') and not retained.exists()
    retained.mkdir()
    evidence=LOCAL/'delivery-correction-v03';evidence.mkdir()
    old=LOCAL/'RAW_EVIDENCE.zip'
    with zipfile.ZipFile(old) as z:
        index=z.read('INDEX.json')
        assert 'local/parent-remote/RAW_EVIDENCE.zip' not in z.namelist()
    (evidence/'FAILED_ARCHIVE_INDEX.json').write_bytes(index)
    receipt=dict(utc=now(),scope='CPU delivery only; no further GPU starts',
        cause='Root archive exclusion compared only basename, unintentionally omitting inherited parent RAW_EVIDENCE.zip',
        failed_archive_sha256=sha(old),failed_archive_bytes=old.stat().st_size,
        retained_failed_artifacts=str(retained),all_scientific_bytes_reincluded=True,
        formal_requests_rerun=0,independent_results_sha256=sha(LOCAL/'INDEPENDENT_RESULTS.json'),
        metadata_correction='INDEPENDENT_CPU now identifies the actual standalone V02 auditor and V02 synthetic suite')
    for p in [old,PUB/'RAW_EVIDENCE_MANIFEST.json',*sorted(PUB.glob('RAW_EVIDENCE.part*'))]:
        dest=retained/p.name;assert not dest.exists();shutil.move(str(p),str(dest))
    for name in ['RAW_EVIDENCE_MANIFEST.json','INDEPENDENT_CPU.json','RESULTS.md']:
        source=retained/name if name=='RAW_EVIDENCE_MANIFEST.json' else PUB/name
        shutil.copyfile(source,evidence/('PREVIOUS_'+name))
    for name in ['INDEPENDENT_CPU.json','RESULTS.md']:
        shutil.move(str(PUB/name),str(retained/name))
    restore=LOCAL/'restore-local'
    assert restore.resolve()==Path('D:/hsc95/restore-local')
    shutil.move(str(restore),str(retained/'restore-local'))
    save(evidence/'DELIVERY_CORRECTION.json',receipt);save(PUB/'DELIVERY_CORRECTION_V03.json',receipt)
    src=(CODE/'delivery95.py').read_text(encoding='utf-8')
    changes={
        "CODE/'audit95.py'":"CODE/'audit95_v02.py'",
        "synthetic_checks=read(PUB/'SYNTHETIC_CHECKS.json')":"synthetic_checks=read(PUB/'SYNTHETIC_CHECKS_V02.json'),script_path='scripts/platform/rtx_querylayout_mechanism_v1/audit95_v02.py'",
        "['native','parent-restored','restore-local','restore-remote']":"['native','native-repair','parent-restored','restore-local','restore-remote']",
        "if p.name in ['STATUS.json','RAW_EVIDENCE.zip','controller.lock'] or p.name.startswith('controller'):continue":"if rel.as_posix() in ['STATUS.json','RAW_EVIDENCE.zip','controller.lock','controller-v02.lock']:continue",
        "parent=target/'local/parent-remote/RAW_EVIDENCE.zip';parent_count=check_nested(parent)":"corrected=check_nested(target/'local/SOURCE_RUNTIME_V02.zip')\n    parent=target/'local/parent-remote/RAW_EVIDENCE.zip';parent_count=check_nested(parent)",
        "source_runtime_files=nested,parent_scientific_files=parent_count":"source_runtime_files=nested,corrected_source_runtime_files=corrected,parent_scientific_files=parent_count",
        "Run the standalone stdlib audit95.py":"Run the standalone stdlib audit95_v02.py",
        "if __name__=='__main__':closeout()":"if __name__=='__main__':\n    import correction95_v02\n    correction95_v02.delivery95.closeout=closeout\n    correction95_v02.corrected_delivery()",
    }
    for oldtext,newtext in changes.items():
        assert oldtext in src,oldtext;src=src.replace(oldtext,newtext)
    src=src.replace("return '\\n'.join(lines)","lines += ['', '## Preserved implementation and delivery faults', '', 'Four original Smol/Llama PQ warm failures remain charged and were never retried. Prospective V02 changes only the host graph capacity bound by the predeclared maximum q=4; all numerical DLLs and operators are unchanged. QB eligibility was recovered from existing final tensor aliases and twelve exact outputs, without GPU reruns. Original frozen files remain immutable. V03 repairs only parent-archive inclusion and auditor metadata after all 2016 formal requests completed; the failed archive index, manifest, original reports and controller failure are retained. See IMPLEMENTATION_FAULT_CORRECTION.json, RESOURCE_CORRECTION.json and DELIVERY_CORRECTION_V03.json.', '']\n    return '\\n'.join(lines)")
    out=CODE/'delivery95_v03.py';assert not out.exists();out.write_text(src,encoding='utf-8')
    compile(src,str(out),'exec')
    status('CPU_DELIVERY_V03_READY',formal_completed=2016,no_GPU_rerun=True)

if __name__=='__main__':main()
