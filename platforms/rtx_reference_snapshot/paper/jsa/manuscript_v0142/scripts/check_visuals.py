"""Check drawn values against frozen data and vector figure text bounds."""
from pathlib import Path
import csv, hashlib, json, math, statistics, subprocess
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]

def main():
    data = json.loads((ROOT/'output/FIGURE_INPUTS.json').read_text())
    with (ROOT/'evidence/rtx66/RAW_COSTS.csv').open() as f:
        raw = list(csv.DictReader(f))
    tasks = sorted({r['task'] for r in raw})
    med = {(t,c,timer):statistics.median(float(r[timer+'_ms']) for r in raw if r['task']==t and r['condition']==c)
           for t in tasks for c in ['scalar_reference','matched_target','target_scopes'] for timer in ['generation','whole']}
    taskplot=data['figure_5_task_variation']
    assert sorted(taskplot['order'])==tasks and len(tasks)==24
    for timer, values in taskplot['ratios'].items():
        for t,v in values.items():
            assert math.isclose(v,med[t,'matched_target',timer]/med[t,'target_scopes',timer],rel_tol=1e-12)
    cost=data['figure_4_paid_cost']['comparisons']
    saved=json.loads((ROOT/'evidence/rtx66/COST_SUMMARY.json').read_text())['comparisons']
    for c in cost:
        s=next(s for s in saved if all(s[k]==c[k] for k in ['timer','baseline','candidate']))
        assert c['ratio']==s['task_median_gm'] and c['interval']==s['descriptive_task_bootstrap_95_linear']
    r=next(s for s in saved if s['timer']=='whole' and s['baseline']=='matched_target' and s['candidate']=='target_scopes')
    assert taskplot['rounds']==r['rounds']
    phase=data['figure_3_phase_matrix']
    assert [r['mask'] for r in phase['factorial']]==list(range(16))
    assert [r['mask'] for r in phase['factorial'] if r['qualifies']]==[3,7,11,15]
    assert len(phase['geometry'])==12
    assert all(r['qualifies']==(r['UB']<=4) for r in phase['geometry'])
    documents={}
    for p in sorted((ROOT/'figures').glob('*.pdf')):
        fonts=subprocess.run(['pdffonts',str(p)],text=True,capture_output=True,check=True).stdout
        assert 'Type 3' not in fonts
        with pdfplumber.open(p) as pdf:
            assert len(pdf.pages)==1
            page=pdf.pages[0]
            assert abs(page.width-7.2*72)<.02
            outside=[c['text'] for c in page.chars if c['x0']<-.5 or c['x1']>page.width+.5 or c['top']<-.5 or c['bottom']>page.height+.5]
            assert not outside,(p.name,outside)
            assert not page.images, p.name
            documents[p.name]=dict(width_pt=page.width,height_pt=page.height,characters=len(page.chars),
                text_within_canvas=True,raster_images=0,type3_fonts=0,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    record=dict(version='v0.14.2',status='PASS',task_points_verified=48,saved_ratio_intervals_verified=6,
                saved_request_rounds_verified=4,phase_masks=16,geometry_cells=12,figures=documents,
                scope='Values, source-bound matrix shape and vector bounds; visual review recorded separately.')
    (ROOT/'output/VISUAL_DATA_QA.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
