"""Download the pinned historical evidence using host Git credentials, never log secrets."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header('Authorization')
        return redirected


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def recover(root):
    root = Path(root)
    index = json.loads((root / 'OBJECT_PARTS.json').read_bytes())
    assert sha(root / 'OBJECT_PARTS.json') == 'ae2fcd4a0333bb2d594a21d6e48b76f8ddb78d4162ccaa090eb72623a50fcbe0'
    release = json.loads((root / 'HISTORICAL_RELEASE.json').read_bytes())
    assets = {a['name']: a for a in release['assets']}
    result = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True, check=True)
    credential = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    download = root / 'historical-download'
    download.mkdir(exist_ok=True)
    pins = [dict(p, name=Path(p['path']).name) for p in index['parts']]
    pins.append(dict(index['members_manifest'], name='completed-through-day0.OBJECT_MEMBERS.json'))

    def one(pin):
        dest = download / pin['name']
        if dest.exists():
            assert sha(dest) == pin['sha256'], 'existing download changed'
            return pin['name']
        for attempt in range(5):
            partial = download / (pin['name'] + '.attempt-' + str(attempt))
            if partial.exists():
                continue
            try:
                req = urllib.request.Request(assets[pin['name']]['url'] + '?b570=' + str(time.time_ns()), headers={
                    'Authorization': 'Bearer ' + credential['password'],
                    'Accept': 'application/octet-stream', 'User-Agent': 'HeteroSpec-history-recovery'})
                with urllib.request.build_opener(SafeRedirect).open(req, timeout=90) as response, partial.open('xb') as output:
                    while chunk := response.read(4 * 1024 * 1024):
                        output.write(chunk)
                assert partial.stat().st_size == pin['bytes'] and sha(partial) == pin['sha256'], 'download digest mismatch'
                partial.rename(dest)
                print('VERIFIED', pin['name'], flush=True)
                return pin['name']
            except Exception as error:
                # Keep failed bytes and a sanitized failure classification.
                print('RETAINED_FAILURE', pin['name'], attempt, type(error).__name__, flush=True)
        raise RuntimeError('download attempts exhausted: ' + pin['name'])

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        names = list(pool.map(one, pins))
    (root / 'HISTORICAL_DOWNLOAD_VERIFIED.json').write_text(json.dumps({'assets': names, 'index_sha256': sha(root / 'OBJECT_PARTS.json')}, indent=2))


if __name__ == '__main__':
    recover(sys.argv[1])
