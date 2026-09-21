#!/usr/bin/env python3
"""Replay selected figure checks without regenerating or editing their assets."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import csv
import re
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

# Verify the style variants against the same independently replayed frozen data.
freeze=json.loads((EVID/'NARRATIVE_V03_BASELINE.json').read_text())
def rows(name):return list(csv.DictReader((FIG/'data'/name).read_text().splitlines()))
def close(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12),(a,b)
style_checks={}
for asset in ('m4','verification','state'):
    receipt=json.loads((FIG/f'style_v04/qa/{asset}_render.json').read_text())
    source=FIG/f'style_v04/pdf/{asset}.pdf'
    expected=freeze['protected_figure_tree_sha256'][str(source.relative_to(ROOT))]
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected==receipt['output_sha256']['pdf']
    assert receipt['out_of_bounds_text']==[]
    for path,sha in receipt['inputs'].items():
        assert hashlib.sha256((FIG/path).read_bytes()).hexdigest()==sha
    if asset=='m4':
        for artist,row in zip(receipt['artists'],rows('figure3_workloads.csv')):
            close(artist['estimate'],row['speedup'])
            close(artist['ci'][0],row['ci_low']);close(artist['ci'][1],row['ci_high'])
    elif asset=='verification':
        data=rows('figure2_micro_cells.csv')
        for artist in receipt['artists']:
            values=[float(r['v2_micro']) for r in data if r['path']==artist['path']]
            assert len(values)==len(artist['points'])
            for x,y in zip(artist['points'],values):close(x,y)
            close(artist['range'][0],min(values));close(artist['range'][1],max(values))
            assert artist['filled']==(artist['path'] in ('M4 Metal','RTX serialized'))
            if artist['path'].startswith('B570'):assert 'inadmissible' in artist['status']
    else:
        isolated=rows('figure4_isolated.csv');realized=rows('figure4_realized.csv')
        for artist in receipt['artists']:
            if artist['kind']=='isolated':
                data=sorted([r for r in isolated if r['device']==artist['device']],key=lambda r:int(r['context']))
                for i,row in enumerate(data):
                    close(artist['values'][i],row['tokens_s'])
                    close(artist['cis'][i][0],row['ci_low']);close(artist['cis'][i][1],row['ci_high'])
            elif artist['kind']=='realized':
                row=next(r for r in realized if r['device']==artist['device']);x=0
                for component,key in zip(artist['components'],('draft_s','target_s','residual_s')):
                    close(component['x'],x);close(component['width'],row[key]);x+=float(row[key])
                close(x,row['total_s'])
            elif artist['kind']=='baseline':
                for row in realized:close(artist['x'],row['baseline_s'])
    style_checks[asset]={'status':'PASS','sha256':expected,'native_width_in':receipt['width_in'],'native_height_in':receipt['height_in']}

# The selected final schematic is the already selected B asset, not a new quantitative analysis.
for path,sha in freeze['selected_schematic_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
schematic=PdfReader(FIG/'mechanism_v05/mechanism.pdf')
assert abs(float(schematic.pages[0].mediabox.width)/72-6.75)<1e-4
text=schematic.pages[0].extract_text()
assert 'Neither diagnosis assigned' in text and 'post-prefill' in text
assert 'does not survive the tested' in text and 'stateful integration.' in text

# The appendix retains the original rounded ranges and all 11 source cells.
lookup=(HERE/'tables/06_verification_lookup.tex').read_text()
for interval in ('1.02--1.08','0.98--1.01','2.14--2.43','1.24--1.64','1.98--1.99'):
    assert interval in lookup and interval in (HERE/'tables/03_mechanism.tex').read_text()
parsed=re.findall(r'^([^&\n]+) & (\d+) & ([\d.]+) & (.+?) \\\\$',lookup,re.M)
source_rows=rows('figure2_micro_cells.csv')
assert len(parsed)==len(source_rows)==11
for (path,context,value,status),row in zip(parsed,source_rows):
    assert path==row['path'] and context==row['context']
    assert value==f"{float(row['v2_micro']):.6f}"
    if path.startswith('B570'):assert 'diagnostic, inadmissible' in status
    if path=='RTX batched':assert status=='Correctness-blocked; diagnostic'
    if path=='RTX serialized':assert status=='Exact secondary control'
inventory=FIG/'style_v04/tables/appendix_table.tex'
assert hashlib.sha256(inventory.read_bytes()).hexdigest()==freeze['protected_figure_tree_sha256'][str(inventory.relative_to(ROOT))]
assert len(re.findall(r'^.* & .* \\\\$',inventory.read_text(),re.M))==9  # header and eight cases

# Verify actual PDF form placement, including widths, not just requested TeX sizes.
placements=[]
selected={'m4':3.25,'verification':6.75,'state':6.75,'mechanism':6.75}
for name in ('main','appendix'):
    pdf=PdfReader(HERE/'build'/f'{name}.pdf')
    for number,page in enumerate(pdf.pages,1):
        xobjects=page['/Resources'].get('/XObject',{})
        def visit(operator,operands,cm,tm):
            if operator!=b'Do' or operands[0] not in xobjects:return
            form=xobjects[operands[0]].get_object();filename=str(form.get('/PTEX.FileName',''))
            if not filename.endswith('.pdf'):return
            asset=Path(filename).stem
            assert name=='main' and asset in selected,(name,filename)
            bbox=form['/BBox'];matrix=form.get('/Matrix',[1,0,0,1,0,0])
            width=(float(bbox[2])-float(bbox[0]))*math.hypot(cm[0],cm[1])*float(matrix[0])/72
            assert abs(width-selected[asset])<0.002,(asset,width)
            placements.append({'pdf':name,'page':number,'asset':asset,'actual_width_in':width})
        page.extract_text(visitor_operand_before=visit)
assert len(placements)==4 and {p['asset'] for p in placements}==set(selected),placements
report={'status':'PASS','integration_main':freeze['main_head'],'mechanism_source_head':freeze['mechanism_source_head'],
        'source_records':len(source_lock),'historically_checked_narrative_documents':historical_documents,
        'original_five_figure_replays':results,'active_style_checks':style_checks,'actual_placements':placements,
        'appendix_lookup_cells':11,'appendix_inventory_cases':8,'assets_regenerated':False}
(EVID/'NARRATIVE_FIGURE_V03_QA.json').write_text(json.dumps(report,indent=2)+'\n')
print('Figure v0.3 PASS: frozen numerical replays, three style variants, selected final schematic, four native-width placements, and appendix tables.')
