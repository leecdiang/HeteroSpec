"""Reassemble only the pinned hashed exposure metadata, never model weights."""
from pathlib import Path
import gzip, hashlib, json

def main():
    root=Path(__file__).resolve().parent
    manifest=json.loads((root/'EXCLUSION_PARTS.json').read_text());parts=[]
    for row in manifest['parts']:
        path=root/row['name'];data=path.read_bytes()
        if path.parent!=root or len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise RuntimeError('Exact public exclusion part changed')
        parts.append(data)
    joined=b''.join(parts)
    if len(joined)!=manifest['joined_bytes'] or hashlib.sha256(joined).hexdigest()!=manifest['joined_sha256']:
        raise RuntimeError('Joined exclusion metadata changed')
    review=json.loads((root/'EXPOSURE_REVIEW.json').read_text());raw=gzip.decompress(joined)
    if hashlib.sha256(raw).hexdigest()!=review['uncompressed_sha256'] or len(raw.splitlines())!=review['hashed_exclusion_key_count']:
        raise RuntimeError('Exclusion semantics changed')
    path=root/manifest['joined_name']
    if path.exists():
        if path.read_bytes()!=joined:raise RuntimeError('Preserve existing mismatched assembly')
    else:
        with path.open('xb') as stream:stream.write(joined)
    print('PINNED_EXCLUSION_METADATA_ASSEMBLED_ZERO_MODEL_WORK',flush=True)

if __name__=='__main__':main()
