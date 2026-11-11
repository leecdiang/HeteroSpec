"""Classify actual source transfer; don't count a renamed model as zero-change reuse."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared'))
from experiment import read,save,require

def classify(before,after):
    for x in (before,after):require(x.get('rule_files') and x.get('backend_files') and x.get('model_sha256'),'Incomplete transfer manifest')
    changed=[]
    for section in ('rule_files','backend_files'):
        for name in sorted(set(before[section])|set(after[section])):
            if before[section].get(name)!=after[section].get(name):changed.append(section+'/'+name)
    return dict(changed_files=changed,source_rule_transfer='UNCHANGED' if not changed else 'EXTENDED_NEW_VERSION',
            zero_modification_claim_allowed=not changed,
            model_changed=before['model_sha256']!=after['model_sha256'],
            numeric_qualification='MUST_USE_INDEPENDENT_LLAMA_REFERENCE',
            compiler_and_hardware_identity='BIND_SEPARATELY; source equality alone is not binary equality')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('before');p.add_argument('after');p.add_argument('out');a=p.parse_args();save(a.out,classify(read(a.before),read(a.after)))
