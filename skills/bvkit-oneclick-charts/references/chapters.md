# 20 章 → 渲染器 → 必做口径

`chapter` 是 spec 的唯一必填路由键。下表每一行对应一次 `render`。

| 章 | 原方法主题 | renderer | 关键 params | 必做口径（review 会查） |
| --- | --- | --- | --- | --- |
| 01 | 图表有效性评审 | review | 无（只评审 spec） | 标题、数据性质、无双轴、不截断基线 |
| 02 | 探索叙事（问题+背景） | timeseries | `x`,`series`,`events` | 时间口径声明、0 基线、事件按真实时间对齐 |
| 03 | 加权词云 | wordcloud | `word`,`count`,`top` | 权重口径、右侧核对面板、不跨语料比面积 |
| 04 | 多变量颜色编码 | matrix | `rows`,`cols`,`value`,`cmap` | 色觉友好、灰度可分 |
| 05 | 任务中心路线图 | geo | `routes` | 起点标记、任务写明 |
| 06 | 时空轨迹 | geo | `routes`（含 `t`） | 多轨迹共起点不叠字、采样密度注明 |
| 07 | 双模网络/共现投影 | network | `source`,`target`,`weight`,`threshold` | 阈值声明、孤立节点单列 |
| 08 | 跨期相似网络 | network | 同 07，两期各跑一次 | 阈值声明、两期同尺度 |
| 09 | 相似性地图 | scatter | `x`,`y`,`cluster` | 轴有标签、异常点区分 |
| 10 | 网络 + 指标联动 | network | 同 07 | 选中态配色一致 |
| 11 | 版本历史时间线 | timeseries | `x`,`series` | 时间正序、粒度匹配跨度、不插值 |
| 12 | 多维交叉计数 | matrix | `rows`,`cols`,`value` | 计数和等于 n、每轴类别可读 |
| 13 | 可比小倍数 | smallmultiples | `facet`,`x`,`y`,`ncol` | 缺失显式标注（断线+虚线）、共享轴 |
| 14 | 期望 vs 实际 | matrix + `expected` | `rows`,`cols`,`value`,`expected` | 双面板、空洞红框 |
| 15 | 实体共现矩阵 | matrix | `rows`,`cols`,`value` | 采集完整性提示、对角为 0 |
| 16 | 活动日志聚合 | matrix | `rows`,`cols`,`value` | 时间窗与粒度写明、尺度写明 |
| 17 | 视觉 + 声音 | multimodal | `metrics`,`pitch_base`,`write_wav` | 模拟/观测区分、映射公式写出 |
| 18 | 体数据切片 | volume | `grid`,`peaks` | 参数记录、统一值域 colorbar、切片位置入标题 |
| 19 | 动画 | animation | `points`,`frames`,`fps` | 静态替代、身份保持、固定轴范围 |
| 20 | 视觉论证审计 | review | 无 | 每个断言配可指认证据 |

## 哪些章节本质不可"一键出图"

01 与 20 的方法产出是**文字结论**（哪张图无效、哪个断言没证据），不是图。bvkit 把这两章做成 `review`：
对一份 spec 执行静态评审，输出 error/warn 清单。这是这两章唯一可执行的形态。

## 参数化的边界

- 07/08/10：阈值由数据决定，必须由调用方给；不给会 warn 并记入 audit。
- 11：取"最近 N 条"还是"最早 N 条"是分析判断，bvkit 只保证时间正序与刻度粒度。
- 17：音高映射是设计选择，公式会写入 audit.params。
- 18：`peaks` 不给则用内置双高斯演示场，audit 会写明"合成标量场"。
