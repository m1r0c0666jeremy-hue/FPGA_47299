# 10_memory_video_out

memory_video_out.v已接入综合，保留DDR、调度与显示时序，在hdmi_mixer与hdmi_tx之间连接02目录的image_preprocess。处理候选模式及局部复位由顶层传入。厂家FIFO尾字、完整帧恢复等问题本轮暂缓，见[当前清单](../../docs/问题清单_10_3.md)。
