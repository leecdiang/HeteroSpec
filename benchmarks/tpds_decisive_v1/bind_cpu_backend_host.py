"""Version the complete runtime without overwriting the failed no-CPU bundle."""
from operator_host import *

def main():
    cpu=OP/'cpu-v2/bin/ggml-cpu.dll';assert cpu.exists()
    for arm in ('original','graph_tiles','backend_loop4','packed'):
        for kind,previous,version,receipt in [('driver',4,5,'RUNTIME_BINDING.json'),('service',3,4,'BUILD.json')]:
            old=OP/(arm+'-'+kind+'-v'+str(previous));new=OP/(arm+'-'+kind+'-v'+str(version));new.mkdir();(new/'bin').mkdir()
            for p in old.iterdir():
                if p.is_file() and p.name!=receipt:shutil.copy2(p,new/p.name)
            for p in (old/'bin').iterdir():
                if p.is_file():os.link(p,new/'bin'/p.name)
            binding=json.loads((old/receipt).read_bytes())
            binding['previous_binding']=dict(path=str(old/receipt),sha256=sha(old/receipt))
            binding['runtime_change']='none' if arm=='original' else 'add shared CPU host-buffer backend; CUDA, ggml-base, core and executable unchanged'
            if arm!='original':
                os.link(cpu,new/'bin'/cpu.name);binding['modules'][cpu.name]=sha(cpu)
            put(new/receipt,binding)

if __name__=='__main__':main()
