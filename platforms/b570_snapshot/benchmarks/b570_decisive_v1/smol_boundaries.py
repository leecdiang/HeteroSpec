"""Bind committed KV to emitted greedy prefixes, including pending terminal IDs."""
from smol_state import *

def verify(a,reference,arm):
 prompt=reference['prompt_ids'];ids=reference['ids'];eog=reference['eog']
 assert (a['prompt_ids'],a['ids'],a['eog'])==(prompt,ids,eog)
 states=a['committed_states'];commits=a['commits'];assert len(commits)==len(ids)
 for i,c in enumerate(commits):assert c['index']==i and c['id']==ids[i] and c['eog']==eog[i]
 if arm=='M':expected=list(range(len(ids)))
 else:
  expected=[]
  for i,c in enumerate(commits):
   if not c['accepted'] or c['eog'] or i==len(ids)-1:
    expected.append(i+1 if c['accepted'] else i)
 assert len(expected)==len(states),(arm,'committed boundary count')
 for n,s in zip(expected,states,strict=True):
  assert s['prefix']==prompt+ids[:n],(arm,'committed state contains uncommitted proposal')
  assert s['position_min']==0 and s['position_max']==len(prompt)+n-1
  assert len(canonical_verified(s['sequence']))==len(prompt)+n
 final=expected[-1];assert final in (len(ids)-1,len(ids))
 suffix=[dict(position=len(prompt)+j,id=ids[j],eog=eog[j]) for j in range(final,len(ids))]
 return dict(arm=arm,committed_boundaries=len(states),every_state_is_a_greedy_emitted_prefix=True,final_materialized_output_tokens=final,final_positioned_unmaterialized_suffix=suffix,terminal_kind='EOG' if eog[-1] else 'CAP128')

def campaign(group):
 from smol_verify import input_row,captures
 rows=[];prefix='dev' if group=='development' else 'test';count=4 if group=='development' else 12
 for index in range(count):
  r=read(SROOT/'campaign02/runs'/f'{prefix}-{index}-oldR/0.json')
  arms=[verify(read(captures(group,index,arm,'heavy')/'1.json'),r,arm) for arm in ('M','H1','C1U1','C4U1','C4U2','C4U4')]
  rows.append(dict(input_id=input_row(group,index)['id'],arms=arms))
 return dict(status='ACTUAL_COMMITTED_PREFIX_AND_PENDING_SUFFIX_PASS',roots=rows)

if __name__=='__main__':write(SROOT/'campaign02'/('BOUNDARIES-'+sys.argv[1]+'.json'),campaign(sys.argv[1]))
