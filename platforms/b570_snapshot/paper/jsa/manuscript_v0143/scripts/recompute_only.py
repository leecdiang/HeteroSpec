"""Recompute frozen exports while preserving the supplied figures and tables."""
from pathlib import Path
import hashlib,json
from reconstruct import compute
ROOT=Path(__file__).resolve().parents[1]

def main():
    lock=json.loads((ROOT/'provenance/LOCKED_VISUAL_ASSETS.json').read_text())
    for name,wanted in lock['assets'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==wanted,name
    qa,_=compute()
    out=ROOT/'output';out.mkdir(exist_ok=True)
    (out/'NUMERICAL_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
    (out/'FIGURE_INPUTS.json').write_bytes((ROOT/'provenance/FIGURE_INPUTS_V0142.json').read_bytes())
    (out/'ASSET_PRESERVATION_QA.json').write_text(json.dumps(dict(version='v0.14.3',baseline_pr=73,
        unchanged_assets=len(lock['assets']),sha256=lock['assets'],figures_regenerated=False,tables_regenerated=False),indent=2)+'\n')
    print(json.dumps({k:qa[k] for k in ['status','sources','phase_passing_masks','rtx_request_regressions','b570_formal_complete','b570_task_pairs','new_model_requests']},indent=2))

if __name__=='__main__':main()
