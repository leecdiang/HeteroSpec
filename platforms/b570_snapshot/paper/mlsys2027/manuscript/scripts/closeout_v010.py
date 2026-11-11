#!/usr/bin/env python3
"""Package author provenance and bind final deliverables; no circular self hashes."""
import hashlib,json,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];REV=HERE.parent/'reviews/reconstruction_v010';OUT=HERE/'output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert json.loads((REV/'BUILD_QA.json').read_text())['body_pages']==10
 assert json.loads((REV/'PDF_QA.json').read_text())['visual_review']=='PASS'
 for p in ['SYSTEMS','EVIDENCE','CLARITY']:assert (REV/f'reviewers/{p}_INITIAL.md').is_file() and (REV/f'reviewers/{p}_RECHECK.md').is_file()
 files={}
 for p in REV.rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts or p.name.startswith('STAGING_'):continue
  files['reviews/'+p.relative_to(REV).as_posix()]=p
 for p in (HERE.parents[2]/'scripts/audit').glob('*.py'):files['programs/'+p.name]=p
 for p in HERE.joinpath('scripts').glob('*v010.py'):files['document-programs/'+p.name]=p
 author=OUT/'author-evidence-packet-v0.10.0.zip'
 with zipfile.ZipFile(author,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,p in sorted(files.items()):z.write(p,n)
  z.writestr('SHA256SUMS.json',json.dumps({n:sha(p) for n,p in sorted(files.items())},indent=2)+'\n')
  z.writestr('README.md','''# Author evidence packet v0.10.0
Private source paths and repository provenance are retained; this is not the anonymous submission packet.
Contains full independent audit outputs, inventories, attempt/source/hash mappings, all exported intervention arrays and selected complete raw captures; exact initial/final manuscript review packets and independent simulation reports; document/numeric/provenance QA. Raw code and capsules absent from the compact package remain traceable to original repository/Actions artifacts described in rtx/REVIEW_REPORT.md and COVERAGE.json. This packet is not the entire1.2GBraw archive, and supplies no omitted model/runtime binary bytes or trusted absolute clock. No inference was rerun.
SHA256SUMS binds every preexisting member. README and manifest have no circular self hashes. Final artifact manifest outside this ZIP binds the ZIP itself. Run standard ZIP member hashing first; scientific export verification is inside the final review packet's anonymous ZIP. Original reviewers retain initial scores; rechecks do not seek upgraded ratings.
''')
 # Verify persisted ZIP membership and bytes.
 with zipfile.ZipFile(author) as z:
  manifest=json.loads(z.read('SHA256SUMS.json'))
  assert set(manifest)|{'SHA256SUMS.json','README.md'}==set(z.namelist())
  for n,h in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 deliverables=['manuscript-v0.10.0.pdf','appendix-v0.10.0.pdf','overleaf-intervention-reconstruction-v0.10.0.zip','anonymous-intervention-evidence-v0.10.0.zip','author-evidence-packet-v0.10.0.zip']
 source_files=[p for folder in ['sections','tables','figures/intervention_v010','scripts'] for p in (HERE/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and ('v010' in str(p) or 'intervention_v010' in str(p))]
 m={'version':'v0.10.0','source_parent':'3a0d3c9eb1c8778141bf546b5cdd25ad1e5243e4','base_branch':'codex/rtx-target-verification-intervention-v1','dependency':'Stacked on open Draft PR53; not yet accepted into main','frozen_tag_commit':'1d3b556c93b477680788dfd1eb0737dfe9eee28c','artifacts':{n:{'bytes':(OUT/n).stat().st_size,'sha256':sha(OUT/n)} for n in deliverables},'new_sources':{p.relative_to(HERE).as_posix():sha(p) for p in source_files},'document_source_sha256':json.loads((REV/'BUILD_QA.json').read_text())['package']['source_files'],'main_pages':{'body':10,'references':2},'appendix_pages':24,'evidence_status':'B570 PASS / RTX QUALIFIED_PASS','limitations':['Offline review: no new model forward','Omitted weight/runtime binary bytes unauthenticated','No trusted absolute experiment clock','No intervention latency or energy measurement','Finite study-specific descriptions/cohorts; shared RTX numerics','Four inherited literature fresh retrievals unavailable, recorded explicitly'],'qa':{n:sha(REV/n) for n in ['BUILD_QA.json','PDF_QA.json','PACKAGE_QA.json','FIGURE_TABLE_QA.json','UNIFIED_RECOMPUTATION_RECEIPT.json','NUMERICAL_QA.log']},'publication':'Draft PR only; no merge, tag movement or release'}
 dest=HERE.parent/'evidence/FINAL_ARTIFACT_MANIFEST_V010.json';dest.parent.mkdir(exist_ok=True);dest.write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'status':'PASS','author_packet_bytes':author.stat().st_size,'artifacts':m['artifacts']}))
if __name__=='__main__':main()
