"""Non-formal R0: output equivalence and direct boundary qualification."""
import argparse,json
from pathlib import Path
from common import *

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    repo=Path.cwd();target,draft=assets(repo);problems=dataset(repo);a.root.mkdir(parents=True,exist_ok=True)
    result={'schema':'heterospec.b570.direct_id.r0.v1','status':'RUNNING','started':utc(),'pairs':[],'state_reset':[],'eos_tests':[]}
    for task in SANITY:
        prompt=a.root/(task.replace('/','_')+'.txt');prompt.write_text(PREFIX+problems[task]['prompt'],encoding='utf-8',newline='\n')
        for cond in CONDITIONS:
            stem=task.replace('/','_')+'-'+cond
            print(stem,flush=True)
            original=execute(a.root,stem+'-original',command(ORIGINAL,target,draft,prompt,cond),False)
            direct=execute(a.root,stem+'-direct',command(INSTRUMENTED,target,draft,prompt,cond))
            pair={'task_id':task,'condition':cond,'original':original,'instrumented':direct,
                  'stdout_byte_equal':original['stdout_sha256']==direct['stdout_sha256']}
            result['pairs'].append(pair);save(a.root/'R0.json',result)
            if not original['execution_valid'] or not direct['execution_valid'] or not pair['stdout_byte_equal']:
                result['status']='FAIL_STOP_R0';save(a.root/'R0.json',result);raise RuntimeError('R0 no-semantic-change or placement gate failed')
    for cond in CONDITIONS:
        # Re-enter a previous prompt after all other prompts: a new process has no resident request state.
        task=SANITY[0];prompt=a.root/(task.replace('/','_')+'.txt')
        repeated=execute(a.root,'reset-'+cond,command(INSTRUMENTED,target,draft,prompt,cond))
        earlier=next(x['instrumented'] for x in result['pairs'] if x['task_id']==task and x['condition']==cond)
        result['state_reset'].append({'condition':cond,'run':repeated,'exact_to_first':repeated['raw_committed_ids']==earlier['raw_committed_ids']})
    # Mechanistic EOG probe, separate from HumanEval; bias affects only this non-formal termination check.
    prompt=a.root/'eog_probe.txt';prompt.write_text('Hello',encoding='utf-8')
    for cond in CONDITIONS:
        cmd=command(INSTRUMENTED,target,draft,prompt,cond)+['--logit-bias','151645+100']
        row=execute(a.root,'eog-'+cond,cmd)
        result['eos_tests'].append({'condition':cond,'run':row,'pass':row['execution_valid'] and row['eos'] and row['generated_ids']==[151645]})
    result['status']='PASS' if all(x['exact_to_first'] for x in result['state_reset']) and all(x['pass'] for x in result['eos_tests']) else 'FAIL_STOP_R0'
    result['ended']=utc();result['raw_lengths']=[len(x['instrumented']['raw_committed_ids']) for x in result['pairs']]
    result['semantic_lengths']=[x['instrumented']['semantic_output_length'] for x in result['pairs']]
    save(a.root/'R0.json',result);print(json.dumps({'status':result['status'],'raw_lengths':result['raw_lengths'],'semantic_lengths':result['semantic_lengths']}),flush=True)
    if result['status']!='PASS':raise RuntimeError('R0 qualification failed')

if __name__=='__main__': main()
