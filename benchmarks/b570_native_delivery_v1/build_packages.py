"""Select authenticated existing bytes into new model-free source/reference packages."""
from pathlib import Path
import argparse,hashlib,json,shutil,zipfile
ARCHIVE_SHA='78abc364729fed7ba0f8b92cf3594eed2511df181714e9f53b19ede2a4465973'
ARCHIVE_BYTES=1367643308
BASELINE='41cb7504ece1f78109fde6895b10ffc56dff8ef1'
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--dest',type=Path,required=True);a=p.parse_args();code=Path(__file__).resolve().parent
    if a.dest.exists():raise ValueError('Fresh package destination required')
    if a.source.stat().st_size!=ARCHIVE_BYTES or sha(a.source)!=ARCHIVE_SHA:raise ValueError('Original sealed archive mismatch')
    a.dest.mkdir(parents=True)
    with zipfile.ZipFile(a.source)as source:
        original=source.read('manifest.json');manifest=json.loads(original);origin={x['path']:x for x in manifest['files']}
        if len(origin)!=len(manifest['files']):raise ValueError('Duplicate source entry')
        output=[]
        for kind in ['minimal','four_input_references']:
            root=a.dest/kind;root.mkdir()
            selected=[]
            for name in origin:
                if kind=='minimal':take=name.startswith(('kit/','fixture/','references/qual-2/','evidence/capture-a2/','evidence/stage-a1/'))or name in ['upstream.tar.gz','bundle_manifest.py']
                else:take=name.startswith('references/')or name in ['kit/audit_request.py','kit/INPUT_PANEL.json']
                if take:selected.append(name)
            if any(n.endswith(('.gguf','.dll','.exe'))for n in selected):raise ValueError('Weights/binaries excluded from new delivery')
            for name in selected:
                row=origin[name];data=source.read(name)
                if len(data)!=row['bytes']or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Source member mismatch '+name)
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            (root/'provenance').mkdir();(root/'provenance/ORIGINAL_MANIFEST.json').write_bytes(original)
            write(root/'provenance/SOURCE_ARCHIVE.json',{'archive_sha256':ARCHIVE_SHA,'archive_bytes':ARCHIVE_BYTES,'baseline_commit':BASELINE,'baseline_pr':148,'members_preserved_byte_for_byte':len(selected),'source_path_is_local_custody_only':str(a.source.resolve())})
            (root/'delivery').mkdir()
            extras=['verify_package.py','LICENSE']if kind=='four_input_references'else['verify_package.py','download.py','README.md','DEPENDENCIES.md','MODEL_SOURCES.json','LICENSE']
            for name in extras:shutil.copyfile(code/name,root/'delivery'/name)
            if kind=='four_input_references':
                (root/'delivery/README.md').write_text('# Four-input historical references\n\nRun `python -B -X utf8 delivery/verify_package.py --root . --out ../new-reference-audit`. This is a CPU-only integrity/inter-arm audit, with 914 vectors across all four fixed inputs. Native source/build commands are in the separate minimal package.\n',encoding='utf-8')
            rows=[]
            for f in sorted(root.rglob('*')):
                if not f.is_file():continue
                name=f.relative_to(root).as_posix();row={'path':name,'bytes':f.stat().st_size,'sha256':sha(f)}
                if name in origin and name in selected:row['origin_member']=name
                rows.append(row)
            write(root/'manifest.json',{'schema':1,'platform':'b570','package_kind':kind,'source_archive_sha256':ARCHIVE_SHA,'source_manifest_sha256':hashlib.sha256(original).hexdigest(),'files':rows,'scope':'Existing byte delivery and CPU audits; no new native execution/performance claim'})
            filename='B570_MINIMAL_SOURCE_REQUEST_V1.zip'if kind=='minimal'else'B570_FOUR_INPUT_REFERENCES_V1.zip'
            archive=a.dest/filename
            with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3)as zipped:
                for f in sorted(root.rglob('*')):
                    if f.is_file():zipped.write(f,f.relative_to(root).as_posix())
            output.append({'kind':kind,'name':filename,'path':str(archive.resolve()),'bytes':archive.stat().st_size,'sha256':sha(archive),'files':len(rows),'original_members':len(selected),'manifest_sha256':sha(root/'manifest.json')})
            print(json.dumps(output[-1]),flush=True)
    write(a.dest/'PACKAGES.json',{'source_archive_sha256':ARCHIVE_SHA,'assets':output,'new_model_requests':0,'new_native_runs':0})
if __name__=='__main__':main()
