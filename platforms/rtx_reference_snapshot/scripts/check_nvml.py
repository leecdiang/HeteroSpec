import os
import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime, timezone

import pynvml


def read_optional(label, call, default=""):
    last_error = None
    for _ in range(3):
        try:
            return call()
        except pynvml.NVMLError as exc:
            last_error = exc
            time.sleep(0.05)
    print(f"NVML read failed for {label}: {last_error}", file=sys.stderr)
    return default


parser = argparse.ArgumentParser()
parser.add_argument("--duration", type=int, default=30)
parser.add_argument("--interval", type=float, default=1.0)
parser.add_argument("--output", default=str(Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1])) / "telemetry" / "nvidia_idle_30s.csv"))
args = parser.parse_args()

pynvml.nvmlInit()
try:
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    name = pynvml.nvmlDeviceGetName(handle)
    power_limit_mw = read_optional("power_limit", lambda: pynvml.nvmlDeviceGetEnforcedPowerLimit(handle), 0)
    print("GPU name:", name)
    print("NVML driver:", pynvml.nvmlSystemGetDriverVersion())
    print("NVML enforced power limit W:", power_limit_mw / 1000 if power_limit_mw else "unavailable")
    fields = ["timestamp", "power_W", "gpu_util_pct", "memory_util_pct", "temperature_C", "sm_clock_MHz", "memory_clock_MHz", "vram_used_MB", "sample_source"]
    with open(args.output, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        start = time.monotonic()
        next_sample = start
        while time.monotonic() - start < args.duration:
            # Hybrid/Optimus can invalidate a persistent NVML handle when the dGPU
            # changes power state. Reinitialize once per 1 Hz sample.
            pynvml.nvmlShutdown()
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = read_optional("utilization", lambda: pynvml.nvmlDeviceGetUtilizationRates(handle), None)
            memory = read_optional("memory", lambda: pynvml.nvmlDeviceGetMemoryInfo(handle), None)
            power_mw = read_optional("power", lambda: pynvml.nvmlDeviceGetPowerUsage(handle), None)
            temperature = read_optional("temperature", lambda: pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU), None)
            sm_clock = read_optional("sm_clock", lambda: pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM), None)
            memory_clock = read_optional("memory_clock", lambda: pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM), None)
            source = "NVML"
            power_invalid = power_mw is None or (power_limit_mw and power_mw > power_limit_mw)
            if util is None or power_invalid or sm_clock is None or sm_clock > 5000:
                query = subprocess.check_output([
                    "nvidia-smi",
                    "--query-gpu=power.draw,utilization.gpu,utilization.memory,temperature.gpu,clocks.current.sm,clocks.current.memory,memory.used",
                    "--format=csv,noheader,nounits",
                ], text=True, encoding="utf-8", errors="replace").strip().split(", ")
                smi_power, smi_gpu, smi_mem_util, smi_temp, smi_sm, smi_mem_clock, smi_vram = query
                if power_invalid:
                    power_mw = float(smi_power) * 1000
                if util is None:
                    gpu_util, memory_util = smi_gpu, smi_mem_util
                else:
                    gpu_util, memory_util = util.gpu, util.memory
                if temperature is None:
                    temperature = smi_temp
                if sm_clock is None or sm_clock > 5000:
                    sm_clock = smi_sm
                if memory_clock is None:
                    memory_clock = smi_mem_clock
                vram_used = smi_vram if memory is None else f"{memory.used / 1024**2:.1f}"
                source = "NVML+nvidia-smi_fallback"
            else:
                gpu_util, memory_util = util.gpu, util.memory
                vram_used = "" if memory is None else f"{memory.used / 1024**2:.1f}"
            writer.writerow({
                "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds"),
                "power_W": "" if power_mw is None else f"{power_mw / 1000:.1f}",
                "gpu_util_pct": gpu_util,
                "memory_util_pct": memory_util,
                "temperature_C": temperature,
                "sm_clock_MHz": sm_clock,
                "memory_clock_MHz": memory_clock,
                "vram_used_MB": vram_used,
                "sample_source": source,
            })
            stream.flush()
            next_sample += args.interval
            time.sleep(max(0.0, next_sample - time.monotonic()))
finally:
    pynvml.nvmlShutdown()
