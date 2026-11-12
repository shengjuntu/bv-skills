"""bvkit renderers (extended): 相似性散布图、词云（可选依赖）。"""
import os

import numpy as np

from core import BVSpecError, new_audit


def render_scatter(rows, p, spec, meta):
    """相似性地图：二维投影 + 簇编码 + 稀疏/异常点单独标注（bv-09）。"""
    import matplotlib.pyplot as plt
    x, y, c = p.get("x"), p.get("y"), p.get("cluster")
    if not (x and y):
        raise BVSpecError("scatter needs params.x/y")
    clusters = sorted({str(r.get(c, "-")) for r in rows}) if c else ["-"]
    fig, ax = plt.subplots(figsize=(9.6, 6.0))
    for i, cl in enumerate(clusters):
        pts = [(r[x], r[y]) for r in rows if str(r.get(c, "-")) == cl]
        pts = [(a, b) for a, b in pts if isinstance(a, float) and isinstance(b, float)]
        if not pts:
            continue
        xs, ys = zip(*pts)
        label = cl + ("（稀疏/异常）" if p.get("outlier_labels") and cl in p.get("outlier_labels", []) else "")
        ax.scatter(xs, ys, s=48, color=("#9aa5ad" if "稀疏" in label else None) or ["#1f4e79", "#2e7d32", "#b7791f", "#9c4a1a", "#6a3d9a"][i % 5],
                   label="%s（%d）" % (label, len(pts)), alpha=0.88)
    ax.set_xlabel(p.get("x_label", "维度1（示意）"))
    ax.set_ylabel(p.get("y_label", "维度2（示意）"))
    ax.set_title(p.get("title") or "相似性地图", loc="left", fontsize=11)
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    checks = {"clusters": len(clusters), "points": len(rows), "axes_labelled": True}
    audit = new_audit(chapter=spec.get("chapter"), renderer="scatter",
                      data_source=(meta or {}).get("path") or "inline", n_records=len(rows),
                      checks=checks,
                      limits=["投影坐标为二维示意，未跑真实 embedding；轴标签已写明"],
                      params={"x": x, "y": y, "cluster": c})
    return fig, audit


def render_wordcloud(rows, p, spec, meta):
    """加权词云 + 数值核对视图（bv-03）。需 wordcloud 库。"""
    import matplotlib.pyplot as plt
    try:
        from wordcloud import WordCloud
    except ImportError as e:
        raise BVSpecError("wordcloud renderer needs the 'wordcloud' package: %s" % e)
    wc_col, n_col = p.get("word"), p.get("count")
    if not (wc_col and n_col):
        raise BVSpecError("wordcloud needs params.word/count")
    freq = {str(r[wc_col]): float(r[n_col]) for r in rows if isinstance(r.get(n_col), float)}
    top = sorted(freq.items(), key=lambda kv: -kv[1])[: int(p.get("top", 15))]
    total = sum(freq.values()) or 1
    wc = WordCloud(font_path=p.get("font_path"), width=int(p.get("width", 1600)),
                   height=int(p.get("height", 1000)), max_words=int(p.get("max_words", 120)),
                   prefer_horizontal=0.9, colormap=p.get("colormap", "viridis"),
                   background_color="white", random_state=42).generate_from_frequencies(freq)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.2), gridspec_kw={"width_ratios": [1.35, 1]})
    a1.imshow(wc, interpolation="bilinear")
    a1.axis("off")
    a1.set_title("词云（max_words=%d，布局 seed=42）" % p.get("max_words", 120), fontsize=10, loc="left")
    labels = [k for k, _ in top][::-1]
    vals = [v for _, v in top][::-1]
    a2.barh(labels, vals, color="#1f4e79")
    for i, v in enumerate(vals):
        a2.text(v + max(0.5, v * 0.01), i, "%d（%.2f%%）" % (v, 100.0 * v / total), va="center", fontsize=7.5)
    a2.set_title("核对视图：Top-%d 原始频次与占比（总量 %.0f）" % (len(top), total), fontsize=10, loc="left")
    a2.set_xlabel("原始频次")
    fig.tight_layout()
    checks = {"unique_words": len(freq), "tokens": int(total), "layout_seed": 42,
              "checklist_panel": True}
    audit = new_audit(chapter=spec.get("chapter"), renderer="wordcloud",
                      data_source=(meta or {}).get("path") or "inline", n_records=len(freq),
                      checks=checks,
                      limits=["词云不可跨语料比较相对频率；顶部词序以右侧核对面板为准"],
                      params={"top": len(top), "total": int(total)})
    return fig, audit
