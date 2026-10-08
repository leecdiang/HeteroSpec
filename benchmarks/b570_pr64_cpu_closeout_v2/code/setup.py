"""Bind an existing read-only PR64 restore; does not restore bulk or load a model."""
import argparse,pathlib,json,zipfile,hashlib
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--archive',required=True);p.add_argument('--restore',required=True);a=p.parse_args()
r=pathlib.Path(a.root);(r/'private').mkdir(parents=True,exist_ok=True)
with open(a.archive,'rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
assert h=='6840d4d6f179564b57ef7c5b994da62c6b2e1d51b606f8a9cfbb8f91c26646fb'
with zipfile.ZipFile(a.archive) as z:(r/'private/CAS_INDEX.json').write_bytes(z.read('INDEX.json'))
(r/'CONFIG.json').write_text(json.dumps(dict(study_root=str(r),read_only_restore=a.restore,archive=a.archive,archive_sha256=h,PR64='68421206452c22caef19c9fb34452cb04a3f99b3',PR63='66594b349955e66146702325559c26019ea16485',main='e87291d26df32f2cb9571e005ab173b1c7a6830b',new_model_requests=0,new_forward=0,new_warmup=0),indent=2),encoding='utf-8')
print('Set HS_CPU_ROOT to',r,'then run evidence.py once and resume.py. PR63 restore path follows the original Stage0 receipt; see README for rebinding on another host.')
