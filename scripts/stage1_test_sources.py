"""Formal stage-one OSD bindings for inherited image/latency fixtures."""
from refined_testlib import R
OSD_ZERO_ARGS="2'd0,672'd0,16'd0,4'd0,3'd0,3'd0,3'd0,4'd0,4'd0,4'd0,4'd0,1'b0,2'd0,11'd0,20'd0,4'd0,4'd0,1'b0,1'b0,1'b0,1'b0,3'd5,"
EXTRA_OSD=[R/'rtl/color_regions'/n for n in ('stage1_arith.v','stage1_render.v','stage1_ui_formatter.v','stage1_ui_text.v')]
