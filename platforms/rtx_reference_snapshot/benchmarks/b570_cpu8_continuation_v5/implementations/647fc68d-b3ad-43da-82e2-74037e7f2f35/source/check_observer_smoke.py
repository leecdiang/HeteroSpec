"""Reconstruct a native observer smoke; does not convert it into review clean."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))

def check(folder,kind,expected_rejection):
    def load(name):return json.loads((folder/name).read_bytes())
    def rows(name):
        raw=(folder/name).read_bytes()
        if not raw.endswith(b'\n'):raise ValueError('partial smoke journal')
        out=[json.loads(s) for s in raw.splitlines()]
        if any(r['seq']!=i+1 for i,r in enumerate(out)):raise ValueError('smoke sequence')
        return out
    es=rows('OS_EVENTS.jsonl');rs=rows('RESOURCES.jsonl')
    starts=[r for r in es if r['event']=='OBSERVER_START']
    if len(starts)!=1 or starts[0]['process_kind']!=kind:raise ValueError('profile binding')
    from observer_policy import profile
    if starts[0]['limits']!=profile(kind,starts[0]['seconds']):raise ValueError('noncanonical resource profile')
    created={};closed={}
    for r in es:
        if r['event']=='PROCESS_CREATE':
            key=(r['pid'],r['created_filetime'])
            if key in created:raise ValueError('duplicate identity')
            created[key]=r
        if r['event']=='PROCESS_CLOSED':
            key=(r['pid'],r['created_filetime'])
            if key in closed or int(r['exit_filetime'])<=int(r['created_filetime']):raise ValueError('exit identity/time')
            closed[key]=r
    if not created or set(created)!=set(closed):raise ValueError('actual exit coverage')
    decisions=[r for r in rs if r['event']=='LIMIT_DECISION']
    from observer_policy import violations
    for r in decisions:
        if r['limits']!=starts[0]['limits'] or violations(r['limits'],r['members'],r['observer_rss'],len(r['job_pids']))!=r['violations']:
            raise ValueError('resource decision reconstruction')
    # A sampled identity is known evidence even when no debug create was received.
    for r in rs:
        for member in r.get('members',[])+r.get('exit_races',[]):
            key=(member['pid'],member.get('created_filetime'))
            if key[1] is not None:
                if key not in created or key not in closed:raise ValueError('sampled identity lacks actual exit')
            elif not any(k[0]==key[0] for k in closed):raise ValueError('unresolved sampled PID')
        if any(not any(key[0]==pid for key in closed) for pid in r.get('job_pids',[])):
            raise ValueError('unresolved Job membership')
    if expected_rejection:
        incomplete=load('INCOMPLETE.json')
        if 'COMMAND_RESOURCE_LIMIT:live_process_count' not in incomplete['error']:raise ValueError('wrong rejection reason')
        if not incomplete['cleanup_confirmed'] or incomplete['unclosed'] or incomplete.get('cleanup_error'):
            raise ValueError('failed smoke cleanup')
        if not any(r['violations']==['live_process_count'] for r in decisions):raise ValueError('wrong/missing control')
        if not any(r['event']=='FAILURE_JOB_EMPTY' and r['active_pids']==[] for r in es):raise ValueError('failure Job closure')
    else:
        receipt=load('RECEIPT.json')
        if receipt['status']!='CLOSED' or receipt['root_exit_code']!=0 or not receipt['all_observed_closed']:
            raise ValueError('healthy observer receipt')
        if len(created)<11 or not any(len(r['members'])>=11 for r in decisions):raise ValueError('ten-helper concurrency not reached')
        if any(r['violations'] for r in decisions):raise ValueError('unexpected limit')
        if not any(r['event']=='JOB_EMPTY' and r['active_pids']==[] for r in es):raise ValueError('Job closure')
    return dict(status='OBSERVER_SMOKE_PASS',kind=kind,expected_rejection=expected_rejection,observed=len(created),closed=len(closed),review_clean=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--folder',required=True);p.add_argument('--kind',choices=['case','review'],required=True)
    p.add_argument('--expect-rejection',action='store_true');a=p.parse_args()
    print(json.dumps(check(Path(a.folder),a.kind,a.expect_rejection)))
if __name__=='__main__':main()
