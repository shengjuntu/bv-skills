"""bvkit validate: 数据进入渲染前的核验层。

设计要点（来自实测教训）：
- "2019.3" 这类「年.序号」编码必须按年月解析，不能当小数（否则 11 月变 1.1 月，图上完全看不出来）。
  判定规则：整列为 4 位年 + 1~2 位序号、且序号范围 1..12、且列名/相邻列提示时间 → 判为年月。
  显式声明优先：params["date_format"] = "ym" / "decimal" 时不做猜测。
- 缺失不补零：缺失值单独记录，交给渲染器显式标注。
- 重复键、类型混杂、编码异常都要报；不能静默吞掉。
"""
import csv
import io
import json
import os
import re

from core import BVDataError, new_audit

YM_PAT = re.compile(r"^(19|20)\d{2}[.\-/]\d{1,2}$")
YM_COMPACT = re.compile(r"^(19|20)\d{2}(0[1-9]|1[0-2])$")
DEFECT_PAT = re.compile(r"(缺失|缺|missing|nan|null|none|n/a|未知|---)", re.I)


def detect_encoding(path):
    with open(path, "rb") as f:
        raw = f.read(4)
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return "utf-16"
    for enc in ("utf-8", "gbk"):
        try:
            with open(path, "rb") as f:
                f.read().decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    raise BVDataError("cannot decode %s as utf-8 or gbk" % path)


def load_table(path, sheet=None):
    """Return (rows: list[dict], meta: dict). Supports csv/tsv/json/xlsx."""
    if not os.path.exists(path):
        raise BVDataError("data file not found: %s" % path)
    lower = path.lower()
    meta = {"path": path, "format": os.path.splitext(lower)[1]}

    if lower.endswith((".xlsx", ".xls")):
        try:
            import pandas as pd
        except ImportError:
            raise BVDataError("xlsx needs pandas + openpyxl")
        kw = {"sheet_name": sheet} if sheet else {}
        df = pd.read_excel(path, **kw)
        meta["columns"] = list(df.columns)
        meta["sheets"] = None
        rows = df.where(pd.notnull(df), None).to_dict("records")
        return rows, meta

    if lower.endswith(".json"):
        with open(path, "r", encoding=detect_encoding(path)) as f:
            obj = json.load(f)
        if isinstance(obj, dict):
            for key in ("rows", "records", "data", "items"):
                if key in obj and isinstance(obj[key], list):
                    obj = obj[key]
                    break
        if not isinstance(obj, list):
            raise BVDataError("json must be an array of objects (or {rows:[...]})")
        meta["columns"] = list(obj[0].keys()) if obj else []
        return obj, meta

    enc = detect_encoding(path)
    delim = "\t" if lower.endswith(".tsv") else ","
    with open(path, "r", encoding=enc, newline="") as f:
        reader = csv.DictReader(f, delimiter=delim)
        rows = [dict(r) for r in reader]
        meta["columns"] = reader.fieldnames or []
    meta["encoding"] = enc
    return rows, meta


def parse_period(s):
    """'2019.3' -> 2019.1667 (年月) ; '2019-03' -> same ; '201903' -> same.
    Returns float(year + (month-1)/12) or None if not a period."""
    if s is None:
        return None
    if isinstance(s, (int, float)) and not isinstance(s, bool):
        # 已经由 validate 转好的年值（或原生数值时间轴）直接返回
        return float(s)
    t = str(s).strip()
    if not t:
        return None
    if YM_PAT.match(t):
        y, m = re.split(r"[.\-/]", t)
        m = int(m)
        if 1 <= m <= 12:
            return float(int(y)) + (m - 1) / 12.0
        return None
    if YM_COMPACT.match(t):
        return float(int(t[:4])) + (int(t[4:]) - 1) / 12.0
    return None


def looks_like_ym_column(values):
    total = [v for v in values if v not in (None, "")]
    if len(total) < 3:
        return False
    hits = sum(1 for v in total if YM_PAT.match(str(v).strip()))
    if hits / len(total) < 0.9:
        return False
    months = []
    for v in total:
        m = str(v).strip().split(".")[-1] if "." in str(v) else str(v).strip().split("-")[-1]
        try:
            months.append(int(m))
        except ValueError:
            return False
    return all(1 <= m <= 12 for m in months)


def coerce_number(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(",", "").replace(" ", "")
    if t in ("", "-", "—"):
        return None
    if t.endswith("%"):
        try:
            return float(t[:-1])
        except ValueError:
            return None
    for suffix in ("万", "亿", "k", "K", "M"):
        if t.endswith(suffix):
            t = t[:-1]
    try:
        return float(t)
    except ValueError:
        return None


def is_missing(v):
    return v is None or (isinstance(v, str) and (v.strip() == "" or DEFECT_PAT.search(v)))


def profile_column(name, values, date_format=None):
    """Infer type and issues for one column."""
    issues, kind = [], "text"
    nonnull = [v for v in values if not is_missing(v)]
    if not nonnull:
        return {"name": name, "kind": "empty", "issues": [{"level": "error", "msg": "整列为空"}],
                "n": 0, "missing": len(values)}

    if date_format == "ym" or (date_format is None and looks_like_ym_column(nonnull)):
        parsed = [parse_period(v) for v in nonnull]
        if all(p is not None for p in parsed):
            kind = "period_ym"
            issues.append({"level": "info",
                           "msg": "列按「年.月」解析（%d 值），不是小数；月序 1..12 已校验" % len(parsed)})
    nums = [coerce_number(v) for v in nonnull]
    if all(n is not None for n in nums) and kind == "text":
        kind = "number"
    elif kind == "text":
        hit = sum(1 for n in nums if n is not None)
        if 0 < hit < len(nums):
            issues.append({"level": "warn",
                           "msg": "%d/%d 个值可转数值，其余为文本：混合类型" % (hit, len(nums))})
    return {"name": name, "kind": kind, "issues": issues, "n": len(nonnull),
            "missing": sum(1 for v in values if is_missing(v))}


def validate(rows, spec=None, meta=None):
    """Full-table validation. Returns (report, prepared).

    report = {issues:[{level,col,msg}], columns:[profile], n_rows, missing_cells, dropped_rows}
    prepared = transformed values ready for renderers (period columns -> float year)
    """
    spec = spec or {}
    meta = meta or {}
    if not rows:
        raise BVDataError("empty table")
    cols = list(rows[0].keys())
    date_cols = spec.get("date_columns") or []
    date_format = spec.get("date_format")
    profiles, issues, prepared = [], [], [dict(r) for r in rows]

    for c in cols:
        vals = [r.get(c) for r in rows]
        fmt = date_format if c in date_cols else None
        prof = profile_column(c, vals, fmt)
        profiles.append(prof)
        issues.extend([dict(col=c, **i) for i in prof["issues"]])
        if prof["kind"] in ("period_ym", "number"):
            for r in prepared:
                if prof["kind"] == "period_ym":
                    r[c] = parse_period(r.get(c))
                else:
                    r[c] = coerce_number(r.get(c))

    # duplicates on declared keys
    keys = spec.get("primary_key")
    if keys:
        seen, dups = set(), []
        for r in rows:
            k = tuple(str(r.get(x)) for x in keys)
            if k in seen:
                dups.append(k)
            seen.add(k)
        if dups:
            issues.append({"level": "error", "col": "/".join(keys),
                           "msg": "%d 条重复主键，例如 %s" % (len(dups), dups[0])})

    missing_cells = sum(p["missing"] for p in profiles)
    if missing_cells:
        issues.append({"level": "warn", "col": "*",
                       "msg": "%d 个缺失单元格；渲染时将显式标注，不补零" % missing_cells})

    # out-of-range for declared bounds
    for b in spec.get("bounds") or []:
        c, lo, hi = b["col"], b.get("min"), b.get("max")
        bad = [r[c] for r in prepared if isinstance(r.get(c), float)
               and ((lo is not None and r[c] < lo) or (hi is not None and r[c] > hi))]
        if bad:
            issues.append({"level": "warn", "col": c,
                           "msg": "%d 个值越界 [%s, %s]，例如 %s" % (len(bad), lo, hi, bad[0])})

    report = {"n_rows": len(rows), "columns": profiles, "issues": issues,
              "missing_cells": missing_cells, "encoding": meta.get("encoding"),
              "format": meta.get("format")}
    return report, prepared


def to_audit_checks(report):
    levels = [i["level"] for i in report["issues"]]
    return {
        "rows": report["n_rows"],
        "encoding": report.get("encoding") or "-",
        "errors": levels.count("error"),
        "warnings": levels.count("warn"),
        "missing_cells": report["missing_cells"],
        "date_columns": len([c for c in report["columns"] if c["kind"] == "period_ym"]),
    }


def print_report(report, stream=None):
    import sys
    stream = stream or sys.stdout
    print("rows=%d  cols=%d  missing=%d" % (
        report["n_rows"], len(report["columns"]), report["missing_cells"]), file=stream)
    for p in report["columns"]:
        print("  %-18s %-10s missing=%d" % (p["name"], p["kind"], p["missing"]), file=stream)
    for i in report["issues"]:
        print("  [%s] %s: %s" % (i["level"], i.get("col", "*"), i["msg"]), file=stream)
