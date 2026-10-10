# 帧头修复与宽范围颜色版本

工程 `td_project/target_lock_robust.al`；构建脚本 `scripts/build_target_lock_robust.tcl`。

bit SHA256：`f065ae6c179ece9b51384bc5cbefed8149c298703fa7e4199072138fe670411d`。

TD6.2.168116 / PH1P35MDG324 −3，SWNS+0.149ns、HWNS+0.020ns。原960字打包仅720字写入缺陷已修复并通过仿真。新bit未上板；所有闪屏原因和宽阈值实物识别效果尚待队友验收。详见 `reports/LockingnTracking采集修复验证报告.md` 和最终 `reports/robust_build_manifest.json`。不得用旧构建入口覆盖旧bit。
