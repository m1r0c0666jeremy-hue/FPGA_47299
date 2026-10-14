"""Production fixed AWB + gap-safe packer + preserved writer, actual vendor FIFO."""
from pathlib import Path
import subprocess,os
R=Path(__file__).resolve().parents[1];O=R/'build/sim/stable_ingress';O.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','');logs=[]
def run(cmd):
    q=subprocess.run(list(map(str,cmd)),cwd=R,env=env,capture_output=True,text=True,timeout=900)
    logs.append(q.stdout+q.stderr);print(logs[-1],flush=True)
    (R/'reports/transparent_ring/regression/stable_ingress.log').write_text('\n'.join(logs),encoding='utf-8')
    if q.returncode:raise SystemExit(q.returncode)
s=(R/'sim/tb_target_ingress_probe.sv').read_text(encoding='utf-8')
s=s[:s.index('module divider')]
s=s.replace('tb_target_ingress_probe','tb_stable_ingress')
s=s.replace("awb #(.IMG_WIDTH(1280),.IMG_HEIGHT(4)) isp(cc,rst,1'b0,sof,rgb,valid,,al,asf,ar,av,1'b1);",
            "stable_awb isp(cc,rst,1'b0,sof,valid,rgb,12'd1536,12'd2048,al,asf,av,ar);")
s=s.replace('data_96bit_to_128bit packer','stable_packer packer')
s=s.replace('integer cycle=0','reg [127:0] expected[0:172799];integer j;\n integer cycle=0')
s=s.replace('words=words+1;', 'expected[words]=pr;words=words+1;')
s=s.replace('always @(posedge dc)if(rst&&wr)dd=dd+1;', '''always @(posedge dc)if(rst&&wr)begin
 if(dd>=words || data!==expected[dd] || addr!==dd*8)$fatal(1,"production DDR payload/address beat%0d",dd);
 for(j=0;j<16;j=j+1)if(data[127-j*8-:8]!==((dd*16+j)%3==0?8'hc0:8'h40))$fatal(1,"production AWB numeric byte %0d",dd*16+j);
 dd=dd+1;end
 always @(posedge cc)if(rst && writer.fifo_push && writer.S_fifo_rst)$fatal(1,"push during reset");''')
s=s.replace('$finish;', 'if(words!=EXPECTED || dd!=EXPECTED || overflow)$fatal(1,"production frame-head/count");$display("STABLE_INGRESS_PASS exact fixed-WB/packer/writer %0d words",dd);$finish;')
vendor=[R/'user_source/ip_source/w128_d512_fifo/w128_d512_fifo.v',R/'user_source/ip_source/w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v']
for full in (False,True):
    expected=172800 if full else 960
    src=s.replace('module tb_stable_ingress;',f'module tb_stable_ingress;localparam EXPECTED={expected};')
    if full:src=src.replace('y<4','y<720')
    bench=O/f'awb_pack_{expected}.sv';bench.write_text(src,encoding='utf-8')
    files=[bench,R/'rtl/color_regions/stable_awb.v',R/'rtl/color_regions/stable_packer.v',R/'user_source/hdl_source/video_in.v',*vendor]
    exe=O/f'awb_pack_{expected}.vvp'
    run([iv,'-g2012','-s','tb_stable_ingress','-o',exe,*files]);run([iv.with_name('vvp.exe'),exe])
for cp,dp in [(8,7),(5,11),(11,5)]:
    exe=O/f'writer_vendor_{cp}_{dp}.vvp'
    run([iv,'-g2012','-s','tb_robust_ingress',f'-Ptb_robust_ingress.CP={cp}',f'-Ptb_robust_ingress.DP={dp}',
         '-o',exe,R/'sim/tb_robust_ingress.sv',*vendor,R/'user_source/hdl_source/video_in.v',R/'rtl/04_tracking/target_frame_store.v'])
    run([iv.with_name('vvp.exe'),exe])
print('STABLE_INGRESS_ALL_PASS',flush=True)
