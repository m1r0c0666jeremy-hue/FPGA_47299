"""Reproduce the unchanged upstream FIFO reset problem; failure is evidence,
not an acceptance pass. Does not modify RTL or relax full-frame checks.
"""
from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parents[1];out=r/'build/sim/target_lock';out.mkdir(parents=True,exist_ok=True)
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
files=['sim/tb_target_ingress_probe.sv','sim/fifo_model.sv','user_source/hdl_source/isp/awb/awb.v','user_source/hdl_source/isp/awb/signal_delay.v','user_source/hdl_source/isp/data96_128/data96_128.v','user_source/hdl_source/video_in.v']
c=subprocess.run(list(map(str,[iv,'-g2012','-s','tb_target_ingress_probe','-o',out/'probe.vvp',*files])),cwd=r,env=env,capture_output=True,text=True)
assert c.returncode==0,c.stdout+c.stderr
p=subprocess.run([str(iv.with_name('vvp.exe')),str(out/'probe.vvp')],cwd=r,env=env,capture_output=True,text=True,timeout=60)
text=p.stdout+p.stderr
(r/'reports/target_ingress_probe.log').write_text(text,encoding='utf-8')
print(text)
assert p.returncode==0
assert 'packed_words=960 DDR_writes=720 expected=960' in text,'Probe behavior changed: investigate; do not silently change expected count'
print('KNOWN_INGRESS_FAILURE_REPRODUCED (NOT AN ACCEPTANCE PASS)')
