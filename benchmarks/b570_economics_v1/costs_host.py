"""Complete fixed-panel cost tables; no inclusive-parent double counting."""
from native_host import *
from costs import decompose,economic_identity
import statistics,math

def a1():
 assert (ROOT/'A1_TIMING_COMPLETE.json').exists()
 inputs=read(ROOT/'EXPOSED_INPUTS.json')['inputs'];rows=[]
 for x in read(ROOT/'A1_SCHEDULE.json')['schedule']:
  folder=ROOT/'runs'/x['name'];r=inputs[x['root']]
  old=read(OLD_CAMPAIGN/'runs'/f"{'dev' if r['group']=='development' else 'test'}-{r['index']}-oldR/0.json")
  for j,kind in enumerate(('warmup','measure')):
   p=folder/f'{j}.json';d=read(p);assert (d['prompt_ids'],d['ids'],d['eog'])==(old['prompt_ids'],old['ids'],old['eog'])
   metrics=read(str(p)+'.metrics.json');sidecar=read(str(p)+'.cost.json') if x['mode'] else None
   row=dict(**x,kind=kind,input_id=r['id'],root_id=r['root_id'],metrics_sha256=sha(str(p)+'.metrics.json'),endpoint_equal=True)
   row.update(decompose(metrics['service_ms']/1000,sidecar));rows.append(row)
 groups={}
 for arm in ('M','H1','C4U4'):
  g={}
  for mode in (0,1,2):
   rs=[r for r in rows if r['kind']=='measure' and r['arm']==arm and r['mode']==mode]
   g[str(mode)]=dict(measurements=len(rs),service_s=sum(r['service_s'] for r in rs))
   if mode:
    keys=rs[0]['phase_exclusive_s'].keys();g[str(mode)]['exclusive_phase_totals_s']={k:sum(r['phase_exclusive_s'][k] for r in rs) for k in keys}
  g['mode1_over_mode0']=g['1']['service_s']/g['0']['service_s']
  sync0=[r for r in rows if r['kind']=='measure' and r['arm']==arm and r['mode']==0 and r['root'] in (0,2)]
  g['mode2_over_matched_mode0']=g['2']['service_s']/(sum(r['service_s'] for r in sync0)/2)
  g['root_mode1_over_mode0']={str(i):sum(r['service_s'] for r in rows if r['kind']=='measure' and r['arm']==arm and r['mode']==1 and r['root']==i)/sum(r['service_s'] for r in rows if r['kind']=='measure' and r['arm']==arm and r['mode']==0 and r['root']==i) for i in range(4)}
  groups[arm]=g
 identities=[]
 for i in range(4):
  rs=[r for r in rows if r['kind']=='measure' and r['root']==i and r['mode']==1]
  # Pair by scheduled block; no alternative timing window selected by sign.
  for block in (0,1):
   matched={r['arm']:r for r in rs if f'-b{block}-' in r['name']}
   for arm in ('H1','C4U4'):identities.append(dict(root=i,block=block,arm=arm,**economic_identity(matched['M'],matched[arm])))
 out=dict(status='A1_FIXED_EXPOSED_ALL_COMPLETE',measurements=54,warmups=54,summary=groups,records=rows,descriptive_identities=identities,device_kernel_times=None,draft_sync_s=None,draft_proposal_s=None,draft_continuation='actual combined call; no invented split',timing_subtraction=False)
 write(ROOT/'A1_COSTS.json',out);print(json.dumps(groups,indent=2),flush=True)

if __name__=='__main__':a1()
