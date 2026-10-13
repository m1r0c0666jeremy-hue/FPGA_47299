"""AWB timing -> packer -> real writer; exact data/address checks, not count only."""
from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parents[1];out=r/'build/sim/robust';out.mkdir(parents=True,exist_ok=True)
iv=r/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
logs=[]
def run(cmd):
 p=subprocess.run(list(map(str,cmd)),cwd=r,env=env,capture_output=True,text=True,timeout=180)
 logs.append(p.stdout+p.stderr);print(logs[-1],flush=True)
 (r/'reports/robust_ingress.log').write_text('\n'.join(logs),encoding='utf-8')
 assert p.returncode==0
src=(r/'sim/tb_target_ingress_probe.sv').read_text(encoding='utf-8').replace('tb_target_ingress_probe','tb_robust_awb')
src=src.replace('integer cycle=0', 'reg [127:0] expected[0:959];\n integer cycle=0')
src=src.replace('words=words+1;', 'expected[words]=pr;words=words+1;')
src=src.replace('always @(posedge dc)if(rst&&wr)dd=dd+1;', '''always @(posedge dc)if(rst&&wr)begin
 if(dd>=words || data!==expected[dd] || addr!==dd*8) $fatal(1,"AWB order/address mismatch beat=%0d addr=%0d",dd,addr);
 dd=dd+1;
 end
 always @(posedge cc) if(rst && writer.fifo_push && writer.S_fifo_rst) $fatal(1,"write during FIFO reset");''')
src=src.replace('$finish;', 'if(words!=960 || dd!=960 || overflow) $fatal(1,"frame-head loss"); $display("PASS AWB 960 packed = 960 DDR, all data/addresses matched"); $finish;')
bench=out/'tb_robust_awb.sv';bench.write_text(src,encoding='utf-8')
files=[bench,'sim/fifo_model.sv','user_source/hdl_source/isp/awb/awb.v','user_source/hdl_source/isp/awb/signal_delay.v','user_source/hdl_source/isp/data96_128/data96_128.v','user_source/hdl_source/video_in.v']
run([iv,'-g2012','-s','tb_robust_awb','-o',out/'awb.vvp',*files]);run([iv.with_name('vvp.exe'),out/'awb.vvp'])
for cp,dp in [(8,7),(5,11),(11,5)]:
 exe=out/f'writer_{cp}_{dp}.vvp'
 run([iv,'-g2012','-s','tb_robust_ingress',f'-Ptb_robust_ingress.CP={cp}',f'-Ptb_robust_ingress.DP={dp}','-o',exe,'sim/tb_robust_ingress.sv','sim/fifo_model.sv','user_source/hdl_source/video_in.v','rtl/04_tracking/target_frame_store.v'])
 run([iv.with_name('vvp.exe'),exe])
vendor=['user_source/ip_source/w128_d512_fifo/w128_d512_fifo.v','user_source/ip_source/w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v']
logs.append('VENDOR_FIFO_RTL: actual Gray-pointer/reset/flag/RAM-inference implementation, no physical timing model')
run([iv,'-g2012','-s','tb_robust_awb','-o',out/'awb_vendor.vvp',*[f for f in files if f!='sim/fifo_model.sv'],*vendor]);run([iv.with_name('vvp.exe'),out/'awb_vendor.vvp'])
for cp,dp in [(8,7),(5,11),(11,5)]:
 exe=out/f'writer_vendor_{cp}_{dp}.vvp'
 run([iv,'-g2012','-s','tb_robust_ingress',f'-Ptb_robust_ingress.CP={cp}',f'-Ptb_robust_ingress.DP={dp}','-o',exe,'sim/tb_robust_ingress.sv',*vendor,'user_source/hdl_source/video_in.v','rtl/04_tracking/target_frame_store.v'])
 run([iv.with_name('vvp.exe'),exe])
print('ROBUST_INGRESS_PASSED')
