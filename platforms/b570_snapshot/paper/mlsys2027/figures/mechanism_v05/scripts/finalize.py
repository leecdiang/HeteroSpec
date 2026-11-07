#!/usr/bin/env python3
"""Package selected B, captions, manifest and immutable output fingerprints."""
from pathlib import Path
import hashlib, json, re, shutil

HERE=Path(__file__).resolve().parents[1]
BASE='974e84540b5193b416e20920629260ff320f759d'

def main():
    validation=json.loads((HERE/'qa/validation.json').read_text())
    assert all(x['status']=='PASS' for x in validation['candidates'].values())
    for ext in ('pdf','svg','tex'):
        shutil.copyfile(HERE/f'candidate_b/mechanism.{ext}',HERE/f'mechanism.{ext}')
        assert (HERE/f'mechanism.{ext}').read_bytes()==(HERE/f'candidate_b/mechanism.{ext}').read_bytes()
    shutil.copyfile(HERE/'candidate_b/caption.tex',HERE/'caption.tex')
    md=['# Proposed mechanism captions v0.5\n\nSelected: **B**. Not integrated into the manuscript. Future semantic label: `fig:translation`.\n']
    for c in ('b','a'):
        text=(HERE/f'candidate_{c}/caption.tex').read_text().strip()
        text=re.sub(r'\\textbf\{([^}]+)\}',r'**\1**',text).replace(r'\textquotesingle s',"'s").replace(r'\%', '%')
        md.append('\n## Candidate '+c.upper()+'\n\n'+text+'\n')
    (HERE/'CAPTION_SUGGESTIONS.md').write_text(''.join(md))
    costs=json.loads((HERE/'qa/page_cost.json').read_text())
    paths=['mechanism.pdf','mechanism.svg','mechanism.tex','caption.tex',
           *[f'candidate_{c}/{n}' for c in ('a','b') for n in ('mechanism.pdf','mechanism.svg','mechanism.tex','caption.tex')],
           'qa/proof_a.pdf','qa/proof_b.pdf']
    hashes={p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in paths}
    (HERE/'SHA256SUMS').write_text(''.join(f'{v}  {k}\n' for k,v in hashes.items()))
    manifest=dict(version='v0.5',base_branch='paper/mlsys2027-figure-style-v0.4',source_commit=BASE,
      work_branch='paper/mlsys2027-mechanism-figure-v0.5',selected='B',selected_status='PUBLICATION-CANDIDATE',
      question='How can local opportunity fail to translate into qualified integrated post-prefill decode gain in the tested configurations?',
      manuscript_role='Proposed beginning of Section 5 after its opening paragraph; no integration or numbering change.',
      semantic_label_for_later='fig:translation',
      extraction_script='scripts/extract.py',drawing_script='scripts/render.py',independent_validator='scripts/validate.py',
      sources=json.loads((HERE/'data/source_lock.json').read_text()),
      full_precision_anchors='data/evidence.json',scientific_validation='../MECHANISM_FIGURE_VALIDATION.md',
      visual_review='../MECHANISM_FIGURE_REVIEW.md',
      candidates={c.upper():dict(**costs[c],status='PUBLICATION-CANDIDATE' if c=='b' else 'VALIDATED_ALTERNATIVE',
          pdf=f'candidate_{c}/mechanism.pdf',svg=f'candidate_{c}/mechanism.svg',source=f'candidate_{c}/mechanism.tex',
          caption=f'candidate_{c}/caption.tex',numeric_validation='PASS',
          native_color_grayscale_96_180dpi='PASS',independent_svg_visual_check='PASS',embedded_pdf_fonts='PASS',
          vector_only='PASS',no_clipped_text='PASS') for c in ('a','b')},
      interpretation=dict(m4='Primary independent frozen studies; not assigned to either diagnosis.',
        rtx='Batched path blocked; serialized exact controls secondary. Micro context range is not a CI or complete R_target.',
        b570='Fast and serialized paths diagnostic, globally inadmissible.',
        state='Primary qualified negative outcome; mechanism-supported measured full-prefix replay+proposal, inseparable.',
        scope='Configuration-scoped and non-exhaustive; no new theoretical model; post-prefill decode.'),
      output_sha256=hashes)
    (HERE/'MECHANISM_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Selected B copied byte-for-byte; captions, manifest, and',len(hashes),'checksums saved.')

if __name__=='__main__': main()
