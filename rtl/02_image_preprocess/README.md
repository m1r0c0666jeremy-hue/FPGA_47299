# 02_image_preprocess

职责：独立图像预处理、增强和算法切换。

状态：ImagePreprocess分支已加入 `image_preprocess.v` 并接入综合。位于DDR读回、hdmi_mixer之后和hdmi_tx之前，接收RGB888及同步信号；00原图、01 Sobel边缘、10灰度、11二值化。算法和时序约定见[10_3模块说明](../../docs/图像处理与拨动开关_10_3.md)。本模块实物效果待验收。

本次范围及接口限制见[工程README](../../README.md)和[架构与接口](../../docs/架构与接口.md)。目录存在不代表板上实现；未实现目录仅作功能组织，不放空壳硬件模块。
