"""Restore a selected original-path subtree from the portable evidence ZIP.

Concatenate numbered ZIP parts first. Only writes beneath a fresh destination;
original Windows absolute paths are identifiers, never restoration destinations.
"""
import argparse,hashlib,json,os,zlib,zipfile,io,bisect
from pathlib import Path,PureWindowsPath

def key(path):return str(PureWindowsPath(path)).casefold()

class PartsReader(io.RawIOBase):
    """Seek over verified parts without making a second full-size ZIP."""
    def __init__(self,index):
        self.rows=json.loads(Path(index).read_bytes())['parts'];self.parent=Path(index).parent;self.position=0;self.starts=[0]
        for row in self.rows:
            p=self.parent/row['name']
            if p.stat().st_size!=row['bytes']:raise ValueError('part size')
            with p.open('rb') as f:
                if hashlib.file_digest(f,'sha256').hexdigest()!=row['sha256']:raise ValueError('part digest')
            self.starts.append(self.starts[-1]+row['bytes'])
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.position
    def seek(self,offset,whence=0):
        self.position=offset if whence==0 else self.position+offset if whence==1 else self.starts[-1]+offset
        if self.position<0:raise ValueError('negative seek')
        return self.position
    def read(self,n=-1):
        n=min(n if n>=0 else self.starts[-1],self.starts[-1]-self.position);pieces=[]
        while n>0:
            i=bisect.bisect_right(self.starts,self.position)-1;offset=self.position-self.starts[i];take=min(n,self.rows[i]['bytes']-offset)
            with (self.parent/self.rows[i]['name']).open('rb') as f:f.seek(offset);data=f.read(take)
            if len(data)!=take:raise ValueError('truncated part')
            pieces.append(data);n-=take;self.position+=take
        return b''.join(pieces)

def restore(bundle,prefix,destination):
    destination=Path(destination).resolve();destination.mkdir(exist_ok=False)
    root=PureWindowsPath(prefix);seen={};count=0
    source=PartsReader(bundle) if str(bundle).endswith('.parts.json') else bundle
    with zipfile.ZipFile(source) as archive:
        manifest=json.loads(archive.read('FILES.json'))
        for row in manifest['files']:
            original=PureWindowsPath(row['path'])
            try:relative=original.relative_to(root)
            except ValueError:continue
            if not relative.parts:continue
            if '..' in relative.parts:raise ValueError('unsafe relative path')
            output=destination.joinpath(*relative.parts);output.parent.mkdir(parents=True,exist_ok=True)
            if not output.resolve().is_relative_to(destination):raise ValueError('path escape')
            if row['sha256'] in seen:
                try:os.link(seen[row['sha256']],output)
                except OSError:
                    import shutil
                    shutil.copyfile(seen[row['sha256']],output)
            else:
                digest=hashlib.sha256();size=0
                with output.open('xb') as f:
                    for chunk in row['chunks']:
                        raw=zlib.decompress(archive.read('chunks/'+chunk[:2]+'/'+chunk))
                        if hashlib.sha256(raw).hexdigest()!=chunk:raise ValueError('chunk digest mismatch')
                        digest.update(raw);size+=len(raw);f.write(raw)
                if digest.hexdigest()!=row['sha256'] or size!=row['bytes']:raise ValueError('file digest mismatch')
                seen[row['sha256']]=output
            count+=1
    if not count:raise ValueError('no files match source prefix')
    print('Restored and hash-verified',count,'files; distinct payloads',len(seen))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('bundle',type=Path);p.add_argument('original_prefix');p.add_argument('destination',type=Path);a=p.parse_args();restore(a.bundle,a.original_prefix,a.destination)
