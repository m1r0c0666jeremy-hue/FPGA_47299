# 原始基线副本

`lab1` 保留从本地SC500 720P Lab1压缩包导入的工程、源码、约束及IP结构。入口为 `lab1/td_project/camera_to_dsi_display.al`，顶层 `design_top_wrapper`。逐文件哈希见 `../reports/source_manifest.json`。

该副本用于对照，不随正式工程修改；不包含包内旧编译产物。新编译结果在 `../build/baseline`，日志在 `../reports/baseline_build.log`。正常开发使用 `../td_project/criticalwork.al`。

基线编译通过不证明其引脚匹配实际板卡。所有bit均引脚待核对、暂不可上板；未做实物验收。
