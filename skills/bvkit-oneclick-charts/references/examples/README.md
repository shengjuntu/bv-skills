# examples（可跑示例）

5 个 spec，覆盖 5 个图元族（时间序列 / 网络 / 关系矩阵 / 轨迹 / 小倍数）。

## 运行

在 skill 根目录（含 `SKILL.md` 的那一层）执行，`PYTHONPATH` 指向 `scripts`：

```bash
PYTHONPATH=scripts python3 -m bvkit render --spec references/examples/ex02_narrative.json
PYTHONPATH=scripts python3 -m bvkit render --spec references/examples/ex07_network.json
PYTHONPATH=scripts python3 -m bvkit render --spec references/examples/ex14_relation.json
PYTHONPATH=scripts python3 -m bvkit render --spec references/examples/ex06_routes.json
PYTHONPATH=scripts python3 -m bvkit render --spec references/examples/ex13_facets.json
```

`data.path` 相对 spec 文件解析，所以在任意 cwd 下都能找到同目录的 `data/*.csv`。
产物写到 spec 里 `out` 指定的路径（相对 cwd）。

## 各例看点

| spec | 看点 |
| --- | --- |
| `ex02_narrative.json` | `2019.3` 被解析成 2019 年 3 月；事件点按真实时间落在下方事件面板，不是等间距 |
| `ex07_network.json` | 两派自然分开；`threshold: 2`（共现≥2 次）把跨派弱连接过滤掉，audit 记录过滤前后边数 |
| `ex14_relation.json` | 右面板期望矩阵；3 个期望关系在实际记录里为空（`n` 留空），被红框标为“空洞” |
| `ex06_routes.json` | 三条航线共起点 → 只标一个星标；终点用编号，全名进图例框；下方面板核对时长 |
| `ex13_facets.json` | 三个渠道各缺一个月份：折线在该处断开 + 灰虚线 + “未采集：N” |

## 改成自己的数据

复制一个 spec，把 `data.path` 指到自己的 csv，改 `chapter` 即可换图类型；参数表见
`../params.md`，各章必做口径见 `../chapters.md`。
