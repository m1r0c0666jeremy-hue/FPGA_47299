# 本地工具

当前使用TD 6.2.168116、Icarus 13、Verilator 5.050及GCC 16.2。TD及设备许可由原环境提供；Python脚本均以工程目录自动定位源文件。

Icarus局部运行时在 `tools/iverilog/ucrt64/bin`。下载包及SHA清单位于 `tools/iverilog/manifest.json`。

长用例的原生仿真工具在 `tools/native_sim/ucrt64`，包版本、URL及SHA位于其 `manifest.json`。这套工具不要求系统级安装，不改变永久PATH。移植时可以准备同版本工具，或根据已保留的MSYS2索引重建：

```powershell
New-Item -ItemType Directory -Force build/tool_index | Out-Null
tar -xf tools/iverilog/ucrt64.db -C build/tool_index
python scripts/install_fhd_native_sim.py
```

安装脚本校验每个包的SHA256并只解压到工程的tools目录。索引中的包版本须与清单对应，不能静默换版本。MSYS2包的许可证保留在工具安装目录内。

Verilator使用带时间控制的编译仿真，不启用未支持结构黑盒选项。相同源、夹具、参数和工具清单的显示矩阵在同一进程中复用一次编译，每个组合独立运行并记录可执行文件哈希和参数。四态初始化/错误检查仍使用Icarus。

文档：[Verilator执行选项](https://verilator.org/guide/latest/exe_verilator.html)、[MSYS2 Verilator包](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-verilator)。
