"""Finite byte/state comparisons. No tolerance, text-only or candidate-oracle fallback.

Use captures from independent R cases at the same logical prefix. Full serialized
bytes are a conservative default. If only non-value serialization metadata differs,
use the reviewed active-state extractor in a NEW recorded comparison version.
"""
from pathlib import Path
import argparse
from common import read, need, sha, save

def compare(manifest):
    mode=manifest.get('mode','candidate_vs_reference')
    need(mode in ('candidate_vs_reference','reference_repeat'),'Unknown comparison mode')
    same=manifest.get('reference_executable_sha256')==manifest.get('candidate_executable_sha256')
    need(same if mode=='reference_repeat' else not same,'Wrong independent/repeat executable identity')
    need(manifest.get('reference_core')=='pristine-upstream','Reference cannot be a candidate strategy switch')
    pairs=manifest['pairs'];need(pairs,'No capture pairs')
    out=[]
    for p in pairs:
        need(p['kind'] in ('full_requested_logits','active_sequence_serialized','frontier'),'Unknown comparison kind')
        a,b=Path(p['reference']),Path(p['candidate']);need(a.is_file() and b.is_file(),'Missing capture; not a pass')
        need(a.resolve()!=b.resolve(),'A capture cannot be compared to itself')
        need(a.stat().st_size>0,'Empty capture')
        h1,h2=sha(a),sha(b);out.append(dict(p,reference_sha256=h1,candidate_sha256=h2,reference_bytes=a.stat().st_size,candidate_bytes=b.stat().st_size,equal=h1==h2))
    return {'mode':mode,'pairs':out,'passed':all(p['equal'] for p in out),'scope':manifest['scope'],'not_arbitrary_input_proof':True}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('out',type=Path);a=p.parse_args();save(a.out,compare(read(a.manifest)))
