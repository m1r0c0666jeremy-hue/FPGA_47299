# Region_Recognition_1019 存档说明

- 存档名：**Region_Recognition_1019：双色区域识别、五档放大与视频稳定版（默认底栏）**。
- 分支：`Region_Recognition_1019`。
- 功能交付基线：`56a716b05ed1388631d53885de9ffa9bbc85028d`。
- 实际编译源码：`ca2622973e41f96a06b8baf747334a74ddbc2595`；295项编译输入与该提交逐字节一致。
- GitHub：[Region_Recognition_1019](https://github.com/m1r0c0666jeremy-hue/FPGA_47299/tree/Region_Recognition_1019)。

## TD打开的工程

`D:/aaa_FPGA/transparent-ring-stability/td_project/target_color_regions_refined.al`

这是当前功能工程入口。原`target_color_regions.al`的用户未提交修改继续保留，本存档不修改或提交该文件。

## 烧录的bit

`D:/aaa_FPGA/transparent-ring-stability/build/target_color_regions_refined_20261019_100417/target_color_regions.bit`

SHA256：`fe6029bb4fd343df1e7757418c1b2540e2c9884d93f27206a9464509bc3586fe`

同源源码包：`build/target_color_regions_refined_20261019_100417/color_video_refined_source.zip`

源码包SHA256：`84711c7f21cb0f5d025d3842c9cb52cc62028695356b4442e9f5b5981ec5502e`

同目录有SHA256SUMS.txt、冻结编译输入和完整报告。旧bit与源码包保留。

## 功能与验证状态

保留四种图像模式、红蓝/黄紫两配色、1/1.5/2/3/4倍、默认180°、双色工具选取/尖端/跟随、透明官方Logo和板内延迟。底栏仅保留概况和校准提示，KEY2+KEY3不再分页。

157项当前源码软件检查及完整TD通过：Slice17584/21216、ERAM100/108、DSP40/40；建立+0.142ns，保持+0.020ns。STA覆盖98.65%，原时钟与例外限制如实保留，约束未放宽。

本次仅新增分支和存档说明，不修改功能源码或重建bit。46项实物结果仍待验，未执行板卡下载或Flash写入。

操作见[一页上板与拍摄说明](颜色视频显示改进_上板一页.md)，验证见[最终报告](../reports/refined/最终验证报告.md)。
