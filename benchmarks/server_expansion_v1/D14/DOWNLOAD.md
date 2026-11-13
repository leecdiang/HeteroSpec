# Download first; no GPU use

```bash
MODEL_DIR="$HOME/heterospec-models"
mkdir -p "$MODEL_DIR"
hf download Qwen/Qwen3-14B-GGUF Qwen3-14B-Q8_0.gguf \
  --revision c75e7b2d0234068f674a1bacf548ea32e27ccd29 --local-dir "$MODEL_DIR"
printf '%s  %s\n' 'a0dfe649137410b7d82f06a209240508e218f32f5b6fd81b69d6932160cfcd9d' \
  "$MODEL_DIR/Qwen3-14B-Q8_0.gguf" | sha256sum -c -
```

File size15,698,533,728 bytes (15.70GB decimal); exact same weight bytes as the
historical14B deployment. Keep Qwen3-0.6B Q8 draft (639,446,688 bytes, SHA in
models.json). Do not substitute Q4, FP16, a different converter or a larger draft.
Only use the approved user-space hf installation; do not upgrade company Python.
Alternatively shared/acquire.py implements standard-library range resume and exact
size/hash validation. Avoid shared storage/network interference with PR196 timing.
Do not load the model after download until the actual GPU allocation is approved.
