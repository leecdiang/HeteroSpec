#!/usr/bin/env python3
"""Independent invariance and rendered-object checks; no new statistical analysis.

Reads frozen CSVs with csv, not plotting helpers. Checks the coordinates/sizes
read back from actual Matplotlib artists, compiled table text, export hashes,
PDF font embedding and vector-only PDF/SVG output for every candidate.
"""
from pathlib import Path
import csv,json,hashlib,re,math,subprocess
import fitz
HERE=Path(__file__).resolve().parents[1];FIG=HERE.parent;ROOT=FIG.parents[2]
def rows(name):return list(csv.DictReader((FIG/'data'/name).read_text().splitlines()))
def receipt(name):return json.loads((HERE/f'qa/{name}_render.json').read_text())
def close(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-13,abs_tol=1e-13),(a,b)
def main():
    lock=json.loads((HERE/'frozen_inputs.json').read_text())
    for row in lock['files']:
        assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
    profiles=[]
    for name,keys,count in [('figure1_overview.csv',['case'],4),('figure2_micro_cells.csv',['path','context'],11),
        ('figure3_workloads.csv',['workload'],2),('figure4_isolated.csv',['device','context'],6),
        ('figure4_realized.csv',['device'],2),('figure5_regimes.csv',['case'],8)]:
        rs=rows(name);assert len(rs)==count;assert len({tuple(r[k] for k in keys) for r in rs})==count
        assert all(v is not None and v!='' for r in rs for v in r.values())
        profiles.append(dict(table=name,rows=count,duplicate_keys=0,missing=0,unchanged=True))
    names=['figure1A','figure1B_table','figure1B_prose','verification','m4','state','appendix_table'];checks={n:[] for n in names}
    micro=rows('figure2_micro_cells.csv')
    for a in receipt('verification')['artists']:
        src=[r for r in micro if r['path']==a['path']];values=[float(r['v2_micro']) for r in src]
        assert len(a['points'])==len(values)
        for x,y in zip(a['points'],values):close(x,y)
        for x,y in zip(a['range'],[min(values),max(values)]):close(x,y)
        assert a['filled']==(src[0]['status']=='qualified')
        assert a['marker']==('s' if 'serialized' in a['path'] else 'o')
        assert a['status']=={'M4 Metal':'Qualified','RTX batched':'Blocked','RTX serialized':'Exact secondary control','B570 fast':'Diagnostic; inadmissible','B570 serialized':'Diagnostic; inadmissible'}[a['path']]
        if a['path'].startswith('B570'):assert 'inadmissible' in a['status']
    checks['verification'].append('All 11 plotted cells, five context ranges, fill/shape/status mappings equal frozen inputs; range is not CI.')
    for a,r in zip(receipt('m4')['artists'],rows('figure3_workloads.csv')):
        close(a['estimate'],r['speedup']);close(a['ci'][0],r['ci_low']);close(a['ci'][1],r['ci_high'])
    checks['m4'].append('Both point coordinates and both asymmetric CI endpoints match frozen studies; counts moved to caption.')
    real=rows('figure4_realized.csv');iso=rows('figure4_isolated.csv')
    for a in receipt('state')['artists']:
        if a['kind']=='isolated':
            rs=sorted([r for r in iso if r['device']==a['device']],key=lambda r:int(r['context']))
            for i,r in enumerate(rs):close(a['values'][i],r['tokens_s']);close(a['cis'][i][0],r['ci_low']);close(a['cis'][i][1],r['ci_high'])
            assert a['marker']==('o' if a['device']=='CPU' else 'D')
        elif a['kind']=='realized':
            r=next(r for r in real if r['device']==a['device']);left=0
            for p,key in zip(a['components'],['draft_s','target_s','residual_s']):
                close(p['x'],left);close(p['width'],r[key]);left+=float(r[key])
            close(left,r['total_s']);assert f"{float(r['total_s']):.2f} s" in a['label'];assert f"{float(r['headline_speedup']):.3f}× GM" in a['label']
        else:
            for r in real:close(a['x'],r['baseline_s'])
    checks['state'].append('Six isolated medians/CIs; six true component widths; totals and separate prompt-GM labels invariant. Baseline equals both frozen arithmetic means.')
    overview=rows('figure1_overview.csv')
    for a,r in zip(receipt('figure1A')['artists'],overview):
        fmt='.2f' if r['case']=='358H NPU' else '.3f'
        for k in ['local_low','local_high']:assert format(float(r[k]),fmt) in a['signal_text']
        if r['status']=='blocked':assert a['outcome_text']=='Blocked; no admissible speedup'
        else:
            assert f"{float(r['speedup']):.3f}" in a['outcome_text'] and r['exact'] in a['outcome_text']
            assert ('Profitable' if float(r['speedup'])>1 else 'Negative') in a['outcome_text']
    checks['figure1A'].append('All four case indicators, speedups, exact counts and blocked/negative/profitable classifications preserved.')
    for name in ['figure1B_table','figure1B_prose']:
        tex=(HERE/f'tables/{name}.tex').read_text();pdf=' '.join(fitz.open(HERE/f'pdf/{name}.pdf')[0].get_text().split())
        for r in overview:
            fmt='.2f' if r['case']=='358H NPU' else '.3f'
            for k in ['local_low','local_high']:
                v=format(float(r[k]),fmt);assert v in tex and v in pdf,(name,v)
            if r['status']!='blocked':assert f"{float(r['speedup']):.3f}" in pdf and r['exact'] in pdf
        checks[name].append('All four frozen local indicators, three admissible speedups and exact counts survive compiled text; no blocked speedup invented.')
        if name=='figure1B_table':
            lines=[line for line in tex.splitlines() if ' & ' in line][1:]
            for line,r in zip(lines,overview):
                parts=line.split(' & ');fmt='.2f' if r['case']=='358H NPU' else '.3f'
                for k in ['local_low','local_high']:assert format(float(r[k]),fmt) in parts[1]
                if r['status']=='blocked':assert 'Blocked; no admissible speedup' in parts[2]
                else:assert f"{float(r['speedup']):.3f}" in parts[2] and r['exact'] in parts[2]
    tex=(HERE/'tables/appendix_table.tex').read_text();pdf=' '.join(fitz.open(HERE/'pdf/appendix_table.pdf')[0].get_text().split())
    for r in rows('figure5_regimes.csv'):
        assert r['case'] in tex and r['mechanism'] in tex
        if r['exact']!='frozen gate FAIL':assert r['exact'] in pdf
        assert {'PRIMARY':'P','SECONDARY':'S','MECHANISM_SUPPORTED':'M','DIAGNOSTIC':'D'}[r['evidence_class']] in tex
        line=next(line for line in tex.splitlines() if line.startswith(r['case']+' & '));parts=line.split(' & ')
        assert parts[2]=={'profitable':'Profitable','negative':'Negative','not_admissible':'Not admissible'}[r['profitability']]
        assert parts[3]==('P/M' if r['case'].startswith('358H') else {'PRIMARY':'P','SECONDARY':'S','MECHANISM_SUPPORTED':'M','DIAGNOSTIC':'D'}[r['evidence_class']])
        assert ('Qualified' in parts[1])==(r['admissibility']=='qualified')
    for dev,field in [('CPU','target_pct'),('NPU','draft_pct')]:
        r=next(x for x in real if x['device']==dev);assert f"{float(r[field]):.2f}%" in pdf
    checks['appendix_table'].append('All eight categorical cases, evidence classes, exactness counts and prior 358H mechanism percentages retained; B570 still inadmissible.')
    caps=json.loads((HERE/'qa/caption_transfer.json').read_text())
    for r in real:
        for key in ['draft_pct','target_pct','residual_pct']:assert f"{float(r[key]):.2f}" in caps['state']['caption']
        for key in ['ci_low','ci_high']:assert f"{float(r[key]):.3f}" in caps['state']['caption']
        assert f"{float(r['residual_s'])*1000:.2f}" in caps['state']['caption']
    checks['state'].append('All moved component percentages, residual milliseconds and prompt-GM CI bounds independently match the caption handoff.')
    results=[]
    for name in names:
        r=receipt(name);path=HERE/f'pdf/{name}.pdf';doc=fitz.open(path);page=doc[0]
        assert not page.get_images(full=True),name
        assert all(f[1] not in ['n/a',''] for f in page.get_fonts(full=True)),name
        font_log=subprocess.check_output(['pdffonts',str(path)],text=True)
        for line in font_log.splitlines()[2:]:assert re.search(r'\byes\s+yes\s+(yes|no)\b',line),line
        svg=(HERE/f'svg/{name}.svg').read_text();assert '<image' not in svg and '<svg' in svg
        for ext in ['pdf','svg']:assert hashlib.sha256((HERE/f'{ext}/{name}.{ext}').read_bytes()).hexdigest()==r['output_sha256'][ext]
        for word in page.get_text('words'):
            assert word[0]>=-.2 and word[1]>=-.2 and word[2]<=page.rect.width+.2 and word[3]<=page.rect.height+.2,(name,word)
        close(page.rect.width/72,r['width_in']) if name not in ['figure1B_table','figure1B_prose','appendix_table'] else None
        assert abs(page.rect.width/72-r['width_in'])<1e-4
        results.append(dict(asset=name,status='PASS',checks=checks[name],width_in=page.rect.width/72,height_in=page.rect.height/72,vector_only=True,fonts_embedded=True,no_clipped_text=True))
    report=dict(status='PASS',scope='Style invariance against frozen validated tables, not new inference or experiment replay.',
        base_commit=lock['base_commit'],frozen_files_verified=len(lock['files']),data_quality=profiles,candidates=results)
    (HERE/'qa/validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 27 frozen files; all 7 candidates independently checked; values/CIs/status, vector-only, fonts and bounds.')
if __name__=='__main__':main()
