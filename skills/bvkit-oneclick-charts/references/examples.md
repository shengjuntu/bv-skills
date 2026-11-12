# 例子即说明书

17 个图表类型各有一份可跑 spec，再加 1 份 `chapter` 写法示例。每份都自带数据文件，复制就行，不用先读参数表。

在 skill 根目录（含 `SKILL.md` 的那一层）执行：

```bash
python3 scripts/cli.py guide                                  # 先看有哪些类型
python3 scripts/cli.py render --spec references/ex_trend.json  # 照抄一个改
```

## 一、按“我想看什么”找例子

| 我想看什么 | 例子 | 数据文件 | 数据长什么样 | 图上该看到 |
| --- | --- | --- | --- | --- |
| 随时间的走势 | `ex_trend.json` | `narrative.csv` | `ym,event,cat,v` | 折线从 0 起；事件按真实时间落在下方面板，不等间距 |
| 两类别的交叉计数 | `ex_heatmap.json` | `heat_region.csv` | `region,channel,count` | 每格有数字；计数之和等于样本数 |
| 期望和实际差在哪 | `ex_compare.json` | `cmp_team.csv` | `row,col,actual`（空格=空洞） | 双面板；空格被红框标出，不是白底凑数 |
| 多变量的整体形态 | `ex_matrix.json` | `mtx_item.csv` | `row,col,value` | 单面板色块；灰度下仍能分辨深浅 |
| 谁和谁一起出现 | `ex_cooccurrence.json` | `cooc_pair.csv` | `row,col,count` | 对角线为 0 并在图上说明 |
| 时间窗里的位置分布 | `ex_window_heatmap.json` | `win_zone.csv` | `zone,hour,count` | 标题写明窗口与尺度 |
| 关系网络 | `ex_network.json` | `affiliation.csv` | `a,b,w` | 低于阈值的一次性连接被滤掉，0 度节点单独一列 |
| 两期是否相似、阈值怎么定 | `ex_similarity.json` | `affiliation.csv` | `a,b,w` | 与 `ex_network` 同一份数据、只把 `threshold` 从 2 放到 1：桥接边进来，两派变连通 |
| 分布与异常点 | `ex_scatter.json` | `sc_cluster.csv` | `x,y,cluster` | 稀疏点标注为“稀疏/异常”，不混进簇 |
| 分渠道对比，缺口要看出来 | `ex_facets.json` | `facets.csv` | `channel,month,active` | 缺的月份（整行缺失也算）折线断开 + 灰虚线 + “未采集：N”，不补零 |
| 一条路怎么走 | `ex_route.json` | 内联 `params.routes` | 每点 `lon,lat,t` | 共起点只标一个星；终点用编号，全名在图例 |
| 起点终点与路线 | `ex_map.json` | 内联 `params.routes` | 同上 | 起点标星，终点编号 |
| 词的重要性 | `ex_wordcloud.json` | `wc_term.csv` | `term,weight` | 右侧有频次核对面板，不是只有一朵云 |
| 三维数据内部 | `ex_volume.json` | 内联 `params.peaks` | 峰位置与幅度 | 三片过峰值、共用值域、各自 colorbar |
| 过程怎么演变 | `ex_animation.json` | 内联 `params` | `points,frames,fps` | 同时产出 GIF 和起止帧静态图 |
| 数值与声音对应 | `ex_soundmap.json` | `snd_metric.csv` | `name,value` | 图上写出音高公式；可选导出 wav |
| 这图站不站得住 | `ex_review.json` | `narrative.csv` | 任意 | 不产图，只打印评审清单 |
| （回查）章节写法 | `ex02_narrative.json` | `narrative.csv` | 同上 | 与 `ex_trend` 等价，只是写 `chapter` 而非 `kind` |

## 二、三个完整例子，直接改

**趋势图**（`ex_trend.json`）——最常用，一份时间列 + 一份数值列：

```json
{
  "kind": "trend",
  "out": "out/ex_trend",
  "title": "示例：月度规模走势（下方事件按真实时间对齐）",
  "note": "示例数据，5 个时间点",
  "date_format": "ym",
  "date_columns": ["ym"],
  "data": {"path": "narrative.csv"},
  "params": {
    "x": "ym",
    "series": [{"name": "月活（万）", "y": "v"}],
    "events": {"col": "event", "at": "ym", "cat": "cat"},
    "y_label": "万"
  }
}
```

`ym` 里的 `2019.3` 会被当成 2019 年 3 月（不是小数 2019.3），这正是 `date_format` 存在的原因。

**网络图**（`ex_network.json`）——一行一条关系，加阈值就过滤弱连接：

```json
{
  "kind": "network",
  "out": "out/ex_network",
  "data": {"path": "affiliation.csv"},
  "params": {"source": "a", "target": "b", "weight": "w", "threshold": 2}
}
```

**关系审计**（`ex_compare.json`）——`expected` 用 `行|列` 作键，`actual` 留空即空洞：

```json
{
  "kind": "compare",
  "out": "out/ex_compare",
  "data": {"path": "cmp_team.csv"},
  "params": {
    "rows": "row", "cols": "col", "value": "actual",
    "expected": {"仓储|补货": 1, "财务|报销": 1, "客服|退款": 1}
  }
}
```

## 三、换自己的数据

1. 复制最接近的那份 json，只改 `data.path`、`title`、`note`。
2. 数据文件的列名照抄原例子，就不用改 `params`。
3. 跑之前可以先 `python3 scripts/cli.py validate --spec 我的.json` 只验数据；再 `review` 只查配置。
4. 产物写到 `out` 前缀（相对 cwd），旁边同时生成 `.audit.json` 与 `.audit.md`，口径与丢弃项都记在里面。

## 四、四类例子不需要数据文件

`route`、`map`、`volume`、`animation` 的输入是坐标或参数，直接写在 `params` 里；`review` 只输出清单。这五类和其余例子一样可以直接跑，但换数据时要改的是 `params` 而不是 csv。

## 五、例子之间的取舍

- 例子只放**必需参数 + 一个体现口径的可选项**（如 `threshold`、`expected`、`outlier_labels`），不堆全部参数；完整参数见 `params.md`。
- 每个例子都标注“示例数据”，图上不会冒充真实结论。
- 每份 spec 都能被 `selftest` 之外单独跑通；改过参数表后要重跑一遍全部例子（`scripts/cli.py render --spec references/ex_*.json`）。
