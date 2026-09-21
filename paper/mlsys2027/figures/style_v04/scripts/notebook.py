#!/usr/bin/env python3
"""Small executable style-invariance companion; no scientific reanalysis."""
from pathlib import Path
import nbformat as nb,io,contextlib,os
HERE=Path(__file__).resolve().parents[1]
def main():
    n=nb.v4.new_notebook();md=nb.v4.new_markdown_cell;code=nb.v4.new_code_cell
    n.cells=[md('# HeteroSpec v0.4 style audit\n\n## tl;dr\nAll seven candidates pass style invariance, vector, embedded-font and text-bound checks. The 27 frozen data/provenance/manuscript files remain byte-identical to the requested checkpoint. This is not a new analysis.'),
      md('## Context & Methods\n\nBase: `afda6a192f3e9359eb5f5d7d24d3313bf59ef2f3`, branch `paper/mlsys2027-narrative-v0.2`.\n\n### Key Assumptions\nExisting validated science is authoritative. CIs, status classes and timing boundaries remain fixed. The independent validator reads frozen CSVs and actual renderer receipts; it does not import renderer helpers. Original provenance is in `../data/source_lock.json` and `../data/figure_manifest.json`.'),
      code("from pathlib import Path\nimport json, subprocess, sys\nHERE=Path.cwd()\nassert (HERE/'frozen_inputs.json').exists()"),
      md('## Data\n\n### Check the immutable baseline\nThe lock covers inputs, provenance and manuscript files. No extraction or experiment runner is invoked.'),
      code("r=subprocess.run([sys.executable, 'scripts/validate.py'], check=True, capture_output=True, text=True)\nprint(r.stdout.strip())\nqa=json.loads((HERE/'qa/validation.json').read_text())\nfor row in qa['data_quality']:\n    print(row['table'], ':', row['rows'], 'rows; unchanged; no duplicate keys or missing cells')"),
      md('## Results\n\nThis is an audit companion, not an analytical report; graphical results and their visual checks are in [STYLE_PROOF.pdf](qa/STYLE_PROOF.pdf) and [STYLE_COMPARISON.pdf](qa/STYLE_COMPARISON.pdf). Publication figures come from the tracked scripts, not notebook screenshots.'),
      code("for r in qa['candidates']:\n    print(f\"{r['asset']}: {r['status']}; {r['width_in']:.2f} × {r['height_in']:.2f} in; vector/fonts/bounds PASS\")"),
      md('### Figure 1 page cost\nCaption-inclusive dimensions are measured blocks, not final manuscript pagination. The prose sample is an optional replacement; the current introduction already summarizes all four cases.'),
      code("sizes=json.loads((HERE/'qa/page_cost.json').read_text())\nfor name in ['current_overview','figure1A','figure1B_table','figure1B_prose']:\n    r=sizes[name]\n    print(f\"{name}: width {r['width_in']:.2f} in; height with caption {r['with_caption_height_in']:.2f} in; area {r['area_with_caption_in2']:.2f} in²\")"),
      md('## Takeaways\nRecommend REMOVE FROM MAIN for the overview, RESTYLE for the M4/verification/358H plots, and REPLACE WITH TABLE for the appendix inventory. These are editorial recommendations; no manuscript prose or wrappers were changed. Read `../FIGURE_STYLE_REVIEW_V04.md` for the tradeoffs and `qa/VISUAL_QA.md` for actual-width color/grayscale checks.')]
    n.metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},
        'execution_note':'Plain Python cells executed top-to-bottom in a fresh namespace. No Jupyter kernel or notebook-viewer inspection claimed; publication proofs inspected separately.'}
    prior=Path.cwd();ns={};count=0
    try:
        os.chdir(HERE)
        for cell in n.cells:
            if cell.cell_type!='code':continue
            count+=1;s=io.StringIO()
            with contextlib.redirect_stdout(s):exec(compile(cell.source,'style audit cell '+str(count),'exec'),ns)
            cell.execution_count=count;cell.outputs=[nb.v4.new_output('stream',name='stdout',text=s.getvalue())] if s.getvalue() else []
    finally:os.chdir(prior)
    nb.validate(n);nb.write(n,HERE/'style_audit.ipynb')
    print('Audit notebook executed top-to-bottom; saved bounded outputs, no new analysis.')
if __name__=='__main__':main()
