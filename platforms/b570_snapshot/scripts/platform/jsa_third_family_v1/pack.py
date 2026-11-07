"""Scientific CPU bundle and separate full private-core author archive; no weights/DLLs."""
from common import *
import zipfile
OUTPUT=REPO.parent.parent/'outputs'
def scientific():
    files={}
    for root,prefix in [(PUB,'repository/benchmarks/jsa_third_family_v1'),(Path(__file__).parent,'repository/scripts/platform/jsa_third_family_v1'),(DESIGN,'repository/docs/experiments/jsa_third_family_20261011')]:
        for p in root.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip':files[prefix+'/'+p.relative_to(root).as_posix()]=p
    for dirname in ['runs','static-native/full','zero-load']:
        root=LOCAL/dirname
        for p in root.rglob('*'):
            if p.is_file():files['third-family/'+p.relative_to(LOCAL).as_posix()]=p
    for name in ['EXPOSURE_CATALOG.json','EXPOSURE_CATALOG_HEADS_HOST.json','GIT_HISTORY_TEXT_OBJECTS.json','AVAILABLE_CANDIDATES.json','AVAILABLE_CANDIDATES_HEADS_HOST.json','LLAMA_MEMORY_ADMISSION_01.json','LLAMA_MEMORY_ADMISSION_02.json','PR_HEADS.json','F0A_REMOTE_RECEIPT.json','F0B_REMOTE_RECEIPT.json','native/SOURCE_HASHES.json','native/SOURCE_HASHES_FINAL.json','native/PATCH.json','native/CAPTURE_SHAPE_PATCH.json','native/SERVER_BUILD.json','native/build-server.log','native/capture-shape-build.log']:
        p=LOCAL/name
        if p.exists():files['third-family/'+name]=p
    return files
def archive(path,files):
    assert not path.exists();index={'schema':'heterospec.third_family.archive.v1','files':{name:{'sha256':sha(p),'bytes':p.stat().st_size} for name,p in sorted(files.items())},'weights':'external pinned full hashes, not included','numerical_DLLs':'external unchanged published runtime hashes, not included'}
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('INDEX.json',json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        for name,p in sorted(files.items()):z.write(p,name)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),'logical_files':len(files)}
def main():
    OUTPUT.mkdir(parents=True,exist_ok=True);assert (PUB/'RESULTS.json').exists()
    files=scientific();raw=archive(PUB/'RAW_EVIDENCE.zip',files)
    for p in (LOCAL/'native/source').rglob('*'):
        if p.is_file():files['third-family/native/source/'+p.relative_to(LOCAL/'native/source').as_posix()]=p
    for name in ['llama-server.exe','llama-cli.exe']:files['third-family/native/build/bin/'+name]=LOCAL/'native/build/bin'/name
    files['third-family/native/vocabulary.exe']=LOCAL/'native/vocabulary.exe'
    for dirname in ['preparation-versions','native/version01','native/driver/generated']:
        for p in (LOCAL/dirname).rglob('*'):
            if p.is_file() and p.suffix not in ['.obj','.o','.dll','.a']:files['third-family/'+p.relative_to(LOCAL).as_posix()]=p
    full=archive(OUTPUT/'HeteroSpec_RTX_三家族同日实验_完整记录.zip',files)
    save(PUB/'ARCHIVE_MANIFEST.json',{'raw_scientific':raw,'private_author_archive':full,'upstream':read(PUB/'NATIVE_BUILD.json')['patch']['upstream'],'private_source_files':len(read(LOCAL/'native/SOURCE_HASHES_FINAL.json')),'models_not_included':True,'numerical_DLLs_not_included':True,'CPU_reproduce':'restore ZIP in a fresh directory, run repository/scripts/platform/jsa_third_family_v1/analyse.py, compare byte SHA256 with RESULTS.json','original_PR80_archive_binding':read(PUB/'NATIVE_BUILD.json')['patch']['restored_archive_sha256'],'utc':now()})
    print(json.dumps({'raw':raw,'author':full}),flush=True)
if __name__=='__main__':main()
