"""One of three fixed rounds; author already authorized all normal gate passages."""
import argparse,subprocess,sys
from common import HERE,DESIGN,BASE,load,sha,need
p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--round',type=int,required=True);a=p.parse_args()
f=DESIGN/'results/CONFIRMATION_FREEZE.json';need(sha(f)==a.freeze,'exact prospective freeze required');cfg=load(f);row=cfg['rounds'][a.round]
need(all(sha(r['path'])==r['sha256'] for r in cfg['external_cpu_files']),'frozen CPU runtime/toolchain drift')
args=[sys.executable,'-B',str(HERE/'run_dev.py'),'--id',row['id'],'--revision',str(cfg['final_development_revision']),'--round',str(a.round),'--order',row['order'],'--freeze',a.freeze]
raise SystemExit(subprocess.run(args).returncode)
