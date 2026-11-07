"""Build the prospective artifact set; no model process is launched."""
import datetime, difflib, json, shutil, subprocess, sys
from pathlib import Path
from prepare import ROOT, PR134, PR135, read, write, item, sha

WORKTREE=Path('C:/Users/DIANG/.codex/worktrees/b570-prefill-closeout/HeteroSpec')
RESULT_PATH='benchmarks/b570_prefill_closeout_v1'
def main():
    sys.path.insert(0,str(ROOT/'design'));import toolkit
    write('ORDER.json',toolkit.timing_plan('B570'))
    slots=[]
    for mode,indices,arms in [('E0',range(1),['BASE','SUBMIT']),('E1',range(4),['R','BASE','SUBMIT'])]:
        for i in indices:
            for arm in arms:
                for category in ['capture','count']:
                    slots.append({'slot':f'{mode}/{i}/{arm}/{category}','mode':mode,'index':i,'arm':arm,
                                  'category':category,'input_id':'HumanEval/42' if mode=='E0' else read(ROOT/'INPUT_PANEL.json')['inputs'][i]['id']})
    slots += [dict(x,mode='E2') for x in read(ROOT/'ORDER.json')]
    assert len(slots)==156 and len({x['slot'] for x in slots})==156
    write('REGISTERED_SLOTS.json',slots)
    prefix_old=(PR135/'prefill_submit.cpp').read_text().split('void equivalent(')[0]
    prefix_new=(ROOT/'closeout.cpp').read_text().split('void equivalent(')[0]
    (ROOT/'request_observer_diff.patch').write_text(''.join(difflib.unified_diff(prefix_old.splitlines(True),prefix_new.splitlines(True),fromfile='PR135/qualified-request',tofile='PR141/request-with-expanded-observer')))
    write('CPU_VALIDATION.json',{'status':'PASS','shared_toolkit_distinct_tests':16,
          'native_launched':False,'compiled':'MSVC 19.44.35228.0; /O2 /W4 /fp:precise /utf-8',
          'native_driver_sha256':sha(ROOT/'build/Release/closeout.exe'),
          'compile_cost_boundary':'Included in conservative owned preparation wall since 2026-10-21T10:45:26Z; not isolated compiler CPU seconds.'})
    frozen=[]
    own=['prepare.py','create_driver.py','closeout.cpp','closeout_main.cpp.inc','CMakeLists.txt','run.py','audit.py','freeze.py',
         'INPUT_PANEL.json','ORDER.json','REGISTERED_SLOTS.json','MODEL_RECHECK.json','RUNTIME_MANIFEST.json',
         'REFERENCE_RECOVERY.json','RAW_RECOVERY_MANIFEST.json','HISTORY.json','AUTHORIZATION.json','PREPARATION.json',
         'SOURCE_AUDIT.md','CPU_VALIDATION.json','request_observer_diff.patch']
    for name in own:frozen.append(item(ROOT/name))
    frozen += [item(p) for p in sorted((ROOT/'build/Release').glob('*.dll'))]
    frozen.append(item(ROOT/'build/Release/closeout.exe'))
    frozen += read(ROOT/'MODEL_RECHECK.json')
    frozen += [dict((k,v) for k,v in x.items() if k in ['path','bytes','sha256']) for x in read(ROOT/'RAW_RECOVERY_MANIFEST.json')]
    frozen += [item(PR134/f'qual-{i}/result.json') for i in range(4)]
    frozen += [item(PR134/'INPUT_PANEL.json'),item(PR135/'prefill_submit.cpp'),item(PR135/'BUILD_MANIFEST.json'),
               item(Path('C:/hs/b570-spec-bridge-20261020200000/results/result.json'))]
    frozen += [item(p) for p in sorted((ROOT/'design').glob('*')) if p.is_file()]
    # Directly compile only this host. Header and library identities are part of the receipt.
    for p in [Path('C:/hs/b570-direct-id-v1-src/include/llama.h'),
              Path('C:/hs/b570-direct-id-v1-src/ggml/include/ggml.h'),
              Path('C:/hs/b570-direct-id-v1-src/ggml/include/ggml-backend.h'),
              Path('C:/hs/b570-spec-bridge-20261020200000/build/Release/llama.lib'),
              Path('C:/hs/b570-direct-id-v1-build/ggml/src/Release/ggml.lib'),
              Path('C:/hs/b570-direct-id-v1-build/ggml/src/Release/ggml-base.lib')]:frozen.append(item(p))
    write('FROZEN_FILES.json',frozen)
    dest=WORKTREE/RESULT_PATH;dest.mkdir(parents=True,exist_ok=False)
    for p in ROOT.iterdir():
        if p.is_file() and p.suffix not in ['.zip']:shutil.copy2(p,dest/p.name)
    shutil.copytree(ROOT/'design',dest/'design')
    print(json.dumps({'prepared_path':str(dest),'frozen_files':len(frozen),'slots':len(slots),'native_starts':0}))

if __name__=='__main__':main()
