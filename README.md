# 手动选点放大与中文 OSD

在摄像头画面上移动十字准心，按选点进行 1、2、4 倍放大。底部 OSD 信息栏显示坐标、倍率和操作状态。

当前分支：`ScalingTest`。这是独立功能或历史实验分支。完整的区域与路线操作见 [main](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/main)。

## 快速开始

1. 准备 HX1P35A 开发板、SC500CS 摄像头、HDMI 显示器和下载器。
2. 在 TD 6.2.168116 中打开 [td_project/scaling_test.al](td_project/scaling_test.al)，或直接下载下表的 bit。
3. 先通过 BitWriter 下载到 SRAM，复位后确认原图，再按使用手册校准和操作。

| 文件 | 路径 |
|---|---|
| TD 工程 | [td_project/scaling_test.al](td_project/scaling_test.al) |
| 下载文件 | [build/scaling_test/scaling_test.bit](build/scaling_test/scaling_test.bit) |
| 操作手册 | [连接、校准、开关与按键](docs/USER_GUIDE.md) |
| 编译与校验 | [工程入口、下载步骤与 SHA256](docs/BUILD.md) |
| 版本选择 | [分支说明](docs/BRANCHES.md) |

## 操作速查

| 输入 | 功能 |
|---|---|
| SW1 SW2 = 00 / 01 / 10 / 11 | 原图 / Sobel 边缘 / 灰度 / 二值化 |
| KEY1 | 复位，恢复 1 倍与默认选点 |
| KEY2，SW3 = 1 / 0 | 增大 / 减小相机增益 |
| KEY3，SW3 SW4 = 00 / 01 / 10 / 11 | 向下 / 向右 / 向左 / 向上移动选点 |
| KEY4，SW4 = 1 / 0 | 放大 / 缩小，档位为 1、2、4 倍 |

KEY3 按住可连续移动，超过 1 秒后加速。操作开始时锁定开关方向，松开后重按才采用新的方向。多个功能键同时按下时暂停调节。

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

已有首次上板记录，准心、缩放、增益和 OSD 功能通过；连续运行观察未执行。数字放大不增加原始采集细节。

来源见 [源码与素材说明](docs/来源与修改记录.md)。厂家 IP、字体和参考工程保留原有声明。本仓库暂未添加统一开源许可证。
