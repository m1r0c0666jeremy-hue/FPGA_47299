# 单色候选与中文诊断存档＋帧头采集修复

> 发布状态（2026-10-11）：代码提交 `fc383a5066740a4cb1b6a425cea64da554ca3cca`，存档名"LockingnTracking：恢复单色候选并修复帧头丢字"；通过合并提交 `b41f0602f92076eb088c5a545f39017a089d44b4` 普通推送至 GitHub `LockingnTracking`。远端保留原有 cf8 历史，活动代码树恢复到 f395 单色候选基线并只移植帧头修复。

使用者 于 2026-10-11 要求：提取"LockingnTracking：修复帧头丢字并放宽双色判色联调版本"里的闪屏修复，应用到"LockingnTracking：存档单色候选框与中文诊断联调版本"。

## 实际源码组合

- 功能、检测器、颜色参数、显示、OSD、生成器与原 TD 工程：`f395cc011ef4c21f15863192ce148938834bd639`。
- 唯一移植的修复源码：`user_source/hdl_source/video_in.v`，字节级等同于 `cf8b7c463a415bd8741fed4ec68ff3eeac252455`。
- 新独立构建工程与输出：`target_lock_candidates_ingress`。它引用旧工程相同源文件和约束，不引用 P0 诊断副本。
- 历史修复中对检测器除法器的优化、宽范围颜色阈值、面积/填充门槛调整均没有移植。

| 参数 | 此版本 |
|---|---:|
| 红蓝强通道最小值 / 通道差 / 比例 | 80 / 32 / 3:2 |
| 黄紫双强通道最小值 / 通道差 / 比例 / 平衡 | 80 / 24 / 5:4 / 2倍 |
| 单色合格像素数量 | 64～20000 |
| 包围框填充率最低 | 30% |
| 中心间距范围 | 16～600像素 |
| 连续确认 / 最大跳变 | 3帧 / 96像素 |
| 尖端模型 | L=40、D=20、K=0.5 |

这些是所选旧存档的参数，不代表重新标定或已解决颜色识别。单色合格可独立画框，双色连续三帧合格才显示尖端并跟随，KEY3 长按隐藏诊断及目标标注。

## 闪屏修复的内容

原写入器在帧头复位 FIFO 时，摄像头已经输出有效打包字，导致前批数据丢失；既有复现为 960 个打包字只有 720 个 DDR 写入。

移植的写入器用 256×128 位暂存 RAM 接收帧头数据，通过请求/确认跨时钟握手等待 DDR 结束旧写入、复位 FIFO、发布新帧地址，随后释放暂存数据。保留逐字顺序与地址推进、四像素采集吞吐、完整帧检查及异常帧溢出拒绝。帧复位期间暂存 RAM 写入是正常行为；禁止的是把数据直接写入正在复位的 FIFO。

原修复文件 SHA256：`6c02b617ef32c478ab39bf17e0fe5e48a3f6e38eca1796bf628cb19052c7838b`。提取的补丁见 `reports/candidate_ingress_frame_fix.patch`，来源和恢复清单见 `reports/candidate_ingress_restore_manifest.json`。

## 工程与验证入口

工程：`td_project/target_lock_candidates_ingress.al`。

```powershell
& 'D:/26_software/TangDynasty/bin/td_commands_prompt.exe' 'D:/aaa_FPGA/criticalwork/scripts/build_target_lock_candidates_ingress.tcl'
```

TD 命令行路径使用正斜杠，避免 Tcl 将 Windows 反斜杠解释为转义字符。输出目录只使用 `build/target_lock_candidates_ingress`。不要运行旧 candidate/robust/P0 构建脚本，否则可能覆盖对应旧输出。

软件回归：`scripts/test_candidates_ingress.py --stage <阶段>`，支持 `unit/ingress/detection/full/video/osd/regression`。复用旧存档原有的输入与黄金参考，所有输出以 `candidate_ingress` 区分；不改写历史测试预期和日志。

生成文件的参数和哈希与 f395 原生成清单一并恢复，审计核对生成器、模板、配置和生成结果，不使用无参数生成器重写旧资产。新构建输入冻结与结果审计：`scripts/audit_candidates_ingress.py`；输入清单、实际构建、软件证据与新 bit 哈希见最终 `reports/candidate_ingress_build_manifest.json`。具体结果见 `reports/LockingnTracking单色候选与帧头修复验证报告.md`。

## 当前操作和回退

SW1/SW2 仍为原图、灰度、边缘、二值化；SW3 上=0 红蓝，下=1 黄紫；SW4 控制 KEY2 亮暗及 KEY4 放大/缩小；KEY1 复位；KEY3 短按检测启停、长按1秒标注显隐。恢复正常四模式，不启用 P0 四个诊断页面。

当前分支仍为 LockingnTracking，Git HEAD 不回移、既有历史不丢弃；工作树记录向旧代码的恢复。之前当前树的3026个 Git 可见文件（含未提交 P0、bit、原型、报告）已逐字节验证备份到：

`D:/aaa_FPGA/archives/LockingnTracking_before_candidates_ingress_20261011_163732.zip`

ZIP SHA256：`f31255130074e54566fd631bdfac287836de6074ff436966e75a1fcf087a9c68`。根 AGENTS 的当时正文也包含在 ZIP 中。旧 bit 全部保留并审计哈希。备份覆盖当时 Git 可见文件，不包括忽略的仿真缓存或 .git；提交历史仍在原仓库中。接续 P0 时需恢复该备份的相应源码、生成器及参数，不能拿当前旧配置配合 P0 模块重新编译。

本轮不提交、不推送、不下载或烧 Flash。使用者 已反馈原 cf8 版本闪屏解决；这个恢复旧颜色参数后的新组合仍需用新 bit 上板检查连续视频、控制、两配色候选/诊断与锁定情况。任何软件或布局通过都不替代新组合的实物验收。
