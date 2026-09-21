#!/usr/bin/env python3
"""Replay selected figure checks without regenerating or editing their assets."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import subprocess
from pypdf import PdfReader

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
FIG = HERE.parent / 'figures'
EVID = HERE.parent / 'evidence'
integration = json.loads((EVID/'NARRATIVE_FIGURE_INTEGRATION_BASELINE.json').read_text())
source_lock = json.loads((FIG/'data/source_lock.json').read_text())
historical_documents = []
for source in source_lock:
    path = source['path']
    current = (ROOT/path).read_bytes()
    if path == 'paper/mlsys2027/WRITING_STATUS.md':
        # Narrative status was intentionally updated; inspect its frozen figure-source revision.
        current = subprocess.check_output(['git','show',f"{integration['main_head']}:{path}"],cwd=ROOT)
        historical_documents.append(path)
    assert hashlib.sha256(current).hexdigest() == source['sha256'], path

spec = importlib.util.spec_from_file_location('selected_figure_validation',FIG/'scripts/validate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
results = {}
for i in range(1,6):
    findings = getattr(module,f'f{i}')()
    source = FIG/'pdf'/f'figure{i}.pdf'
    path = str(source.relative_to(ROOT))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == integration['protected_sha256'][path]
    page = PdfReader(source).pages[0]
    expected_width = 3.25 if i == 3 else 6.75
    assert abs(float(page.mediabox.width)/72-expected_width)<1e-4
    receipt=json.loads((FIG/f'qa/figure{i}_render.json').read_text())
    assert receipt['out_of_bounds_text']==[]
    results[str(i)]={'status':'PASS','findings':findings,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                     'native_width_in':expected_width,'native_height_in':float(page.mediabox.height)/72}

# Verify actual PDF form placements, not merely the requested LaTeX widths.
placements=[]
for name in ('main','appendix'):
    pdf=PdfReader(HERE/'build'/f'{name}.pdf')
    for number,page in enumerate(pdf.pages,1):
        xobjects=page['/Resources'].get('/XObject',{})
        def visit(operator,operands,cm,tm):
            if operator!=b'Do' or operands[0] not in xobjects:return
            form=xobjects[operands[0]].get_object()
            filename=str(form.get('/PTEX.FileName',''))
            if '/figures/pdf/figure' not in filename:return
            asset=Path(filename).stem
            bbox=form['/BBox'];matrix=form.get('/Matrix',[1,0,0,1,0,0])
            width=(float(bbox[2])-float(bbox[0]))*math.hypot(cm[0],cm[1])*float(matrix[0])/72
            expected=3.25 if asset=='figure3' else 6.75
            assert abs(width-expected)<0.002,(asset,width,expected)
            assert (name=='appendix')==(asset=='figure5'),(name,asset)
            placements.append({'pdf':name,'page':number,'asset':asset,'actual_width_in':width})
        page.extract_text(visitor_operand_before=visit)
assert len(placements)==5,placements
assert {p['asset'] for p in placements if p['pdf']=='main'}=={'figure1','figure2','figure3','figure4'}
report={'status':'PASS','integration_main':integration['main_head'],'source_records':len(source_lock),
        'historically_checked_narrative_documents':historical_documents,'figures':results,
        'actual_placements':placements,'assets_regenerated':False}
(EVID/'NARRATIVE_FIGURE_QA.json').write_text(json.dumps(report,indent=2)+'\n')
print('Figure integration PASS: five independent numerical replays, immutable assets, and five native-width PDF placements.')
