"""Describe completed evidence on the same draft release; never publish it."""
from pathlib import Path
import resume_remote_evidence_v2 as d

FOLDER=Path('D:/hs144-evidence-e5c03228')


def main():
    receipt=d.read(FOLDER/'REMOTE_RESUME_COMPLETE.json')
    probes=d.read(FOLDER/'REMOTE_ACCESS_PROBES_V2.json')
    assert receipt['status']=='COMPLETE_DRAFT_RELEASE_ASSET_DELIVERY' and len(receipt['assets'])==17
    assert probes['status']=='PASS_ALL_17_AUTHENTICATED_ASSET_ACCESS'
    release=d.api(f'repos/{d.REPO}/releases/{d.RELEASE_ID}')
    assert release['draft'] and release['target_commitish']==d.EXECUTION
    name='RTX PR140 amended closeout: complete original raw evidence (15 ZIPs)'
    body=f'''Complete original raw evidence for [PR144](https://github.com/{d.REPO}/pull/144), under the approved PR140 natural-source and worker-budget amendment.

Study UUID: `{d.STUDY}`. Execution freeze: `{d.EXECUTION}`.

All **15 original lossless ZIP shards plus ARCHIVES.json and FILES.json** are present. Every uploaded asset byte count and GitHub-reported full SHA256 matches the existing local original. Authenticated binary checks compare all of ARCHIVES.json and the first/last 64 KiB of every other asset. These bounded checks do not claim full remote ZIP readback or remote re-extraction.

- ARCHIVES.json SHA256: `{receipt['local_archive_manifest_sha256']}`
- FILES.json SHA256: `{receipt['local_file_manifest_sha256']}`
- 23,398 packaged files, 14,758,946,212 uncompressed bytes; 12,399,195,667 original ZIP bytes.

Use the stable asset API links in PR144's RAW_ACCESS.json with authenticated draft-release permissions and Accept: application/octet-stream. Verify all downloaded ZIPs against ARCHIVES.json, extract them into one directory, and verify every extracted path/size/SHA256 against FILES.json.

All original evidence and failed/interrupted transport receipts are preserved. No original shard was repacked, no experiment was rerun, and no scientific criterion, result or historical charge changed. Model weights and third-party numerical DLL bytes are excluded; their identity manifests remain included. This release and PR144 remain drafts. No merge or manuscript/arXiv submission.
'''
    payload={'name':name,'body':body,'draft':True,'target_commitish':d.EXECUTION}
    path=Path(__file__).parent/'complete_release_metadata_payload.json'
    d.save(path,payload)
    try:d.api(f'repos/{d.REPO}/releases/{d.RELEASE_ID}','PATCH',path)
    except RuntimeError:
        observed=d.api(f'repos/{d.REPO}/releases/{d.RELEASE_ID}')
        if any(observed.get(k)!=v for k,v in payload.items()):raise
    current=d.api(f'repos/{d.REPO}/releases/{d.RELEASE_ID}')
    assert all(current.get(k)==v for k,v in payload.items())
    assert current['tag_name']==release['tag_name'] and current['id']==d.RELEASE_ID
    d.save(FOLDER/'DRAFT_RELEASE.json',current)
    print('DRAFT_RELEASE_METADATA_COMPLETE_PRESERVED_DRAFT',current['id'],flush=True)


if __name__=='__main__':main()
