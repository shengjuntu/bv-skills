"""bvkit core: errors, fonts, palette, audit, export."""
import json
import os
import sys

VERSION = "2.1.0"


class BVError(Exception):
    code = "BV_ERROR"


class BVFontError(BVError):
    code = "BV_FONT"


class BVDataError(BVError):
    code = "BV_DATA"


class BVSpecError(BVError):
    code = "BV_SPEC"


# ---------------------------------------------------------------- fonts
CANDIDATE_FONTS = [
    os.path.expanduser("~/.local/share/fonts/wqy-microhei.ttc"),
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]


def resolve_font(explicit=None):
    """Return (path, font_name). Raises BVFontError instead of silently tofu."""
    from matplotlib import font_manager
    cands = ([explicit] if explicit else []) + CANDIDATE_FONTS
    for p in cands:
        if p and os.path.exists(p):
            font_manager.fontManager.addfont(p)
            return p, font_manager.FontProperties(fname=p).get_name()
    raise BVFontError(
        "no CJK font found; bvkit refuses to render (would produce tofu boxes). "
        "install one (e.g. apt-get install fonts-wqy-microhei) or pass font=/path/to/font.ttc"
    )


def setup_style(font_path=None, dpi=140):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    path, name = resolve_font(font_path)
    plt.rcParams.update({
        "font.family": name,
        "font.weight": "normal",
        "axes.titleweight": "normal",
        "axes.labelweight": "normal",
        "axes.unicode_minus": False,
        "figure.dpi": dpi,
        "savefig.dpi": dpi,
        "axes.edgecolor": "#555555",
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": "#e8e8e8",
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    })
    return {"font_path": path, "font_name": name}


# ---------------------------------------------------------------- palette
# 色觉友好（Okabe-Ito 变体），并保证灰度可分离
PALETTE = ["#1f4e79", "#2e7d32", "#b7791f", "#9c4a1a", "#6a3d9a", "#0f7b6c", "#7a7a7a", "#c23b22"]


def color(i):
    return PALETTE[i % len(PALETTE)]


# ---------------------------------------------------------------- audit
REQUIRED_AUDIT_FIELDS = [
    "chapter", "renderer", "output", "data_source", "n_records",
    "checks", "dropped", "missing", "params", "limits",
]


def new_audit(**kw):
    a = {k: kw.get(k) for k in REQUIRED_AUDIT_FIELDS}
    for k, v in kw.items():
        a.setdefault(k, v)
    a.setdefault("checks", {})
    a.setdefault("dropped", [])
    a.setdefault("missing", [])
    a.setdefault("limits", [])
    return a


def write_audit(audit, out_base, fmt="json"):
    """audit sidecar next to the image: <out>.audit.json + <out>.audit.md"""
    path = out_base + ".audit.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    md = out_base + ".audit.md"
    lines = ["# bvkit audit", "", "| 字段 | 值 |", "| --- | --- |"]
    for k in ["chapter", "renderer", "output", "data_source", "n_records"]:
        lines.append("| %s | %s |" % (k, audit.get(k)))
    lines += ["", "## 校验", "", "| 项 | 结果 |", "| --- | --- |"]
    for k, v in (audit.get("checks") or {}).items():
        lines.append("| %s | %s |" % (k, v))
    for key, title in [("dropped", "丢弃/排除"), ("missing", "缺失"), ("limits", "限制")]:
        items = audit.get(key) or []
        lines += ["", "## " + title, ""]
        lines += ["- " + str(x) for x in items] if items else ["- 无"]
    if audit.get("params"):
        lines += ["", "## 参数", "", "```json",
                  json.dumps(audit["params"], ensure_ascii=False, indent=2), "```"]
    with open(md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path, md


# ---------------------------------------------------------------- export
def export(fig, out_path, formats=("png",)):
    """Save fig in requested formats. Returns list of written paths."""
    import matplotlib.pyplot as plt
    base, ext = os.path.splitext(out_path)
    if ext:
        base = base if ext.lower() not in (".png", ".svg", ".pdf") else base
    written = []
    for fmt in formats:
        p = out_path if (fmt == "png" and out_path.lower().endswith(".png")) else base + "." + fmt
        fig.savefig(p, bbox_inches="tight", facecolor="white", format=fmt)
        written.append(p)
    plt.close(fig)
    return written
