"""Publish only a source-matched timing-passed FUNCTIONAL bit, never a diagnostic substitute."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,zipfile
from audit_color_regions import audit,read,sha,R

def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copy_once(source,dest):
 if dest.exists():assert sha(source)==sha(dest),'Refuse to overwrite: '+str(dest)
 else:shutil.copy2(source,dest)

p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);a=p.parse_args()
attempt=(R/a.attempt).resolve();m=audit(attempt,True)
required={
 'classifier':['9029 groups','rational oracle'],
 'runs':['36800 groups','three-event EOL'],
 'labeler':['PASS ring','PASS diagonal_equality','PASS 32_runs','PASS 128_labels','PASS three_eol_events'],
 'finalize':['PASS frame-finalizer case 13','17174 cycles','17154 cycles'],
 'grid':['PASS all_active','53541 cycles'],
 'transport':['PASS functional frame store','PASS confirmation','PASS display atomic blank commit'],
 'association':['6 asynchronous full transactions','416/451-bit CDC'],
 'roi':['PASS ROI','SOF collision atomicity'],
 'backpressure':['PASS backpressure','frame wrap and recovery'],
 'capture_pair0':['PASS capture: pair=0','9 full frames'],
 'capture_pair1':['PASS capture: pair=1','9 full frames'],
 'capture_pair0_moving':['PASS moving low-saturation materials','B thin ring 28% fill'],
 'capture_pair1_moving':['PASS moving low-saturation materials','B thin ring 28% fill'],
 'faults':['PASS capture faults','exact centre RGB','recovery'],
 'osd':['zoom=2 pair=1','zoom=1 pair=0','show=0'],
 'video':['PASS functional video:'],
 'ingress':['PASS AWB 960 packed = 960 DDR, all data/addresses matched','PASS ingress CP=8 DP=7','PASS ingress CP=5 DP=11','PASS ingress CP=11 DP=5']}
logs={}
for name,markers in required.items():
 file=R/f'reports/color_regions_{name}.log';s=read(file)
 assert all(marker in s for marker in markers),(name,markers)
 assert 'FATAL' not in s and 'Traceback' not in s and 'ERROR' not in s,name
 logs[file.relative_to(R).as_posix()]=sha(file)
video=read(R/'reports/color_regions_video.log')
assert video.count('PASS functional video:')==15
assert sum(map(int,re.findall(r'pixels=\s*(\d+)',video)))==15175680
assert read(R/'reports/color_regions_osd.log').count('PASS compact OSD full frame')==8
out=R/'build/target_color_regions';out.mkdir(exist_ok=True)
files=[q for q in attempt.iterdir() if q.is_file() and (q.suffix in ('.bit','.area','.ts','.timing','.qor') or q.name.endswith('_clocks.txt'))]
for q in files:copy_once(q,out/q.name)
copy_once(R/'reports'/(attempt.name+'.log'),out/'build.log')
copy_once(attempt/'inputs.json',out/'build_inputs.json')
copy_once(attempt/'run.tcl',out/'build_attempt.tcl')
m.update(test_logs=logs,interface={'capture_pixels_per_clock':4,'classifier_cycles':4,'result_bits':416,'snapshot_bits':451},
 hardware='NOT TESTED',classifier='RELATIVE_CHROMA_AND_HUE_ENGINEERING_DEFAULTS_NOT_CALIBRATED',
 limits={'runs_per_line_per_color':32,'labels_per_color':128,'edges_per_color':512,
         'line_deadline_cycles':288,'finalizer_deadline_per_color':65536,'grid_deadline':65536,
         'measured_max_line_cycles':203,'measured_finalizer_max':17174,'measured_grid_max':53541,
         'frame_minimum_input_clocks':230400,'stale_display_frames':15},
 validation_counts={'classifier_pixels':36116,'runs_groups':36800,'capture_input_frames':47,'capture_complete_length_frames':45,
                    'functional_video_frames':19,'functional_video_pixels':15175680,'osd_complete_frames':8},
 git='HEAD preserved; functional changes uncommitted; no push; no download or Flash programming')
manifest=R/'reports/color_regions_build_manifest.json';save(manifest,m)
area=m['resources'];tim=m['timing_ns']
attempts=[]
for d in sorted((R/'build').glob('color_regions_*')):
 q=d/'target_color_regions_gate.area'
 if not q.is_file():continue
 s=read(q)
 if not re.search(r'^#slice\*\s+(\d+)',s,re.M):continue
 attempts.append({'directory':d.relative_to(R).as_posix(),'stage':'SYNTHESIS_ESTIMATE_NOT_FINAL_PNR',
  'slice_estimate':int(re.search(r'^#slice\*\s+(\d+)',s,re.M)[1]),
  'eram':int(re.search(r'^#eram\s+(\d+)',s,re.M)[1]),'dsp':int(re.search(r'^#dsp\s+(\d+)',s,re.M)[1])})
save(R/'reports/color_regions_resource_attempts.json',{'synthesis_attempts':attempts,'final_pnr':area,
 'notes':['Initial noncanonical multi-port run RAM expanded to flip-flops; replaced by canonical dual-port RAM.',
          'Two direct record write lanes plus a single-write spill FIFO preserved up to three EOL events.',
          'Fixed image-bank selection tree and non-reset metadata RAM replaced wide repeated register multiplexers.',
          'One background ROI datapath and four-bit validity avoid redundant parallel arithmetic/candidate copies.',
          'AWB and vendor interfaces unchanged; throughput always four pixels per capture clock.']})
report=R/'reports/LockingnTracking颜色区域功能版验证报告.md'
report.write_text(f'''# 颜色区域功能版验证报告（2026-10-13）

功能源码、软件回归、综合布局布线和同源bit核对通过，实物尚未验收。分支LockingnTracking，HEAD {m['head']}，改动尚未提交/推送。

构建：TD6.2.168116 / PH1P35MDG324 / -3；入口td_project/target_color_regions.al。最终尝试 `{m['attempt']}`，{len(m['inputs'])}项源码/厂家IP/约束输入逐文件SHA256与冻结ZIP一致。视频帧头修复、厂家MIPI/ISP/AWB/DDR及{len(m['protected_bits'])}份历史bit保护审计通过。工程明确排除老师大诊断面板、旧全局检测及尖端跟踪。

| 指标 | 原正常候选版 | 新功能版最终报告 |
|---|---:|---:|
| Slice / 21216 | 19105 | {area['Slice']} |
| LUT6 / 21216 | 17250 | {area['LUT6']} |
| 寄存器 / 42432 | 18733 | {area['Register']} |
| ERAM20K / 108 | 56 | {area['ERAM20K']} |
| DSP / 40 | 31 | {area['DSP']} |
| 建立余量SWNS(ns) | +0.117 | {tim['SWNS']:+.3f} |
| 保持余量HWNS(ns) | +0.020 | {tim['HWNS']:+.3f} |

时钟及例外约束沿用正常入口，未通过放宽约束或丢弃输入像素过关。STA覆盖{m['sta_coverage_percent']}%；{m['ignored_max_delay_constraints']}条最大延迟约束被例外忽略，不能解释为全部物理CDC已经证明。相机局部时钟布线警告见最终日志/时钟报告，实物时钟与连续采集仍需上板确认。

分类保持四像素/拍，四拍延迟；坐标/valid/配色/Session/帧身份同步延迟，公开采集帧号仍在原始SOF更新。灰度/高亮/二值属于显示页面，颜色身份来自相对色差和简化色相。检测掩码与显示掩码使用同一分类模块/参数，原图清晰度未为检测而模糊。

行程统计采用两条直接RAM写通道与8项单写单读溢出队列；只在行末可能出现的第三事件排队，不串行化四像素输入。行扫描实测最高203拍，截止288拍；共享帧后归并每色预算65536拍，512边/深度7压力实测17174拍；全图两色920格压力扫描53541拍，截止65536拍。两色归并和网格总预算196608拍加有限控制开销，小于满帧230400输入拍。截止/容量超限拒绝受影响结果；结果端忙时保持冻结银行，不能覆盖未消费数据。

独立黄金参考：有理数色相与逐像素8邻接搜索，未复制硬件行程标签规则。通过36116分类像素、36800行程组、10类行处理和14类归并；32/33行程、128/129标签、512边、实心/薄环/对角、局部范围公平排序、剪裁及密集负例。4完整720p粗网格帧逐格比较两色计数与独立ROI。

红蓝与黄紫各9完整静止帧，另外各9完整移动帧：不同尺寸A、暗色B、低饱和材料近似输入、28%填充薄环、三帧确认、移动范围更新、远处同色块独立框及消失清框。另11帧故障序列含9个完整长度帧、1短帧和1超长帧：故障、SOF同拍首像素、空拍、启停、切色/Session、64像素同帧平均RGB及恢复。合计47帧采集序列（45个完整长度帧）是合成RGB验证，不能当作打印纸或色环实物成功率。

416/451位实际异步邮箱、实际银行/帧号首行请求、迟到/空结果、停止、银行复用中止和中途复位联接通过。范围重叠、相邻、实际边缘、原子更新撞SOF、忙碌冻结、跳号/重复/回绕/96像素跳变及连续15显示帧过期清框通过。

原AWB→打包960字=DDR960字且内容/地址一致；三组异步时钟、实际厂家FIFO、完整172800字、DDR停顿/溢出/复位恢复通过。完整功能视频15组19帧、15175680源图像素检查四页/三倍率/停顿/图像切换；8完整OSD帧检查模式名、两配色、三倍率框映射、长按隐藏与顶部无面板。

完整帧标志检查像素数量与已接入的采集溢出故障，不是全面CSI包错误证明；无法单凭计数发现“丢一组、重复另一组”的数量相抵空间错误。未改动已修复的采集写入握手。

所有日志哈希、资源、输入、范围和接口在color_regions_build_manifest.json。初始无法推导行记录RAM的超容量综合、旧225900未收敛布线和073609布局前中止尝试均保留，不计为通过。最终bit SHA256 `{m['bit_sha256']}`。

使用限制：每色最多两个颜色区域，不认定唯一工具；不输出尖端、不自动移动显示窗口。同色物体实际接触属于同一连通区域，三个以上对象不保证工具进入两个槽。首版色域参数未经真实摄像头标定。请按docs/LockingnTracking颜色区域功能版上板.md进行清晰实体/打印和手机兼容验证，记录掉框、抖动、误框和视频异常。
''',encoding='utf-8')
# Build dependencies + precise generation/validation dependencies. Historical
# diagnostic HDL remains in the user's repository but is excluded from this ZIP.
sources=set(m['inputs'])|set(logs)|{'README.md',manifest.relative_to(R).as_posix(),report.relative_to(R).as_posix(),
 'docs/LockingnTracking颜色区域功能版上板.md','docs/color_regions_implementation_status.md',
 'reports/color_regions_hardware_record.csv','reports/color_regions_video_cases.json','reports/color_regions_resource_attempts.json',
 'scripts/generate_target.py','scripts/teacher_color_reference.py','scripts/test_robust_ingress.py',
 'scripts/target_osd_template.v.txt','scripts/build_target_lock_candidates_ingress.tcl',
 'td_project/target_lock_candidates_ingress.al','reports/target_generation_manifest.json',
 'reports/target_preview/glyphs.png','vendor_reference/lab3_osd/osd_char_lib.v',
 'sim/tb_scaling_video.sv','sim/tb_target_ingress_probe.sv','sim/tb_robust_ingress.sv','sim/fifo_model.sv',
 'reports/color_regions_baseline.json'}
sources|={q.relative_to(R).as_posix() for q in R.glob('scripts/*color_regions*') if q.is_file()}
sources|={q.relative_to(R).as_posix() for q in R.glob('sim/tb_color_regions*') if q.is_file()}
sources|={q.relative_to(R).as_posix() for q in (R/'rtl').rglob('*.v') if 'teacher_color_diag' not in q.parts}
sources|={q.relative_to(R).as_posix() for q in out.iterdir() if q.is_file()}
sources|={q.relative_to(R).as_posix() for q in R.glob('reports/color_regions_preview/*_zoom_*_pair_*.png')}
archive=out/'color_regions_source_snapshot.zip'
assert not archive.exists(),'Source package already exists; preserve it and use a new version for changes.'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
 for name in sorted(sources):z.write(R/name,name)
with zipfile.ZipFile(archive) as z:
 for name in sources:assert hashlib.sha256(z.read(name)).hexdigest()==sha(R/name)
delivery=dict(status=m['status'],branch=m['branch'],baseline_head=m['head'],ui_version='R1-01',
 bit_path=(out/'target_color_regions.bit').as_posix(),bit_sha256=m['bit_sha256'],
 source_snapshot=archive.as_posix(),source_snapshot_sha256=sha(archive),resources=area,timing_ns=tim,
 instructions=(R/'docs/LockingnTracking颜色区域功能版上板.md').as_posix(),
 report=report.as_posix(),hardware_record=(R/'reports/color_regions_hardware_record.csv').as_posix(),
 source_files=len(sources),build_inputs=len(m['inputs']),hardware='NOT TESTED',git=m['git'])
save(R/'reports/color_regions_delivery.json',delivery)
print('FUNCTIONAL_COLOR_REGIONS_DELIVERY_READY',m['bit_sha256'],flush=True)
