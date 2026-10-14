# 当前实施状态（2026-10-14）

当前仓库为 `D:/aaa_FPGA/color-regions-env-issues`，分支 `docs/color-regions-env-issues`，基线 `0735398`。Jeremy 已批准实施正式双色工具、尖端与跟随方案；沿用 `td_project/target_color_regions.al`，编译白名单切至 `stable_*` 和串行 `regions_divide`。具体交付文件、同源哈希与最终状态以 `reports/stable_regions_delivery.json` 为准。

操作见 [双色工具正式功能版上板](双色工具正式功能版上板.md)，软件/构建/实物结果分别见 [验证报告](../reports/双色工具正式功能版验证报告.md)。实物记录为两份 `stable_regions_hardware_*.csv`，尚无新版实测数据。原 `criticalwork` 工作区及其未提交 `.al` 修改保留。

以下为历史颜色区域版记录，其 bit 路径、旧协议及“不输出尖端/不自动跟随”描述不适用于当前正式工程。

# 历史实施状态（2026-10-13）

**最终状态：功能bit已经完成综合布局布线，软件与同源审计通过，实物待验。** 唯一下载文件为 `build/target_color_regions/target_color_regions.bit`，SHA256 `87956070e9ddfb8d1c3c56cef5adf830b6513b34e9f1d3cd4a5ff2554d8a1e0f`。最终Slice19873/21216、LUT6 18429/21216、寄存器21416、ERAM85/108、DSP9/40；SWNS+0.128ns/HWNS+0.020ns，覆盖97.87%。200项冻结输入和10份历史bit核对通过。交付包、报告和测试路径以 `reports/color_regions_delivery.json` 为准。

低饱和材料近似输入及28%填充薄环的两配色缓慢移动、消失清框验证通过；最终OSD八完整帧覆盖四页、两配色、三倍率与隐藏。完整记录为 `reports/LockingnTracking颜色区域功能版验证报告.md`。当前没有提交、推送、下载或烧Flash。

## 下方为最终构建前的实施过程记录

功能工程 `td_project/target_color_regions.al` 已生成并接通。源码在 `rtl/color_regions/`，只编译明确列出的功能模块及原厂家采集/DDR/ISP；顶部老师诊断、旧全局检测与尖端跟踪不参与编译。仍为LockingnTracking/e82a62f，未提交、推送或烧录。

已实现：四像素并行判色、两帧银行粗网格、每色局部8邻接行程连通分析、共享帧后归并/除法、每色两候选与三帧确认、416位结果/451位图像快照、实际图像银行选择、不可变首行请求、四个功能页面和精简中文OSD。局部范围用一个帧后运算单元轮流计算四槽，全部完成后原子发布，不串行化输入像素。

已通过独立参考和模块/联接测试：36116判色像素、36800四像素行程组、10类连通行处理（环形、对角、32/33段、128/129标签和行末3事件）、13类帧后归并（512边/深度7边界）、4完整720p粗网格帧；两配色各9完整采集帧，短/长/故障、SOF与首像素同拍、空拍、启停、切色/会话、准确64像素RGB和恢复；宽数据跨域/帧银行/显示联接、重复/跳号、银行复用、帧号回绕、忙碌与冻结银行恢复；ROI重叠/相邻/实际边缘/更新撞SOF检查。

原960字精确DDR写入及完整帧/三组异步时钟回归通过。功能视频15组19帧（15175680源图像素）四页面/三倍率/DDR停顿与图像切换回归通过；中文框及底栏预览在 `reports/color_regions_preview/`。最终扩展OSD倍率/配色和原子范围版本的采集恢复回归正在收尾。

当前最后完整构建尝试为 `build/color_regions_full_20261013_073802/`。综合估算Slice20945、ERAM85、DSP9，**尚非最终布局布线数据**。旧225900尝试在布线未收敛时结束，073609尝试为修正ROI原子发布而在布局前停止；各输入快照/日志保留，不标为通过。最终bit尚未生成；不能使用旧诊断bit代替。

最终交付必须经构建输入逐项核对、原RTL与旧bit保护审计、非负建立/保持余量和打包哈希核对，输出到 `build/target_color_regions/`。操作与测试见 [上板说明](LockingnTracking颜色区域功能版上板.md)，实物记录模板为 `reports/color_regions_hardware_record.csv`。实物尚未验证。

---

# 以下是初始实施记录（已被上述状态更新）

User approved implementation on LockingnTracking, e82a62f. No reset, commit,
push or download. Historical teacher diagnostics and all old bits are protected.
Baseline freeze: reports/color_regions_baseline.json and its verified source ZIP.

Active intended entry: td_project/target_color_regions.al (not generated yet).
Intended bit: build/target_color_regions/target_color_regions.bit (NOT BUILT).
Do not offer the old diagnostic bit as this delivery.

Implemented so far:
- New relative-chroma/hue four-pixel classifier, four cycles. Generated ONLY by
  generate_target.py --color-regions [--check]; regions_* integer configuration.
- Independent Fraction hue and pixel BFS Python oracle.
- Four-pixel horizontal run frontend: up to three closing runs at EOL.
- Bounded per-colour run labeler: 32 runs/line, 128 labels, 512 edges, 3 RAM line
  banks sharing two ports, eight-event FIFO, dual-frame statistics, 288 deadline.
- Frame finalizer: rank union, moments/boxes, shared restoring divider, score,
  fair candidate selection across two ROIs, capacity/deadline invalidation.
- Double-bank 40x23 dual-colour coarse grid, segment accumulation and frozen
  background flood fill, 65536 cycle limit; counts use one capture RAM port.
- 416-bit result / 451-bit frame-store and fixed-center display modules written,
  not tested or connected yet. Frame-store chooses actual newest matching bank.

Passed current tests (Python311 at C:/Users/w/AppData/Local/Programs/Python/Python311/python.exe;
iverilog/vvp under tools/iverilog/ucrt64/bin with its directory added to PATH):
- test_color_regions_classifier.py: 9029 groups = 36116 pixels, bubbles/boundaries.
- test_color_regions_runs.py: 36800 groups, moments/membership/clipping/overflow.
- test_color_regions_labeler.py: independent pixel components, empty/solid/ring,
  diagonal, 32/33 runs, 128/129 labels, full width. Worst measured row 204 clocks.
- test_color_regions_finalize.py: 11 cases, ranking/fairness/clipping and divide.
- test_color_regions_grid.py: four full 720p frames, every grid count and ROI;
  worst both-colour 920-cell active case 53541 clocks (limit65536).
Logs are reports/color_regions_*.log. These are module tests, NOT hardware proof.

Still required:
1. Capture pipeline: original raw SOF frame numbering, four-cycle sideband delay,
   count/fault validation, ownership of double banks, two labelers and one shared
   finalizer, grid scan, frame-boundary ROI commit, 8x8 post-RGB sample and packet.
2. Three-frame per-candidate confirmation, two slots per colour, 96px guard,
   session/pair/enable and consecutive ID checks, no stale or tip output.
3. Test frame-store/display; mailbox readiness, actual image selection and stable
   reader first-request bank+frame bundle; latest completed empty beats old boxes.
4. Functional pages/raw/highlight/grey/colour binary, compact Chinese footer and
   2px boxes, KEY3 long hide, no giant diagnostics; source-centre sample only on
   highlight page; no new top PRE/YC panel or old tip tracker.
5. Generate explicit .al/top/memory/reader wrappers, exclude old detector/tracker,
   teacher/diagnostic/Sobel chain. Preserve video_in.v SHA
   6c02b617ef32c478ab39bf17e0fe5e48a3f6e38eca1796bf628cb19052c7838b.
6. Integration/video/960-word regression, module and whole design TD synthesis,
   P&R, resource/timing audit, source snapshot/bit matching, hardware guide.

Potential follow-up test/fix notes:
- regions_run_labeler abort priority on malformed early EOL should be checked;
  healthy lines meet budget, but the case statement can override an early abort.
- regions_grid NEIGHBOR_GET queue-full state assignment can be overridden by the
  later neighbour-advance assignment; make error priority explicit. Real visited
  BFS cannot exceed920 cells, but fault guard should still be structurally sound.
- Add simultaneous capture on other bank during grid read, arbitrary valid gaps,
  bank-clear/SOF collision, graph depth and512-edge boundary tests.
- Existing graph finalizer uses one colour per call (65536 clock deadline); top
  shares it across two colours. Coarse phase then65536 -> total196608 plus small
  controller overhead <230400. Source updates cannot overwrite owned banks.
- Grid address calculation assumes WIDTH1280/GW40; preserve that contract or
  parameterize properly before using a smaller-width testbench.

Candidate128 layout: root127:121, valid120, score119:92, ROI91:90,
fill89:83, cy82:73, cx72:62, count61:42, ymax41:32, ymin31:22,
xmax21:11, xmin10:0.
Stat149 layout: clip148, ROI147:146, sumq145:124, ymax123:114,
ymin113:104, xmax103:93, xmin92:82, sy81:51, sx50:20, count19:0.
Packet416: original low256 first A/B coordinates/area/fill/tags; tip zero;
bit255 done; bits234:231 per-colour error; second A64 [319:256], B64[383:320]
each {more, valid, count20, box42}; [407:384] RGB mean;408 sample valid;
412/411 coarse-more A/B;415:413 protocol1; remaining bits zero.
