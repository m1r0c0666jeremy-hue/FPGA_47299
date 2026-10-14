"""Unique audited test bit, exact compiled inputs and reviewable source package."""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil,zipfile,subprocess
from audit_stable_regions import audit
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p,obj):
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
args=argparse.ArgumentParser();args.add_argument('--attempt',required=True)
args.add_argument('--previous-delivery',help='Preserve an interrupted package and publish to a new directory')
a=args.parse_args()
attempt=(R/a.attempt).resolve();obj=audit(attempt,True)
assert obj['branch']=='feature/transparent-ring-stability'
previous=None
if a.previous_delivery:
 previous_path=(R/a.previous_delivery).resolve()
 assert previous_path.is_relative_to(R/'build')
 previous=json.loads((previous_path/'delivery.json').read_text(encoding='utf-8'))
 assert sha(R/previous['bit'])==previous['bit_sha256']==obj['bit_sha256']
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
dest=R/'build'/f'target_color_regions_ring_stability_{stamp}';dest.mkdir(exist_ok=False)
bit=dest/'target_color_regions.bit';shutil.copy2(attempt/bit.name,bit);assert sha(bit)==obj['bit_sha256']
for name in ('target_color_regions_phy.area','target_color_regions_phy.ts','target_color_regions_pr.timing','target_color_regions_exception.timing','target_color_regions_clocks.txt','inputs.json','inputs_after.json','run.tcl'):
 shutil.copy2(attempt/name,dest/name)
shutil.copy2(attempt/'source_snapshot.zip',dest/'compiled_source_snapshot.zip')
shutil.copy2(R/'reports'/(attempt.name+'.log'),dest/'td_build.log')
obj.update(status='TEST_SOFTWARE_AND_BUILD_PASSED_HARDWARE_PENDING',archive_name='透明色环稳定性优化：判色、候选质量与显示调整',
 delivery_directory=dest.relative_to(R).as_posix(),bit=bit.relative_to(R).as_posix(),hardware='PENDING; no board or Flash write',
 guide='docs/透明色环稳定性优化_上板与复测.md',validation='reports/transparent_ring/最终验证报告.md')
report=R/obj['validation'];assert report.is_file()
text=report.read_text(encoding='utf-8')
assert '<!-- BUILD_RESULT -->' in text or previous is not None
block=f'''TD最终完整构建通过：{obj['input_count']}项编译输入前后哈希相同。

| 项目 | 实际最终结果 |
|---|---|
| Slice/LUT6/寄存器 | {obj['resources']['Slice']}/21216 / {obj['resources']['LUT6']}/21216 / {obj['resources']['Register']}/42432 |
| ERAM/DSP | {obj['resources']['ERAM20K']}/108 / {obj['resources']['DSP']}/40 |
| 建立/保持最差余量 | {obj['timing_ns']['SWNS']:+.3f}ns / {obj['timing_ns']['HWNS']:+.3f}ns |
| STA覆盖率 | {obj['sta_coverage_percent']:.2f}% |
| 原最大延迟例外忽略 | {obj['ignored_max_delay_constraints']}条 |
| 实物 | 待验 |

新独立测试bit：`{obj['bit']}`，SHA256 `{obj['bit_sha256']}`。

冻结目录：`{attempt.relative_to(R).as_posix()}`。ADC/SDC及历史bit/ZIP保护核对通过；没有放宽约束。工具通过不等同于完整物理CDC/相机时钟验证或实体材料识别成功。
'''
if previous:
 assert previous['bit'] in text
 text=text.replace(previous['bit'],obj['bit'])
 obj['previous_interrupted_delivery']=previous['delivery_directory']
else:text=text.replace('<!-- BUILD_RESULT -->',block)
report.write_bytes(text.encode('utf-8'))
readme=R/'README.md';old=readme.read_text(encoding='utf-8')
marker='## 当前正式工程：'
assert marker in old
intro=f'''## 当前分支：透明色环稳定性优化（2026-10-15）

`feature/transparent-ring-stability`，基线43564ee；在独立工作区实施四步材料/背景校准、候选质量、v3同帧诊断、官方图标、组合键和默认180°显示，保留双色工具/尖端/跟随。软件与TD通过，实物待验。

[新独立上板测试bit]({obj['bit']})、[同源源码包]({(dest/'transparent_ring_stability_source.zip').relative_to(R).as_posix()})、[操作与最小复测](docs/透明色环稳定性优化_上板与复测.md)、[实际验证报告](reports/transparent_ring/最终验证报告.md)。历史bit和下方历史说明保留，不能用旧bit执行四步流程。

本版实际Slice18981/21216、ERAM100/108、DSP40/40，建立+0.110ns/保持+0.020ns。新输出独立且输入冻结，未放宽约束。完整构建用 `scripts/run_stable_regions_build.py --stage full --prefix ring_stability`；只读审计用 `scripts/audit_color_regions.py --attempt build/ring_stability_full_20261015_014510 --check-build`。不要直接重跑冻结目录run.tcl覆盖历史输出。

'''
if previous:
 assert previous['bit'] in old and previous['source_zip'] in old
 old=old.replace(previous['bit'],obj['bit']).replace(previous['source_zip'],(dest/'transparent_ring_stability_source.zip').relative_to(R).as_posix())
else:old=old.replace(marker,intro+marker,1)
readme.write_bytes(old.encode('utf-8'))
record(dest/'build_manifest.json',obj)
# Use exact compile inputs plus source/scripts/benches/evidence; exclude every
# historical bit, arbitrary build cache and failed attempt from the source ZIP.
paths={R/n for n in json.loads((attempt/'inputs.json').read_text(encoding='utf-8'))}
for folder,exts in [('scripts',{'.py','.tcl','.txt'}),('sim',{'.v','.sv','.json'}),('rtl',{'.v','.json'})]:
 paths|={p for p in (R/folder).rglob('*') if p.is_file() and p.suffix in exts}
paths|={p for p in (R/'reports/transparent_ring').rglob('*') if p.is_file() and p.suffix in ('.md','.log','.json','.csv','.png') and not p.name.startswith('delivery_')}
paths|={p for p in (R/'docs').glob('透明色环*.md')}
paths|={p for p in (R/'assets/osd/anlogic').iterdir() if p.is_file()}
paths|={R/'README.md'}
paths|={p for p in (R/'build/sim').rglob('*.sv') if ('stable_' in str(p.relative_to(R)) or 'ring_' in str(p.relative_to(R)))}
manifest={p.relative_to(R).as_posix():sha(p) for p in sorted(paths)}
archive=dest/'transparent_ring_stability_source.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(paths):z.write(p,p.relative_to(R))
 z.writestr('SOURCE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(manifest)|{'SOURCE_MANIFEST.json'}
 for name,h in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==h,name
compiled=json.loads((attempt/'inputs.json').read_text(encoding='utf-8'))
assert all(manifest[n]==h for n,h in compiled.items()),'Source archive is not same-source'
shutil.copy2(report,dest/'验证报告.md');shutil.copy2(R/obj['guide'],dest/'上板操作.md')
obj.update(source_zip=archive.relative_to(R).as_posix(),source_zip_sha256=sha(archive),source_files=manifest,
 outputs={p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file()})
record(dest/'delivery.json',obj);record(R/'reports/transparent_ring'/f'delivery_{stamp}.json',obj)
with (dest/'SHA256SUMS.txt').open('x',encoding='utf-8') as f:
 for p in sorted(dest.iterdir()):
  if p.is_file() and p.name!='SHA256SUMS.txt':f.write(f'{sha(p)}  {p.name}\n')
print('RING_DELIVERY_PASS',dest,obj['bit_sha256'],'source_files',len(manifest),flush=True)
