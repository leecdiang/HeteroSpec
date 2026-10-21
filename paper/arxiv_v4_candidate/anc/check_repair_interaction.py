"""Independent arithmetic checks for the explicit retrospective interaction."""
from pathlib import Path
import csv, hashlib, importlib.util, json, math

def verify(check,root:Path):
    raw=(root/'anc/rtx_repair_cost.csv').read_bytes()
    check('Original repair CSV bytes preserved',hashlib.sha256(raw).hexdigest()=='a1c86506b1298becd0a3b23c323f9aa2305ddf891e302da4c61927c3126505fa')
    with (root/'anc/rtx_repair_cost.csv').open(newline='') as f:
        rows=list(csv.DictReader(f))
    c={(x['family'],x['comparison']):float(x['ratio']) for x in rows}
    data=json.loads((root/'anc/repair_interaction.json').read_text())
    check('Retrospective result is not new native evidence',data['new_native_executions']==0 and data['status']=='RETROSPECTIVE_REPORTED_RATIO_RECONSTRUCTION')
    for fam in ('Qwen3','SmolLM2','Llama'):
        f=data['families'][fam];q=c[fam,'M_QB/C_QB']
        check(f'{fam} target-only comparison remains qualified',c[fam,'R/M_QB']>1 and all(int(x['regressed_tasks'])==0 for x in rows if x['family']==fam and x['comparison']=='R/M_QB'))
        for layout in ('GS','PQ'):
            expected=c[fam,f'M_{layout}/M_QB']*q/c[fam,f'C_{layout}/C_QB']
            check(f'{fam}/{layout} draft identity',math.isclose(expected,f['draft_value'][layout],rel_tol=2e-15))
        gamma=c[fam,'C_GS/C_QB']/c[fam,'M_GS/M_QB']
        check(f'{fam} interaction from independent ratios',math.isclose(gamma,f['gamma_QB_from_GS'],rel_tol=2e-15))
        check(f'{fam} report rounding keeps parity classification',all((lo>1)==(hi>1) for lo,hi in f['report_rounding_enclosures'].values()))
        check(f'{fam} crossover includes PQ, not QB-only',f['local_repair_crosses_draft_parity']==(fam!='SmolLM2'))
    spec=importlib.util.spec_from_file_location('repairgen',root/'scripts/generate_repair_interaction.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for name,expected in mod.outputs(root).items():
        check('Retrospective generated artifact: '+name,(root/name).read_text()==expected)
    texfiles=list(root.rglob('*.tex'))
    check('No TeX source under arXiv ancillary directory',not list((root/'anc').rglob('*.tex')))
    check('TeX compilation independent of ancillary data',all('\\input{anc/' not in p.read_text() for p in texfiles))
    check('Original and new retrospective formulas both retained','\\label{eq:draft}' in (root/'sections/05_evaluation.tex').read_text() and '\\label{eq:repairinteraction}' in (root/'sections/05_evaluation.tex').read_text())
    return {k:v['gamma_QB_from_GS'] for k,v in data['families'].items()}
