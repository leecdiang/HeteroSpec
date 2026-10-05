import openvino as ov

print("OpenVINO:", ov.__version__)
core = ov.Core()
print("available_devices:", core.available_devices)

for device in core.available_devices:
    try:
        name = core.get_property(device, "FULL_DEVICE_NAME")
    except Exception as exc:
        name = f"FAILED_TO_READ_NAME: {exc}"
    print(device, "->", name)
