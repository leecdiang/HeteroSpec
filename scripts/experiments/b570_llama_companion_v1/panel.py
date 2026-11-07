"""Seal a tokenized natural panel after candidate freeze and both-platform exposure review."""
import argparse
from pathlib import Path
from common import digest, read, sha, write, need, utc
from design import select, timing_balance


def make(pool_path, exposure_path, freeze_path, out, count):
    freeze = read(freeze_path);need(freeze.get('frozen_utc'), 'candidate must be frozen first')
    pool = read(pool_path);exposure = read(exposure_path)
    need(exposure.get('complete') is True and exposure.get('unresolved_sources') == [], 'incomplete exposure inventory')
    need(set(exposure.get('platforms', [])) >= {'RTX', 'B570'}, 'both-platform exposure exclusion required')
    rows = select(pool['inputs'], exposure['keys'], count);timing_balance(rows)
    write(out, rows)
    write(str(out)+'.selection.json', {'pool_sha256': sha(pool_path), 'exposure_sha256': sha(exposure_path),
          'candidate_freeze_sha256': sha(freeze_path), 'panel_sha256': sha(out), 'selected_utc': utc(),
          'count': len(rows), 'task_domain_cross_length': True, 'new_model_requests': 0,
          'tokenizer_binding': pool['tokenizer_binding'], 'shared_RTX_panel': False,
          'note': 'Independent Vulkan panel unless separately co-frozen before either platform exposes outputs. Never block the running RTX study.'})
    return rows


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('pool','exposure','freeze','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--count',type=int,default=24,choices=[12,24]);a=p.parse_args();make(a.pool,a.exposure,a.freeze,a.out,a.count)
