"""Conservative current-host public transform; original bytes remain private."""
import re
from pathlib import Path


def transform(text,root):
    text=text.replace(str(root),'${HS_ROOT}').replace(str(Path.home()),'${HOST_HOME}')
    text=re.sub(r'GPU-[0-9a-fA-F-]{16,}','${ALLOCATED_GPU_UUID}',text)
    if re.search(r'(?<!\d)(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)',text):
        raise ValueError('Internal network literal requires explicit privacy review')
    return text
