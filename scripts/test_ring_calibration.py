"""Run old and new acquisition tests and focused distribution counterexamples."""
from pathlib import Path
import subprocess,os,argparse
R=Path(__file__).resolve().parents[1];O=R/'build/sim/ring_calibration';O.mkdir(parents=True,exist_ok=True)
P=R/'reports/transparent_ring';P.mkdir(parents=True,exist_ok=True)
iv=R/'tools/iverilog/ucrt64/bin/iverilog.exe';env=os.environ.copy();env['PATH']=str(iv.parent)+os.pathsep+env.get('PATH','')
def run(name,src,modules):
    tb=O/(name+'.sv');tb.write_text(src,encoding='utf-8');logs=[]
    for cmd in ([iv,'-g2012','-s','tb','-o',O/(name+'.vvp'),tb,*modules],[iv.with_name('vvp.exe'),O/(name+'.vvp')]):
        r=subprocess.run(list(map(str,cmd)),cwd=R,env=env,capture_output=True,text=True,timeout=1800)
        logs.append(r.stdout+r.stderr);print(logs[-1],flush=True)
        (P/(name+'.log')).write_text('\n'.join(logs),encoding='utf-8')
        if r.returncode:raise SystemExit(r.returncode)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--baseline',action='store_true');args=a.parse_args()
    src=(R/'sim/ring_baseline/tb_calibration.sv').read_text(encoding='utf-8')
    module=R/'rtl/color_regions/stable_calibration.v'
    if args.baseline:
        module=R/'sim/ring_baseline/stable_calibration.v'
    else:
        src=src.replace('status[7:6]','status[7:5]').replace('frame_status[7:6]','frame_status[7:5]').replace('status[5]','status[4]')
        src=src.replace('n<500000','n<3000000').replace('n>=500000','n>=3000000')
        src=src.replace('dut.state==23 && dut.phase==3','dut.state==35 && dut.phase==4')
        src=src.replace('frame_status[7:5]!=3','frame_status[7:5]!=4')
        src=src.replace('dut.state=23;dut.phase=3;', 'dut.state=35;dut.phase=4;dut.best_valid=1;dut.best_model=saved[127:64];')
        src=src.replace('frames(1);if(status[7:5]!=3)', 'frames(1);if(status[7:5]!=4)')
        src=src.replace('frames(5);if(status[7:5]!=3)', 'frames(5);if(status[7:5]!=4)')
        # Every successful white step must acquire a real eight-frame background.
        src=src.replace('sample=1;@(negedge clk);sample=0;frames(1);', 'sample=1;@(negedge clk);sample=0;frames(4);if(status[7:5]!=3)$fatal(1,"background acquisition");\nsample=1;@(negedge clk);sample=0;frames(1);',1)
        src=src.replace('frames(4);if(status[7:5]!=2)$fatal(1,"neutral white failed");', 'frames(4);if(status[7:5]!=2)$fatal(1,"neutral white failed");\nsample=1;@(negedge clk);sample=0;frames(4);if(status[7:5]!=3)$fatal(1,"background retry failed");')
        src=src.replace('sample=0;frames(4);\nsample=1;@(negedge clk);sample=0;frames(5);', 'sample=0;frames(4);\nsample=1;@(negedge clk);sample=0;frames(4);\nsample=1;@(negedge clk);sample=0;frames(5);')
        src=src.replace('STABLE_CALIBRATION_PASS', 'RING_CALIBRATION_PASS').replace('white/A/B eight full frames','white/background/A/B eight full frames')
        src=src.replace('status[3:0]!=4)$fatal(1,"insufficient material', 'status[3:0]!=10)$fatal(1,"insufficient material')
        src=src.replace('initial begin repeat(3)', '''always @(posedge clk)if(rst && dut.sample_write && dut.phase==2)begin
if(dut.rx!=52+160*(dut.groups%8)+8*dut.frames || dut.ry!=17+90*(dut.groups/8)+8*((3*dut.frames)%8))
$fatal(1,"background coordinate mismatch frame%0d group%0d xy%0d/%0d",dut.frames,dut.groups,dut.rx,dut.ry);
end
initial begin repeat(3)''',1)
    run('calibration_baseline' if args.baseline else 'calibration_acquisition',src,[module,R/'rtl/color_regions/regions_divide.v'])
