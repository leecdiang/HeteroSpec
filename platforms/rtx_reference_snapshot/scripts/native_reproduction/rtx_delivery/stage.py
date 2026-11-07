"""Repeat real q3 fixture through original and clean rebuilt replay, check bytes."""
import argparse,json,pathlib,shutil,subprocess,time
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from rtx_recover import sha,read,save
P=pathlib.Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=P);a=ap.parse_args();root=a.root.resolve()
    out=root/'stage-replays';out.mkdir(exist_ok=False);fixture=root/'stage-fixture';registry=read(root/'STAGE_ORIGIN.json')['registry'];rows=[]
    expected=root/'stage-expected'
    for build in ('original/native','clean-build'):
        for arm in ('MQ','PQ','QB'):
            for repeat in range(2):
                label=build.replace('/','-')+'-'+arm+'-r'+str(repeat);dest=out/label
                assert all(sha(fixture/n)==h for n,h in registry.items())
                cmd=[root/build/'bin/querylayout-replay.exe',fixture,arm,dest,root/build/'bin'];start=time.perf_counter()
                with (out/(label+'.log')).open('wb') as f:p=subprocess.Popen(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT);rc=p.wait(timeout=120)
                assert all(sha(fixture/n)==h for n,h in registry.items())
                match={s:rc==0 and (dest/(s+'.bin')).read_bytes()==(expected/(arm+'-r0')/(s+'.bin')).read_bytes() for s in ('QK','softmax','AV')}
                rows.append(dict(label=label,pid=p.pid,exit_code=rc,seconds=time.perf_counter()-start,argv=list(map(str,cmd)),stage_matches=match,input_before_after=True));save(out/'RECEIPTS.json',rows)
                print(label,rc,match,flush=True)
    save(root/'STAGE_RESULT.json',dict(status='PASS' if all(all(r['stage_matches'].values()) for r in rows) else 'FAIL',coordinate='Qwen_l00_prefill_q3',comparison='all three stages against authenticated E1 repeated own-arm outputs; MQ own path and PQ/QB identity also checked',pq_qb_equal=all((expected/'PQ-r0'/(s+'.bin')).read_bytes()==(expected/'QB-r0'/(s+'.bin')).read_bytes() for s in ('QK','softmax','AV')),mq_own=all((fixture/('native_'+s+'.bin')).read_bytes()==(expected/'MQ-r0'/(s+'.bin')).read_bytes() for s in ('QK','softmax','AV')),rows=rows))
if __name__=='__main__':main()
