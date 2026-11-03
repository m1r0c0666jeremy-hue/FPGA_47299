# 双色工具定位与单色候选显示

对合格单色区域独立画框，双色连续确认后估算尖端并跟随。帧头暂存和跨时钟握手用于处理采集帧头数据丢失；颜色参数仍需结合材料和照明验证。

当前分支：`LockingnTracking`。这是独立功能或历史实验分支。完整的区域与路线操作见 [main](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/main)。

## 快速开始

1. 准备 HX1P35A 开发板、SC500CS 摄像头、HDMI 显示器和下载器。
2. 在 TD 6.2.168116 中打开 [td_project/target_lock_candidates_ingress.al](td_project/target_lock_candidates_ingress.al)，或直接下载下表的 bit。
3. 先通过 BitWriter 下载到 SRAM，复位后确认原图，再按使用手册校准和操作。

| 文件 | 路径 |
|---|---|
| TD 工程 | [td_project/target_lock_candidates_ingress.al](td_project/target_lock_candidates_ingress.al) |
| 下载文件 | [build/target_lock_candidates_ingress/target_lock_candidates_ingress.bit](build/target_lock_candidates_ingress/target_lock_candidates_ingress.bit) |
| 操作手册 | [连接、校准、开关与按键](docs/USER_GUIDE.md) |
| 编译与校验 | [工程入口、下载步骤与 SHA256](docs/BUILD.md) |
| 版本选择 | [分支说明](docs/BRANCHES.md) |

## 操作速查

| 输入 | 功能 |
|---|---|
| SW1 SW2 = 00 / 01 / 10 / 11 | 原图 / 边缘 / 灰度 / 二值图 |
| SW3 = 0 / 1 | 红 A、蓝 B / 黄 A、紫 B |
| SW4 = 1 / 0 | 增加 / 减少增益或倍率 |
| KEY1 | 复位 |
| KEY2 | 按 SW4 调节相机增益；校准中取消 |
| KEY3 短按松手 | 启停检测；支持校准的版本中确认取样 |
| KEY3 长按约 1 秒 | 显隐视频标注，底栏保留 |
| KEY4 | 按 SW4 切换 1、2、4 倍，到端点保持 |

## 目录

| 目录 | 内容 |
|---|---|
| `td_project/` | TD 工程、引脚和时序约束 |
| `rtl/` | 顶层控制、检测、跟踪、图像处理与显示逻辑 |
| `user_source/`、`ip/` | 相机、DDR、显示等厂家源码与 IP |
| `docs/` | 使用方法和版本说明 |
| `scripts/`、`sim/` | 生成、构建、审计与仿真代码，部分脚本依赖原开发环境 |
| `build/`、`reports/` | 已归档产物与验证证据，文件按对应版本使用 |

## 使用边界

数字放大不增加原始采集细节。软件与构建记录只对应其绑定版本，实物画质、识别效果和连续运行结果需按本分支说明核实。

来源见 [源码与素材说明](docs/来源与修改记录.md)。厂家 IP、字体和参考工程保留原有声明。本仓库暂未添加统一开源许可证。
