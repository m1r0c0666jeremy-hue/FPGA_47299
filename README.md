# 摄像头、图像处理与 HDMI 显示工程
Maintainer: Fle & Jeremy

## 当前实施：区域示教与顺序报警第一阶段（2026-10-22）

工作分支`feature/region-sequence-stage1`，独立入口`td_project/target_color_regions_stage1.al`。支持十字准心示教A–D四区、撤销/删除、顺序测试、乱序/回访蜂鸣报警、暂停、静音和重测；原有四模式、两配色、五倍率与校准/跟踪继续保留。

保留全部功能，当前采用有效计数保护的区域存储及按有效顶点分组写入的显示快照，控制复位、接口和节拍不变。最新032009整机布局为19974 Slice/19729 LUT6/23711寄存器/99 ERAM/40 DSP，比前一C结构版多155 Slice，比优化前少278 Slice；降低驱动负担有这项资源代价，不能把局部+9 Slice当整机结果。当前d61da97新源码110/110软件全部通过（software_current_20261024_0406），含真实4区32点、84视频组合与4组实际capture/DDR/显示连接。唯一034232采用官方routability/16线程，原约束不变，最终零冲突布线与时序尚待通过，无本阶段可交付bit。见[验证与资源对比](reports/stage1/validation.md)、[中文操作与实测表](docs/区域顺序_第一阶段_操作与实测.md)、[执行记录](docs/区域顺序_第一阶段_执行记录.md)。旧版交付与原工程保留。

## 当前实施：颜色识别、视频稳定性与显示功能改进

分支 `release/transparent-ring-stability-20261015`，基线 `2f79847`。本轮入口为 **`td_project/target_color_regions_refined.al`**：独立DDR握手/恢复与相机应答监督、定向背景校准、五档倍率、透明官方Logo、默认底栏及校准提示和v4板内延迟。原工程、历史bit及源码包保留。

10月19日按Jeremy要求取消三个诊断分页及KEY2+KEY3切页，保留四种图像模式、两配色和五档倍率。资源与交付状态见下方清单。

软件与完整TD构建通过，实物待验。[独立测试bit](build/target_color_regions_refined_20261019_100417/target_color_regions.bit)、[同源源码包](build/target_color_regions_refined_20261019_100417/color_video_refined_source.zip)。建立+0.142ns，保持+0.020ns；ERAM100/108，DSP40/40。

[一页校准与拍摄说明](docs/颜色视频显示改进_上板一页.md)、[诊断数字解释](docs/颜色视频显示改进_诊断字段.md)、[验证报告](reports/refined/最终验证报告.md)、[实物复测表](reports/refined/hardware_retest.csv)。实物尚未验证。

新生成器：`scripts/generate_refined_regions.py [--check]`；构建：`scripts/run_refined_build.py --stage full`；审计：`scripts/audit_refined.py --regression --attempt <完整构建目录>`。每次构建使用独立冻结目录；旧生成和构建入口继续属于下方历史版本。

## 当前分支：透明色环稳定性优化（2026-10-15）

`feature/transparent-ring-stability`，基线43564ee；在独立工作区实施四步材料/背景校准、候选质量、v3同帧诊断、官方图标、组合键和默认180°显示，保留双色工具/尖端/跟随。软件与TD通过，实物待验。

[新独立上板测试bit](build/target_color_regions_ring_stability_20261015_033550/target_color_regions.bit)、[同源源码包](build/target_color_regions_ring_stability_20261015_033550/transparent_ring_stability_source.zip)、[操作与最小复测](docs/透明色环稳定性优化_上板与复测.md)、[实际验证报告](reports/transparent_ring/最终验证报告.md)。历史bit和下方历史说明保留，不能用旧bit执行四步流程。

本版实际Slice18981/21216、ERAM100/108、DSP40/40，建立+0.110ns/保持+0.020ns。新输出独立且输入冻结，未放宽约束。完整构建用 `scripts/run_stable_regions_build.py --stage full --prefix ring_stability`；只读审计用 `scripts/audit_color_regions.py --attempt build/ring_stability_full_20261015_014510 --check-build`。不要直接重跑冻结目录run.tcl覆盖历史输出。

## 当前正式工程：双色工具识别、尖端定位与自动跟随（2026-10-14）

本地仓库 `D:/aaa_FPGA/color-regions-env-issues`，分支 `docs/color-regions-env-issues`，基线 `0735398`。沿用 `td_project/target_color_regions.al`：固定白平衡与两组材料校准、八邻域去孤立、80×45 双银行网格、每色四候选、中央选取一件工具、K=0.5 尖端和平滑放大跟随。四页面、配色与倍率操作保留。

[正式 bit](build/target_color_regions_stable_20261014_040811/target_color_regions.bit)、[同源源码包](build/target_color_regions_stable_20261014_040811/color_regions_stable_source.zip)。

[上板与校准](docs/双色工具正式功能版上板.md)、[软件／构建／实物验证报告](reports/双色工具正式功能版验证报告.md)、[正式 bit 与同源 ZIP 清单](reports/stable_regions_delivery.json)。新版实物验收待执行，记录表为 `reports/stable_regions_hardware_trials.csv` 和 `reports/stable_regions_hardware_metrics.csv`。下载文件以新交付清单为准；下方旧版本路径和数据保留为历史记录。

生成正式资产：`python scripts/generate_target.py --color-regions`；只读核对加 `--check`。完整编译：`python scripts/run_stable_regions_build.py --stage full`，每次创建新版本目录。只读审计：`python scripts/audit_color_regions.py --attempt build/最终构建目录 --check-build`。旧版本生成器和无参数入口不用于本次正式工程。

---

## 当前功能工程：独立颜色区域框选（2026-10-13）

唯一推荐的新功能入口为 `td_project/target_color_regions.al`，下载 [target_color_regions.bit](build/target_color_regions/target_color_regions.bit)。采用四像素并行的相对色差/简化色相分类、全图粗网格寻找、局部连通区域分离和三帧确认，每色最多两个独立框；四页为原图、色彩高亮、灰度、色彩二值。移除顶部大诊断面板与旧尖端/自动跟随链路，底栏及原按键、手动倍率保留。

[上板操作与测试](docs/LockingnTracking颜色区域功能版上板.md)、[验证报告](reports/LockingnTracking颜色区域功能版验证报告.md)、[交付与哈希](reports/color_regions_delivery.json)。软件与TD综合布局布线通过：Slice19873、LUT6 18429、ERAM85、DSP9；SWNS+0.128ns/HWNS+0.020ns。bit SHA256 `87956070e9ddfb8d1c3c56cef5adf830b6513b34e9f1d3cd4a5ff2554d8a1e0f`。实物尚未验收，请先验证清晰色环/打印颜色与视频稳定性。后面的老师诊断及旧候选章节是保留的历史入口，不参与新工程编译。工作区从e82a62f继续，没有重置、提交或推送；帧头丢字修复及10份已有bit保持。

## 当前实验：老师 YCbCr 思路的独立颜色诊断（2026-10-12）

从 `LockingnTracking` 的 `e82a62f` 继续，新增8×8真实AWB前后RGB与AWB后Y/Cb/Cr采样、四页旧RGB掩码对照，以及独立窗口标定工具。原判色、面积/填充规则、帧头修复及正常工程保留；当前YCbCr目标分类尚未用实物数据标定。

- 入口：[诊断上板操作](docs/LockingnTracking老师判色诊断上板操作.md)、[标定工具](docs/LockingnTracking老师判色标定工具.md)、[实测记录表](reports/teacher_color_hardware_record.csv)。
- 独立工程 `td_project/target_teacher_color_diag.al`、构建脚本 `scripts/build_target_teacher_color_diag.tcl`、下载输出 `build/target_teacher_color_diag/target_teacher_color_diag.bit`。最终有效版本/构建状态以 `reports/teacher_color_delivery.json` 为准。
- 诊断版 `598716C1` 已通过软件回归、TD综合布局布线及97项输入/9份旧bit哈希审计：Slice20117、LUT6 17612、ERAM75、DSP19，SWNS+0.125ns/HWNS+0.012ns。完整记录见[诊断验证报告](reports/LockingnTracking老师判色诊断验证报告.md)。没有真实样本时不启用YC窗口，不声称色环识别已修复。当前改动尚未提交/推送、未下载或烧Flash；按操作说明先做SRAM诊断采样。

## 最新存档：单色候选功能与帧头丢字修复（2026-10-11）

当前 LockingnTracking 活动源码采用单色候选框与中文诊断存档 `f395cc0` 的功能与颜色参数，只移植 `cf8b7c4` 的 `video_in.v` 帧头暂存／跨时钟握手修复。存档名：**LockingnTracking：恢复单色候选并修复帧头丢字**。代码提交 `fc383a5066740a4cb1b6a425cea64da554ca3cca`，已通过保留远端历史的合并提交推送到 GitHub `LockingnTracking`。远端分支地址：[FPGA_47299 / LockingnTracking](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/LockingnTracking)。

- TD 工程：[target_lock_candidates_ingress.al](td_project/target_lock_candidates_ingress.al)，BitWriter 文件：[target_lock_candidates_ingress.bit](build/target_lock_candidates_ingress/target_lock_candidates_ingress.bit)，SHA256 `92fba519873b691074582b614f03eb081b45b07735934e846767956599803b7d`。
- 完整说明：[Git恢复与帧头修复](docs/LockingnTracking_Git回退与帧头修复_2026-10-11.md)，[工程使用及回归入口](docs/LockingnTracking单色候选与帧头修复.md)，[验证报告](reports/LockingnTracking单色候选与帧头修复验证报告.md)。
- 960 个打包字写入 960 个 DDR 字及视频回归通过；新组合仍需上板验证，不能据此宣称颜色识别或硬件验收通过。

## 最新开发：单色候选框与诊断（2026-10-10）

开启搜索后，红／蓝或黄／紫各自通过检查即可独立画框；只有双色连续3帧合格才显示估算尖端并跟随。视频区新增A/B像素数、填充率和失败原因，KEY3长按可一并隐藏。颜色阈值及原操作不变。

- [单色候选操作与模块路径](docs/LockingnTracking单色候选诊断.md)、[本轮验证报告](reports/LockingnTracking单色候选验证报告.md)。
- 新工程 `td_project/target_lock_candidates.al`，构建脚本 `scripts/build_target_lock_candidates.tcl`，输出 `build/target_lock_candidates/target_lock_candidates.bit`。旧工程和bit保留。
- 存档名：**LockingnTracking：存档单色候选框与中文诊断联调版本**。单元、帧同步、完整视频、72幅OSD及原算法回归通过；TD综合布局布线和源码／bit同源审计通过。
- 仍为联调版本，旧采集帧头丢数据及离焦识别问题未修复。本次按Jeremy要求完成后提交并上传LockingnTracking，不合并main，不下载板卡或烧Flash。

## 最新开发：双配色、中文标注与KEY3长短按（2026-10-09）

在LockingnTracking的061cfd7上新增中文随目标标签、红蓝／黄紫切换和KEY3长短按。**SW3=0红A蓝B，SW3=1黄A紫B；KEY3短按松手启停，长按1秒显隐视频标注；KEY2改为按SW4增减增益。** 长按隐藏仍检测／跟随，底栏状态、配色、标定和安路Logo保留。KEY4按SW4缩放、SW1/2四模式保持。

- [最新操作、参数及接口](docs/LockingnTracking双配色与中文标注.md)，[本轮验证报告](reports/LockingnTracking双配色验证报告.md)。下方旧操作仅作历史，不再按SW3控制显隐／增益。
- 独立入口 `td_project/target_lock_dualcolor.al`／`scripts/build_target_lock_dualcolor.tcl`，输出 `build/target_lock_dualcolor/target_lock_dualcolor.bit`；旧工程及bit保留。
- 存档名：**LockingnTracking：存档中文标注、双配色与KEY3长短按联调版本**。2026-10-09按Jeremy要求将源码、同源bit和验证证据一并纳入本次Git存档，上传目标仅为GitHub的LockingnTracking分支。
- 本轮不加入离焦滤波、锐化或双线性。原帧头丢数据问题未修复；构建同源及本轮软件验证不代替完整采集接入和实物验收。未下载、烧Flash或合并main。

## 最新接续：同步队友实物测试记录（2026-10-08）

已将本地 LockingnTracking 从 `067664c` 快进到 GitHub 同名分支 `21609e587b3d68540f85ec1856ae5b2d7d8966f6`，接收两条提交、三个文档文件的更新；检测源码、参数和 bit 没有随这次远端更新改变。Jeremy确认队友实测“离焦模糊时可以锁定、对焦清晰后不能锁定”，详见 [实物问题记录](docs/实物问题记录_对焦依赖检测.md)。这属于部分实物观察，不是完整验收通过。

本地接续存档名：**LockingnTracking：同步队友实物测试记录并存档离焦锁定问题**。本轮只同步、阅读代码并记录说明，未修复、重新构建或下载；新接续提交仅保存在本地，未推送。标记不要求圆形，颜色、面积、填充率及跟踪条件说明见 [本次接续说明](docs/LockingnTracking接续_2026-10-08.md)。下文2026-10-07内容保留为开发历史，中间bit和采集接入问题仍待处理。

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
