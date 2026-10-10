# 单色候选诊断联调构建

工程：`td_project/target_lock_candidates.al`；构建：`scripts/build_target_lock_candidates.tcl`。

当前目录专用于单色候选框、双色锁定和中文诊断版本，不覆盖旧dualcolor／target_lock产物。最终bit哈希、资源及时序见 `reports/LockingnTracking单色候选验证报告.md` 和 `reports/candidate_build_manifest.json`。

旧采集帧头丢数据问题未修复；构建通过不表示完整采集或实物验收通过。本助手没有下载板卡或烧写Flash。勿将用户此前烧入Flash的旧版本当成本次版本。
