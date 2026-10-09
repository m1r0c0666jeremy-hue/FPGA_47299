# LockingnTracking 双配色与中文标注验证报告

日期：2026-10-09。开发基线061cfd7，远端实施前核对为21609e5。修改保持在LockingnTracking，main及ImproveFourfoldScale保持原提交。

## 功能与边界

新增中文标记名称／估算尖端说明、SW3红蓝／黄紫选择、KEY3短按松手启停和长按1秒显隐，KEY2改为由SW4决定增益方向。长按只隐藏视频标注，保留底栏并继续检测跟随。操作详情见 `docs/LockingnTracking双配色与中文标注.md`。

颜色配置在采集帧起点锁定，256位结果携带原始配色、启用和会话。跟踪／显示拒绝迟到的旧配置结果。显隐与底栏配色在显示帧边界提交，标签在视频区内按T/A/B避让，必要时使用左上固定说明区。

本轮没有添加滤波／锐化／双线性或修复旧采集链路。此前帧头丢数据复现继续保留，原日志 `reports/target_ingress_probe.log` 未修改；没有放宽帧完整性检查。新版本即使软件及TD通过，也仍是联调版本，不能宣称完整采集接入或实物验收通过。

## 验证项目

| 项目 | 覆盖内容与证据 |
|---|---|
| 控制 | 999/1000/1001ms、长按不重复、松手不误触发、隐藏时启停、多键冲突、复位等待释放、配色会话、SW4增益锁定及缩放；dualcolor_unit_simulation.log |
| 原红蓝检测／跟踪 | 22个128×64场景、2个1280×720帧；4组L/D各450次独立定点参考；同一unit日志 |
| 黄紫及配置管线 | 69个采集帧，包括阈值上下界、缺色、白黑灰绿／红蓝干扰、随机噪点、填充率及短长帧、SOF与首像素同拍／分拍；真实异步10位指令邮箱连接检测和跟踪，11个旧配置结果拒绝、10次有效输出；dualcolor_detection_simulation.log |
| 黄紫完整帧 | 5个1280×720帧，面积64／63、20000／20200边界及远处同色像素拉低填充率；dualcolor_full_simulation.log |
| 显示／缓存／跨时钟 | 原帧号与缓存检查、迟到快照、旧会话、额外错误配色拒绝；无快照时显隐仍在VS提交；异步256位邮箱100次整包一致；unit日志 |
| 完整视频 | 最终源码15组／19帧，四模式×三倍率、边界、动态窗口、延迟／欠载／恢复，逐像素对照；dualcolor_video_simulation.log |
| 中文OSD | 最终源码52幅720p、47,923,200像素，包含两配色×四模式×三倍率、各状态、隐藏、四角、拥挤回退及Logo；dualcolor_osd_simulation.log及dualcolor_preview |
| 原算法回归 | 未修改的开关、17×9及1280×720图像处理三组通过，完整测试3,688,960像素；dualcolor_preprocess_regression.log |

检测统计和像素绘制分别由独立Python整数／栅格参考核对。OSD字模本身是生成资产，几何、颜色、文字布局由参考程序重建；这些预览是仿真，不是实拍。DDR视频验证沿用行为模型，不证明真实DDR、相机接口或物理板卡通过。

上述项目最终日志全部通过，完整视频共核对15,175,680个有效像素。`scripts/audit_dualcolor.py --record-build` 已核对构建输入、生成资产、厂家来源、旧bit及六份测试日志，并生成同源清单。

## 最终构建与审计结果

2026-10-09完成TD 6.2.168116综合、布局布线及bit生成，器件PH1P35MDG324，速度等级−3。最终判色实现采用移位加法，黄紫69帧与5个完整帧均重新通过；以下数据属于这次最终构建，不是此前中间结果。

| 项目 | 最终结果 |
|---|---:|
| LUT6 | 16636 / 21216（78.41%） |
| 寄存器 | 17670 |
| Slice | 18717 / 21216（88.22%） |
| ERAM20K | 52 / 108 |
| DSP | 30 / 40 |
| 建立时间最差余量SWNS | +0.142ns |
| 保持时间最差余量HWNS | +0.020ns |
| STA约束覆盖率 | 97.42% |

时序报告无已分析路径的建立／保持违例，但逻辑占用较高、时序余量有限；不是全路径或实物稳定性证明。约束与此前target_lock／scaling_test一致，例外报告仍有18条Gray地址跨域最大延迟路径被set_clock_groups忽略，未在本轮扩大修改范围。

最终bit：`build/target_lock_dualcolor/target_lock_dualcolor.bit`，SHA256：

```text
40ca82c86b289eb3392623bfaa0e5270bc067c2130b78ae5e4c0b70f301d01e5
```

构建输入及验后清单分别为 `reports/dualcolor_build_inputs.json`、`reports/dualcolor_build_manifest.json`；完整构建日志为 `reports/dualcolor_build.log`，资源、时序和例外报告在新build目录。原target_lock、scaling_test和imagepreprocess_10_3的bit哈希均未改变。

交付状态为 **SOFTWARE_AND_BUILD_PASS_INTEGRATION_PENDING（软件与构建通过，集成待验）**。新bit与当前源码同源；旧采集帧头丢数据问题仍在，不能将这次结果写成完整相机采集通过或离焦问题已修复。开发基线为061cfd7；2026-10-09按Jeremy后续明确要求，以“LockingnTracking：存档中文标注、双配色与KEY3长短按联调版本”为名保存本次源码、bit、文档及验证证据，上传目标仅为GitHub的LockingnTracking，不合并main。

## 来源、复现及实物待验

先复用大赛Lab1采集／ISP／DDR接口和Lab3字模／OSD来源，vendor_reference和登记的厂家工作副本无新增修改；中文缺字仍由本机黑体生成。Red_Tracker仅作判色／准心思路参考，未复制其平台RTL。新增黄紫判据为整数比较，常数比例使用明确的移位加法，控制DSP资源占用。

使用独立target_lock_dualcolor工程，保持旧bit及旧报告；构建前保存输入哈希，构建后将实际输入、bit与测试日志绑定。原target审计保留其完整采集验收门槛，不将其改为“已通过”。新审计状态为SOFTWARE_AND_BUILD_PASS_INTEGRATION_PENDING。

队友仍需测试两套实际色环、红蓝板背景／黄紫物体干扰、清晰与离焦对照、倾斜尖端误差、失锁和重锁、全部按键以及标签可读性。黄紫阈值只是初值，换色不能保证避免所有背景误识别。未下载、未烧Flash；Git存档上传依据Jeremy后续明确请求，不表示实物验收完成。
