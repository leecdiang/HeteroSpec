#!/usr/bin/env python3
"""Manifest for style assets; original scientific provenance stays byte-identical."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parents[1]
def main():
    qa=json.loads((HERE/'qa/validation.json').read_text());assert qa['status']=='PASS'
    original=json.loads((HERE.parent/'data/figure_manifest.json').read_text())
    ids={'figure1A':1,'figure1B_table':1,'figure1B_prose':1,'verification':2,'m4':3,'state':4,'appendix_table':5}
    records=[];hashes=[]
    for c in qa['candidates']:
        name=c['asset'];src=original[ids[name]-1];outs=[]
        for ext in ['pdf','svg']:
            rel=f'{ext}/{name}.{ext}';b=(HERE/rel).read_bytes();sha=hashlib.sha256(b).hexdigest()
            outs.append(dict(path=rel,sha256=sha));hashes.append(f'{sha}  {rel}\n')
        records.append(dict(asset=name,original_asset_id=ids[name],style_base_commit=qa['base_commit'],
            scientific_manifest_pointer='../data/figure_manifest.json',scientific_source_lock_pointer='../data/source_lock.json',
            original_source_commit=src['source_commit'],original_sources=src['sources'],
            original_estimator=src['estimator'],original_evidence=src['evidence'],original_correctness=src['correctness'],original_caveats=src['caveats'],
            original_plotting_tables=['../data/'+x for x in src['tables']],
            scripts=['scripts/plot.py' if name in ['figure1A','verification','m4','state'] else 'scripts/tables.py','scripts/validate.py'],
            tested_width_in=c['width_in'],height_in=c['height_in'],validation=c,
            color_qa='PASS at native width; see qa/VISUAL_QA.md',grayscale_qa='PASS at native width; see qa/VISUAL_QA.md',outputs=outs))
    (HERE/'STYLE_MANIFEST.json').write_text(json.dumps(records,indent=2)+'\n')
    for p in [HERE/'qa/STYLE_PROOF.pdf',HERE/'qa/STYLE_COMPARISON.pdf']:
        hashes.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(HERE)}\n')
    (HERE/'SHA256SUMS').write_text(''.join(hashes))
    print('Manifest: 7 candidates, 14 vector exports, inherited scientific provenance and 2 proof hashes.')
if __name__=='__main__':main()
