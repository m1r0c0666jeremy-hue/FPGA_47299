# 05_roi_processing

职责：局部区域裁剪、放大及跟随/固定观察区。

2026-10-05：ScalingTest 已实现 `scaling_line_reader.v` 并加入 `td_project/scaling_test.al`。采用两组完整行缓存、240 个 128 位事务/源图行和 1／2／4 倍最近邻显示；帧内固定取图参数及 DDR 读缓存区，欠载后本帧剩余视频变黑，保留 OSD，旧响应排空后在后续帧恢复。固定观察区仍为实时视频，未实现自动跟踪。

接口、缓存所有权与验证边界见 [ScalingTest说明](../../docs/ScalingTest使用与实现.md)。软件验证不代表板上验收。
