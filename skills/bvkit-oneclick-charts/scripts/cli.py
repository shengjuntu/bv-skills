"""bvkit CLI: list / inspect / validate / render / review / selftest."""
import argparse
import json
import os
import sys

from core import BVError, VERSION, export, setup_style, write_audit
from renderers import RENDERERS
from renderers2 import render_scatter, render_wordcloud
from review import format_findings, review_audit, review_spec
from routes import KINDS, ROUTES, kind_info, resolve_kind, rules_for, route
from validate import load_table, print_report, to_audit_checks, validate

ALL_RENDERERS = dict(RENDERERS)
ALL_RENDERERS["scatter"] = render_scatter
ALL_RENDERERS["wordcloud"] = render_wordcloud


def _load_spec(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve(spec, spec_dir=None):
    """Fill renderer from the chart intent (kind/chart) or the chapter route; load data.

    入口优先级：kind / chart > chapter。
    相对路径的 data.path 先按 cwd 找，找不到再按 spec 所在目录找（便于 examples 就地运行）。
    """
    kind = spec.get("kind") or spec.get("chart")
    chapter = None
    if kind:
        try:
            chapter = resolve_kind(kind)
        except KeyError as e:
            raise BVError(str(e.args[0]))
    elif spec.get("chapter"):
        chapter = str(spec.get("chapter")).zfill(2)
    if chapter is None:
        raise BVError(
            "spec 需要一个图表类型：'kind'（推荐，如 trend/heatmap/network/facets）"
            "或 'chapter'（01-20）。跑 guide 子命令看全部 kind。"
        )
    renderer = spec.get("renderer")
    if not renderer:
        renderer, _task = route(chapter)
    if renderer not in ALL_RENDERERS:
        raise BVError("unknown renderer %r; available: %s" % (renderer, sorted(ALL_RENDERERS)))
    data = spec.get("data") or {}
    path = data.get("path")
    if path and not os.path.isabs(path) and not os.path.exists(path) and spec_dir:
        cand = os.path.join(spec_dir, path)
        if os.path.exists(cand):
            path = cand
    if path:
        rows, meta = load_table(path, sheet=data.get("sheet"))
    elif data.get("rows"):
        rows, meta = data["rows"], {"path": "inline"}
    else:
        rows, meta = [], {"path": "inline"}
    return chapter, renderer, rows, meta


def cmd_list(args):
    print("%-4s %-16s %s" % ("章", "renderer", "任务"))
    for ch, (rd, task) in sorted(ROUTES.items()):
        print("%-4s %-16s %s" % (ch, rd, task))
    return 0


def cmd_guide(args):
    """按“你想看什么”列图表类型，不要求记章节号。"""
    print("按你想画的东西选 kind（章节号只是内部实现，不用记）\n")
    print("%-14s | %s" % ("kind", "你需要有什么数据 -> 画出来是什么"))
    print("-" * 78)
    for k in sorted(KINDS):
        ch, need, desc = KINDS[k]
        print("%-14s | %s -> %s" % (k, need, desc))
    print("\n最小 spec（把 kind 换掉就能画别的）：")
    print('  {"kind": "trend", "out": "out/trend", "data": {"path": "my.csv"},')
    print('   "params": {"x": "month", "series": [{"name": "销量", "y": "value"}]}}')
    print("  python3 scripts/cli.py render --spec my.json")
    print("\n拿不准就用 review（只出评审清单，不产图）。")
    return 0


def cmd_inspect(args):
    t = str(args.target).strip()
    try:
        if t.lower() in KINDS:
            ch = resolve_kind(t.lower())
            print("kind %s -> chapter %s" % (t.lower(), ch))
        else:
            ch = t.zfill(2)
        rd, task = route(ch)
    except KeyError:
        raise BVError(
            "不认识 %r。可用图表类型（kind）: %s；也可以直接给章节号 01-20。"
            "跑 `cli.py guide` 看每种类型需要什么数据。" % (t, ", ".join(sorted(KINDS)))
        )
    print("chapter %s -> renderer %s" % (ch, rd))
    print("task: %s" % task)
    print("rules:")
    for r in rules_for(ch):
        print("  - %s: %s" % (r, RULE_DOC_TEXT(r)))
    return 0


def RULE_DOC_TEXT(rule):
    from routes import RULE_DOC
    return RULE_DOC.get(rule, rule)


def cmd_validate(args):
    spec = _load_spec(args.spec) if args.spec else {}
    if spec.get("kind") or spec.get("chart"):
        try:
            spec = dict(spec, chapter=resolve_kind(spec.get("kind") or spec.get("chart")))
        except KeyError as e:
            raise BVError(str(e.args[0]))
    data = spec.get("data") or {}
    path = args.data or data.get("path")
    if not path:
        raise BVError("validate needs --data or spec.data.path")
    rows, meta = load_table(path, sheet=(data.get("sheet") if data else None))
    report, prepared = validate(rows, spec=spec, meta=meta)
    print_report(report)
    if spec.get("review", True):
        findings = review_spec(dict(spec, renderer=spec.get("renderer")), report)
        print("\nreview:")
        print(format_findings(findings))
    if args.json:
        print(json.dumps({"report": report, "checks": to_audit_checks(report)},
                         ensure_ascii=False, indent=2))
    return 0 if not [i for i in report["issues"] if i["level"] == "error"] else 2


def cmd_render(args):
    spec = _load_spec(args.spec)
    chapter, renderer, rows, meta = _resolve(spec, os.path.dirname(os.path.abspath(args.spec)))
    style = setup_style(spec.get("font_path"), dpi=int(spec.get("dpi", 140)))

    report = None
    if renderer not in ("geo", "volume", "multimodal", "animation") and rows:
        report, prepared = validate(rows, spec=spec, meta=meta)
        rows = prepared
        errs = [i for i in report["issues"] if i["level"] == "error"]
        if errs and not args.force:
            print("数据校验未通过，拒绝渲染（--force 可跳过）:", file=sys.stderr)
            print_report(report, sys.stderr)
            return 2

    findings = review_spec(dict(spec, renderer=renderer, chapter=chapter), report)
    blocking = [f for f in findings if f["level"] == "error"]
    if blocking and not args.force:
        print("评审未通过，拒绝渲染（--force 可跳过）:", file=sys.stderr)
        print(format_findings(blocking), file=sys.stderr)
        return 3

    out = spec["out"]
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    p = dict(spec.get("params") or {})
    p.setdefault("title", spec.get("title"))
    p.setdefault("note", spec.get("note"))
    if renderer == "wordcloud":
        p.setdefault("font_path", style["font_path"])
    fig, audit = ALL_RENDERERS[renderer](rows, p, dict(spec, chapter=chapter), meta)
    formats = spec.get("formats") or ["png"]
    written = export(fig, out, formats=formats)

    audit["checks"].update(to_audit_checks(report) if report else {})
    audit["checks"]["font"] = style["font_name"]
    audit["checks"]["renderer_mods"] = renderer
    base = os.path.splitext(written[0])[0]
    if out.lower().endswith((".png", ".svg", ".pdf")):
        base = os.path.splitext(out)[0]
    json_p, md_p = write_audit(audit, base)
    ra = review_audit(audit, chapter)
    print("rendered: %s" % ", ".join(written))
    print("audit:    %s" % json_p)
    print("rules:    %d satisfied / %d not_satisfied / %d manual"
          % (len(ra["satisfied"]), len(ra["not_satisfied"]), len(ra["unverified"])))
    if ra["not_satisfied"]:
        print("not satisfied: %s" % ", ".join(ra["not_satisfied"]))
    if ra["unverified"]:
        print("需人工复核: %s" % ", ".join(ra["unverified"]))
    if findings:
        print("\nreview note:\n" + format_findings(findings))
    return 0


def cmd_review(args):
    spec = _load_spec(args.spec)
    if spec.get("kind") or spec.get("chart"):
        try:
            spec = dict(spec, chapter=resolve_kind(spec.get("kind") or spec.get("chart")))
        except KeyError as e:
            raise BVError(str(e.args[0]))
    data = spec.get("data") or {}
    report = None
    if data.get("path"):
        rows, meta = load_table(data["path"], sheet=data.get("sheet"))
        report, _ = validate(rows, spec=spec, meta=meta)
    findings = review_spec(spec, report)
    if report:
        print_report(report)
        print()
    print(format_findings(findings))
    return 0 if not [f for f in findings if f["level"] == "error"] else 2


def cmd_selftest(args):
    from selftest import main as selftest_main
    return selftest_main(args.workdir)


def build_parser():
    ap = argparse.ArgumentParser(prog="bvkit", description="one-click chapter charting with built-in audit (%s)" % VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="章节 -> 图表族 映射（回查用）").set_defaults(func=cmd_list)

    gd = sub.add_parser("guide", help="按'你想画什么'选图表类型（推荐入口，不用记章节）")
    gd.set_defaults(func=cmd_guide)

    ins = sub.add_parser("inspect", help="看某个图表类型或某章的口径必做项")
    ins.add_argument("target", help="kind（如 trend）或章节号（如 02）")
    ins.set_defaults(func=cmd_inspect)

    val = sub.add_parser("validate", help="只做数据核验")
    val.add_argument("--data")
    val.add_argument("--spec")
    val.add_argument("--json", action="store_true")
    val.set_defaults(func=cmd_validate)

    ren = sub.add_parser("render", help="一键出图 + 审计")
    ren.add_argument("--spec", required=True)
    ren.add_argument("--force", action="store_true")
    ren.set_defaults(func=cmd_render)

    rev = sub.add_parser("review", help="渲染前静态评审配置")
    rev.add_argument("--spec", required=True)
    rev.set_defaults(func=cmd_review)

    st = sub.add_parser("selftest", help="跑内置自检（含 2019.3 陷阱与缺失格）")
    st.add_argument("--workdir", default="/tmp/bvkit_selftest")
    st.set_defaults(func=cmd_selftest)
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except BVError as e:
        print("[%s] %s" % (e.code, e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
