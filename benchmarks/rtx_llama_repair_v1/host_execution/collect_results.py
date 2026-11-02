"""Copy compact, immutable scientific receipts for the separate results PR."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    root=Path('E:/rtx160');research=root/'research';epoch=research/'epoch07'
    required=[epoch/'CANDIDATE_FREEZE.json',epoch/'QUALIFICATION_PASS.json',epoch/'FINAL_COST.json',epoch/'INDEPENDENT_COST.json',epoch/'INDEPENDENT_QUALIFICATION.json',research/'LEDGER_AUDIT.json',research/'CROSS_MODEL_REGRESSION.json']
    assert all(p.exists() for p in required),'scientific closeout not complete'
    assert not a.out.exists();a.out.mkdir(parents=True);entries=[]
    def copy(path,name):
        dest=a.out/name;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists()
        shutil.copy2(path,dest);assert sha(path)==sha(dest)
        entries.append({'path':name,'source':str(path),'bytes':dest.stat().st_size,'sha256':sha(dest)})
    for name in ('HISTORY.json','EARLY_ROW_MAP02.json','ORIGINAL_BINDING.json','REFERENCES.json','DEV.json'):
        copy(Path('D:/rtx160/research/history01')/name,'history/'+name)
    for folder in ('epoch01','epoch02','epoch03','epoch04','epoch06','epoch07','qwen8b02','qwen14b02'):
        b=research/folder
        for f in sorted(b.glob('*.json')):
            if f.name in ('CONFIG.json','DEV.json','SLOTS.json','DEV_REFERENCES.json','BINDING.json','ORIGINAL_BINDING.json','PLAN.json','POLICY.json'):continue
            copy(f,folder+'/'+f.name)
        for f in sorted((b/'units').glob('*/RECEIPT.json')):
            copy(f,folder+'/'+f.relative_to(b).as_posix())
    op=research/'epoch03/units/attention_replay01'
    for name in ('MECHANISM_AUDIT02.json','MANIFEST.json'):
        copy(op/name,'operator-replay/'+name)
    for name in ('LEDGER.jsonl','RESOURCE_POLICY.jsonl','ENGINEERING_CHANGES.jsonl','LEDGER_AUDIT.json','CROSS_MODEL_REGRESSION.json','SELECTION_PROVENANCE.json','HELDOUT_SELECTION01.json','HOST_SCHEMA_REPAIR.json'):
        copy(research/name,'shared/'+name)
    for config in sorted(p for p in root.glob('*config*') if p.is_dir()):
        for name in ('BUILD.json','LLAMA_SOURCE_BINDING.json'):
            copy(config/'build'/name,config.name+'/'+name)
    for name in ('TOKENIZATION_RECEIPT.json','COUNTS.json'):
        copy(root/'preparation01'/name,'tokenization/'+name)
    for name in ('COVERAGE_REVIEW.json','REMOTE_REFS.txt','GIT_REFS.txt'):
        copy(root/'exposure04'/name,'exposure/'+name)
    for f in sorted(Path('D:/rtx160/operations').glob('*.json')):
        if not f.name.startswith(('PACK','ARCHIVE','UPLOAD','REMOTE','DELIVERY','PUBLISH','TRANSPORT')):
            copy(f,'operations/'+f.name)
    report={'status':'SCIENTIFIC_RECEIPTS_COPIED_BYTE_EXACT','files':entries,
      'source_commit_start':'aff1d029966a20adebfad6b664a36f32ed04bf9c',
      'scope':'Compact PR receipts. Complete vectors, states, source trees, failed raw and preparation inventories are in the release archive; no omitted failure is credited back.'}
    with (a.out/'INDEX.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(report['status'],len(entries),flush=True)


if __name__=='__main__':main()
