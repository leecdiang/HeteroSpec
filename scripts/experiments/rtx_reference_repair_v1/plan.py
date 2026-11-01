"""Explicit development, held-out and timing schedules; no execution on import."""
from __future__ import annotations
from common import STUDY, need, valid_input, digest
ARMS={'R':('R',1,1,False,False,0), 'M_PQ':('PQ',1,4,True,False,0),
      'M_QB':('QB',0,4,True,False,0), 'C_PQ':('PQ',1,4,True,True,3),
      'C_QB':('QB',0,4,True,True,3)}
TIMING_ARMS=('R','M_PQ','M_QB','C_PQ_A','C_PQ_B','C_QB')
# No task IDs or token values occur in the candidate policy.
DEVELOPMENT_RECIPES=(('R','native'),('R','reference'),('R','pq'),('R','qb'),
 ('M_PQ','native'),('M_QB','native'),('C_PQ','native'),('C_QB','native'),
 ('M_PQ','reference'),('M_QB','reference'),('C_PQ','reference'),('C_QB','reference'))

def policy_check(p):
    need(set(p)<= {'prefill','rowwise_roles','mechanism','revision'},'policy contains unregistered/task-specific fields')
    need(p.get('prefill') in ('native','reference'),'unknown global producer policy')
    need(type(p.get('rowwise_roles')) is int and 0<=p['rowwise_roles']<=7,'role mask')
    need(bool(p.get('mechanism')),'state proposed mechanism, not only PASS')
    return digest(p)

def slot(panel,i,arm,producer,observer,identifier,category,**more):
    native='C_PQ' if arm in ('C_PQ_A','C_PQ_B') else arm
    scope,sel,ub,scoped,draft,k=ARMS[native];x=panel['inputs'][i];valid_input(x)
    return dict(schema=1,study_id=STUDY,family='Qwen',slot_id=identifier,source_index=i,
      input_id=x['id'],prompt_ids_sha256=x['prompt_ids_sha256'],arm=native,experiment_arm=arm,
      scope=scope,layout_selector=sel,target_ub=ub,target_outputs=ub,scoped_target=scoped,
      draft_enabled=draft,k=k,lifecycle='resident',observer=observer,producer='NATIVE',
      category=category,repair={'prefill':producer,'trace':{'mode':'off'}},**more)

def development(panel):
    need(len(panel['inputs'])==4,'use four retained development inputs')
    return [slot(panel,i,a,p,o,f'dev/i{i:02d}/{a}/{p}/{o}','development')
      for i in range(4) for a,p in DEVELOPMENT_RECIPES for o in ('off','heavy')]

def qualification(panel,policy):
    policy_check(policy);need(len(panel['inputs'])==12,'12 held-out inputs required')
    return [slot(panel,i,a,'native' if a=='R' else policy['prefill'],o,
       f'heldout/i{i:02d}/{a}/{o}','qualification')
       for i in range(12) for a in ARMS for o in ('off','heavy')]

def timing(panel,policy,session):
    policy_check(policy);need(len(panel['inputs'])==12,'12 inputs');need(type(session) is int and 0<=session<4,'session')
    result=[]
    for j in range(12):
        i=(j+session)%12;off=(i+session)%6;order=TIMING_ARMS[off:]+TIMING_ARMS[:off]
        for arm in order:
            for category in ('warmup','measured'):
                result.append(slot(panel,i,arm,'native' if arm=='R' else policy['prefill'],'off',
                    f'formal/s{session}/i{i:02d}/{arm}/{category}',category,session=session))
    return result

def trace_slot(panel,index,arm,producer,reference_ids,prefix_length,trace=None):
    need(arm in ('R','M_PQ','M_QB'),'teacher replay uses ordinary target-only; no fake speculation')
    need(type(prefix_length) is int and 0<=prefix_length<len(reference_ids)<=128,'prefix window')
    s=slot(panel,index,arm,producer,'heavy',f'probe/i{index:02d}/{arm}/{producer}/p{prefix_length}','diagnostic')
    s['repair']['teacher_tokens']=reference_ids[:prefix_length]
    s['repair']['probe']=True
    s['repair']['trace']=trace or {'mode':'tensors','phases':['ORDINARY'],
       'name_regex':r'^(l_out|result_norm|result_output)(-[0-9]+)?$',
       'min_call_position':len(panel['inputs'][index]['prompt_ids'])+max(0,prefix_length-1),
       'max_files':256,'max_bytes':256*1024**2}
    return s

def assert_distinct_panels(dev,test):
    for key in ('id','prompt_ids_sha256','text_sha256'):
        need(all(key in x for x in dev['inputs']+test['inputs']),'missing exposure field '+key)
        values=[x[key] for x in test['inputs']]
        need(len(values)==len(set(values)),'duplicate held-out '+key)
        need(not set(values)&{x[key] for x in dev['inputs']},'development/held-out overlap '+key)
