"""Historical saved-byte reader fixture, explicitly not new GPU qualification."""
import argparse
import struct
from pathlib import Path
from check_numeric import state,vectors
from support import fresh,read


def main():
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--frontier',required=True)
    p.add_argument('--profile',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    profile=read(a.profile);profile=profile.get('Qwen32B',profile)
    with Path(a.state).open('rb')as f:header=f.read(16)
    positions=struct.unpack_from('<I',header,12)[0]
    result=dict(scope='HISTORICAL_READER_FIXTURE_ONLY_NOT_NEW_NUMERIC_QUALIFICATION',
                state=state(a.state,a.state,positions,profile),frontier=vectors(a.frontier,a.frontier,1,151936),
                native_model_requests=0,GPU_initialized=False)
    fresh(a.out,result)


if __name__=='__main__':main()
