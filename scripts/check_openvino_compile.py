import numpy as np
import openvino as ov

core = ov.Core()
parameter = ov.opset13.parameter([1, 4], np.float32, name="input")
constant = ov.opset13.constant(np.ones((1, 4), dtype=np.float32))
result = ov.opset13.add(parameter, constant)
model = ov.Model([result], [parameter], "gate0_toy_add")

devices = list(core.available_devices)
targets = ["CPU"]
gpu = next((d for d in devices if d == "GPU" or d.startswith("GPU.")), None)
if gpu:
    targets.append(gpu)
if "NPU" in devices:
    targets.append("NPU")

for target in targets:
    try:
        compiled = core.compile_model(model, target)
        output = compiled([np.zeros((1, 4), dtype=np.float32)])[0]
        ok = np.allclose(output, np.ones((1, 4), dtype=np.float32))
        print(f"{target}: COMPILE_PASS inference={ok}")
    except Exception as exc:
        print(f"{target}: COMPILE_FAIL {type(exc).__name__}: {exc}")

missing = [name for name in ("CPU", "GPU", "NPU") if not any(d == name or d.startswith(name + ".") for d in devices)]
if missing:
    raise SystemExit("FAIL missing devices: " + ", ".join(missing))
