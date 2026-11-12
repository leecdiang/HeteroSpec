"""Capture actual source and recorded full compile/link recipes, no GPU calls.

No object, archive, model, state or old output is distributed as build input.
The original reference and running experiment directories remain read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


def main(study_root,configuration,model_build,out,implementation):
    sys.path.insert(0,str(implementation/'execution_s3_v1'));sys.path.append(str(implementation/'execution_v1'))
    from public_text import transform
    import archive
    if out.exists():raise ValueError('Fresh source snapshot required')
    out.mkdir(parents=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    c=json.loads(configuration.read_text());build=json.loads((model_build/'BUILD.json').read_text())
    original=Path(build['unchanged_numerical_objects'][0]['path']).parent
    rn=study_root/'run-01/build-R-01/native';cn=study_root/'run-01/build-loop4-01/native'
    ru=json.loads((rn/'compile_commands.json').read_text());cu=json.loads((cn/'compile_commands.json').read_text())
    rs=Path(next(x['file']for x in ru if x['file'].endswith('/llama.cpp'))).parent.parent
    cs_old=Path(next(x['file']for x in cu if x['file'].endswith('/llama.cpp'))).parent.parent
    cs=original/'source';front=model_build/'frontend'
    def ninja(folder,targets):return subprocess.check_output(['ninja','-t','commands',*targets],cwd=folder,text=True).splitlines()
    r_commands=ninja(rn,['bin/transfer-worker'])
    old_link=shlex.split(ninja(cn,['bin/transfer-worker'])[-1]);targets=[x for x in old_link if x.endswith('.a')and not x.startswith('/')]
    c_commands=ninja(cn,targets)
    if any('.rsp'in x for x in r_commands+c_commands):raise ValueError('Response-file expansion needs explicit capture before reconstruction')
    aliases={str(rs):'${R_SOURCE}',str(cs_old):'${C_SOURCE}',str(cs):'${C_SOURCE}',
        str(original.parent/'backend/source'):'${C_SOURCE}',str(study_root/'q32-q4-full-build-04/loop4/source'):'${C_SOURCE}',
        str(front):'${FRONTEND}',str(original/'frontend'):'${FRONTEND}',str(rn):'${R_NATIVE}',str(cn):'${C_NATIVE}',
        str(original/'libllama.a'):'${C_NATIVE}/llama/src/libllama.a',
        str(original.parent/'backend/libggml-cuda.a'):'${C_NATIVE}/llama/ggml/src/ggml-cuda/libggml-cuda.a',
        str(original):'${MODEL_OUT}',str(model_build):'${MODEL_OUT}',str(study_root):'${CACHE}'}
    def mapped(text):
        for old,new in sorted(aliases.items(),key=lambda x:-len(x[0])):text=text.replace(old,new)
        return text
    commands=[]
    for role,cwd,items in [('R',rn,r_commands),('candidate-libraries',cn,c_commands)]:
        for item in items:commands.append(dict(role=role,cwd=mapped(str(cwd)),shell=mapped(item)))
    for label,path in [('model-entry',model_build/'compile-model-entry.command.json'),
                       ('model-counts',original/'compile-model-counts/command.json'),
                       ('model-link',model_build/'link-model-worker.command.json')]:
        item=json.loads(path.read_text());commands.append(dict(role=label,cwd=mapped(item['cwd']),argv=[mapped(x)for x in item['argv']]))
    # Tool binaries are installed SDK requirements, never copied numerical
    # inputs. Record exact identities and resolve them explicitly at rebuild.
    import re
    tools={}
    for item in commands:
        raw=item.get('shell',' '.join(item.get('argv',[])))
        # Executables under the study's tools cache need an installed-tool
        # override rather than a nonexistent compiler in the new build cache.
        for token in shlex.split(raw):
            if Path(token).name in ('cmake','nvcc','c++','g++','cc','gcc','ar','ranlib')and ('/'in token):
                original_tool=token.replace('${CACHE}',str(study_root))
                if Path(original_tool).is_file():tools[token]=dict(basename=Path(token).name,sha256=sha(original_tool),recorded_path=transform(original_tool,study_root))
    for ordinal,old in enumerate(sorted(tools)):
        marker='${TOOL_'+str(ordinal)+'}';tools[old]['marker']=marker
        for item in commands:
            if 'shell'in item:item['shell']=item['shell'].replace(old,marker)
            if 'argv'in item:item['argv']=[x.replace(old,marker)for x in item['argv']]
    text_suffixes={'.c','.cc','.cpp','.cxx','.h','.hpp','.hxx','.cu','.cuh','.inc','.inl','.ipp','.tpp','.in','.cmake','.S','.s','.asm','.def','.py','.sh','.cl','.metal'}
    files=[];origins=[];unused_private_shaped=[]
    required=set(Path(x['file'])for x in ru)
    for x in cu:
        path=Path(x['file'])
        required.add(cs/path.relative_to(cs_old)if path.is_relative_to(cs_old)else path)
    closure=json.loads(Path(c['compiled_closure']).read_text())
    candidate_aliases=[cs_old,cs,original.parent/'backend/source',study_root/'q32-q4-full-build-04/loop4/source']
    for name in closure['files']:
        path=Path(name);translated=False
        for alias in candidate_aliases:
            if path.is_relative_to(alias):required.add(cs/path.relative_to(alias));translated=True;break
        if not translated:required.add(path)
    def add(path,relative):
        if path.is_symlink():path=path.resolve()
        original=path.read_bytes();text=original.decode('utf8');templated=False
        try:reviewed=transform(text,study_root)
        except ValueError:
            if path not in required:
                unused_private_shaped.append(dict(path=relative,sha256=hashlib.sha256(original).hexdigest(),bytes=len(original),
                    scope='Uncompiled upstream example/test material with private-address-shaped literals; source retained privately, not needed by recorded build'))
                return
            raise ValueError('Compiled source needs explicit literal review: '+str(path))
        if reviewed!=text:
            text=mapped(text).replace(str(Path.home()),'${HOST_HOME}');templated=True
            if transform(text,study_root)!=text:raise ValueError('Source requires explicit privacy review: '+str(path))
        raw=text.encode('utf8')
        target=out/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            if target.read_bytes()!=raw:raise ValueError('Conflicting actual source bytes: '+relative)
            return
        target.write_bytes(raw);files.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
             path_template=templated,original_sha256=hashlib.sha256(original).hexdigest()))
    for label,folder in [('R_source',rs),('C_source',cs),('frontend',front)]:
        count=0
        for path in sorted(folder.rglob('*')):
            if not path.is_file()or'.git'in path.parts or'__pycache__'in path.parts:continue
            if path.suffix not in text_suffixes and path.name!='CMakeLists.txt'and not path.name.upper().startswith(('LICENSE','COPYING','COPYRIGHT','NOTICE')):continue
            add(path,label+'/'+str(path.relative_to(folder)));count+=1
        origins.append(dict(label=label,files=count))
    external=[]
    roots=[str(rs),str(cs_old),str(cs),str(original.parent/'backend/source'),str(study_root/'q32-q4-full-build-04/loop4/source'),str(front),str(original/'frontend')]
    for name,digest in closure['files'].items():
        path=Path(name)
        if any(path.is_relative_to(Path(x))for x in roots):continue
        if path.is_relative_to(study_root):
            if path.suffix not in text_suffixes:continue
            logical=mapped(str(path));destination=logical.replace('${CACHE}','seed/cache').replace('${R_NATIVE}','seed/R_native').replace('${C_NATIVE}','seed/C_native').replace('${MODEL_OUT}','seed/model')
            if '${'in destination:continue
            add(path,destination)
        else:external.append(dict(path=name,sha256=digest))
    recipe=dict(schema='hs.strong.full-source-reconstruction.v1',origins=origins,commands=commands,tools=list(tools.values()),external_requirements=external,
        source_reference_commit='0cae43063cf15170e91a2ff4d034da0ecef4a1b2',candidate_base_commit='873d16712fbf3bc04f54e9b3753515c5dbebb60f',
        numerical_inputs='SOURCE_ONLY_NO_OLD_OBJECT_ARCHIVE_ELF_OR_ORACLE',source_files=files,unused_uncompiled_material_withheld=unused_private_shaped,
        phases='Full pristine R and full candidate numerical libraries, then shared S3 frontend/counts/link',
        qualification='A rebuild is CPU-only and unqualified; another run/device needs repeated independent R and all protocol qualification before timing')
    (out/'RECIPE.json').write_text(json.dumps(recipe,indent=2)+'\n')
    selection=dict(schema='hs.strong.public-selection.v1',terminal_status='COMPLETE',private_literals=[str(study_root),str(Path.home())],files=[])
    for path in out.rglob('*'):
        if path.is_file():selection['files'].append(dict(path=str(path.relative_to(out)),bytes=path.stat().st_size,sha256=sha(path),payload_kind='utf8-text',public_review='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS'))
    result=archive.create(out,selection,out.parent/(out.name+'.tar.gz'))
    (out.parent/(out.name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(result,source_files=len(files),compile_link_steps=len(commands),GPU_requests=0)))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('study-root','configuration','model-build','out','implementation'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();main(a.study_root,a.configuration,a.model_build,a.out,a.implementation)
