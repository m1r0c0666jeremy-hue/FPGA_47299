"""New Boolean sensor decoder compared against the frozen prior case ROM."""
from test_native_zoom_core import execute
from refined_testlib import R

if __name__=='__main__':
 old=R/'build/native_zoom_place_20261029_165246/compiled_source/rtl/color_regions/native_sensor_table.v'
 import hashlib
 assert hashlib.sha256(old.read_bytes()).hexdigest()=='f115831a225fd0b70311d8476eaab9a90beafdaff4de116a58d8408c7b2af2c1'
 golden=old.read_text(encoding='utf-8').replace('module native_sensor_table','module frozen_sensor_table')
 tb='''`timescale 1ns/1ps
module tb;reg [8:0] index=0;wire [31:0] actual,expected;wire [8:0] asize,esize;
native_sensor_table dut(index,actual,asize);frozen_sensor_table golden(index,expected,esize);
integer n;initial begin for(n=0;n<512;n=n+1)begin index=n;#1;if(actual!==expected || asize!==esize || asize!=88)$fatal(1,"sensor sequence %0d",n);end
$display("NATIVE_SENSOR_ROM_PASS all512/88officialwrites/defaultzero/equivalent");$finish;end endmodule'''
 execute('sensor_rom',tb+'\n'+golden,['native_sensor_table.v'])
