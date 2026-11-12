# bv-skills v2.0.0

把 `beautiful-visualization-skills-v1.0.0`（1 个路由工作台 + bv-01~bv-20）重组为**一个可执行的 skill + 8 个渲染器 + 审计产物**。

原包 21 个 skill 里 0 个 `.py/.sh/.js`，20 章方法是纯文档，执行时靠人读懂再手写脚本。
v2.0.0 保留方法中的可判定部分并固化为代码，其余（分析判断、数据选期）仍由调用方决定。

## 目录

```
bv-skills-v2.0.0/
└── skills/bvkit-oneclick-charts/
    ├── SKILL.md                 # agent 入口：触发场景、命令、spec 格式、错误码
    ├── bvkit/                   # python 包（10 个模块）
    │   ├── core.py              # 字体探测/调色板/audit/导出
    │   ├── validate.py          # 编码、类型、年月、缺失、重复、越界
    │   ├── routes.py            # 20 章 → renderer + 每章口径规则
    │   ├── renderers.py         # timeseries/matrix/network/smallmultiples/geo/volume/multimodal/animation
    │   ├── renderers2.py        # scatter/wordcloud
    │   ├── review.py            # 渲染前静态评审 + 渲染后规则复核
    │   ├── selftest.py          # 13 个样例 + 5 个反例
    │   └── cli.py               # list/inspect/validate/review/render/selftest
    ├── references/
    │   ├── chapters.md          # 20 章 → 图元 → 参数 → 必做口径
    │   ├── params.md            # 8 个渲染器参数表
    │   └── errors.md            # 错误码、退出码、"图不对但不报错"排查
    └── examples/                # 5 份可跑 spec + 4 份数据
```

## 装什么

```bash
python3 -m pip install matplotlib numpy
python3 -m pip install networkx wordcloud   # 仅 07/08/10 与 03 需要
```

中文字体（缺了会 `BV_FONT` 中止，不会出豆腐块）：

```bash
sudo apt-get install -y fonts-wqy-microhei    # 或把 ttc 放到 ~/.local/share/fonts/
```

## 先验证，再交付

```bash
cd skills/bvkit-oneclick-charts
PYTHONPATH=. python -m bvkit selftest --workdir /tmp/bvkit_selftest
PYTHONPATH=. python -m bvkit render --spec examples/ex02_narrative.json
```

`selftest` 会产出 13 张图 + 2 个附件（wav/gif），并跑 5 个反例：

1. `2019.11` 必须解析成 2019.8333（不是 2019.11）
2. 关闭 0 基线且无理由 → 拒绝
3. 双 y 轴 → 拒绝
4. 缺失格 → 不补零、holes 计数正确
5. 时间列口径 → 写入 audit

## 这一版验证到什么程度

在服务器（anaconda python3.14 / matplotlib 3.11.0 / WQY MicroHei）上跑了 7 轮：

| 轮次 | 结果 | 当轮修掉的问题 |
| --- | --- | --- |
| 1 | 13/13 出图，判定 13 FAIL | 判定门槛把 json 当图片比字节；audit 没合入数据校验项 |
| 2 | 13/13 PASS | 字体 bold 缺失警告（去掉 bold 请求） |
| 3 | PASS | 事件面板空白（两面板未共享 x 轴）→ sharex |
| 4 | PASS | 事件解析在数值列上失效（`parse_period` 只认字符串）；网络标签压点；地图图例框盖住终点 |
| 5 | PASS | 小倍数跨缺失点直连（看起来像插值）→ NaN 断线 |
| 6 | 2 FAIL（07/10） | 规则复核改三档时，`checks` 里引用了尚未赋值的 `thr`（无 threshold 即崩）；同时"时间口径"警告对 1–12 的月份数字列误报 |
| 7 | 13/13 PASS | `thr` 改用 `p.get("threshold")`；口径警告只在"疑似时间列解析失败"时触发；ex07 标题与实参对齐 |

每轮都取回 PNG 逐张目检，不是只看 PASS。当前 13 张全部通过目检。

**没做的验证**：色盲模拟（只有色板约束，没有模拟渲染）、体数据的独立重建对照、音高的盲听辨识。这三项在 audit 的 `limits` 里写明。

## 与原包的关系

- 方法依据：`bv-01`~`bv-20` 的 `references/practice.md`（未复制进本包，需要时回查原包）。
- 路由表：原 `beautiful-visualization-workbench/references/catalog.md` 的 20 章主题，压缩为 `routes.ROUTES`。
- 不是替代关系：原包讲"为什么这样画"，本包只管"按这个方法把图跑出来并留下审计"。
- 20 章里 01/20 的产出是文字结论，本包用 `review` 子命令执行（评审 spec 配置），不产图。这是设计取舍，不是遗漏。

## 已知边界

- 不做交互式图表（D3/ECharts），交付静态图 + 审计。
- 图类型由 `chapter` 决定，不提供"任意数据 → 任意图"的通用绘图，避免口径漂移。
- 07/08/10 的阈值、11 的取数区间、17 的音高映射属分析判断，必须由调用方给；不给会 warn 并记入 audit。
