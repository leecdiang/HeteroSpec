"""Whitelist small CPU deliverables into additive checkout; no raw or executable copies."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).parent
FILES=['PROTOCOL.json','PROTOCOL_AMENDMENT_01.md','REMOTE_SNAPSHOTS.json','PUBLIC_DEPENDENCY_BINDINGS.json','EXACT_SOURCES.json','INPUT_BINDINGS.json','UNIT_MANIFEST.json','ARCHIVE_ACCESS.json','SESSION_BINDINGS.json','COUNTS.json','QUALIFICATION_RECOMPUTED.csv','RAW_COSTS.csv','TASK_COST_PAIRS.csv','ROUND_COST_PAIRS.csv','CONDITION_TASK_MEDIANS.csv','COST_SUMMARY.json','SOURCE_TIMER_AUDIT.md','INDEPENDENT_VERIFICATION.json','POST_AUDIT.json','CLAIM_EVIDENCE_MATRIX.csv','PAPER_HANDOFF.md','REPORT.zh-CN.md','DECISION.json','NEXT_STAGE.md','README.md','REPRODUCE.md','ANALYSIS_REPAIRS.md','SOFTWARE.json','VISUAL_CHECKS.json','STATUS.json','LEDGER.jsonl','requirements.txt','identity.py','analyze.py','verify.py','handoff.py','resume.py','seal_public.py']
FILES += ['figures/'+base+'.'+ext for base in ['task_speed_pairs','aggregate_and_rounds'] for ext in ['svg','pdf','png']]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--checkout',required=True);a=ap.parse_args();dest=Path(a.checkout)/'benchmarks/rtx_pr62_cpu_reference_closeout_v1';dest.mkdir(parents=True,exist_ok=True)
    assert not (dest/'PUBLIC_FILES.json').exists(),'sealed delivery already exists; use a new checkout'
    assert all(p.relative_to(dest).as_posix() in FILES+['.gitattributes'] for p in dest.rglob('*') if p.is_file()),'unexpected file in partial staging'
    assert json.loads((ROOT/'INDEPENDENT_VERIFICATION.json').read_text())['status']=='PASS'
    entries=[]
    for rel in FILES:
        src=ROOT/rel;data=src.read_bytes();assert len(data)<1000000,rel
        if src.suffix in ['.json','.jsonl','.csv','.md','.txt']:
            text=data.decode('utf-8');assert 'C:\\Users\\' not in text and 'C:/Users/' not in text and 'D:/HeteroSpec' not in text,rel
        target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        entries.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
    # Preserve exact CPU-output bytes, including csv.writer's CRLF, across Windows Git.
    attrs=b'* -text\n*.pdf binary\n*.png binary\n';(dest/'.gitattributes').write_bytes(attrs)
    entries.append({'path':'.gitattributes','bytes':len(attrs),'sha256':hashlib.sha256(attrs).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(attrs)).encode()+b'\0'+attrs).hexdigest()})
    manifest={'status':'PASS','files':entries,'self_excluded':'PUBLIC_FILES.json','small_CPU_derived_only':True,'raw_native_arrays_telemetry_models_binaries_excluded':True,'dependencies_and_absolute_checkpoint_roots_excluded':True}
    (dest/'PUBLIC_FILES.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'files':len(entries)+1,'bytes':sum(x['bytes'] for x in entries),'additive_directory':dest.as_posix().split('/benchmarks/')[-1]}))
if __name__=='__main__':main()
