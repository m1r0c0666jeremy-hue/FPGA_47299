# 摄像头、图像处理与 HDMI 显示工程
Maintainer: Fle & Jeremy

## 当前开发：LockingnTracking（2026-10-07，接入验证未完成）

从本地main `4c26207` 创建 **LockingnTracking**，main与ImproveFourfoldScale分支保留。新增红前蓝后双色检测、估算尖端、KEY3启停持续跟踪、窗口跟随与SW3标注显隐；沿用main最近邻缩放。

- [使用、参数与实现](docs/LockingnTracking使用与实现.md)、[验证报告与接入问题](reports/LockingnTracking验证报告.md)、[锁定状态OSD仿真预览](reports/target_preview/osd_02.png)。
- 新工程 `td_project/target_lock.al`、构建脚本 `scripts/build_target_lock.tcl`。不要使用旧scaling_test入口编译新顶层。
- L=40mm、D=20mm、K=0.5；修改 `rtl/03_tool_detection/target_config.json` 后运行 `scripts/generate_target.py`，再重新编译。
- 独立控制、检测／跟踪、15组完整显示、10幅OSD及原算法回归通过。**AWB→打包→旧FIFO联调复现帧头数据被复位吞掉；整体接入尚未完成。2026-10-07 Jeremy决定保存并上传本分支，具体测试与问题处理交给队友，本次不继续修复。**
- 存档名：**LockingnTracking：存档双色锁定跟踪与OSD开发版本，待队友联调**。上传目标为GitHub同名分支，提交号以Git记录为准。
- 当前target_lock.bit是中间构建，不代表最新源码同源、不可作为可上板交付。未下载、未烧Flash、未合并main；上传不代表问题已修复或实物验收通过。

以下为旧main及更早版本历史记录，不能作为本分支新功能的上板结论。

## 历史主干：准心、手动缩放与中文 OSD（2026-10-05）

当前为 **main**，已同步远端 `8136663`，包含 ScalingTest 功能及队友首次上板验收记录。Jeremy 本次确认队友的十字准心、放大、OSD 功能测试成功；报告记录第 0～5 步通过，第 6 步连续稳定性观察跳过，仅 SRAM 在线下载、未烧 Flash。测试设备为 HX1P35A V1.0、MLK-CAM001 V1.0（SC500CS）、KTC H25T7。

- 当前工程：[scaling_test.al](td_project/scaling_test.al)，构建脚本：[build_scaling_test.tcl](scripts/build_scaling_test.tcl)。旧 `criticalwork.al` 不适用于当前顶层。
- 当前下载文件：[scaling_test.bit](build/scaling_test/scaling_test.bit)，SHA256：`a598cff3ea804c0fbc9e54d1693e03cfc32fa4b9aef2d7133f234879dc6edf8c`。
- [使用与实现](docs/ScalingTest使用与实现.md)、[实物验收与软件验证报告](reports/ScalingTest验证报告.md)、[Git 存档](docs/Git存档说明.md)。
- SW1/2 选择四模式；KEY1 复位；KEY2 按 SW3 调增益；KEY3 按 SW3/SW4 的 00/01/10/11 下/右/左/上移动；KEY4 按 SW4=1/0 放大/缩小。四个开关均已实测上=0、下=1。
- 1/2/4 倍最近邻放大、黄色黑边准心、底部 96 行中文 OSD 及安路标识已实现。4 倍将 320×156 原图区域放大为 1280×624 视频区，单个源像素重复为 4×4 色块；Jeremy 反馈像素感明显，画质优化尚未实施。
- 当前六个综合功能目录为 00/01/02/05/09/10；自动跟踪、双色检测、尖端标定及准心隐藏仍未实现。

本轮运行 `scripts/audit_scaling.py` 通过，核对 65 个工程依赖、来源和构建输入/bit 哈希及已存档测试日志；未重新仿真、编译或下载。存档名：**同步main：存档队友已验收的十字准心、缩放与OSD功能**。

以下为 2026-10-04 四模式阶段历史说明，旧工程入口、按键用途和“缩放/OSD未实现”等描述仅适用于当时版本。

---

更新：2026-10-04；当前主干 **main**，已同步队友四模式实物验收版本v1.2；功能最初在ImagePreprocess分支开发。平台 HX1P35A / PH1P35MDG324 −3，TD 6.2.168116。

新增拨动开关选择与图像处理，顶层已整合并重新综合、布局布线、生成bit。Jeremy于2026-10-04补充截图确认队友提亮后版本已成功摄像头采集并显示，正常观察未发现补黑；**本轮新增四模式已于 2026-10-04 完成实物验收**（`00/01/10/11` 逐项通过，见[第二轮](reports/图像处理验证_10_3.md)与第三轮记录）；仅 SRAM 在线下载，未烧写 Flash；30 分钟连续运行按 Jeremy 决定跳过、记为未执行。

## 操作与入口

两位顺序是 **SW1、SW2**；SW1=A4，SW2=B4。**实物实测极性为上=0、下=1**（与手册 p21 描述相反，见[图像处理与拨动开关](docs/图像处理与拨动开关_10_3.md) 的"实物更正"节）。

| SW1 SW2 位置 | 模式 | 屏幕效果 |
|---|---|---|
| 上 上 | 00 | 原图，不处理（彩色） |
| 上 下 | 01 | Sobel边缘检测（黑底亮轮廓） |
| 下 上 | 10 | 灰度变换 |
| 下 下 | 11 | 二值化，灰度≥128为白 |

开关稳定约20ms后，在下一帧边界切换（2026-10-04 实物验证）。KEY1复位、KEY2/3曝光调节保持原用途。边缘模式的前两行、前两列为黑色，窗口中心与输出坐标相差1像素，详见[算法与接口说明](docs/图像处理与拨动开关_10_3.md)。

- [TD工程](td_project/criticalwork.al)：顶层 `criticalwork_top`，使用项目相对路径。
- [新增图像处理bit](build/imagepreprocess_10_3/imagepreprocess_10_3.bit)及[使用说明](build/imagepreprocess_10_3/使用说明_10_3.md)。
- [本轮验证报告](reports/图像处理验证_10_3.md)、[当前待解决问题](docs/问题清单_10_3.md)。
- [编译说明](docs/编译说明.md)、[架构](docs/架构与接口.md)、[接线与验收](docs/接线与验收.md)、[Git存档](docs/Git存档说明.md)。

三组针对性仿真通过，其中完整720p测试核对3,688,960个有效像素及同步信号。布线后SWNS +1.177ns、HWNS +0.020ns、STA覆盖96.00%；LUT6 10,850、寄存器13,794、slice 13,390（63.11%）。这些是软件验证，不能代替实物验收。

## 目录与范围

| 目录 | 用途 |
|---|---|
| rtl/00_top_control | 板级顶层、PLL/复位连接、开关同步消抖、状态同步 |
| rtl/01_camera | 配置、MIPI/RAW10、厂家彩色转换与128位打包封装 |
| rtl/02_image_preprocess | 显示侧RGB888原图/边缘/灰度/二值化 |
| rtl/10_memory_video_out | DDR缓存、调度、显示时序、处理模块连接、HDMI |
| rtl其余9个目录 | 职责说明，未实现、未接入综合 |
| user_source | 厂家源码/IP原结构；保留队友已登记7项修改，本轮未改 |
| vendor_reference/lab1 | 独立原始基线，193个文件哈希不变 |
| scripts、sim | 编译、审计、仿真脚本；仿真模型不加入硬件工程 |
| build/imagepreprocess_10_3、reports | 本轮bit与软件验证证据 |

原队友bit仍在 `build/criticalwork/criticalwork.bit`，不包含新增处理模块。历史报告按其对应提交理解，不作为新bit的验证结论。

输出维持1280×720、总周期1650×750、75MHz像素时钟，理论约60.606Hz。不是分辨率放大，也不是已实测的标准60Hz。跟踪、局部放大、对准和“安路”Logo叠加尚未实现。

按Jeremy要求，本轮暂不修改打包复位、缓存尾字、完整帧恢复等旧问题。已解决的基础引脚对照与基本出图不再列入当前待办；未解决项集中见问题清单。迁移工程应携带整个文件夹，不能只复制 `.al`。

## ImproveFourfoldScale 上板验收结论（2026-10-06）

分支 ScalingTest 之上还完成了 **ImproveFourfoldScale** 版本（4 倍的「原图/灰度」改为双线性插值，
1/2 倍与边缘/二值化保持最近邻）。该版本已于 2026-10-06 完成**首次上板 A/B 验收并通过**：

- 结论与量化数据：[docs/ImproveFourfoldScale上板验收结论.md](docs/ImproveFourfoldScale上板验收结论.md)
- 测试流程与判据：[docs/上板测试流程_ImproveFourfoldScale.md](docs/上板测试流程_ImproveFourfoldScale.md)
- 设计与软件验证：[docs/ImproveFourfoldScale使用与实现.md](docs/ImproveFourfoldScale使用与实现.md)、[reports/ImproveFourfoldScale验证报告.md](reports/ImproveFourfoldScale验证报告.md)
- 证据与靶标：[细缝可辨性对比](reports/improve_fourfold_ab/细缝可辨性对比_旧bit_vs_新bit.png)、[四倍缩放 AB 对照卡](docs/四倍缩放AB对照卡_1920x1080.png)

关键数据：4× 原图/灰度边缘过渡宽度 17 → 25 像素（平滑生效），窄缝平均深度 0.71 → 0.71（可辨性未下降）；
1×/2× 与 4× 边缘/二值化与旧 bit 无可辨差异。
**说明**：该版本的 RTL 与 bit 已归档在 `ImproveFourfoldScale` 分支（`86ef777`）；本分支归档说明文档与验收结论，未合并 main。
