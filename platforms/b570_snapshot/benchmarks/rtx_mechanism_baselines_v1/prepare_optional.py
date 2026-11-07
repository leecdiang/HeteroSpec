"""Exact CPU input copy for optional compact q4, no scientific outputs imported."""
import copy,shutil
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
def main():
    r=root();old=load(Path('D:/hs121-0cd72634-266d-4b57-9b00-1d7df2327735/INPUTS.json'));rows=load(r/'INPUTS.json')
    for v in [0,1]:
        cid=f'q4-compact-v{v}';c=copy.deepcopy(old[cid]);src=Path(c['root']);dest=r/'inputs'/cid;dest.mkdir()
        for row in c['inputs']:shutil.copyfile(src/row['name'],dest/row['name']);assert sha(dest/row['name'])==row['sha256']
        c.update(root=str(dest),serial_roots=[],references={l:dict(path=str(dest/'ordinary_reference.bin'),sha256=None) for l in ['PQ','QB','QH_C']});rows[cid]=c
    save(r/'INPUTS_INITIAL.json',load(r/'INPUTS.json'))
    # CPU preparation revision precedes execution freeze; initial exact index retained.
    (r/'INPUTS.json').rename(r/'INPUTS_PRE_OPTIONAL.json');save(r/'INPUTS.json',rows)
if __name__=='__main__':main()
