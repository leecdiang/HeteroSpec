"""Independently verify the accepted presentation against frozen input tables."""
from pathlib import Path
import csv, json, math, hashlib, subprocess
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
DATA=HERE.parents[2]/'figures/data'
REPO=HERE.parents[4]
BASE='50050f6'

def rows(name):return list(csv.DictReader((DATA/name).read_text().splitlines()))
def same(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-13,abs_tol=1e-13),(a,b)
def validate():
    reports={}
    for name,dimensions in [('m4',(234,111.6)),('verification',(486,152.64)),('state',(486,190.8))]:
        r=json.loads((HERE/f'qa/{name}.json').read_text())
        assert not r['out_of_bounds_text']
        for fn,sha in r['inputs'].items():
            p=DATA/fn
            assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
            assert p.read_bytes()==subprocess.check_output(['git','show',BASE+':'+p.relative_to(REPO).as_posix()],cwd=REPO)
        pdf=PdfReader(HERE/f'pdf/{name}.pdf');p=pdf.pages[0]
        same(p.mediabox.width,dimensions[0]);same(p.mediabox.height,dimensions[1])
        assert '<image' not in (HERE/f'svg/{name}.svg').read_text()
        if name=='m4':
            source=rows('figure3_workloads.csv');assert len(source)==len(r['artists'])==2
            for a,s in zip(r['artists'],source):
                same(a['estimate'],s['speedup']);same(a['ci'][0],s['ci_low']);same(a['ci'][1],s['ci_high'])
        elif name=='verification':
            source=rows('figure2_micro_cells.csv');assert len(r['artists'])==5
            assert sum(len(a['points']) for a in r['artists'])==len(source)==11
            for a in r['artists']:
                rs=[s for s in source if s['path']==a['path']]
                assert len(rs)==len(a['points'])==len(a['contexts'])
                for x,c,s in zip(a['points'],a['contexts'],rs):same(x,s['v2_micro']);same(c,s['context'])
                if a['path'].startswith('B570'):assert 'inadmissible' in a['status']
        else:
            for a in r['artists']:
                fn='figure4_isolated.csv' if a['kind']=='isolated' else 'figure4_realized.csv'
                rs=[s for s in rows(fn) if s['device']==a['device']]
                if a['kind']=='isolated':
                    assert len(a['values'])==len(a['cis'])==len(rs)==3
                    for x,ci,s in zip(a['values'],a['cis'],rs):same(x,s['tokens_s']);same(ci[0],s['ci_low']);same(ci[1],s['ci_high'])
                else:
                    s=rs[0]
                    for x,k in zip(a['components'],['draft_s','target_s','residual_s']):same(x,s[k])
                    same(sum(a['components']),s['total_s']);same(a['total'],s['total_s']);same(a['headline_speedup'],s['headline_speedup'])
                    same(a['dominant_share'],s['target_pct' if a['device']=='CPU' else 'draft_pct'])
        reports[name]={'status':'PASS','sha256':hashlib.sha256((HERE/f'pdf/{name}.pdf').read_bytes()).hexdigest(),'inputs':r['inputs']}
    # The rejected schematic remains exactly the selected upstream asset.
    mechanism=DATA.parent/'mechanism_v05/mechanism.pdf'
    assert mechanism.read_bytes()==subprocess.check_output(['git','show',BASE+':'+mechanism.relative_to(REPO).as_posix()],cwd=REPO)
    return reports

if __name__=='__main__':
    validate();print('Approved presentation PASS: frozen coordinates, intervals, widths, dimensions and unchanged schematic.')
