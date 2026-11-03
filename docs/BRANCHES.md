# 分支与版本

首次使用建议从 `main` 开始。不同分支的按键分配、配色、工程入口和 bit 文件可能不同，请使用同一分支内的文件。

| 分支 | 用途 |
|---|---|
| [Behaviour_region_1024](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/Behaviour_region_1024) | 矩形区域示教与顺序检查 |
| [ColorRegionDetection](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/ColorRegionDetection) | 独立颜色区域检测 |
| [EN_Project_1020](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/EN_Project_1020) | 颜色识别与五档放大观察 |
| [Final_Mode_1028](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/Final_Mode_1028) | 基于 FPGA 的精密操作视觉辅助系统 |
| [Final_Mode_1101](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/Final_Mode_1101) | 精密操作视觉辅助系统：配色与帧率演示版 |
| [ImagePreprocess](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/ImagePreprocess) | 摄像头图像处理与 HDMI 显示 |
| [ImproveFourfoldScale](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/ImproveFourfoldScale) | 四倍双线性放大 |
| [LockingnTracking](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/LockingnTracking) | 双色工具定位与单色候选显示 |
| [Region_Recognition_1019](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/Region_Recognition_1019) | 颜色识别与五档放大观察 |
| [ScalingTest](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/ScalingTest) | 手动选点放大与中文 OSD |
| [Teach_auto_routine_1027](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/Teach_auto_routine_1027) | 工具路线录制与顺序回放 |
| [docs/color-regions-env-issues](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/docs%2Fcolor-regions-env-issues) | 历史文档与实物问题记录；对应功能：双色工具定位与自动跟随 |
| [docs/contributor-note](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/docs%2Fcontributor-note) | 历史文档与实物问题记录；对应功能：摄像头图像处理与 HDMI 显示 |
| [docs/git-workflow-and-identity](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/docs%2Fgit-workflow-and-identity) | 历史文档与实物问题记录；对应功能：摄像头图像处理与 HDMI 显示 |
| [docs/locking-tracking-focus-issue](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/docs%2Flocking-tracking-focus-issue) | 历史文档与实物问题记录；对应功能：双色工具定位与跟踪实验 |
| [docs/region-recognition-1019-feedback](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/docs%2Fregion-recognition-1019-feedback) | 历史文档与实物问题记录；对应功能：颜色识别与五档放大观察 |
| [docs/scalingtest-acceptance](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/docs%2Fscalingtest-acceptance) | 历史文档与实物问题记录；对应功能：手动选点放大与中文 OSD |
| [docs/stable-tool-tracking-issues](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/docs%2Fstable-tool-tracking-issues) | 历史文档与实物问题记录；对应功能：双色工具定位与自动跟随 |
| [main](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/main) | 默认使用版本，采用远端 Final_Mode_1028 的工程代码 |
| [native-1080p](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/native-1080p) | 原生 1080p30 视觉辅助候选工程 |
| [native-720p](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/native-720p) | 720p 源图坐标与局部放大 |
| [release/transparent-ring-stability-20261015](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/release%2Ftransparent-ring-stability-20261015) | 透明色环校准与工具跟踪 |
| [stable-color-tool-tracking](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/stable-color-tool-tracking) | 双色工具定位与自动跟随 |

`native-1080p` 与 `native-720p` 是独立分支，不包含主干的四矩形和路线示教界面。`Final_Mode_1101` 使用红黄 / 蓝紫配色并显示 FPS；`Final_Mode_1028` 使用红蓝 / 黄紫配色。

构建日志、实测结果和时序数字只对应其记录的源码与 bit，不跨版本套用。
