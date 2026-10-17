"""Publish only a passing, same-source test bit into a new timestamp directory."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,shutil,zipfile
from audit_refined import audit,R

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def record(path,data):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')

ap=argparse.ArgumentParser();ap.add_argument('--attempt',required=True);args=ap.parse_args()
obj=audit(args.attempt,True)
attempt=R/obj['build']['attempt']
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
dest=R/'build'/f'target_color_regions_refined_{stamp}';dest.mkdir(exist_ok=False)
bit=dest/'target_color_regions.bit';shutil.copy2(attempt/bit.name,bit)
assert sha(bit)==obj['build']['bit_sha256']
for name in ('target_color_regions_phy.area','target_color_regions_phy.ts','target_color_regions_pr.timing','target_color_regions_exception.timing','target_color_regions_clocks.txt','inputs.json','inputs_after.json','source_context.json','run.tcl','summary.json'):
    shutil.copy2(attempt/name,dest/name)
for name in ('official_strategy_ph1.json','official_strategy_context.json'):
    if (attempt/name).is_file():shutil.copy2(attempt/name,dest/name)
checkpoint=obj['build']['summary'].get('checkpoint_provenance')
if checkpoint:
    for name in ('checkpoint_provenance.json','placed_clocks.txt','placed_exceptions.timing'):
        shutil.copy2(attempt/name,dest/name)
shutil.copy2(attempt/'td.log',dest/'td_build.log')
shutil.copy2(attempt/'compiled_inputs.zip',dest/'compiled_source_snapshot.zip')
obj.update(status='TEST_SOFTWARE_AND_BUILD_PASSED_HARDWARE_PENDING',archive_name='颜色识别、视频稳定性与显示功能改进',delivery_directory=dest.relative_to(R).as_posix(),bit=bit.relative_to(R).as_posix(),bit_sha256=sha(bit),hardware='PENDING; no board download or Flash write',guide='docs/颜色视频显示改进_上板一页.md',validation='reports/refined/最终验证报告.md')
report=R/obj['validation'];originals={report:report.read_bytes()};updates={};text=originals[report].decode('utf-8')
pending_status='**当前状态：139项软件验证已通过，TD完整构建仍在进行，暂无新bit/同源ZIP，实物全部待验。**'
assert pending_status in text,'Review the current report status before publication'
text=text.replace(pending_status,f'**当前状态：{len(obj["regression"])}项软件验证及完整TD构建通过，实物待验。**')
assert '<!-- BUILD_RESULT -->' in text,'Report already published; preserve it and use a new reviewed report'
assert '<!-- STORE_RESULT -->' not in text,'Complete the actual new-selector live verification report first'
assert '<!-- FINAL_SOFTWARE_RESULT -->' in text
text=text.replace('<!-- FINAL_SOFTWARE_RESULT -->',f'最终只读审计核对{len(obj["regression"])}项与当前源码哈希一致的通过记录。包含625行帧尾提示、原11状态及两种中止边界、正式OSD四组完整联接20帧、80组合图像矩阵。失败和未采用原型不计入通过数量。完整逐项记录与日志哈希见交付audit.json；实物结果均待验。')
b=obj['build'];s=b['summary'];r=s['resources'];t=s['slack_ns']
flow_args=['--stage','full','--map-mode',s.get('map_mode','auto'),'--pack-effort',s.get('pack_effort','medium'),'--strategy',str(s.get('placement_strategy',1)),'--route-effort',s.get('route_effort','normal')]
for key,flag in [('macro_performance','--macro-performance'),('map_strategy','--map-strategy'),('infer_fsm','--infer-fsm'),('pack_mode','--pack-mode'),('place_effort','--place-effort'),('max_fanout','--max-fanout')]:
    if s.get(key) is not None and s.get(key)!='project':flow_args += [flag,str(s[key])]
if s.get('official_strategy'):
    for name,definition in s['official_strategy']['selected'].items():
        flow_args += ['--official-syn' if definition['is_syn']=='syn' else '--official-phy',name]
    flow_args += ['--official-strategy-file',b['attempt']+'/official_strategy_ph1.json']
recipe='scripts/run_refined_build.py '+' '.join(flow_args)
checkpoint_note=''
if checkpoint:
    recipe=f'scripts/run_refined_route.py --parent {checkpoint["parent"]} --route-effort {s["route_effort"]}'
    checkpoint_note=f'\n本次完整流程分为：`{checkpoint["parent"]}`完成综合/布局，本目录从其SHA256验证的布局检查点继续布线/时序/bitgen。导入前后时钟及例外报告一致，全部冻结源文件与原提交一致；不是跳过综合或放宽约束。检查点SHA256 `{checkpoint["checkpoint_sha256"]}`。\n'
block=f'''完整TD构建通过，{b['frozen_inputs']}项编译输入冻结后逐项一致。

| 项目 | 最终实际结果 |
|---|---|
| Slice / LUT6 / 寄存器 | {r['slice']}/21216 / {r['lut6']}/21216 / {r['reg']}/42432 |
| ERAM / DSP | {r['eram']}/108 / {r['dsp']}/40 |
| 建立 / 保持最差余量 | {t['SWNS']:+.3f}ns / {t['HWNS']:+.3f}ns |
| STA覆盖率 | {b['sta_coverage_percent']:.2f}% |
| 被忽略的最大延迟例外 | {b['ignored_max_delay_constraints']}条 |

测试bit：`{obj['bit']}`，SHA256 `{obj['bit_sha256']}`。

独立尝试：`{b['attempt']}`。原ADC/SDC未放宽；原时钟和例外限制保留，不能解释为完整物理验证。实物全部待验。

编译源码提交：`{b['compiled_source_commit']}`，{b['git_blob_inputs_verified']}项编译输入与该提交的Git原始文件逐字节相同。
{checkpoint_note}

复现需使用实际通过的工具设置：`{recipe}`。脚本调用TD并创建新的时间戳目录；不要直接重跑历史目录的run.tcl，以免覆盖已交付证据。新.al为功能工程入口，完整工具参数以本次run.tcl及summary.json为准。
'''
updates[report]=text.replace('<!-- BUILD_RESULT -->',block).encode('utf-8')
guide=R/obj['guide'];originals[guide]=guide.read_bytes();text=originals[guide].decode('utf-8')
marker='**构建尚未完成。烧录文件和哈希以后续正式交付清单为准。实物项目均待验。**'
assert marker in text
updates[guide]=text.replace(marker,f'**软件与TD构建通过，实物待验。**\n\n测试bit：`{bit.as_posix()}`\n\nSHA256：`{obj["bit_sha256"]}`').encode('utf-8')
readme=R/'README.md';originals[readme]=readme.read_bytes();text=originals[readme].decode('utf-8')
marker='<!-- REFINED_DELIVERY -->\n完整构建和最终交付正在进行，目前不要将中间尝试作为上板版本。'
assert marker in text
updates[readme]=text.replace(marker,f'软件与完整TD构建通过，实物待验。[独立测试bit]({obj["bit"]})、[同源源码包]({(dest/"color_video_refined_source.zip").relative_to(R).as_posix()})。建立{t["SWNS"]:+.3f}ns，保持{t["HWNS"]:+.3f}ns；ERAM{r["eram"]}/108，DSP{r["dsp"]}/40。').encode('utf-8')
record(dest/'audit.json',obj)
# The exact compiler inputs are mandatory; additional sources and evidence make
# the tests reviewable without packing historical bits or arbitrary caches.
compiled=json.loads((attempt/'inputs.json').read_text(encoding='utf-8'))
paths={R/name for name in compiled}
if checkpoint:
    parent=R/checkpoint['parent'];paths.add(attempt/checkpoint['checkpoint_name'])
    paths.add(attempt/'checkpoint_provenance.json')
    for name in ('summary.json','source_context.json','inputs.json','inputs_after.json','flow_options.json','run.tcl','td.log','target_color_regions_gate.area','target_color_regions_phy.area','placed_clocks.txt','placed_exceptions.timing','official_strategy_ph1.json','official_strategy_context.json',checkpoint['checkpoint_name']):
        if (parent/name).is_file():paths.add(parent/name)
    paths|={parent/'compiled_source'/name for name in compiled}
for name in ('official_strategy_ph1.json','official_strategy_context.json'):
    if (attempt/name).is_file():paths.add(attempt/name)
# Preserve the generator's implementation-start project and the later UI save.
# Neither replaces the user's project or enters the new compilation.
protection=json.loads((R/'reports/refined/protected_inputs.json').read_text(encoding='utf-8'))
observed=json.loads((R/'reports/refined/user_project_change_20261017.json').read_text(encoding='utf-8'))
paths.add(R/protection['backup']/'sources_before.zip')
paths.add(R/observed['preserved_copy'])
for folder,exts in [('scripts',{'.py','.tcl','.txt'}),('sim',{'.sv','.v','.json'}),('rtl',{'.v','.json'})]:
    paths|={p for p in (R/folder).rglob('*') if p.is_file() and p.suffix in exts}
paths|={p for p in (R/'reports/refined').rglob('*') if p.is_file() and p.suffix in {'.md','.log','.json','.csv','.png'} and not p.name.startswith('delivery_') and not (p.parent.name=='regression' and p.suffix=='.log' and not p.with_suffix('.json').is_file())}
paths|={p for p in (R/'docs').glob('颜色视频显示改进*.md')}
paths|={p for p in (R/'assets/osd/anlogic').iterdir() if p.is_file()}
paths.add(readme)
for record_path in (R/'reports/refined/regression').glob('*.json'):
    entry=json.loads(record_path.read_text(encoding='utf-8-sig'))
    if entry.get('output'):
        tb=Path(entry['output'])/'tb.sv'
        if tb.is_file():paths.add(tb)
    paths|={R/name for name in entry.get('inputs',{}) if (R/name).is_file()}
# Full video oracle files referenced by the generated benches.
paths|={p for p in (R/'build/sim').glob('refined_video*/*.hex') if p.is_file()}
# Preserve the explicit expectation files used by the archived benches as well
# as the generators, rather than leaving only absolute readmemh references.
for bench in list(paths):
    if bench.name!='tb.sv':continue
    for name in re.findall(r'\$readmem[hb]\s*\(\s*"([^"]+)"',bench.read_text(encoding='utf-8-sig')):
        p=Path(name);p=(p if p.is_absolute() else R/p).resolve()
        if p.is_relative_to(R/'build/sim') and p.is_file():paths.add(p)
manifest={p.relative_to(R).as_posix():hashlib.sha256(updates[p]).hexdigest() if p in updates else sha(p) for p in sorted(paths)}
assert all(manifest[n]==h for n,h in compiled.items())
archive=dest/'color_video_refined_source.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(paths):
        if p in updates:z.writestr(p.relative_to(R).as_posix(),updates[p])
        else:z.write(p,p.relative_to(R).as_posix())
    z.writestr('SOURCE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())==set(manifest)|{'SOURCE_MANIFEST.json'}
    for n,h in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
record(dest/'source_files.json',manifest)
(dest/'验证报告.md').write_bytes(updates[report]);(dest/'上板一页.md').write_bytes(updates[guide])
obj.update(source_zip=archive.relative_to(R).as_posix(),source_zip_sha256=sha(archive),source_files=manifest,outputs={p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file()})
record(dest/'delivery.json',obj);record(R/'reports/refined'/f'delivery_{stamp}.json',obj)
with (dest/'SHA256SUMS.txt').open('x',encoding='utf-8',newline='\n') as f:
    for p in sorted(dest.iterdir()):
        if p.is_file() and p.name!='SHA256SUMS.txt':f.write(f'{sha(p)}  {p.name}\n')
# Publish local pointers only after the bit, source ZIP and every checksum have
# been written and verified. A failed archive leaves the pending instructions.
assert all(p.read_bytes()==data for p,data in originals.items()),'Documentation changed during packaging'
for p,data in updates.items():p.write_bytes(data)
print('REFINED_DELIVERY_PASS',dest,'files',len(manifest),'bit',obj['bit_sha256'],flush=True)
