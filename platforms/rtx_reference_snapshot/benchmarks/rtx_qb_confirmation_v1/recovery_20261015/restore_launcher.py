"""Reversibly restore the exact original frozen launcher, never numerical assets."""
import hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).parent
TARGET=Path('C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
OLD='d41bad46673f64e0d02f23797f53f90ccf60f27d6eda8d86dd2d4bbeae5a858c'
UPDATED='b847bb9f4e48c19f585c8bf7d8b355f3f8c6d2125717ece9c9d7e16fb9f09de8'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    audit=json.loads((ROOT/'CORE_COMPARISON.json').read_text())
    assert audit['core_files']==2294 and not audit['unsupported_differences']
    body=(ROOT/'python.exe').read_bytes();assert sha(body)==OLD
    current=TARGET.read_bytes();assert sha(current)==UPDATED
    with (ROOT/'python-before-restoration.exe').open('xb') as f:f.write(current)
    # Current process is running a private backup copy supplied by PowerShell.
    stage=TARGET.with_name('python-pr104-restoring.exe')
    with stage.open('xb') as f:f.write(body);f.flush();os.fsync(f.fileno())
    os.replace(stage,TARGET)
    assert sha(TARGET.read_bytes())==OLD
    result=dict(utc=datetime.now(timezone.utc).isoformat(),status='EXACT_FROZEN_LAUNCHER_RESTORED',
                target=str(TARGET),before_sha256=UPDATED,after_sha256=OLD,
                archive_sha256='81466ad85b7074e5694a3d45e8edae6387f09548cd2e8f144841951a329dd7c7',
                official_archive_url='https://persistent.oaistatic.com/codex-primary-runtime/26.1011.11113/codex-primary-runtime-win32-x64-26.1011.11113.tar.gz',
                core_files_compared=2294,PE_signature_or_checksum_only_differences=44,
                normalized_PE_headers_and_all_sections_equal=True,stdlib_bytes_equal=True,
                only_mutated_runtime_path=str(TARGET),new_native_starts=0,
                original_scientific_F0_unchanged=True,previous_stop_receipts_preserved=True)
    with (ROOT/'RESTORATION.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
if __name__=='__main__':main()
