#!/usr/bin/env python3
"""Audit a reconstructed Transformers source against the frozen canonical GGUF.

This is Phase-0 qualification only. It does not record performance measurements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gguf import GGUFReader
from safetensors import safe_open
import torch
from transformers import AutoTokenizer


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scalar(value: Any) -> Any:
    return value.item() if hasattr(value, "item") else value


def source_tensor_for_gguf(name: str) -> str:
    if name == "token_embd.weight":
        return "model.embed_tokens.weight"
    if name == "output_norm.weight":
        return "model.norm.weight"
    prefix, layer_text, suffix = name.split(".", 2)
    if prefix != "blk":
        raise KeyError(name)
    mapping = {
        "attn_q.weight": "self_attn.q_proj.weight",
        "attn_k.weight": "self_attn.k_proj.weight",
        "attn_v.weight": "self_attn.v_proj.weight",
        "attn_output.weight": "self_attn.o_proj.weight",
        "attn_q_norm.weight": "self_attn.q_norm.weight",
        "attn_k_norm.weight": "self_attn.k_norm.weight",
        "attn_norm.weight": "input_layernorm.weight",
        "ffn_gate.weight": "mlp.gate_proj.weight",
        "ffn_up.weight": "mlp.up_proj.weight",
        "ffn_down.weight": "mlp.down_proj.weight",
        "ffn_norm.weight": "post_attention_layernorm.weight",
    }
    return f"model.layers.{layer_text}.{mapping[suffix]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gguf", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--functional", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reader = GGUFReader(args.gguf)
    config = json.loads((args.source / "config.json").read_text(encoding="utf-8"))
    tokenizer_json = json.loads((args.source / "tokenizer.json").read_text(encoding="utf-8"))
    tokenizer_config = json.loads((args.source / "tokenizer_config.json").read_text(encoding="utf-8"))

    metadata_map = {
        "architecture": ("general.architecture", "model_type"),
        "layer_count": ("qwen3.block_count", "num_hidden_layers"),
        "context_length": ("qwen3.context_length", "max_position_embeddings"),
        "hidden_size": ("qwen3.embedding_length", "hidden_size"),
        "intermediate_size": ("qwen3.feed_forward_length", "intermediate_size"),
        "attention_heads": ("qwen3.attention.head_count", "num_attention_heads"),
        "kv_heads": ("qwen3.attention.head_count_kv", "num_key_value_heads"),
        "head_dim": ("qwen3.attention.key_length", "head_dim"),
        "rope_theta": ("qwen3.rope.freq_base", "rope_theta"),
        "rms_norm_eps": ("qwen3.attention.layer_norm_rms_epsilon", "rms_norm_eps"),
        "vocab_size": ("tokenizer.ggml.tokens", "vocab_size"),
        "bos_token_id": ("tokenizer.ggml.bos_token_id", "bos_token_id"),
        "eos_token_id": ("tokenizer.ggml.eos_token_id", "eos_token_id"),
    }
    architecture_checks: dict[str, Any] = {}
    for label, (gguf_key, config_key) in metadata_map.items():
        gguf_value = reader.fields[gguf_key].contents()
        if label == "vocab_size":
            gguf_value = len(gguf_value)
        gguf_value = scalar(gguf_value)
        source_value = config[config_key]
        if isinstance(gguf_value, float) or isinstance(source_value, float):
            matches = abs(float(gguf_value) - float(source_value)) <= 1e-10
        else:
            matches = gguf_value == source_value
        architecture_checks[label] = {
            "gguf": gguf_value,
            "source": source_value,
            "match": matches,
        }

    gguf_tokens = list(reader.fields["tokenizer.ggml.tokens"].contents())
    gguf_merges = list(reader.fields["tokenizer.ggml.merges"].contents())
    model_vocab = tokenizer_json["model"]["vocab"]
    added = {int(item["id"]): item["content"] for item in tokenizer_json["added_tokens"]}
    source_tokens: dict[int, str] = {int(idx): token for token, idx in model_vocab.items()}
    source_tokens.update(added)
    comparable_ids = sorted(source_tokens)
    token_mismatches = [
        {"id": idx, "gguf": gguf_tokens[idx], "source": source_tokens[idx]}
        for idx in comparable_ids
        if idx >= len(gguf_tokens) or gguf_tokens[idx] != source_tokens[idx]
    ]
    source_merges = [" ".join(pair) if isinstance(pair, list) else pair for pair in tokenizer_json["model"]["merges"]]
    merge_mismatches = [
        idx for idx, (left, right) in enumerate(zip(gguf_merges, source_merges)) if left != right
    ]

    corpus = [
        "Hello, world!",
        "你好，世界！",
        "def fibonacci(n):\n    if n < 2:\n        return n",
        "The quick brown fox jumps over the lazy dog.",
        "<|im_start|>user\n2+2?<|im_end|>\n<|im_start|>assistant\n",
        "Reason carefully: 17 * 23 =",
    ]
    source_tokenizer = AutoTokenizer.from_pretrained(args.source, local_files_only=True)
    import openvino_genai as ov_genai

    gguf_tokenizer = ov_genai.Tokenizer(str(args.gguf))
    corpus_checks = []
    for prompt in corpus:
        source_ids = source_tokenizer.encode(prompt, add_special_tokens=False)
        gguf_ids = [int(item) for item in gguf_tokenizer.encode(prompt, add_special_tokens=False).input_ids.data[0]]
        corpus_checks.append(
            {
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "source_ids": source_ids,
                "gguf_ids": gguf_ids,
                "match": source_ids == gguf_ids,
            }
        )

    tensor_checks: list[dict[str, Any]] = []
    weight_path = args.source / "model.safetensors"
    with safe_open(weight_path, framework="pt", device="cpu") as tensors:
        source_keys = set(tensors.keys())
        mapped_source_keys = set()
        for tensor in reader.tensors:
            source_name = source_tensor_for_gguf(tensor.name)
            mapped_source_keys.add(source_name)
            source_shape = tuple(int(item) for item in tensors.get_slice(source_name).get_shape())
            gguf_shape = tuple(int(item) for item in tensor.shape)
            tensor_checks.append(
                {
                    "gguf": tensor.name,
                    "source": source_name,
                    "gguf_shape": gguf_shape,
                    "source_shape": source_shape,
                    "match_after_storage_order_reversal": gguf_shape == tuple(reversed(source_shape)),
                }
            )
        unmapped_source = sorted(source_keys - mapped_source_keys)
        embedding = tensors.get_tensor("model.embed_tokens.weight")
        lm_head = tensors.get_tensor("lm_head.weight")
        embedding_bytes = embedding.view(torch.uint8).numpy().tobytes()
        lm_head_bytes = lm_head.view(torch.uint8).numpy().tobytes()
        tied_weight_check = {
            "config_tie_word_embeddings": bool(config.get("tie_word_embeddings")),
            "embedding_sha256": hashlib.sha256(embedding_bytes).hexdigest(),
            "lm_head_sha256": hashlib.sha256(lm_head_bytes).hexdigest(),
            "byte_identical": bool(torch.equal(embedding, lm_head)),
        }

    files = []
    for path in sorted(item for item in args.source.iterdir() if item.is_file()):
        files.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})

    chat_template = tokenizer_config.get("chat_template", "")
    gguf_chat_template = str(reader.fields["tokenizer.chat_template"].contents())
    all_architecture_match = all(item["match"] for item in architecture_checks.values())
    all_tensor_shapes_match = all(item["match_after_storage_order_reversal"] for item in tensor_checks)
    all_corpus_match = all(item["match"] for item in corpus_checks)
    canonical_template_overlay_required = chat_template != gguf_chat_template
    structural_pass = (
        all_architecture_match
        and not token_mismatches
        and len(gguf_merges) == len(source_merges)
        and not merge_mismatches
        and (chat_template == gguf_chat_template or canonical_template_overlay_required)
        and all_tensor_shapes_match
        and all_corpus_match
        and tied_weight_check["byte_identical"]
    )
    functional_summary = None
    classification = "PENDING_FUNCTIONAL_CHECK" if structural_pass else "UNRESOLVED"
    if args.functional:
        functional = json.loads(args.functional.read_text(encoding="utf-8"))
        functional_summary = {
            "artifact": str(args.functional),
            "prompt_count": functional["prompt_count"],
            "first_token_matches": functional["first_token_matches"],
            "full_eight_token_matches": functional["full_eight_token_matches"],
        }
        if structural_pass and functional["first_token_matches"] == functional["prompt_count"]:
            classification = "STRONGLY_SUPPORTED"
        else:
            classification = "UNRESOLVED"

    payload = {
        "schema": "heterospec.358h.reconstructed_source_equivalence.v1",
        "formal_measurement": False,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "historical_exact_source_recovered": False,
        "source": {
            "repository": "Qwen/Qwen3-0.6B",
            "revision": args.source_revision,
            "role": "reconstructed_runtime_source",
            "files": files,
        },
        "canonical_gguf": {
            "repository": "Qwen/Qwen3-0.6B-GGUF",
            "revision": "23749fefcc72300e3a2ad315e1317431b06b590a",
            "sha256": sha256(args.gguf),
        },
        "architecture_checks": architecture_checks,
        "tokenizer": {
            "gguf_token_count": len(gguf_tokens),
            "source_defined_token_count": len(source_tokens),
            "all_source_defined_tokens_match_by_id": not token_mismatches,
            "token_mismatches": token_mismatches[:20],
            "gguf_extra_reserved_token_slots": len(gguf_tokens) - len(source_tokens),
            "gguf_merge_count": len(gguf_merges),
            "source_merge_count": len(source_merges),
            "merge_mismatch_count": len(merge_mismatches),
            "chat_template_exact_match": chat_template == gguf_chat_template,
            "canonical_gguf_template_overlay_required": canonical_template_overlay_required,
            "canonical_gguf_template_overlay_policy": "Exported OpenVINO tokenizer_config.json must use the frozen GGUF template verbatim before qualification.",
            "chat_template_source_sha256": hashlib.sha256(chat_template.encode("utf-8")).hexdigest(),
            "chat_template_gguf_sha256": hashlib.sha256(gguf_chat_template.encode("utf-8")).hexdigest(),
            "fixed_corpus": corpus_checks,
            "all_fixed_corpus_token_ids_match": all_corpus_match,
        },
        "tensors": {
            "gguf_tensor_count": len(reader.tensors),
            "mapped_tensor_count": len(tensor_checks),
            "all_shapes_match_after_storage_order_reversal": all_tensor_shapes_match,
            "unmapped_source_tensors": unmapped_source,
            "tied_weight_check": tied_weight_check,
            "checks": tensor_checks,
        },
        "structural_equivalence_pass_with_canonical_template_overlay": structural_pass,
        "functional_equivalence_summary": functional_summary,
        "classification": classification,
        "limitation": "The historical source commit remains unrecoverable; structural equivalence cannot prove weight-value identity after Q8_0 quantization. The immutable candidate's chat template differs from the GGUF and must be replaced verbatim by the frozen GGUF template in the runtime representation.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "structural_equivalence_pass": structural_pass,
        "architecture_match": all_architecture_match,
        "tokenizer_match": not token_mismatches and not merge_mismatches and all_corpus_match,
        "chat_template_match": chat_template == gguf_chat_template,
        "tensor_shapes_match": all_tensor_shapes_match,
        "output": str(args.output),
    }, indent=2))
    return 0 if structural_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
