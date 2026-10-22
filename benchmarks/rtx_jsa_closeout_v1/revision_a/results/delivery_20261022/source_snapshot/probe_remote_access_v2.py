"""Authenticated bounded payload checks; never launches native/model work.

The full archive digest comes from GitHub metadata. Payload checks read the
first and last 64 KiB, plus the entire small ARCHIVES index, not full ZIPs.
Credentials and temporary signed redirect URLs are never persisted.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

import resume_remote_evidence_v2 as delivery

FOLDER = Path('D:/hs144-evidence-e5c03228')
CHUNK = 65536


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def bounded_fetch(api_url, token, first, last, total):
    opener = urllib.request.build_opener(NoRedirect)
    url = api_url
    redirects = 0
    for step in range(5):
        headers = {'Accept': 'application/octet-stream',
                   'Range': f'bytes={first}-{last}',
                   'User-Agent': 'HeteroSpec-PR144-evidence-access-check',
                   'Cache-Control': 'no-cache'}
        if step == 0:
            headers['Authorization'] = 'Bearer ' + token
            headers['X-GitHub-Api-Version'] = '2022-11-28'
        try:
            response = opener.open(urllib.request.Request(url, headers=headers), timeout=90)
        except urllib.error.HTTPError as error:
            if error.code in (301, 302, 303, 307, 308):
                location = error.headers.get('Location', '')
                error.close()
                parsed = urllib.parse.urlsplit(location)
                host = parsed.hostname or ''
                if parsed.scheme != 'https' or not (
                    host.endswith('.githubusercontent.com') or
                    host.endswith('.github.com') or host.endswith('.s3.amazonaws.com')
                ):
                    raise RuntimeError('Unexpected release payload redirect host') from None
                url = location  # Ephemeral URL; never saved or logged.
                redirects += 1
                continue
            code = error.code
            error.close()
            raise RuntimeError(f'Payload HTTP status {code}') from None
        except urllib.error.URLError:
            raise RuntimeError('Payload network request failed') from None
        with response:
            status = response.status
            content_range = response.headers.get('Content-Range')
            if status == 206:
                if content_range != f'bytes {first}-{last}/{total}':
                    raise RuntimeError('Content-Range differs from requested exact byte range')
            elif status == 200 and first == 0 and last + 1 == total:
                pass
            else:
                raise RuntimeError(f'Unexpected bounded payload HTTP status {status}')
            body = response.read(last - first + 2)
            if len(body) != last - first + 1:
                raise RuntimeError('Payload range byte count mismatch')
            return body, {'http_status': status, 'content_range': content_range,
                          'redirect_count': redirects,
                          'credential_forwarded_to_storage': False}
    raise RuntimeError('Too many payload redirects')


def main(folder, only):
    index = delivery.read(folder / 'ARCHIVES.json')
    expected = {row['name']: row for row in index['archives']}
    for name in ('ARCHIVES.json', 'FILES.json'):
        path = folder / name
        expected[name] = {'bytes': path.stat().st_size, 'sha256': delivery.sha(path)}
    token = subprocess.check_output(['gh', 'auth', 'token'], stderr=subprocess.DEVNULL).decode().strip()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', token):
        raise RuntimeError('Unexpected credential format')
    result_path = folder / 'REMOTE_ACCESS_PROBES_V2.json'
    output = delivery.read(result_path) if result_path.exists() else {
        'status': 'IN_PROGRESS', 'study_uuid': delivery.STUDY,
        'execution_commit': delivery.EXECUTION, 'release_id': delivery.RELEASE_ID,
        'native_launches': 0, 'assets': {},
        'verification_scope': 'Authenticated GitHub metadata size/full server SHA256 and bounded binary payload comparisons. Full ARCHIVES.json GET; first/last 65536 bytes of every ZIP and FILES.json. No full remote ZIP readback or remote re-extraction.',
        'credentials_or_signed_urls_persisted': False,
    }
    rows = {row['name']: row for row in delivery.assets() if row['name'] in expected}
    for name in sorted(rows, key=lambda item: (expected[item]['bytes'], item)):
        if only and name != only:
            continue
        asset, identity = rows[name], expected[name]
        if not delivery.verified_asset(asset, identity):
            continue
        if name in output['assets'] and output['assets'][name]['asset_id'] == asset['id']:
            continue
        size = identity['bytes']
        ranges = [(0, size - 1)] if size <= CHUNK else [(0, CHUNK - 1), (size - CHUNK, size - 1)]
        checks = []
        for first, last in ranges:
            with (folder / name).open('rb') as source:
                source.seek(first)
                local = source.read(last - first + 1)
            for attempt in range(1, 5):
                try:
                    body, response = bounded_fetch(asset['url'], token, first, last, size)
                    if body != local:
                        raise RuntimeError('Remote payload bytes differ from original local bytes')
                    break
                except RuntimeError as error:
                    if attempt == 4:
                        raise RuntimeError(name + ': ' + str(error)) from None
                    time.sleep(attempt * 2)
            checks.append({'first_byte': first, 'last_byte': last, 'bytes': len(body),
                           'local_and_remote_sha256': hashlib.sha256(body).hexdigest(),
                           'exact_byte_match': True, 'checked_utc': delivery.now(), **response})
        output['assets'][name] = {**delivery.receipt(asset, identity), 'payload_checks': checks}
        output['checked_utc'] = delivery.now()
        output['verified_assets'] = len(output['assets'])
        output['total_assets'] = len(expected)
        output['status'] = 'PASS_ALL_17_AUTHENTICATED_ASSET_ACCESS' if len(output['assets']) == len(expected) else 'IN_PROGRESS'
        delivery.save(result_path, output)
        print('PAYLOAD_ACCESS_PASS', name, 'checked_bytes', sum(c['bytes'] for c in checks), flush=True)
    print('ACCESS_PROBES', len(output['assets']), 'of', len(expected), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, default=FOLDER)
    parser.add_argument('--only')
    args = parser.parse_args()
    main(args.folder, args.only)
