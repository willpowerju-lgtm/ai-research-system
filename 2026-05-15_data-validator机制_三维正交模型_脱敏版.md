---
title: "data-validator 机制 — 金融数据信任的三维正交模型"
date: 2026-05-15
type: personal
tags: ["personal", "Personal", "data-validation", "design-philosophy"]
日期: "2026-05-15"
content_type: "deep_analysis"
summary: "金融投研里 data trust 不是一维 yes/no，而是三个互相正交的维度：信源质量 tier (T1-T4) / 时效性 as_of / 交叉验证 alignment。data-validator registry 给每条 data point 同时存这三个独立标签，下游 skill 引用时三维同时决策。derived data 走木桶原则继承最差 tier，但时效性和对齐度独立计算，不被 tier 覆盖。这是把 data trust 从 ad-hoc judgement 转成可审计工程问题的核心机制，也是 data-validator 作为 cross-cutting QC 放在 L0 基础设施层的根本理由。"
companies: []
themes: ["投研系统", "data validation", "registry 设计", "QC 治理"]
sector: []
key_points:
  - "三维正交模型：tier（信源质量）/ as_of（时效性）/ alignment（交叉验证）三个独立维度，任一不能 cover 其他两个"
  - "T1-T4 信源分级：T1 一手 filing / T2 已验证 vendor / T3 forecast 或单源 web / T4 单源 DR 推断（必 footnote）"
  - "Derived data 木桶原则：继承所有 input 中最差的 tier，永远不可能比最弱的 input 更强"
  - "时效性独立于 tier：T1 + stale 依旧 flag，再硬的财报数字过期了也得降级"
  - "Alignment 独立于 tier：单源即使 T1 也降权，多源 gap 本身就是 alpha 入口"
  - "Registry 同时存三个标签，下游 skill 引用时三维联合决策；这把 data trust 从 ad-hoc judgement 变成可审计工程问题"
  - "data-validator 是 cross-cutting 的，归 L0 基础设施而非业务层 —— 它是每一层都要遵守的物理定律"
---

# data-validator 机制 — 金融数据信任的三维正交模型

> 一份工程实践笔记。
> 写给自己对 data-validator skill 设计经验的总结，以及任何在做"AI 系统怎么保证数据可信"的人。

---

## 一、问题缘起：data trust 不是一维 yes / no

最早做财务建模 skill 的时候，data trust 这件事是隐式的——LLM 在 prompt 里被告诉"数据要来自财报"，输出的时候顺手在脚注里写一句"来自 XX 年报第 N 页"，就算交代了。

跑了两个 IC Memo 之后这套就崩了。

崩的方式很多样：
- 某个 cell 写的是"来自年报"，但实际是 LLM 把卖方 forecast 当成年报披露照抄了
- 某个 ratio 看着对，但拆开来看分子是 T1 一手数据，分母是 LLM 推算的——derived 出来的东西比 input 还"硬"
- 某个数字标的是"2024 年报"，但用的是 2024Q3 季报的数字，时间窗错位
- 同一个营收数字，年报披露和管理层电话会口径差 3%，LLM 挑了一个就用

每一类错误的根因都不一样。但表面上它们看起来都是"数据错"——直到你意识到 data trust **本身不是一维的**。

一条数据可不可信，至少由三个互相正交的维度决定。每一个都不能 cover 另外两个。

这篇就是把这三个维度拆开讲清楚，以及 data-validator registry 是怎么设计来同时跟踪这三个维度的。

---

## 二、维度一：信源质量（tier）

**这条数据来自哪里，决定了它的可信天花板。**

借鉴 deep-research-workflow + data-validator 的 registry schema，分四个 tier：

| Tier | 性质 | 典型来源 | 处理 |
|------|------|----------|------|
| **T1** | 一手硬数据 | 招股书 / 年报 / 季报 / 官方公告（落到 filing 文档的口径） | 直接引用，可进交付物正文 |
| **T2** | 已验证 vendor | Capital IQ / yfinance / AKShare 等数据 vendor 直接输出的**非预测**字段 | 抽检后引用 |
| **T3** | Forecast / 共识 / 单源 web | 卖方一致预期、Bloomberg 共识（≥ 2 underlying）、公众号披露、单一调研口径 | 需要 cross-validation 才能用 |
| **T4** | 单源 DR 推断 | Gemini DR 单源结论 / 弱推断 | 必须 footnote 标注，不能进交付物正文 |

Tier 在数据入库时就 assign，不允许后续修改（除非主动经过 verification 流程升级）。

### Derived data 走木桶原则

复合指标继承所有 input 中最差的 tier，永远不可能比最弱的 input 更强：

```
inputs: [T1, T1] → derived tier = T1
inputs: [T1, T2] → derived tier = T2
inputs: [T1, T4] → derived tier = T4    ← worst case 传播
inputs: [T3, T4] → derived tier = T4
```

这条规则是反直觉但必要的。一个 WACC 由 risk-free rate (T1) / equity premium (T2) / beta (T2) / tax rate (T1) 算出来，看着挺"硬"——但如果 ERP 用的是某个卖方研报里的单一估计（T3），那整个 WACC 就是 T3，下游 DCF 估值也是 T3，不管中间步骤有多严谨。

木桶原则的实现要求 derived data 必须以 Excel native formula 形式存储，而不是 hardcoded value：

```
正确：   ws["E5"].value = "=B2*(1-C3)"         ← formula，可审计
正确：   ws["D8"].value = "=WACC_calc!B5"      ← 跨 sheet 引用
错误：   ws["E5"].value = 0.082                ← hardcode 杀死 audit trail
错误：   ws["E5"].value = float(wacc_result)   ← hardcode 杀死 audit trail
```

只有 input 参数（risk-free rate / beta / ERP 等）允许 hardcode——这些 ARE 模型输入，不是推导结果。其他所有 derived 字段如果用 hardcode，木桶原则就 silently 失效了。

---

## 三、维度二：时效性（as_of）

**这条数据是什么时候的。时效性和质量是独立维度——不能用 T1 来 cover staleness。**

这是 tier 系统最容易被忽视的盲区。"年报数据"听起来很硬，但如果年报是 2024 年的，现在是 2026 年中、公司已经发了三个季报，那这条年报数据用在估值里就是 stale 的。再硬的财报数字也经不起"上一财年还没更新到当前财年"这种 staleness。

所以每条 data point 入库时必须绑定 `as_of date`，记录这条数据反映的是什么时候的事实。

### Registry 在交付前 gate check 时校验 as_of

data-validator 不做每日巡检（那是 librarian 在 wiki 页面上的事）—— 它的工作发生在**交付前 gate check 阶段**：

- 每个交付物（IC Memo / 三表模型 / 卖方 report）声明自己的 vintage 要求（"基于 FY25 中期 outlook"）
- Registry 把声明的 vintage 和被引用 data point 的 `as_of_date` 做对比
- 任一 data point 超出 vintage 容忍窗口 → 自动 flag，必须显式 acknowledge 或换源

即使原本是 T1 一手数据，过期了也得降级或下架。Registry 关心的是"这条数据用在这个交付物里是否 still valid"，不关心"今天它本身有没有更新版本"——后者是 librarian 的活。

### 为什么时效性必须独立于 tier

如果时效性吸入 tier（比如"T1 自动包含 ≤ 90 天"），就会出现两个问题：
1. **过度严格**：一份 5 年前的招股书披露的"公司创始团队背景"是 T1，永不变化，不该因为是 5 年前就降级
2. **过度宽松**：一份 2 周前的年报 T1，但分布在不同章节的数据可能 as_of 不同（资产负债表 12/31 vs 业务讨论 3 月）——不能用一个统一的 staleness threshold cover

时效性必须按 data point 粒度独立跟踪，每条都自己的 `as_of`，每条都自己的 staleness rule。Tier 管"这条数据来自哪"；as_of 管"这条数据反映的是什么时候"。两件不同的事。

---

## 四、维度三：交叉验证对齐（alignment）

**这条数据有多少独立来源在说同一件事。alignment 也是独立维度——单源数据天然该打折，即使是 T1。**

单一 source 的数据即使来自年报，也保留一份怀疑：
- **口径错位**：年报披露的"营收"可能是合并口径，卖方建模用的可能是非合并；管理层电话会讲的"核心业务收入"可能剔除某项一次性收入
- **时间窗错位**：年报是日历年口径，但行业惯例可能是 fiscal year；月度数据来源可能用的是不同截止日
- **统计范畴错位**：管理层口径里的"出海销量"可能含 KD 组装，但海关数据是整车出口；不同来源可能是不同范畴

所以单源 T1 即使是 T1，也保留怀疑。多源对齐才是真正的高 trust。

### 仲裁规则

多源冲突时，按 tier + 时间锚定自动仲裁：

- **Tier 优先**：T1 覆盖 T2，T2 覆盖 T3
- **同 tier 冲突**：按时间锚定，新数据覆盖旧数据
- **真模糊的 gap**（两份 T1 互相打架 / 时间太接近无法分先后）：raise 给人介入，不强行选边

### Gap 本身就是 alpha 入口

最有意思的现象是：**买方 alpha 经常就藏在"同事实多源口径不一致"的 gap 里**。

- 卖方 forecast 和管理层指引不一致 → 哪边对？为什么不一致？
- 调研拿到的渠道反馈和报表趋势相反 → 调研早还是报表早？哪个是先行信号？
- 公众号披露的运营数据和 IR 口径方向不一致 → 公众号可能拿到了一手数据而 IR 还在按上一周期口径
- 招股书里的市占率和卖方写的不一致 → 卖方用的是不同口径，但哪个口径是"市场认知"？

这些 gap 一旦被系统显式标出来，就是研究该深挖的方向。**所以 alignment 维度的产出不只是"该用哪个数字"的清单，更是一份"值得追问的问题"清单**。

这一点之前在 librarian 升级笔记里有专门展开——B 级（T3）信源的存在意义不是和 A 级（T1/T2）竞争权威性，而是和 A 级形成对照。它们的"软"反而是价值所在——只有软信息才能携带 A 级硬数据还没沉淀进去的 forward-looking 信号。

---

## 五、data-validator registry 的设计选择

三维互相正交意味着**不能用单一指标概括 trust**。所以 data-validator registry 给每条 data point 同时存三个独立维度的标签，每个维度都是 first-class 字段。下面是一条真实 data_point 在 v2.1 schema 下长什么样：

```json
{
  "id": "AAPL_revenue_FY24Q3",
  "label": "Apple FY24 Q3 净销售额",

  // ── 数据本身 ──
  "value": "85.78",
  "value_numeric": {"point_estimate": 85.78},
  "unit": "Bn",
  "currency": "USD",

  // ── 维度一：信源质量 (tier) ──
  "source_tier": "T1",
  "source_type": "quarterly_report",
  "sources": [
    {"name": "AAPL FY24 Q3 10-Q",
     "timestamp": "2024-06-29",
     "retrieval_method": "NLM",
     "retrieval_date": "2026-05-20"}
  ],

  // ── 维度二:时效性 (as_of) ──
  "entity":        "AAPL",        // ticker / 短码，支持跨 deck 时序聚合
  "period":        "FY24-Q3",     // 报告期 token (FY2024 / 2024-Q3 / TTM-... / spot-...)
  "as_of_date":    "2024-06-29",  // 数据代表的 ISO 日期 (staleness 主输入)
  "as_of_type":    "period_end",  // period_end / snapshot / ttm_cutoff / annual / monthly
  "verified_date": "2026-05-20",  // QC 触碰时间 (仅作 as_of_date 缺失时的 fallback)

  // ── 维度三:交叉验证 (alignment) ──
  // 多源在 sources[] 同时存,conflict 按 tier + as_of 仲裁
  // T3 强制 ≥2 sources;T4 允许单源但必须 footnote 标注

  // ── 通用元数据 ──
  "data_category":      "financial_metric",
  "geographic_scope":   "US",
  "notes":              "Q3 净销售额 YoY +5%, 主要来自 Services 板块加速",
  "used_in":            [{"slide": "P3", "location_ref": "table_cell"}],
  "update_history":     []
}
```

字段对应三个维度：

- **维度一 信源质量** → `source_tier` + `source_type` + `sources[]`
- **维度二 时效性** → `as_of_date`（数据代表的日期）+ `as_of_type`（数据形态：快照 / 期末 / TTM 截止 / 年度 / 月度）+ `period`（人读 token）+ `entity`（公司短码）
- **维度三 交叉验证** → `sources[]` 数组本身 + cross-validation 规则（T3 必须 ≥2 sources，T4 单源但必须 footnote）

`as_of_date` 拆成 first-class 字段的关键意义：staleness check 优先吃它而不是 `verified_date`——FX / 股价 / IV 这类 spot 数据不会因为今天 QC 过就显得"新鲜"。`as_of_type` 进一步把"数据形态"显式标出来，让 validator 能用不同 staleness 阈值老化（snapshot 数据日级别 stale，财报数据季度级别 stale）。

`entity` 字段单拎出来的实际价值是跨 deck 时序聚合：要"拉 AAPL 所有历史季度 revenue"这种 query 直接 grep `entity:"AAPL"` 再按 `as_of_date` 排序就行，不用靠在 id 后缀里硬塞日期再 regex —— 这是把 registry 从单 deck 工具升格为可跨 deck 复用的资产库的关键。

### 两套 schema 的关系：DRW 嵌套 vs data-validator flat

实际跑起来 registry 存在两套 schema，都遵守"三维独立 first-class 字段"的设计原则，只是组织方式不同：

| Schema | 结构 | 适合的场景 | 衍生数据怎么处理 |
|---|---|---|---|
| **deep-research-workflow** | L1 原子数据 + L2 衍生数据嵌套（`derivation.depends_on`） | 研究报告全文（docx）：每个数字都有 L1 / L2 身份，依赖图原生在数据条目里 | L2 显式声明 `depends_on: [L1-...]`，木桶 tier 从依赖图自动算 |
| **data-validator** | 扁平 `data_points[]` 列表 + 单独的 `dependency_graph` 块 | PPTX / DOCX / XLSX cell-level 追溯：每个 cell 对应一个 id，slide / location 精确定位 | 依赖关系另存 `dependency_graph` 块，木桶原则按规范执行 |

两套 schema 共用同一套 `as_of_date` / `as_of_type` / `source_tier` / `entity` 字段语义，可以互相 import 转换。**选哪套不重要，重要的是三维独立标签的强制性**——任何 registry 都必须能回答"这条数据来自哪里 / 是什么时候的 / 有几个来源在说同一件事"三个独立问题。

下游 skill 引用时三个维度同时决策：

- **Derived data** 走木桶原则继承最差 tier（见 §二）
- **时效性**独立计算，不被 tier 覆盖——T1 + stale 依旧 flag（见 §三）
- **Alignment** 独立计算，单源即使 T1 也降权（见 §四）

### Registry 是 source of truth，Excel 只是视图

Registry 以 JSON 形式持久化在磁盘，是机器可读的 single source of truth。Excel 里的 `_Registry` sheet 是给人看的视图，从 JSON 导出生成。两边永远要保持同步——验证脚本永远以 JSON 为准。

这样做的好处是：
- **可审计**：每个数字都能追溯到 source + tier + as_of + sources，不允许 LLM 凭空生成
- **可重放**：跑同一个 registry 应该永远产出同样的 verdict（确定性）
- **可 diff**：模型 v2 vs v3 的差别可以通过 registry diff 精确定位到哪些 data point 改了

### 为什么"为什么这条数据可以进 deck"不再是 LLM 判断

引入 registry 之前，"这条数据可不可以进 deck"是 LLM 临场判断——LLM 看到 prompt 里说"数据要来源准确"，就 case-by-case 决定是否引用。这种判断是 ad-hoc 的，不可审计，不可重放。

引入 registry 之后，这个判断变成了 registry 在交付前自动跑的三维检查：

```
gate_check(data_point):
    if tier in [T3, T4] and len(sources) < 2:
        return BLOCK  # alignment 不够
    if staleness(as_of_date) > threshold[as_of_type]:
        return BLOCK  # 时效性不够 (阈值按 as_of_type 区分)
    if tier == T4 and not has_footnote:
        return BLOCK  # 必须 footnote
    if abs(date_of(period) - as_of_date) > 31_days:
        return WARN   # period token 和 as_of_date 不一致 (copy-paste 失误)
    if category in PERIOD_CATS and as_of_type == "snapshot":
        return WARN   # 语义冲突 (revenue 不该是 snapshot)
    return PASS
```

这把 data trust 从 ad-hoc judgement 变成了**可审计的工程问题**。LLM 不再是 trust 的判断者，registry 才是。

最后两条 WARN 是 v2.1 实施过程才意识到要加的：用户写 `period="2024-Q3"` 但 `as_of_date="2025-09-30"` 是典型 copy-paste 失误，必须立刻报警；`revenue` 标 `as_of_type="snapshot"` 是把"快照型"和"期间型"两种数据形态混用，semantic 上就是错的。这两条都不是"概念新"，是"概念拆细到字段层面之后才看得见的边界"——写代码反推概念，往往就是这样从抽象的维度切到可落地的字段。

---

## 六、为什么 data-validator 放在 L0 cross-cutting

按系统架构分层，data-validator 是 cross-cutting 的——L4 深度研究在用、L5 输出渲染在用、L3 持仓监控也在用。它不属于任何一个业务层。

把它放在 L0 基础设施（而不是某个业务层下面）的根本理由是：**三维数据信任模型是每一层都要遵守的物理定律**，不是某一个 workflow 的内部细节。

具体表现：
- 财报点评（L3）依赖 tier 仲裁判定 beat / miss 用哪个数字
- IC Memo 生产（L4）依赖三维联合 gate check 决定哪些数字进交付物
- 三表建模（L4）依赖 derived 木桶原则保证 WACC / DCF 的 tier 不被错误抬高
- Deck 渲染（L5）依赖 T4 footnote 标注 rule 决定哪些数字必须有角标
- Librarian 健康检查（贯穿）依赖 as_of staleness 决定哪些 wiki 段落该 flag

如果 data-validator 归在某一个业务层下面，其他业务层引用它就成了"跨层依赖"，破坏了分层的清晰性。把它升到 L0 cross-cutting，所有业务层都把它当成 ambient 基础设施，跟"文件路由"、"web 入口"、"LLM 引擎调度"一样——是上面所有层共用、缺它跑不通的能力。

Layer 0 提供的就是这种 ambient 能力。data-validator 在这里安身立命。

---

## 七、实际使用：三个具体场景

光讲原则容易抽象。下面三个例子展示三维 registry 在真实交付物里怎么工作 —— 每一个对应一个维度起决定作用的瞬间。第一个来自实战（某 OEM onboarding 时的真实分析），后两个是高频典型场景。

### 7.1 案例一：多源拼出单源拼不出的答案（alignment 工作）

给某 OEM 做 onboarding 的时候要回答："为什么 GPM 从 24Q4 的 10.6% 反弹到 26Q1 的 16.0%（+5.4ppt）？"

这种问题没有一个 source 能单独回答。Librarian 在 vault 扫一圈，拼出来的答案来自七个独立来源：

| 来源 | tier | 提供什么 |
|---|---|---|
| AKShare 季度 GPM 时序 | T2 | 季度走势 + 出口占比基线 |
| 卖方 A、B、C 三家拆解 | T3 × 3 | 各自的驱动力分解（口径略有出入） |
| 专家访谈（同业销售总监） | T3 | 验证海外 ASP 溢价 + dealer rebate 口径 |
| IPO 招股书 FY22/23 GPM 历史 | T1 | 历史基线 + 三重国内压低因素披露 |
| 自家 OEM 研究 deck | T2 | 一手综合分析 |

任何一份单看都不完整：卖方三家口径互相略有出入，专家访谈是 view 不是数据，AKShare 只有总数没有拆解，招股书只解释结构不解释当下。七份对齐之后，**+5.4ppt 的反弹被分解成三个性质完全不同的驱动**：

| 驱动力 | 贡献 | 性质 | 可持续性 |
|---|---|---|---|
| 出口占比 48% → 65% mix shift | +1.0-1.3ppt | 结构性 | Q1 有季节性，全年回到 50-55% |
| **24Q4 异常低基数均值回归** | **+2.0-2.5ppt** | **一次性** | **不可持续 —— 已完成** |
| 海外 vs 国内毛利剪刀差 | +0.5-1.0ppt | 结构性 | 取决于国内价格战 + NEV mix |

**最关键的 finding**：**+5.4ppt 里有近一半（+2.0-2.5ppt）是均值回归而非结构性改善**。单看任一份卖方研报都说不出"哪部分是一次性"——卖方倾向把所有 GPM 提升都说成结构性。alignment 维度让多源对照之后，一次性与结构性的边界变得清晰，进一步得出结论：

> **16% 大概率是周期高点（Q1 季节性 + 出口占比峰值），全年 14-15% 更现实**。

这个判断 single source 看不出来 —— 只有 alignment 维度把多源对齐到同一个事实模型上，才能识别哪个 driver 是"会消失的"。

所以"卖方研报"个体上是 T3（单源未验证），但同一事实多份对齐之后整体 trust 显著提升 —— 这正是 alignment 独立维度的设计意图。

### 7.2 案例二：木桶原则避免 silent tier inflation（tier 工作）

WACC 计算长这样：

```
WACC = (E/V) × [Rf + β × ERP] + (D/V) × Rd × (1 − T)
```

五个 input 各自有自己的 tier：

| Input | tier | 来源 |
|---|---|---|
| Rf（10Y 国债） | T1 | FRED 直接拉 |
| β | T2 | yfinance 历史回归 |
| ERP | **T3** | Damodaran 网站单源估计 |
| Tax rate T | T1 | 年报 effective tax rate |
| E/V, D/V | T1 | 年报资产负债表 |

没有 registry 之前 LLM 会做什么？算完 WACC 后把结果当成"硬数据"用 —— 因为大部分 input 是 T1。下游 DCF 估值出来也"看着挺硬"。

有了木桶原则之后：

```
WACC.tier = min(Rf.tier, β.tier, ERP.tier, T.tier, capital_structure.tier)
          = min(T1, T2, T3, T1, T1)
          = T3
```

WACC 实际是 T3 —— 因为 ERP 是单源 Damodaran。下游 DCF 估值 inherit T3，所以 DCF 数字**不能直接进 IC Memo 正文**，必须 footnote 标注"假设 ERP 6% 来自 Damodaran 单源估计"。

这条规则反直觉但救命 —— 它强制 LLM 在使用 derived 数据时面对真实 tier，而不是被 mostly-T1 inputs 的"硬度"骗到。

### 7.3 案例三：staleness 击穿"两份 T1"伪对齐（as_of 工作）

写 IC Memo 经常碰到这种情形：某指标在年报里有数（T1），在后续季度业绩交流里管理层口头修订了（T1）。tier 维度看两份都是 T1，看起来"互相对齐"。

举一个典型场景：

| Source | tier | as_of | 内容 |
|---|---|---|---|
| FY24 年报披露 FY25 capex 指引 | T1 | 2024-12-31 | "FY25 capex ~50 亿" |
| FY25 Q1 业绩交流管理层口径 | T1 | 2025-04-30 | "FY25 capex 上调到 60-65 亿（投资某新工厂）" |

如果只看 tier 维度：两份都是 T1，看起来对等。LLM 可能：
- 取其中一份（运气问题）
- 取平均（更糟，造假数）
- 都引用（让读者自己 reconcile）

**as_of 维度直接击穿这种伪对齐** —— 4 月的管理层口径是 2024 年报披露之后 4 个月的更新，应该自动 supersede。registry 在 gate check 时按 as_of 排序，最新口径覆盖旧的指引；旧的指引在 wiki 上保留一份 diff 痕迹（"FY24 年报原指引 50 亿，2025-04 上调至 60-65 亿"），但下游交付物只引用最新的。

类似 case 还有很多：

- 年报披露的某细分业务占比 → 后续季报 disclosed 已经变了
- 上一份卖方 TP → 该卖方新一份研报已经修订
- 三个月前的 Damodaran ERP → 已更新

**共同点**：两个 source 都是高 tier，tier 维度看对等。但 as_of 不同 —— 新的 vintage 自动 supersede 旧的。

如果只有 tier，这种错位 silently 通过。as_of 独立维度把"什么时候的事实"显式标出来，让 staleness 强制流入交付前的 gate check。

### 三个案例共同点

都是 "如果只看一维 trust，数据会 silently 通过 gate"。三维独立标签把这种 silent failure 显式化：

- Case 1 → alignment 让多源拼出 single source 见不到的 finding（区分一次性 vs 结构性）
- Case 2 → tier 木桶让 derived 数据面对真实信源强度（避免 silent inflation）
- Case 3 → as_of 击穿伪对齐（最新 vintage supersede）

三维都不能省，互相不能 cover。这就是为什么 data-validator registry 必须同时存三个独立标签。

---

## 八、跟 Guide / Hook / Eval 的关系

回过头看，这套三维数据信任模型和我之前写的 Guide / Hook / Eval 架构其实是**同一种思路的两个应用**：

- **G/H/E**：把 agent 行为的不可靠拆成 *会过期 / 不会过期 / 必须硬约束* 三个维度，让最值得投资的那一层（Eval）跨模型最抗腐
- **三维数据信任**：把数据可信度拆成 *tier / 时效 / 对齐* 三个独立维度，让"这条数据值不值得用"从 ad-hoc 判断变成可审计的工程问题

两件事的共同点：

> 把一个看似一维的判断问题分解成多维正交的工程问题。不依赖单点判断（任何一点都可能错），让每一维都有自己的约束机制，靠组合保证总体可信。

这是处理"LLM 在高 stakes 场景下不能完全 trust"这件事的通用思路——任何时候 LLM 要做一个"yes / no" 判断，先问自己这个判断是不是真的一维的；如果不是，拆维度，每个维度独立约束，最后组合裁决。

agent 行为这样处理；数据信任这样处理；以后可能还有第三件、第四件事这样处理。

---

## 后记

这套机制不是设计出来的，是踩坑踩出来的。最早做 IC Memo 的时候每条数据都标"来自 XX 报告"就算交代了。两个 deck 之后开始出问题——明明每个数字都"标了来源"，但放在一起就是错的。

意识到三维正交那一刻，很多之前看起来无关的失败模式突然变成了一个统一的故障模型：tier 错位、as_of 错位、alignment 错位。三类故障互相不相关，但都被"data trust 是一维"这个错误假设掩盖了。

拆开三个维度之后，data-validator 的设计就变得几乎是必然的——三个独立标签同时存、derived 走木桶、时效性独立巡检、对齐度独立加权、所有 gate check 在交付前自动跑。代码层面的复杂度其实不高（registry schema 也就一百多行 Python），难的是先把这三个维度从一团叫"data trust"的概念里拆出来。

这是过去一段时间最实际的体感：**好的工程架构往往是先把概念拆对，代码就顺了**。反过来也成立——写代码会反推你把概念拆得更细。"as_of"这个抽象维度，只有真正落到 `as_of_date` + `as_of_type` 两个 first-class 字段，才暴露出"快照型 vs 期间型数据的 staleness 语义完全不同"这个之前没看见的隐含假设。

---

*脱敏说明：本文涉及的具体公司 / ticker / 基金名已隐去，只保留架构与方法论。*
*Last updated: 2026-05-20*
