# 摄像头图像处理与 HDMI 显示

通过 SC500CS 摄像头采集图像，在 FPGA 中完成原图、Sobel 边缘、灰度和二值化处理，经 HDMI 输出。

当前分支：`docs/contributor-note`。这是历史文档分支。首次使用完整作品请切换到 [main](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/main)。

## 快速开始

1. 准备 HX1P35A 开发板、SC500CS 摄像头、HDMI 显示器和下载器。
2. 在 TD 6.2.168116 中打开 [td_project/criticalwork.al](td_project/criticalwork.al)，或直接下载下表的 bit。
3. 先通过 BitWriter 下载到 SRAM，复位后确认原图，再按使用手册校准和操作。

| 文件 | 路径 |
|---|---|
| TD 工程 | [td_project/criticalwork.al](td_project/criticalwork.al) |
| 下载文件 | [build/imagepreprocess_10_3/imagepreprocess_10_3.bit](build/imagepreprocess_10_3/imagepreprocess_10_3.bit) |
| 操作手册 | [连接、校准、开关与按键](docs/USER_GUIDE.md) |
| 编译与校验 | [工程入口、下载步骤与 SHA256](docs/BUILD.md) |
| 版本选择 | [分支说明](docs/BRANCHES.md) |

## 操作速查

| 输入 | 功能 |
|---|---|
| SW1 SW2 = 00 / 01 / 10 / 11 | 原图 / Sobel 边缘 / 灰度 / 二值化 |
| KEY1 | 复位 |
| KEY2 | 减小摄像头增益 |
| KEY3 | 增大摄像头增益 |

这里调节的是相机增益。二值化阈值为灰度 128；边缘模式的前两行、前两列为黑色。

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
