---
name: bvkit-oneclick-charts
description: 把 20 章"美丽可视化"方法压缩成 6 个图元族的一键出图工具。当用户要求"按某章的做法画一张图""用 bv-02/07/14 那种图""把这份数据画成时间序列/热图/网络/小倍数/轨迹/体数据切片"，或需要一张带口径审计（0 基线、无双轴、缺失标注、确定性种子、字体已装）的图时使用。不用于海报、插画、写实图片和纯装饰图。
compatibility: python3 + matplotlib + numpy；词云需 wordcloud，网络需 networkx；需要系统 CJK 字体（缺失会明确报 BV_FONT，不会静默出豆腐块）。
---

# bvkit 一键出图

## 它是什么

原 20 章 skills 是方法论文档（0 个可执行文件），执行时靠人读懂再手写脚本。bvkit 把这些方法里**可判定的部分**固化成代码：

| 层 | 作用 | 对应原来的问题 |
| --- | --- | --- |
| 数据核验 | 编码、类型、`2019.3` 年月、缺失、重复键、越界 | bv-02 月份错位、bv-13 补零、bv-15 完整性 |
| 路由 | 章节号 → 渲染器，不用读文档选图 | 20 章不知道该用哪个图 |
| 渲染 | 8 个渲染器，口径默认值内置 | bv-06 标签堆叠、bv-07 布局压团、bv-12 缺类别刻度、bv-18 无色标 |
| 评审 | 渲染前静态拦截 + 渲染后规则复核 | bv-01 双轴/截断基线、bv-20 断言无证据 |
| 审计 | 每张图旁边落一份 json+md | 无"必须标示例数据"的强制 |

## 三条命令

```bash
python -m bvkit list                  # 20 章 -> renderer 映射
python -m bvkit inspect 02            # 某章的口径必做项
python -m bvkit validate --data x.csv # 只做数据核验
python -m bvkit review --spec s.json  # 只做静态评审
python -m bvkit render --spec s.json  # 核验 + 评审 + 出图 + 审计
python -m bvkit selftest              # 13 个内置样例 + 5 个反例
```

## spec 格式

```json
{
  "chapter": "02",
  "out": "out/bv02_story",
  "formats": ["png", "svg"],
  "title": "用户规模与政策节点",
  "note": "示例数据，n=5",
  "date_format": "ym",
  "date_columns": ["ym"],
  "data": {"path": "data/story.csv"},
  "params": {
    "x": "ym",
    "series": [{"name": "规模", "y": "v"}],
    "events": {"col": "event", "at": "ym", "cat": "cat"}
  }
}
```

- `chapter` 必填（01-20），决定 renderer；`renderer` 可显式覆盖。
- `data` 三选一：`{"path": "x.csv"}`、`{"path": "x.json", "sheet": "S1"}`、`{"rows": [...]}`。
- `out` 不要带扩展名；`formats` 决定导出 png/svg/pdf。
- 退出码：0 成功；1 环境/参数错误；2 数据核验失败；3 评审拦截。加 `--force` 可越过 2/3，但审计里会留痕。

## 内置口径（不可通过参数关闭）

这些不是默认值，是硬规则——违反会报 `BV_SPEC` 或直接拒绝渲染：

- 计数/规模类 **0 基线**；关闭必须给 `baseline_reason`。
- **无双 y 轴**（不同量级拆面板）。
- 缺失格 **文字/虚线标注，不补零**。
- 网络 0 度节点 **单列**，不混入布局。
- 地图多轨迹共起点时 **只标一个"共起点"**，终点用编号 + 图例。
- 体数据切片 **过峰值**，三片 **共用同一值域** + 各自 colorbar。
- 动画 **必须同时出静态替代**（起止帧）。
- 随机布局/词云/动画 **固定 seed=42**。
- 字体缺失 → `BV_FONT` 报错并中止，不继续出图。

## 20 章 → 渲染器

| 章节 | renderer | 说明 |
| --- | --- | --- |
| 01 / 20 | review | 只输出评审清单，不产图（这两章产出的是文字结论） |
| 02 / 11 | timeseries | 时间序列 + 事件面板（事件按真实时间对齐） |
| 03 | wordcloud | 词云 + 右侧 Top-N 频次核对面板 |
| 04 / 12 / 14 / 15 / 16 | matrix | 分类矩阵热图；14 额外给期望/实际双面板 |
| 05 / 06 | geo | 轨迹图：编号 + 图例 + 时长面板 |
| 07 / 08 / 10 | network | 投影网络；阈值可调，孤立节点单列 |
| 09 | scatter | 投影散布 + 簇/异常点区分 |
| 13 | smallmultiples | 小倍数 + 未采集虚线标注 |
| 17 | multimodal | 视觉 + 音高映射（可写 wav） |
| 18 | volume | 三正交切片 |
| 19 | animation | GIF + 静态替代 |

完整参数见 `references/params.md`，章节任务原文见 `references/chapters.md`。

## 审计产物

每张图旁边生成：

- `<out>.audit.json` — 机器读：`chapter/renderer/output/data_source/n_records/checks/dropped/missing/params/limits`
- `<out>.audit.md` — 人读：校验项表格 + 丢弃项 + 限制声明

`checks` 里必然出现这些键，交付时可直接引用：

```json
{"zero_baseline": true, "dual_axis": false, "missing_not_zeroed": true,
 "date_columns": 1, "seed": 42, "font": "WenQuanYi Micro Hei", "rows": 5}
```

## 出错怎么办

| 码 | 含义 | 处理 |
| --- | --- | --- |
| `BV_FONT` | 找不到 CJK 字体 | 装 fonts-wqy-microhei，或 spec 里给 `font_path` |
| `BV_DATA` | 文件缺失/编码无法识别/空表/JSON 结构不对 | 按提示换文件或转码 |
| `BV_SPEC` | 缺 params 必需字段、renderer 不认识、依赖未装（wordcloud） | 按提示补字段或装依赖 |
| 退出码 2 | 数据核验有 error（重复主键等） | 看 stdout 的 issues；确认无误再 `--force` |
| 退出码 3 | 评审拦截（双轴、无理由截断基线、动画无静态替代） | 改配置；不要用 `--force` 掩盖 |

## 边界（明确不做）

- 01/20 不产图：它们的方法是评审与论证审计，输出是结论。
- 不做交互式图表（D3/ECharts）：本包交付静态图 + 审计。
- 不做"数据→任意图表类型"的通用绘图：图类型由章节决定，避免口径漂移。
