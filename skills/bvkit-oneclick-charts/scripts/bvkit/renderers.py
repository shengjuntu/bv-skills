"""bvkit renderers: 6 个图元族，8 个渲染函数。

所有渲染器返回 (fig, audit)。审计里的口径项（0 基线、无双轴、缺失已标注、种子固定）是硬性默认，
不是可选装饰——这是与通用绘图库的差别。
"""
import os
import wave

import numpy as np

from .core import BVError, BVSpecError, color, new_audit
from .validate import parse_period

SEED = 42


def _seed():
    rng = np.random.default_rng(SEED)
    np.random.seed(SEED)
    return rng


# ---------------------------------------------------------------- timeseries
def render_timeseries(rows, p, spec, meta):
    import matplotlib.pyplot as plt
    _seed()
    xcol = p.get("x")
    if not xcol:
        raise BVSpecError("timeseries needs params.x")
    xs = [r.get(xcol) for r in rows]
    if any(x is None for x in xs):
        raise BVSpecError("x column %r has unparsed values" % xcol)
    series = p.get("series")
    if not series:
        series = [{"name": c, "y": c} for c in rows[0].keys()
                  if c != xcol and isinstance(rows[0].get(c), float)]
    fig, axes = plt.subplots(2 if p.get("events") else 1, 1,
                             figsize=(11.6 if p.get("events") else 9.2, 7.0 if p.get("events") else 4.6),
                             squeeze=False, sharex=True,
                             gridspec_kw={"height_ratios": [1.15, 1]} if p.get("events") else None)
    ax1 = axes[0][0]
    checks = {"zero_baseline": bool(p.get("zero_baseline", True)), "dual_axis": False,
              "deterministic": True, "missing_marks": False,
              "time_ascending": all(xs[i] < xs[i + 1] for i in range(len(xs) - 1)),
              "granularity": "%d 点 / %.2f 年" % (len(xs), max(xs) - min(xs))}
    for i, s in enumerate(series):
        ys = [r.get(s["y"]) for r in rows]
        ax1.plot(xs, ys, color=color(i), lw=2.2, marker="o", ms=4, label=s.get("name") or s["y"])
        if p.get("label_points", True):
            for xx, yy in [(xs[0], ys[0]), (xs[-1], ys[-1])]:
                ax1.annotate("%.0f" % yy if abs(yy) >= 1 else "%.2f" % yy, (xx, yy),
                             textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    if checks["zero_baseline"]:
        ax1.set_ylim(bottom=0)
    else:
        spans = [[r.get(s["y"]) for r in rows] for s in series]
        lo, hi = min(min(v) for v in spans), max(max(v) for v in spans)
        pad = (hi - lo) * 0.15 or 1
        ax1.set_ylim(lo - pad, hi + pad)
    ax1.set_ylabel(p.get("y_label", ""))
    ax1.set_title(p.get("title") or spec.get("title") or "时间序列", loc="left", fontsize=11.5)
    if len(series) > 1:
        ax1.legend(fontsize=8)
    aud_dropped, aud_limits = [], []
    if p.get("events"):
        ev = p["events"]
        ax2 = axes[1][0]
        cats = sorted({str(r.get(ev.get("cat") or "cat", "事件")) for r in rows if r.get(ev["col"])})
        cat_y = {c: 0.75 - i * (0.62 / max(1, len(cats) - 1 or 1)) for i, c in enumerate(cats)}
        handles = []
        for i, c in enumerate(cats):
            handles.append(plt.Line2D([], [], marker="o", ls="", color=color(i), label=c))
        for r in rows:
            if not r.get(ev["col"]):
                continue
            xx = parse_period(r.get(ev.get("at") or xcol))
            if xx is None:
                aud_dropped.append("事件 %r 时间不可解析" % r.get(ev["col"]))
                continue
            cat = str(r.get(ev.get("cat") or "cat", "事件") or "事件")
            ax2.scatter(xx, cat_y.get(cat, 0.3), s=90, color=color(cats.index(cat)), zorder=3)
            ax2.annotate(str(r[ev["col"]]), (xx, cat_y.get(cat, 0.3)), textcoords="offset points",
                         xytext=(0, 11), ha="center", fontsize=7.2)
        ax2.set_yticks(list(cat_y.values()))
        ax2.set_yticklabels(list(cat_y.keys()), fontsize=8)
        ax2.set_ylim(-0.12, 1.0)
        ax2.set_title(p.get("events_title", "背景事件（位置=真实时间，颜色=类别）"), loc="left", fontsize=10.5)
        ax2.legend(handles=handles, loc="upper right", ncol=len(cats), fontsize=8)
        aud_limits.append("事件面板仅展示 %d 条已解析事件" % sum(1 for r in rows if r.get(ev["col"])))
    fig.tight_layout()
    audit = new_audit(chapter=spec.get("chapter"), renderer="timeseries",
                      data_source=(meta or {}).get("path") or "inline",
                      n_records=len(rows), checks=checks, dropped=aud_dropped,
                      limits=aud_limits + ["无 y 轴双轴；无平滑插值"],
                      params={k: v for k, v in p.items() if k in ("x", "zero_baseline", "label_points")})
    return fig, audit


# ---------------------------------------------------------------- matrix
def render_matrix(rows, p, spec, meta):
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    _seed()
    rcol, ccol, vcol = p.get("rows"), p.get("cols"), p.get("value")
    if not (rcol and ccol and vcol):
        raise BVSpecError("matrix needs params.rows/cols/value")
    rl = sorted({str(r[rcol]) for r in rows}, key=_natural_key)
    cl = sorted({str(r[ccol]) for r in rows}, key=_natural_key)
    M = np.full((len(rl), len(cl)), np.nan)
    for r in rows:
        v = r.get(vcol)
        if isinstance(v, (int, float)):
            M[rl.index(str(r[rcol])), cl.index(str(r[ccol]))] = float(v)
    expected = p.get("expected")
    n_panels = 2 if expected else 1
    fig, axes = plt.subplots(1, n_panels, figsize=(5.6 * n_panels + 2.4, 5.4), squeeze=False)
    ax = axes[0][0]
    im = ax.imshow(M, cmap=p.get("cmap", "YlOrBr"))
    for i in range(len(rl)):
        for j in range(len(cl)):
            if np.isnan(M[i, j]):
                ax.text(j, i, "缺失", ha="center", va="center", fontsize=7, color="#777777")
            else:
                ax.text(j, i, ("%g" % M[i, j]), ha="center", va="center", fontsize=8.2)
    ax.set_xticks(range(len(cl)))
    ax.set_xticklabels(cl, rotation=35, ha="right", fontsize=8.5)
    ax.set_yticks(range(len(rl)))
    ax.set_yticklabels(rl, fontsize=8.5)
    ax.set_title(p.get("title") or "实际覆盖", loc="left", fontsize=10)
    div = make_axes_locatable(ax)
    cax = div.append_axes("right", size="3.5%", pad=0.12)
    plt.colorbar(im, cax=cax)
    missing = int(np.isnan(M).sum())
    checks = {"missing_cells": missing, "missing_not_zeroed": True, "deterministic": True,
              "expected_actual_pair": bool(expected)}
    holes = []
    if expected:
        E = np.zeros_like(M)
        for i, r in enumerate(rl):
            for j, c in enumerate(cl):
                key = "%s|%s" % (r, c)
                E[i, j] = 1.0 if expected.get(key, 0) else 0.0
        ax2 = axes[0][1]
        from matplotlib.colors import ListedColormap
        ax2.imshow(E, cmap=ListedColormap(["#ffffff", "#2e7d32"]), vmin=0, vmax=1)
        for i, r in enumerate(rl):
            for j, c in enumerate(cl):
                if E[i, j] and np.isnan(M[i, j]):
                    holes.append((r, c))
                    ax2.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                                edgecolor="#c23b22", lw=2.0))
                    ax2.text(j, i, "空洞", ha="center", va="center", fontsize=7.5, color="#c23b22")
        ax2.set_xticks(range(len(cl)))
        ax2.set_xticklabels(cl, rotation=35, ha="right", fontsize=8.5)
        ax2.set_yticks(range(len(rl)))
        ax2.set_yticklabels(rl, fontsize=8.5)
        ax2.set_title("期望关系（红框=实际空洞）", loc="left", fontsize=10)
        checks["holes"] = len(holes)
    fig.tight_layout()
    audit = new_audit(chapter=spec.get("chapter"), renderer="matrix",
                      data_source=(meta or {}).get("path") or "inline", n_records=len(rows),
                      checks=checks, missing=["缺失格按文字标注，未补零（%d 格）" % missing] if missing else [],
                      limits=["色阶与会话字体无关，灰度可分"],
                      params={"rows": rcol, "cols": ccol, "value": vcol})
    if holes:
        audit["dropped"] = ["实际空洞：%s→%s" % (a, b) for a, b in holes]
    return fig, audit


def _natural_key(s):
    import re
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(s))]


# ---------------------------------------------------------------- network
def render_network(rows, p, spec, meta):
    import networkx as nx
    import matplotlib.pyplot as plt
    _seed()
    s, t, w = p.get("source"), p.get("target"), p.get("weight")
    if not (s and t):
        raise BVSpecError("network needs params.source/target")
    G = nx.Graph()
    for r in rows:
        a, b = str(r[s]), str(r[t])
        val = r.get(w) if w else 1
        if isinstance(val, (int, float)):
            G.add_edge(a, b, weight=float(val))
    checks = {"nodes": G.number_of_nodes(), "edges": G.number_of_edges(), "seed": SEED,
              "layout": p.get("layout", "kamada_kawai"), "threshold_set": bool(p.get("threshold"))}
    dropped = []
    thr = p.get("threshold")
    if thr:
        keep = [(a, b, d) for a, b, d in G.edges(data=True) if d["weight"] >= thr]
        G2 = nx.Graph()
        G2.add_nodes_from(G.nodes())
        for a, b, _d in keep:
            G2.add_edge(a, b)
        dropped.append("阈值 %.2f 过滤掉 %d 条边" % (thr, G.number_of_edges() - G2.number_of_edges()))
        G = G2
        checks["edges_after_threshold"] = G.number_of_edges()
    iso = [n for n in G.nodes() if G.degree(n) == 0]
    core = G.subgraph([n for n in G.nodes() if n not in iso])
    fig, ax = plt.subplots(figsize=(9.4, 6.2))
    if len(core) > 1:
        pos = (nx.kamada_kawai_layout(core) if p.get("layout", "kamada_kawai") == "kamada_kawai"
               else nx.circular_layout(core))
        nx.draw_networkx_edges(core, pos, ax=ax, edge_color="#6b8aa6", width=1.2)
        nx.draw_networkx_nodes(core, pos, ax=ax, node_color="#9ecae1", node_size=170,
                               edgecolors="#1f4e79", linewidths=0.8)
        nx.draw_networkx_labels(core, pos, ax=ax, font_size=7.2, font_color="#0b2b3d")
    for k, n in enumerate(iso):
        ax.scatter([1.32], [0.55 - k * 0.13], s=110, c="#9aa5ad", edgecolors="#666666")
        ax.text(1.39, 0.55 - k * 0.13, "%s（孤立）" % n, fontsize=6.8, va="center")
    ax.set_xlim(-1.2, 2.0 if iso else 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.axis("off")
    ax.set_title(p.get("title") or "相似/共现网络", loc="left", fontsize=11)
    ax.text(0.0, -0.06, "节点 %d · 边 %d · 阈值 %s · 布局 %s" % (
        G.number_of_nodes(), G.number_of_edges(), thr if thr else "未设",
        p.get("layout", "kamada_kawai")), transform=ax.transAxes, fontsize=8, color="#555555")
    fig.tight_layout()
    if iso:
        dropped.append("%d 个 0 度节点单列在右侧，未混入布局" % len(iso))
    audit = new_audit(chapter=spec.get("chapter"), renderer="network",
                      data_source=(meta or {}).get("path") or "inline", n_records=len(rows),
                      checks=checks, dropped=dropped,
                      limits=["边宽未编码权重（权重仅用于阈值）"] if not p.get("width_by_weight") else [],
                      params={"threshold": thr, "layout": p.get("layout", "kamada_kawai")})
    return fig, audit


# ---------------------------------------------------------------- smallmultiples
def render_smallmultiples(rows, p, spec, meta):
    import matplotlib.pyplot as plt
    _seed()
    facet, x, y = p.get("facet"), p.get("x"), p.get("y")
    if not (facet and x and y):
        raise BVSpecError("smallmultiples needs params.facet/x/y")
    cats = sorted({str(r[facet]) for r in rows}, key=_natural_key)
    ncol = int(p.get("ncol", 3))
    nrow = int(np.ceil(len(cats) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.5 * ncol, 3.0 * nrow + 0.6),
                             sharey=True, sharex=True, squeeze=False)
    missing_pts, shown, miss_by_cat = [], 0, {}
    for k, c in enumerate(cats):
        ax = axes[k // ncol][k % ncol]
        seq = [(r[x], r[y] if isinstance(r.get(y), float) else float("nan"))
               for r in rows if str(r[facet]) == c and isinstance(r.get(x), float)]
        seq.sort()
        if seq:
            xs, ys = zip(*seq)
            # nan 让折线在未采集处断开，而不是跨点直连（避免视觉插值）
            ax.plot(xs, ys, lw=1.8, color="#1f4e79", marker="o", ms=3)
        miss = [(r[x], r[y]) for r in rows if str(r[facet]) == c and not isinstance(r.get(y), float)]
        for a, _b in miss:
            ax.axvline(a, color="#bbbbbb", ls=":", lw=1.2, zorder=1)
            missing_pts.append((c, a))
        if miss:
            miss_by_cat[c] = [("%g" % a) for a, _ in miss]
            ax.text(0.02, 0.94, "未采集：%s" % "、".join(miss_by_cat[c]), transform=ax.transAxes,
                    fontsize=7, color="#777777", va="top")
        ax.set_title("%s%s" % (c, "（含未采集）" if miss else ""), fontsize=9)
        shown += 1
    for k in range(len(cats), nrow * ncol):
        axes[k // ncol][k % ncol].axis("off")
    fig.suptitle(p.get("title") or "小倍数", x=0.01, ha="left", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    checks = {"facets": len(cats), "missing_cells": len(missing_pts), "no_zero_fill": True,
              "missing_not_zeroed": True, "line_break_at_missing": True, "shared_axis": True}
    audit = new_audit(chapter=spec.get("chapter"), renderer="smallmultiples",
                      data_source=(meta or {}).get("path") or "inline", n_records=len(rows),
                      checks=checks,
                      missing=["%s @ %s 未采集（灰 x，不补零）" % (c, a) for c, a in missing_pts],
                      limits=["所有分面共享 y 轴范围以便比较"],
                      params={"facet": facet, "x": x, "y": y, "ncol": ncol})
    return fig, audit


# ---------------------------------------------------------------- geo
def render_geo(rows, p, spec, meta):
    import matplotlib.pyplot as plt
    _seed()
    routes = p.get("routes")
    if not routes:
        raise BVSpecError("geo needs params.routes")
    fig = plt.figure(figsize=(12, 7.2))
    axm = fig.add_subplot(2, 1, 1)
    all_lon = [q["lon"] for rt in routes for q in rt["points"]]
    all_lat = [q["lat"] for rt in routes for q in rt["points"]]
    axm.set_xlim(min(all_lon) - 12, max(all_lon) + 14)
    axm.set_ylim(min(all_lat) - 12, max(all_lat) + 16)
    dur_labels = []
    for i, rt in enumerate(routes):
        xs = [q["lon"] for q in rt["points"]]
        ys = [q["lat"] for q in rt["points"]]
        ts = [q.get("t", 0) for q in rt["points"]]
        axm.plot(xs, ys, lw=2.0, color=color(i))
        axm.scatter(xs, ys, c=ts, cmap="plasma", s=105, zorder=3, edgecolor="white", linewidth=1.1)
        axm.annotate(str(i + 1), (xs[-1], ys[-1]), textcoords="offset points", xytext=(9, 5),
                     fontsize=13)
        dur_labels.append("%d  %s（%.1fh，%d 采样点）" % (i + 1, rt["name"], ts[-1], len(ts)))
    # 共起点只标一次（避免多条航线的起点标签互相覆盖）
    firsts = [(round(rt["points"][0]["lon"], 1), round(rt["points"][0]["lat"], 1)) for rt in routes]
    if len(set(firsts)) == 1:
        ox, oy = firsts[0]
        axm.scatter([ox], [oy], marker="*", s=320, color="#222222", zorder=4)
        axm.annotate(p.get("origin_label", "共起点"), (ox, oy), textcoords="offset points",
                     xytext=(-4, -26), ha="center", fontsize=9,
                     bbox=dict(boxstyle="round,pad=0.25", fc="#f2f2f2", ec="#999999", lw=0.8))
    axm.text(0.985, 0.97, "\n".join(dur_labels), transform=axm.transAxes, fontsize=8,
             va="top", ha="right", bbox=dict(boxstyle="round,pad=0.35", fc="white",
                                            ec="#cccccc", lw=0.8))
    axm.set_xlabel("经度")
    axm.set_ylabel("纬度")
    axm.set_title(p.get("title") or "时空轨迹（地图仅标编号，全名见图例）", loc="left", fontsize=11)
    axb = fig.add_subplot(2, 1, 2)
    for i, rt in enumerate(routes):
        ts = [q.get("t", 0) for q in rt["points"]]
        axb.plot(ts, [i] * len(ts), marker="o", ms=8, lw=0, color=color(i))
    axb.set_yticks(range(len(routes)))
    axb.set_yticklabels([chr(0x2460 + i) for i in range(len(routes))], fontsize=11)
    axb.set_xlabel("时长（小时）")
    axb.set_title("时间轴核对：仅起/中转/终点采样", loc="left", fontsize=10)
    fig.tight_layout()
    checks = {"routes": len(routes), "label_mode": "numbered_legend",
              "sampling_points": sum(len(rt["points"]) for rt in routes),
              "sampling_density_noted": True,
              "origin_marked": len(set(firsts)) == 1}
    audit = new_audit(chapter=spec.get("chapter"), renderer="geo",
                      data_source=(meta or {}).get("path") or "inline",
                      n_records=sum(len(rt["points"]) for rt in routes), checks=checks,
                      limits=["只有端点/中转采样，轨迹密度不足，未插值"],
                      params={"routes": len(routes)})
    return fig, audit


# ---------------------------------------------------------------- volume
def render_volume(rows, p, spec, meta):
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    _seed()
    n = int(p.get("grid", 64))
    g = np.linspace(0, 1, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    peaks = p.get("peaks") or [{"c": [0.46, 0.5, 0.5], "s": 0.14, "a": 1.0},
                               {"c": [0.72, 0.3, 0.68], "s": 0.10, "a": 0.55}]
    F = np.zeros_like(X)
    for pk in peaks:
        c = pk["c"]
        F += pk.get("a", 1.0) * np.exp(-((X - c[0]) ** 2 + (Y - c[1]) ** 2 + (Z - c[2]) ** 2) / (2 * pk["s"] ** 2))
    idx = [int(round(pk["c"][k] * (n - 1))) for pk in peaks for k in range(3)]
    slices = [("x=%.2f" % peaks[0]["c"][0], F[int(peaks[0]["c"][0] * (n - 1)), :, :]),
              ("y=%.2f" % peaks[1]["c"][1], F[:, int(peaks[1]["c"][1] * (n - 1)), :]),
              ("z=%.2f" % peaks[1]["c"][2], F[:, :, int(peaks[1]["c"][2] * (n - 1))])]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.9))
    vmax = float(F.max())
    for ax, (name, sl) in zip(axes, slices):
        im = ax.imshow(sl, cmap=p.get("cmap", "inferno"), origin="lower", extent=[0, 1, 0, 1],
                       vmin=0.0, vmax=vmax)
        ax.set_title(name, fontsize=9.5)
        ax.set_xlabel("归一化坐标", fontsize=8)
        ax.set_ylabel("归一化坐标", fontsize=8)
        div = make_axes_locatable(ax)
        cax = div.append_axes("right", size="4%", pad=0.1)
        plt.colorbar(im, cax=cax)
    fig.suptitle(p.get("title") or "体数据正交切片", x=0.01, ha="left", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    checks = {"grid": "%d^3" % n, "slices": 3, "colorbar": True, "params_recorded": True,
              "slice_positions": [nm for nm, _ in slices], "shared_value_range": True}
    audit = new_audit(chapter=spec.get("chapter"), renderer="volume",
                      data_source="synthetic gaussian field", n_records=n ** 3, checks=checks,
                      limits=["合成标量场，非真实影像；未做独立重建验证"],
                      params={"grid": n, "peaks": peaks})
    return fig, audit


# ---------------------------------------------------------------- multimodal
def render_multimodal(rows, p, spec, meta):
    import matplotlib.pyplot as plt
    _seed()
    metrics = p.get("metrics") or [{"name": r.get("name"), "value": r.get("value")} for r in rows]
    base = float(p.get("pitch_base", 220.0))
    gain = float(p.get("pitch_gain", 4.0))
    pitch = [base + gain * m["value"] for m in metrics]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5))
    ys = range(len(metrics))
    a1.barh(list(ys), [m["value"] for m in metrics], color="#2a6f97")
    a1.set_yticks(list(ys))
    a1.set_yticklabels([m["name"] for m in metrics], fontsize=9)
    for i, m in enumerate(metrics):
        a1.text(m["value"] + max(1, m["value"] * 0.01), i, "%g" % m["value"], va="center", fontsize=8)
    a1.set_title("(a) 视觉编码：指标值", loc="left", fontsize=10)
    a2.barh(list(ys), pitch, color="#9c4a1a")
    a2.set_yticks(list(ys))
    a2.set_yticklabels([m["name"] for m in metrics], fontsize=9)
    for i, f in enumerate(pitch):
        a2.text(f + max(2, f * 0.005), i, "%dHz" % f, va="center", fontsize=8)
    a2.set_title("(b) 声音映射：同一数值→音高", loc="left", fontsize=10)
    a2.set_xlabel("频率 Hz")
    fig.suptitle(p.get("title") or "视觉—声音互补映射", x=0.01, ha="left", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    wav_path, frames = None, 0
    if p.get("write_wav"):
        sr = int(p.get("sample_rate", 22050))
        seg = []
        for f in pitch:
            t = np.arange(int(sr * 0.35)) / sr
            seg.append(0.5 * np.sin(2 * np.pi * f * t) * np.hanning(len(t)))
            seg.append(np.zeros(int(sr * 0.08)))
        sig = np.concatenate(seg)
        wav_path = os.path.splitext(spec["out"])[0] + ".wav"
        os.makedirs(os.path.dirname(os.path.abspath(wav_path)), exist_ok=True)
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes((sig * 32767).astype(np.int16).tobytes())
        frames = len(sig)
    checks = {"metrics": len(metrics), "pitch_range": "%d-%dHz" % (min(pitch), max(pitch)),
              "wav": bool(wav_path)}
    audit = new_audit(chapter=spec.get("chapter"), renderer="multimodal",
                      data_source=(meta or {}).get("path") or "inline", n_records=len(metrics),
                      checks=checks,
                      limits=["合成正弦音，非真实听觉设计；未做盲听辨识测试"],
                      params={"pitch_base": base, "pitch_gain": gain, "frames": frames})
    if wav_path:
        audit["dropped"] = ["wav: %s" % os.path.basename(wav_path)]
    return fig, audit


# ---------------------------------------------------------------- animation
def render_animation(rows, p, spec, meta):
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    rng = _seed()
    n = int(p.get("points", 40))
    frames = int(p.get("frames", 12))
    x0 = rng.normal(0, 1, n)
    y0 = 0.5 * x0 + rng.normal(0, 0.5, n)
    dx = float(p.get("dx", 1.4))
    dy = float(p.get("dy", 0.6))
    fig_a, ax_a = plt.subplots(figsize=(8.6, 4.6), dpi=110)
    xlim = (min(x0) - 1.5, max(x0) + dx + 1.5)
    ylim = (min(y0) - 1.5, max(y0) + dy + 1.5)

    def upd(f):
        ax_a.clear()
        k = f / max(1, frames - 1)
        ax_a.scatter(x0 * (1 - k) + (x0 + dx) * k, y0 * (1 - k) + (y0 + dy) * k,
                     c="#2a6f97", s=28, alpha=0.85)
        ax_a.set_xlim(*xlim)
        ax_a.set_ylim(*ylim)
        ax_a.set_title("第 %d/%d 帧（同色同大小=身份保持）" % (f + 1, frames), fontsize=9)
        ax_a.grid(color="#eeeeee", lw=0.5)

    gif_path = os.path.splitext(spec["out"])[0] + ".gif"
    os.makedirs(os.path.dirname(os.path.abspath(gif_path)), exist_ok=True)
    anim = FuncAnimation(fig_a, upd, frames=frames, interval=120)
    anim.save(gif_path, writer=PillowWriter(fps=int(p.get("fps", 8))))
    plt.close(fig_a)
    fig_b, (b1, b2) = plt.subplots(1, 2, figsize=(11, 4.4))
    b1.scatter(x0, y0, c="#2a6f97", s=28)
    b1.set_title("静态替代：起始帧", fontsize=9)
    b2.scatter(x0 + dx, y0 + dy, c="#2a6f97", s=28)
    b2.set_title("静态替代：结束帧", fontsize=9)
    for b in (b1, b2):
        b.set_xlim(*xlim)
        b.set_ylim(*ylim)
        b.grid(color="#eeeeee", lw=0.5)
    fig_b.tight_layout()
    checks = {"frames": frames, "identity_preserved": True, "static_alt": True, "axis_fixed": True}
    audit = new_audit(chapter=spec.get("chapter"), renderer="animation",
                      data_source="synthetic scatter", n_records=n, checks=checks,
                      limits=["动画仅展示单一位移过程；静态替代可独立回答同一问题"],
                      params={"points": n, "frames": frames, "fps": p.get("fps", 8)})
    audit["dropped"] = ["gif: %s" % os.path.basename(gif_path)]
    return fig_b, audit


RENDERERS = {
    "timeseries": render_timeseries,
    "matrix": render_matrix,
    "network": render_network,
    "smallmultiples": render_smallmultiples,
    "geo": render_geo,
    "volume": render_volume,
    "multimodal": render_multimodal,
    "animation": render_animation,
}
