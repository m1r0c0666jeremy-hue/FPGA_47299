"""Independent distribution fixtures; acquisition is covered separately."""
from pathlib import Path
import colorsys,subprocess,argparse,json
from test_ring_calibration import R,O,P,run
def hsv(h):return tuple(round(v*255) for v in colorsys.hsv_to_rgb(h/360,.75,.65))
def packed(a):return '\n'.join(''.join('%02x%02x%02x'%tuple(p) for p in a[i:i+4]) for i in range(0,2048,4))
def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',action='store_true');p.add_argument('--extended',action='store_true');a=p.parse_args()
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
    if a.extended:
        cases=[('purple_dark_bias',[(120,40,100)]*2048,[(60,0,40)]*2048,True),
               ('yellow_dark_bias',[(120,120,40)]*2048,[(60,60,0)]*2048,True),
               ('blue_metal_reflection',[(80,100,120)]*2048,[(160,180,200)]*2048,True),
               ('purple_neutral_background',[(100,60,100)]*2048,[(28,24,28)]*2048,True),
               ('yellow_bright_neutral',[(120,120,60)]*2048,[(248,248,220)]*2048,True)]
    for name,pixels,bg,success in cases:
        cp=int(name.startswith(('purple','yellow'))) if a.baseline else int(not name.startswith('yellow'))
        (O/(name+'.hex')).write_text(packed(pixels),encoding='ascii')
        (O/(name+'_bg.hex')).write_text(packed(bg),encoding='ascii')
        setup='' if a.baseline else f'''$readmemh("{(O/(name+'_bg.hex')).as_posix()}",dut.background);dut.background_valid=1;'''
        is_a=name.startswith('yellow') if a.baseline else not name.startswith(('purple','yellow'));phase=(2 if a.baseline else 3) if is_a else (3 if a.baseline else 4);busy=5 if a.baseline else 4
        model='dut.staged_a' if is_a else f'dut.profiles[{cp}][127:64]'
        check=f'if(dut.phase!={phase+1 if is_a else 0} || status[3:0]!=0)$fatal(1,"expected valid distribution %h",status);' if success else 'if(dut.phase==0 || status[3:0]==0 || dut.profiles[0]!==saved)$fatal(1,"unsafe distribution accepted %h",status);'
        if name in ('dark_blue_background','purple_dark_bias','yellow_dark_bias'):
            if a.baseline:check+=f'if({model}[44:37]>60 || {model}[36:29]>60)$fatal(1,"baseline fixture no longer reproduces false colour");'
            else:check+=f'if({model}[44:37]<=60 && {model}[36:29]<=60)$fatal(1,"adaptive gates failed to reject dark colour");'
        if name=='blue_metal_reflection':
            check+=f'if({model}[28:27]'+('!=0' if a.baseline else '==0')+')$fatal(1,"reflection saturation search");'
        check=check.replace('profiles[0]',f'profiles[{cp}]')
        src=f'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;wire [11:0] gr,gb;wire [127:0] models;wire [15:0] rev;wire active,needs,fp;wire [7:0] status,fs;wire [23:0] fg;
stable_calibration dut(clk,rst,1'b0,1'b0,96'd0,1'({cp}),1'b0,1'b0,1'b0,1'b0,gr,gb,models,rev,active,needs,status,fp,fg,fs);
wire [63:0] trained={model};
integer n;reg [127:0] saved;
initial begin repeat(3)@(negedge clk);rst=1;@(negedge clk);saved=dut.profiles[{cp}];
$readmemh("{(O/(name+'.hex')).as_posix()}",dut.samples);{setup}
dut.phase={phase};dut.cp={cp};dut.staged_r=1024;dut.staged_b=1024;dut.staged_a=dut.profiles[{cp}][63:0];dut.state=5;dut.clear_index=0;#1;
n=0;while(status[{busy}] && n<3000000)begin @(negedge clk);n=n+1;end
if(n>=3000000)$fatal(1,"search timeout %0d",dut.state);{check}
$display("RING_DISTRIBUTION_PASS {name} baseline={int(a.baseline)} success={int(success)} cycles=%0d model=%h",n,trained);$finish;end endmodule'''
        src=src.replace(model+'[44:37]','trained[44:37]').replace(model+'[36:29]','trained[36:29]').replace(model+'[28:27]','trained[28:27]')
        run(('before_' if a.baseline else 'after_')+name,src,[module,R/'rtl/color_regions/regions_divide.v'])
    print('RING_DISTRIBUTIONS_PASS',flush=True)
if __name__=='__main__':main()
