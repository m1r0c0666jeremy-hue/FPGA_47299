# 02: 交付来源可核验的 720p 候选

**What to build:** 交付 bit、同源源码、哈希和现场操作说明；编译输入完全相同则复用已审计 bit，否则须重新完整构建通过。

**Blocked by:** 01 恢复 720p 全链路并保留源坐标。

**Status:** implemented; software verified; final package verification recorded in reports/720p

- [x] 在确认的边界 B 拒绝混入 FHD 的源码、错误 bit 和无效证据。
- [x] 验证全部编译输入与物理构建证据对应。
- [x] 交付可独立复核的包，明确历史构建复用和硬件待验。
