# 双配色中文标注：独立联调构建

本目录由 `scripts/build_target_lock_dualcolor.tcl` 生成，工程是 `td_project/target_lock_dualcolor.al`，输出 `target_lock_dualcolor.bit`。旧 `build/target_lock/target_lock.bit` 保持原样。

操作、L/D标定、颜色阈值和复现实验见 `docs/LockingnTracking双配色与中文标注.md`。构建输入与bit SHA256见 `reports/dualcolor_build_manifest.json`，测试、资源、时序和边界见 `reports/LockingnTracking双配色验证报告.md`。

本bit仅用于队友联调。既有AWB→打包→video_in帧头FIFO复位丢数据问题仍在；软件测试和源码同源构建不等于完整采集接入通过，不证明清晰画面识别、真实色环适配或上板稳定性。本轮未下载、未烧Flash。
