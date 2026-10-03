# Git本地存档

首次建档日期：2026-10-03。仓库根目录：`D:\aaa_FPGA\criticalwork`。Git是保留文件版本和改动历史的工具；一次commit（提交）就是一个可追溯快照。

本次存档包含源码、TD工程/约束、厂家原始基线、脚本/测试、文档、bit及命名的编译报告/日志，以及当前便携仿真器和原始下载包。厂家原文件按字节保存，`.gitattributes` 禁用自动换行转换，避免来源哈希被Git改变。

`.gitignore` 排除TD正在使用的锁文件、GUI临时日志、仿真生成文件、重复的final_timing报告和实例中间文件；这些文件仍留在本地，没有删除。许可证、私钥和环境凭据文件也被排除。因忽略文件不在提交中，Git不是当前文件夹每一个临时文件的完整磁盘镜像。

本次使用已有Git作者设置，只在本地提交，不配置或推送远程。首次快照用标签 `archive-2026-10-03-camera-hdmi` 标识；它仍是“引脚未核对、不可上板”的版本，标签不表示硬件发布。

## 常用操作

在PowerShell执行：

```powershell
Set-Location 'D:\aaa_FPGA\criticalwork'
git status
git log --oneline -5
git show --stat archive-2026-10-03-camera-hdmi
```

`status`查看哪些文件变了，`log`查看历史，`show`查看某次快照。做完一轮改动后，先检查差异，再提交明确文件：

```powershell
git diff
git add -- rtl/00_top_control/criticalwork_top.v
git commit -m "说明本次改了什么"
```

示例路径仅示范用法，实际应列出本轮需要存档的所有文件。不要未经核对就用覆盖、强制回退或清理命令处理工作目录。已提交源码后若重新编译覆盖报告和bit，需要再次审核并提交结果，避免代码与编译证据不对应。

本地Git不能防硬盘损坏。备份仓库时应包含隐藏的 `.git` 目录；公开上传前需另行核对厂家/IP代码再分发许可和日志中的本机路径。本次未向GitHub上传任何内容。
