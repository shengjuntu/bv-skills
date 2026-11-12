---
name: bvkit-oneclick-charts
display_name: '数据图表一键出图'
display_name_en: 'One-Click Data Charts'
description: '把一份表格或一句话的作图意图变成一张带审计的静态图。当用户说"把这份数据画成趋势图/热图/网络图/分布图""这个数据该用什么图""出一张能核对口径的图""画图但别补零、别用双轴"时使用。数据格式支持 CSV/JSON/XLSX，一次可选 png/svg/pdf/wav/gif。不用于海报、插画、写实图片和纯装饰图。'
description_zh: '给一份数据和一句"我想看什么"，直接出图并附审计旁注。类型按意图选（趋势、对比、关系、分布、占比、轨迹、切片、动画），不需要记章节号；双轴、补零、缺字体降级会被直接拦截。'
description_en: 'Turns a table plus a plain-language chart intent into one audited static chart. Pick the type by intent (trend, comparison, relation, distribution, share, trajectory, slice, motion) with no chapter numbers. Dual axes, zero-filled gaps and silent font fallback are blocked.'
version: '2.1.1'
author: 'shengjuntu'
allowed-tools:
  - Bash
  - Read
  - Write
examples_zh: ['把这份月度销量表画成带事件标注的趋势图', '把这张人员共现表画成网络图，把只出现一次的弱连接过滤掉', '把期望和实际的对照表画成矩阵，把空着的格子标出来']
examples_en: ['Turn this monthly sales table into a trend chart with event markers', 'Draw this co-occurrence table as a network and filter one-off links', 'Render this expected-vs-actual table as a matrix and mark the empty cells']
compatibility: 'python3.9+ 与 matplotlib、numpy；网络需 networkx，词云需 wordcloud；需系统 CJK 字体（缺失直接报 BV_FONT 中止）。'
---

# 数据图表一键出图

## 一句话

给一份数据 + 一句“我想看什么”，出一张图，旁边附一份审计（用了什么口径、丢了什么、哪里没做）。

## 30 秒上手

```bash
python3 scripts/cli.py guide                    # 我该选哪种图？列出全部类型和所需数据
python3 scripts/cli.py render --spec references/ex_trend.json   # 直接跑一份现成例子
python3 scripts/cli.py render --spec my.json    # 出图 + 审计
python3 scripts/cli.py review --spec my.json    # 只检查配置，不出图
python3 scripts/cli.py selftest                 # 13 个内置样例 + 5 个反例
```

最小 spec 只要三样：**画什么（kind）、数据在哪、哪列是什么**。不想自己写，就照抄 `references/ex_<kind>.json` 再改 `data.path`。

```json
{
  "kind": "trend",
  "out": "out/sales",
  "data": {"path": "sales.csv"},
  "params": {"x": "month", "series": [{"name": "销量", "y": "value"}]}
}
```

## 选哪种图（不需要记章节号）

| 你想看什么 | `kind` | 你需要有什么数据 |
| --- | --- | --- |
| 随时间的走势 | `trend` | 一列时间 + 一列数值（可再加一列事件文字） |
| 两个类别的交叉计数 | `heatmap` | 两列分类（或已交叉计数的三列） |
| 期望和实际差在哪 | `compare` | 期望一组关系 + 实际一组，或两列期望/实际值 |
| 多变量的整体形态 | `matrix` | 若干行若干列的多变量数值 |
| 谁和谁一起出现 | `cooccurrence` | 实体成对出现，或共现计数 |
| 按时间窗聚合的位置分布 | `window_heatmap` | 一列时间 + 一列位置/类别 |
| 关系网络、谁连谁 | `network` | 两列节点（一行一条关系） |
| 两期是否相似 | `similarity` | 两期相似度或两期指标 |
| 分布与异常点 | `scatter` | 两列坐标，或两个可投影的数值 |
| 分渠道/分类对比，缺口要看出来 | `facets` | 一列分类 + 一列时间 + 一列数值 |
| 一条路怎么走的 | `route` | 一列顺序 + 两列坐标 |
| 起点终点与路线 | `map` | 起点/终点/节点坐标 |
| 词的重要性 | `wordcloud` | 一列词 + 一列权重 |
| 三维数据内部长什么样 | `volume` | 三维网格数值 |
| 过程怎么演变 | `animation` | 逐帧实体位置或状态 |
| 数值与声音怎么对应 | `soundmap` | 一列数值序列 |
| 这图本身站不站得住 | `review` | 已有图或 spec（只出评审清单，不产图） |

完整说明与所需数据可用 `python3 scripts/cli.py guide` 现场打印；某个类型的必做口径用 `python3 scripts/cli.py inspect trend`。

**每种类型都配了一份能跑的例子**：`references/ex_<kind>.json` + 同目录下它自己的 csv。按“我想看什么”索引在 `references/examples.md`，每行写明数据长什么样、图上该看到什么、换成自己的数据要改哪几行。

## spec 格式

必填三项：`kind`（或 `chapter`，见下文）、`out`、`data`。

```json
{
  "kind": "trend",
  "out": "out/sales",
  "formats": ["png", "svg"],
  "title": "销量与促销节点",
  "note": "示例数据，n=5",
  "date_format": "ym",
  "date_columns": ["month"],
  "data": {"path": "sales.csv"},
  "params": {
    "x": "month",
    "series": [{"name": "销量", "y": "value"}],
    "events": {"col": "event", "at": "month", "cat": "cat"}
  }
}
```

- `data` 三选一：`{"path": "x.csv"}`、`{"path": "x.xlsx", "sheet": "S1"}`、`{"rows": [...]}`。
- `data.path` 相对 spec 所在目录解析（先试 cwd），所以 spec 和 csv 放一起就能直接跑。
- `out` 不要带扩展名；`formats` 决定导出 png/svg/pdf（17 可加 wav，19 可加 gif）。
- 退出码：0 成功；1 环境/参数错误；2 数据核验失败；3 评审拦截。`--force` 可越过 2/3，但审计留痕。
- 要精确复刻某一章的方法时，把 `kind` 换成 `"chapter": "02"` 即可，两者等价（kind 只是一层更好懂的别名）。

## 内置口径（不通过参数关闭）

这些是硬规则，违反会报 `BV_SPEC` 或直接拒绝渲染：

- 计数/规模类 **0 基线**；关闭必须给 `baseline_reason`。
- **无双 y 轴**（量级不同就拆面板）。
- 缺失格 **文字/虚线标注，不补零**；小倍数缺失处折线断开。
- 网络 0 度节点 **单列**，不混入布局。
- 地图多轨迹共起点时 **只标一个“共起点”**，终点用编号 + 图例。
- 体数据切片 **过峰值**，三片 **共用同一值域** + 各自 colorbar。
- 动画 **必须同时出静态替代**（起止帧）。
- 随机布局/词云/动画 **固定 seed=42**。
- 字体缺失 → `BV_FONT` 报错并中止，不继续出图。

## 审计产物

每张图旁边生成两个文件：

- `<out>.audit.json` — 机器读：`chapter/renderer/output/data_source/n_records/checks/dropped/missing/params/limits`
- `<out>.audit.md` — 人读：校验项表格 + 丢弃项 + 限制声明

`checks` 里必然出现这些键，交付时可直接引用：

```json
{"zero_baseline": true, "dual_axis": false, "missing_not_zeroed": true,
 "date_columns": 1, "seed": 42, "font": "WenQuanYi Micro Hei", "rows": 5}
```

## 想回查章节

`kind` 与章节是一一映射，`python3 scripts/cli.py list` 打印全表；`inspect 02` 与 `inspect trend` 输出同一组口径规则。章节只在 `audit.json` 里留作溯源，不是使用前提。

## 出错怎么办

| 码 | 含义 | 处理 |
| --- | --- | --- |
| `BV_FONT` | 找不到 CJK 字体 | 装 fonts-wqy-microhei，或 spec 里给 `font_path` |
| `BV_DATA` | 文件缺失/编码无法识别/空表/JSON 结构不对 | 按提示换文件或转码 |
| `BV_SPEC` | 缺 params 必需字段、kind 不认识、依赖未装 | 按提示补字段或装依赖 |
| 退出码 2 | 数据核验有 error（重复主键等） | 看 stdout 的 issues；确认无误再 `--force` |
| 退出码 3 | 评审拦截（双轴、无理由截断基线、动画无静态替代） | 改配置；不要用 `--force` 掩盖 |

## 环境前置

```bash
python3 -m pip install matplotlib numpy
python3 -m pip install networkx wordcloud     # 仅 network/cooccurrence 与 wordcloud 需要
sudo apt-get install -y fonts-wqy-microhei    # 或把 ttc 放到 ~/.local/share/fonts/
```

无 sudo 时把字体文件放到 `~/.local/share/fonts/wqy-microhei.ttc` 即可；也可在 spec 里用 `font_path` 指定绝对路径。

## 权限与数据用途

- 只读：spec 指定的 csv/json/xlsx 数据文件、`references/` 下的参数表与示例。
- 只写：spec 里 `out` 指定的输出前缀（`.png/.svg/.pdf/.wav/.gif` 与 `.audit.json/.audit.md`）。
- 不联网：无 HTTP 请求、无遥测、不上传数据。
- 不读用户目录之外的内容；不写系统路径。
- 依赖在本地执行，`seed` 固定，同一输入同一输出。

## 边界（明确不做）

- `review` 不产图：它的产出是评审清单与改版建议。
- 不做交互式图表（D3/ECharts）：本包交付静态图 + 审计。
- 不做“任意数据 → 任意图”的通用绘图：类型由 `kind` 决定，避免口径漂移。
