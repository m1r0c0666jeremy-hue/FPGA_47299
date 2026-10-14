"""Create a new blank board record; never infer a result from simulation."""
from pathlib import Path
import csv
R=Path(__file__).resolve().parents[1];p=R/'reports/transparent_ring/hardware_retest.csv'
fields=['场景','配色','次数','待验状态','bit_SHA256','相机增益','光照','材料','背景','校准成功','图像帧F','参数版本V','A原始','A过滤','A候选N','A支持Q','A选槽S','A阶段F','B原始','B过滤','B候选N','B支持Q','B选槽S','B阶段F','依据P','拒绝R','确认C','丢失L','误框或误尖端','首次锁定帧数','静止抖动','遮挡恢复是否同工具','照片视频路径','备注']
assert not p.exists(),'Board record already exists; preserve it'
rows=[]
for scene,pair in [('p1金属尖端','红蓝'),('p12纸面文字','红蓝'),('p2黑背景','黄紫'),('p3黑背景','黄紫'),('p5PCB紫噪声','黄紫'),('p6PCB紫噪声','黄紫'),('p11假黄色','黄紫'),('p8成功样例','红蓝'),('p10成功样例','红蓝'),('p13成功样例','红蓝')]:
 for trial in range(1,4):rows.append(dict(zip(fields[:4],[scene,pair,trial,'待验'])))
for pair in ('红蓝','黄紫'):
 for scene in ('黑笔管透明环重校准/静止/移动','黑台面空场60秒','白纸空场60秒','PCB空场60秒','短暂缺色/恢复','超过15采集帧/回中央重选'):
  rows.append(dict(zip(fields[:4],[scene,pair,1,'待验'])))
with p.open('x',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print('RING_BOARD_RECORD_CREATED',len(rows),'PENDING rows')
