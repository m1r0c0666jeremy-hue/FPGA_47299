# LockingnTracking：Git 回到单色候选存档，仅保留帧头丢字修复

2026-10-11，按 Jeremy 确认的计划完成。当前路径仍为 `D:/aaa_FPGA/criticalwork`。

## 当前 Git 与源码

- 分支 `LockingnTracking`，HEAD **f395cc011ef4c21f15863192ce148938834bd639**，即“存档单色候选框与中文诊断联调版本”。
- 2827个原有受Git管理的文件逐字节核对，唯一差异为 `user_source/hdl_source/video_in.v`，原样来自 cf8b7c463a415bd8741fed4ec68ff3eeac252455。
- 修复SHA256：`6c02b617ef32c478ab39bf17e0fe5e48a3f6e38eca1796bf628cb19052c7838b`。帧头数据先暂存，等待DDR换帧、FIFO复位、新地址发布后再放行；端口兼容，未放宽完整帧检查。
- 判色、面积、填充、除法、OSD、按键、跟踪、模式和倍率全部采用f395。红蓝80/32/3:2；黄紫80/24/5:4/平衡2倍；面积64～20000、填充至少30%、间距16～600。
- 修复未提交、未推送。其他分支、标签、远端地址及缓存引用保持。origin/LockingnTracking仍cf8，本地落后一条；后续不要直接拉取覆盖旧存档基线。

## 打开与下载

TD打开 [target_lock_candidates_ingress.al](../td_project/target_lock_candidates_ingress.al)，BitWriter下载 [target_lock_candidates_ingress.bit](../build/target_lock_candidates_ingress/target_lock_candidates_ingress.bit)。旧候选bit尚未包含修复，不用于验证本组合。

bit SHA256：`92fba519873b691074582b614f03eb081b45b07735934e846767956599803b7d`。78项构建输入与原清单完全一致，复用原同源bit，本轮未重新进行TD构建。实验.al恢复自bit配套源码快照；TD保存的格式/编译顺序版本另行归档。

原构建数据：Slice19105/21216、LUT6 17250、寄存器18733、ERAM56/108、DSP31/40；SWNS+0.117ns/HWNS+0.020ns、覆盖97.50%。这是匹配源码的历史构建结果。18条Gray最大延迟被时钟例外忽略的限制仍在。

## 本轮重新验证

- 采集：960打包字=960次DDR写入，逐字数据与地址匹配。简化/厂家FIFO分别在三组异步时钟下验证172800字完整720p帧、停顿、短帧、溢出、复位和换帧恢复。
- 视频：15组、19帧、15175680像素，覆盖四模式、三倍率、边界窗口、读写竞争、异常帧及恢复。
- 审计：旧存档文件、唯一修复、78项输入、生成资产、分支/标签/远端引用、bit及完整归档全部核对。厂家FIFO端口宽度仿真告警沿用原IP，未修改厂家代码。

回归入口：`scripts/test_git_return.py --stage ingress`、`--stage video`；新日志`reports/git_return_*`，历史日志保持。只读审计`scripts/audit_git_return.py`，加`--archive`核对全部归档文件。

## 备份与状态边界

完整原工程：`D:/aaa_FPGA/archives/criticalwork_before_git_return_20261011_203250`，含.git、未提交文件、P0、宽阈值工程、10份旧bit及忽略的缓存。6309文件共1551589804字节，全部哈希与归档前一致。

TD关闭时保存的工程文件另存 `D:/aaa_FPGA/archives/criticalwork_before_git_return_20261011_203250_td_saved/td_project/target_lock_candidates_ingress.al`，未覆盖原版本。目录被占用时采用逐文件移动，空目录保留，没有删除文件。完整清单：`D:/aaa_FPGA/archives/git_return_record_20261011_203250.json`。

以 [git_return_restore_manifest.json](../reports/git_return_restore_manifest.json) 的当前Git状态为准。README和candidate_ingress历史报告中的“HEAD仍cf8”等正文保持，仅代表此前交付状态。P0/robust不在当前活动工程；生成器采用f395，不支持`--color-diag`。

本组合仍需上板检查闪屏、黑块、视频就绪、模式、倍率及按键。960→720是已复现的丢字路径，不能证明它是所有实物闪屏的唯一原因；软件通过不能证明颜色识别或硬件验收通过。本轮未下载板卡、未烧Flash。
