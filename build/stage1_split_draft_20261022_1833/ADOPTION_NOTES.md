# 采用前仍需完成（不代表已采用）

91038的新鲜14帧与8RGB全部通过并exit0关闭，stamp_validation.json已绑定证据；已量化组合门级少644 Slice、ERAM+3，只是局部估计。正式源仍199a457。若采用：

- 点位/校验来自shared_vertex目录，编辑器用本目录stage1_regions_shared.v，绘制器用stage1_render_stamp.v。复制前核对当前308输入及私有证据哈希；原297输入和用户文件继续保护。
- 必须维护generate_stage1.py的真实连接：编辑器新增saved_vertices/draft_vertices；OSD使用saved输入和新增168位I_region_draft，利用已有area_count/draft_count传给SPLIT_DRAFT=1绘制器。原合成render_vertices可保留兼容输出，但实际显示不能再使用它，否则前端宽选择不会消失。不要复制本目录stage1_osd.v测试适配器作为正式OSD。
- 新OSD草稿参数可放在原region_vertices之后。footer局部扩展OSD_ZERO_ARGS，video用命名草稿零值，live连接真实saved/draft，overlay/region_footer明确连接草稿。尽量不改stage1_test_sources.py共享测试依赖，以便保留确实未受影响证据。
- geometry测试连接实际SHARED_VERTEX=1外部口；render测试像probe/replay一样拆分四个顶点组；guard核对两平面及区域号/可见性的同拍冻结；regions采用coupled.py的真实定点联接，不能只测试旧默认路径。
- stamp中的span_lo/hi/span_valid空诊断线应在正式版移除，并调整render测试的失败诊断，不保留无驱动线。缓存地址、有效银行及同址读写时序仍须当前回归和真实TD映射验证。
- audit_stage1的regions门槛应要求实际编辑→绘制标记和renderer依赖。修改审计器会使routing_guards报告哈希失效：重跑六类走线守卫并同步package路径。最终software_current报告也须新生成并同步package，不能把1545旧源审计称当前通过。
- 原文件名集合仍308；维护生成器、短项验证、提交后新冻结，重跑所有当前哈希已失效的几何/编辑/14帧/8RGB/底栏/84视频/4live。未变模块只按真实哈希复用。
- 优先用已成功布局的pr5、sequential/min64、area_prior/high/maxfan128/more_lut_pair建立新正式资源比较；原ADC/SDC不变。最终route零冲突且setup/hold均非负、package与独立verify成功前，不交付bit。

所有私有/取消/失败输出保留。用户已明确“不再安排定时”，不创建新定时，也不恢复已删除的旧fpga项；主任务继续实施。
