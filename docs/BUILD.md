# 编译与下载

## 环境与工程入口

使用安路 Tang Dynasty（TD）6.2.168116，目标器件为 PH1P35MDG324，速度等级 -3，开发板为 HX1P35A。摄像头使用配套 SC500CS 模组。

完整获取 `docs/contributor-note` 分支后，在 TD 中打开 [criticalwork.al](../td_project/criticalwork.al)，顶层为 `criticalwork_top`。保留整个仓库目录结构，工程通过相对路径引用 RTL、厂家 IP 和约束。

`.al` 是工程文件；`.bit` 是给板卡下载的配置文件，两者用途不同。工程中的部分 Path 字段保留原开发目录，迁移后先检查依赖是否解析到当前仓库。

## 使用现成 bit

本分支文件：[imagepreprocess_10_3.bit](../build/imagepreprocess_10_3/imagepreprocess_10_3.bit)。

仓库相对路径：`build/imagepreprocess_10_3/imagepreprocess_10_3.bit`。

SHA256：`eddd9d7d28eb431de92d1d0f061962645b7734b027469290ae06166c9183ddf9`。

SHA256 是文件校验值，用于确认下载的文件与这里相同。PowerShell 可在仓库根目录检查：

```powershell
Get-FileHash -Algorithm SHA256 'build/imagepreprocess_10_3/imagepreprocess_10_3.bit'
```

在 BitWriter 中连接下载器、扫描器件并添加上述 bit，先选择 SRAM 在线下载。核对下载日志的实际文件路径，避免使用其他分支的同名文件。SRAM 配置断电后失效，写入 Flash 后才会在重新上电时自动加载。Flash 的型号和连接方式按实际板卡配置。

## 重新编译

在 TD 中检查器件、顶层、源文件列表和 ADC 引脚约束、SDC 时序约束，然后依次完成读入设计、综合、布局布线、时序检查和生成 bit。把新输出放到独立目录，保留原有 bit 与报告。

仅生成 bit 文件不表示构建合格。检查工具退出状态、最终 DRC 规则检查、建立与保持时序余量，以及源码与产物的对应关系。更改源文件、IP、工程或约束后，旧 bit 和旧测试结果不能替代新构建结果。

`scripts/` 中包含各历史版本的生成、测试和构建脚本，其中部分绑定原开发分支、路径、冻结输入和旧交付文件。它们不是迁移后的一键安装入口；出现分支或哈希保护失败时，先核对对应版本和依赖。

## 首次上板

先检查原图与显示分辨率，再检查图像模式、相机增益和按键。支持校准的版本应使用实际安装的材料重新校准。按 [使用手册](USER_GUIDE.md) 测试本分支功能，记录冷启动、遮挡恢复和连续运行结果。软件仿真、时序通过与板上实测分别记录。
