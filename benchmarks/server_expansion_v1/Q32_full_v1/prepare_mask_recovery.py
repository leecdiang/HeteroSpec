"""Correct the diagnostic request mask, without weakening its ownership gate."""
from pathlib import Path
import argparse,shutil
from build import sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--privacy-source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir()
 for name in('build.py','resource_guard.py'):shutil.copy2(a.source/name,a.out/name)
 s=(a.source/'qualification.py').read_text().replace("self.w/'qualification-04'","self.w/'qualification-05'")
 anchor="  for c in cases:\n   n=sum(len(z['ids'])for z in c['forced']);";assert s.count(anchor)==1;s=s.replace(anchor,"  for c in cases:\n   c['forced'][1]['all']=True # Explicitly request every verification row, never fabricate absent vectors\n   n=sum(len(z['ids'])for z in c['forced']);",1)
 anchor="if(prior/'HOST.json').exists()and read(prior/'HOST.json')['status']=='COMPLETE':";assert s.count(anchor)==1;s=s.replace(anchor,"if(prior/'HOST.json').exists()and read(prior/'HOST.json')['status']=='COMPLETE'and read(prior_job)==m:",1);(a.out/'qualification.py').write_text(s)
 s=(a.source/'finish.py').read_text().replace('qualification-04','qualification-05').replace('closure-04','closure-05').replace('FINISH_NOT_ADMITTED-04','FINISH_NOT_ADMITTED-05');(a.out/'finish.py').write_text(s)
 s=(a.privacy_source/'archive.py').read_text().replace('PIPELINE_LAUNCH_04','PIPELINE_LAUNCH_05').replace('PIPELINE_COORDINATOR_CLOSED04','PIPELINE_COORDINATOR_CLOSED05').replace('qualification-04','qualification-05').replace('closure-04','closure-05').replace('finish-04','finish-05').replace("w/'export-05'","w/'export-06'");(a.out/'archive.py').write_text(s)
 shutil.copy2(Path(__file__).parent/'mask_recovery_coordinator.py',a.out/'coordinator.py')
 save(a.out/'ADAPTER_BINDING.json',dict(original_sources={n:sha(a.source/n)for n in('qualification.py','finish.py')},privacy_archive_source_sha256=sha(a.privacy_source/'archive.py'),new_sources={p.name:sha(p)for p in a.out.iterdir()if p.is_file()},changes=['Explicit all=True for every registered forced VERIFY width, unchanged all-row ownership assertion','Recompute scalar R if exact payload differs, no mismatched-job oracle reuse','Same source04 native ELF, numerical core, R and strict vector/KV readers','Supported packed subset only; six-arm performance remains denied; preserve incorrect-mask payload/native results and charged cost']))
if __name__=='__main__':main()
