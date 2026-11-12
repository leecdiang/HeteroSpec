"""Fixed CPU estimands; no model/GPU imports. Synthetic tests are not observations."""
import argparse
import math
import random
from statistics import median
from support import read, fresh, need, normalize


def geometric(values):
    values=list(values)
    return math.exp(sum(math.log(x) for x in values)/len(values))


def percentile(values, p):
    s = sorted(values)
    at = (len(s)-1)*p
    lo = math.floor(at)
    hi = math.ceil(at)
    return s[lo] + (s[hi]-s[lo])*(at-lo)


def threshold(interval):
    lo, hi = interval
    if hi < .99:
        return 'C_at_least_1pct_faster_on_registered_panel'
    if lo > 1/.99:
        return 'B_at_least_1pct_faster_on_registered_panel'
    if lo >= .99 and hi <= 1.01:
        return 'finite_ratio_interval_within_1pct_of_B_not_identical'
    if hi < 1:
        return 'C_direction_only'
    if lo > 1:
        return 'B_direction_only'
    return 'uncertain_not_equivalent'


def analyze(rows, phase):
    rows = normalize(rows, phase)
    measured = [r for r in rows if r['role'] == 'measured']
    lookup = {(r['slot'],r['block'],r['arm']):r['elapsed_s'] for r in measured}
    slots, rounds = (range(4),range(3)) if phase == 'S2' else (range(12),range(4))
    contrasts = []
    for candidate, base in (('C','B'),('B','G'),('C','G')):
        logs = {s: [math.log(lookup[s,b,candidate]/lookup[s,b,base]) for b in rounds] for s in slots}
        root_logs = {s: sum(v)/len(v) for s,v in logs.items()}
        item = dict(candidate=candidate,baseline=base,per_slot_log_ratios=logs,
                    ratio=math.exp(sum(root_logs.values())/len(root_logs)),
                    total_ratio=sum(r['elapsed_s'] for r in measured if r['arm']==candidate)/
                                sum(r['elapsed_s'] for r in measured if r['arm']==base))
        if phase == 'S2':
            item['per_cell_geometric_ratio'] = {s:math.exp(v) for s,v in root_logs.items()}
            item['scope'] = 'four_exposed_cells_descriptive_not_full_model_prediction'
        else:
            rng = random.Random(20261110)
            samples = []
            for _ in range(20000):
                code = [root_logs[rng.randrange(0,6)] for _ in range(6)]
                maths = [root_logs[rng.randrange(6,12)] for _ in range(6)]
                samples.append(math.exp((sum(code)/6+sum(maths)/6)/2))
            tail = .025 if (candidate,base)==('C','B') else .0125
            interval = [percentile(samples,tail),percentile(samples,1-tail)]
            item.update(interval=interval,confidence=.95 if tail==.025 else .975,
                        bootstrap=dict(unit='whole_root_all_four_rounds',strata=[6,6],
                                       replicates=20000,seed=20261110,percentile='linear_R7'),
                        per_root_ratio={s:math.exp(x)for s,x in root_logs.items()},
                        median_root_ratio=median(math.exp(x)for x in root_logs.values()))
            if candidate=='C' and base=='B':
                item['label']=threshold(interval)
        contrasts.append(item)
    return dict(phase=phase,complete=True,measured=len(measured),warmups=len(rows)-len(measured),
                contrasts=contrasts,all_rows=rows,not_new_blind_evidence=phase=='S2',
                operation_and_caller_costs_are_distinct=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--phase',choices=['S2','S3'],required=True)
    p.add_argument('--input',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    fresh(a.out,analyze(read(a.input),a.phase))


if __name__=='__main__':
    main()
