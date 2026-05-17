---
title: "Claude Code Skills Network — 完整技术版 (Full)"
date: 2026-05-12
type: personal
tags: ["personal", "Personal"]
日期: "2026-05-12"
content_type: "deep_analysis"
summary: "Claude Code 65+ skills 系统架构全景，完整技术细节版，含所有gate ID、检查项、文件路径、阈值"
companies: []
themes: ["投研系统", "人工智能", "知识管理"]
sector: []
key_points: ["9层架构 L0-L8，65+ active skills", "Eval体系6域·20+ gate节点·70+检查项", "Codex跨模型审查9 gate (G1-GR)覆盖全部高价值输出", "IC Memo Outliner 5道hard block gate", "Librarian H1-H8每日健康检查+14项Holdings Eval Gate"]
---

# Claude Code · Skills Network — 完整技术版

> 系统架构全景 · 内部技术文档 · Updated 2026-05-12
> 65+ active skills · 9 layers · 20+ gate · 70+ checks
> ⚠️ 本文档含完整实现细节，仅供内部参考，不可对外

---

## 版本对比

| 维度 | 旧版 (2026-03) | 当前版 (2026-05) |
|------|----------------|-----------------|
| Skills 总数 | 37 active | 65+ active |
| 功能层 | 5 层 (L0–L5) | 9 层 (L0–L8) |
| 核心枢纽 | cloud-files-router / onenote-nlm-sync / notebooklm-router-py | +web-access / obsidian-librarian / llm-subagent |
| 知识闭环 | OneNote ↔ NLM ↔ 云端文件 三角 | +Obsidian vault 四角闭环 |
| Deck 渲染 | 单一模板 | 三模板体系 (acme/navy/机构) + JSON SSOT |
| AI 引擎 | Gemini Chrome UI | +DeepSeek V4-Pro/V3 + 火山方舟 ASR + GPT-4o |
| Eval 体系 | data-validator | 独立层: 6 域 Eval · Codex 跨模型 9 gate · 全链路 QC |
| 投研中枢 | (无) | 活 Wiki: 跨源综合 + Q&A 复利 + 健康仲裁 + 全链路 QC |

---

## LAYER 0 · 元技能层 — Meta Skills

| Skill | 功能 |
|-------|------|
| ★新 think | 写代码前的设计和验证，将想法转化为已验证的计划 |
| ★新 design | UI/组件/页面/视觉界面构建 |
| ★新 read | 读取任何 URL/网页/PDF，转换为 Markdown |
| ★新 write | 写作风格修改，剥离 AI 写作模式，使文字自然 |

---

## LAYER 1 · 数据采集 & 外部源接入 — Raw Data Ingestion

**旧有 (4)**
- web-pdf-fetcher — IR 网站 PDF 下载，绕过 bot 检测与 403 拦截
- reddit-research — Reddit 公开 JSON API 直查，品牌情绪/竞品对比
- apify-ecommerce — Amazon/Walmart/eBay 等 50+ 平台价格监控
- mediacrawler-router — 小红书/微博/B站/贴吧多平台并行采集

**新增 (5)**
- ★新 wechat-daily-fetch — 公众号增量抓取 → MD → 自动 tag → Wiki
- ★新 wechat-research — 公众号批量抓取 → 按月合并 PDF → 上传 NLM → 问答提炼
- ★新 hf-banker-repo-router — 外资卖方研报抓取，下载前列标题确认
- ★新 citi-velocity-fetcher — Citi Velocity 研报 API 批量下载，零浏览器 UI
- ★新 capital-iq-router — S&P Capital IQ Pro 登录态数据拉取 (Chrome/CDP)

---

## LAYER 2 · 基础设施 & 路由层 — Infrastructure & Routing

### 文件路由核心枢纽
- cloud-files-router — 云端文件 WebDAV，工作文档/财报/模型文件同步主干道

### 数据 API 路由群
- ak-xq-router — AKShare+雪球双源，A 股港股全覆盖，内建 Consensus
- sw-api-router — 申万行业指数 API：PE BAND/PB-ROE/换手率，6 大模块
- fred-router — FRED 专用：HY/IG 信用利差、失业率、JOLTS、Sahm Rule
- nbs-router — 中国宏观 data.stats.gov.cn API
- iv-snapshot — 美股 ATM IV/IV Rank/P/C Ratio，收盘后降级 HV

### AI 引擎路由群
- gemini-deep-research-router — Gemini Deep Research 专属
- ★新 gpt-imagegen — 文生图默认入口，ChatGPT gpt-4o + CDP + 自动下载
- ★新 llm-subagent — DeepSeek V4-Pro 推理/V3 轻量 + 火山方舟 ASR 转写，四模式
- ★新 web-access — 联网通用入口 (搜索/抓取/CDP 登录态)，替代 gemini-router

### 系统治理群 ★ 新增板块
- ★新 tag-pipeline — vault 未标注 MD 用 LLM 自动打标 + 同步更新 wiki
- ★新 session-log — 跨 session 工作台账 + 工作流状态机
- ★新 codex-review — 独立模型跨模型审查，覆盖研究/IC Memo/财报/调研
- ★新 health — 配置问题检查、MCP 服务器审计、多层健康检查

> 已移除：gemini-router (并入 web-access) · gemini-imagegen (被 gpt-imagegen 替代)

---

## LAYER 3 · 核心知识层 & 语义打通 — Knowledge Base & Semantic Layer

### NotebookLM 知识库群
- report-prep-notebooklm — 自动收集年报/季报/卖方报告，三市场覆盖
- notebooklm-router-py — Google RPC 直调，批量问答与跨 transcript 语义搜索

### OneNote 个人笔记层
- onenote-nlm-sync — OneNote 读写主控，Graph API
- onenote-quick-research — 5 页固定结构快速建档
- ★新 onenote-obsidian-sync — OneNote 导出 MD 到 Obsidian vault

### 研究入口
- ★新 quick-research-lite — 轻量版 deep research，公开信息公司/行业研究

> 四角知识闭环：OneNote ↔ NotebookLM ↔ 云端文件 ↔ Obsidian vault，任意节点写入后可自动同步至其余三端

---

## LAYER 4 · 分析 & 情报层 — Analysis & Intelligence

### 持仓专属监控
- 持仓 A · weekly-monitor — 周报 Word+Excel
- 持仓 B · biweekly-monitor — 双周报 Word+Excel
- 特定标的 · user-research — 多平台用户舆情月度报告

### 情绪 & 估值周期
- sentiment-cycle — F/N/L/M 四层评分，S 曲线情绪定位
- ★新 sw-sector-scanner — 申万板块 Leading Indicator 追踪系统
- ★新 sw-sector-cycle-research — 申万板块估值 + leading indicator (左侧建仓)

### 研究辅助
- serious-answer — 严肃回答规范，三层认知标注
- ★新 humanizer-zh — 去除中文文本 AI 痕迹
- ★新 learn — 深入学习陌生领域，六阶段工作流

---

## LAYER 5 · 深度研究 & 建模层 — Deep Research & Modelling

- **deep-research-workflow** — 旗舰研究工作流，4 阶段 · NLM/Gemini DR/Claude 三源融合 · 11 agent 并行。多个 Eval 检查点嵌入主流程
- earnings-review — 财报点评 Phase A 数字核实 + Phase B 结构化点评。内建信号扫描，异常后自动升级审查强度
- 3-statements-ultra — 机构级三表模型，完整公式联动，内置三表交叉验证
- visiting-memo — 公司调研备忘录 Word 生成器，多维度准确性检查
- data-validator — 数据来源注册表 + 跨 slide 一致性校验 + 过时性检查

---

## LAYER 6 · 输出渲染层 — Output & Rendering

### IC Memo 生产链
- ic-memo-outliner — 规划层，内置多道质量门禁
- ★新 json-ic-outliner — JSON SSOT 规划层，渲染器无关
- ic-pptx — 机构品牌 PPTX 渲染，12 种 layout

### Deck 三模板体系 ★ 新增
- ★新 acme-slides-creator-json — acme 品牌浅色商务风 (JSON SSOT → PPTX)
- ★新 navy-slides-creator-json — 深蓝机构式 deck (JSON SSOT → PPTX)
- ★新 layout-json-renderer — JSON SSOT → HTML preview + 原生 PPTX dual renderer
- ★新 slides-template-creator — Skill factory，品牌 deck 样本一键 fork

### 研究报告输出 ★ 新增
- ★新 visiting-memo-public — 调研纪要公开版
- ★新 banker-report-creator — 研报 Word 渲染器，机构版式
- ★新 gs-research-chart — 机构研报风格图表生成器

### 其他输出
- hf-morning-brief — 开盘前决策报告 6 模块，HTML 输出
- pptx-template-analyzer — 任意 pptx 母版自动解析
- ★新 deck-translation — PPTX 中译英全流程，格式 100% 保留
- ★新 docx — Word 文档创建/读取/编辑通用 skill

> 已移除：html5-editor (废弃，直出 PPTX 替代)

---

## LAYER 7 · 质量保障 & Eval 体系 ★ 完整技术版

> Eval 不是一个 skill，而是贯穿全系统的质量基础设施。从数据进入 (L1) → 最终交付 (L6) → 知识沉淀 (L8)，每一层都有专属验证机制。当前共 6 大 Eval 域、20+ gate 节点、70+ 检查项。核心原则：过不了 gate 就不允许交付，所有 hard block 自动执行，不依赖人工判断。

### Eval 六域总览

| 域 | 覆盖范围 | Gate 数 | 检查项 | 执行方式 |
|---|---------|---------|--------|---------|
| ① Deck QC Pipeline | PPTX/HTML 输出文件 | 4 步串行 | ~20 项 | 全自动 hard block |
| ② 数据溯源 & 模型验证 | 数值来源·公式·过时性·三表联动 | 2 gate | ~25 项 | 全自动 hard block |
| ③ Codex 跨模型审查 | 研究·IC Memo·财报·调研纪要 | 9 gate (G1–GR) | ~40 项 | Codex dispatch |
| ④ 研究工作流内嵌 Eval | Deep Research·财报点评·调研纪要 | 5+ gate | ~30 项 | 工作流内触发 |
| ⑤ 知识库健康检查 | Holdings/Coverage wiki·vault 数据 | H1–H8 + 14 项 | ~22 项 | 每日自动+季度深扫 |
| ⑥ 基础设施审计 | 配置·Hook·MCP·安全·scope drift | 2 skill | ~20 项 | 按需+post-impl |

---

### 7.1 Deck 四步 Gate — PPTX/HTML 输出质量

所有 PPTX/HTML 输出必须通过四步串行 gate，任一步 FAIL 即阻断交付。deck-eval-router 提供 preset 链路：`final_gate` (完整四步+source-clean) / `build_gate` (构建时三步) / `fast_check` (快速迭代两步) / `html_gate` (HTML 专用两步)。

| 步骤 | Skill | 做什么 | 判定逻辑 |
|-----|-------|-------|---------|
| Step 1 | pptx-repair | PPTX self-check + auto-fix 预处理 | 8 类已知 XML bug 自动修复，exit 2 = 修复失败 |
| Step 2 | pptx-eval | PowerPoint COM 打开验证 + 布局审计 | COM 能否无修复对话框加载 + 边距/重叠/溢出检测 |
| Step 3 | density-eval | slide 密度 9-grid 评估 | 每页 9 宫格，≥3 空格 = FAIL，2 空格 = WARN |
| Step 4 | deck-eval-router | 统一路由 + source-clean + 聚合裁决 | 聚合前三步 + 品牌词/AI 工具词扫描 + 最终 PASS/FAIL |

**pptx-eval 扩展检查项：**
- 字体审计：Typeface vs OFFICE_BASELINE_FONTS 白名单（禁止 Söhne/Inter/Tiempos fallback）
- WCAG 对比度：文本 vs 背景色对比度（AA normal ≥4.5, AA large ≥3.0）
- 视觉 Delta（可选）：与基线 PNG 比较，MAE ≤15 & SSIM ≥0.70

**density-eval 豁免规则：**
- cover/divider/section/title layout 自动豁免
- BCG 矩阵、竞争格局等 sparse-by-design pattern 可标 exempt
- Hook 集成：`~/.claude/hooks/density_gate.py` 在 Write 时自动拦截 FAIL 文件

---

### 7.2 数据溯源 & 模型验证

#### data-validator — 五层数据质量检查

所有数值必须注册到 `_data_registry.json`，未注册的数字写 `{{placeholder}}`。

- **Tier 分级**：T1(官方 IR) → T2(券商/AKShare) → T3(多源 web) → T4(单源 web)，派生数据取最低 Tier
- **过时性阈值**：按类别分设（最新财报 ≤30 天, consensus ≤60 天, 历史数据 ≤1 年）
- **交叉验证**：T1/T2 vs T3/T4 差异 ≥5% → 双值标注，不静默取舍
- **公式检查**：dependency graph 遍历，算术断言，domain 规则 (ROIC 一致性, Fwd PE 来源, 收入交叉核验)
- **硬编码禁令**：所有派生单元格必须引用假设/输入，禁止直接写死数字

#### 3-statements-ultra — 三表模型验证

- **Rule Zero (HARDCODE BAN)**：所有预测单元格 = 公式 (=Assumptions!)，历史 = 引用 (=Raw_Info!)，违反即阻断
- **代码生成协议**：≤400 行/code block，execute-before-next（防止截断导致静默丢失）
- **三表交叉验证**：IS 合计→BS 校验, BS 留存收益→CF 联动, CF 期末现金→BS 现金反链
- **检查单元格**：Revenue/NI/Balance check cells 全部 auto-formula
- **Checkpoint 日志**：`_model_log.md` 逐 tab 记录关键合计（disk is truth，防 compact 丢失）
- **Deferred 链接**：`_pending_links.json` 记录 BS→CF 待回填引用（防 session 中断遗忘）

---

### 7.3 Codex 跨模型审查 — 消除单模型偏见

codex-review 通过独立 OpenAI Codex agent 对 Claude 产出做交叉审查，消除 sycophancy bias。9 个 gate 覆盖全部高价值输出环节：

| Gate | 审查对象 | 核心检查维度 |
|------|---------|------------|
| G1 | Deep Research S1 问题设计 | 覆盖度、锐度、CIQ 锚定、M10/M11 判断力 |
| G2 | DRW S4 Brief 摘要 | 锚点完整性、叙事平衡、T1 数据接地 |
| G3a | DRW S4 报告正文 | Notes 提取深度、段落 specificity、跨 section 一致性 |
| G3b | DRW S4 数字交叉核验 | Data×registry 交叉、T4 脚注、孤立数字检测 |
| G4 | HF Memo 投资备忘 | Bear case 真实性、概率校准、VP 质量、止损锚定 |
| GA/GB/GC | IC Memo Outliner | GA 机械检查 (thesis tree) + GB/GC 语义 C1–C6 |
| GE | Earnings Review 财报点评 | Beat/miss 算术、quality layer 证据、5C-transcript 对齐 |
| GV | Visiting Memo 调研纪要 | 数字 vs 来源、姓名准确性、AI 痕迹零容忍、fabrication 检测 |
| GR | 通用研究 Gate | 算术、地理、引用、来源 vintage、计数精确度 |

**判定机制：**
- 三级裁决：PASS / CONDITIONAL（用户决策）/ FAIL（必须修改+重跑）
- 每条 issue 标注 severity：BLOCKER（阻断交付）/ WARNING（需关注）/ INFO（建议）
- FAIL + BLOCKER = 修改后必须重新 dispatch 验证，不允许人工 override

---

### 7.4 研究工作流内嵌 Eval

#### deep-research-workflow — 四阶段嵌入式验证

旗舰研究工作流在 4 个 session 中内嵌 5 个 Codex gate + 自动 state checkpoint：

- S1 Step 4B → **G1 gate**：问题设计质量审查（pre-user display，问题给用户看之前先过 gate）
- S4 Step 3.0 → **G2 gate**：Brief 摘要锚点完整性
- S4 Step 3.4 → **G3a + G3b gate**：报告正文 + 数字双重交叉验证
- HF Memo 完成 → **G4 gate**：投资备忘录 bear case/概率/止损审查
- `auto_state_checkpoint.py`：Hook 自动触发，主线程无感知，防 compact 丢失中间状态
- Data Registry 交叉检查：materiality ≥5% 的差异 → `_data_registry.json` 标注 `[CROSS_CHECK]`

#### earnings-review — 信号扫描 + 高嫌疑模式

财报点评在 Step 0 做强制信号扫描，满足任一条件自动升级为"高嫌疑模式"：
- credibility downgrade 连续 ≥2 个季度
- quality rating 为"有隐忧"或"质量恶化"
- 核心 KPI miss 连续 ≥2 个季度
- 管理层承诺过期未兑现
- → 高嫌疑模式自动升级 5C interrogation 优先级 + Phase A/B QC 全开
- Codex GE gate：Phase A+B 交叉验证后才能 close session-log

#### visiting-memo — AI 痕迹零容忍

调研纪要的核心 Eval 是 AI 痕迹检测，因为纪要是对外文档：
- Codex GV gate：数字 vs 来源材料、姓名拼写、section 完整性
- AI-trace 硬阻断：regex 黑名单 ("NLM"/"self-organized"/"generated"/"ASR"/"本纪要由…生成" 等)
- TBD/UNVERIFIED 策略：docx 中绝不出现，转为自然语言描述或 gap-summary 表
- ASR error propagation 检查：如果源自录音转写，额外验证转写错误是否扩散

---

### 7.5 IC Memo Outliner 五道 Gate

IC Memo 是最高价值输出物，outliner 阶段设 5 道 hard block gate，SESSION_1 不过 gate 不允许 close：

| Gate | 层级 | 检查内容 | 工具 |
|------|------|---------|------|
| Gate 1 | L0 机械 | Thesis tree 结构：4-part 必备 (intro/argumentation/valuation/risk)，6 页必含 (F1/F2/V1/V2/V3) | `check_thesis_tree.py` |
| Gate 2 | L1 语义 | Codex GA：C1 覆盖度·C2 论证·C3 估值·C4 财务·C5 金字塔·C6 连贯性 | Codex dispatch |
| Gate 3 | L0 数据 | Data registry 完整性：≥90% 数字有 tier tag，无未注册数字 | `outliner_qc_gate.py` |
| Gate 4 | L0 密度 | Per-slide: ≥6 numbers + ≥120 words + ≥3 tier tags；slide count 25–30 | `outliner_qc_gate.py` |
| Gate 5 | L0 来源 | 每个主要 source document section → ≥1 slide (`_source_coverage.json`) | `outliner_qc_gate.py` |

**反面模式惩罚：**
- box-stretching（空白拉伸充数）→ 扣分
- repeated hero（同一数字反复出现）→ 扣分
- axis label as data（坐标轴标签充当数据点）→ 扣分
- TBD/`{{}}`未填充（placeholder token 未在 SESSION 1B Phase 2 消解）→ 阻断

---

### 7.6 知识库健康检查 — Librarian Eval

L8 Librarian 层自带两层 Eval 机制：每日自动健康检查 (H1–H8) + Holdings 新页面 14 项 Eval gate。

#### 每日健康检查 H1–H8

| 检查项 | 检查内容 | 级别 |
|-------|---------|------|
| H1 | Bare empty values：表格含"—"而无 n/a 标注 | WARN |
| H2 | Backtick in table：Dataview 解析阻断 | WARN |
| H3 | Year/quarter 混排：同一表格年度与季度混用 | WARN |
| H4 | News staleness：最新新闻 > 30 天 | WARN |
| H5 | Source links missing：broker rating 条目无 wikilink | WARN |
| H6 | Updated field expired：> 7 天未刷新 | WARN |
| H7 | Header-item mismatch：列头写"归母净利"但行填 proxy (PBT/non-GAAP) | WARN |
| H8 | Data source shortcut：AKShare/router 可用但用了 proxy | WARN |

#### Holdings 新页面 14 项 Eval Gate

新建 Holdings/Coverage 页面必须全部 PASS 才能 ship，不允许 DEFERRED：

- **结构 4 项**：section 完整性、frontmatter、auto-block markers、subsection 编号
- **数据 5 项**：财务表格 ≥4、model linkage ≥20 quarterly rows、market consensus 含 CapIQ+vs-consensus、guide-vs-actual ≥4Q history、charts ≥3 chartsview blocks
- **质量 5 项**：bear case ≥3 sourced items + tail risk、section 语义匹配 (关键指引 ≠ 已报业绩)、数值 QC (抽查 ±1% tolerance)、口径标注 (GAAP vs Non-GAAP)、近期要点 7 桶排序正确

#### Q&A Memory QC（4 项检查单）

- Q1 Source hierarchy：Vault (T1/T2) > web (T3/T4)
- Q2 Numeric cross-verification：关键数字 ≥2 源交叉验证
- Q3 Opinion tagging：推断类内容必须有前缀标注
- Q4 Logical self-consistency：不得与 vault 已有数据矛盾

---

### 7.7 基础设施审计 — Post-Implementation & Config

#### check — 实现后审查

任务完成后的结构化 review，按改动规模分 3 个深度 (Quick/Standard/Deep)：

- **6 类 hard stop**：破坏性自动执行、缺失 release artifact、未知标识符、SQL/命令注入、硬编码 credential、依赖版本异常
- **Scope drift 检测**：变更文件是否与目标相关、是否偷偷重构了无关代码、是否引入了未要求的抽象
- **四级 Specialist**：Security (注入/认证/密钥) · Architecture (组合/级联) · Performance (内存/循环复杂度) · Adversarial (假设违反/滥用场景)
- **Autofix 路由**：`safe_auto` (立即修) → `gated_auto` (批量确认) → `manual` (用户签核) → `advisory` (仅通知)

#### health — 配置健康审计

6 层系统审计，按项目规模 (Simple/Standard/Complex) 调节深度：

- CLAUDE.md 全局+本地规则一致性
- Skills 安全扫描 + invoke 调优
- Hooks 文件系统+生命周期完整性
- MCP Live Check：对每个 server 做最小安全调用，报告存活/错误类型
- Issue 分级：`[!] Critical`（违规/安全发现）· `[~] Structural`（位置/结构问题）· `[-] Incremental`（改进建议）

---

### 7.8 自动阻断机制汇总

以下 gate 全部为自动执行，FAIL 时阻断交付，不依赖人工判断：

| 触发点 | 阻断条件 | 恢复路径 |
|-------|---------|---------|
| pptx-repair exit 2 | 修复失败或发现未知缺陷 | 手动修复 XML 后重新 repair |
| pptx-eval COM fail | PowerPoint 无法无修复对话框加载 | repair → 重跑 eval |
| density-eval ≥3 空格 | slide 密度不达标 | 重新布局内容后重跑 |
| deck-eval-router exit 1 | 任一子 eval FAIL | 修复后重跑完整 preset 链 |
| outliner_qc_gate 5 道 Gate | storyline/data/density/source/count 任一不过 | 修改 outline 后重跑 |
| data-validator FAIL | tier 缺失/过时/交叉验证 >5% 差异 | 修正数据来源后重新 validate |
| 3-stmt Rule Zero | 预测单元格硬编码（非公式） | 改为公式引用 |
| Codex FAIL + BLOCKER | G1/G2/G3b/GA/GB/GC/GE/GV 的 BLOCKER | 修改 + 重新 dispatch |
| AI-trace regex hit | visiting-memo 检测到禁止词 | 删除 AI 痕迹后重新生成 |
| Holdings Eval 未全 PASS | 14 项 gate 任一 FAIL | 补充数据/修正格式后重跑 |
| `density_gate.py` Hook | Write PPTX 时 density FAIL | 设 `OUTLINER_QC_SKIP=1` (仅 draft) 或修复 |

---

## LAYER 8 · 投研知识库 — 活 Wiki 体系 ★ 最终整合层 (完整版)

> 前面所有层的产出最终都汇入这一层。Librarian 不是又一个 skill — 它是整个系统的知识资产沉淀库。

### 各层向 L8 的汇入

| 源层 | 汇入内容 | 在 wiki page 上的体现 |
|-----|---------|---------------------|
| L1 数据采集 | 研报 PDF、公众号文章、卖方研报、爬虫数据 | §4 Key Take-Away 七桶自动分类入库 |
| L2 基础设施 | 云端模型文件、API 拉取的股价/估值/宏观数据 | §3 Valuations 实时缩放、registry diff 日志 |
| L3 知识层 | NLM 语义检索结果、OneNote 个人笔记 | vault 扫描初步结论、Q&A 存档双链 |
| L4 分析情报 | 周报/双周报、情绪定位、板块估值 | §5 Known Truth、§6 Bull/Bear Case 交叉验证 |
| L5 深度研究 | 财报点评、三表模型、调研纪要 | §2 Model Snapshot、§7 Key Guidance、Q&A 归档 |
| L6 输出渲染 | IC Memo、早报、研报 Word | §4 🔬 研究 Activity 桶置顶 |
| L7 Eval | 数据一致性检查、过时性标记、健康检查结果 | 健康检查 WARNING、跨源矛盾标红 |

### 活 Wiki 的五大机制

#### 8.1 每日信息流

持仓和覆盖标的的 wiki page 不是静态快照，而是每天滚动更新的信息流。遵守 14 段标准结构，估值段实时缩放（每天拉最新股价，按 `live_price / model_price` 缩放市值/EV/PE/EV-EBITDA）。

§4 Key Take-Away 每天扫描近 90 天窗口内所有相关文件，塞进 7 个桶：

| 优先级 | 桶 | 更新节奏 |
|-------|---|---------|
| 1 | 🔬 近期研究 Activity & Task (置顶) | 研究动作落盘即刷新 |
| 2 | 📢 公司公告 | 紧跟财报和重大事件 |
| 3 | 📑 券商研报 | 新报告入库即更新 |
| 4 | 🎙 会议纪要 | 按访谈/调研节奏 |
| 5 | 📰 新闻动态 (每日 WebSearch) | 每天 |
| 6 | ⚖ 监管政策 (每日 WebSearch) | 每天 |
| 7 | 🏭 竞品动态 (每日 WebSearch) | 每天 |

沉淀资产三段：关键指引 (Key Guidance)、Known Truth、近期 Thesis——更新频率低，但每个字都来自反复验证。

#### 8.2 Question List + Vault 扫描

见分析师前，建 question list，librarian 对 vault 做全量扫描，每个问题下自动附"vault 扫描初步结论"——交叉综合所有纪要、研报、公众号、模型数据。打印出来就是完整的会前 briefing。

会后，question list 转化为 Q&A 存档，逐题回填，触发 wiki 级联更新：新数据更新对应段落、Key Take-Away 刷新、催化剂日历加入时间节点、Next steps 自动生成。

#### 8.3 Q&A 双链复利

第一条链：问题→答案→存档（带路由方式、来源标注、置信度评分）。第二条链：答案→wiki 更新→下次提问的上下文。两条链合在一起就是复利：每轮循环 wiki 变厚一层，question list 起点变高一层。

复利循环：新建 coverage → 原始材料入库 → wiki v1 → 分析师会议 (question list 引用 v1) → Q&A 归档 → wiki v2 → 下次季报 (question list 引用 v2) → 更精准的问题 → wiki v3…

#### 8.4 健康检查与跨源仲裁

每天自动跑两层：

**第一层 — 状态巡查**：TP 超 60 天未更新？距财报不到 21 天？股价偏离 TP 超 30%？新研报未反映？催化剂到期未验证？触发 WARNING 后 LLM 过一遍论点一致性。

**第二层 — 跨源矛盾扫描**：同一家公司的多个来源做冲突检测，按信源置信度 (A 级财报/模型 > B 级调研/卖方/web search) + 时间锚定做仲裁。判不准的主动 raise 给人介入。

#### 8.5 Holdings / Coverage / Company Page · 14 段标准结构

L1–L7 所有产出最终呈现在公司主页上：

§1 Why Own It → §2 Model Snapshot → §3 Valuations (实时缩放) → §4 Key Take-Away (7 桶) → §5 Known Truth → §6 Bull/Bear Case → §7 Key Guidance → §8 财务表格 → §9 Q&A 归档双链 → §10 催化剂日历 → §11 监管动态 → §12 竞品对比 → §13 历史 thesis 演化 → §14 Source registry

所有 source 必须 wikilink，所有数值必须 tier 标注，所有变化都进 health check。

---

## 核心理念

> 一套好的投研系统不只是帮你记住了什么，而是在你需要之前就把信息拼好了、验证好了、分类好了。你要做的只是判断。

> 最终输出物的质量是过程的自然结果，不是事后修补的产物。

---

## 关键数据流 · 七条核心路径

| # | 路径 | 数据流 |
|---|------|-------|
| ① | 研究启动链 | report-prep-notebooklm → notebooklm-router-py + cloud-files-router + onenote-nlm-sync → deep-research-workflow |
| ② | 财报点评链 | cloud-files-router → earnings-review Phase A/B → onenote-nlm-sync → NLM 自动同步 |
| ③ | IC Memo 生产链 | json-ic-outliner → data-validator → layout-json-renderer (三模板) + gpt-imagegen → deck-eval-router (四步 QC) |
| ④ | 每日决策链 | ak-xq-router + fred-router + iv-snapshot → hf-morning-brief + sentiment-cycle + sw-sector-scanner |
| ⑤ ★新 | 卖方研报链 | hf-banker-repo-router / citi-velocity-fetcher → tag-pipeline → obsidian-librarian wiki |
| ⑥ ★新 | 微信公众号链 | wechat-daily-fetch → tag-pipeline → obsidian-librarian wiki / wechat-research → NLM |
| ⑦ ★新 | Onboarding 全生命周期 | 丢材料 → 标准归档 → 14 段 wiki 构建 → 跨源自检 → question list + vault 扫描 → 会后归档 → 日常追踪 |

---

## 系统特征总结

| 维度 | 现状 |
|------|------|
| Skills 总数 | 65+ active skills，9 个功能层 (L0–L8) |
| 核心枢纽 | cloud-files-router (文件) / obsidian-librarian (活 Wiki) / web-access (联网) / llm-subagent (AI 引擎) |
| 知识闭环 | Obsidian ↔ OneNote ↔ NLM ↔ 云端文件 四角互通 |
| 投研中枢 | 活 Wiki：跨源综合 + 7 桶每日 feed + Q&A 双链复利 + 健康检查仲裁 |
| Eval 体系 | 6 域 · 20+ gate · 70+ 检查项：Deck QC / 数据溯源 / Codex 跨模型 / 研究内嵌 / 知识库健康 / 基础设施审计 |
| Deck 体系 | JSON SSOT → 三模板 (acme/navy/机构) |
| AI 引擎 | Claude 主力 + DeepSeek V4-Pro/V3 + 火山方舟 ASR + GPT-4o imagegen + Gemini DR |
| 最脆弱节点 | Chrome CDP 依赖 (capital-iq-router / gpt-imagegen / gemini-DR) |
| 最稳定节点 | 纯 API 层：ak-xq-router / sw-api-router / fred-router / nbs-router |
| 核心理念 | 最终输出物的质量是过程的自然结果，不是事后修补的产物 |

---
*内部技术文档 · Claude Code Skills Network · Full version · Updated 2026-05-12*
*⚠️ 本文档含完整实现细节，仅供内部参考*
