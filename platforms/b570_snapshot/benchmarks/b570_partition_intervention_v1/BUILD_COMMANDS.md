# New frontend build identity

Configured and built in the independent worktree using:

```
python scripts/platform/b570_partition_intervention_v1/build_source.py
cmake -S scripts/platform/b570_partition_intervention_v1 -B C:/hs/b570-partition-intervention-v1-build -G "Visual Studio 17 2022" -A x64
cmake --build C:/hs/b570-partition-intervention-v1-build --config Release --parallel 4
```

CMake detected MSVC 19.44.35228.0, compiler path under Visual Studio 2022 BuildTools/VC/Tools/MSVC/14.44.35207, Windows SDK 10.0.26100.0, and host build 10.0.26300. The new executable links the read-only retained b10839 static/import libraries; all seven copied DLLs match the prior frozen DLL digests. Model/dataset bytes were freshly rehashed before R0. The runtime's source identity is verified against the retained upstream archive, with the already-known observational direct-ID header exception. The old speculative example's instrumentation is retained; generated_speculative.cpp adds the new fork observer without editing that historical source.

The authoritative runtime identity is the real source/library/executable/DLL/model hashes in BUILD_IDENTITY.json. No old environment identity is inherited. Boundary input audits rehash the executable, DLLs, retained original CLI, models and dataset and check environment and frozen formal source. Chinese OS-caption display encoding is not used as a device/OS identity field; numeric OS build, GPU names/driver IDs and Vulkan version are separately recorded.
