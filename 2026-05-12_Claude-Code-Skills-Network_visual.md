---
title: "Claude Code Skills Network — 视觉架构图 (Visual Map)"
date: 2026-05-12
type: personal
tags: ["personal", "Personal", "skills-architecture", "visual-map"]
日期: "2026-05-12"
content_type: "deep_analysis"
source_file: "Claude Code Skills Network (2026-05-12 Updated).docx"
summary: "Claude Code 65+ skills 架构全景图，视觉地图版（9 layers · ▌ 板块卡片 · 7 核心数据流 · 6 Eval 域）"
companies: []
themes: ["投研系统", "人工智能", "知识管理", "skills-architecture"]
sector: []
key_points:
  - "9 层架构 L0-L8，65+ active skills"
  - "L0 元技能 / L1 基础设施（通用能力）/ L2 数据采集（具体外部源）/ L3 知识库 / L4 分析情报 / L5 深度研究建模 / L6 输出渲染 / L7 Eval / L8 投研活 Wiki"
  - "核心枢纽：cloud-files-router (文件) / obsidian-librarian (活 Wiki) / web-access (联网) / llm-subagent (AI 引擎)"
  - "四角知识闭环：Obsidian ↔ OneNote ↔ NotebookLM ↔ 云端文件"
  - "Eval 六域：Deck QC / 数据溯源 / 跨模型 / 研究内嵌 / 知识库健康 / 基础设施审计"
  - "Deck 三模板体系 (acme / navy / 机构) + JSON SSOT"
  - "AI 引擎：Claude 主力 + DeepSeek V4-Pro/V3 + 火山方舟 ASR + GPT-4o imagegen + Gemini DR"
  - "七条核心数据流：研究启动 / 财报点评 / IC Memo 生产 / 每日决策 / 卖方研报 / 公众号 / Onboarding 全生命周期"
related:
  - "[[2026-05-12_Claude-Code-Skills-Network_full|Full 完整技术版]]"
  - "[[2026-05-12_Claude-Code-Skills-Network_lite|Lite 精简版]]"
---

# Claude Code · Skills Network — 视觉架构图

> 系统架构全景 · 内部文档 · 脱敏版
> Updated 2026-05-12 · **65+ active skills · 9 layers**

---

## LAYER 0 · 元技能层 — Meta Skills

| Skill | Tag | 功能 |
|---|---|---|
| ★新  **think** | [Design] [Validation] | 写代码前的设计和验证，将想法转化为已验证的计划 |
| ★新  **design** | [UI] [Component] | UI/组件/页面/视觉界面构建 |
| ★新  **read** | [URL] [PDF] [Markdown] | 读取任何 URL/网页/PDF，转换为 Markdown |
| ★新  **write** | [风格] [Anti-AI] | 写作风格修改，剥离 AI 写作模式，使文字自然 |

---

## LAYER 1 · 基础设施 & 通用能力 — Infrastructure & Generic Capabilities

按功能定位划分（不按实现）：这一层提供所有上层 skill 共享的底层能力 —— 文件路由、通用 web 入口、PDF 获取、AI 引擎调度、系统治理。不绑定具体数据源，稳定可复用。

### ▌ 文件路由核心枢纽

| Skill | Tag | 功能 |
|---|---|---|
| **cloud-files-router** | [WebDAV] [文件主干道] | 工作文档/财报/模型文件同步主干道，所有 skill 共享的文件读写入口 |

### ▌ 通用 web 与 PDF

| Skill | Tag | 功能 |
|---|---|---|
| ★新  **web-access** | [搜索] [抓取] [CDP] | 联网通用入口 (搜索/抓取/CDP 登录态)，替代 gemini-router |
| **web-pdf-fetcher** | [Fallback] [IR/PDF] | IR 网站 PDF 下载，绕过 bot 检测与 403 拦截，自动提取 PDF 链接 |

### ▌ AI 引擎路由群

| Skill | Tag | 功能 |
|---|---|---|
| **gemini-deep-research-router** | [Chrome UI] [深度研究] | Gemini Deep Research 专属，提交后即可切走，等待期间并行处理其他任务 |
| ★新  **gpt-imagegen** | [文生图] [CDP] | 文生图默认入口，ChatGPT gpt-4o + CDP + 自动下载 |
| ★新  **llm-subagent** | [DeepSeek] [ASR] | DeepSeek V4-Pro 推理 / V3 轻量 + 火山方舟 ASR 转写，四模式 |

### ▌ 系统治理群  ★ 新增板块

| Skill | Tag | 功能 |
|---|---|---|
| ★新  **tag-pipeline** | [LLM 打标] | vault 未标注 MD 用 LLM 自动打标 + 同步更新 wiki |
| ★新  **session-log** | [跨 session] [状态机] [3 层记忆] | 跨 session 工作台账 + 工作流状态机，防 compact 丢失中间状态。配套**三层记忆机制**：MEMORY.md（常驻索引）/ memory/topic/（按需拉取）/ session-log/（跨 session 台账）—— state 落 disk 不在 context |
| ★新  **codex-review** | [跨模型] [Skill 审查] | 独立模型跨模型审查，覆盖研究/IC Memo/财报/调研等高价值输出 |
| ★新  **health** | [配置] [MCP] | 配置问题检查、MCP 服务器审计、多层健康检查 |
| **data-validator** | [数据 QC] [registry] | 数据来源注册表 + 跨 slide 一致性 + 过时性 + 下游依赖传播；集成于所有交付前 pipeline（建模 / outliner / deck render） |

> ▶ 已移除：**gemini-router**（并入 web-access）· **gemini-imagegen**（被 gpt-imagegen 替代）

---

## LAYER 2 · 数据采集 & 外部源接入 — Data Ingestion

按功能定位划分：每个 skill 对应一类特定外部数据源。任务是把 bytes 落盘 —— 不做分析、不做转换。无论实现是纯 Python wrapper 还是 CDP browser，只要"获取特定数据"就在这一层。

### ▌ 金融数据 API 群

| Skill | Tag | 功能 |
|---|---|---|
| **ak-xq-router** | [A股] [港股] [Consensus] | AKShare + 雪球双源，A股港股全覆盖；内建 Consensus，EPS/NI/Revenue 预测统一口径 |
| **sw-api-router** | [申万] [行业估值] | 申万行业指数 API：PE BAND / PB-ROE / 换手率 / Z-score，6 大模块 |
| **fred-router** | [美国宏观] | FRED 专用：HY/IG 信用利差、失业率、JOLTS 职位空缺、Sahm Rule 衰退指标 |
| **nbs-router** | [中国宏观] | data.stats.gov.cn API：批量拉取 CPI/PMI/商品房等月频数据 |
| **iv-snapshot** | [波动率] [期权] | 美股开盘时段实时 ATM IV / IV Rank / P/C Ratio，收盘后自动降级 HV |
| ★新  **capital-iq-router** | [CapIQ] [CDP] | S&P Capital IQ Pro 登录态数据拉取 (Chrome/CDP) |

### ▌ 社交、论坛、电商

| Skill | Tag | 功能 |
|---|---|---|
| **reddit-research** | [社区舆情] | Reddit 公开 JSON API 直查，无需账号，适用品牌情绪/竞品对比/用户痛点挖掘 |
| **apify-ecommerce** | [电商] [价格监控] | Amazon/Walmart/eBay 等 50+ 平台价格监控、评论采集、卖家发现 |
| **mediacrawler-router** | [爬虫] [多平台] | 小红书/微博/B站/贴吧多平台并行采集，帖子+评论 JSONL 输出 |

### ▌ 公众号与卖方研报

| Skill | Tag | 功能 |
|---|---|---|
| ★新  **wechat-daily-fetch** | [公众号] [增量] | 公众号增量抓取 → MD → 自动 tag → 写入 Wiki |
| ★新  **wechat-research** | [批量] [NLM 链路] | 公众号文章批量抓取 → 按月合并 PDF → 上传 NLM → 问答提炼 |
| ★新  **hf-banker-repo-router** | [卖方研报] | 外资卖方研报抓取，下载前列标题确认 |
| ★新  **citi-velocity-fetcher** | [Citi] [API] | Citi Velocity 研报 API 批量下载，零浏览器 UI |

---

## LAYER 3 · 核心知识层 & 语义打通 — Knowledge Base & Semantic Layer

### ▌ NotebookLM 知识库群

| Skill | Tag | 功能 |
|---|---|---|
| **report-prep-notebooklm** | [建库] [文档收集] | 自动收集年报/季报/卖方报告，覆盖美股 SEC、港股港交所、A 股巨潮三市场 |
| **notebooklm-router-py** | [Python API] [批量问答] | Google RPC 直调，批量问答与跨 transcript 语义搜索 |

### ▌ OneNote 个人笔记层

| Skill | Tag | 功能 |
|---|---|---|
| **onenote-nlm-sync** | [读写] [Graph API] | OneNote 读写主控，新建/读取页面，分区 PDF 自动导入 NLM |
| ★新  **onenote-obsidian-sync** | [Markdown] [Graph API] | OneNote 导出 MD 到 Obsidian vault，打通 OneNote → Obsidian 单向同步 |

### ▌ 研究入口

| Skill | Tag | 功能 |
|---|---|---|
| ★新  **quick-research-lite** | [轻量 DR] [公开信息] | 轻量版 deep research，公开信息公司/行业研究，单线程跑完 |

> ▶ **四角知识闭环**：OneNote 个人笔记 ↔ NotebookLM 语义库 ↔ 云端文件 ↔ Obsidian vault，任意节点写入后可自动同步至其余三端

---

## LAYER 4 · 分析 & 情报层 — Analysis & Intelligence

### ▌ 持仓监控 & 财报点评

| Skill | Tag | 功能 |
|---|---|---|
| **持仓 A · weekly-monitor** | [周报] [Word+Excel] | 股价/技术面、宏观高频、监管动态、机构持仓、券商评级，Word 周报 + Excel 历史数据库 |
| **持仓 B · biweekly-monitor** | [双周报] [Word+Excel] | 股价与财报预期、宏观、行业高频、监管+竞争+舆情、机构持仓、券商评级 |
| **特定标的 · user-research** | [多平台] [NLP] [月度] | 多平台数据采集 → NLP 分析 → 14 模块投资级 Word 报告 + Excel |
| **earnings-review** | [财报点评] [Phase A/B] [通用] | 通用财报点评，适用所有持仓 & 覆盖标的。Phase A 数字核实 + beat/miss 判断；Phase B 结构化点评（经营质量 / 预期差 / 前瞻）。自动 NLM 更新 |

### ▌ 情绪 & 估值周期

| Skill | Tag | 功能 |
|---|---|---|
| **sentiment-cycle** | [S 曲线] [情绪定位] | F/N/L/M 四层评分，定位任意股票情绪阶段 (S1 萌芽 → S2 加速 → S3 拐点 → 顶峰) |
| ★新  **sw-sector-scanner** | [板块] [Leading Indicator] | 申万板块 Leading Indicator 追踪系统，识别历史信号低位的板块 |
| ★新  **sw-sector-cycle-research** | [左侧建仓] [估值周期] | 申万板块估值 + leading indicator 追踪 (左侧建仓决策) |

### ▌ 快速初查 & 决策简报

| Skill | Tag | 功能 |
|---|---|---|
| **onenote-quick-research** | [快速建档] [5 页结构] | 5 页结构化初查：Summary → 业务 → 市场 → 竞争 → 估值。新票快速建档用 |
| **hf-morning-brief** | [早报] [HTML] [每日] | 开盘前决策简报 6 模块（宏观/持仓/IV/情绪/板块/日程），Quick / Full 双模式 HTML 输出 |

### ▌ 研究辅助

| Skill | Tag | 功能 |
|---|---|---|
| **serious-answer** | [严肃回答] [来源核实] | 三层认知标注：①确认事实  ②我推断  ③我认为；数据必查证，禁止编造 |
| ★新  **learn** | [深入学习] [六阶段] | 深入学习陌生领域的六阶段工作流：scope → map → core → connect → apply → reflect |

---

## LAYER 5 · 深度研究 & 建模层 — Deep Research & Modelling

按功能定位：这一层是"一次性产出完整投资交付物"的旗舰工作流。多 agent 并行 / 长 workflow / 输出完整 IC Memo 或三表模型。**earnings-review 归 L4 持仓监控**（routine，不是一次性深研），**data-validator 归 L1 cross-cutting QC**（这里只调用、不归属）。注：本文是 9 层视图（L0 = Meta），所以基础设施在 L1；主站和 v2 essay 用 6/7 层视图，data-validator 在 L0。

| Skill | Tag | 功能 |
|---|---|---|
| **deep-research-workflow** | [旗舰研究工作流] [4 阶段] [11 agent 并行] | NLM / Gemini DR / Claude 三源融合 · per-slide RAG · state machine recovery。产出链：问题清单 → 三表 Excel → IC 报告 (Word) → HF 备忘录 (含对抗性框架)。多个 Eval 检查点嵌入主流程关键节点，产出前自动验证 |
| **3-statements-ultra** | [三表模型] [IS/BS/CF] | 从零构建机构级三表模型，完整公式联动，季度/半年/年频自适应，IFRS/US GAAP/中国准则兼容。内置三表交叉验证和检查点日志 |
| **visiting-memo** | [调研纪要] [Word] | 公司调研备忘录生成器，按机构标准格式输出 Word。内置多维度准确性检查，对外文档严格质量把控 |

---

## LAYER 6 · 输出渲染层 — Output & Rendering

### ▌ IC Memo 生产链

| Skill | Tag | 功能 |
|---|---|---|
| **ic-memo-outliner** | [规划层] [≤6 Part] | storyline + outline.md，内置多道质量门禁 (thesis tree / 数据密度 / 来源覆盖) |
| ★新  **json-ic-outliner** | [SSOT] [Renderer-agnostic] | JSON SSOT 规划层，渲染器无关，与 layout-json-renderer 双向对接 |
| **ic-pptx** | [PPTX] [机构深蓝] | 机构品牌 PPTX 渲染，12 种 layout，多步 QC gate 出厂 |

### ▌ Deck 三模板体系  ★ 新增

| Skill | Tag | 功能 |
|---|---|---|
| ★新  **acme-slides-creator-json** | [acme] [浅色商务风] | JSON SSOT → 原生 PPTX，acme 品牌浅色商务风模板 |
| ★新  **navy-slides-creator-json** | [navy] [机构式] | JSON SSOT → 原生 PPTX，深蓝机构式 deck 模板 |
| ★新  **layout-json-renderer** | [HTML+PPTX] [双渲染] | JSON SSOT → HTML preview + 原生 PPTX dual renderer |
| ★新  **slides-template-creator** | [Skill Factory] [Fork] | Skill factory：品牌 deck 样本一键 fork 出 outliner + creator 双 skill |

### ▌ 研究报告输出  ★ 新增

| Skill | Tag | 功能 |
|---|---|---|
| ★新  **visiting-memo-public** | [调研] [公开版] | 调研纪要公开版 Word 渲染器，对外披露安全 |
| ★新  **banker-report-creator** | [研报] [Uninodue] | 研报 Word (.docx) 渲染器，机构研报版式 |
| ★新  **gs-research-chart** | [机构图表] [navy+coral] | 机构研报风格图表生成器 (navy + coral 配色，Exhibit 标题) |

### ▌ 其他输出

| Skill | Tag | 功能 |
|---|---|---|
| **pptx-template-analyzer** | [模板解析] [校准补丁] | 任意 pptx 母版自动解析 layout/placeholder/字体配色，生成补丁 |
| ★新  **deck-translation** | [PPT 中译英] [格式保留] | PPTX 中译英全流程，格式 100% 保留 |
| ★新  **docx** | [Word] [通用] | Word 文档创建/读取/编辑通用 skill |
| ★新  **humanizer-zh** | [去 AI 痕迹] [输出后处理] | 中文输出后处理 —— 剥离 AI 写作 pattern（"值得注意的是"、"综上所述"等），渲染前最后一道 |

> ▶ 已移除：**html5-editor**（IC Memo HTML5 编辑器，废弃，直出 PPTX 替代）

---

## LAYER 7 · 质量保障 & Eval 体系  ★ 本次升级重点 — Quality Assurance & Evaluation

> ▶ Eval 不是一个 skill，而是贯穿全系统的质量基础设施。从数据进入 (L1) → 最终交付 (L6) → 知识沉淀 (L8)，每一层都有专属验证机制。当前共 6 大 Eval 域，覆盖数据、格式、叙事、跨模型、知识库、基础设施六个维度。**核心原则：过不了 gate 就不允许交付。**

### ▌ Eval 六域总览

| 域 | 覆盖范围 | 执行方式 |
|---|---|---|
| ① Deck 输出质量 | PPTX / HTML 自动检查：布局合规 → 密度评估 → 源清洁度 → 输出裁决 | 四步串行 gate，全自动 hard block |
| ② 数据溯源 & 模型验证 | 数值来源注册 + 过时性 + 交叉核验 + 三表交叉验证 | 全自动 hard block |
| ③ 跨模型审查 | 独立模型对高价值输出做交叉审查，消除单模型偏见 | 多 gate 覆盖研究/IC Memo/财报/调研 |
| ④ 研究工作流内嵌 | 深度研究/财报点评/调研纪要各关键节点设置检查点 | 工作流内触发 |
| ⑤ 知识库健康检查 | Holdings/Coverage wiki 每日巡查 + 新页面准入门槛 | 每日自动 + 季度深扫 |
| ⑥ 基础设施审计 | 配置一致性、MCP 健康、安全扫描、实现后审查 | 按需 + 任务完成后 |

### ▌ Deck 四步 Gate

> 所有 PPTX/HTML 输出必须通过四步串行 gate，任一步 FAIL 即阻断交付：

| 步骤 | Skill | 功能 |
|---|---|---|
| Step 1 | **pptx-repair** | 自动检测并修复常见 PPTX XML 缺陷 |
| Step 2 | **pptx-eval** | 真实环境打开验证 + 布局审计 (边距/重叠/溢出/字体/对比度) |
| Step 3 | **density-eval** | 每页密度评估，过疏或过密自动标警 |
| Step 4 | **deck-eval-router** | 统一路由 + 品牌词扫描 + 输出最终裁决 |

### ▌ 数据溯源 & 模型验证

所有数值必须注册来源并标注置信度分级。多源交叉核验，差异超阈值自动双值标注。过时数据按类别分设检查阈值。三表模型内置 IS→BS→CF 三表交叉验证和 Checkpoint 日志，确保公式联动完整性。

### ▌ 跨模型审查

通过独立模型对 Claude 产出做交叉审查，消除单模型偏见。多个 gate 覆盖研究问题设计、报告正文、数字交叉核验、IC Memo 论证树、财报点评、调研纪要等高价值输出环节。**三级裁决**：PASS / CONDITIONAL / FAIL，FAIL 必须修改后重新验证。

### ▌ 研究工作流内嵌 Eval

| Skill | 嵌入点 | 说明 |
|---|---|---|
| **deep-research-workflow** | [多检查点嵌入] | 旗舰研究流程在问题设计、摘要生成、报告正文、数字核验、HF Memo 五个关键节点设置跨模型审查检查点。自动 state checkpoint 防止中间状态丢失 |
| **earnings-review** | [信号扫描] [自动升级] | 内建信号扫描机制，识别异常模式后自动升级审查强度。完成后跨模型交叉验证才能关闭 session |
| **visiting-memo** | [对外文档质控] | 多维度准确性检查：数字 vs 来源、姓名拼写、AI 痕迹零容忍、fabrication 检测。纪要是对外文档，质控标准最严格 |
| **IC Memo outliner** | [多道质量门禁] | IC Memo 规划阶段设有多道 gate：论证树结构检查、语义审查、数据密度、来源覆盖、slide 数量。不过 gate 不允许进入渲染阶段 |

### ▌ 知识库健康检查

L8 Librarian 层自带两层 Eval 机制：每日自动健康巡查 (8 项检查) + Holdings 新页面多项 Eval gate。

- **每日巡查覆盖**：表格数据完整性、来源链接、更新时效、数据口径一致性、数据源优先级等
- **新页面准入**：必须通过结构/数据/质量三层 Eval 才允许交付

### ▌ 基础设施审计

| Skill | Tag | 功能 |
|---|---|---|
| **check** | [实现后审查] | 任务完成后结构化 review，按改动规模分档。多维度检查：安全/架构/性能/对抗性。自动修复分级路由 |
| **health** | [配置审计] | 多层系统审计：配置一致性、MCP 存活检查、Hook 完整性、安全扫描。Issue 分级报告 |

---

## LAYER 8 · 投研知识库 — 活 Wiki 体系  ★ 最终整合层 — Living Wiki · Final Knowledge Aggregation

> ▶ 前面所有层的产出 (爬取的数据 / 路由的 API / 检索的知识 / 分析的结论 / 建模的数字 / 渲染的报告 / Eval 的质量结果) 最终都汇入这一层。**Librarian 不是又一个 skill — 它是整个系统的知识资产沉淀库。**

### ▌ 各层向 L8 的汇入

| 源层 | 汇入内容 | 在 wiki page 上的体现 |
|---|---|---|
| L1 基础设施 | 文件路由产出（模型 / PDF 存储路径）、通用 web 抓取的原始 bytes、AI 引擎调用日志 | 数据血缘的底层 hop |
| L2 数据采集 | 金融 API 数据（股价 / 估值 / 宏观 / 板块）、研报 PDF、公众号、卖方研报、爬虫数据、Capital IQ comps | Key Take-Away 多桶分类 + Valuations 实时缩放 + 数据变更日志 |
| L3 知识层 | NLM 语义检索结果、OneNote 个人笔记 | vault 扫描结论、Q&A 存档双链 |
| L4 分析情报 | 周报/双周报、情绪定位、板块估值 | 交叉验证、Bull/Bear Case 更新 |
| L5 深度研究 | 财报点评、三表模型、调研纪要 | Model Snapshot、Key Guidance、Q&A 归档 |
| L6 输出渲染 | IC Memo、早报、研报 Word | 研究 Activity 桶置顶 |
| L7 Eval | 数据一致性检查、过时性标记、健康检查结果 | 健康检查 WARNING、跨源矛盾标红 |

### ▌ 活 Wiki 的核心机制

| § | 机制 | 说明 |
|---|---|---|
| **8.1 每日信息流** | [多桶聚合] [实时缩放] | 持仓与覆盖标的 wiki 每天滚动更新。估值段实时缩放。Key Take-Away 每天扫描近期窗口内所有相关文件，按类型自动分桶。还有三段沉淀资产：关键指引、Known Truth、近期 Thesis |
| **8.2 Question List + Vault 扫描** | [会前 briefing] | 见分析师前建 question list，librarian 对 vault 全量扫描，每个问题下自动附初步结论。会后 Q&A 存档触发 wiki 级联更新 |
| **8.3 Q&A 双链复利** | [问题→答案→wiki] | 第一链：问题→答案→存档。第二链：答案→wiki 更新→下次提问的上下文。复利循环：每轮 wiki 厚一层，question list 起点高一层 |
| **8.4 健康检查 & 跨源仲裁** | [状态巡查] [跨源冲突] | 每天自动两层。第一层状态巡查：检测过时、偏离、未反映新数据等异常。第二层跨源矛盾扫描：按信源置信度 + 时间锚定做仲裁，判不准的主动 raise 给人 |

### Holdings / Coverage / Company Wiki Page  [活 Wiki 终态]

L1–L7 所有产出最终呈现在公司主页上：多段标准结构活页，覆盖核心论点、模型快照、实时估值、近期要点、多空论点、关键指引、财务数据、Q&A 归档、催化剂日历等。所有来源必须双链指向，所有变化都进健康检查。

---

## LAYER Σ · 关键数据流 · 七条核心路径 — Core Data Flows

| # | 路径名称 | 数据流 |
|---|---|---|
| ① | 研究启动链 | report-prep-notebooklm → notebooklm-router-py + cloud-files-router + onenote-nlm-sync → deep-research-workflow |
| ② | 财报点评链 | cloud-files-router → earnings-review Phase A/B → onenote-nlm-sync → NLM 自动同步 |
| ③ | IC Memo 生产链 | json-ic-outliner → data-validator → layout-json-renderer (三模板) + gpt-imagegen → deck-eval-router 四步 QC |
| ④ | 每日决策链 | ak-xq-router + fred-router + iv-snapshot → hf-morning-brief + sentiment-cycle + sw-sector-scanner |
| ⑤  ★新 | 卖方研报链 | hf-banker-repo-router / citi-velocity-fetcher → tag-pipeline → obsidian-librarian wiki |
| ⑥  ★新 | 微信公众号链 | wechat-daily-fetch → tag-pipeline → obsidian-librarian wiki  /  wechat-research → NLM |
| ⑦  ★新 | Onboarding 全生命周期 | 丢材料 → 标准归档 → wiki 构建 → 跨源自检 → 会前准备 → 会后归档 → 日常追踪 |

---

## LAYER ✓ · 系统特征总结 — System Profile

| 维度 | 现状 |
|---|---|
| **Skills 总数** | 65+ active skills，分布于 9 个功能层 (Layer 0–8) |
| **核心枢纽** | cloud-files-router (文件) / obsidian-librarian (活 Wiki) / web-access (联网) / llm-subagent (AI 引擎) |
| **知识闭环** | Obsidian ↔ OneNote ↔ NotebookLM ↔ 云端文件  四角互通 |
| **投研中枢** | 活 Wiki：跨源综合 + 多桶每日 feed + Q&A 双链复利 + 健康检查仲裁 |
| **Eval 体系** | 6 域覆盖：Deck QC / 数据溯源 / 跨模型 / 研究内嵌 / 知识库健康 / 基础设施审计 |
| **Deck 体系** | JSON SSOT → 三模板 (acme / navy / 机构) |
| **AI 引擎** | Claude 主力 + DeepSeek V4-Pro/V3 + 火山方舟 ASR + GPT-4o imagegen + Gemini DR |
| **核心理念** | 最终输出物的质量是过程的自然结果，不是事后修补的产物 |

---

> ———  内部文档 · 脱敏版 · Claude Code Skills Network · Updated 2026-05-12  ———
