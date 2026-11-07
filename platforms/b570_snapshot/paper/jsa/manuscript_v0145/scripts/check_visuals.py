"""Check drawn values against frozen data and vector figure text bounds."""
from pathlib import Path
import csv, hashlib, json, math, re, statistics, subprocess
import xml.etree.ElementTree as ET
import pdfplumber
from revision_qa import figure_inputs

ROOT = Path(__file__).resolve().parents[1]

BLUE='#426b8b'; OCHRE='#b07b43'; GREEN='#3e725e'; GRAY='#72787c'


def style(element):
    return dict(part.strip().split(':', 1) for part in element.get('style', '').split(';') if ':' in part)


def svg(name):
    return ET.parse(ROOT/'figures'/(name+'.svg')).getroot()


def uses(group):
    return [e for e in group.iter() if e.tag.endswith('use')]


def rgb(hexcode):
    return tuple(int(hexcode[i:i+2], 16)/255 for i in [1, 3, 5])


def color_equal(color, hexcode):
    return color is not None and all(abs(a-b) < 1e-8 for a, b in zip(color, rgb(hexcode)))


def rendered_semantics(data):
    # Inspect actual vector objects, not just a palette declaration in inputs.
    revision=data['semantic_visual_revision']
    cross=data['figure_2_natural_crosses']
    axes={g.get('id'):g for g in svg('figure_2_natural_crosses').iter() if g.get('id','').startswith('axes_')}
    for i, case in enumerate(cross['cases']):
        matrix=case['matrix']
        flags=[matrix[r][0]!=matrix[r][1] for r in range(2)] + [matrix[0][k]!=matrix[1][k] for k in range(2)]
        entry=revision['figure2_categorical_adjacency'][i]
        assert flags==entry['horizontal_different']+entry['vertical_different']
        axis=axes[f'axes_{i+1}']
        lines=[g for g in axis if g.get('id','').startswith('line2d_')]
        assert len(lines)==4
        for group, changed in zip(lines, flags):
            path=next(e for e in group if e.tag.endswith('path'))
            assert style(path)['stroke'].strip()==(OCHRE if changed else GRAY)
            assert 'marker' not in path.attrib, 'Relations must not imply temporal transitions'
        glyphs=[''.join(e.itertext()).strip() for e in axis.iter() if e.tag.endswith('text')]
        assert [g for g in glyphs if g in ['=', '≠']]==['≠' if flag else '=' for flag in flags]
        assert [g for g in glyphs if g.isdecimal()]==[str(v) for row in matrix for v in row]
        patches=[g for g in axis if g.get('id','').startswith('patch_')]
        assert len(patches)==4
        for group, value in zip(patches, [v for row in matrix for v in row]):
            path=next(e for e in group if e.tag.endswith('path'))
            assert style(path)['stroke'].strip()==(BLUE if value==matrix[0][0] else OCHRE)
    # The only filled fraction in F is 18/72; it is not a time series.
    bars=[next(e for e in g if e.tag.endswith('path')) for g in axes['axes_6'] if g.get('id','').startswith('patch_')]
    assert len(bars)==3
    def width(path):
        coordinates=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',path.get('d'))))
        return max(coordinates[0::2])-min(coordinates[0::2])
    assert math.isclose(width(bars[2])/width(bars[1]),cross['downstream_changed']/cross['forks'],abs_tol=1e-7)

    with pdfplumber.open(ROOT/'figures/figure_1_architecture.pdf') as pdf:
        page=pdf.pages[0]
        nodes=[c for c in page.curves if c['fill'] and c['stroke'] and c['y1']<110]
        assert len(nodes)==7
        phases=sorted([c for c in nodes if c['x1']<240],key=lambda c:(-c['y0'],c['x0']))
        horizontal_gap=min(phases[1]['x0']-phases[0]['x1'],phases[3]['x0']-phases[2]['x1'])
        vertical_gap=min(phases[0]['y0']-phases[2]['y1'],phases[1]['y0']-phases[3]['y1'])
        assert horizontal_gap>=18 and vertical_gap>=15
        constrained=sorted([c for c in nodes if c['x0']>240],key=lambda c:c['x0'])
        assert all(color_equal(c['stroking_color'],GREEN) for c in constrained)
        shafts=sorted([c for c in page.curves if abs(c['y0']-c['y1'])<1e-6
                      and 60<c['y0']<70 and color_equal(c['stroking_color'],GRAY)],key=lambda c:c['x0'])
        assert len(shafts)==3
        clearances=[constrained[0]['x0']-shafts[0]['x1']]
        for i in [1,2]:
            clearances.extend([shafts[i]['x0']-constrained[i-1]['x1'],constrained[i]['x0']-shafts[i]['x1']])
        assert min(clearances)>=7
    # Check filled target/draft phase switches in the exported SVG.
    groups=[g for g in svg('figure_3_phase_matrix').iter() if g.get('id','').startswith('PathCollection_')]
    assert len(groups)==140
    for i, entry in enumerate(data['figure_3_phase_matrix']['factorial']):
        for j, enabled in enumerate(entry['bits']):
            actual=style(uses(groups[i*8+j])[0])
            expected=BLUE if j<2 else OCHRE
            assert actual['stroke'].strip()==(expected if enabled else '#d9dfe1')
            assert actual['fill'].strip()==(expected if enabled else '#ffffff')

    # Verify the 48+4 plotted positions and roles, independently of timer labels.
    groups=[g for g in svg('figure_5_task_variation').iter() if g.get('id','').startswith('PathCollection_')]
    assert len(groups)==52
    for offset,timer,left in [(0,'generation',.07),(24,'whole',.405)]:
        for i,task in enumerate(data['figure_5_task_variation']['order']):
            use=uses(groups[offset+i])[0]
            actual=style(use)
            value=data['figure_5_task_variation']['ratios'][timer][task]
            plotted=.80+(float(use.get('x'))/518.4-left)/.28*(1.48-.80)
            assert math.isclose(plotted,value,abs_tol=1e-7)
            assert actual['stroke'].strip()==OCHRE
            assert actual['fill'].strip()==(OCHRE if value>1 else '#ffffff')
    for i,entry in enumerate(data['figure_5_task_variation']['rounds']):
        use=uses(groups[48+i])[0]
        plotted=.91+(float(use.get('x'))/518.4-.80)/.17*(1.075-.91)
        assert math.isclose(plotted,entry['gm'],abs_tol=1e-7)
        assert style(use)['stroke'].strip()==OCHRE
    # Colors on the actual labeled comparison values and path names.
    for figure, required in [
        ('figure_4_paid_cost',[(f'{c["ratio"]:.3f}×',GREEN if c['candidate']=='matched_target' else OCHRE if c['baseline']=='matched_target' else GRAY) for c in data['figure_4_paid_cost']['comparisons']]),
        ('figure_S1_b570_contract',[('ordinary',BLUE),('matched',GREEN),('candidate',OCHRE)]),
        ('figure_S2_358h_budget',[(f'{p[key]:.3f}',OCHRE if key=='actual' else GREEN) for p in data['figure_S2_358h_budget']['points'].values() for key in ['actual','ceiling']])]:
        with pdfplumber.open(ROOT/'figures'/(figure+'.pdf')) as pdf:
            words=pdf.pages[0].extract_words(extra_attrs=['non_stroking_color'])
            for label, color in required:
                assert any(w['text']==label and color_equal(w['non_stroking_color'],color) for w in words),(figure,label,color)
    allowed={BLUE,OCHRE,GREEN,GRAY,'#202629','#d9dfe1','#f1f5f8','#fbf5ee','#f0f6f2','#ffffff','#000000'}
    for path in (ROOT/'figures').glob('*.svg'):
        assert set(re.findall(r'#[0-9a-f]{6}',path.read_text()))<=allowed,path.name
    return dict(actual_figure2_ids_and_twenty_equality_links_verified=True,
        actual_18_of_72_bar_fraction_verified=True,
        figure1c_horizontal_gap_pt=horizontal_gap,figure1c_vertical_gap_pt=vertical_gap,
        figure1c_minimum_arrow_to_box_clearance_pt=min(clearances),
        actual_enabled_target_and_draft_switch_colors_verified=True,
        actual_48_task_and_4_round_positions_and_roles_verified=True,
        actual_R_M_C_and_speculative_comparison_colors_verified=True,
        seven_svg_palettes_have_only_shared_role_colors=True)

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
    revision_inputs=figure_inputs(json.loads((ROOT/'provenance/V0143_BASELINE_CONTENT.json').read_text()))
    semantic_checks=rendered_semantics(data)
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
    record=dict(version='v0.14.4',status='PASS',task_points_verified=48,saved_ratio_intervals_verified=6,
                saved_request_rounds_verified=4,phase_masks=16,geometry_cells=12,
                revised_figure_source_checks=revision_inputs,rendered_semantic_checks=semantic_checks,figures=documents,
                scope='Values, source-bound matrix shape and vector bounds; visual review recorded separately.')
    (ROOT/'output/VISUAL_DATA_QA.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
