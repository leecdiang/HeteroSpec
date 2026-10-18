"""Publish compact, exact evidence copies; raw telemetry remains local."""
import collections,shutil,statistics as st
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from audit_rtx import csvwrite

def main():
    r=root();arc=Path(str(r)+'-archive');e=V/'execution';e.mkdir(exist_ok=True)
    for name in ['CPU_TESTS_FINAL','CPU_RAW_NEGATIVE','CPU_ULP_TESTS','IDENTITY_AUDIT','ARCHIVAL_AUDIT','RESOURCE_SUMMARY','GPU_EXECUTION_CLOSED','QUERY_AND_FAILURE_ACCOUNTING','PRE_GRAPH_TOOL_FAILURE_0','CPU_PREPARATION_FAILURE_0','CPU_CLOSURE_FORMAT_FAILURE_0']:
        shutil.copyfile(r/(name+'.json'),e/(name+'.json'))
    for name in ['AUDIT','ANALYSIS']:shutil.copyfile(r/'analysis'/(name+'.json'),e/(name+'.json'))
    for name in ['ARCHIVE','FRESH_RECOMPUTE']:shutil.copyfile(arc/(name+'.json'),e/(name+'.json'))
    shutil.copyfile(Path(str(r)+'-fresh')/'RESTORE.json',e/'RESTORE.json')
    shutil.copyfile(r/'analysis/HOST_COSTS.csv',V/'results/HOST_COSTS.csv')
    a=load(r/'analysis/ANALYSIS.json');rows=[]
    for key,x in a['cells'].items():
        if key.endswith('|AA'):rows.append(dict(cell=key.split('|')[0],median_absolute_paired_difference_us=st.median(abs(p['difference_us']) for p in x['pairs']),blocks=x['blocks'],ratio=x['ratio']))
    csvwrite(V/'results/PER_VALUE_AA.csv',rows)
    save(V/'EXACT_ARTIFACTS.json',{p.relative_to(V).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in e.glob('*.json')})
    print('exact published artifacts',len(list(e.glob('*.json'))))
if __name__=='__main__':main()
