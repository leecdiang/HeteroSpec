"""Acquire only the pinned source kit and pristine upstream. Never fetch DLLs/models.

Offline use: supply --archive and --upstream (an exact clean Git checkout).
A failed extraction/stage remains under its unique directory; don't overwrite it.
"""
from __future__ import annotations
import argparse, os, re, shutil, stat, subprocess, zipfile
from pathlib import Path, PurePosixPath
from common import need, sha, read, save, inventory, command
HERE = Path(__file__).resolve().parent

def extract(archive, out, expected, max_bytes=2*1024**3):
    need(sha(archive) == expected, 'Source archive SHA256 mismatch')
    out = Path(out); need(not out.exists(), 'Fresh extraction directory required')
    with zipfile.ZipFile(archive) as z:
        rows = z.infolist(); seen = set(); total = 0
        for r in rows:
            p = PurePosixPath(r.filename)
            need(r.filename and '\\' not in r.filename and not p.is_absolute() and '..' not in p.parts,
                 'Unsafe ZIP path')
            need(not any(':' in s for s in p.parts), 'Drive/stream path in ZIP')
            need(r.filename not in seen, 'Duplicate ZIP member'); seen.add(r.filename)
            need(not stat.S_ISLNK(r.external_attr >> 16), 'ZIP symlink')
            total += r.file_size; need(total <= max_bytes, 'Source archive expansion limit')
        out.mkdir(parents=True)
        z.extractall(out)
    m = read(out / 'SOURCE_ASSET_MANIFEST.json')['files']
    actual = inventory(out); actual.pop('SOURCE_ASSET_MANIFEST.json')
    need(set(actual) == set(m), 'Incomplete/unexpected source-kit membership')
    for name, row in m.items():
        need(actual[name] == row['sha256'] and (out/name).stat().st_size == row['bytes'], 'Source member mismatch: '+name)
    return actual

def function_replace(text, name, replacement):
    # Reviewed frontend functions only. Parse braces while ignoring strings/comments.
    m = re.search(r'(?m)^static\s+(?:json|J)\s+'+re.escape(name)+r'\s*\([^)]*\)\s*\{', text)
    if not m: return text, 0
    i=text.index('{',m.start()); depth=0; quote=None; line=False; block=False; escape=False
    for j in range(i,len(text)):
        c=text[j]; nxt=text[j:j+2]
        if line:
            if c=='\n':line=False
            continue
        if block:
            if text[j-1:j+1]=='*/':block=False
            continue
        if quote:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c==quote:quote=None
            continue
        if nxt=='//':line=True;continue
        if nxt=='/*':block=True;continue
        if c in ('"',"'"):quote=c;continue
        if c=='{':depth+=1
        if c=='}':
            depth-=1
            if depth==0:return text[:m.start()]+replacement+text[j+1:],1
    raise RuntimeError('Unterminated reviewed function '+name)

def port(front):
    edits=[]
    for p in sorted(Path(front).glob('*')):
        if p.suffix not in ('.cpp','.hpp','.h','.inc') or p.name=='profiler.inc':continue
        old=p.read_text(encoding='utf-8'); s=old
        s=re.sub(r'(?m)^\s*#\s*include\s*[<"](?:windows|psapi)\.h[>"]\s*$', '#include "linux_platform.hpp"',s, flags=re.I)
        for name in ('module_inventory','modules'):
            s,n=function_replace(s,name,'static json '+name+'(){ return json(linux_transfer::modules()); }')
            if n:edits.append({'file':p.name,'operation':'POSIX loaded-module inventory','count':n})
        # The reviewed entry loads ggml-base.dll solely for the clock bootstrap.
        pattern=r'wchar_t exe\[32768\];GetModuleFileNameW\(nullptr,exe,32768\);.*?init\(\);'
        if re.search(pattern,s,re.S):
            s,n=re.subn(pattern,'const auto bin=linux_transfer::executable().parent_path();\n        ggml_time_init();',s,count=1,flags=re.S)
            edits.append({'file':p.name,'operation':'native ELF executable and linked ggml clock','count':n})
        s=s.replace('#include "profiler.inc"','#include "linux_profile_disabled.hpp"')
        # SDK DLL profiler is explicitly unavailable in this clean-build port.
        # Native tracing on Linux is a separate instrumented build, never fake zeros.
        s=s.replace('__declspec(dllexport)','__attribute__((visibility("default")))')
        s=s.replace('__declspec(dllimport)','')
        if s!=old:p.write_text(s,encoding='utf-8')
    shutil.copy2(HERE/'native/linux_platform.hpp',Path(front)/'linux_platform.hpp')
    shutil.copy2(HERE/'native/linux_profile_disabled.hpp',Path(front)/'linux_profile_disabled.hpp')
    unresolved=[]
    for p in sorted(Path(front).glob('*')):
        if p.suffix not in ('.cpp','.hpp','.h','.inc') or p.name=='profiler.inc':continue
        for token in ('<windows.h>','<psapi.h>','LoadLibraryW(', 'GetProcAddress(', 'GetModuleFileNameW(', 'EnumProcessModules(', 'GetCurrentProcess('):
            if token in p.read_text(encoding='utf8'):unresolved.append([p.name,token])
    return {'edits':edits,'unresolved_windows_calls':unresolved,
            'status':'SOURCE_PORTED_NOT_BUILT' if not unresolved else 'PORT_ADAPTATION_REQUIRED',
            'native_profile_supported':False}

def prepare(out, archive=None, upstream=None):
    pins=read(HERE/'pins.json'); out=Path(out).resolve();need(not out.exists(),'Fresh version directory required');out.mkdir(parents=True)
    if archive is None:
        dl=out/'download';dl.mkdir()
        command(['gh','release','download',pins['candidate']['tag'],'--repo',pins['candidate']['repo'],
                 '--pattern',pins['candidate']['asset'],'--dir',dl],out/'acquire-source',timeout=1800)
        archive=dl/pins['candidate']['asset']
    need(Path(archive).stat().st_size == pins['candidate']['bytes'],'Pinned source size mismatch')
    original=out/'authenticated-kit';extract(archive,original,pins['candidate']['sha256'])
    if upstream is None:
        upstream=out/'upstream-git'
        command(['git','init',upstream],out/'git-init')
        command(['git','-C',upstream,'fetch','--depth=1',pins['reference']['repo'],pins['reference']['commit']],out/'git-fetch',timeout=1800)
        command(['git','-C',upstream,'checkout','--detach','FETCH_HEAD'],out/'git-checkout')
    upstream=Path(upstream).resolve()
    head=subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()
    need(head==pins['reference']['commit'],'Wrong upstream commit')
    need(not subprocess.check_output(['git','-C',str(upstream),'status','--porcelain','--untracked-files=all'],text=True).strip(),'Unclean independent reference checkout')
    refs=out/'sources/reference';shutil.copytree(upstream,refs,ignore=shutil.ignore_patterns('.git'))
    for recipe in ('loop4','packed'):
        shutil.copytree(original/'native/cores'/recipe,out/'sources'/recipe)
    a=inventory(out/'sources/loop4');b=inventory(out/'sources/packed')
    differences=[p for p in sorted(set(a)|set(b)) if a.get(p)!=b.get(p)]
    need(differences==['src/llama-graph.cpp'],'Candidate core differences changed; inspect before attribution')
    for recipe in ('loop4','packed'):
        root=out/'sources'/recipe
        for required in ('ggml/src/ggml-cuda/mmvq.cu','ggml/src/ggml-cuda/quantize.cuh','src/llama-context.cpp'):
            need((root/required).is_file(),'Missing actual numerical source: '+required)
    shutil.copytree(original/'native/frontend',out/'frontend')
    result=port(out/'frontend')
    save(out/'PORT.json',result)
    save(out/'SOURCE_LOCK.json',{'pins':pins,'archive_sha256':sha(archive),'reference_commit':head,
          'sources':{r:inventory(out/'sources'/r) for r in ('reference','loop4','packed')},
          'frontend':inventory(out/'frontend'),'candidate_core_differences':differences,
          'status':result['status'],'native_build':'NOT_RUN','GPU_qualification':'NOT_RUN'})
    print(result['status'])
    if result['unresolved_windows_calls']:
        print('Retain this epoch; adapt only the reported platform code in a new epoch. See HOST_ADAPTER.md.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--archive',type=Path);p.add_argument('--upstream',type=Path)
    a=p.parse_args();prepare(a.out,a.archive,a.upstream)
