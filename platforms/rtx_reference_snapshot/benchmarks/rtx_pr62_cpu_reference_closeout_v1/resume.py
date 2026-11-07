"""Foreground CPU-only stage driver. Whitelisted Python analysis children; no native/model entry."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).parent
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--restored',required=True);p.add_argument('--phase2',required=True);p.add_argument('--phase2-archive',required=True);p.add_argument('--force-cpu',action='store_true');a=p.parse_args()
    args={k:str(Path(v).resolve()) for k,v in vars(a).items() if k!='force_cpu'}
    stages=[('identity.py',['--archive',args['archive'],'--restored',args['restored'],'--phase2',args['phase2'],'--phase2-archive',args['phase2_archive']],['INPUT_BINDINGS.json','UNIT_MANIFEST.json','ARCHIVE_ACCESS.json']),('analyze.py',['--experiment',str(Path(args['restored'])/'experiment')],['COUNTS.json','QUALIFICATION_RECOMPUTED.csv','RAW_COSTS.csv','TASK_COST_PAIRS.csv','ROUND_COST_PAIRS.csv','COST_SUMMARY.json','SESSION_BINDINGS.json','CONDITION_TASK_MEDIANS.csv']),('verify.py',['--experiment',str(Path(args['restored'])/'experiment'),'--archive',args['archive'],'--phase2',args['phase2'],'--phase2-archive',args['phase2_archive']],['INDEPENDENT_VERIFICATION.json','POST_AUDIT.json']),('handoff.py',[],['REPORT.zh-CN.md','PAPER_HANDOFF.md','CLAIM_EVIDENCE_MATRIX.csv','DECISION.json','NEXT_STAGE.md','README.md','SOFTWARE.json','figures/task_speed_pairs.svg','figures/task_speed_pairs.pdf','figures/task_speed_pairs.png','figures/aggregate_and_rounds.svg','figures/aggregate_and_rounds.pdf','figures/aggregate_and_rounds.png'])]
    previous='initial';checkpoint=ROOT/'CHECKPOINT.json';saved=json.loads(checkpoint.read_text()) if checkpoint.exists() else {};now={}
    for script,options,files in stages:
        tag=digest(ROOT/script)+previous+json.dumps(args,sort_keys=True);old=saved.get(script,{})
        valid=not a.force_cpu and old.get('tag')==tag and all((ROOT/f).exists() and digest(ROOT/f)==old.get('outputs',{}).get(f) for f in files)
        if not valid:subprocess.run([sys.executable,str(ROOT/script),*options],check=True)
        hashes={f:digest(ROOT/f) for f in files};now[script]={'tag':tag,'outputs':hashes};previous=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
        tmp=checkpoint.with_suffix('.tmp');tmp.write_text(json.dumps(now,indent=2)+'\n',encoding='utf-8',newline='\n');tmp.replace(checkpoint)
        with (ROOT/'LEDGER.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'stage':script,'status':'REUSED_VERIFIED' if valid else 'COMPLETED_CPU','utc':datetime.now(timezone.utc).isoformat(),'new_model_requests':0})+'\n')
    (ROOT/'STATUS.json').write_text(json.dumps({'stage':'CPU_ANALYSIS_COMPLETE','delivery':'PENDING_OR_SEPARATELY_RECORDED','new_model_requests':0,'new_target_draft_forwards':0,'new_warmups':0},indent=2)+'\n',encoding='utf-8',newline='\n')
if __name__=='__main__':main()
