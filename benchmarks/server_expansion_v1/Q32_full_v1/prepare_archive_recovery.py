"""Data-only export successor: redact arbitrary home paths and partial UUIDs.

Never weaken the final privacy assertion or touch native/compiled evidence.
The first failed export directory and its exception remain preserved.
"""
from pathlib import Path
import argparse,shutil
from build import sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir();shutil.copy2(a.source/'build.py',a.out/'build.py');source=a.source/'archive.py';s=source.read_text().replace("w/'export-04'","w/'export-05'")
 anchor='assert not re.search(';assert s.count(anchor)==1
 # Redact before the unchanged fail-closed assertion. This also handles public
 # upstream example paths that are unrelated to the local account.
 replacement='s=re.sub(r"/home/[^/\\s\\\"\\\']+","$HOME_USER",s);s=re.sub(r"GPU-[0-9a-fA-F-]{8,}","<allocated-or-redacted-GPU>",s);s=re.sub(r"\\b192\\.168(?:\\.\\d{1,3}){1,2}\\b","<private-network>",s);assert not re.search('
 s=s.replace(anchor,replacement,1);(a.out/'archive.py').write_text(s)
 save(a.out/'ADAPTER_BINDING.json',dict(original_archive_sha256=sha(source),new_archive_sha256=sha(a.out/'archive.py'),scope='Privacy export only: redact arbitrary home directory names/partial GPU UUID literals, preserve exact raw commitments and fail-closed privacy assertion; no native work, no numeric comparison change',old_export_kept=True))
if __name__=='__main__':main()
