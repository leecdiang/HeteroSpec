"""Pure logical registry generation and semantic validation against fixed PR103 bytes."""
import copy,collections
from pathlib import Path
from pinned_sources import *
C=load('contracts');S=load('state_distance')

def key(c):return c['task'],c['recipient'],c['state']
def label(c):return c['state']+'@'+c['recipient']
def kvkey(c):return c['task']+'|'+label(c)
def logkey(c):return c['task']+'|recipient_'+c['recipient']
def spec_equal(a,b):return {'path','bytes','sha256'}<=set(a) and {'path','bytes','sha256'}<=set(b) and a['bytes']==b['bytes'] and a['sha256']==b['sha256'] and Path(a['path']).resolve()==Path(b['path']).resolve()
def insert(entries,k,v):require(k not in entries,'duplicate logical registry key: '+k);entries[k]=v

def build_registry(cells):
 """Order-invariant pure function; 56 logical KV entries even when CAS SHA repeats."""
 entries={};initial={};sources=collections.defaultdict(list);seen=set()
 for c in cells:
  require(key(c) not in seen,'duplicate logical cell');seen.add(key(c));require(c['donor']==('B' if c['recipient']=='A' else 'A'),'wrong donor direction')
  insert(entries,kvkey(c),{'KV':copy.deepcopy(c['mixture_spec']),'logical':{k:c[k] for k in ('task','recipient','state','donor','direction')}})
  lk=logkey(c);pin=c['initial_logits_spec'];require(lk not in initial or spec_equal(initial[lk],pin),'recipient logits differ across seven states');initial[lk]=copy.deepcopy(pin);sources[lk].append(kvkey(c))
 for lk,pin in initial.items():insert(entries,lk,{'logits':pin,'referenced_by':sorted(sources[lk])})
 return {'schema':2,'logical_KV_cells':len(seen),'recipient_logit_entries':len(initial),'entries':dict(sorted(entries.items()))}

class PayloadReader:
 def __init__(self):self.cache={};self.reads={}
 def __call__(self,spec):
  k=(str(Path(spec['path']).resolve()),spec['bytes'],spec['sha256'])
  if k not in self.cache:
   p=Path(spec['path']);require(p.stat().st_size==spec['bytes'] and sha(p)==spec['sha256'],'payload changed: '+str(p));self.cache[k]=p.read_bytes();self.reads[k[0]]=spec['sha256']
  return self.cache[k]

def registry_mismatches(plan,reg):
 entries=reg.get('entries',reg);bad=[]
 for c in plan['cells']:
  name=kvkey(c) if reg.get('schema')==2 else c['task']+'|'+c['state'];e=entries.get(name)
  if e is None or not spec_equal(e.get('KV',{}),c['mixture_spec']):bad.append({'task':c['task'],'recipient':c['recipient'],'state':c['state'],'lookup':name,'expected_sha256':c['mixture_spec']['sha256'],'actual_sha256':None if e is None else e.get('KV',{}).get('sha256')})
 return bad

def validate_registry_against_plan(plan,reg,audit,reader=None):
 C.validate_new_plan(plan);cells=plan['cells'];expected={(t,r,s) for t in C.CASES for r in ('A','B') for s in C.STATES};require(len(cells)==56 and {key(c) for c in cells}==expected,'missing/extra/duplicate logical cells');bad=registry_mismatches(plan,reg);require(not bad,'registry mismatched logical cells: '+str(len(bad)))
 entries=reg['entries'];expected_keys={kvkey(c) for c in cells}|{logkey(c) for c in cells};require(set(entries)==expected_keys and reg['logical_KV_cells']==56 and reg['recipient_logit_entries']==8,'missing/extra logical registry entries');lookup={key(c):c for c in cells};fixed={(r['task'],r['recipient'],r['selector']):r for r in audit['rows'] if r['repeat']==0};reader=reader or PayloadReader();groups=collections.defaultdict(list)
 for c in cells:
  e=entries[kvkey(c)];require(e['logical']=={k:c[k] for k in ('task','recipient','state','donor','direction')},'registry coordinate changed');require(c['direction']==c['donor']+'->'+c['recipient'],'wrong direction');require(spec_equal(entries[logkey(c)]['logits'],c['initial_logits_spec']),'recipient initial logits swap');groups[logkey(c)].append(kvkey(c));ref=fixed[key(c)];require(c['mixture_spec']['sha256']==ref['mixture_spec']['sha256'] and c['mixture_spec']['bytes']==ref['mixture_spec']['bytes'] and c['initial_logits_spec']['sha256']==ref['initial_logits_spec']['sha256'],'mixture/initial is not fixed PR103 coordinate')
  actual=reader(e['KV']);reader(entries[logkey(c)]['logits']);own=reader(lookup[(c['task'],c['recipient'],'EMPTY')]['mixture_spec']);other='B' if c['recipient']=='A' else 'A';donor=reader(lookup[(c['task'],other,'EMPTY')]['mixture_spec']);require(actual==S.splice(own,donor,len(c['prompt_ids']),c['state']),'EMPTY/ALL/subset imported bytes wrong');require(c['reference_endpoint']==ref['endpoint'],'reference endpoint drift')
 for k,names in groups.items():require(entries[k]['referenced_by']==sorted(names),'missing/extra initial-logits source relationships')
 for s in plan['requests']:
  c=lookup[key(s)];require(all(s[k]==c[k] for k in ('task','recipient','donor','state','direction','cuts','prompt_ids','mixture_spec','initial_logits_spec','reference_endpoint','reference_old_slots')),'request/cell mismatch')
  stage=('anchor_' if s['state'] in ('EMPTY','ALL') else 'subset_')+s['mode'];require(s['stage']==stage and (s['mode']=='heavy' or s['repeat']==0),'wrong stage/mode/repeat');require(spec_equal(entries[kvkey(s)]['KV'],s['mixture_spec']) and spec_equal(entries[logkey(s)]['logits'],s['initial_logits_spec']),'slot registry lookup differs')
 for stage,n in [('anchor_counts',16),('anchor_heavy',32),('subset_counts',40),('subset_heavy',80)]:
  rr=[r for r in plan['requests'] if r['stage']==stage];require(len(rr)==n and sorted(r['order'] for r in rr)==list(range(n)),'stage/order budget')
 return {'logical_cells':56,'requests':168,'logical_registry_entries':64,'all_source_bytes_checked':True,'selected_identity':'EMPTY=recipient; ALL=other recipient full KV; all states retain recipient initial logits','physical_payloads_may_deduplicate':True}
