# 安路官方 Logo 素材

保存日期：2026-10-04。来源为[安路科技官网首页](https://www.anlogic.com/)实际引用的图片。

| 文件 | 内容 | 来源／生成方式 |
|---|---|---|
| `anlogic_logo_official.svg` | 图形标识＋中英文公司全称，原始尺寸290×33 | [官网桌面页原图](https://www.anlogic.com/Public/Uploads/uploadfile/images/20230414/logo.svg) |
| `anlogic_logo_mobile_official.svg` | 独立图形标识，原始尺寸48×31 | [官网移动页原图](https://www.anlogic.com/Public/Uploads/uploadfile/images/20230909/logo_ph1.svg) |
| `anlogic_logo_preview.png` | 完整Logo的透明背景PNG，1160×132 | 使用Sharp以288 DPI渲染桌面页SVG，仅转换格式，未重绘或改变图形 |

SVG为矢量图，放大不依赖固定像素；两份SVG保持下载原始字节。PNG为便于预览的派生文件，并非官网另行发布的位图。

原始文件SHA256：

- `anlogic_logo_official.svg`：`4022485e1b6fc597df78de0b9ce3b3b0d80dbe4f18cec519ea60ef24b2acc358`
- `anlogic_logo_mobile_official.svg`：`63f1452a54e7e392496e0a72a92a9ff1ce960976b41314acc335d1aa02fadd12`

Logo权利归安路相关权利人所有；本目录记录项目展示素材来源，不将其声明为本项目原创或开源授权素材。官网图片下载需要携带官网首页作为Referer。

## 工程接入状态

2026-10-05：已由 `scripts/generate_scaling_osd.py` 将官方独立图形转换为96×62、2位调色板像素 ROM，并配“安路科技”字样接入 ScalingTest。调色板为背景白、深蓝 `1c2c4e`、红 `ed1b23`；不是完整官网横版图的缩小版。SVG 原件保持不变。

`scaling_glyph_atlas.png` 是所需60个字符的点阵预览，`anlogic_symbol_96x62.png` 是官方图形的栅格化来源，`scaling_rom_manifest.json` 记录生成文件、字体哈希和复用大赛字符。构建已包含 ROM，实际 HDMI 上的清晰度和连续性仍待上板。软件逐像素对照和 RTL 预览见 [验证报告](../../../reports/ScalingTest验证报告.md)。
