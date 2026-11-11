"""Apply separately switchable Q8 activation and physical-prefix contracts."""
from pathlib import Path
import argparse,json
from reference_q8 import apply as q8
from prefix_extent import apply as prefix

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);a=p.parse_args()
    source=Path(a.source);q8(source);print(json.dumps(prefix(source),indent=2))
