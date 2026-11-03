# ImproveFourfoldScale：4 倍双线性显示

日期：2026-10-05。分支从本地 main `4c2620782e7f29367620975b51e850a34f846ef1` 创建。功能按 使用者 确认的方案实现，**新 bit 待上板**；main 的实物验收不能替代本版本验收。

## 使用范围

| 显示模式 | 1 倍 | 2 倍 | 4 倍 |
|---|---|---|---|
| 原图、灰度 | 原结果 | 原最近邻 | 双线性 |
| 边缘、二值化 | 原结果 | 原最近邻 | 原最近邻 |

所有按键、开关、增益、移动速度、倍率和底部 OSD 布局不变。SW1/2 仍为原图/边缘/灰度/二值化；SW3/4 均上=0、下=1。未新增板上算法切换操作。用 main 的旧 bit 与新 bit 对比，不通过改变开关映射切换算法。

双线性降低块状感，也会柔化细线、窄间隙和轮廓；不增加光学分辨率，不保证精密测量精度。本版本无锐化、超分辨率、AI 补图、多帧融合或跟踪。

## 坐标与算术

源图仍为 1280×720，视频区仍为 1280×624，底部 96 行为 OSD。4 倍选取 320×156 源区域，窗口与原图坐标保持原定义。

双线性使用以四分之一源像素为单位的局部坐标：`qx=clamp(x-2,0,1276)`、`qy=clamp(y-2,0,620)`。整数部分为 `qx/4,qy/4`，小数权重 `a=qx%4,b=qy%4`。四邻域在当前窗口内复制边界，不取窗口外数据。源像素 i 的中心在屏幕 `4*i+2`，因此黄色准心仍对应选定的原图采样位置；这不是半像素中心或 align_corners 坐标约定。

RGB 三通道分别计算：

```
H0=(4-a)*P00+a*P10
H1=(4-a)*P01+a*P11
C=((4-b)*H0+b*H1+8)>>4
```

水平和为 10 位，纵向和连同舍入偏置为 12 位。只在最后舍入一次，最大累加值 4088，输出自然在 0～255，且不超过四邻域的最小/最大值。乘 0/1/2/3/4 使用移位加法；不新增 DSP。最近邻路径用零权重走相同流水线。

灰度在插值后的 RGB 上使用旧公式；边缘、二值化在处理前旁路插值，像素结果保持 main 行为。未更改 Sobel 原有右下一个像素的窗口位置定义。

## 缓存、帧同步与故障处理

四个逻辑行缓存以源行号低两位分配，每行 128 个打包字位置中使用 80 个。每个字含 16 个 RGB888 像素，仍以三个 DDR 128 位响应拼接。四份 384×512 双时钟 RAM 接收相同写入，分别读取四邻域，每拍一个输出像素，跨 16 像素字边界也无需多周期停顿。

每行仍请求 240 个 DDR 事务；只是预取更早，不增加所需源行范围。行号和有效标志区分缓存内容；参与读取的旧行在 RAM 读取完成前不得复用。地址寄存的一拍由 `read_hold` 保护，正在加载的银行由唯一 pending 请求保护。RAM 数组及 RAM 输出寄存器不整体复位。

DDR 读写仲裁沿用 main 的最后写入拍保护，相机不增加反压。请求参数保持到应答；帧缓存基址只在帧首请求锁定。本次用保持到应答的 stale 标志替代有限位宽帧计数来丢弃跨帧旧响应，避免旧响应等待多帧后代号回绕误接纳。

所需任一行缺失时，故障像素及本帧剩余视频为黑，OSD 保留；旧请求排空后在后续帧恢复。DDR 若永不返回响应，仍不能自动恢复；不修复厂家采集坏帧隔离、旧打包复位或整个缓存管理。

窗口模块新增两位模式输入/输出，与坐标、倍率在原始 VS 上升沿一起提交。缩放器延后锁定该组参数，下游图像处理同样使用已提交模式。板级端口不变。

缩放器五级寄存依次为：地址/参数、RAM 输出、邻域选择、水平和、纵向输出。图像处理五级、OSD 两级，合计十二级；输入采样沿算第一级，输出于 n+11 沿更新。RGB、HS、VS、DE 同延迟；显示可用标志按缩放输出对齐。相对 main 增加三拍，即像素时钟 75 MHz 下约 40 ns，非端到端延迟实测。

## 构建与复现

新工程为 `td_project/improve_fourfold_scale.al`，构建脚本为 `scripts/build_improve_fourfold_scale.tcl`；输出 `build/improve_fourfold_scale/improve_fourfold_scale.bit`。**不能使用旧 scaling_test 构建脚本构建本分支**，以免缺少新模块或覆盖旧证据。

在项目根目录执行，Python 可使用本机已安装的便携运行时：

```powershell
python scripts/test_fourfold.py
python scripts/test_fourfold_reset.py
python scripts/test_fourfold_fault.py
python scripts/test_fourfold_osd.py
python scripts/test_fourfold_preprocess.py
python scripts/preview_fourfold.py
& 'D:/26_software/TangDynasty/bin/td_commands_prompt.exe' D:/aaa_FPGA/criticalwork/scripts/build_improve_fourfold_scale.tcl *> reports/td_improve_fourfold_scale.log
python scripts/audit_fourfold.py --record-build
python scripts/audit_fourfold.py
```

`--record-build` 仅在新构建成功、源文件未晚于 bit 后记录哈希，不用于掩盖源码变化。测试输出在独立目录，旧 main 日志、bit 和审计脚本不修改。旧 `audit_scaling.py` 针对旧构建清单，当前分支使用新审计入口。

## 来源与修改范围

优先核查 `D:/BaiduNetdiskDownload/HX1P35A_Contest_202606` 的 2026 Lab1～Lab3、比赛文档包及参考 IP 文档包。已找到的 `isp/demosaic_4x_2_0/bilinear_interpolation.v` 是 Bayer 颜色还原，不是图像缩放。本版本继续使用其既有相机/ISP 基础，没有修改厂家文件。Lab1/Lab3 的原始来源和哈希仍见原 manifests。

其次查阅 [freecores/video_stream_scaler](https://github.com/freecores/video_stream_scaler/blob/master/rtl/verilog/scaler.v)，参考相邻两行和四邻域插值思路。该通用实现声明系数量化误差，本项目没有复制、编译或移植它的源代码，而是独立实现固定 4 倍精确权重、当前 DDR 协议和准心坐标约定。不存在引入其他厂商 FPGA IP 的要求。

## 上板对照步骤与结果（2026-10-06 已执行）

1. 固定相机、拍摄距离、目标、照明和增益；准备细线、窄间隙、斜边及真实工具。记录板卡、镜头、屏幕与下载 bit 哈希。
2. 用旧 main bit 记录 1/2/4 倍四模式画面及选点坐标；换新 bit，恢复同样参数。仅 SRAM 在线下载，不烧 Flash。
3. 4 倍原图/灰度观察方块过渡，同时确认细线、窄间隙是否仍可辨。不能只以"更平滑"作为验收依据。
4. 对照 1/2 倍全部模式及 4 倍边缘/二值化；确认按键、增益、准心尺寸/落点、中文和 Logo 不变。
5. 移动工具、移动观察窗到四角，反复切倍率/模式及复位；检查新增错位、闪烁、异常黑屏、拖影。记录实际连续观察时长，30 分钟不设为前置条件。
6. 通过/失败与具体异常写入新报告。未执行的项目保持待测；失焦或镜头分辨率不足须与插值问题分开记录。

### 执行结果（2026-10-06，使用者 实测）

第 1～5 条已执行并**通过**：4× 原图/灰度确认为双线性（同机位 A/B：边缘过渡宽度 17 → 25 像素）；
细线/窄缝**仍可辨**（窄缝平均深度 0.71 vs 0.71，缝 1/2/3/4/6px 五组均可解析）；1×/2× 与 4× 边缘/二值化
与旧 bit 无可辨差异；准心、OSD、按键、增益与动态稳定性均与 ScalingTest 一致。
第 6 条结论见 [上板验收结论](../docs/ImproveFourfoldScale上板验收结论.md) 与
[验证报告](../reports/ImproveFourfoldScale验证报告.md)。30 分钟连续运行与 4× 二值化"白级"两项**未覆盖**（按决定不再补测）。
