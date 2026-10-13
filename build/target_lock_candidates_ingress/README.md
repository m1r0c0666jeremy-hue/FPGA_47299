# f395单色候选＋cf8帧头修复

独立 bit：`target_lock_candidates_ingress.bit`。SHA256 `92fba519873b691074582b614f03eb081b45b07735934e846767956599803b7d`。

基线f395、仅video_in使用cf8；其余旧判色/诊断/跟踪保持。Slice19105、LUT617250、ERAM56、DSP31；SWNS+0.117ns/HWNS+0.020ns。软件与TD通过，新组合实物待验。

见 `docs/LockingnTracking单色候选与帧头修复.md` 与对应报告/清单。原bit保留。
