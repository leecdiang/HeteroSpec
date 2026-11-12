# Resource reader correction before first S3 request

The first F2 was fully read back but started zero S3 GPU requests. Inspection found that the inherited host checked total minus used memory, which can overstate actually free VRAM because driver-reserved memory is separate. This epoch uses the explicit NVML memory.free field and records gpu_free_bytes. A CPU fixture rejects a case with 2 GiB total-minus-used but only 512 MiB free.

No native binary, numerical object, reference, root, request, order, clock, statistic or budget changed. The previous F2 and readback remain retained. The corrected complete F2 must be publicly read back before starting S3. Earlier measurement data are not overwritten; their old sampling scope must be described accurately.
