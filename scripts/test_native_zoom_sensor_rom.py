"""New Boolean sensor decoder compared against the frozen prior case ROM."""
from test_native_zoom_core import execute
from refined_testlib import R

if __name__=='__main__':
 old=R/'build/native_zoom_place_20261029_165246/compiled_source/rtl/color_regions/native_sensor_table.v'
 import hashlib
 assert hashlib.sha256(old.read_bytes()).hexdigest()=='f115831a225fd0b70311d8476eaab9a90beafdaff4de116a58d8408c7b2af2c1'
 golden=old.read_text(encoding='utf-8').replace('module native_sensor_table','module frozen_sensor_table')
 tb='''`timescale 1ns/1ps
module tb;reg clk=0;always #5 clk=~clk;reg [8:0] index=511;wire [31:0] actual,expected;wire [8:0] asize,esize;
native_sensor_table dut(index,actual,asize);frozen_sensor_table golden(index,expected,esize);
reg [6:0] level=0;wire [15:0] actual_gain,expected_gain;
native_gain_table gains(clk,1'b1,level,actual_gain);SC500GainTbl original_gain(clk,1'b1,level,expected_gain);
integer n;initial begin for(n=0;n<512;n=n+1)begin index=n;#1;if(actual!==expected || asize!==esize || asize!=88)$fatal(1,"sensor sequence %0d",n);end
for(n=0;n<128;n=n+1)begin @(negedge clk);level=n;@(posedge clk);#1;if(actual_gain!==expected_gain)$fatal(1,"gain equivalence %0d got%h expected%h",n,actual_gain,expected_gain);end
$display("NATIVE_SENSOR_ROM_PASS all512/88officialwrites/gain128/defaultzero/equivalent");$finish;end endmodule'''
 execute('sensor_rom',tb+'\n'+golden,['native_sensor_table.v','native_gain_table.v',str(R/'user_source/hdl_source/uics500_cfg/SC500GainTbl.v')])
