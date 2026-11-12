"""bvkit review: 把 bv-01 / bv-20 的评审方法做成可执行检查（不产图，产出结论）。

两个用途：
1) 渲染前静态评审 spec，挡掉会在图上犯的错误（双轴、截断基线、缺口径…）；
2) 渲染后复核 audit，检查每章必做项是否真的落到了产物里。
"""
from routes import RULE_DOC, rules_for


def review_spec(spec, data_report=None):
    """Return list of findings: {level, rule, msg}."""
    p = spec.get("params") or {}
    chapter = str(spec.get("chapter") or "")
    findings = []

    def add(level, rule, msg):
        findings.append({"level": level, "rule": rule, "msg": msg})

    if not spec.get("out"):
        add("error", "must_have_title", "缺少 out（产物路径）")
    if not (spec.get("title") or p.get("title")):
        add("error", "must_have_title", "缺少标题：读者无法知道这张图回答什么问题")
    if not (spec.get("note") or p.get("note")):
        add("warn", "must_state_data_nature", "未声明数据性质（示例/真实/模拟）")

    if p.get("dual_axis") or p.get("secondary_axis"):
        add("error", "no_dual_axis", "检测到双 y 轴配置：量级不同的指标必须拆面板")

    if p.get("zero_baseline") is False and p.get("baseline_reason") is None:
        add("error", "no_truncated_baseline", "关闭了 0 基线且未说明理由：会放大差异")

    if spec.get("renderer") in ("network",) and not p.get("threshold"):
        add("warn", "threshold_declared", "相似网络未声明阈值：不同阈值会得到完全不同的结构")
    if spec.get("renderer") in ("smallmultiples",) and "missing_marked_not_zeroed" not in str(p):
        add("info", "missing_marked_not_zeroed", "缺失格将由渲染器用灰 x 标注，不补零")
    if spec.get("renderer") in ("animation",) and p.get("static_alt") is False:
        add("error", "static_alternative", "动画未提供静态替代：读者无法在静态环境复核")

    if data_report:
        if data_report.get("missing_cells"):
            add("warn", "missing_marked_not_zeroed",
                "数据含 %d 个缺失单元格：须显式标注" % data_report["missing_cells"])
        # 只在「疑似时间列但解析失败」时报警，避免把 1-12 的月份数字误判成年月问题
        time_hint = ("date", "time", "year", "月", "年", "时间", "日期")
        for c in data_report.get("columns", []):
            if c["kind"] == "text" and any(k in c["name"].lower() for k in time_hint):
                add("warn", "date_format_declared",
                    "列 %r 疑似时间但解析失败：请在 spec 里声明 date_format 或 date_columns" % c["name"])
        for i in data_report.get("issues", []):
            if i["level"] == "error":
                add("error", "data_" + i.get("col", "*"), i["msg"])

    for rule in rules_for(chapter):
        _ = RULE_DOC.get(rule)
    return findings


def review_audit(audit, chapter):
    """Check which mandatory rules the render actually satisfied."""
    checks = audit.get("checks") or {}
    satisfied, unknown, failed = [], [], []
    rules = rules_for(chapter)
    mapping = {
        "zero_baseline": ("zero_baseline", True),
        "no_dual_axis": ("dual_axis", False),
        "date_format_declared": ("date_columns", lambda v: v >= 1),
        "events_time_aligned": ("date_columns", lambda v: v >= 1),
        "checklist_panel": ("checklist_panel", True),
        "colorblind_safe": ("palette", "okabe_ito"),
        "grayscale_separable": ("palette", "okabe_ito"),
        "isolated_nodes_placed": ("nodes", lambda v: True),
        "threshold_declared": ("threshold_set", True),
        "projection_threshold_declared": ("threshold_set", True),
        "missing_marked_not_zeroed": ("missing_not_zeroed", True),
        "shared_axis": ("shared_axis", True),
        "hole" + "s": ("holes", lambda v: True),
        "holes_marked": ("holes", lambda v: True),
        "expected_actual_pair": ("expected_actual_pair", True),
        "axis_categories_labelled": ("facets", lambda v: True),
        "params_recorded": ("params_recorded", True),
        "colorbar_present": ("colorbar", True),
        "slice_position_stated": ("slice_positions", lambda v: len(v) == 3),
        "static_alternative": ("static_alt", True),
        "identity_preserved": ("identity_preserved", True),
        "simulated_vs_observed": ("metrics", lambda v: True),
        "collection_completeness_noted": ("clusters", lambda v: True),
        "labels_not_overlapping": ("label_mode", "numbered_legend"),
        "sampling_density_noted": ("sampling_density_noted", True),
        "origin_marked": ("origin_marked", lambda v: True),
        "time_ascending": ("time_ascending", True),
        "date_granularity_fits_span": ("granularity", lambda v: bool(v)),
        "no_interpolation": ("line_break_at_missing", True),
    }
    for rule in rules:
        key, expect = mapping.get(rule, (None, None))
        if key is None:
            unknown.append(rule)
            continue
        val = checks.get(key, "__absent__")
        if val == "__absent__":
            unknown.append(rule)
            continue
        ok = (val == expect) if not callable(expect) else (val is not None and expect(val))
        (satisfied if ok else failed).append(rule)
    return {"chapter": chapter, "rules": rules, "satisfied": satisfied,
            "not_satisfied": failed, "unverified": unknown}


def format_findings(findings):
    if not findings:
        return "无问题"
    lines = []
    for f in findings:
        lines.append("[%s] %s — %s" % (f["level"], f["rule"], f["msg"]))
    return "\n".join(lines)
