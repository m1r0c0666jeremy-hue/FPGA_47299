# 交付打包恢复记录

首次打包目录 `build/target_color_regions_ring_stability_20261015_025936` 已生成bit、编译输入快照、源码ZIP及清单，但以ASCII写入SHA256SUMS.txt时不能编码中文文件名，因此中止。该目录及部分校验清单原样保留，不作为完整交付入口。

北京时间2026-10-15 03:30的 automation-2 续作修正校验清单为UTF-8，使用 `package_ring_stability.py --previous-delivery` 在新的时间戳目录重新打包。没有修改编译输入或重建bit；核对206项冻结输入、ZIP逐文件哈希和历史文件保护。新的完整目录以成功打印 RING_DELIVERY_PASS 的交付清单为准。

实物复测待验；此次恢复未下载板卡或烧写Flash。
