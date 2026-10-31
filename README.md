# 摄像头、图像处理与 HDMI 显示工程

## 2026-10-31 21:44：取消只重算准心，健康视频继续发布

新增真实读图联接用例复现并修正了第一份流水接线的边界问题：手势取消若与待发布碰拍，不能撤销正常视频帧并误触示教缺帧保护。现把真实相机/亮度故障与点操作事件分开；手势/KEY4/模式仅重新准备坐标，来源变化保留同一健康图像，最终坐标/视口/身份仍原子提交。同拍停止不发布旧回放点。8帧实际reader+健康保护的取消/模式/相机/亮度/恢复、600坐标/取消重算、960叠加及64 RTL编译通过；完整164+160回归刷新中，尚无修正后合格bit。b3的19056布局仅属纠正前版本，不能当当前结果。旧构建/取消/失败记录全保留。功能、旧DDR配置和约束保持，实物待Jeremy。以下为历史记录。

## 2026-10-31 20:24：显示端时序定向修复，软件验证中

上一轮152923已自然结束并生成bit，但最终建立−21.006ns／保持−0.097ns，不合格，不能烧录验收。Jeremy批准按真实路径修复：视口在消隐内分拍准备并原子发布、叠加坐标18→20拍、显示分类锁存像素对并同步valid/坐标。仅4/304编译RTL变化，检测核心、DDR旧时钟/IP、相机、约束及全部旧功能保留；medium未采用。正式600组视口+28取消/4覆盖/复位、960组坐标+20重启及64明文RTL联接已过，完整163项及160基础回归正在刷新，尚无新整机物理通过。接续入口build/current_targeted_display_retime_path.txt；本修复不能宣称花屏已解决，最终仍需Jeremy上板验收。以下为历史记录。

## 2026-10-31 15:28：交付优先，旧时钟红黄＋FPS小改版

Jeremy明确暂缓DDR修正，旧版所有功能保留，不删显示页、倍率或示教。当前304编译输入与d574eed/205333布局逐字一致，已直接启动152923布线，无重新综合。保留红黄默认／蓝紫备用、有效FPS、底栏防闪字和紧凑诊断，不新增PDF算法。旧50MHz参考与名义100MHz DDR IP不匹配风险仍存在，不能宣称花屏已解决；100MHz修正和固定银行优化完整备份在build/legacy_clock_ryfps_20261031_152819/before.zip。现布局19147 Slice／98ERAM／40DSP，最终DRC／时序／bit尚待。使用[本轮操作与验收](docs/Final_Mode_红黄蓝紫_FPS与稳定性_操作验收.md)查看按键、FPS和剩余风险；以下记录为各阶段历史，不代表当前配置。

Maintainer: Fle & Jeremy

## 2026-10-30：恢复Final_Mode旧版，红黄双色、FPS与DDR定向修正

正式入口为 `td_project/target_color_regions_stage1.al`，停止原生高清。默认红A黄B、备用蓝A紫B，新增有效新图像FPS、持久故障线索和同帧底栏。新候选仍在验证，尚无本轮最终物理与上板通过。操作、风险及验收见 [说明](docs/Final_Mode_红黄蓝紫_FPS与稳定性_操作验收.md)。接续入口 `build/current_ry_bp_path.txt`。

10月31日12:40，Jeremy批准提前停止长期未收敛的布线重试，采用逐拍等价的固定银行选择电路。原普通布线PHY-8080失败、重试主动取消两种记录分别保留。仅一份编译RTL变化；功能、DDR/IP、时钟、缓存和约束保持。源码a7efb49的163项当前软件及160项基础回归已全部通过，实际布局19312 Slice、98 ERAM、40 DSP。最终布线未完成，不能以软件或布局通过冒充交付通过，也不能据此判定花屏已解决。

发现旧DDR50MHz参考与100MHz配置不一致；Jeremy已批准独立100MHz参考和局部复位释放桥；随后取消构建次数上限。当前同源CongestionHigh整机构建在进行，原TimingUltra布局工具崩溃记录保留。不更改厂家IP或相机／HDMI时钟，不以此认定花屏根因或稳定性已修复。旧候选、native独立归档、所有失败取消记录保持。本轮不推送、上板或Flash。以下为历史记录。


## 2026-10-30 10:18：方案二当前验证全过，唯一新布线101718

11:52更新：普通布线自然完成后报PHY-8080，末轮25内部争用20563，未进入最终DRC；同一66524/session74114依预先配置自动重试routability，没有人工取消或另开TD。源码e0ec及63+155+11保持。交付工具新增从实际执行日志重建最终布线参数，避免将检查点默认normal误作实际重试参数；两份真实失败/重试片段的2正例、5负例解析检查通过，仅为工具测试。实际候选形成后须执行的损坏交付检查由16增至18项，尚未执行完整候选检查。没有新bit或同源包。

编译源e0ec5dc，63/63原生+155/155未变回归+11保护全过，所有仿真结束。100249完整新综合布局通过及严格327当前/冻结/Git、时钟/DB/有效参数核验。实际20538 Slice、20095 LUT6、24740寄存器、107 ERAM、40 DSP；相对f7d为+118 Slice、+170 LUT6、-21寄存器，不能称为整机资源节省。读取器DSP由9降8，整机仍40；同策略布局预测拥挤网格44→19、线长3899557→3840508，最高局部等级3→4，属于混合结果，不能当最终拥塞或时序通过。唯一新正式布线为101718/session74114，最终结果及新bit/同源包仍待完成。方案一和诊断页面删除未实施。

## 2026-10-30 09:42：按方案二优化固定算术，已恢复工作

Jeremy授权仅实施方案二：原生显示读取核心的三处行号除3取余改为精确基4数位折叠，行地址乘1920改为25位移位差；缓冲结构、显示页面、全部功能和约束不变。1024种行号三条路径、32768种方向/银行/首行组合与冻结f7d参考的地址逐拍等价通过，包含非法行号的原有25位回绕语义；11项工程保护及85源接口编译通过。当前要求63项原生验证，显示相关21项待刷新；新整机实际资源尚未知，不能引用旧20420/107/40作为新源结果。09:21原布线按用户要求取消并保留，不是工具完整失败；本次须从新源重新综合布局。最终物理和同源交付尚未完成。


## 2026-10-30：旧版恢复、红黄默认／蓝紫备用与有效FPS（验证中）

正式入口为 `td_project/target_color_regions_stage1.al`，基线为远端Final_Mode_1028的4081ad0，304输入恢复前逐项同源一致。原生高清已终止，源码工具独立归档，原实验及旧构建日志不删除、不参与本工程编译。当前开发保留Git历史，无推送／上板／Flash操作。

红A前黄B后默认，蓝A前紫B后备用，00短按KEY4切组。两组保留四步校准和原K公式与操作。保留720p、624+96、原五档数字倍率、两方向、四矩形及30秒示教。FPS为一秒内首次显示的完整有效新图像数，重复帧、回放虚拟点不计数；HDMI刷新率保持原设置。底栏按同一快照显示，修复实时状态变化时擦除文字的闪字机制。紧凑诊断E高半字节1=相机、2=恢复、3=DDR、4=像素读行；R为恢复次数四位十六进制，L仅表示观察到lane flag，不是CRC或坏帧计数，不触发复位。

当前仅软件验证中，尚无本源最终资源／DRC／时序或新合格bit。最多两轮正式整机构建，10月31日15:00冻结功能、17:00前Jeremy上板验收目标，不能保证额度内收敛。通过前仅候选，严重花屏再次发生即不能宣称稳定。

## 2026-10-29：原生2倍细节与三档倍率整合中

在 `Final_Mode_1028` 新增独立工程 `td_project/target_color_regions_native_zoom.al`，原TD工程保持原样。新模式采用2592×1944原生采集、高清裁剪存储和双路2×2缩小；保留1×、1.5×、2×及原1倍坐标，删除活动3×/4×入口。K与亮度操作沿用实物确认版本。详见[实施与实测表](docs/原生2倍细节与三档倍率_实施与实测.md)。当前尚无最终整机物理及同源交付结论，所有旧候选保持不动；不推送、不烧录。

10月30日09:14接续：仍沿用04:13启动的唯一041323布线进程，现Phase1重新布线，尚无最终DRC/时序及新bit。编译源仍f7d9dcd，327份当前与冻结输入一致，62项原生、155项未变回归及11保护证据保持。独立交付校验补强了对应Bound检查及完成顺序；历史日志解析器2正例/3负例通过，属于工具检查，不能当新程序物理或交付通过。交付损坏用例由14增至16项，仍须实际新候选形成后执行。

10月30日04:14最新状态：编译源f7d9dcd已采用原生检测四路→两路分时共享，数学、坐标、K、显示及其他功能不变，掩码及其身份整体延后一拍。**62/62原生检查、155/155未变回归和11保护负例全部通过**。新完整综合及布局040136通过，实际20420 Slice、19925 LUT6、24761寄存器、107 ERAM、40 DSP；较同策略上一源减少357 Slice。327份当前/冻结/Git、时钟、DB及参数核验通过。唯一正式布线041323正在运行；布局时序预估仍有负余量，不是最终时序结论，尚无新bit或同源包。020830原布线因四轮量化恶化而主动取消，所有记录保留。接续入口仍为 `build/current_native_zoom_path.txt`，下方为历史过程。

当前编译源码7b88445的新综合及布局已通过容量检查：21173/21216 Slice、107/108 ERAM、40/40 DSP。56项原生检查、155项未变模块回归及11项保护负例通过；正式布线仍在运行，最终零冲突、建立和保持余量尚未通过，不能作为上板候选。接续入口为 `build/current_native_zoom_path.txt`。

22:39更新：已采用银行选择预计算与共享像素选择，当前编译源码b1ef178，57项原生检查、155项未变回归及11保护负例全过；旧7b布线因拥塞回升而主动优化取消并保留，新整机223152采用TimingUltra综合布局中，尚无新资源/最终时序或候选bit。上述21173仅为旧7b实际结果。

23:12更新：223152在布局阶段工具崩溃，记录保留；经实际异常dump、327份输入与综合检查点严格核验后，231041从同源gate继续，仅改布局策略2。软件证据保持当前，新物理及烧录候选仍未完成。

23:28更新：231041也发生工具异常。探针确认检查点会恢复旧物理参数，因此改为232608全新CongestionHigh综合及布局，无检查点参数继承；逻辑与约束保持。尚无b1源码有效布局或候选bit，软件57+155及11保护仍当前通过。

23:50更新：232608布局已通过，实际21134 Slice/20824 LUT6/25308寄存器/107 ERAM/40 DSP，327份输入、检查点、真实时钟和参数核验通过。正式布线234758正在运行；Manhattan预估仍有负余量，尚无最终DRC/时序通过和候选bit。

10月30日00:00更新：针对99.61%容量与银行选择长链，已在停止并保存旧布线后采用2720936两项等价优化：缩小滚动像素暂存、固定银行资格判断及更新。新完整综合布局235656正在运行，新源实际资源未知。当前50/57原生、155/155未变回归及11保护通过，只缺实际完整帧写入联接与六组完整视频；旧21134及旧57全过不能作为本源最终结果。未删功能、未放宽约束。

00:06更新：当前2720936的57/57原生检查、155/155未变回归及11保护全部通过，全部软件进程已结束。唯一新布局235656继续，尚无新实际布局、最终DRC/时序或候选bit。

00:14更新：235656实际布局通过20777 Slice/20460 LUT6/24820寄存器/107 ERAM/40 DSP，比上一版少357 Slice。327份当前/冻结/Git、时钟、DB及有效参数核验通过。布局预估建立改善至-1.172ns（仍非最终结果），唯一正式布线001227运行中；最终零DRC及非负建立/保持尚待验证，暂无新候选bit。

00:43更新：补充同一运行中六个完整帧的倍率/方向/边缘视口切换，4792320像素独立预期全部通过，未改硬件。当前58/58原生、155/155未变回归及11保护全过；唯一正式布线001227继续，尚无新候选bit。

02:04更新：原布线四个完整迭代持续恶化、约45分钟无新低，已保留记录并主动结束，转为同源020240布局策略2和宏单元拥塞优化。严格复用已核验综合gate，硬件源码、功能、约束与58+155/11软件证据保持；新实际布局/最终布线尚未完成。02:00一次接续已执行并删除，不重复定时。

02:09更新：同源pr2/macro_congestion实际布局通过20763 Slice/20401 LUT6/24796寄存器/107 ERAM/40 DSP，严格源/检查点/时钟/参数核验通过。唯一新正式布线020830继续，最终DRC/时序与候选bit仍待完成。

## 2026-10-28：共享K、亮度读回与显示共享候选

本轮在Teach_auto_routine_1027完成共享K0.00～2.00／步0.01／默认0.50；00长按KEY2+KEY3进入K页，KEY3加、KEY4减、KEY2退出，页内保留KEY2标注及KEY3跟踪长按。01仅KEY4撤点／删区；11播放中KEY3忽略，不再提示STOP FIRST。相机增加芯片身份、六寄存器写后读回及明确故障。

采用Jeremy批准的两项显示优化：底栏共用数值转换器，矩形在消隐期逐区准备下一扫描行、标签避让逐项计算。完整文字、标签位置、A/B框、全部倍率配色、四矩形、示教及720p/624+96保留。靠近／远离／静止继续暂缓，保留区内停留；原生细节采集仅完成可行性说明，尚未合入。

功能/编译源码fe98cc43b4450ff094b32503303a169360f2591a。155/155项当前软件通过（reports/stage1/software_current_display_20261028_0954.json）；原160项中145项保留原证据、15项相机依赖已重新执行。84视频70287360像素、4组完整采集链路仿真48显示帧38338560像素、K数学18524组、实际K采集10帧9216000像素、35相机专项与22相机OSD场景均通过。新增共享数值512例、完整底栏256例32768字符、14组渲染11182080像素及20组拥挤／裁剪标签15974400像素等价检查通过。长路线等比加速与真实75MHz消抖联接分别记录。

当前源码已完成整机综合，布局build/stage1_place_20261028_160918及最终布线build/stage1_route_20261028_162228_338952均退出0，原约束不变；最终零DRC、无多驱动及异常时序路径、Bound Check通过，建立+0.110ns、保持+0.020ns。实际19030 Slice/18661 LUT6/22131寄存器/98 ERAM/40 DSP。物理配置采用厂商TimingUltra，布局策略2、高扇出阈值128；实际参数见交付目录flow_options.json。304当前/冻结/rawGit、检查点与约束往返、用户TD原字节和22交付保护负例核验通过。暂停取消与已复现失败记录均保留，不冒充通过。

软件与物理通过仅标候选；交付须通过严格同源打包及另起进程独立核验。最终烧录路径、bit及源码包SHA256以新交付目录delivery.json、SHA256SUMS.txt为准。实物待Jeremy，本轮未推送、未上板、未写Flash。

## 历史候选：30秒示教与四矩形共享电路（2026-10-26）

Jeremy晚间批准：共享四区停留计数器，四矩形轮流使用一套判断电路；暂缓靠近／远离／静止分析，回放改为播放／停止／从头重播。播放中KEY3保持运行并提示STOP FIRST，实时10档原暂停仍保留。30秒/20Hz时间戳、停顿、视口跟随、四区域、全部五倍率/两组配色、624行视频+96行底栏及原检测保留。

当前c0c09cf整机物理已通过：place220555及route222201_476507退出0，完整新综合，正常16线程布线无重试，原约束不变；最终零冲突DRC、无多驱动／异常时序路径、Bound Check通过，建立+0.009ns、保持+0.020ns。实际18927 Slice/18539 LUT6/21875寄存器/98 ERAM/40 DSP。物理审查reports/stage1/lean_final_physical_20261026_224302.json；新bit已生成，最终交付目录及SHA256以delivery.json和SHA256SUMS.txt为准。软件124/124全部当前通过；84项视频70287360像素、4组真实采集联接48显示帧38338560像素均通过，报告reports/stage1/software_current_lean_20261026_225925.json。

旧8413的121软件和91.41%布局不是本版结果。旧8413版普通布线最低1396处冲突仍报错，回退日志缺终态；这些失败记录均保留。备份和接续索引build/stage1_teach_lean_20261026_213350/state.json。最终需当前软件全过、零DRC/无异常路径/建立保持非负，以及同源包和独立核验。见[操作与22步实测表](docs/示教录制回放与运动状态_操作与验证.md)。不推送、不上板、不写Flash。

## 历史修订：跨帧记点、两点自动保存与常显底栏（2026-10-25）

在Behaviour_region_1024完善4个矩形A-D。正常换帧消隐不再误取消按键；第二点松手自动校验保存；KEY3短按清草稿，KEY4撤点/逆序删区。KEY2长按只隐藏视频标注，底部两行始终显示，00明确显示实际亮度、倍率和标注开关。真实故障及250毫秒无新图像仍取消，并保留原因。11继续预留。

当前功能/编译源码bda34d3；111项软件与新的整机物理全部通过：最终零冲突DRC、无异常时序路径，建立+0.101ns、保持+0.020ns；18181 Slice/18014 LUT6/21050寄存器/96 ERAM/40 DSP。新候选附delivery.json、SHA256SUMS、bit、同源ZIP及独立核验，实物由Jeremy按[25步实测表](docs/区域顺序_第一阶段_操作与实测.md)确认；本轮不推送、不代烧录。下方10月24日时序与bit为历史候选。

## 历史候选：区域示教与顺序报警第一阶段（2026-10-22）

工作分支`Behaviour_region_1024`，独立入口`td_project/target_color_regions_stage1.al`。支持十字准心示教A–D四区、撤销/删除、顺序测试、乱序/回访蜂鸣报警、暂停、静音和重测；原有四模式、两配色、五倍率与校准/跟踪继续保留。

当前为Jeremy批准的四个轴对齐矩形A-D，每区两个对角点；保留进出、停留计时、顺序报警、删除、静音、暂停和重测，以及原图像、校准、跟踪功能。任意多边形、精确距离与接近/远离显示暂缓，旧多边形算术/绘制缓存不再实例化。功能源码78858ad；107项当前软件与最终布局布线已通过：零冲突DRC、无异常时序路径、建立+0.005ns、保持+0.020ns；18089 Slice/17909 LUT6/20868寄存器/96 ERAM/40 DSP，较G3少1817 Slice及2 ERAM。实物尚待测试；下载以新交付目录delivery.json和SHA256SUMS标明的bit为准，旧失败目录产物不可代替。见[严格审计](reports/stage1/final_rect_build_review_20261024_1304.json)、[验证记录](reports/stage1/validation.md)、[中文操作与实测表](docs/区域顺序_第一阶段_操作与实测.md)。旧交付与源码备份保留。

## 当前实施：颜色识别、视频稳定性与显示功能改进

分支 `release/transparent-ring-stability-20261015`，基线 `2f79847`。本轮入口为 **`td_project/target_color_regions_refined.al`**：独立DDR握手/恢复与相机应答监督、定向背景校准、五档倍率、透明官方Logo、默认底栏及校准提示和v4板内延迟。原工程、历史bit及源码包保留。

10月19日按Jeremy要求取消三个诊断分页及KEY2+KEY3切页，保留四种图像模式、两配色和五档倍率。资源与交付状态见下方清单。

软件与完整TD构建通过，实物待验。[独立测试bit](build/target_color_regions_refined_20261019_100417/target_color_regions.bit)、[同源源码包](build/target_color_regions_refined_20261019_100417/color_video_refined_source.zip)。建立+0.142ns，保持+0.020ns；ERAM100/108，DSP40/40。

[一页校准与拍摄说明](docs/颜色视频显示改进_上板一页.md)、[诊断数字解释](docs/颜色视频显示改进_诊断字段.md)、[验证报告](reports/refined/最终验证报告.md)、[实物复测表](reports/refined/hardware_retest.csv)。实物尚未验证。

新生成器：`scripts/generate_refined_regions.py [--check]`；构建：`scripts/run_refined_build.py --stage full`；审计：`scripts/audit_refined.py --regression --attempt <完整构建目录>`。每次构建使用独立冻结目录；旧生成和构建入口继续属于下方历史版本。

## 当前分支：透明色环稳定性优化（2026-10-15）

`feature/transparent-ring-stability`，基线43564ee；在独立工作区实施四步材料/背景校准、候选质量、v3同帧诊断、官方图标、组合键和默认180°显示，保留双色工具/尖端/跟随。软件与TD通过，实物待验。

[新独立上板测试bit](build/target_color_regions_ring_stability_20261015_033550/target_color_regions.bit)、[同源源码包](build/target_color_regions_ring_stability_20261015_033550/transparent_ring_stability_source.zip)、[操作与最小复测](docs/透明色环稳定性优化_上板与复测.md)、[实际验证报告](reports/transparent_ring/最终验证报告.md)。历史bit和下方历史说明保留，不能用旧bit执行四步流程。

本版实际Slice18981/21216、ERAM100/108、DSP40/40，建立+0.110ns/保持+0.020ns。新输出独立且输入冻结，未放宽约束。完整构建用 `scripts/run_stable_regions_build.py --stage full --prefix ring_stability`；只读审计用 `scripts/audit_color_regions.py --attempt build/ring_stability_full_20261015_014510 --check-build`。不要直接重跑冻结目录run.tcl覆盖历史输出。

## 当前正式工程：双色工具识别、尖端定位与自动跟随（2026-10-14）

本地仓库 `D:/aaa_FPGA/color-regions-env-issues`，分支 `docs/color-regions-env-issues`，基线 `0735398`。沿用 `td_project/target_color_regions.al`：固定白平衡与两组材料校准、八邻域去孤立、80×45 双银行网格、每色四候选、中央选取一件工具、K=0.5 尖端和平滑放大跟随。四页面、配色与倍率操作保留。

[正式 bit](build/target_color_regions_stable_20261014_040811/target_color_regions.bit)、[同源源码包](build/target_color_regions_stable_20261014_040811/color_regions_stable_source.zip)。

[上板与校准](docs/双色工具正式功能版上板.md)、[软件／构建／实物验证报告](reports/双色工具正式功能版验证报告.md)、[正式 bit 与同源 ZIP 清单](reports/stable_regions_delivery.json)。新版实物验收待执行，记录表为 `reports/stable_regions_hardware_trials.csv` 和 `reports/stable_regions_hardware_metrics.csv`。下载文件以新交付清单为准；下方旧版本路径和数据保留为历史记录。

生成正式资产：`python scripts/generate_target.py --color-regions`；只读核对加 `--check`。完整编译：`python scripts/run_stable_regions_build.py --stage full`，每次创建新版本目录。只读审计：`python scripts/audit_color_regions.py --attempt build/最终构建目录 --check-build`。旧版本生成器和无参数入口不用于本次正式工程。

---

## 当前功能工程：独立颜色区域框选（2026-10-13）

唯一推荐的新功能入口为 `td_project/target_color_regions.al`，下载 [target_color_regions.bit](build/target_color_regions/target_color_regions.bit)。采用四像素并行的相对色差/简化色相分类、全图粗网格寻找、局部连通区域分离和三帧确认，每色最多两个独立框；四页为原图、色彩高亮、灰度、色彩二值。移除顶部大诊断面板与旧尖端/自动跟随链路，底栏及原按键、手动倍率保留。

[上板操作与测试](docs/LockingnTracking颜色区域功能版上板.md)、[验证报告](reports/LockingnTracking颜色区域功能版验证报告.md)、[交付与哈希](reports/color_regions_delivery.json)。软件与TD综合布局布线通过：Slice19873、LUT6 18429、ERAM85、DSP9；SWNS+0.128ns/HWNS+0.020ns。bit SHA256 `87956070e9ddfb8d1c3c56cef5adf830b6513b34e9f1d3cd4a5ff2554d8a1e0f`。实物尚未验收，请先验证清晰色环/打印颜色与视频稳定性。后面的老师诊断及旧候选章节是保留的历史入口，不参与新工程编译。工作区从e82a62f继续，没有重置、提交或推送；帧头丢字修复及10份已有bit保持。

## 当前实验：老师 YCbCr 思路的独立颜色诊断（2026-10-12）

从 `LockingnTracking` 的 `e82a62f` 继续，新增8×8真实AWB前后RGB与AWB后Y/Cb/Cr采样、四页旧RGB掩码对照，以及独立窗口标定工具。原判色、面积/填充规则、帧头修复及正常工程保留；当前YCbCr目标分类尚未用实物数据标定。

- 入口：[诊断上板操作](docs/LockingnTracking老师判色诊断上板操作.md)、[标定工具](docs/LockingnTracking老师判色标定工具.md)、[实测记录表](reports/teacher_color_hardware_record.csv)。
- 独立工程 `td_project/target_teacher_color_diag.al`、构建脚本 `scripts/build_target_teacher_color_diag.tcl`、下载输出 `build/target_teacher_color_diag/target_teacher_color_diag.bit`。最终有效版本/构建状态以 `reports/teacher_color_delivery.json` 为准。
- 诊断版 `598716C1` 已通过软件回归、TD综合布局布线及97项输入/9份旧bit哈希审计：Slice20117、LUT6 17612、ERAM75、DSP19，SWNS+0.125ns/HWNS+0.012ns。完整记录见[诊断验证报告](reports/LockingnTracking老师判色诊断验证报告.md)。没有真实样本时不启用YC窗口，不声称色环识别已修复。当前改动尚未提交/推送、未下载或烧Flash；按操作说明先做SRAM诊断采样。

## 最新存档：单色候选功能与帧头丢字修复（2026-10-11）

当前 LockingnTracking 活动源码采用单色候选框与中文诊断存档 `f395cc0` 的功能与颜色参数，只移植 `cf8b7c4` 的 `video_in.v` 帧头暂存／跨时钟握手修复。存档名：**LockingnTracking：恢复单色候选并修复帧头丢字**。代码提交 `fc383a5066740a4cb1b6a425cea64da554ca3cca`，已通过保留远端历史的合并提交推送到 GitHub `LockingnTracking`。远端分支地址：[FPGA_47299 / LockingnTracking](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/LockingnTracking)。

- TD 工程：[target_lock_candidates_ingress.al](td_project/target_lock_candidates_ingress.al)，BitWriter 文件：[target_lock_candidates_ingress.bit](build/target_lock_candidates_ingress/target_lock_candidates_ingress.bit)，SHA256 `92fba519873b691074582b614f03eb081b45b07735934e846767956599803b7d`。
- 完整说明：[Git恢复与帧头修复](docs/LockingnTracking_Git回退与帧头修复_2026-10-11.md)，[工程使用及回归入口](docs/LockingnTracking单色候选与帧头修复.md)，[验证报告](reports/LockingnTracking单色候选与帧头修复验证报告.md)。
- 960 个打包字写入 960 个 DDR 字及视频回归通过；新组合仍需上板验证，不能据此宣称颜色识别或硬件验收通过。

## 最新开发：单色候选框与诊断（2026-10-10）

开启搜索后，红／蓝或黄／紫各自通过检查即可独立画框；只有双色连续3帧合格才显示估算尖端并跟随。视频区新增A/B像素数、填充率和失败原因，KEY3长按可一并隐藏。颜色阈值及原操作不变。

- [单色候选操作与模块路径](docs/LockingnTracking单色候选诊断.md)、[本轮验证报告](reports/LockingnTracking单色候选验证报告.md)。
- 新工程 `td_project/target_lock_candidates.al`，构建脚本 `scripts/build_target_lock_candidates.tcl`，输出 `build/target_lock_candidates/target_lock_candidates.bit`。旧工程和bit保留。
- 存档名：**LockingnTracking：存档单色候选框与中文诊断联调版本**。单元、帧同步、完整视频、72幅OSD及原算法回归通过；TD综合布局布线和源码／bit同源审计通过。
- 仍为联调版本，旧采集帧头丢数据及离焦识别问题未修复。本次按Jeremy要求完成后提交并上传LockingnTracking，不合并main，不下载板卡或烧Flash。

## 最新开发：双配色、中文标注与KEY3长短按（2026-10-09）

在LockingnTracking的061cfd7上新增中文随目标标签、红蓝／黄紫切换和KEY3长短按。**SW3=0红A蓝B，SW3=1黄A紫B；KEY3短按松手启停，长按1秒显隐视频标注；KEY2改为按SW4增减增益。** 长按隐藏仍检测／跟随，底栏状态、配色、标定和安路Logo保留。KEY4按SW4缩放、SW1/2四模式保持。

- [最新操作、参数及接口](docs/LockingnTracking双配色与中文标注.md)，[本轮验证报告](reports/LockingnTracking双配色验证报告.md)。下方旧操作仅作历史，不再按SW3控制显隐／增益。
- 独立入口 `td_project/target_lock_dualcolor.al`／`scripts/build_target_lock_dualcolor.tcl`，输出 `build/target_lock_dualcolor/target_lock_dualcolor.bit`；旧工程及bit保留。
- 存档名：**LockingnTracking：存档中文标注、双配色与KEY3长短按联调版本**。2026-10-09按Jeremy要求将源码、同源bit和验证证据一并纳入本次Git存档，上传目标仅为GitHub的LockingnTracking分支。
- 本轮不加入离焦滤波、锐化或双线性。原帧头丢数据问题未修复；构建同源及本轮软件验证不代替完整采集接入和实物验收。未下载、烧Flash或合并main。

## 最新接续：同步队友实物测试记录（2026-10-08）

已将本地 LockingnTracking 从 `067664c` 快进到 GitHub 同名分支 `21609e587b3d68540f85ec1856ae5b2d7d8966f6`，接收两条提交、三个文档文件的更新；检测源码、参数和 bit 没有随这次远端更新改变。Jeremy确认队友实测“离焦模糊时可以锁定、对焦清晰后不能锁定”，详见 [实物问题记录](docs/实物问题记录_对焦依赖检测.md)。这属于部分实物观察，不是完整验收通过。

本地接续存档名：**LockingnTracking：同步队友实物测试记录并存档离焦锁定问题**。本轮只同步、阅读代码并记录说明，未修复、重新构建或下载；新接续提交仅保存在本地，未推送。标记不要求圆形，颜色、面积、填充率及跟踪条件说明见 [本次接续说明](docs/LockingnTracking接续_2026-10-08.md)。下文2026-10-07内容保留为开发历史，中间bit和采集接入问题仍待处理。

## 当前开发：LockingnTracking（2026-10-07，接入验证未完成）

从本地main `4c26207` 创建 **LockingnTracking**，main与ImproveFourfoldScale分支保留。新增红前蓝后双色检测、估算尖端、KEY3启停持续跟踪、窗口跟随与SW3标注显隐；沿用main最近邻缩放。

- [使用、参数与实现](docs/LockingnTracking使用与实现.md)、[验证报告与接入问题](reports/LockingnTracking验证报告.md)、[锁定状态OSD仿真预览](reports/target_preview/osd_02.png)。
- 新工程 `td_project/target_lock.al`、构建脚本 `scripts/build_target_lock.tcl`。不要使用旧scaling_test入口编译新顶层。
- L=40mm、D=20mm、K=0.5；修改 `rtl/03_tool_detection/target_config.json` 后运行 `scripts/generate_target.py`，再重新编译。
- 独立控制、检测／跟踪、15组完整显示、10幅OSD及原算法回归通过。**AWB→打包→旧FIFO联调复现帧头数据被复位吞掉；整体接入尚未完成。2026-10-07 Jeremy决定保存并上传本分支，具体测试与问题处理交给队友，本次不继续修复。**
- 存档名：**LockingnTracking：存档双色锁定跟踪与OSD开发版本，待队友联调**。上传目标为GitHub同名分支，提交号以Git记录为准。
- 当前target_lock.bit是中间构建，不代表最新源码同源、不可作为可上板交付。未下载、未烧Flash、未合并main；上传不代表问题已修复或实物验收通过。

以下为旧main及更早版本历史记录，不能作为本分支新功能的上板结论。

## 历史主干：准心、手动缩放与中文 OSD（2026-10-05）

当前为 **main**，已同步远端 `8136663`，包含 ScalingTest 功能及队友首次上板验收记录。Jeremy 本次确认队友的十字准心、放大、OSD 功能测试成功；报告记录第 0～5 步通过，第 6 步连续稳定性观察跳过，仅 SRAM 在线下载、未烧 Flash。测试设备为 HX1P35A V1.0、MLK-CAM001 V1.0（SC500CS）、KTC H25T7。

- 当前工程：[scaling_test.al](td_project/scaling_test.al)，构建脚本：[build_scaling_test.tcl](scripts/build_scaling_test.tcl)。旧 `criticalwork.al` 不适用于当前顶层。
- 当前下载文件：[scaling_test.bit](build/scaling_test/scaling_test.bit)，SHA256：`a598cff3ea804c0fbc9e54d1693e03cfc32fa4b9aef2d7133f234879dc6edf8c`。
- [使用与实现](docs/ScalingTest使用与实现.md)、[实物验收与软件验证报告](reports/ScalingTest验证报告.md)、[Git 存档](docs/Git存档说明.md)。
- SW1/2 选择四模式；KEY1 复位；KEY2 按 SW3 调增益；KEY3 按 SW3/SW4 的 00/01/10/11 下/右/左/上移动；KEY4 按 SW4=1/0 放大/缩小。四个开关均已实测上=0、下=1。
- 1/2/4 倍最近邻放大、黄色黑边准心、底部 96 行中文 OSD 及安路标识已实现。4 倍将 320×156 原图区域放大为 1280×624 视频区，单个源像素重复为 4×4 色块；Jeremy 反馈像素感明显，画质优化尚未实施。
- 当前六个综合功能目录为 00/01/02/05/09/10；自动跟踪、双色检测、尖端标定及准心隐藏仍未实现。

本轮运行 `scripts/audit_scaling.py` 通过，核对 65 个工程依赖、来源和构建输入/bit 哈希及已存档测试日志；未重新仿真、编译或下载。存档名：**同步main：存档队友已验收的十字准心、缩放与OSD功能**。

以下为 2026-10-04 四模式阶段历史说明，旧工程入口、按键用途和“缩放/OSD未实现”等描述仅适用于当时版本。

---

更新：2026-10-04；当前主干 **main**，已同步队友四模式实物验收版本v1.2；功能最初在ImagePreprocess分支开发。平台 HX1P35A / PH1P35MDG324 −3，TD 6.2.168116。

新增拨动开关选择与图像处理，顶层已整合并重新综合、布局布线、生成bit。Jeremy于2026-10-04补充截图确认队友提亮后版本已成功摄像头采集并显示，正常观察未发现补黑；**本轮新增四模式已于 2026-10-04 完成实物验收**（`00/01/10/11` 逐项通过，见[第二轮](reports/图像处理验证_10_3.md)与第三轮记录）；仅 SRAM 在线下载，未烧写 Flash；30 分钟连续运行按 Jeremy 决定跳过、记为未执行。

## 操作与入口

两位顺序是 **SW1、SW2**；SW1=A4，SW2=B4。**实物实测极性为上=0、下=1**（与手册 p21 描述相反，见[图像处理与拨动开关](docs/图像处理与拨动开关_10_3.md) 的"实物更正"节）。

| SW1 SW2 位置 | 模式 | 屏幕效果 |
|---|---|---|
| 上 上 | 00 | 原图，不处理（彩色） |
| 上 下 | 01 | Sobel边缘检测（黑底亮轮廓） |
| 下 上 | 10 | 灰度变换 |
| 下 下 | 11 | 二值化，灰度≥128为白 |

开关稳定约20ms后，在下一帧边界切换（2026-10-04 实物验证）。KEY1复位、KEY2/3曝光调节保持原用途。边缘模式的前两行、前两列为黑色，窗口中心与输出坐标相差1像素，详见[算法与接口说明](docs/图像处理与拨动开关_10_3.md)。

- [TD工程](td_project/criticalwork.al)：顶层 `criticalwork_top`，使用项目相对路径。
- [新增图像处理bit](build/imagepreprocess_10_3/imagepreprocess_10_3.bit)及[使用说明](build/imagepreprocess_10_3/使用说明_10_3.md)。
- [本轮验证报告](reports/图像处理验证_10_3.md)、[当前待解决问题](docs/问题清单_10_3.md)。
- [编译说明](docs/编译说明.md)、[架构](docs/架构与接口.md)、[接线与验收](docs/接线与验收.md)、[Git存档](docs/Git存档说明.md)。

三组针对性仿真通过，其中完整720p测试核对3,688,960个有效像素及同步信号。布线后SWNS +1.177ns、HWNS +0.020ns、STA覆盖96.00%；LUT6 10,850、寄存器13,794、slice 13,390（63.11%）。这些是软件验证，不能代替实物验收。

## 目录与范围

| 目录 | 用途 |
|---|---|
| rtl/00_top_control | 板级顶层、PLL/复位连接、开关同步消抖、状态同步 |
| rtl/01_camera | 配置、MIPI/RAW10、厂家彩色转换与128位打包封装 |
| rtl/02_image_preprocess | 显示侧RGB888原图/边缘/灰度/二值化 |
| rtl/10_memory_video_out | DDR缓存、调度、显示时序、处理模块连接、HDMI |
| rtl其余9个目录 | 职责说明，未实现、未接入综合 |
| user_source | 厂家源码/IP原结构；保留队友已登记7项修改，本轮未改 |
| vendor_reference/lab1 | 独立原始基线，193个文件哈希不变 |
| scripts、sim | 编译、审计、仿真脚本；仿真模型不加入硬件工程 |
| build/imagepreprocess_10_3、reports | 本轮bit与软件验证证据 |

原队友bit仍在 `build/criticalwork/criticalwork.bit`，不包含新增处理模块。历史报告按其对应提交理解，不作为新bit的验证结论。

输出维持1280×720、总周期1650×750、75MHz像素时钟，理论约60.606Hz。不是分辨率放大，也不是已实测的标准60Hz。跟踪、局部放大、对准和“安路”Logo叠加尚未实现。

按Jeremy要求，本轮暂不修改打包复位、缓存尾字、完整帧恢复等旧问题。已解决的基础引脚对照与基本出图不再列入当前待办；未解决项集中见问题清单。迁移工程应携带整个文件夹，不能只复制 `.al`。
