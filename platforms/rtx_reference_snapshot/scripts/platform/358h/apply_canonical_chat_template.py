#!/usr/bin/env python3
"""Apply the frozen GGUF chat template to an exported OpenVINO model."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from gguf import GGUFReader


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gguf", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()

    target = args.model_dir / "chat_template.jinja"
    before = target.read_bytes()
    template = str(GGUFReader(args.gguf).fields["tokenizer.chat_template"].contents())
    after = template.encode("utf-8")
    target.write_bytes(after)
    payload = {
        "schema": "heterospec.358h.canonical_chat_template_overlay.v1",
        "formal_measurement": False,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "target": str(target.resolve()),
        "reason": "The immutable reconstructed source template differs from the historically authoritative GGUF template; runtime semantics are restored from the frozen canonical artifact.",
        "before_sha256": digest(before),
        "after_sha256": digest(after),
        "canonical_gguf_template_sha256": "57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361",
        "after_matches_canonical": digest(after) == "57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361",
    }
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["after_matches_canonical"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
