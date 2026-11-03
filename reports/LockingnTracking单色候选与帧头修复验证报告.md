# 单色候选与帧头修复验证报告

日期：2026-10-11。结论：已完成 f395 单色候选/中文诊断源码恢复，只移植 cf8 的 video_in 帧头修复；模块、完整帧采集、视频与 OSD 回归，以及 TD 综合布局布线通过。新组合尚未上板，不宣称清晰对焦颜色识别已修复。

## 源码与历史

- 功能基线：`f395cc011ef4c21f15863192ce148938834bd639`。
- 闪屏修复来源：`cf8b7c463a415bd8741fed4ec68ff3eeac252455`；`video_in.v` SHA256：`6c02b617ef32c478ab39bf17e0fe5e48a3f6e38eca1796bf628cb19052c7838b`。
- Git 分支仍 LockingnTracking，HEAD 保留 cf8，本次以工作文件恢复旧版；未 reset、未重写历史、未提交/推送。
- 旧候选构建输入逐项字节比较：仅 video_in 使用 cf8，其他全部与 f395 相同；新工程源列表与 f395 相同，无 P0 诊断副本。生成配置、模板、生成器与生成结果哈希一致。
- 78 项新构建输入自构建前冻结到验后保持一致；10 份原 bit 哈希不变。完整输入、结果哈希和证据见 `candidate_ingress_build_manifest.json`。
- P0 及软件原型的3026个 Git 可见文件和当时根 AGENTS 已压缩备份、CRC/逐文件字节验证；备份路径 `D:\aaa_FPGA\archives\LockingnTracking_before_candidates_ingress_20261011_163732.zip`，SHA256 `f31255130074e54566fd631bdfac287836de6074ff436966e75a1fcf087a9c68`。保留的 P0/robust 历史文件不参与新工程；当前旧生成器不支持 --color-diag。

## 验证结果

| 类别 | 通过内容 | 新日志 |
|---|---|---|
| 采集入口 | 实际 AWB/打包路径960字全部写入，逐字数据和地址一致；简化FIFO与厂家FIFO各三组异步时钟；172800字完整720p、停顿、短帧、溢出及复位恢复 | candidate_ingress_ingress.log |
| 单元 | 202个十进制诊断、按键边界、跨域/帧绑定、22小帧＋2完整红蓝帧、4组共1800个尖端参考 | candidate_ingress_unit_simulation.log |
| 检测集成 | 71帧，异步控制、换色/启停、11次过期结果拒绝 | candidate_ingress_detection_simulation.log |
| 完整黄紫 | 5个720p帧，64/63、20000边界和远端干扰的原填充率拒绝行为 | candidate_ingress_full_simulation.log |
| 视频 | 15组19帧，15175680视频像素；四模式、三倍率、窗口/缓存提交、读取竞争与坏帧恢复 | candidate_ingress_video_simulation.log |
| OSD | 72幅完整图，66355200像素，对应旧标签、数字、独立候选和失败原因的逐像素参考 | candidate_ingress_osd_simulation.log |
| 原图像处理 | 开关与17×9、1280×720四模式独立参考回归 | candidate_ingress_preprocess_regression.log |

全部测试复用旧黄金参考，不通过修改预期放宽门槛；所有新输出独立，原成功记录未覆盖。厂家 FIFO RTL 仿真只验证逻辑，不代替物理时序/CDC 或实物验收。

## 实际 TD 构建

TD6.2.168116，PH1P35MDG324 −3；实际入口 `td_project/target_lock_candidates_ingress.al` / `scripts/build_target_lock_candidates_ingress.tcl`。

| 指标 | 原 f395 candidate | 新 candidate＋采集修复 |
|---|---:|---:|
| Slice | 18073/21216 | 19105/21216 |
| LUT6 | 16071/21216 | 17250/21216 |
| 寄存器 | 18697 | 18733 |
| ERAM20K | 52/108 | 56/108 |
| DSP | 31/40 | 31/40 |
| SWNS | +0.022 ns | +0.117 ns |
| HWNS | +0.020 ns | +0.020 ns |
| 时序覆盖 | 97.58% | 97.50% |

采集仍四像素每拍；256×128位暂存只处理帧头握手，不增加整帧缓存。所有原厂 IP/约束保留；18条 Gray 地址最大延迟仍因时钟分组被忽略，覆盖率不表示全部跨域物理证明，具体见本轮 exception.timing。

最终 bit：`build/target_lock_candidates_ingress/target_lock_candidates_ingress.bit`；SHA256：`92fba519873b691074582b614f03eb081b45b07735934e846767956599803b7d`。

首次 TD 调用使用 Windows 反斜杠，Tcl 对路径转义，尚未开始编译；启动失败记录保留 `candidate_ingress_build_launcher_failed.log`。改用正斜杠后本轮综合、布局布线及 bitgen 完成，成功构建日志为 `candidate_ingress_build.log`。

## 实物边界及下一步

使用者 已反馈 cf8 原版闪屏解决；本轮是恢复旧颜色/面积/填充后的新组合，还没有下载或烧 Flash。先用最终新 bit SRAM 下载验证持续视频、四模式/三倍率、KEY3 启停/长按、两配色单色候选/诊断及三帧锁定。原 f395 的清晰失效/离焦成功与同色干扰问题不因迁移写入器自动消失。所有板上观察须记录下载文件哈希；严禁将软件/TD通过写成新组合硬件已验收。
