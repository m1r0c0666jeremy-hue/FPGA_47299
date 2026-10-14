"""Create empty hardware records once; never replace measurements."""
from pathlib import Path
import csv,itertools
R=Path(__file__).resolve().parents[1]
combinations=list(itertools.product(['实体工具色环','平放色环','打印标记'],['黑台面','白纸','绿色PCB'],['红蓝','黄紫']))
p=R/'reports/stable_regions_hardware_trials.csv'
if not p.exists():
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['材料','背景','配色','次数','状态','选取成功','首次锁定采集帧数','失败原因','bit_SHA256','相机增益','照明','日期','视频文件'])
        for c in combinations:
            for n in range(1,11):w.writerow([*c,n,'待验',*['']*8])
p=R/'reports/stable_regions_hardware_metrics.csv'
if not p.exists():
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['材料','背景','配色','状态','十次成功数','最大首次锁定采集帧数','静止10秒尖端峰峰源像素','静止10秒窗口峰峰源像素','平面K0.5尖端误差源像素','无工具60秒有效尖端次数','遮挡停窗','恢复同一工具','bit_SHA256','板卡相机','相机增益','照明','日期','视频文件','备注'])
        for c in combinations:w.writerow([*c,'待验',*['']*15])
print('STABLE_HARDWARE_RECORDS_READY 180 unmeasured trials, 18 unmeasured metric rows')
