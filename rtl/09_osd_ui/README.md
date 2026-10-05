# 09_osd_ui

职责：按键界面、图文叠加和安路Logo。

2026-10-05：ScalingTest 已加入综合。`scaling_osd.v` 在四模式处理之后叠加黄色黑边准心、底部96行不透明信息栏、中文模式/原图坐标/倍率/方向/状态及官方图形配“安路科技”。字模和 Logo 为同步块 RAM，RGB 和 VS/HS/DE 一起延迟两拍。

原始 [Logo素材](../../assets/osd/anlogic/README.md) 和前期 [方案记录](../../docs/按键复用与OSD方案_10_4.md) 保留。`scripts/generate_scaling_osd.py` 复用大赛 Lab3 的数字、英文及“安路”字模，补齐所需中文，生成有限字符 ROM 与两位调色板 Logo；生成文件不要手工改，需修改脚本后重新生成。

布局与测试见 [ScalingTest说明](../../docs/ScalingTest使用与实现.md)。尚未上板；实际显示器上的清晰度、开关极性和持续出图待实测。
