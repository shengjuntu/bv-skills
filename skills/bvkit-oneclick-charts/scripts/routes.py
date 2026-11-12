"""bvkit routes: 20 章 -> 6 图元族 + 每章的口径规则（机器可读）。

设计原则：路由保证「选图」不靠读文档；rules 保证「口径」不靠执行者临场记得。
"""

# chapter -> (renderer, 一句话任务)
ROUTES = {
    "01": ("review", "评审图表有效性并给改版方案（输出检查清单，不产图）"),
    "02": ("timeseries", "把探索结果组织成带明确问题与背景的时间序列叙事"),
    "03": ("wordcloud", "加权词云 + 数值核对视图"),
    "04": ("matrix", "多变量颜色/亮度编码并检查可读性"),
    "05": ("geo", "任务中心的路线图（连接关系、空间、用户定位）"),
    "06": ("geo", "时空轨迹（编号标记 + 采样密度提示）"),
    "07": ("network", "双模网络与共现投影"),
    "08": ("network", "跨期相似网络 + 阈值敏感性"),
    "09": ("scatter", "相似性地图（投影、簇、异常点）"),
    "10": ("network", "网络 + 指标联动分析台"),
    "11": ("timeseries", "版本历史时间线 + 累积曲线（真实提交数据）"),
    "12": ("matrix", "多维分类交叉计数（稀疏交叉表）"),
    "13": ("smallmultiples", "可比小倍数 + 缺失格显式标注"),
    "14": ("matrix", "期望 vs 实际关系矩阵，标出空洞"),
    "15": ("matrix", "实体共现矩阵 + 采集完整性说明"),
    "16": ("matrix", "活动日志聚合（位置×时间窗热图）"),
    "17": ("multimodal", "视觉 + 声音互补映射"),
    "18": ("volume", "体数据正交切片 + 参数记录"),
    "19": ("animation", "动画 + 静态替代"),
    "20": ("review", "视觉论证草图与修辞审计（输出检查清单，不产图）"),
}

# 每章必须满足的口径规则（review 阶段执行；render 阶段自动落到 audit.checks）
RULES = {
    "01": ["must_have_title", "must_state_data_nature", "no_dual_axis", "no_truncated_baseline"],
    "02": ["date_format_declared", "zero_baseline", "events_time_aligned"],
    "03": ["weight_table_public", "checklist_panel", "no_cross_corpus_compare"],
    "04": ["colorblind_safe", "grayscale_separable"],
    "05": ["origin_marked", "task_stated"],
    "06": ["labels_not_overlapping", "sampling_density_noted"],
    "07": ["projection_threshold_declared", "isolated_nodes_placed"],
    "08": ["threshold_declared", "both_periods_same_scale"],
    "09": ["axes_labelled", "outliers_distinguished"],
    "10": ["linked_selection_consistent"],
    "11": ["time_ascending", "date_granularity_fits_span", "no_interpolation"],
    "12": ["counts_sum_to_n", "axis_categories_labelled"],
    "13": ["missing_marked_not_zeroed", "shared_axis"],
    "14": ["expected_actual_pair", "holes_marked"],
    "15": ["collection_completeness_noted", "diagonal_zero"],
    "16": ["window_declared", "scale_declared"],
    "17": ["simulated_vs_observed", "mapping_declared"],
    "18": ["params_recorded", "colorbar_present", "slice_position_stated"],
    "19": ["static_alternative", "identity_preserved"],
    "20": ["claim_evidence_paired"],
}

# 规则的人类可读说明（同时用于 review 输出与文档生成）
RULE_DOC = {
    "must_have_title": "必须有标题写明问题或口径",
    "must_state_data_nature": "必须声明数据是示例/真实/模拟",
    "no_dual_axis": "禁止双 y 轴（量级不同的指标必须分面）",
    "no_truncated_baseline": "不得截断基线放大差异（比率类除非有正当理由并注明）",
    "date_format_declared": "时间列必须声明解析口径（年是年、月是月）",
    "zero_baseline": "计数/规模类必须 0 起",
    "events_time_aligned": "事件位置必须与真实时间对齐，不得等间距排布",
    "weight_table_public": "词云必须给出权重口径与数值核对",
    "checklist_panel": "词云必须配数值核对视图",
    "no_cross_corpus_compare": "词云面积不可跨语料比较相对频率",
    "colorblind_safe": "分类配色需色觉友好（≥4 类时不得只用红绿）",
    "grayscale_separable": "配色需在灰度下可分离",
    "origin_marked": "路线图必须标出起点/当前位置",
    "task_stated": "必须写明该图的查找/导航任务",
    "labels_not_overlapping": "多轨迹共起点时不得用端点文字标签（改用编号+图例）",
    "sampling_density_noted": "采样密度不足必须注明",
    "projection_threshold_declared": "投影必须声明连边阈值",
    "isolated_nodes_placed": "0 度节点必须单独归置，不混入主布局",
    "threshold_declared": "相似网络必须声明阈值",
    "both_periods_same_scale": "跨期比较需同尺度同口径",
    "axes_labelled": "投影轴必须是具名或有说明的维度",
    "outliers_distinguished": "稀疏/异常点需与簇区分",
    "linked_selection_consistent": "联动视图的选中态配色必须一致",
    "time_ascending": "时间轴必须正序（最新在前需显式声明）",
    "date_granularity_fits_span": "刻度粒度必须能区分跨度（跨度小于两月时不得用月度刻度）",
    "no_interpolation": "累积/时间序列不得插值填补",
    "counts_sum_to_n": "交叉计数之和必须等于样本数",
    "axis_categories_labelled": "并行坐标每轴必须标出类别，不能只有数值刻度",
    "missing_marked_not_zeroed": "缺失格必须显式标注，不补零",
    "shared_axis": "小倍数必须共享尺度以便比较",
    "expected_actual_pair": "关系审计必须同时给期望与实际",
    "holes_marked": "空洞必须在图上标出而非只在文字里说",
    "collection_completeness_noted": "共现图必须提示采集完整性未核",
    "diagonal_zero": "实体共现矩阵对角应为 0 并说明",
    "window_declared": "聚合视图必须写明时间窗与粒度",
    "scale_declared": "聚合视图必须写明尺度",
    "simulated_vs_observed": "多模态必须区分模拟/观测/展示变换",
    "mapping_declared": "数值→感官的映射公式必须写出",
    "params_recorded": "体数据必须记录网格/σ/切片位置",
    "colorbar_present": "切片图必须带色标且统一值域",
    "slice_position_stated": "切片位置必须写在标题里",
    "static_alternative": "动画必须提供静态替代视图",
    "identity_preserved": "动画过渡必须保持对象身份（同色同大小）",
    "claim_evidence_paired": "每个视觉断言必须配可指认证据",
}


def route(chapter):
    if chapter not in ROUTES:
        raise KeyError("unknown chapter %r; known: %s" % (chapter, sorted(ROUTES)))
    return ROUTES[chapter]


def rules_for(chapter):
    return RULES.get(chapter, [])


# 意图 -> (chapter, 需要什么数据, 画出来是什么)
# 这是给"不知道该选第几章"的人和 agent 用的入口；chapter 只是内部的实现细节。
KINDS = {
    "trend": ("02", "一列时间 + 一列数值（可选一列事件文字）", "折线走势，下方按真实时间排事件"),
    "heatmap": ("12", "两列分类（或已交叉计数的三列）", "分类×分类的计数热图"),
    "compare": ("14", "期望一组关系 + 实际一组关系（或两列期望/实际值）", "期望 vs 实际双面板，空洞描红"),
    "matrix": ("04", "若干行若干列的多变量数值", "多变量颜色编码矩阵"),
    "cooccurrence": ("15", "实体与实体成对出现（或共现计数）", "实体×实体共现矩阵"),
    "window_heatmap": ("16", "一列时间 + 一列位置/类别", "位置×时间窗的聚合热图"),
    "network": ("07", "两列节点（一行一条关系）", "投影网络，孤立节点单列"),
    "similarity": ("08", "两期相似度或两期指标", "跨期相似网络，阈值可调"),
    "scatter": ("09", "两列坐标或两个可投影的数值", "投影散点，簇与异常点分开"),
    "facets": ("13", "一列分类 + 一列时间 + 一列数值", "小倍数折线，缺失处断开并标注"),
    "route": ("06", "一列顺序 + 两列坐标（经纬或平面）", "时空轨迹，共起点只标一次"),
    "map": ("05", "起点/终点/节点坐标", "路线图，起点标星"),
    "wordcloud": ("03", "一列词 + 一列权重", "加权词云 + 右侧频次核对面板"),
    "volume": ("18", "三维网格数值", "三正交切片，共用值域"),
    "animation": ("19", "逐帧实体位置或状态", "GIF + 起止帧静态替代"),
    "soundmap": ("17", "一列数值序列", "视觉 + 音高映射（可写 wav）"),
    "review": ("01", "已有图或 spec（不产图）", "只输出评审清单与改版建议"),
}


def kind_info(kind):
    """意图名 -> (chapter, 需要的数据, 画出来是什么)。未知则给可用清单。"""
    key = str(kind or "").strip().lower()
    if key not in KINDS:
        raise KeyError(
            "未知的图表意图 %r；可用: %s" % (kind, ", ".join(sorted(KINDS)))
        )
    return KINDS[key]


def resolve_kind(kind):
    """意图名 -> chapter（供 spec 的 kind/chart 字段使用）。"""
    return kind_info(kind)[0]

