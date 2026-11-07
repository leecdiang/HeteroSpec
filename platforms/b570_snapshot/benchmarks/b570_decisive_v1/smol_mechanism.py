"""Actual caller/physical graph columns and full draft F32 frontier diagnostics."""
from smol_verify import *
from collections import Counter

def mechanism(group,index):
 rows=[];baseline=None
 for arm in ARMS:
  a=read(captures(group,index,arm,'heavy')/'1.json')
  if arm=='M':continue
  ts=[t for t in a['trace'] if t['event']=='decode' and t['role']=='draft' and t['phase']=='prefill']
  continuation=[t for t in a['trace'] if t['event']=='decode' and t['role']=='draft' and t['phase']=='continuation']
  assert all(t['caller_batch_length']==1 for t in continuation)
  columns=Counter(g['ne1'] for t in ts for g in t['graphs'] if g['tensor']=='embd')
  assert columns and max(columns)==(1 if arm in ('H1','C1U1','C4U1') else int(arm[3]))
  vectors=a['draft_prefill_vectors'];assert len(vectors)==1
  path=native_path(vectors[0]['path']);raw=path.read_bytes();values=np.frombuffer(raw,dtype='<f4');assert values.shape==(49152,) and np.isfinite(values).all()
  if arm=='H1':baseline=values.copy()
  difference=np.abs(values.astype(np.float64)-baseline.astype(np.float64))
  rows.append(dict(arm=arm,caller_histogram=dict(sorted(Counter(t['caller_batch_length'] for t in ts).items())),observed_embedding_columns=dict(sorted(columns.items())),graph_scope='Scheduler tensor shape observation, not an asserted kernel identity',only_final_prompt_output=sum(sum(t['logits_requested']) for t in ts)==1,subsequent_draft_callers_are_singleton=True,draft_frontier_sha256=sha(path),draft_F32_different_elements_from_H1=int(np.count_nonzero(values.view('<u4')!=baseline.view('<u4'))),draft_max_abs_difference_from_H1=float(difference.max()),arithmetic_scope='Ordinary physical width can change draft logits/proposals; target T is independently qualified'))
 return dict(input_id=input_row(group,index)['id'],prompt_tokens=len(input_row(group,index)['prompt_ids']),arms=rows,no_performance_screening=True)

if __name__=='__main__':
 group=sys.argv[1];count=4 if group=='development' else 12
 write(SROOT/EPOCH/('MECHANISM-'+group+'.json'),dict(roots=[mechanism(group,i) for i in range(count)]))
