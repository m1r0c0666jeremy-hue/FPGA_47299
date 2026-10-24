"""Compare actual OSD raster output with independently composed reference strings/pixels."""
from pathlib import Path
import json,os,re,subprocess
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[1];out=root/'build/sim/scaling_test';out.mkdir(parents=True,exist_ok=True)
bin=root/'tools/iverilog/ucrt64/bin';env=os.environ.copy();env['PATH']=str(bin)+os.pathsep+env.get('PATH','')
files=['sim/tb_scaling_osd.sv',*[f'rtl/09_osd_ui/{n}.v' for n in ['scaling_osd','scaling_glyph_rom','scaling_logo_rom']]]
subprocess.run([str(bin/'iverilog.exe'),'-g2012','-s','tb_scaling_osd','-o',str(out/'osd.vvp'),*files],cwd=root,env=env,check=True)
c=subprocess.run([str(bin/'vvp.exe'),str(out/'osd.vvp'),f'+OUT={out.as_posix()}'],cwd=root,env=env,capture_output=True,text=True,timeout=300)
print(c.stdout+c.stderr);assert c.returncode==0
font=np.zeros((2048,24),dtype=bool)
for row,bits in re.findall(r"mem\[(\d+)\]=24'h([0-9a-f]+)",(root/'rtl/09_osd_ui/scaling_glyph_rom.v').read_text()):
 font[int(row)]=[(int(bits,16)>>(23-x))&1 for x in range(24)]
chars=json.loads((root/'assets/osd/anlogic/scaling_rom_manifest.json').read_text(encoding='utf-8'))['characters']
logo=np.array(Image.open(root/'assets/osd/anlogic/anlogic_symbol_96x62.png').convert('RGBA'))
palette=np.where((logo[:,:,0].astype(float)>logo[:,:,1]*1.4)[:,:,None],np.array([237,27,35]),np.array([28,44,78]))
cases=[(0,0,0,0,0,0,0,0,1),(1279,719,1279,623,1,1,1,1,1),(1279,0,1278,2,2,2,2,2,1),(0,719,2,622,2,3,3,3,1),(640,360,640,312,0,0,0,0,0),(640,360,640,312,0,0,1,0,1)]
yy,xx=np.indices((720,1280));checks=[]
for i,(cx,cy,sx,sy,z,m,d,s,ok) in enumerate(cases):
 im=np.full((720,1280,3),[64,128,160] if ok else [0,0,0],dtype=np.uint8)
 dx=abs(xx-sx);dy=abs(yy-sy)
 black=(((dx>=2)&(dx<=13)&(dy<=2))|((dy>=2)&(dy<=13)&(dx<=2)))&(yy<624)
 yellow=(((dx>=3)&(dx<=12)&(dy<=1))|((dy>=3)&(dy<=12)&(dx<=1)))&(yy<624)
 im[black]=0;im[yellow]=[255,255,0];im[624:]=[16,32,48];im[632:712,1024:1264]=255
 area=im[641:703,1032:1128];opaque=logo[:,:,3]>=128;area[opaque]=palette[opaque]
 def text(x,y,s,color=(255,255,255)):
  for k,ch in enumerate(s):
   mask=font[chars.index(ch)*24:chars.index(ch)*24+24]
   im[y:y+24,x+k*24:x+(k+1)*24][mask]=color
 text(16,636,f'模式：{["原图","边缘","灰度","二值化"][m]:<3} 坐标：({cx:04d},{cy:04d}) 倍率：{1<<z}倍')
 text(16,680,f'KEY3方向：{"下右左上"[d]} 状态：{["待命","移动","到边界","按键冲突","视频未就绪"][s if ok else 4]}')
 text(1144,660,'安路科技',(28,44,78))
 actual=np.array(Image.open(out/f'osd_{i}.ppm'))
 mismatch=np.any(actual!=im,axis=2)
 if mismatch.any():
  y,x=np.argwhere(mismatch)[0];raise AssertionError(f'OSD case {i}: {mismatch.sum()} pixel differences; first ({x},{y}) actual {actual[y,x]} expected {im[y,x]}')
 Image.fromarray(actual).save(out/f'osd_{i}.png')
 checks.append(f'PASS OSD case {i}: 921600 pixels; mode={m} coordinate=({cx},{cy}) zoom={1<<z} direction={d} status={s if ok else 4}')
result=c.stdout+'\n'+'\n'.join(checks)+'\n';print(result)
(root/'reports/scaling_osd_simulation.log').write_text(result,encoding='utf-8')
