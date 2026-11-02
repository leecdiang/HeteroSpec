"""Seal once, qualify completely, enforce independent full vectors, then all costs."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha,digest,utc
import host,design
from independent_qualification import audit as independently_qualify
from independent_cost import audit as independently_cost

def run(epoch,panel,out):
    epoch=Path(epoch);panel=Path(panel);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    c=host.check(epoch,full=True);frozen=read(epoch/'FREEZE.json');selection=read(str(panel)+'.selection.json');rows=read(panel)
    need(selection['panel_sha256']==sha(panel) and selection['candidate_freeze_sha256']==sha(epoch/'FREEZE.json') and selection['new_model_requests']==0 and len(rows)==24,'prospective frozen 24 panel')
    need(not(epoch/'PANEL_SEAL.json').exists(),'fresh unseen confirmation only')
    exposure=Path(c['research_root'])/'EXPOSURE.jsonl';prior=[json.loads(line) for line in exposure.read_text(encoding='utf-8').splitlines()];ids={x['id'] for x in prior};tokens={x['prompt_ids_sha256'] for x in prior}
    need(all(x['id'] not in ids and digest(x['prompt_ids']) not in tokens for x in rows),'already exposed panel')
    need(frozen['epoch_sha256']==sha(epoch/'EPOCH.json'),'freeze identity')
    write(epoch/'PANEL_SEAL.json',{'panel_sha256':sha(panel),'selected_after_freeze':True,'utc':utc(),'cross_project_exclusion_report':frozen['review']['cross_project_exposure_audit']})
    host.execute(epoch,'confirm-oracle',design.references(rows),oracle=True)
    host.execute(epoch,'confirm-candidate',design.qualification(rows))
    independently_qualify(epoch,panel,out/'INDEPENDENT_QUALIFICATION.json')
    # The registered host revalidates its exact matrix and runs all six original
    # Williams periods. The independent gate above forbids timing after any
    # committed-vector failure, even when all endpoint tokens happen to agree.
    host.confirm(epoch,panel)
    independently_cost(epoch,panel,out/'INDEPENDENT_COST.json')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('epoch','panel','out'):p.add_argument('--'+k,required=True)
    a=p.parse_args();run(a.epoch,a.panel,a.out)
