"""CPU-only pinned input reuse and isolated native build. Never starts a GPU."""
import copy,json,os,shutil,subprocess,time,uuid
from pathlib import Path
V=Path(__file__).resolve().parent
P=V.parent/'rtx_boundary_confirmation_v1'
OLD=Path('D:/hs121-0cd72634-266d-4b57-9b00-1d7df2327735')
for name in ['common.py','lifecycle.py','cpu_job.py','graph_base.h','hs113_graph.h','core_gate.h','boundary_cpu.cpp']:
    assert not (V/name).exists();shutil.copyfile(P/name,V/name)
from common import load,save,sha
from plan import make_plan
r=Path('D:/hs122-'+str(uuid.uuid4()));r.mkdir()
save(V/'LOCAL_RUN.json',dict(root=str(r)))
s=load(OLD/'RUN_SPEC.json');s.update(run_id='rtx-mechanism-baselines-v1',execution_id=r.name,start_epoch=1792317519.0,global_seconds=21600,delivery_reserve_seconds=2700,parent_commit='d82ec4097adfa032886040e075e71e41cfeb5855',design_commit='c505f1fb341bb0ed08735a369e405183283db9bc')
save(r/'RUN_SPEC.json',s);save(r/'RUNTIME_MANIFEST.json',s['numerical_DLLs'])
for name,h in s['numerical_DLLs'].items():assert sha(Path(s['runtime_directory'])/name)==h
save(r/'DUAL_PLAN_INITIAL.json',make_plan('dual'))
plan=make_plan('off-only');save(r/'plan.json',plan)
rows=load(OLD/'INPUTS.json');selected={}
# Includes optional q4 input bytes now, but no optional GPU task is admitted yet.
ids=[c['case_id'] for c in plan['cases']]+[f'q4-k256-v{v}' for v in [0,1]]
for cid in ids:
    c=copy.deepcopy(rows[cid]);src=Path(c['root']);dest=r/'inputs'/cid;dest.mkdir(parents=True)
    for p in src.rglob('*'):
        if p.is_file() and (p.suffix=='.bin' and p.stem in ['Q','K','V','mask'] or p.name in ['snapshot.json','INPUT.json']):
            target=dest/p.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);assert sha(target)==sha(p)
    for row in c['inputs']:assert sha(dest/row['name'])==row['sha256']
    c['root']=str(dest);c['serial_roots']=[str(dest/f'serial{j}') for j in range(c['q'])]
    c['references']={l:dict(path=str(dest/'ordinary_reference.bin'),sha256=None) for l in ['PQ','QB','QH_C']}
    selected[cid]=c
save(r/'INPUTS.json',selected)
save(r/'INPUT_PROVENANCE.json',dict(parent_input_index_sha256=sha(OLD/'INPUTS.json'),parent_freeze_sha256=sha(OLD/'FREEZE.json'),parent_closed_sha256=sha(OLD/'GPU_EXECUTION_CLOSED.json'),selected_cases=ids,all_full_inputs_exact=True,old_outputs_imported=False,GPU_calls=0))
(V/'build').mkdir()
for name in ['libggml.dll.a','libggml-base.dll.a']:shutil.copyfile(Path('D:/hs121')/P.relative_to(V.parents[1])/ 'build'/name,V/'build'/name)
print(r,flush=True)
