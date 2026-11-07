"""Map observed GGUF tensor types to proposed arithmetic recipes, without bypasses."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared'))
from experiment import read,save,require

def review(inventory,recipes):
    table=recipes['recipes'];out=[]
    for tensor in inventory['tensors']:
        key=str(tensor['type']);recipe=table.get(key)
        status='NO_RECIPE'
        if recipe:
            require(recipe.get('source_sha256') and recipe.get('activation_input'),'Incomplete arithmetic recipe declaration')
            status='PROPOSED_NOT_QUALIFIED'
        out.append(dict(name=tensor['name'],shape=tensor['shape'],type=key,recipe=recipe,status=status))
    return dict(tensors=out,actual_types=inventory['tensor_type_counts'],numeric_qualified=False,
                rule='Never change a Q8 guard to admit another type without native arithmetic/replay qualification')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('inventory');p.add_argument('recipes');p.add_argument('out');a=p.parse_args();save(a.out,review(read(a.inventory),read(a.recipes)))
