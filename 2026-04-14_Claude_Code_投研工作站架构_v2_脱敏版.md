---
title: Claude Code 投研工作站架构 v2.0
date: 2026-04-14
type: architecture
status: desensitized
version: 2.0
tags: ["personal", "Personal"]
日期: "2026-04-14"
content_type: "news"
summary: "介绍投研工作站v2.0架构"
companies: []
themes: ["投研工具", "架构升级", "AI工作站", "数据采集"]
sector: []
key_points: ["v2.0较v1新增约10个技能，扩展为六层架构", "新增工作台账层（L6），整合 session 与 workflow 状态机", "L0/L1 按功能定位划分（不按实现）：L0 基础设施 = 通用能力（文件路由 / web 入口 / PDF 获取 / AI 引擎调度）+ QC 治理（data-validator，cross-cutting），L1 数据采集 = 具体外部数据源"]
---

# Claude Code · 投研工作站架构 v2.0

**脱敏版 · 六层架构 · 2026-04-14 更新** ^kp1-六层架构

> 相比 v1（37 skills / 5 层），本版新增约 10 个 skill，扩展到 6 层（新增 Session 工作台账层），并把 "联网入口" 和 "LLM 调度" 从散点整合为统一路由。 ^kp2-工作台账

---

## LAYER 0 · 基础设施 & 通用能力 — *Infrastructure & Generic Capabilities* ^kp3-基础设施

按功能定位划分（不按实现）：这一层提供所有上层 skill 共享的底层能力 —— 文件路由、通用 web 入口、PDF 获取、AI 引擎调度，以及 cross-cutting 的 QC 治理。不绑定具体数据源，稳定可复用。

### 文件路由

- **cloud-files-router** · 坚果云 WebDAV — GitHub 索引缓存（1800+ 文件）、alias_map / folder_index，工作文档/财报/模型同步主干道

### 通用 web 与 PDF

| Skill | 标签 | 职责 |
|---|---|---|
| **web-access** ⭐NEW | [CDP][统一入口] | 全局联网枢纽，CDP 携带 Chrome 登录态绕反爬，内置 WebSearch/Fetch/curl/Jina 工具层，覆盖所有通用网页任务 |
| web-pdf-fetcher | [Fallback][IR/PDF] | IR 网站 PDF 下载终极 fallback，绕 bot 检测和 403，支持 IR 列表页自动取 PDF |

### AI 引擎路由群

| Skill | 能力 |
|---|---|
| gemini-router | Chrome CDP Gemini 非 DR 查询：单问题、多问题 question-splitter 并行、追问 |
| gemini-deep-research-router | Gemini Deep Research 专属：提交后切出，等待期并行其他任务 |
| gemini-imagegen | 文生图 + 自动下载（lh3 解析），批量 PPT 插图 |
| **llm-subagent** ⭐NEW | 火山方舟 (doubao-seed / Kimi-k2.5) 中文搬运 + ASR 转写（TOS 上传 + bigasr，完全替代 NLM 上传流程） |

### QC 治理（cross-cutting）

| Skill | 作用 |
|---|---|
| **data-validator** | 数值溯源 registry —— 跨 slide / 跨文档一致性 + staleness 检查 + 下游依赖保证。所有交付前 pipeline 都依赖（建模 / outliner / deck render） |

---

## LAYER 1 · 数据采集 & 原始信号 — *Data Ingestion*

按功能定位划分：每个 skill 对应一类特定外部数据源。任务是把 bytes 落盘 —— 不做分析、不做转换。无论实现是纯 Python wrapper（AKShare/FRED）还是 CDP browser（Capital IQ/微博），只要功能是"获取特定数据"就在这一层。

### 金融数据 API 群（结构化数据源）

| Skill | 覆盖 |
|---|---|
| ak-xq-router | A/H 股：AKShare + 雪球双源，筹码/资金/融券/K 线/板块/北向/股东人数，consensus EPS·NI·Revenue 内置 |
| sw-api-router | 申万行业估值：PE BAND / PB-ROE / Z-score / 股息率 / 跨板块 PE 拓展与压缩 / 价格 |
| fred-router | 美国宏观：ICE BofA OAS HY/IG 信用利差、失业率、JOLTS、Sahm Rule 衰退指标 |
| nbs-router | 中国宏观：data.stats.gov.cn API，CPI/PMI/商品房销售/房地产投资/规工面积月频 |
| iv-snapshot | 波动率/期权：美股开盘实时 ATM IV / IV Rank / P/C Ratio（yfinance），盘前盘后可用 |
| **capital-iq-router** NEW | S&P Capital IQ Pro 登录态数据拉取（CDP）—— comps / consensus / ownership / 13F / segments / transcripts |

### 社交、论坛、电商

| Skill | 标签 | 职责 |
|---|---|---|
| reddit-research | [社区][JSON] | Reddit 公开 JSON API 直查，品牌情感挖掘 |
| apify-ecommerce | [电商][价格监控] | Amazon/Walmart/eBay 50+ 平台价格、评论、卖家发现 |
| mediacrawler-router | [爬虫][多平台] | 小红书/微博/B 站/贴吧并行采集，JSONL + 结构化错误 |

### 公众号与卖方研报

| Skill | 标签 | 职责 |
|---|---|---|
| **wechat-daily-fetch** NEW | [公众号][增量] | 增量抓公众号 → MD → 归档索引 |
| **wechat-research** NEW | [公众号][批量] | 批量抓 → 按月合并 PDF → NLM 建库 |
| **hf-banker-repo-router** NEW | [卖方研报][批量] | 外资卖方研报批量抓取（nash-ai / 报告大厅等） |
| **citi-velocity-fetcher** NEW | [FICC][研报] | Citi Velocity 研报拉取 |

---

## LAYER 2 · 知识库 & 语义层 — *Knowledge Base*

按功能定位：这一层只管知识的**存储 / 检索 / 同步**，不产出分析。所有分析型产物（初查 / 周报 / 财报点评 / 深度研究）放到 L3 或 L4。

| Skill | 角色 |
|---|---|
| report-prep-notebooklm | NLM 自动收集卖方/业绩说明会/美股 SEC/港股港交所，URL 批量入库，单 notebook ≤300 source |
| notebooklm-router-py | 直接调用 Google RPC 绕过 Chrome UI，批量问答、跨 transcript 语义搜索，无 DOM 坑 |
| onenote-nlm-sync | OneNote Graph API：读写分区页面、PDF 自动分区导入 NLM、GitHub Actions 07:00 自动触发、YouTube transcript 提取 |
| **onenote-obsidian-sync** NEW | OneNote ↔ Obsidian vault 双向同步，打通个人笔记与原子化片段库 |

> **四角知识闭环**：OneNote 个人笔记 ↔ NotebookLM 语义库 ↔ 坚果云工作文档 ↔ Obsidian vault — 任一节点写入后可自动同步到其余三角。

---

## LAYER 3 · 分析 & 情报 — *Analysis & Intelligence*

### 持仓专属监控（示例脱敏）

| Skill | 频率 | 输出 |
|---|---|---|
| 持仓 A · 周度监控 [示例] | 周更 | 股价/技术面/行业高频/监管舆情/机构动作/券商评级 → Word 周报 + Excel 历史库 |
| 持仓 B · 双周监控 [示例] | 双周 | 股价/财报预期/行业高频/竞争对手/监管/机构动作 → Word + Excel |

### 情绪、周期与板块扫描

- **sentiment-cycle** — F/N/L/M 四层评分定位任意股票情绪阶段（S1 萌芽 → S4 分裂），Post-S3 trajectory override
- **sw-sector-cycle-research** ⭐NEW — 申万行业板块估值 + Leading Indicator 完整追踪框架
- **sw-sector-scanner** ⭐NEW — 板块 Leading Indicator 系统扫描，识别历史中枢低位行业，追踪先行信号/资金流入辅助侧翻决策

### 快速初查 & 决策简报

| Skill | 职责 |
|---|---|
| onenote-quick-research | 5 页结构化初查（Summary / 业务 / 市场 / 竞争 / 估值）—— 新票快速建档用，产出落到 OneNote |
| hf-morning-brief | 开盘前决策简报 —— 6 模块（宏观 / 持仓 / IV / 情绪 / 板块 / 日程），Quick / Full 双模式 HTML 输出 |

### 专题舆情 & 研究规范

| Skill | 职责 |
|---|---|
| 用户舆情研究 [示例] | 多平台爬虫 + NLP 打分，14 项投资级 Word + Excel 汇总，覆盖产品/评论/地区分布/二级评论 |
| serious-answer | ①确认事实 / ②我推断 / ③我认为 三层认知标签强制规范，数据必溯源禁编造 |

---

## LAYER 4 · 深度研究 & 建模 — *Deep Research & Modelling*

按功能定位：这一层是"一次性产出完整投资交付物"的工作流。多 agent 并行、长 workflow、最终产物是完整的 IC Memo / 三表模型 / 调研备忘录。**earnings-review 归 L3 持仓监控（不是一次性深度研究），data-validator 归 L0 cross-cutting QC**（这里只调用、不归属）。

| Skill | 方法论 |
|---|---|
| **deep-research-workflow** 旗舰 | 4 阶段 · NLM / Gemini DR / Claude 三源融合 · 11 agent 并行 · per-slide RAG 防上下文退化 · state machine recovery · 产出链：问题清单 → 三表 Excel → IC 报告 Word → HF 备忘录（对抗性框架） |
| ic-memo-outliner | 规划层 —— thesis tree + 6 段 storyline + 逐 slide outline + data 底稿，路由到 L5 渲染层 |
| 3-statements-ultra | 零代码建模机构级三表（IS/BS/CF），完整公式联动，季/半年/年频自适应，IFRS / US GAAP 双兼容 |
| visiting-memo / **visiting-memo-public** NEW | 公司调研备忘录自动生成，template.docx 母版 unpack-repack；public 版为脱敏通用模板 |

---

## LAYER 5 · 输出 & 渲染 — *Output & Rendering*

### IC Memo 生产链

```
ic-memo-outliner  →  ic-pptx renderer     →  gpt-imagegen
(规划层 · 6 Part   (渲染层 · Pattern          (封面/插图 · GPT-4o
 storyline         A–L · 100% 继承 ·           CDP 文生图 + 自动
 outline.md        QC 5-phase sub-agent)        下载与嵌入)
 + data.xlsx)
```

### 其他输出工具

| Skill | 用途 |
|---|---|
| html5-editor | IC Memo HTML5 幻灯片实时编辑：图表/颜色/字体，inject 模式注入任意 slides |
| pptx-template-analyzer | 上传 .pptx 母版自动解析 layout/placeholder/字体配色，生成 template_constants.py 校准补丁 |
| **docx skill** NEW | 机构级叙事 Word 产出（docx-js 路径），强制规范：禁止裸 python-docx 临时脚本 |
| **humanizer-zh** NEW | 中文输出后处理 —— 去除 AI 生成痕迹（避免 "值得注意的是"、"综上所述" 等 AI tell），渲染前最后一道 |
| skill-creator | 新建/修改/测评 skill：SKILL.md 模板、eval 运行、描述词优化 |

---

## LAYER 6 · 会话 & 工作台账 — *Session & State* ⭐NEW LAYER

> **与 L0 的关系**：按功能定位，session / workflow / harness 这些组件本质上也是"基础设施"（generic 运行时能力，被所有 skill 复用）。这里单独成层是为了凸显"时间轴 / 跨 session 状态"这一维度 —— L0 处理空间（数据从哪来、文件去哪），L6 处理时间（session 之间状态怎么传）。两层正交，物理上 L6 跑在 L0 之上。

### 三层记忆架构

state 必须落 disk、不在 context 里 —— compact / 新 session 时从 disk 读，不从 context 猜。三层各司其职：

| 层 | 位置 | 性质 | 加载方式 |
|---|------|------|----------|
| **Layer 1 · 索引** | `MEMORY.md` | 常驻 context 的轻量索引（每条 ≤ 150 字） | 自动预加载，每次 session 都看得到 |
| **Layer 2 · 主题** | `memory/topic/*.md` | 按需拉取的主题深度记忆（不预加载） | 主线程按当前任务主动 read |
| **Layer 3 · 台账** | `session-log/*.md` | 跨 session 工作台账，按日期归档 | search-only，记录"上次做了什么、做到哪了" |

设计原则：**"记住怎么做" → CLAUDE.md / Guide；"记住是什么" → MEMORY.md / memory/topic/；"记住做了什么" → session-log/**。三层互不重叠。

### 组件清单

| 组件 | 作用 |
|---|---|
| **session-log** | 跨 session 工作台账 + 工作流状态机，按日期归档，GitHub 同步，支持跨 skill 状态传递与 retrospective |
| workflow-state machine | multi-phase skill 强制规范：`wf.checkpoint / wl.phase_done / close(retrospective)`，Python 库注入所有 ≥2 阶段 skill |
| **harness 工具集** NEW | `loop`（定时任务）· `schedule`（远程 cron）· `simplify`（代码 reuse/quality review）· `update-config`（settings.json hooks 配置） |
| **claude-api** | 构建/调试/优化 Claude API 应用（prompt caching 强制） |

---

## 关键数据流 · 五条核心路径

| 链路 | 组件 |
|---|---|
| ① **研究启动链** | report-prep-notebooklm（建库）→ notebooklm-router-py（语义检索）+ cloud-files-router（拉工作文档）+ onenote-nlm-sync（查个人笔记）→ deep-research-workflow（综合产出） |
| ② **财报点评链** | cloud-files-router（拉财报原文）→ earnings-review Phase A → Phase B → onenote-nlm-sync（写入）→ NLM 同步 |
| ③ **IC Memo 生产链** | ic-memo-outliner（storyline）→ data-validator（数据注册）→ ic-pptx renderer（Pattern 渲染）+ gemini-imagegen（插图）→ html5-editor（交互编辑） |
| ④ **每日决策链** | ak-xq-router + fred-router + iv-snapshot → hf-morning-brief（6 模块）+ sentiment-cycle + sw-sector-scanner → HTML 决策报告 |
| ⑤ **调研采集链** ⭐NEW | llm-subagent ASR（TOS 上传 + bigasr 录音转写）→ Sonnet 主线程结构化 → visiting-memo-public（Word 输出）→ onenote-obsidian-sync（笔记同步）→ NLM 建库 |

---

## 系统特征总结

| 维度 | 现状 |
|---|---|
| **Skills 总数** | ~45 个 active skills（v1: 37），分布于 6 个功能层 |
| **核心枢纽** | cloud-files-router（文件）/ onenote-nlm-sync（笔记）/ notebooklm-router-py（语义）/ **web-access（联网）** |
| **知识闭环** | OneNote ↔ NotebookLM ↔ WebDAV ↔ Obsidian vault，**四角互通**（v1 为三角） |
| **最脆弱节点** | Chrome UI 自动化四件套（gemini-router / gemini-DR / NLM Chrome / web-access CDP），依赖 DOM 稳定 |
| **最稳定节点** | 数据 API 路由群（ak-xq / sw-api / fred / nbs / iv-snapshot）+ LLM 引擎调度（llm-subagent）—— 这些 skill 跑在权威 API 之上，不依赖 DOM，错误模式 well-defined |
| **v2 关键升级** | ① web-access CDP 统一联网入口（替代散落 WebSearch/Fetch）② llm-subagent 火山方舟 + ASR（替代 Haiku 中文任务 + NLM 转写上传流程）③ wechat × 2 公众号双链路 ④ sw-sector × 2 行业周期框架 ⑤ Obsidian vault 接入（5950 文件）⑥ Session 层独立为 Layer 6 ⑦ docx skill 强制规范 |
| **待补强** | 跨 skill 状态传递仍靠 workflow-state 手工衔接；Gemini DR 超时；Obsidian vault 5950 文件 retag pipeline 未跑完（断点 726/2156）；四角同步延迟 |

---

*Claude Code Investment Research Workstation · v2.0 · 脱敏版 · Internal Doc · 2026-04-14*
