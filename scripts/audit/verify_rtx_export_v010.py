#!/usr/bin/env python3
"""Recompute finite RTX comparisons from the anonymous complete-array export.

This validates exported committed output data, not raw logger integrity, runtime
binary identity, historical timing or independent absolute execution chronology.
The companion raw audit retains that provenance separately.
"""
import argparse,collections,json,pathlib

def main():
    p=argparse.ArgumentParser();p.add_argument('--arrays',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path);a=p.parse_args()
    data=json.loads(a.arrays.read_text());rows=data['records'];assert len(rows)==645
    table={(r['task'],r['condition'],r['rep']):r for r in rows};assert len(table)==645
    tasks=sorted({r['task'] for r in rows});assert len(tasks)==43
    assert set(table)=={(t,c,r) for t in tasks for c in ['R','H0','H1','N0','N1'] for r in [1,2,3]}
    eog={128247,151643,151645,151662,151663,151664}
    for r in rows:
        ids=r['ids'];assert ids and len(ids)<=128 and all(type(i)==int and 0<=i<151936 for i in ids)
        assert not any(i in eog for i in ids[:-1]);terminal=ids[-1] in eog
        assert terminal or len(ids)==128
        assert r['endpoint']==('EOS' if terminal else 'limit') and r['cap']==128 and r['inclusive_eog']==terminal and r['overshoot']==0
    def eq(t,c,d,r):
        x,y=table[t,c,r],table[t,d,r];return x['ids']==y['ids'] and x['endpoint']==y['endpoint']
    taskrows=[]
    for t in tasks:
        for c in ['R','H0','H1','N0','N1']:
            x=table[t,c,1];assert all(table[t,c,r]['ids']==x['ids'] and table[t,c,r]['endpoint']==x['endpoint'] for r in [2,3])
        counts={c+'/'+d:sum(eq(t,c,d,r) for r in [1,2,3]) for c,d in [('H0','N0'),('H1','N1'),('N0','R'),('N1','R'),('N0','N1')]}
        before,after=counts['N0/R'],counts['N1/R']
        transition='match_to_match' if before==after==3 else 'mismatch_to_match' if after==3 else 'match_to_mismatch' if before==3 else 'mismatch_to_mismatch'
        taskrows.append({'task':t,'cohort':'old19' if t.startswith('HumanEval/') else 'new24','matches':counts,'transition':transition,'output_noop':counts['N0/N1']==3})
    groups={}
    for cohort in ['old19','new24']:
        sub=[r for r in taskrows if r['cohort']==cohort]
        groups[cohort]={'tasks':len(sub),'observations_per_comparison':3*len(sub),'matches':{k:sum(r['matches'][k] for r in sub) for k in sub[0]['matches']},'transitions':dict(collections.Counter(r['transition'] for r in sub))}
    result={'status':'PASS','units':645,'task_units':43,'groups':groups,'task_rows':taskrows}
    text=json.dumps(result,indent=2)+'\n'
    if a.output:a.output.write_text(text)
    print(text)

if __name__=='__main__':main()
