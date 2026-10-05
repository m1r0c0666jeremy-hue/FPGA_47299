# 大赛 Lab3 OSD 参考代码

2026-10-05，按 Jeremy“先用大赛资料，再查 GitHub”的要求，优先检查本机 `D:/BaiduNetdiskDownload/HX1P35A_Contest_202606` 的 SC500 实验。此处四个文件来自 `7_lab_ex_2026_nosoft/lab_ex3_osd_SC500_720P.zip`，保持原始字节，完整入口和 SHA256 见 [manifest.json](manifest.json)。厂商原有署名保留；未将参考文件重复加入综合。

| 文件 | 本次采用方式 |
|---|---|
| hdmi_mixer.v | 参考按视频位置叠加字模和标识的结构，扩展为帧参数、中文双行底栏和准心 |
| osd_char_lib.v | 生成脚本实际抽取 `0123456789EKY安路：` 的16×16点阵，最近邻调整到24像素字符单元；缺失汉字由本机黑体补齐 |
| anlogic_logo_rom.v | 保存参考；原版160×160固定Logo与本次横向96行底栏不匹配，本次采用已保存的官网独立图形，生成96×62两位调色板同步ROM |
| key_remove_shakes.v | 保存参考；它只产生单次按下脉冲，不提供本次需要的多键冲突、长按加速、开关锁定和复位后等待释放，因此控制模块单独实现 |

现有 Lab1 的采集、ISP、打包、DDR 写入和 HDMI 代码继续沿用，原193文件基线及已登记的7项厂家工作副本修改保持不变。未在查阅的大赛 SC500 实验和文件名索引中找到能直接接入现有128位DDR协议的选点缩放模块；这不代表已逐一审计所有压缩包内的全部源码。

其次比对了 GitHub 上 [FreeCores video_stream_scaler](https://github.com/freecores/video_stream_scaler/blob/master/rtl/verilog/scaler.v)。它的输入/输出是单时钟逐像素握手，不能直接处理本工程 DDR 行地址、128位打包和跨时钟缓存所有权。本次没有复制该项目代码；`scaling_line_reader.v` 针对当前厂家接口实现。数字放大只重复已有像素，不增加光学细节。

生成脚本只保存本次所需字形，不附带整套字体。复现须提供与生成清单哈希一致的 `simhei.ttf`、Python Pillow、Node.js Sharp；已有 RTL ROM 可直接参与综合，无需运行素材生成。
