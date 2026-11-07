"""Boundary audit of real input/runtime bytes; never performs model inference."""
import argparse
from pathlib import Path
from study import ROOT, PLAN, SRC, DATA, TARGET, DRAFT, EXE, RUNTIME, V1, read, sha, save, env_identity, utc

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',required=True);a=p.parse_args()
    manifest=read(PLAN/'BUILD_IDENTITY.json');errors=[];assets={}
    for file,expected in [(DATA,V1['dataset']['sha256']),(TARGET,V1['target']['sha256']),(DRAFT,V1['draft']['sha256'])]:
        digest=sha(file);assets[file.name]=digest
        if digest!=expected:errors.append('asset '+file.name)
    binaries={}
    for name,expected in manifest['binaries'].items():
        digest=sha(EXE.parent/name);binaries[name]=digest
        if digest!=expected:errors.append('runtime '+name)
    original=RUNTIME/'llama-speculative.exe';binaries['retained_original_cli']=sha(original)
    if binaries['retained_original_cli']!=V1['binary_hashes'][original.name]:errors.append('original CLI')
    environment=env_identity()
    if environment!=manifest['environment']:errors.append('environment')
    sources={p.name:sha(p) for p in SRC.iterdir() if p.is_file()}
    frozen=PLAN/'FORMAL_FREEZE.json'
    if frozen.exists():
        for name,expected in read(frozen)['source_files'].items():
            if sources.get(name)!=expected:errors.append('formal source '+name)
    save(PLAN/(a.stage+'_INPUT_AUDIT.json'),{'stage':a.stage,'observed_utc':utc(),'errors':errors,
        'assets':assets,'binaries':binaries,'environment':environment,'source_files':sources,
        'build_identity_sha256':sha(PLAN/'BUILD_IDENTITY.json'),'no_inference':True})
    print(a.stage,'real byte/environment audit', 'PASS' if not errors else errors,flush=True)
    raise SystemExit(bool(errors))

if __name__=='__main__':main()
