# Final_Mode_1101 配色与帧率演示候选（沿用旧DDR配置）

本目录的 `target_color_regions.bit` 可供Jeremy上板验收，未代烧录或写Flash。
以4081ad0旧版为基线，只改红A黄B默认／蓝A紫B备用和有效图像FPS；全部旧功能保留。
正式TD工程：`td_project/target_color_regions_stage1.al`（仓库根目录下）。
操作见仓库 `docs/Final_Mode_1101_配色与帧率演示版.md`。

- 实际编译提交：27da04b18bf1ed71d445a852be23d075f0eaf9db。
- 当前158项及基础160项通过；最终DRC冲突0、无异常时序路径，建立+0.006ns、保持+0.020ns。
- 资源：19009 Slice、98 ERAM、40 DSP；原约束保持。
- 独立核验2223同源成员及304编译输入通过，见independent_verification.json。
- bit SHA256：`7998532c9ef6678883f1035e7fea374ed977065c73694ab8288ee98ba4866bd4`。

本地完整交付：`D:/aaa_FPGA/region-sequence-stage1/build/target_region_sequence_stage1_20261101_024300`。
同源源码与证据包：该目录 `region_sequence_same_source.zip`（约204MB，本地保留，未作为普通Git文件上传）。
源码包SHA256：`c6a789d29bfbecb60900d42c33380d3aca5d0f10aef5a9b614fee8d7f44de8ef`。远端可通过本分支获取源码。

仍沿用旧DDR配置；实际50MHz参考与IP名义100MHz存在已知不匹配风险，未确认为花屏根因，也未在本版修正。
软件和物理通过只标候选，严重花屏及长期运行稳定性待Jeremy实测。
优化版已独立存档，未混入本演示版。
