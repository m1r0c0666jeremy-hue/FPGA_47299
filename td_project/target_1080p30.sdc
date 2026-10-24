# Native SC500CS FHD profile. Receiver budget: at most 960 Mb/s/lane.
# Sensor lane rate remains a hardware measurement, not an inferred achievement.
create_clock -name {sys_clk_50m} -period 20.000 -waveform {0.000 10.000} [get_ports {I_sys_clk}]
create_clock -name {mipi_rx_ck_pad} -period 2.083333 -waveform {0.000 1.041667} [get_nets {IO_rx_clk_pad_p}]
derive_clocks
rename_clock -name {pll_clk_100m} [get_clocks {u_system_pll/u_core/u_PH1P_PHY_PLL.clkc[0]}]
rename_clock -name {pll_clk_24m} [get_clocks {u_system_pll/u_core/u_PH1P_PHY_PLL.clkc[1]}]
rename_clock -name {ISP_PROCESS_CLK} [get_clocks {u_system_pll/u_core/u_PH1P_PHY_PLL.clkc[2]}]
rename_clock -name {HDMI_PIXEL_CLK} [get_clocks {u_hdmi_pll/u_core/u_PH1P_PHY_PLL.clkc[0]}]
rename_clock -name {HDMI_SERIAL_CLK} [get_clocks {u_hdmi_pll/u_core/u_PH1P_PHY_PLL.clkc[1]}]
rename_clock -name {MIPI_RX_BYTE_CLK} [get_clocks {u_camera/u_mipi_dphy_rx_ph1p_mipiio_wrapper/u_ph1p_mipiio_rx_wrapper/u_PH1P_LOGIC_DPHY_MIPI_RX.o_fabric_div4_8_clk}]
# These are physically independent clock domains. Existing handshakes and FIFOs,
# including the new RAW line FIFO, form their data boundaries. Each domain's
# intra-clock paths remain fully timed. No same-domain path is exempted.
set_clock_groups -asynchronous \
 -group [get_clocks {mipi_rx_ck_pad MIPI_RX_BYTE_CLK}] \
 -group [get_clocks {sys_clk_50m pll_clk_100m pll_clk_24m ISP_PROCESS_CLK}] \
 -group [get_clocks {HDMI_PIXEL_CLK HDMI_SERIAL_CLK}] \
 -group [get_clocks {u_video/u_ph1p35_324_ddr_wrapper/u_ddr2/ddr_clk u_video/u_ph1p35_324_ddr_wrapper/u_ddr2/usr_clk}]
# Intentional first-stage data synchronizers in the related system clocks.
# The binary epoch is never sampled; its registered Gray copy settles throughout
# the >=1 ms stream reset. Only the first receiving stage is exempt.
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[0]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[1]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[2]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[3]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[4]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[5]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[6]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[7]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[8]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[9]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[10]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[11]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[12]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[13]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[14]}]
set_false_path -to [get_regs {u_video/capture_epoch_sync/g0[15]}]
set_false_path -to [get_regs {u_camera/u_config/req_sync[0]}]
set_false_path -to [get_regs {u_camera/u_config/up_sync[0]}]
set_false_path -to [get_regs {camera_relay/ready_sync[0]}]
set_false_path -to [get_regs {camera_relay/ack_sync[0]}]
set_false_path -to [get_regs {camera_relay/event_sync[0]}]
set_false_path -to [get_regs {u_camera/ready_capture[0]}]
set_false_path -to [get_regs {u_camera/u_config/frame_sync[0]}]
set_false_path -to [get_regs {u_camera/u_config/bad_sync[0]}]
# Reset bridges deliberately accept an asynchronous assertion at async_n.
# Exempt paths through that reset-only net; release_pipe[0]->[1] stays timed.
set_false_path -through [get_nets {u_camera/processing_reset/async_n}]
# The supervisor's stream reset also feeds vendor FIFO asynchronous assertion.
# Each FIFO already contains its own two-stage local release synchronizer.
set_false_path -through [get_nets {u_video/stream_async_n}]
puts "FHD_CDC_GAIN_FIRST [get_regs {u_camera/u_config/req_sync[0]}]"
puts "FHD_CDC_RESET_NET [get_nets {u_camera/processing_reset/async_n}]"
puts "FHD_CDC_STREAM_RESET [get_nets {u_video/stream_async_n}]"
puts "FHD_CDC_ACK_FIRST [get_regs {camera_relay/ack_sync[0]}]"
puts "FHD_CDC_EVENT_FIRST [get_regs {camera_relay/event_sync[0]}]"
