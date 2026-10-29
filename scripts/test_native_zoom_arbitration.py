"""Actual capture writer, command FIFO and dense reader share the DDR port."""
from refined_testlib import R,literal_fixture
from test_native_zoom_core import execute
import sys

def main():
    tb=literal_fixture(R/'scripts/test_refined_arbitration.py','s')
    tb=tb.replace('module tb;','module tb;localparam BW=240,RECOVER=0;').replace('always #7.5 dc=~dc','always #3.75 dc=~dc')
    tb=tb.replace('arbitration_video_in #(.BW(BW)) writer','refined_video_in writer').replace('refined_line_reader reader','native_line_reader reader')
    tb=tb.replace('reader.ready,reader.sy,reader.job_y,reader.state','reader.core.ready,reader.core.sy,reader.core.job_y,reader.core.state')
    tb=tb.replace('n<230400','n<921600').replace('repeat(260000)','repeat(100000)')
    tb=tb.replace('if(re)begin','if(re)begin')
    tb=tb.replace('integer due[0:2047]', 'always @(posedge dc)if(rst && wr && re)$fatal(1,"registered final write collided with native read");\ninteger due[0:2047]')
    tb=tb.replace('ARBITRATION_PASS','NATIVE_ARBITRATION_PASS').replace('3\'d0,os,oh,od',"3'd2,os,oh,od") if '--dense' in sys.argv else tb.replace('ARBITRATION_PASS','NATIVE_ARBITRATION_PASS')
    mods=['refined_video_in.v','native_line_reader.v','native_line_core.v','native_read_adapter.v','native_downsample2.v','stable_packer.v','stable_model_lane.v','stable_filter4.v','refined_reset_bridge.v','refined_zoom_geometry.v','refined_mc_to_user_interface.v',str(R/'rtl/04_tracking/target_mailbox.v')]
    mods += [str(R/'user_source/ip_source'/n) for n in ('w128_d512_fifo/w128_d512_fifo.v','w128_d512_fifo/soft_fifo_al_4057d6b76aa6.v','w155_d512_fifo/w155_d512_fifo.v','w155_d512_fifo/soft_fifo_al_f58e8b3e1f3d.v')]
    execute('arbitration_dense' if '--dense' in sys.argv else 'arbitration_low',tb,mods,timeout=1800)
if __name__=='__main__':main()
