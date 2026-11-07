"""Package actual evidence; incomplete phases remain explicitly incomplete."""
from host import *
import zipfile
DEST=HERE/'evidence'
def main():
    DEST.mkdir(exist_ok=True)
    prior=read('E:/tpds167/formal01/freeze.json')
    candidate=read(ROOT/'candidate02/binding.json');oracle=read(ROOT/'oracle02/binding.json')
    assert candidate['core']==read('E:/rtx170/new-driver/build.json')['core']
    assert oracle['core']==prior['inputs']['E:\\rtx164\\active03\\qwen_config01\\core\\src\\libllama.a']
    for name,h in prior['numerical_modules'].items():assert candidate['modules'][name]==oracle['modules'][name]==h
    assert sha(MODEL)==prior['models']['target']['sha256']
    receipt=dict(status='ADMITTED_ZERO_FORWARD_NOT_SCIENTIFIC_FREEZE',design_head='801196166c8e2a02215003301d129e68504e6b72',ancestor='371223b696bb805030c29f04e39eb17b57fb2ebb',model_sha256=sha(MODEL),admission=read(ROOT/'admit4096/admission.json'),candidate=candidate,oracle=oracle,reservation=read(ROOT/'RESERVATION.json'))
    put(DEST/'HOST_ADMISSION.json',receipt)
    for name in ('descriptor-census.json','exposure-audit.json','corpus-exclusions.json'):
        shutil.copy2(ROOT/name,DEST/name)
    p=read(ROOT/'provisional-cohort.json')
    put(DEST/'COHORT_PROVISIONAL.json',dict(status=p['status'],calibration=[dict(id=r['id'],root_id=r['root_id']) for r in p['calibration']],test=[dict(id=r['id'],root_id=r['root_id']) for r in p['test']],physical_validation_pending=True,shared_rendering_and_B570_exposure_attestation_pending=True))
    put(DEST/'TOKENIZER_AND_CENSUS.json',dict(status='NATIVE_TOKENIZATION_AND_PREDICTED_GEOMETRY_NOT_FULL_PHYSICAL_CENSUS',corpus_sha256=sha(ROOT/'oasst.messages.jsonl.gz'),revision='56e16363c12104182b8ad8173591b4d1e31c1faa',native_template=read(ROOT/'tokenize01/template.json'),native_executable_sha256=read(ROOT/'tokenize01/launch.json')['exe'],tokenized_rows_sha256=sha(ROOT/'tokenize01/tokens.jsonl'),summary=read(ROOT/'descriptor-census.json')['summary'],cache_policy='exact-token serialized sequence snapshot import',shared_panel_frozen=False))
    entries=[]
    for p in sorted(ROOT.glob('*/launch.json')):
        entries.append(dict(label=p.parent.name,launch=read(p),exit=read(p.parent/'exit.json') if (p.parent/'exit.json').exists() else None,failure=read(p.parent/'failure.json') if (p.parent/'failure.json').exists() else None))
    put(DEST/'LEDGER.json',dict(entries=entries,requests_reserved_started=sum(x['launch']['requests'] for x in entries),zero_forward_started=sum(x['launch']['admissions'] for x in entries),formal_measurements=0))
    with zipfile.ZipFile(DEST/'native-source-kit.zip','x',zipfile.ZIP_DEFLATED) as z:
        for role,base in [('candidate',Path('E:/rtx170/candidate01/source')),('oracle',Path('E:/rtx164/active03/qwen_config01/source'))]:
            for p in base.rglob('*'):
                if p.is_file() and '.git' not in p.relative_to(base).parts:z.write(p,role+'/'+p.relative_to(base).as_posix())
        z.write('E:/tpds167/build01/probe.cpp','adapter/probe.cpp')
    print('source kit bytes',(DEST/'native-source-kit.zip').stat().st_size)
if __name__=='__main__':main()
