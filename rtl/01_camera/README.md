# 01_camera

职责：配套摄像头配置、MIPI接收、RAW10适配、形成彩色图像所必需的厂家ISP和128位打包。

状态：已接入综合：camera_capture.v、camera_status.v。通过实例复用user_source，不移动IP；流接口缺少可靠eol与frame_id。

本次范围及接口限制见[工程README](../../README.md)和[架构与接口](../../docs/架构与接口.md)。目录存在不代表板上实现；未实现目录仅作功能组织，不放空壳硬件模块。
