# bv-skills v2.1.1

把 `beautiful-visualization-skills-v1.0.0`（1 个路由工作台 + bv-01~bv-20）重组为**一个可执行的 skill + 10 个渲染器 + 审计产物**。

原包 21 个 skill 里 0 个 `.py/.sh/.js`，20 章方法是纯文档，执行时靠人读懂再手写脚本。
本包保留方法中的可判定部分并固化为代码，其余（分析判断、数据选期）仍由调用方决定。

## v2.1.1 改了什么

v2.1.0 解决了「名称不直观」和「必须知道第几章才能出图」，但例子还是 5 份散点样例，只能当补充说明看。这一版把**例子本身当成说明书**：17 个类型每个都有一份能跑的 spec 和它自己的数据文件，照着改就能用。

| 问题 | 处理 |
| --- | --- |
| 例子只覆盖 5 个类型，其余要自己读参数表 | 17 个 `kind` 各一份 `ex_<kind>.json` + 自带 csv，共 18 份 spec（另加 1 份 `chapter` 写法） |
| 例子是补充材料，不是说明书 | `references/examples.md` 重写为按「我想看什么」检索的索引：每行给数据形状、该看到什么、换数据改哪几行 |
| 照抄例子仍会踩坑 | 修掉三处会让例子跑不出来或看不清的问题（见下表） |
| 图上的数字看不清 | 矩阵按底色亮度自动取黑/白字；关掉穿过色块的网格线 |
| 类别顺序反直觉 | 矩阵轴改为「数值轴升序、文本轴按首现顺序」，中文不再按码点排（原先是 电话→线上→门店） |

修掉的三处缺陷：

1. `render_multimodal` 把 csv 读出的字符串直接参与音高计算 → `TypeError`。现在统一转数值，非数值报 `BV_ERROR` 并指出是哪一格。
2. `render --spec` 碰到 `review`（01/20 章）直接报 `unknown renderer`。现在走「只评审、不产图」分支，退出码 0/2。
3. `review`/`validate` 不按 spec 目录解析 `data.path`，在包根以外运行就找不到 csv。现在先试 cwd、再试 spec 所在目录。

## v2.1.0 改了什么

v2.0.0 有两个使用层面的问题：市场名称「bvkit 一键出图」看不出是画什么图的；说明要求使用者先知道「第 02 章」才出图，而章节号是内部编号，对外部使用者没有意义。

| 问题 | 处理 |
| --- | --- |
| 名称不直观 | `display_name` 改为「数据图表一键出图」，中英描述改为按意图触发，不再以章节号开场 |
| 不知道选哪章 | 新增 `kind` 意图层（17 个）：`trend`/`heatmap`/`network`/`facets`/… 各自映射到 chapter，spec 只写 `kind` 即可出图 |
| 查不到该选什么 | 新增 `guide` 子命令，按「你想看什么」列出全部 kind 与所需数据形状 |
| 章节号丢失后口径复核失效 | `validate`/`review`/`render` 三处都把解析出的 chapter 注入 spec，规则复核不因用 kind 而跳过 |
| 名称改动波及已发布资产 | `name`（包标识 `bvkit-oneclick-charts`）保持不变，只改展示字段，市场 ID 与版本更新关系不受影响 |

`chapter` 仍可用，与 `kind` 等价；它现在只出现在 `audit.json` 里做溯源，不再是使用前提。

## 目录

```
bv-skills-v2.1.1/
└── skills/bvkit-oneclick-charts/
    ├── SKILL.md                 # agent 入口 + 市场字段（WorkBuddy 8 个必填项已齐）
    ├── scripts/                 # 9 个模块平铺（无子目录）
    │   ├── core.py              # 字体探测/调色板/audit/导出
    │   ├── validate.py          # 编码、类型、年月、缺失、重复、越界
    │   ├── routes.py            # kind → chapter、20 章 → renderer、每章口径规则
    │   ├── renderers.py         # timeseries/matrix/network/smallmultiples/geo/volume/multimodal/animation
    │   ├── renderers2.py        # scatter/wordcloud
    │   ├── review.py            # 渲染前静态评审 + 渲染后规则复核
    │   ├── selftest.py          # 13 个样例 + 5 个反例
    │   ├── cli.py               # guide/list/inspect/validate/review/render/selftest（入口）
    │   └── check_skill.py       # 按 WorkBuddy 规范自检本包
    └── references/
        ├── examples.md          # 说明书：17 行「我想看什么 → 用哪个例子」索引
        ├── chapters.md          # 20 章 → 图元 → 参数 → 必做口径（回查用）
        ├── params.md            # 10 个渲染器参数表
        ├── errors.md            # 错误码、退出码、"图不对但不报错"排查
        ├── ex*.json             # 18 份 spec（17 个 kind + 1 个 chapter 写法）
        └── *.csv                # 11 份示例数据
```

目录取舍：`bvkit/`、`examples/` 顶层目录名不在 WorkBuddy 白名单内；且市场解析器**只接受两级目录**（根/一级/文件），三级会被判「目录层级超限」。因此 python 模块直接平铺到 `scripts/`（模块间用同目录 `import`，入口 `scripts/cli.py`），spec 与 csv 平铺到 `references/`。`SKILL.md` 位于包根层，zip 解开第一层即是它。

## 装什么

```bash
python3 -m pip install matplotlib numpy
python3 -m pip install networkx wordcloud   # 仅 07/08/10、15 与 03 需要
```

中文字体（缺了会 `BV_FONT` 中止，不会出豆腐块）：

```bash
sudo apt-get install -y fonts-wqy-microhei    # 或把 ttc 放到 ~/.local/share/fonts/
```

## 先验证，再交付

```bash
cd skills/bvkit-oneclick-charts
python3 scripts/check_skill.py .                          # 市场格式自检（含目录层级）
python3 scripts/cli.py selftest --workdir /tmp/bvkit_selftest
python3 scripts/cli.py guide                              # 该选哪种图（不用记章节）
python3 scripts/cli.py render --spec references/ex_trend.json     # 照抄一个改
python3 scripts/cli.py render --spec references/ex_review.json    # 只评审，不产图
```

一次跑完全部例子：

```bash
for f in references/ex*.json; do python3 scripts/cli.py render --spec "$f"; done
```

`selftest` 会产出 13 张图 + 2 个附件（wav/gif），并跑 5 个反例：

1. `2019.11` 必须解析成 2019.8333（不是 2019.11）
2. 关闭 0 基线且无理由 → 拒绝
3. 双 y 轴 → 拒绝
4. 缺失格 → 不补零、holes 计数正确
5. 时间列口径 → 写入 audit

## 这一版验证到什么程度

在服务器（anaconda python3.14 / matplotlib 3.11.0 / WQY MicroHei）上，v2.1.1 的结果：

| 项 | 结果 |
| --- | --- |
| `check_skill.py` | PASS（8 个必填字段齐、白名单干净、目录 ≤2 层） |
| `selftest` | 13/13 章 PASS，5/5 反例 PASS |
| 18 份示例 spec | 17 个 kind 全部 exit=0；`ex_review` 只出评审清单（exit=0，无图） |
| 产物 | 每个成功例子落 `.png` + `.audit.json` + `.audit.md`，`ex_animation` 另出 `.gif`，`ex_soundmap` 另出 `.wav` |
| 目检 | 取回 13 张 PNG 逐张看过：词云/散布/体切片/动画双帧/音高映射/轨迹/期望-实际/共现/热图/时间窗/矩阵/相似网络 |

本轮目检改出来的问题就是上面"修掉的三处缺陷"里第 4、5 行的两条（数字被网格线切、深色格黑字、中文按码点排、小时标签显示 `0.0`）。

前 7 轮迭代修掉的：判定门槛按扩展名分设、WQY 无 bold、事件面板 `sharex`、`parse_period` 需接受 int/float、缺失点 NaN 断线、`thr` 未定义、时间口径警告误报。

**没做的验证**：色盲模拟（只有色板约束，没有模拟渲染）、体数据的独立重建对照、音高的盲听辨识。这三项在 audit 的 `limits` 里写明，也没有替用户判断"某个阈值选得对不对"——那属于分析决策。

## WorkBuddy 提交记录

| 项 | 值 |
| --- | --- |
| 平台 | open.workbuddy.cn 技能市场 |
| 资产 ID（平台侧） | `os_d3402337d1449c2e` |
| 市场技能 ID | `skill_2120874585747382272` |
| 市场展示名称 | 数据图表一键出图（v2.0.0 时为「bvkit 一键出图」） |
| 市场展示分类 | 数据分析 |
| 服务类目 | 工具 - 图片处理 |
| 价格 | 免费 |
| 版本 | v2.0.0 已发布；v2.1.0 审核中；v2.1.1 待定 |
| 开发者 | 上海老涂 |
| 提交 / 发布 | 2026-11-12 18:28 提交 v2.0.0，21:41 发布；22:05 提交 v2.1.0（审核中） |

v2.1.0 走「更新版本」入口，平台沿用同一资产 ID `os_d3402337d1449c2e`，未新建资产。
step2 由包内 frontmatter 自动解析出名称「数据图表一键出图」、能力介绍、3 条示例与版本号；
市场展示分类与类目沿用上次的「数据分析 / 工具 - 图片处理」；step3 汇总无误后提交。

上传包是 `workbuddy-bvkit-oneclick-charts.zip`（根层 = `SKILL.md` + `references/` + `scripts/`）。
首轮上传曾失败在「目录层级超限 — 仅支持两级目录」，平铺后解析通过并生成技能 ID。

**注意版本错位**：v2.1.0 是 22:05 提交审核的包，里面只有 6 份示例；v2.1.1 的 18 份示例与渲染器修复不在那次提交里。要让市场侧的包与仓库一致，只有两条路：撤回 v2.1.0 重提 v2.1.1，或等 v2.1.0 通过后再发 v2.1.1。哪条由发布者定。

## 与原包的关系

- 方法依据：`bv-01`~`bv-20` 的 `references/practice.md`（未复制进本包，需要时回查原包）。
- 路由表：原 `beautiful-visualization-workbench/references/catalog.md` 的 20 章主题，压缩为 `routes.ROUTES`。
- 不是替代关系：原包讲"为什么这样画"，本包只管"按这个方法把图跑出来并留下审计"。
- 20 章里 01/20 的产出是文字结论，本包用 `review` 执行（评审 spec 配置），不产图。这是设计取舍，不是遗漏。

## 已知边界

- 不做交互式图表（D3/ECharts），交付静态图 + 审计。
- 图类型由 `kind` 决定（底层仍是 20 章的方法），不提供"任意数据 → 任意图"的通用绘图，避免口径漂移。
- 07/08/10 的阈值、11 的取数区间、17 的音高映射属分析判断，必须由调用方给；不给会 warn 并记入 audit。
- `map` 与 `route` 共用 `geo` 渲染器，区别只在数据意图：`route` 强调沿途顺序与时长，`map` 强调起点终点。
