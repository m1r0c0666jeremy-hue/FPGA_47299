# 05_roi_processing

职责：局部区域裁剪、放大及跟随/固定观察区。

2026-10-05：ScalingTest 已实现 `scaling_line_reader.v` 并加入 `td_project/scaling_test.al`。采用两组完整行缓存、240 个 128 位事务/源图行和 1／2／4 倍最近邻显示；帧内固定取图参数及 DDR 读缓存区，欠载后本帧剩余视频变黑，保留 OSD，旧响应排空后在后续帧恢复。固定观察区仍为实时视频，未实现自动跟踪。

接口、缓存所有权与验证边界见 [ScalingTest说明](../../docs/ScalingTest使用与实现.md)。软件验证不代表板上验收。

## ImproveFourfoldScale（2026-10-06）

当前分支采用四个逻辑行缓存、四份同步写入的打包RAM和 `bilinear_rgb.v`。仅原图/灰度4倍启用双线性；其他组合保持最近邻。模式、窗口、倍率在同一帧边界生效，五级缩放流水线每拍一个RGB888像素。使用独立improve_fourfold_scale工程，详见[新说明](../../docs/ImproveFourfoldScale使用与实现.md)及[报告](../../reports/ImproveFourfoldScale验证报告.md)。新bit待上板。
