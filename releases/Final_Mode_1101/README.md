# Final_Mode_1101 下载文件

本目录提供 [target_color_regions.bit](target_color_regions.bit)，先用 BitWriter 下载到 SRAM 测试。

SHA256：`7998532c9ef6678883f1035e7fea374ed977065c73694ab8288ee98ba4866bd4`。

工程入口为仓库根目录下的 `td_project/target_color_regions_stage1.al`。默认前红后黄，备用前蓝后紫；完整操作见 [使用手册](../../docs/USER_GUIDE.md)。

实际编译提交为 `27da04b18bf1ed71d445a852be23d075f0eaf9db`。158 项当前检查及 160 项基础回归通过，最终 DRC 冲突为 0，无异常时序路径，建立余量 +0.006ns、保持余量 +0.020ns。独立核验见本目录的 `independent_verification.json`。

仍沿用旧 DDR 配置，花屏及连续运行稳定性需单独实测。
