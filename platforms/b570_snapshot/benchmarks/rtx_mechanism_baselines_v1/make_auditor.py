"""Generate cohort-aware CPU auditor from the pinned full-byte core auditor."""
from pathlib import Path
V=Path(__file__).resolve().parent
s=(V/'export_measurements.py').read_text()
s=s.replace('def export(out,draws=4000):','def export(out,draws=4000,cohort="core"):')
s=s.replace("p=load(r/'plan.json');", "p=load(r/('P0_PLAN.json' if cohort=='p0' else 'plan.json'));")
s=s.replace("        if t['stage'] not in ['confirm','producer']:continue", "        if t['stage'] not in ['confirm','producer'] or t['task_id'] not in planned:continue")
s=s.replace("name=('producer' if t['stage']=='producer' else 'confirm')+str(t['block']//4)", "name=('p0confirm' if t['task_id'].startswith('p0off-') else 'producer' if t['stage']=='producer' else 'confirm')+str(t['block']//4)")
s=s.replace("    if (r/'PRODUCER_REFERENCES.json').exists():refs.update(load(r/'PRODUCER_REFERENCES.json'))", "    if (r/'P0_REFERENCES.json').exists():refs.update(load(r/'P0_REFERENCES.json'))")
s=s.replace("if load(a/'STARTED.json')['task']['stage']==stage]", "if load(a/'STARTED.json')['task']['stage']==stage and a.name in planned]")
s=s.replace("ap.add_argument('--out',required=True);", "ap.add_argument('--cohort',choices=['core','p0'],default='core');ap.add_argument('--out',required=True);")
s=s.replace('export(a.out,a.draws)','export(a.out,a.draws,a.cohort)')
(V/'audit_rtx.py').write_text(s)
