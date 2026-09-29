"""Independently validate both panels, rendered coordinates, dimensions and labels."""
from pathlib import Path
import csv,hashlib,json,math
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]

def validate():
    checks=[]
    def check(label,value):
        assert value,label
        checks.append(label)
    r=json.loads((HERE/'qa/verification.json').read_text())
    check('text inside native figure',not r['out_of_bounds_text'])
    for path,digest in r['inputs'].items():
        check('input hash '+path,hashlib.sha256((REPO/path).read_bytes()).hexdigest()==digest)
    rows=list(csv.DictReader((REPO/'paper/mlsys2027/figures/data/figure2_micro_cells.csv').read_text().splitlines()))
    check('exactly 11 historical cells',len(rows)==sum(len(a['points']) for a in r['panel_a'])==11)
    expected=[1.022182,1.076126,1.032264,1.009030,.983148,2.430996,2.137011,1.242576,1.637295,1.982668,1.991707]
    for row,value in zip(rows,expected):check('historical six-decimal value '+row['path']+' '+row['context'],round(float(row['v2_micro']),6)==value)
    for artist in r['panel_a']:
        source=[s for s in rows if s['path']==artist['path']]
        check('A coordinates '+artist['path'],artist['points']==[float(s['v2_micro']) for s in source] and artist['contexts']==[int(s['context']) for s in source])
        check('A path-only encoding '+artist['path'],artist['encoding']=='path type only' and artist['filled'] is True)
    specs=[('benchmarks/rtx_direct_id_v2/FORMAL_ANALYSIS.json','conditions','RTX_BATCHED_K2',75,25,'BLOCKED'),
           ('benchmarks/rtx_direct_id_v2/FORMAL_ANALYSIS.json','conditions','RTX_SERIALIZED_K2',90,30,'QUALIFIED'),
           ('benchmarks/b570_direct_id_v1/FORMAL_ANALYSIS.json','paths','B570_FAST_K2',60,20,'BLOCKED'),
           ('benchmarks/b570_direct_id_v1/FORMAL_ANALYSIS.json','paths','B570_SERIALIZED_K2',78,26,'BLOCKED')]
    check('B four rows',len(r['panel_b'])==4)
    for artist,(source,key,condition,pairs,prompts,status) in zip(r['panel_b'],specs):
        row=json.loads((REPO/source).read_text(encoding='utf-8'))[key][condition]
        check('B source '+condition,(row['exact_pairs'],row['wholly_exact_prompts'],row['qualification'])==(pairs,prompts,status))
        check('B rendered '+condition,(artist['exact_pairs'],artist['exact_prompts'],artist['status'])==(pairs,prompts,status) and artist['condition']==condition)
    check('preregistered threshold',r['threshold']==90)
    pdf=PdfReader(HERE/'pdf/verification.pdf');page=pdf.pages[0]
    check('native 6.75 by 2.12 inches',abs(float(page.mediabox.width)-486)<1e-6 and abs(float(page.mediabox.height)-152.64)<1e-6)
    text=page.extract_text()
    for count in ('75/90','90/90','60/90','78/90'):check('visible count '+count,count in text)
    check('visible statuses',text.count('BLOCKED')==4 and text.count('QUALIFIED')==2)
    check('vector SVG','<image' not in (HERE/'svg/verification.svg').read_text())
    for font in page['/Resources']['/Font'].values():
        font=font.get_object()
        children=font.get('/DescendantFonts',[font])
        for child in children:
            desc=child.get_object()['/FontDescriptor'].get_object()
            check('embedded figure font',any(k in desc for k in ('/FontFile','/FontFile2','/FontFile3')))
    return {'status':'PASS','check_count':len(checks),'checks':checks,'native_size_in':[6.75,2.12],
            'pdf_sha256':hashlib.sha256((HERE/'pdf/verification.pdf').read_bytes()).hexdigest()}

if __name__=='__main__':
    result=validate();(HERE/'qa/validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Figure 3 validation PASS:',result['check_count'],'checks.')
