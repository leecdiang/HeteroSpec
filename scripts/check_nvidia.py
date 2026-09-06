import torch

print("torch:", torch.__version__)
print("cuda runtime:", torch.version.cuda)
print("cuda available:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("device count:", torch.cuda.device_count())
    for index in range(torch.cuda.device_count()):
        prop = torch.cuda.get_device_properties(index)
        print(f"device {index}:", torch.cuda.get_device_name(index))
        print(f"device {index} VRAM GiB:", prop.total_memory / 1024**3)
        print(f"device {index} capability:", torch.cuda.get_device_capability(index))
else:
    raise SystemExit("FAIL: CUDA is unavailable; CPU fallback is forbidden")
