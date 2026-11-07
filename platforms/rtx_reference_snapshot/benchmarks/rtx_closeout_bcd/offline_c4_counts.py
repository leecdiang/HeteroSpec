"""Count logged native calls and micrograph observations, never CUDA launches."""
import json
from close_base import HERE,save,sha

def main():
    rows=[]
    for directory in sorted((HERE/'runs/c4_pilot').glob('r*')):
        if not directory.is_dir():continue
        path=directory/'trace.jsonl'
        events=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        target=[x for x in events if x['event']=='decode' and x['role']=='target' and x['phase']=='continuation']
        rows.append({'session':directory.name,'target_continuation_calls':len(target),
          'target_continuation_micrograph_observations':sum(sum(g['name']=='attn_norm-0' for g in x['graphs']) for x in target),'trace_sha256':sha(path)})
    assert len(rows)==6
    save(HERE/'generated/C4_WORK_COUNTS.json',{'sessions':rows,
       'scope':'Each diagnostic session includes 28 task requests and one warmup. Counts are native call and graph observations, not CUDA-kernel launch counts or speed measurements. Capture costs are excluded from all performance claims.'})
    print(rows,flush=True)

if __name__=='__main__':main()
