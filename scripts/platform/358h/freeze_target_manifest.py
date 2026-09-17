#!/usr/bin/env python3
"""Verify and freeze the cross-platform Qwen3-8B target artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_SIZE = 8_709_518_112
EXPECTED_SHA256 = '408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if not args.model.is_file():
        raise SystemExit(f'model not found: {args.model}')
    digest = hashlib.sha256()
    with args.model.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    actual = digest.hexdigest()
    size = args.model.stat().st_size
    if size != EXPECTED_SIZE or actual != EXPECTED_SHA256:
        raise SystemExit(f'target validation failed: bytes={size}, sha256={actual}')
    manifest = {
        'schema': 'heterospec.358h.target_model.v1',
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'authoritative_repository': 'Qwen/Qwen3-8B-GGUF',
        'authoritative_revision': '7c41481f57cb95916b40956ab2f0b139b296d974',
        'filename': 'Qwen3-8B-Q8_0.gguf',
        'bytes': size,
        'sha256': actual,
        'transport': {
            'url': 'https://www.modelscope.cn/models/Qwen/Qwen3-8B-GGUF/resolve/master/Qwen3-8B-Q8_0.gguf',
            'role': 'transport mirror only; not model provenance',
            'observed_x_linked_etag': EXPECTED_SHA256,
            'byte_identity_verified': True
        },
        'historical_cross_platform_match': 'Same filename, revision, byte length and SHA256 as the frozen B570 target artifact.',
        'formal_measurement': False
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'bytes': size, 'sha256': actual}, indent=2))


if __name__ == '__main__':
    main()

