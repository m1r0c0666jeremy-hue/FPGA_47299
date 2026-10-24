// Native 1080p protocol v5. Buses keep their 128/768/852-bit widths.
// All geometry/area extensions occupy bits that were zero in protocol v4.
`ifndef FHD_METADATA_VH
`define FHD_METADATA_VH
`define FHD_META_VERSION 3'd5
`define FHD_C_X0(c) c[10:0]
`define FHD_C_X1(c) c[21:11]
`define FHD_C_Y0(c) c[32:22]
`define FHD_C_Y1(c) c[43:33]
`define FHD_C_BOX(c) c[43:0]
`define FHD_C_COUNT(c) c[64:44]
`define FHD_C_X(c) c[75:65]
`define FHD_C_Y(c) c[86:76]
`define FHD_C_SUPPORT(c) c[93:87]
`define FHD_C_QUALITY(c) c[95:94]
`define FHD_C_RANK(c) c[119:96]
`define FHD_META_A_Y(m) {m[224],m[57:48]}
`define FHD_META_B_Y(m) {m[225],m[78:69]}
`define FHD_META_TIP_Y(m) {m[226],m[99:90]}
`define FHD_META_A_BOX(m) {m[228],m[141:132],m[227],m[131:122],m[121:111],m[110:100]}
`define FHD_META_B_BOX(m) {m[230],m[183:174],m[229],m[173:164],m[163:153],m[152:142]}
`define FHD_META_A_COUNT(m) {m[248],m[203:184]}
`define FHD_META_B_COUNT(m) {m[249],m[223:204]}
`define FHD_META_RAW_A(m) {m[250],m[275:256]}
`define FHD_META_RAW_B(m) {m[251],m[295:276]}
`define FHD_META_FILTERED_A(m) {m[252],m[315:296]}
`define FHD_META_FILTERED_B(m) {m[253],m[335:316]}
`endif
