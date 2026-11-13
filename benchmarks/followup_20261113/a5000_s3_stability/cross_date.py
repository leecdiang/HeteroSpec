"""Compare retained R0 sentinel trajectories across completed dates; CPU only."""
import argparse
import datetime as dt
import json
from pathlib import Path
import sys


def compare(config, out):
    if out.exists():
        raise ValueError('Fresh evidence path required')
    c = json.loads(config.read_text())
    root = Path(c['output_root'])
    def read(path):
        return json.loads(path.read_text())
    first = read(root / 'R1/STATUS.json')
    second = read(root / 'R2/STATUS.json')
    if first['status'] != 'COMPLETE' or second['status'] != 'COMPLETE':
        raise ValueError('Both completed dates required')
    starts = [read(root / p / 'START.json') for p in ('R1', 'R2')]
    if starts[0]['source_commit'] != starts[1]['source_commit']:
        raise ValueError('Different dated controllers')
    gap = (dt.datetime.fromisoformat(starts[1]['utc']) - dt.datetime.fromisoformat(first['utc'])).total_seconds()
    if gap < 86400:
        raise ValueError('R2 began less than 24h after completed R1')
    sys.path.insert(0, str(Path(c['original_source']) / 'execution_s3_v1'))
    from verify import repeated_R
    roots = read(Path(c['plans']) / 'R1/MANIFEST.json')['roots']['inputs']
    references = [read(root / p / 'ORACLES.json') for p in ('R1', 'R2')]
    profile = read(Path(c['state_profile']))
    result = dict(status='RUNNING', model_calls=0, gap_from_completed_R1_s=gap,
                  scope='Two fixed sentinel R0 trajectories; original complete repeated_R reader', roots={})
    try:
        for slot in (0, 6):
            service = dict(id=f'new-root{slot:02d}', input=roots[slot])
            proof = repeated_R(references[0][str(slot)], references[1][str(slot)], service, profile)
            result['roots'][str(slot)] = dict(root_id=roots[slot]['id'], proof=proof)
        result['status'] = 'COMPLETE_CROSS_DATE_REFERENCE_PASS'
    except BaseException as exc:
        result.update(status='FAILED', error=str(exc))
        raise
    finally:
        with out.open('x') as f:
            json.dump(result, f, indent=2, allow_nan=False)
            f.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    compare(args.config, args.out)
