from pathlib import Path
import json,os
roots={
 'source':r'C:\Users\ASUS\Documents\ChatGPT\HeteroSpec\rtx223-round1-resume-20261112-e03\runtime\final-source',
 'cuda':r'D:\rtx184-tools\cuda',
 'vc':r'D:\rtx184-tools\msvc\VC\Tools\MSVC\14.44.35207',
 'sdk_include':r'D:\rtx184-tools\msvc\Windows Kits\10\Include\10.0.26100.0',
 'sdk_lib_ucrt':r'D:\rtx184-tools\msvc\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64',
 'sdk_lib_um':r'D:\rtx184-tools\msvc\Windows Kits\10\Lib\10.0.26100.0\um\x64',
 'sdk_bin':r'D:\rtx184-tools\msvc\Windows Kits\10\bin\10.0.26100.0\x64'}
for name,root in roots.items():
 files=0;size=0
 for d,ds,fs in os.walk('\\\\?\\'+root):
  for f in fs:files+=1;size+=os.stat(os.path.join(d,f)).st_size
 print(json.dumps({'name':name,'path':root,'files':files,'bytes':size}),flush=True)
