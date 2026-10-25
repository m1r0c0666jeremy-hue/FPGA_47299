# 720p 回退：放大显示，保持源图坐标

当前本地分支：`rollback/720p-source-coordinates`。已按用户确认恢复英文 720p 基线，原编译提交为 `09cccd89e34f2508aeae342a4b1e6819a920d889`。

摄像头和 HDMI 均为 1280×720；视频区 1280×624，底栏 96 行。保留 1×、1.5×、2×、3×、4×局部放大、0°/180°、跟随、四图像模式、两配色、校准和英文 OSD。

同一目标的源图坐标在所有倍率下保持不变。比如源 `(640,360)` 始终为 `(640,360)`；屏幕上的视频、框线和尖端标记按当前视窗映射。视窗中心仍可跟随并限位，不等同于目标坐标。原界面没有数值 X/Y 或 UART 输出，本次保持现有结果元数据接口。

实际恢复的旧时钟是 75MHz 像素、375MHz 串行，总时序 1650×750，理论刷新率约 60.606Hz，不能写成精确 60.000Hz。

## 上板文件

本次候选索引见 `reports/720p/delivery_index.json`；现场使用 `720p_source_coordinates_sram.bit`，先做 SRAM 下载。

这是原已审计 bit 的复用交付，SHA256：

`18fbffee70889073d44f3598029cce8bc5b0662d37f0911e138998315f83844a`

297 项编译输入必须与原冻结输入完全一致。原物理构建：17555 Slice、95 ERAM、40 DSP，建立 +0.103ns、保持 +0.020ns。160 项旧软件证据为历史复核，本次新回归见 `reports/720p/validation.md`。实物仍待验。

[现场下载与操作](docs/720p_回退上板说明.md)；[确认规格](.scratch/720p-source-coordinates/spec.md)。更早的项目历史保存在 `docs/720p_历史README.md`。

## 验证与再次打包

本机已配置局部 Icarus 和 Verilator/GCC 运行时，版本与来源见 `tools/` 中清单。源码包不含二进制运行时，换机器需准备相同工具。长视频使用 Verilator 两态带时间模型，坐标、控制及代表性像素检查仍使用 Icarus 四态模型。

从交付 ZIP 解压源码时，先在源码目录准备与本机工作副本相同的基线文件位置（交付文件与源码目录放在同一父目录），然后安装上述仿真工具：

```powershell
New-Item -ItemType Directory -Force "build/baseline_720p" | Out-Null
Copy-Item "../720p_source_coordinates_sram.bit" "build/baseline_720p/target_color_regions.bit"
Copy-Item "../historical_build_evidence.zip" "build/baseline_720p/osd_memory_same_source.zip"
```

完成后，完整回归和默认打包命令均可使用：

```powershell
python -X utf8 scripts/run_720p_regression.py --workers 3
python -X utf8 scripts/package_720p.py
```

从交付的源码 ZIP 解压后，原 bit 和历史证据在交付目录的相邻文件中，可显式指定：

```powershell
python -X utf8 scripts/package_720p.py --bit "../720p_source_coordinates_sram.bit" --historical-evidence "../historical_build_evidence.zip"
```

打包入口逐项检查历史证据、297 项编译输入和 bit 哈希，任一变化都会拒绝复用。若以后修改 RTL、工程或时钟，必须另行完整 TD 构建；旧脚本有历史分支和路径保护，不能把失败保护直接删除来伪造新构建通过。

TD 工程入口为 `td_project/target_color_regions_refined.al`，顶层 `criticalwork_top`，器件 PH1P35MDG324 -3，TD 6.2.168116。为保持构建来源一致，本次保留该工程的原始字节；如果 TD 重新保存了工程，需重新检查编译输入。
