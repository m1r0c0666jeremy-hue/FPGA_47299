# OSD英文共用字库与静态表压缩

基线：Region_Recognition_1019，7df95aabb9fedc7927d03aa6013aa6a9346eb962。
原中文bit：fe6029bb4fd343df1e7757418c1b2540e2c9884d93f27206a9464509bc3586fe。

当前为开发候选，尚无新的可交付bit。以实际综合、完整布线和当前源码软件证据验收，不提前宣称资源节省。

## 边界

仅修改正式OSD、其程序表、专用英文字符/字形ROM及工程引用。原中文字库、stable_osd、Logo、检测/校准/跟踪/视频存储逻辑与原ADC/SDC保持原字节。
四图像模式、两配色、五倍率、方向、按键、三帧确认、15帧期限与尖端规则不变。
本次不修复假色、误框、E06、黑闪或未经复现的文字残留，不把它们写成已解决。

## 两步候选

1. 45字符的8×16字形，复用中文交付版中英文字符左侧8列原点阵。标签和底栏共用一个同步端口，输出拍数不变。两行64格、625行采样和数值有效性保持。
2. 静态程序表去尾部空格，按模板起点/长度索引；保留两拍读取和原格式化等待拍，越过有效长度输出空格。单独提交和比较，收益不足可独立回退此步。

## 英文/中文对照

| 英文 | 中文含义 |
|---|---|
| RAW / HILITE / GRAY / MASK | 原图 / 色彩高亮 / 灰度 / 色彩二值 |
| R/B / Y/P | 红蓝 / 黄紫配色 |
| RED A1 / BLUE B1 / YELLOW A1 / PURPLE B1 | 红A1 / 蓝B1 / 黄A1 / 紫B1 |
| IDLE / CENTER SELECT / CONFIRMING / TRACKING | 待命 / 中央选取 / 确认中 / 跟踪中 |
| MISSING COLOR / HOLD LOST / RESELECT CENTER | 缺色 / 失锁保持 / 中央重选 |
| TIP OUT OF VIEW / INVALID FRAME | 尖端越界 / 无效帧 |
| CAL WHITE / CAL BACKGROUND / CAL A / CAL B | 白纸 / 空背景 / A / B校准 |
| PROCESSING / SAMPLE FAILED / RECALIBRATE | 采样处理中 / 采样失败 / 请重新校准 |
| VIDEO NOT READY / KEY CONFLICT / NO NEW FRAME / WAIT RESULT | 视频未就绪 / 按键冲突 / 无新帧 / 等待结果 |
| DEFAULT / LEARNED / UPDATE | 默认参数 / 材料已学习 / 需要更新 |
| LAT / AGE / FR / F / V | 板内延迟 / 落后帧数 / 帧 / 图像帧号 / 参数版本 |

E01无效采集帧；E02白纸质量不足；E03增益超范围；E04混色或采样不足；E05模型重叠；E06背景不可分；E07材料保留不足；E08采样窗暗部过多；E09亮度改变；E0A中性弱色差过多；E0B主色相不匹配；E0C有效样本不足。

KEY3:SAMPLE为取样，KEY3:RETRY为重采，KEY2:CANCEL为取消。空背景步先移走双色标记，再对准实际干扰物；不能把目标材料作为背景。
原亮度/方向/倍率/启停及组合键操作仍按《颜色视频显示改进_上板一页》执行。LAT不含曝光和显示器响应；横线表示无效。

## 验收记录

共用中文字库原/新四完整帧RGB及同步逐拍对照已通过。英文45组完整底栏5529600像素以及两种帧尾中止245760像素已通过；覆盖20状态、12失败原因、五倍率和数值边界。初次英文测试的输出计数门控晚一拍已修正，失败日志保留；RTL未因此改变。
后续还须标签边界/非文字像素对照、实际候选80组合及故障/联接回归、实际资源和最终建立/保持检查。

## 构建和后续实物对比

工程入口仍为td_project/target_color_regions_refined.al。生成器scripts/generate_refined_regions.py --check核验生成物；正式设置为area_prior、pack_effort high、strategy5、max_fanout128、normal布线。构建脚本每次新建冻结目录；移到其他路径时重新生成工程、综合和布局，不直接套用含原绝对约束路径的旧检查点。

待全部软件检查合格后，候选bit、同源ZIP和文件校验值放入独立target_color_regions_osd_memory_时间戳目录。以该目录delivery.json和SHA256SUMS.txt为准；当前中文交付保留。实物复测保持相同材料、照明、机位和校准操作，确认英文可读、取样/重采/取消提示完整、标签四边与重叠正确，以及原成功样例没有退步。再检查四图像模式、五倍率和两方向。旧假色、遮挡恢复和黑闪等问题按实际结果记录，不能因节省存储标记为已解决。
