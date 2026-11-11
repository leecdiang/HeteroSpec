"""Publish this output before any selected natural request is executed."""
from runner import *
def main():
    assert not list(ROOT.glob('science-*/launch.json'))
    assert all(x['vectors_equal'] and x['state_equal'] and x['endpoint_equal'] and x['position_equal'] for x in read(ROOT/'ENGINEERING_CONTROLS.json')['proof'])
    put(ROOT/'schedule.json',schedule())
    files=['coverage.json','exclusions.json','full-schedules.json','selected-inputs.json','schedule.json','INHERITED_IDENTITY.json','ENGINEERING_CONTROLS.json','candidate01/binding.json']
    sources=['audit.py','coverage.py','host.py','runner.py','build.py','engineering.py','worker.cpp','timing-only.diff','PLAN.md','freeze.py']
    put(ROOT/'FREEZE.json',dict(design_head='6987317a4a4d4495fa9f1543bf922d978e13d4f8',scientific_parent='aa7ff4e64752be3de0d7974febbce453ae3a96c0',files={p:sha(ROOT/p) for p in files},sources={p:sha(HERE/p) for p in sources},engineering_requests=14,scientific_requests=160,all_stage_cap=200,model_sha256=read(ROOT/'INHERITED_IDENTITY.json')['model_sha256'],phases=['receipt to synchronized import-ready (file read/index/reset/lookup/import)','import-ready to synchronized append completion (planning/graphs included)','append completion to response commit (continuation included)'],timing='capture-off; same worker for every arm; diagnostic serialization after response commit excluded; host wall retained',setup='model load/context creation and original reference snapshot producer separately retained',admission='Identical PR174 C4096 native configuration; free before campaign: GPU11931MiB/RAM33954724KiB; disk>20GiB per launch',no_retries=True,scope='8 conditioned unexposed natural roots; no population-average claim; PR174 AUTO null unchanged'))
    evidence=HERE/'evidence';evidence.mkdir()
    for p in files+['FREEZE.json']:
        dest=evidence/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dest)
    print(sha(ROOT/'FREEZE.json'))
if __name__=='__main__':main()
