# 阶段二十一：大赛资料、官方手册与GitHub对照

2026-10-18恢复后执行；当前正式源码最后功能提交547498a，140项当前源码审计通过。完整尝试为build/refined_full_20261018_163624，尚未通过最终布线及时序，不存在本阶段可交付bit。

## 大赛原厂资料

来源：D:/BaiduNetdiskDownload/HX1P35A_Contest_202606/7_lab_ex_2026_nosoft。

代码更新说明明确说明Lab1、2、3统一为原厂1280×720@60fps，Lab1额外保留1080p30表；并未声称解决高占用设计拥塞。只读ZIP对照发现Lab1的mc_to_user_interface.v、ph1p35_324_ddr_wrapper.v及timing.sdc与仓库原始保留版逐字节一致。不能以替换成该例程来代替已有独立AR/AW/W修正，也不改变当前分辨率。

ZIP内的历史route.qor为12358 Slice、40 ERAM、8 DSP，Setup WNS1408ps、Hold WNS20ps。它是原厂低占用视频基线的保存报告，不能证明加入本项目检测、校准、缩放与恢复逻辑后仍能收敛，也不是本次重编译或实物证据。

逐文件来源、ZIP及条目SHA256、参考副本见build/refined_reference_review_20261018_1638/lab1_comparison.json。原资料不修改。

## 官方手册与工具实际值

来源：D:/26_software/TangDynasty/doc/SWUG。

- SWUG105 PDF29页/正文23页：PH1布局策略1～11，route effort为normal/routability。不得把错误提示中的“high”当作合法route effort；High保持修复模式仅PH2支持。
- SWUG105 PDF75～77页/正文69～71页：report_hfn报告高扇出，report_analysis报告拥塞；可先定位具体网络及拥塞区域，再决定布局或RTL措施。
- SWUG106 PDF40～41页/正文33～34页：局部max_fanout会通过复制instance降低扇出；可能增加资源，不能假定全局降低扇出必然改善。暂不修改正式RTL或运行中的设置。
- SWUG201 PDF77及80页/正文73及76页：负Setup/Hold Slack分别表示对应时序不满足；不以临时布局正值或单一Setup通过替代最终检查。

SWUG105旧手册列fix_hold默认为off；本机TD V6.2.168116的实际report_param -detail -stage route显示fix_hold为on、默认也为on，hold_fix_iteration为5。原厂脚本的drHoldFix也为on。因此当前不能把“漏开保持修复”作为根因，需以实际工具报告为准。完整构建最终仍须两项非负。

手册SHA、完整页文本及已视觉核对的PDF29页表格保存在build/refined_reference_review_20261018_1638；不调整原ADC/SDC。

## 只读拥塞定位

对已完成的私有同实现布局131844导入分析，源DB前后SHA256不变，记录build/refined_congestion_probe_20261018_164003。仅报告，不执行route、修改或导出数据库。

report_hfn显示capture_reset扇出3278、ddr_reset1353及其他跨区域复位网络；拥塞区域报告中存在父模块u_video、缩放、检测、OSD和DDR相关贡献。高扇出不等同关键时序失败，报告中的父模块归属也不能直接当作某一个子模块的根因。私有预布局数据仅用于定位，不能替代正式尝试最终报告。

本轮先完成已证实节省289 Slice的正式候选存储优化构建，不在构建中途更换源文件或追加参数。若仍失败，再依据正式DB的拥塞与高扇出报告选择一项针对性改动，而非同时更改多种算法。

## GitHub对照与边界

检查了以下同器件项目的作者资料：

- https://github.com/Aurora-520/anlogic-ph1p35-vision/blob/main/docs/build.md
- https://github.com/OrdoAbChao7/anlogic-ph1p35-image-processing

前者给出完整工程、实际Place & Route结果和历史best_result的区分方法；后者公开了官方视频基线及若干未通过时序的阶段记录。没有找到适用于本项目当前高占用布局的、带复现证据的PHY-8080直接修复。未复制他人的时钟约束、成功率声明或未验证参数。它们是各自项目的原始资料，不能作为本项目硬件通过依据。

本轮继续采用本机TD自带official_strategy_ph1.json的AreaOptimizeHigh和CongestionHigh，以完整冻结输入、正式入口、最终资源和时序为交付依据。所有软件、构建和实物结果仍分别报告。
