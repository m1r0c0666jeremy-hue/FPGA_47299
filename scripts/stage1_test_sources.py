"""Formal stage-one OSD bindings for inherited image/latency fixtures."""
from refined_testlib import R
OSD_ZERO_ARGS="2'd0,672'd0,16'd0,4'd0,3'd0,3'd0,3'd0,4'd0,4'd0,4'd0,4'd0,1'b0,2'd0,11'd0,20'd0,4'd0,4'd0,1'b0,1'b0,1'b0,1'b0,3'd5,"
EXTRA_OSD=[R/'rtl/color_regions'/n for n in ('stage1_render.v','stage1_ui_formatter.v','stage1_ui_text.v')]
_PORTS=['I_ui_mode','I_region_vertices','I_region_counts','I_region_closed','I_area_count','I_expected_area','I_actual_area',
        'I_draft_count','I_run_state','I_completed','I_occupied','I_area_muted','I_area_trend','I_area_distance','I_area_dwell',
        'I_edit_error','I_start_error','I_area_busy','I_tip_live','I_gain_busy','I_gain_failed','I_gain_slot']
OSD_ZERO_NAMED=','.join('.'+n+'('+v+')' for n,v in zip(_PORTS,OSD_ZERO_ARGS.rstrip(',').split(',')))+','

OSD_ZERO_NAMED += ".I_gain_target(7'd105),.I_tip_reason(4'd0),"
