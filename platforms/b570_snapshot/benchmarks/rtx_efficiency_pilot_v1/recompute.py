"""CPU-only independent recomputation of the public outcome summaries."""
import csv
import json
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parent

def main():
    records=json.loads((ROOT/'TOKEN_OUTCOMES.json').read_text(encoding='utf-8'))['records']
    runs=json.loads((ROOT/'RUNS.json').read_text(encoding='utf-8'))
    indexed={(x['run'],x['round'],x['condition'],x['task']):x for x in records}
    assert len(indexed)==len(records)==300
    for run in runs:
        group=[x for x in records if x['run']==run['run']]
        tasks={x['task'] for x in group}
        assert len(group)==run['measured_requests']
        assert len(group)==len(tasks)*len(run['conditions'])*run['rounds']
        for rnd in range(run['rounds']):
            for cond in run['conditions']:
                for task in tasks:
                    assert (run['run'],rnd,cond,task) in indexed
    def identity(x):
        return x['ids'],x['stop_type'],x['stopping_word'],x['truncated']
    with (ROOT/'SUMMARY.csv').open(encoding='utf-8') as f:
        summary=list(csv.DictReader(f))
    for row in summary:
        items=[x for x in records if x['run']==row['run'] and x['condition']==row['condition'] and (x['group']==row['scope'] or x['task']==row['scope'])]
        refs=[indexed[(x['run'],x['round'],'target',x['task'])] for x in items]
        matches=sum(identity(x)==identity(b) for x,b in zip(items,refs))
        assert matches==int(row['exact_matches'])
        assert len(items)==int(row['requests'])
        ratios=[]
        for rnd in range(3):
            rs=[(x,b) for x,b in zip(items,refs) if x['round']==rnd]
            ratios.append(sum(b['wall_ms'] for x,b in rs)/sum(x['wall_ms'] for x,b in rs))
        assert abs(median(ratios)-float(row['median_wall_speedup']))<1e-12
        assert abs(min(ratios)-float(row['min_wall_speedup']))<1e-12
        if row['qualified_speedup']:
            assert matches==len(items) and row['requested_edit_ast_match']!='False'
    assert all(x['cache_n']==0 for x in records)
    print(f'PASS independent CPU recomputation: {len(records)} direct-ID outcomes, six complete matrices, {len(summary)} summary rows')

if __name__=='__main__':main()
