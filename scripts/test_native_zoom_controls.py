"""Same K and wire-level brightness regressions with the actual native controls/config."""
import argparse,ast
from test_native_zoom_core import execute
from refined_testlib import R
import test_stage1_camera_readback as readback
from test_stage1_k_controls import CONTROLS

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--readback',action='store_true');ap.add_argument('--keys',action='store_true');a=ap.parse_args()
    if a.readback:
        modules=['native_camera_config.v','native_sensor_table.v']
        modules += [str(R/'user_source/hdl_source/uics500_cfg'/n) for n in ('uics500regAE.v','SC500GainTbl.v','uii2c.v')]
        modules += [str(R/'scripts/sc500_i2c_slave_model.v.txt')]
        fixture=readback.src.replace('refined_camera_config','native_camera_config')
        for name,mode,slot in readback.cases:
            execute('camera_readback_'+name,fixture,modules,compile_args=[f'-Ptb.MODE={mode}',f'-Ptb.FAULT_SLOT={slot}'],timeout=600)
    elif a.keys:
        tree=ast.parse((R/'scripts/test_stage1_k_keys75m.py').read_text(encoding='utf-8'))
        fixture=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='src' for t in n.targets))
        execute('k_keys75m',fixture.replace('stage1_controls','native_controls'),['native_controls.v'],timeout=1800)
    else:
        execute('controls',CONTROLS.replace('stage1_controls','native_controls'),['native_controls.v'])
        fixture='''`timescale 1ns/1ps
module tb;reg clk=0;always #5 clk=~clk;reg rst=0;reg [2:0] keys=7;wire [2:0] zoom;
native_controls #(.CYCLES_PER_MS(4),.DEBOUNCE_MS(2),.LONG_PRESS_MS(1000)) dut(.I_clk(clk),.I_rst_n(rst),.I_keys_n(keys),.I_ui_switch(2'b00),.I_gain_ack(1'b0),.I_cal_status(8'd0),.I_pause(1'b0),.I_camera(18'h2005a),.O_zoom(zoom));
integer i;initial begin repeat(4)@(negedge clk);rst=1;repeat(20)@(negedge clk);
for(i=1;i<=6;i=i+1)begin keys=5;repeat(16)@(negedge clk);keys=7;repeat(20)@(negedge clk);
if(zoom!=i%3)$fatal(1,"native three zoom wrap %0d",zoom);end
$display("NATIVE_ZOOM_CONTROLS_PASS three_steps_only");$finish;end endmodule'''
        # Match the unchanged, named native interface rather than stubbed ports.
        fixture=fixture.replace('.key_n(keys),.switches(2\'b00)', '.I_key_n(keys),.I_mode(2\'b00)')
        execute('zoom_controls',fixture,['native_controls.v'])
if __name__=='__main__':main()
