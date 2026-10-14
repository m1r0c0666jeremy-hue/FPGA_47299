"""Independent distribution fixtures; acquisition is covered separately."""
from pathlib import Path
import colorsys,subprocess,argparse,json
from test_ring_calibration import R,O,P,run
def hsv(h):return tuple(round(v*255) for v in colorsys.hsv_to_rgb(h/360,.75,.65))
def packed(a):return '\n'.join(''.join('%02x%02x%02x'%tuple(p) for p in a[i:i+4]) for i in range(0,2048,4))
def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',action='store_true');a=p.parse_args()
    module=R/'rtl/color_regions/stable_calibration.v'
    if a.baseline:
        module=R/'sim/ring_baseline/stable_calibration.v'
    cases=[]
    broad=[hsv(180+i%40) if i<205 else hsv(260) for f in range(8) for i in range(256)]
    polluted=[hsv(210) if f<5 or i<16 else hsv(290) for f in range(8) for i in range(256)]
    target=[(40,80,120)]*2048
    cases.append(('broad_cluster',broad,[(20,20,20)]*2048,not a.baseline))
    cases.append(('polluted_frames',polluted,[(20,20,20)]*2048,a.baseline))
    cases.append(('dark_blue_background',target,[(0,30,60)]*2048,True))
    if not a.baseline:cases.append(('inseparable_background',target,target,False))
    for name,pixels,bg,success in cases:
        (O/(name+'.hex')).write_text(packed(pixels),encoding='ascii')
        (O/(name+'_bg.hex')).write_text(packed(bg),encoding='ascii')
        setup='' if a.baseline else f'''$readmemh("{(O/(name+'_bg.hex')).as_posix()}",dut.background);dut.background_valid=1;'''
        phase=3 if a.baseline else 4;busy=5 if a.baseline else 4
        check='if(dut.phase!=0 || status[3:0]!=0)$fatal(1,"expected valid distribution %h",status);' if success else 'if(dut.phase==0 || status[3:0]==0 || dut.profiles[0]!==saved)$fatal(1,"unsafe distribution accepted %h",status);'
        if name=='dark_blue_background':
            if a.baseline:check+='if(dut.profiles[0][108:101]>60 || dut.profiles[0][100:93]>60)$fatal(1,"baseline fixture no longer reproduces false colour");'
            else:check+='if(dut.profiles[0][108:101]<=60 && dut.profiles[0][100:93]<=60)$fatal(1,"adaptive gates failed to reject dark colour");'
        src=f'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;wire [11:0] gr,gb;wire [127:0] models;wire [15:0] rev;wire active,needs,fp;wire [7:0] status,fs;wire [23:0] fg;
stable_calibration dut(clk,rst,1'b0,1'b0,96'd0,1'b0,1'b0,1'b0,1'b0,1'b0,gr,gb,models,rev,active,needs,status,fp,fg,fs);
integer n;reg [127:0] saved;
initial begin repeat(3)@(negedge clk);rst=1;@(negedge clk);saved=dut.profiles[0];
$readmemh("{(O/(name+'.hex')).as_posix()}",dut.samples);{setup}
dut.phase={phase};dut.cp=0;dut.staged_r=1024;dut.staged_b=1024;dut.staged_a=dut.profiles[0][63:0];dut.state=5;dut.clear_index=0;#1;
n=0;while(status[{busy}] && n<3000000)begin @(negedge clk);n=n+1;end
if(n>=3000000)$fatal(1,"search timeout %0d",dut.state);{check}
$display("RING_DISTRIBUTION_PASS {name} baseline={int(a.baseline)} success={int(success)} cycles=%0d model=%h",n,dut.profiles[0]);$finish;end endmodule'''
        run(('before_' if a.baseline else 'after_')+name,src,[module,R/'rtl/color_regions/regions_divide.v'])
    print('RING_DISTRIBUTIONS_PASS',flush=True)
if __name__=='__main__':main()
