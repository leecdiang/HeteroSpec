#!/usr/bin/env python3
"""Create a non-performance manifest for the frozen canonical draft GGUF."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gguf import GGUFReader


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scalar(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gguf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reader = GGUFReader(args.gguf)
    tokenizer_keys = sorted(k for k in reader.fields if k.startswith("tokenizer."))
    tokenizer: dict[str, Any] = {}
    for key in tokenizer_keys:
        value = reader.fields[key].contents()
        if isinstance(value, list):
            tokenizer[key] = [scalar(item) for item in value]
        else:
            tokenizer[key] = scalar(value)

    tokenizer_bytes = json.dumps(
        tokenizer, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    payload = {
        "schema": "heterospec.358h.canonical_draft_manifest.v1",
        "formal_measurement": False,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "repository": "Qwen/Qwen3-0.6B-GGUF",
            "revision": "23749fefcc72300e3a2ad315e1317431b06b590a",
            "filename": "Qwen3-0.6B-Q8_0.gguf",
            "base_model_declared": "Qwen/Qwen3-0.6B",
            "base_model_revision": None,
            "base_model_revision_status": "NOT_RECORDED_IN_HETEROSPEC_OR_GGUF_METADATA",
        },
        "artifact": {
            "path": str(args.gguf.resolve()),
            "bytes": args.gguf.stat().st_size,
            "sha256": file_sha256(args.gguf),
            "format": "GGUF",
            "quantization": "Q8_0",
        },
        "gguf": {
            "version": scalar(reader.fields["GGUF.version"].contents()),
            "architecture": reader.fields["general.architecture"].contents(),
            "name": reader.fields["general.name"].contents(),
            "file_type": scalar(reader.fields["general.file_type"].contents()),
            "quantization_version": scalar(reader.fields["general.quantization_version"].contents()),
            "tensor_count": scalar(reader.fields["GGUF.tensor_count"].contents()),
        },
        "tokenizer": {
            "storage": "embedded_in_gguf",
            "independent_upstream_revision": None,
            "independent_upstream_revision_status": "NOT_RECORDED",
            "metadata_keys": tokenizer_keys,
            "canonical_json_sha256": hashlib.sha256(tokenizer_bytes).hexdigest(),
            "model": tokenizer.get("tokenizer.ggml.model"),
            "pre": tokenizer.get("tokenizer.ggml.pre"),
            "bos_token_id": tokenizer.get("tokenizer.ggml.bos_token_id"),
            "eos_token_id": tokenizer.get("tokenizer.ggml.eos_token_id"),
            "padding_token_id": tokenizer.get("tokenizer.ggml.padding_token_id"),
            "add_bos_token": tokenizer.get("tokenizer.ggml.add_bos_token"),
            "token_count": len(tokenizer.get("tokenizer.ggml.tokens", [])),
            "merge_count": len(tokenizer.get("tokenizer.ggml.merges", [])),
            "chat_template_sha256": hashlib.sha256(
                str(tokenizer.get("tokenizer.chat_template", "")).encode("utf-8")
            ).hexdigest(),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
