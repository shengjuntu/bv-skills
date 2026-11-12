# examples（可跑示例）

6 个 spec：1 个演示 `kind` 用法（推荐入口），5 个沿用 `chapter`（等价写法，用于回查）。spec 与所需 csv 都平铺在本目录。

## 运行

在 skill 根目录（含 `SKILL.md` 的那一层）执行：

```bash
python3 scripts/cli.py render --spec references/ex_kind_trend.json   # 只写 kind，不写章节
python3 scripts/cli.py render --spec references/ex02_narrative.json
python3 scripts/cli.py render --spec references/ex07_network.json
python3 scripts/cli.py render --spec references/ex14_relation.json
python3 scripts/cli.py render --spec references/ex06_routes.json
python3 scripts/cli.py render --spec references/ex13_facets.json
```

`data.path` 相对 spec 文件解析，所以 spec 里只写 `narrative.csv` 这类文件名即可命中同目录的 csv。
产物写到 spec 里 `out` 指定的路径（相对 cwd）。

## 各例看点

| spec | 写法 | 看点 |
| --- | --- | --- |
| `ex_kind_trend.json` | `"kind": "trend"` | 只给意图就能出图；审计里仍记录它落到了哪一章 |
| `ex02_narrative.json` | `"chapter": "02"` | `2019.3` 被解析成 2019 年 3 月；事件点按真实时间落在下方事件面板，不是等间距 |
| `ex07_network.json` | `"chapter": "07"` | 两派自然分开；`threshold: 2`（共现≥2 次）把跨派弱连接过滤掉，audit 记录过滤前后边数 |
| `ex14_relation.json` | `"chapter": "14"` | 右面板期望矩阵；3 个期望关系在实际记录里为空（`n` 留空），被红框标为“空洞” |
| `ex06_routes.json` | `"chapter": "06"` | 三条航线共起点 → 只标一个星标；终点用编号，全名进图例框；下方面板核对时长 |
| `ex13_facets.json` | `"chapter": "13"` | 三个渠道各缺一个月份：折线在该处断开 + 灰虚线 + “未采集：N” |

## 改成自己的数据

复制一个 spec，把 `data.path` 指到自己的 csv 即可。要换图类型，把 `kind` 改成
另一个意图（先跑 `python3 scripts/cli.py guide` 看清单）；参数表见 `params.md`，
各类型的必做口径见 `chapters.md` 或 `python3 scripts/cli.py inspect <kind>`。
