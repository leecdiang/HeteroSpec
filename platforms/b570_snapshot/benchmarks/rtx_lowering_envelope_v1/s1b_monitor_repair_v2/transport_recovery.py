"""Bounded CPU network publication after a preserved connect failure;no experiment retry."""
import time
from common import V,load,save,env
from transport_lifecycle import TransportChild

def main():
    f=load(V/'F0.json');d=V/'cpu_raw/publication_final/transport-connect-recovery';d.mkdir(exist_ok=False);begin=time.monotonic_ns();error=None
    cmd=[f['git']['path'],'-C',f['repository'],'-c','http.version=HTTP/1.1','push','origin',f['branch']]
    save(d/'CPU_TRANSPORT_STARTED.json',dict(command=cmd,reason='prior GitHub443 connect failure,oldreceipt retained',run_id=f['run_id'],execution_id=f['execution_id'],GPU_starts=0))
    w=TransportChild(f['console_helper'],f['CPU_transport_executables'])
    try:w.run(cmd,d/'push',60,env(''),512*1024**2)
    except BaseException as e:error=repr(e);raise
    finally:
        w.terminate();seconds=(time.monotonic_ns()-begin)/1e9
        save(d/'CPU_TRANSPORT_ENDED.json',dict(seconds=seconds,conservative_owned_seconds=17*seconds,error=error,experiment_retry=False,GPU_queries=0,CUDA_loads=0,graph_calls=0))
if __name__=='__main__':main()
