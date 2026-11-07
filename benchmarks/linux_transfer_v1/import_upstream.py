"""Pinned archive fallback when Git smart-protocol transport is unavailable.

Authenticates the complete tree AND original signed Git commit bytes, without
inventing a replacement commit or changing sources. Inputs are local files; fetch
the fixed codeload archive and GitHub Git-commit API JSON separately.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, os, subprocess, tarfile
from common import need, read, save, sha

COMMIT='0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
TREE='21455f0751564fc633b58ec481a05eeb514a6650'
ARCHIVE_SHA='5425569b37eb461bf82feba00f765fdb8624d7a0bf4719320282d6f0895f379f'

def materialize(archive,metadata,out,receipt):
 archive=Path(archive);metadata=Path(metadata);out=Path(out).resolve()
 need(not out.exists(),'Keep failed imports in separate epochs')
 need(sha(archive)==ARCHIVE_SHA,'Pinned upstream archive bytes changed')
 j=read(metadata);need(j['sha']==COMMIT and j['tree']['sha']==TREE,'Different upstream object')
 v=j['verification'];need(v['verified'] and v['payload'] and v['signature'],'Original signed commit metadata missing')
 headers,sep,message=v['payload'].partition('\n\n');need(sep and headers.splitlines()[0]=='tree '+TREE,'Signed payload tree mismatch')
 # Preserve the final signature newline as a continuation line. Stripping it
 # produces a different object even though the visible signature is unchanged.
 body=(headers+'\ngpgsig '+v['signature'].replace('\n','\n ')+'\n\n'+message).encode()
 digest=hashlib.sha1(b'commit '+str(len(body)).encode()+b'\0'+body).hexdigest()
 need(digest==COMMIT,'Reconstructed commit does not have the original Git SHA')
 out.mkdir(parents=True);seen=set();links=[];prefix='llama.cpp-'+COMMIT
 with tarfile.open(archive,'r:gz') as tf:
  for m in tf:
   parts=PurePosixPath(m.name).parts
   need(parts and parts[0]==prefix and all(x not in ('..','') for x in parts),'Unsafe archive path')
   if len(parts)==1:need(m.isdir(),'Archive root is not a directory');continue
   rel=PurePosixPath(*parts[1:]);need(rel.parts[0]!='.git' and str(rel) not in seen,'Duplicate or Git metadata archive member');seen.add(str(rel))
   p=out/str(rel)
   if m.isdir():p.mkdir(parents=True,exist_ok=True);continue
   p.parent.mkdir(parents=True,exist_ok=True)
   if m.issym():links.append((p,m.linkname));continue
   need(m.isfile(),'Unsupported non-file archive member')
   source=tf.extractfile(m);need(source is not None,'Unreadable archive member')
   with source,p.open('xb') as dest:
    while block:=source.read(1024*1024):dest.write(block)
   p.chmod(0o755 if m.mode&0o111 else 0o644)
 # Links are installed last; no regular file is ever written through a link.
 for p,target in links:
  need(not PurePosixPath(target).is_absolute() and (p.parent/target).resolve().is_relative_to(out),'Unsafe source symlink')
  os.symlink(target,p)
 def git(*args,input=None):
  return subprocess.check_output(['git','-C',str(out),*args],input=input).decode().strip()
 # Tracked upstream files can match upstream's own .gitignore (logs, plist,
 # packaging scripts). A new index must include every authenticated tar member.
 git('init','--quiet');git('config','core.autocrlf','false');git('add','--all','--force')
 need(git('write-tree')==TREE,'Complete archive tree differs from pinned upstream')
 need(git('hash-object','-t','commit','-w','--stdin',input=body)==COMMIT,'Git object import differs')
 (out/'.git/shallow').write_text(COMMIT+'\n');git('update-ref','--no-deref','HEAD',COMMIT)
 need(not git('status','--porcelain','--untracked-files=all'),'Imported upstream checkout is not clean')
 save(receipt,{'commit':COMMIT,'tree':TREE,'tar_sha256':sha(archive),'commit_metadata_sha256':sha(metadata),
  'exact_git_tree_verified':True,'exact_commit_object_verified':True,'source_edits':False,
  'scope':'Content-addressed reconstruction from pinned archive and original signed Git object; no new Git commit and no claim of independent signature-key trust'})

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('archive','metadata','out','receipt'):p.add_argument('--'+name,required=True)
 a=p.parse_args();materialize(a.archive,a.metadata,a.out,a.receipt)
