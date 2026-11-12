"""bvkit selftest: 用内置样例跑通全部渲染器并验证 4 个反例被拦截。"""
import json
import os
import sys

import numpy as np

from cli import ALL_RENDERERS, _resolve, cmd_render
from core import setup_style
from review import format_findings, review_spec
from validate import load_table, validate


def _w(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path


def build_samples(wd):
    rng = np.random.default_rng(42)
    os.makedirs(wd, exist_ok=True)
    os.makedirs(os.path.join(wd, "out"), exist_ok=True)
    specs = {}

    # 02 timeseries（含 "2019.3" 年月 + 事件）
    rows = [{"ym": "2019.3", "v": 12}, {"ym": "2020.6", "v": 18}, {"ym": "2021.11", "v": 26},
            {"ym": "2023.2", "v": 34}, {"ym": "2024.8", "v": 43}]
    p = _w(os.path.join(wd, "ts.json"), rows)
    specs["02"] = {"chapter": "02", "out": os.path.join(wd, "out", "bv02"),
                   "title": "自检：规模变化与事件背景", "note": "示例数据",
                   "date_format": "ym", "date_columns": ["ym"],
                   "data": {"path": p}, "formats": ["png", "svg"],
                   "params": {"x": "ym", "series": [{"name": "规模", "y": "v"}],
                              "events": {"col": "ev", "at": "ym", "cat": "cat"}}}
    for r in rows:
        pass

    # 02 带事件列
    out_rows = []
    evs = [("2019.3", "标准发布", "政策"), ("2020.6", "试点落地", "市场"),
           ("2021.11", "接口规范", "政策"), ("2023.2", "规模化", "市场"), ("2024.8", "端侧普及", "技术")]
    for r, (ym, name, cat) in zip(rows, evs):
        out_rows.append({"ym": ym, "v": r["v"], "ev": name, "cat": cat})
    p = _w(os.path.join(wd, "ts_ev.json"), out_rows)
    specs["02"]["data"] = {"path": p}

    # 03 wordcloud
    freq = [{"w": w, "c": c} for w, c in
            [("数据", 300), ("验证", 180), ("方法", 179), ("记录", 150), ("可视化", 140),
             ("案例", 132), ("流程", 128), ("任务", 120), ("解释", 110), ("边界", 96),
             ("口径", 90), ("评审", 86), ("结构", 80), ("缺失", 74), ("标注", 70)]]
    p = _w(os.path.join(wd, "wc.json"), freq)
    specs["03"] = {"chapter": "03", "out": os.path.join(wd, "out", "bv03"),
                   "title": "自检：加权词云 + 核对视图", "note": "示例频次",
                   "data": {"path": p}, "params": {"word": "w", "count": "c", "top": 12}}

    # 04/12/14/15/16 matrix
    cells = []
    for r_ in ["甲", "乙", "丙", "丁"]:
        for c_ in ["东", "南", "西", "北"]:
            cells.append({"row": r_, "col": c_, "v": int(rng.integers(3, 22))})
    p = _w(os.path.join(wd, "matrix.json"), cells)
    specs["12"] = {"chapter": "12", "out": os.path.join(wd, "out", "bv12"),
                   "title": "自检：交叉计数", "note": "示例 n=%d" % sum(c["v"] for c in cells),
                   "data": {"path": p},
                   "params": {"rows": "row", "cols": "col", "value": "v"}}
    for c in cells[:3]:
        c["v"] = None
    p2 = _w(os.path.join(wd, "matrix_missing.json"), cells)
    exp = {"甲|东": 1, "乙|南": 1, "丙|西": 1, "丁|北": 1}
    specs["14"] = {"chapter": "14", "out": os.path.join(wd, "out", "bv14"),
                   "title": "自检：期望 vs 实际（空洞）", "note": "示例",
                   "data": {"path": p2},
                   "params": {"rows": "row", "cols": "col", "value": "v", "expected": exp}}

    specs["16"] = {"chapter": "16", "out": os.path.join(wd, "out", "bv16"),
                   "title": "自检：位置×时段", "note": "示例日志聚合",
                   "data": {"path": p},
                   "params": {"rows": "row", "cols": "col", "value": "v"}}

    # 07 network（两派）
    edges = []
    for i in range(6):
        for j in range(i + 1, 6):
            edges.append({"s": "m%d" % i, "t": "m%d" % j, "w": 2 + (i + j) % 3})
    for i in range(6, 12):
        for j in range(i + 1, 12):
            edges.append({"s": "m%d" % i, "t": "m%d" % j, "w": 2})
    edges.append({"s": "m0", "t": "m6", "w": 1})
    p = _w(os.path.join(wd, "net.json"), edges)
    specs["07"] = {"chapter": "07", "out": os.path.join(wd, "out", "bv07"),
                   "title": "自检：投影网络（两派）", "note": "示例",
                   "data": {"path": p},
                   "params": {"source": "s", "target": "t", "weight": "w", "threshold": 2}}
    specs["10"] = dict(specs["07"], chapter="10", out=os.path.join(wd, "out", "bv10"),
                       title="自检：网络 + 指标联动")

    # 13 smallmultiples（含缺失）
    sm = []
    for cat in ["A", "B", "C"]:
        for mth in range(1, 13):
            if (cat, mth) in [("A", 3), ("B", 7), ("C", 1)]:
                sm.append({"facet": cat, "m": float(mth), "v": None})
            else:
                sm.append({"facet": cat, "m": float(mth), "v": float(40 + mth * 3 + rng.integers(-4, 4))})
    p = _w(os.path.join(wd, "sm.json"), sm)
    specs["13"] = {"chapter": "13", "out": os.path.join(wd, "out", "bv13"),
                   "title": "自检：小倍数（含未采集）", "note": "示例",
                   "data": {"path": p},
                   "params": {"facet": "facet", "x": "m", "y": "v", "ncol": 3}}

    # 06 geo（三航线共起点）
    specs["06"] = {"chapter": "06", "out": os.path.join(wd, "out", "bv06"),
                   "title": "自检：时空轨迹（共起点）", "note": "示例航段",
                   "data": {"rows": []},
                   "params": {"routes": [
                       {"name": "上海→北京→法兰克福", "points": [{"lon": 121.4, "lat": 31.2, "t": 0},
                                                                {"lon": 116.4, "lat": 39.9, "t": 2.2},
                                                                {"lon": 8.6, "lat": 50.1, "t": 10.5}]},
                       {"name": "上海→迪拜→伦敦", "points": [{"lon": 121.4, "lat": 31.2, "t": 0},
                                                            {"lon": 55.3, "lat": 25.2, "t": 8.2},
                                                            {"lon": 0.1, "lat": 51.5, "t": 15.6}]},
                       {"name": "上海→新加坡", "points": [{"lon": 121.4, "lat": 31.2, "t": 0},
                                                         {"lon": 103.8, "lat": 1.35, "t": 5.4}]}]}}

    # 09 scatter
    pts = []
    for cl, (cx, cy) in {"0": (0, 0), "1": (3, 1), "2": (0.5, 3), "稀疏": (-2, -2)}.items():
        n = 12 if cl != "稀疏" else 4
        for _ in range(n):
            pts.append({"x": float(cx + rng.normal(0, 0.35)), "y": float(cy + rng.normal(0, 0.35)),
                        "cl": cl})
    p = _w(os.path.join(wd, "scatter.json"), pts)
    specs["09"] = {"chapter": "09", "out": os.path.join(wd, "out", "bv09"),
                   "title": "自检：相似性地图", "note": "示例投影",
                   "data": {"path": p},
                   "params": {"x": "x", "y": "y", "cluster": "cl", "outlier_labels": ["稀疏"]}}

    # 17 multimodal
    specs["17"] = {"chapter": "17", "out": os.path.join(wd, "out", "bv17"),
                   "title": "自检：视觉—声音映射", "note": "模拟数据",
                   "data": {"rows": []},
                   "params": {"metrics": [{"name": "流量", "value": 72}, {"name": "延迟", "value": 38},
                                          {"name": "错误率", "value": 12}, {"name": "满意度", "value": 65},
                                          {"name": "成本", "value": 44}],
                              "pitch_base": 220, "pitch_gain": 4, "write_wav": True}}

    # 18 volume
    specs["18"] = {"chapter": "18", "out": os.path.join(wd, "out", "bv18"),
                   "title": "自检：体数据三切片", "note": "合成标量场",
                   "data": {"rows": []}, "params": {"grid": 64}}

    # 19 animation
    specs["19"] = {"chapter": "19", "out": os.path.join(wd, "out", "bv19"),
                   "title": "自检：动画 + 静态替代", "note": "合成散点",
                   "data": {"rows": []}, "params": {"points": 40, "frames": 12, "fps": 8}}

    return specs


def check_products(paths):
    """按产物类型设最低体积门槛：位图/矢量/音频/动图/JSON 各不相同。"""
    floors = {".png": 10000, ".svg": 2000, ".pdf": 2000, ".gif": 5000, ".wav": 20000,
              ".json": 200, ".md": 100}
    ok = True
    for p in paths:
        if not os.path.exists(p):
            print("  MISSING %s" % p, file=sys.stderr)
            ok = False
            continue
        ext = os.path.splitext(p)[1].lower()
        size = os.path.getsize(p)
        if size < floors.get(ext, 200):
            print("  TOO_SMALL %s (%d < %d)" % (p, size, floors.get(ext, 200)), file=sys.stderr)
            ok = False
    return ok


def main(workdir="/tmp/bvkit_selftest"):
    wd = workdir
    specs = build_samples(wd)
    style = setup_style(None)
    print("font: %s (%s)" % (style["font_name"], style["font_path"]))
    print("samples: %d chapters -> %s" % (len(specs), wd))

    results, failed = {}, []
    for ch, spec in sorted(specs.items()):
        base = spec["out"]
        try:
            _ch, renderer, rows, meta = _resolve(spec)
            report = None
            if rows:
                report, prepared = validate(rows, spec=spec, meta=meta)
                rows = prepared
                errs = [i for i in report["issues"] if i["level"] == "error"]
                if errs:
                    raise AssertionError("data errors: %s" % errs)
            p = dict(spec.get("params") or {})
            p.setdefault("title", spec.get("title"))
            p.setdefault("note", spec.get("note"))
            if renderer == "wordcloud":
                p.setdefault("font_path", style["font_path"])
            fig, audit = ALL_RENDERERS[renderer](rows, p, spec, meta)
            if report:
                from validate import to_audit_checks
                audit["checks"].update(to_audit_checks(report))
            from core import export, write_audit
            written = export(fig, base, formats=spec.get("formats") or ["png"])
            write_audit(audit, base)
            extra = [x for x in (audit.get("dropped") or []) if x.startswith(("wav:", "gif:"))]
            audit_path = base + ".audit.json"
            files = written + [audit_path] + [os.path.join(wd, "out", e.split(":")[1].strip())
                                              for e in extra]
            ok = check_products(files)
            results[ch] = {"renderer": renderer, "ok": ok,
                           "files": [os.path.basename(f) for f in files],
                           "checks": audit.get("checks")}
            if not ok:
                failed.append(ch)
            print("  [%s] %-14s %s" % ("PASS" if ok else "FAIL", renderer,
                                       ", ".join(os.path.basename(f) for f in files)))
        except Exception as e:
            failed.append(ch)
            results[ch] = {"renderer": None, "ok": False, "error": str(e)}
            print("  [FAIL] chapter %s: %s" % (ch, e))

    # ---------------- 反例：必须被拦截
    print("\nnegative checks:")
    neg = {}

    # N1: "2019.3" 未被声明时仍应识别为年月（不能当小数）
    rows = [{"ym": "2019.3", "v": "1"}, {"ym": "2019.11", "v": "2"}, {"ym": "2020.2", "v": "3"}]
    rep, prep = validate(rows, spec={"date_columns": ["ym"]})
    ym_col = [c for c in rep["columns"] if c["name"] == "ym"][0]
    neg["ym_parsed_not_decimal"] = ym_col["kind"] == "period_ym" and abs(prep[1]["ym"] - (2019 + 10 / 12.0)) < 1e-6
    print("  [%s] 2019.11 解析为 %.4f（期望 %.4f，非 2019.11）" % (
        "PASS" if neg["ym_parsed_not_decimal"] else "FAIL",
        prep[1]["ym"], 2019 + 10 / 12.0))

    # N2: 关基线且无理由 -> review 必须报 error
    f = review_spec({"chapter": "02", "out": "x", "title": "t", "note": "示例",
                     "data": {"rows": []}, "params": {"zero_baseline": False}})
    neg["baseline_blocked"] = any(x["rule"] == "no_truncated_baseline" and x["level"] == "error" for x in f)
    print("  [%s] 关闭 0 基线被拦截" % ("PASS" if neg["baseline_blocked"] else "FAIL"))

    # N3: 双轴 -> error
    f = review_spec({"chapter": "01", "out": "x", "title": "t", "note": "示例",
                     "data": {"rows": []}, "params": {"dual_axis": True}})
    neg["dual_axis_blocked"] = any(x["rule"] == "no_dual_axis" and x["level"] == "error" for x in f)
    print("  [%s] 双 y 轴被拦截" % ("PASS" if neg["dual_axis_blocked"] else "FAIL"))

    # N4: 缺失格不补零（matrix 的 audit 必须报 missing）
    a14 = results.get("14", {}).get("checks") or {}
    neg["missing_not_zeroed"] = a14.get("missing_not_zeroed") is True and a14.get("missing_cells", 0) > 0
    print("  [%s] 缺失格未补零（holes=%s, missing=%s）" % (
        "PASS" if neg["missing_not_zeroed"] else "FAIL",
        a14.get("holes"), a14.get("missing_cells")))

    # N5: 时间轴正序 + 日期粒度（geo/ts 的 audit 应记录）
    a02 = results.get("02", {}).get("checks") or {}
    neg["date_declared"] = a02.get("date_columns", 0) >= 1
    print("  [%s] 时间列口径已记录（date_columns=%s）" % (
        "PASS" if neg["date_declared"] else "FAIL", a02.get("date_columns")))

    all_ok = (not failed) and all(neg.values())
    summary = {"workdir": wd, "chapters": results, "negative": neg,
               "failed": failed, "pass": all_ok}
    with open(os.path.join(wd, "selftest.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\nresult: %s (%d chapters, %d failed)" % ("PASS" if all_ok else "FAIL",
                                                     len(results), len(failed)))
    print("summary: %s" % os.path.join(wd, "selftest.json"))
    return 0 if all_ok else 1
