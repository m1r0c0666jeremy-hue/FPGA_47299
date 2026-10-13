# Git存档与远程仓库

首次建档日期：2026-10-03。仓库根目录为各自电脑的工程目录：Jeremy 当前使用 `D:\aaa_FPGA\criticalwork`；队友记录的路径为 `E:\FPGA\FPGA26\ImagePreprocess\FPGA_47299-ImagePreprocess`。两者属于不同电脑的工作副本，不能把 Jeremy 的目录标为已废弃。Git是保留文件版本和改动历史的工具；一次commit（提交）就是一个可追溯快照。

本次存档包含源码、TD工程/约束、厂家原始基线、脚本/测试、文档、bit及命名的编译报告/日志，以及当前便携仿真器和原始下载包。厂家原文件按字节保存，`.gitattributes` 禁用自动换行转换，避免来源哈希被Git改变。

`.gitignore` 排除TD正在使用的锁文件、GUI临时日志、仿真生成文件、重复的final_timing报告和实例中间文件；这些文件仍留在本地，没有删除。许可证、私钥和环境凭据文件也被排除。因忽略文件不在提交中，Git不是当前文件夹每一个临时文件的完整磁盘镜像。

首次存档使用已有Git作者设置，只在本地提交。首次快照用标签 `archive-2026-10-03-camera-hdmi` 标识；它仍是“引脚未核对、不可上板”的版本，标签不表示硬件发布。

2026-10-03后续更新：Jeremy明确授权将本工程提交到 [FPGA_47299](https://github.com/m1r0c0666jeremy-hue/FPGA_47299)。远程名称为 `origin`，地址为 `https://github.com/m1r0c0666jeremy-hue/FPGA_47299.git`，使用 `main` 分支，并保留上述首次存档标签。首次推送前检查远程没有分支或标签；不强制覆盖远程历史。忽略的临时文件和凭据不上传。

## 常用操作

在PowerShell执行：

```powershell
Set-Location 'D:\aaa_FPGA\criticalwork' # 换成当前电脑的仓库路径
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

本地Git不能防硬盘损坏。复制仓库备份时应包含隐藏的 `.git` 目录。后续本地提交不会自动同步远程，需将当前分支推送，当前主干使用 `git push origin main`（其他分支按实际分支名推送）；推送前检查文件范围。厂家/IP代码的原有权利声明继续有效，没有为整包新增开源许可证。

## 图像处理分支（10_3）

新分支名为 **ImagePreprocess**，从3844377创建，保留main历史。提交名称为“10_3 新增拨动开关四模式图像处理并整合顶层”。范围含两个新模块、顶层连接、工程约束、仿真/编译证据及文档清理。该段为最初分支开发记录；四模式功能现已由队友以v1.2纳入远端main，并完成实物验收，见下节。

## 2026-10-04 主干同步存档

本次存档名称：**同步main：存档队友已验收的四模式图像处理v1.2**。

本地未提交改动检查为空，从ImagePreprocess切换到main，将main从3844377快进至远端ca44ead；没有重写历史，ImagePreprocess保留在1efd552。接收队友v1.2（8ce88b5）及后续说明修正0d28235、ca44ead。

Jeremy反馈队友已验证图像处理；接收的报告记录原图/边缘/灰度/二值化均通过实物验收。实际SW1/SW2极性为上0下1：上上原图、上下边缘、下上灰度、下下二值化。30分钟测试在远端记录为未执行，不标为通过；旧缓存/复位边界问题仍保留。

同步后检查：58个TD工程文件依赖存在；RTL、user_source、工程约束及图像处理bit与ImagePreprocess完全一致。bit SHA256为eddd9d7d28eb431de92d1d0f061962645b7734b027469290ae06166c9183ddf9。此次只同步和补充存档记录，未重新编译、仿真或下载；硬件结论引用用户反馈与队友报告。

本次新提交仅更新README主干身份和本存档说明，保留队友源码、bit及测试记录原样。提交号用git log -1 --oneline查询。

## 2026-10-04 更新：提交身份与分支流程

本节为队友电脑当时的配置记录，不代表所有协作者的身份或当前分支合并状态；不要据此覆盖另一台电脑的 Git 配置。

**仓库位置**：本地仓库根目录＝本工程目录本身，`origin` = `https://github.com/m1r0c0666jeremy-hue/FPGA_47299.git`，
本地 `main` 跟踪 `origin/main`。仓库为**私有**仓库，仅协作者可访问。

**提交身份（已关联 GitHub 账号）**：本机全局与仓库内均设置为
`Jeremy <161012452+Fle068@users.noreply.github.com>`，对应 GitHub 账号 **Fle068**；
用 noreply 地址可保证提交稳定归属该账号，且不暴露私人邮箱。推送认证使用 Git Credential Manager（已登录 Fle068）。

- 历史提交（`45253e0`…`ca44ead`，含队友的 `3eee5cf`/`1efd552`/`3844377`/`e671630`）署名均为 `m1r0c0666jeremy@gmail.com`；
  若该邮箱也是你的，可在 GitHub → Settings → Emails 添加并验证，历史提交会自动归到你名下。
- 自 2026-10-04 起采用的流程：**特性分支 → 推分支 → 经确认后再合并 main**。

```powershell
git checkout -b feature/xxx      # 1) 本地建分支，不动 main
git add -A; git commit -m "..."  # 2) 提交到分支
git push -u origin feature/xxx   # 3) 只推分支
git checkout main; git merge --no-ff feature/xxx; git push origin main   # 4) 确认后并入主干
```

现存分支：`ImagePreprocess`（队友开发线，未合并）、`ScalingTest`（队友：手动缩放/按键复用/中文OSD，未合并）、
`docs/git-workflow-and-identity`（本次文档分支）。
标签：`v1.1`、`v1.2`、`archive-2026-10-03-camera-hdmi`、`archive-2026-10-04-pins-brightness`、`archive-2026-10-04-imagepreprocess`、`review-2026-10-03-teammate-v1.1`。

## 2026-10-05 主干同步与功能验收存档

存档名称：**同步main：存档队友已验收的十字准心、缩放与OSD功能**。

按 Jeremy 要求，在本地工作区干净的情况下，从 ScalingTest 切换至 main，再将本地 main 从 `e671630` 快进到远端 `8136663`（接收 11 个提交）。远端已合入 ScalingTest 及验收文档；保留本地 ScalingTest（`8ae151f`）、ImagePreprocess（`1efd552`）和旧 bit，没有重写历史。提交作者沿用 Jeremy 本机既有配置，没有按队友电脑的配置修改身份。

Jeremy 确认队友十字准心、放大与 OSD 已成功上板。接收报告记录第 0～5 步通过，SW3/SW4 上=0、下=1，设备为 HX1P35A V1.0 / MLK-CAM001 V1.0（SC500CS）/ KTC H25T7；第 6 步连续稳定性观察跳过，未烧 Flash。按报告末尾的新验收结果理解早期“未执行”描述。

本次运行 `scripts/audit_scaling.py` 通过，核对 193 份 Lab1 来源文件、4 份 Lab3 来源文件、65 个工程依赖、字模/Logo、构建输入与 bit 哈希及存档日志。当前 bit 为 `build/scaling_test/scaling_test.bit`，SHA256 为 `a598cff3ea804c0fbc9e54d1693e03cfc32fa4b9aef2d7133f234879dc6edf8c`。与本地 ScalingTest 相比，RTL、厂家代码、工程约束、脚本、仿真源码和 bit 未变化；本轮未重新仿真、编译、下载。

新提交仅更新 README 和本存档说明，修正当前入口及两台电脑的路径/身份范围。Jeremy 反馈 4 倍像素感明显，当前采用最近邻复制；双线性插值等优化仅为建议，未修改已验收实现。提交号以 `git log -1 --oneline` 为准。

## 2026-10-07 LockingnTracking 开发状态存档与队友交接

存档名称：**LockingnTracking：存档双色锁定跟踪与OSD开发版本，待队友联调**。

从本地main `4c2620782e7f29367620975b51e850a34f846ef1` 创建LockingnTracking，沿用最近邻缩放；main和ImproveFourfoldScale分支保留。按Jeremy明确要求，将当前开发状态提交并推送到 `origin/LockingnTracking`，不合并或推送main，不继续处理本次发现的采集接入问题，具体测试和问题处理交由队友。

归档范围包括双色检测／估算尖端／持续跟踪／OSD源码、独立工程和脚本、已有仿真与静态审计、OSD预览、帧头FIFO复位丢数据的复现证据，以及首轮中间bit和TD报告。中间bit不是最新源码的同源最终产物，不能直接作为可上板交付；尚未做最终完整集成验收、上板、下载或烧Flash。队友先读 `reports/LockingnTracking验证报告.md`，不要把推送成功理解为问题修复完成。

精确提交号与上传状态以Git记录为准；本地仓库外的 `D:/aaa_FPGA/AGENTS.md` 不属于本次GitHub上传内容。

## 2026-10-08 同步队友实物测试记录

存档名称：**LockingnTracking：同步队友实物测试记录并存档离焦锁定问题**。

本地工作区干净，将LockingnTracking从 `067664c` 快进到远端 `21609e587b3d68540f85ec1856ae5b2d7d8966f6`，接收队友实物观察文档；远端这次没有修改RTL、参数或bit。随后添加本地接续说明，记录Jeremy反馈的“离焦可锁定、清晰时失败”，并依据代码澄清检测不限定圆形标记。详见 `docs/LockingnTracking接续_2026-10-08.md`。

本轮只进行同步和文档存档，没有修复或重新构建；未修改main和ImproveFourfoldScale，未下载、未烧Flash。新接续提交仅保存在本地，未推送。中间bit同源性、采集帧完整性及清晰画面检测问题继续保留为待处理事项。
