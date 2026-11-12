# 错误码与处理

## BV_FONT

```
[BV_FONT] no CJK font found; bvkit refuses to render (would produce tofu boxes)
```

原因：系统没有中文字体。**bvkit 不会降级出豆腐块图**，直接中止。

处理（按环境任选一）：

```bash
# Ubuntu/Debian
sudo apt-get install -y fonts-wqy-microhei
# 无 sudo：把字体装到用户目录
mkdir -p ~/.local/share/fonts && cp wqy-microhei.ttc ~/.local/share/fonts/
```

或在 spec 里给绝对路径：

```json
{"font_path": "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"}
```

内置探测顺序：`~/.local/share/fonts/wqy-microhei.ttc` → 系统 wqy → Noto CJK → 文鼎 → `C:/Windows/Fonts/msyh.ttc` → `simhei.ttf`。

## BV_DATA

| 报文 | 原因 | 处理 |
| --- | --- | --- |
| `data file not found` | 路径错 | 检查 `data.path`，相对路径以 spec 所在目录为基准 |
| `cannot decode ... as utf-8 or gbk` | 编码既非 UTF-8 也非 GBK | 用 `iconv` 转码；带 BOM 的 UTF-8 已自动识别 |
| `empty table` | 0 行 | 检查筛选条件 |
| `json must be an array of objects` | JSON 是对象或嵌套 | 用 `{rows:[...]}` 或顶层数组 |
| `xlsx needs pandas + openpyxl` | 缺依赖 | `pip install pandas openpyxl` |

## BV_SPEC

| 报文 | 原因 |
| --- | --- |
| `spec needs 'chapter'` | 没写章节号 |
| `unknown renderer` | `renderer` 拼错 |
| `timeseries needs params.x` | 缺必需参数 |
| `x column has unparsed values` | 时间列里有无法解析的值（如"约2019年"） |
| `wordcloud renderer needs the 'wordcloud' package` | 未安装 wordcloud |

## 退出码 2：数据核验失败

stdout 会列出 `[error]` 项，常见：

- `重复主键`：`primary_key` 指向的列有重复，会破坏矩阵/聚合。
- `整列为空`：该列全空，不能作为维度或数值。

确认数据本身没问题（比如重复是设计如此），再加 `--force`；audit 里会写明强制通过。

## 退出码 3：评审拦截

这些是**方法层面的错误**，不是环境问题，不要用 `--force` 掩盖：

| 规则 | 触发条件 |
| --- | --- |
| `no_dual_axis` | params 里有 `dual_axis`/`secondary_axis` |
| `no_truncated_baseline` | `zero_baseline: false` 且无 `baseline_reason` |
| `static_alternative` | 动画设了 `static_alt: false` |
| `must_have_title` | 没有 `title` |

## 常见"图不对"而不是"报错"

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 事件点全挤在左边 / 不显示 | 时间列没进 `date_columns`，字符串没被解析 | 加 `"date_columns":["ym"], "date_format":"ym"` |
| 月份串位（11 月变 1.1 月） | 把 `2019.11` 当小数 | 同上；`parse_period` 是唯一正确入口 |
| 网络挤成一团 | spring 布局 | `"layout": "kamada_kawai"` |
| 网络只有孤立点 | 阈值过高 | 降 `threshold`；audit 的 `edges_after_threshold` 会显示 |
| 小倍数看起来有值 | 缺失被当作 0 或连线 | bvkit 已断线 + 虚线标注；若数据本身是 0 而非缺失，改数据 |
| SVG 里中文变方框 | SVG 未内嵌字体 | 同时出 png 用于交付；或 `formats:["png","pdf"]` |
