---
title: "FAGB —— 基于 error log 设计的金融领域 benchmark 原型"
date: 2026-05-20
type: personal
tags: ["personal", "benchmark", "model-eval", "design-philosophy"]
summary: "从日常投研工作的 error log 里长出来的一个 benchmark 原型——不出考试题，而是给模型一沓真实研报让它写投资备忘录，用埋在材料里的天然陷阱测它能不能自主发现问题。评分体系 mostly built on verifiable truth：65% 权重由 deterministic verifier（数字溯源 grep / 公式执行 / 时效性 / 单位校验）承担，regex 降到 20%，剩余 15% 用 constrained LLM judge。跑了 7 家公司 / ~86 个 checkpoint，发现前沿模型三大系统性弱点：不独立计算、不质疑权威、不追踪静默修订——全是没人指路时才暴露的静默错误。每条弱点直接对应一类可构造的 SFT / preference 训练数据，benchmark → 训练 → 重测的闭环接口已设计好。"
---

# FAGB —— 基于 error log 设计的金融领域 benchmark 原型

> 一份工程实践笔记。
> 写给自己对 FAGB（Financial Artifact-Grounded Benchmark）设计经验的总结，以及任何在想"怎么测一个 AI 的金融分析判断力"的人。
> 这是 失败金矿 那篇 §五 留的坑——那里只用一节草草带过 FAGB，这里把它填完。

> **这远远不是一个能 publish 的成熟 benchmark。** 它是个人研究的工程原型——7 家公司 / ~86 个 checkpoint 的规模、覆盖窄、没有人类 baseline，这些短板（详见 §七.4 和 §九）都还没补完，仍有大量优化空间。本文要讲的是**设计方向**——"把指针拿掉，让模型自己发现该被发现的东西"——这件事我认为方向是对的。

---

## 一、缘起：现有金融 benchmark 测不到的那块

这事是从 error log 长出来的——日常工作攒了一堆模型在真实投研里犯过的错，自然想反过来做个测试，看不同模型在同一批"已知会翻车"的场景上谁更稳。

第一版做的是考试题，问"算一下 implied P/B""算一下单车利润"。前沿模型 100% 正确率。扩到 45 道自动生成的 Q&A，公平评分下还是 100%。这个 100% 就是第一条 finding：**给模型一个明确问题 + 一份明确材料，纯计算几乎不会错**。考试题测不出弱点，因为难度在"算"，而"算"恰恰是模型最强的地方。

分析师真正难的部分不在"算"，**在真实环境本身**——人类分析师和 agent 面对的从来都不是一道一道考题，而是"把这家公司搞清楚"这件事。考试题有人替你把问题挑出来你只管解；做事得自己先意识到问题在哪。PM 不会说"算一下燃油车合营的净利占比"，他只会甩你一沓材料说"看一下这家公司"。**难的就是要自己意识到**：这两个数报告里没相减，但减出来就是 NEV 亏掉集团利润的故事；管理层那句"Q1 已盈利"和财报数字对不上；新报告的出货量比上一份悄悄低了 1M，标题却写"维持不变"。**一个 benchmark 要测的是 agent 能不能"做事"，而不是"做题"——这是 FAGB 整个设计的出发点**。

现有金融 QA benchmark（FinQA / ConvFinQA / FinanceBench 这族）的结构盲区就在这里。题目本身就是一根**指针**——"What is the implied P/B given TP=13.5 and BPS=8.13?"已经把"去算 implied P/B"这件事指给你了，模型顺着指针执行即可。

**FAGB 的核心理念就是：把指针拿掉。** 只给一个真实 PM 会说的通用任务（"帮我分析一下这个公司/研究一下这个公司"），看模型在没人指路时能不能自己发现该被发现的东西。

这个转向把 benchmark 从"考试"变成了"工作"。v3 沿这个方向做了 workflow 任务 + checkpoint 评分。v4 做了 engine 大改：6 层分层评分替代 binary regex，加入 depth judge 区分"提到了"和"主动分析了"，规模从 4 家扩到 7 家。下面拆开讲。

---

## 二、核心理念：六条

FAGB 的设计可以压成六条原则。

**1. 自然任务，不是 Q&A。** 给模型的指令是"你是买方研究分析师，基于以下文件写一份投资备忘录 / earnings debrief，覆盖评级 / 关键数字 / 估值逻辑/盈利质量/ 催化剂 / 风险"。这是真实 PM 的请求，不是出题人编的问题。产出是一篇自由格式的 memo，不要求特定 JSON 结构。

**2. 陷阱在数据里，不在题目里。** 难度来自材料里**天然存在的误导**——一个名叫 `gpm_total` 的字段实际是 82% 但它不是公司综合毛利率（真实 44%）；几个 segment 加起来不等于 total；forecast 期没有 `E` 后缀混在实际值里；管理层在 Q&A 里说的和同一份报告数据段里的数对不上。这些误导是材料原本就有的，不是为了出题硬塞的。

**3. 通用 prompt，不给分析方向。** prompt 模板是固定的，只说"写 memo"，**绝不**说"帮我算 ICE 贡献占比"或"帮我找报告间矛盾"。原因很硬：真实 PM 不会给这种提示。一旦 prompt 提示了具体分析方向，测的就从"能否自主发现问题"退化成了"被告知后能否执行"——而后者前沿模型早就会了。

**4. 分层评分，regex 只是基础层。** v3 时期的设计原则是"默认不用 LLM-as-judge"，评分全靠 checkpoint 正则匹配。这保证了 verdict 的确定性和可重放——同一份 response 跑一百遍评分结果完全一样。但 v3 跑完发现**诸多分析判断类的内容grading的难题——正则太宽，keyword stuffing 蒙混过关；正则太窄，换个说法就误杀。

v4 的直接回应是 6 层分层评分，把正则从"唯一评分器"降级为"基础层"：

| 层              | 权重  | 做什么                                                                                      | 性质                        |
| -------------- | --- | ---------------------------------------------------------------------------------------- | ------------------------- |
| T3 regex       | 20% | v3 baseline，关键词/数字 pattern 匹配                                                            | deterministic             |
| T1 citation    | 25% | 模型声称"引用/披露"的 source-stated 数字必须在 source 文件中可 grep——编造的数字被拦；derived 数字（模型自己算的）走 T0 computation 层验证，不适用 grep | deterministic             |
| T0 computation | 15% | 有 `derived_formula` 的 checkpoint 实际执行公式，比对模型给的数字                                         | deterministic             |
| T2 depth       | 15% | 4 项 binary rubric（DID_COMPUTE / DID_COMPARE / DID_CHALLENGE / DID_CAUSE），区分"提到了"和"主动分析了" | LLM judge，限定 rubric + 正反例 |
| T1 timeliness  | 15% | 引用数字的时段标记必须匹配 expected period                                                            | deterministic             |
| Unit/currency  | 10% | 单位一致性 + 币种标注                                                                             | deterministic             |

设计逻辑：T0/T1 hard verifier 占 55%（citation + computation + timeliness）完全 deterministic 不可 hack。数字分三类处理：source-stated（引用披露值）走 citation grep，derived（模型主动计算）走 computation 公式验证，model-estimated（模型估算）当前不覆盖。T2 depth 用 LLM 但严格限定在 binary rubric + 正反例 pair + source 数字对照（constrained LLM judge），比开放式 LLM-judge 可复现得多，但不是全 deterministic——Haiku 一致率仅 62%，当前用 Opus 做 judge。"默认不用 LLM-as-judge"仍然是原则——T2 只占 15%。

**5. Runtime leak-resistant。** 环境层面**禁掉联网**（`tools_denied: web_search / web_fetch`），模型只能基于给定文件作答，切断"现场上网搜标准答案"这条路。需要明确的是，这只解决 runtime web leak——如果素材来自公开 filing 或研报，模型预训练阶段可能已经记住了部分内容（training contamination），这一层当前未解决。未来可通过时间窗（post-cutoff 材料）、私有素材、或 held-out source 机制进一步加固

**6. 深度感知，不止测广度。** v3 的 regex-only 评分有一个结构性盲区：它只能测"有没有提到"（广度），测不了"有没有主动分析"（深度）。v4 加入 T2 depth judge，用 4 项 binary rubric 做这件事：

- **DID_COMPUTE** — 模型是否自己做了报告没做的计算（比如减法拆出 NEV 贡献）并且给出了清晰的理由与逻辑
- **DID_COMPARE** — 模型是否做了跨报告/跨时期的数据对比
- **DID_CHALLENGE** — 模型是否用数据质疑了管理层声明或报告结论
- **DID_CAUSE** — 模型是否做了因果归因（不只是列数字，而是解释为什么）

实测发现 depth 区分度有限，但这是测试集 L5 题不够多的问题，不是 judge 本身的问题——详见 §4.4。

这六条之上还有一条硬规则——**删除测试**：

> 删除测试是**出题阶段**对每个 checkpoint 的自检，不是 runtime 测模型。设计 checkpoint 时把材料里能**直接给出答案的那句话**删掉，再问一个判断：**剩下的数据里，这个答案在逻辑上还推得出来吗？**
> - 推得出来 → checkpoint 合格 ✅（这是真正的分析能力测试，模型必须做推理）
> - 推不出来 → checkpoint 不合格 ❌（剩余数据不支撑答案，这个题考的只是"找那句话"，本质是检索）

判官是出题人（或 Opus trap-finding agent），判据是"剩余材料在信息上是否充分到能支撑结论"**，跟具体哪个模型能不能答对无关。这一步是为了筛掉"披着分析外衣的检索题"——一个 checkpoint 如果只有那句话能给答案，删掉它整个数据集就不再支持这个结论了，那它考的其实就是"模型扫到没扫到这句话"，跟分析能力无关。

举两个具体例子，区别就清楚了：

- **检索型（不合格）**：报告白纸黑字写了"TP 从 13.5 降到 11.1"。模型抄一遍就得分；删掉那句话，剩下的数据里**根本没有任何东西**能推出 11.1 这个新数字——出题人自己也推不出来。这种 checkpoint 测的是检索，丢掉。
- **判断型（合格）**：报告只给了 TP=13.50（冻结）和 EPS 的时间序列。出题人在不看 model output 的前提下，单凭剩余数据就能推出"TP 不动但 EPS 在变 → implied P/E 在漂移"。这种 checkpoint 测的是判断，留下。

删除测试是"陷阱在数据里"的操作化判据——它从源头上保证每条 checkpoint 都对应一条**剩余数据足以支撑**的分析推断，而不是单句检索。

---

## 三、构成：一道题长什么样

### 3.1 任务 = 四元组

FAGB 的一道题不是"一个问题"，是一个完整的 task JSON，由四部分构成——这正是 benchmark 的标准结构（Request / Environment / Stopping / Scorer），不只是"一组题目"：

| 部分              | 字段                                           | 内容                                    |
| --------------- | -------------------------------------------- | ------------------------------------- |
| **Request**     | `instruction`                                | 给被测 agent 的任务指令（通用 memo 模板）           |
| **Environment** | `environment.context_files` + `tools_denied` | 可读的文件列表；禁用 web_search / web_fetch；无联网 |
| **Stopping**    | `stopping_criteria`                          | 产出格式（~5000 字 memo）、必需章节               |
| **Scorer**      | `checkpoints`                                | 评分判据（**被测 agent 不可见**）                |

被测 agent 只看到前三部分，看不到 `checkpoints`。

### 3.2 Checkpoint = 把"对"归一化成可判定判据

一道题的难度全在 checkpoint 里。每个 checkpoint 把一条模糊的"分析判断对不对"归一化成一条机器能判定的判据。三种基础 check_type：

- **`must_contain`** — response 必须命中某个正则（模型做对了某个分析）
- **`must_not_contain`** — response 不能命中某个正则（模型没掉进某个陷阱）
- **`number_in_range`** — response 里要出现某个数值（在容差内）

每个 checkpoint 还带一组元数据字段，让 ground truth 可人工复核、支撑分层评分：

| 字段 | 用途 |
|------|------|
| `topic_anchor` | 评分时正则只在这个话题词附近 ±800 字搜，防全文误匹配 |
| `difficulty` | L2-L5 |
| `pattern` | P1-P8 |
| `trap_type` | F-codes |
| `source_file` | checkpoint 对应的原始文件路径（v4 新增） |
| `evidence_span` | 可复核的原文片段（v4 新增） |
| `derived_formula` | 计算公式，供 T0 computation 层执行验证（v4 新增） |
| `metric_anchor` | 数字锚定的具体指标名（v4 新增） |
| `score_type` | 该 checkpoint 适用的评分层（regex / citation / computation / depth 等）（v4 新增） |
| `attribution_exempt` | 是否豁免归因检查（v4 新增） |
| `trap_reason` | 为什么这个点重要 + 模型错了会如何误导投资判断 |

一个真实例子，来自公司C（汽车）那道题：

```json
{
  "id": "C_C21_no_confirm_220bn",
  "description": "Does NOT state 220亿 as confirmed target (mgmt explicitly refused to confirm)",
  "check_type": "must_not_contain",
  "keywords": ["220.*亿.*(?:目标|target|confirmed|确认|预计达到)",
               "全年.*(?:核心|净)利润.*220"],
  "trap_type": "F9",
  "difficulty": "L5"
}
```

材料里管理层因为合规原因明确拒绝确认"全年核心净利 220 亿"这个数。会议纪要里这个数被反复提到，模型很容易顺手把它当成已确认的全年目标写进 memo。这个 checkpoint 测的就是：模型有没有掉进"管理层提了 → 当成确认目标"这个陷阱（F9 = 盲信权威）。删掉纪要里任何单句都不影响——只要模型读到了"管理层不予确认"，它就该知道不能把 220 亿当 base case。

### 3.3 规模与素材

v4 benchmark：**7 家公司 × 5 个行业，~86 个 checkpoint（122 减去删除的 3 个 ticker × 12 CP/ticker）**。

| #   | Ticker  | 公司   | 行业   |
| --- | ------- | ---- | ---- |
| 1   | Co-A    | 公司A  | 医美   |
| 2   | Co-B    | 公司B  | 物流   |
| 3   | Co-C    | 公司C  | 汽车   |
| 4   | AAPL    | 苹果   | 美股科技 |
| 5   | 1211.HK | 比亚迪  | EV   |
| 6   | AUTEL   | 道通智能 | 汽车诊断 |
| 7   | 002028  | 思源电气 | 变压器  |

素材类型（"高质量金融产物"在这里的落地）：

| 格式 | 数量 | 例子 |
|------|------|------|
| 券商研报 .txt | 12 | Citi 多页分析师报告（PDF 提取） |
| 会议纪要 .md | 6 | 中文公司调研 / 业绩会纪要 |
| JSON 财务模型 | 1 | Citi banker model 季度时序 |
| Wiki .md | 1 | Holdings 页（论点 / 指引 / 催化剂） |
| Earnings review .md | 1 | 完整 P&L 拆解 + model variance |
| PDF 研报 | 1 | 公司C 1Q Citi 报告 |

### 3.4 两种模式 + 两个 SKILL

**两种测试模式**用同一套 checkpoint，只是输入形态不同：

- **Mode A Workflow** — 给原始文件（PDF / Word / Excel / JSON / MD）。测端到端能力，**含文件解析**。适合有 file-read 工具的 agent。
- **Mode B Reasoning** — 所有文件预先转成 MD 纯文本。测纯推理性能，消除文件格式处理差异，**跨模型公平对比**。纯 API 模型（如 DeepSeek）走这条。

整套东西拆成两个 SKILL：**SKILL 1 (run benchmark)** 跑测试和评分，**SKILL 2 (creator)** 出题。拆开是为了强制隔离——出题和做题不能共用上下文，详见 §五。

---

## 四、测试什么

### 4.1 典型 failure mode（F-codes）

F-codes 是"模型会犯的金融分析错误"的分类。每条按 **数据呈现 → 应有分析 → 模型出错点** 三步拆开，清晰呈现错误模式。

**F2 字段误标**
- *数据*：财务模型里有一行 `gpm_total[2025Q4] = 82.3%`，同表 `revenue_total = 460.7`、`gp_total = 204.8`，二者相除其实只有 44.5%
- *应有分析*：识别 `gpm_total` 名字虽叫 "total" 但实际是某高毛利 segment（如 产品业务）的口径，**不是**公司综合 GPM；公司真实综合 GPM ≈ 44%
- *模型出错点*：被字段名误导，把 82% 直接写成"公司综合毛利率"，整篇 memo 的盈利能力判断系统性偏高一倍

**F3 实际/预测边界**
- *数据*：模型里 26Q1-Q4 数字没有 `E` 后缀，跟 25 年实际值并排呈现，外观上分不出哪些是已发生、哪些是预测
- *应有分析*：明确标注哪几期属于 forecast、不能当作 fact 引用；引用 forecast 时必须带 "预期/E" 字样
- *模型出错点*：把 26Q2 的预测数字当成"实绩"写进 memo（"Q2 收入 X"），相当于在备忘录里报了一个未来季度还没发生的实际数

**F8 数据捏造**
- *数据*：素材里 Co-A Prime 业务最早从 2024 才有完整披露，2023 只有零星数据
- *应有分析*：写 2023 情况时只用已披露的零星数据，或明确说"2023 Co-A Prime 收入未披露"
- *模型出错点*：编出一个看起来合理的"2023 Co-A Prime 收入 ≈ X 百万"具体数字，纸面工整、实际是无中生有

**F9 盲信管理层**
- *数据*：纪要里"220 亿核心净利"被反复提及，但管理层在同一段紧接着明确表态"**出于合规原因不予确认**"
- *应有分析*：在 memo 里把 220 亿标注为"管理层未确认 / 不构成 base case"，或干脆不写
- *模型出错点*：把 220 亿直接当"全年指引/base case"写入 memo，忽略管理层那句拒绝确认 —— 等于把"被提到"等同于"被承诺"

**F10 增收不增利**
- *数据*：当季收入 YoY +25%，但 NI 亏损同比扩大；同时披露 S&M 同比快速上升、产品 mix 在向低毛利业务倾斜
- *应有分析*：识别"增长是被低毛利业务 + 高费用买来的"，把利润不会自然爬坡作为风险 flag 出来
- *模型出错点*：只看收入增速就写"业务向好/增长强劲"，没把利润反向变化作为对冲 narrative 拎出来，等于挑了报告里好的那一面写

**F12 利润结构倒挂**
- *数据*：新业务占收入的 ~30%，增速非常快，但实际毛利只有25%，净利润亏损；老业务（legacy）虽在萎缩，但仍撑住约 ~80% 毛利率
- *应有分析*：识别"正在用低毛利业务冲整体收入，但传统高毛利业务毛利下滑，moat正在面临挑战"，mix shift 机制下未来的毛利可预期的会不断走低
- *模型出错点*：按收入占比讲业务结构故事，忽略毛利贡献结构，假设未来毛利还会持续增长，得出和真实情况完全相反的判断

**F13 指引前后矛盾**
- *数据*：Q2 报告下调全年指引，Q3 报告又悄悄调回原数，中间没解释为什么
- *应有分析*：把"Q2 ↓ → Q3 ↑"作为指引可信度信号 flag，质疑 management 的 forecasting discipline
- *模型出错点*：只引最新一份报告的指引，没做跨报告累计追踪，相当于把"反复横跳"显示成"维持不变"

**F14 定义精度**
- *数据*：管理层称"已有 25 家门店盈利"——但这是**门店级直接成本口径**（不含总部摊销 / 少数股东权益），同期集团 NI 仍亏损
- *应有分析*：写"盈利"时必须明确口径——门店级 / 公司层 / 含或不含少数股东权益；不要让两种口径在同一段串场
- *模型出错点*：直接照搬"25 家盈利"作为公司层面的盈利证据，掩盖了集团层仍在亏损的事实 —— 读者如果没有足够context读完会以为公司已经走过盈亏平衡点

### 4.2 P1-P8 八类硬陷阱

F-codes 偏"错误类型"，P1-P8 偏"为什么难"。这套是从一轮轮测试里归纳出来的硬 pattern——Opus 反复栽在这上面：

| pattern | 测什么 |
|---------|--------|
| P1 沉默漂移 | 一个数改了，却被描述成"维持不变" |
| P2 方法论内部矛盾 | 同一份报告不同段落用不同基年/口径 |
| P3 声明 vs 数据 | 管理层 Q&A 和同报告数据段自相矛盾 |
| P4 三重数字歧义 | 同一事件三个口径的数字 |
| P5 累积多报告追踪 | 跨 3+ 份报告追踪同一指标 |
| P6 未标注的结构性 | 从 forward cut 推断问题是结构性而非一次性 |
| P7 嵌入式陈旧假设 | 旧估计嵌在总量里，从未更新 |
| P8 先例/趋势识别 | 从分散事件归纳出 pattern |

出题硬规则：≥8/12 的 checkpoint 必须匹配 P1-P8。


### 4.3 三大系统性弱点（最有价值的发现）

跑完 7 家公司、对失败做归因，在当前样本中前沿模型反复暴露出三类系统性弱点（以 F-code 归因的失败为分母；另有 59% 的失败归入 H 类 catch-all，尚未细分到 F-code，不在此三类计数中）。这是整个 benchmark 最值钱的产出：

**弱点一：不独立计算（约占失败的 12%）。** 报告没算的衍生指标，模型也不算——它跟随，不引领。典型例子是公司C（汽车）：报告分别披露了燃油车合营公司的净利和集团合并净利，做个减法就能拆出新能源业务（剔除合营贡献后）的真实盈利水平。模型把两个数都列出来了，但没相减，于是没得出"NEV 板块对集团净利的实际拖累"这个结论。

**弱点二：不质疑权威（约占失败的 16%）。** 管理层说 X，数据说 not-X，模型抄管理层。公司C 220 亿核心净利：纪要里这个数被反复提到，但管理层因为合规原因明确**拒绝确认**。模型多数直接把 220 亿当成"全年目标"或"已确认 base case"写进 memo，没 flag 管理层那句不予确认。这是 sycophancy bias 在金融场景的具体形态。

**弱点三：不追踪静默修订（约占失败的 59%——绝对主力）。** 多份报告之间数字在漂移，标题或叙事却写 unchanged 或反向。比亚迪 25 年出口预测从 1.5M 上调到 1.62M 做了头条（"上调出口"），同份报告里国内预测被悄悄下调更多，总量其实是降的，但模型跟着标题写"出口强劲驱动增长"。苹果 iPhone 出货从 247M 改到 246M 看着像 rounding，可 sell-side 体系里 1M units × ~$800 ASP ≈ $800M 收入差，足够把季度推到 below-consensus 区，研报 summary 仍写 shipments unchanged，模型照抄。模型一律抓不到的原因也很直接：单份报告差异落在 rounding 噪音里，跨多份报告又只读了标题。

注意三类弱点全都是**静默错误**——模型不报错，输出看上去完整又自信，但一个有经验的分析师一眼就能看出来。这正是 失败金矿 那篇讲的"尺子造得出、错误却静默"的领域——必须主动造尺子，错误才会现形。

### 4.4 v4 结果

v4 的 6 层分层评分给出比 v3 更丰富的维度。**注意：以下为未校准（uncalibrated）结果**——完整的投票校准（≥2/3 模型 fail 才保留）是当前待做项，headline 数字会在校准后变动：

| 模型 | Binary（广度）| Checkpoint avg | Depth (Opus judge) | **Combined** |
|------|------------|---------------|-----------|-------------|
| **Sonnet 4.6** | **58.2%** | **0.666** | 0.850 | **0.721** |
| Opus 4.6 max | 53.3% | 0.640 | **0.875** | 0.710 |
| DS V4 pro | 45.9% | 0.600 | 0.850 | 0.675 |

Binary 列是 v3 口径的 regex pass/fail，Sonnet 看起来"赢了" Opus——但这是 Sonnet 条目式写作风格天然命中更多关键词的结果。加入 depth、citation、computation 等维度后，combined 差距收窄到 0.011（0.721 vs 0.710），排名接近。

**Depth judge 的关键发现：三模型深度近乎一样，这是测试集局限不是模型结论。** 三个模型 depth 都在 0.850-0.875，DID_COMPUTE/COMPARE/CAUSE 三项全部 8-10/10 满分，只有 DID_CHALLENGE 有区分度（Opus 5/10 vs Sonnet/DS 4/10，只差 1 个 ticker）。原因很清楚：当前 checkpoint 以 L3/L4 "是否注意到"为主，L5 级"主动做报告没做的分析"太少——题不够难，所以区分不出来。不能从 depth 0.850-0.875 推导"Sonnet 深度足够"或"模型深度一样"——这是尺子的分辨率问题，不是被测物的属性。

**Judge model 选择经过三方验证**：Opus 作为 referee 标准，Sonnet 与 Opus 一致率 91%（可用），Haiku 一致率 62%（不可用——对 DID_CHALLENGE 太宽松，给了 93% pass vs Opus 的 43%）。v4 正式结果使用 Opus 作为 depth judge。

---

## 五、Methodology：pipeline、隔离、grading、校准

### 5.1 五步 pipeline

```
真实金融材料 → FactSheet → 自动检测陷阱 → 生成 checkpoint
                                              ↓
   PM 给任务"写投资备忘录" → 模型写 memo → 对照 checkpoint 评分
                                              ↓
                            校准：丢掉太简单的 → 精简后的 benchmark
```

`FactSheet` 是个关键的中间表示——任何文档（PDF / Excel / 纪要 / 财报 / 研报）都先归一化成 FactSheet（时间序列 / segment / guidance / claim 的标准 schema），出题逻辑只对 FactSheet 操作，不直接碰原始文档。这是 scalability 的地基（见 §六）。

### 5.2 隔离保证（不可违反）

这是整个 benchmark 最容易被破坏、也最关键的一条。

> 被测 agent 必须在**完全隔离的上下文**中运行。出题的那个对话已经接触过 checkpoint / 答案 / 评分逻辑，所以**绝不能**在那个线程里做题。必须 spawn 一个全新 agent，它只能看到 instruction + 文件路径。

| 被测 agent 可以 | 被测 agent 不可以 |
|-----------------|-------------------|
| 读 context_files 列出的文件 | 读 checkpoint JSON / answer key / 其他 model 的 response / 评分脚本 |
| file_read、Python 计算 | web_search、web_fetch |
| instruction + 文件内容 | checkpoint 描述、keywords、expected values、"注意 XX 陷阱"之类的提示 |

出题（SKILL 2）和做题（SKILL 1）拆成两个 skill，本质就是为了强制这道隔离墙。

### 5.3 grading：六层分层 + 三层防误判

6 层分层评分的权重和逻辑见 §二 #4。这里只补 regex 层内部的三层防误判（v3 沿用）：

- **L1 元数据剥离** — 匹配前去掉文件路径/时间戳，防止"Q4"在文件名里被误匹配
- **L2 话题锚定** — checkpoint 带 `topic_anchor`，正则只在锚词附近 ±800 字内搜，避免误匹配命中
- **L3 归因感知** — 禁忌词出现但前面有归因标记（"管理层称""consensus 预期"），不算 fail

即使 regex 层误判，T0/T1 hard verifier 占 55% 权重，整体 combined score 比 v3 显著更稳，但仍需人工 spot-check——claim 三元组提取（§9.2）完成前，false positive / false negative 的系统性统计还没做。

### 5.4 投票校准 vs 单模型锚定

校准是"丢掉太简单的 checkpoint，把难度推进目标区间"。怎么定义"太简单"，有讲究。

早期用**单模型锚定**——以 Opus 为标准，保留所有 Opus 失败的 checkpoint。问题是这会**系统性惩罚锚定模型**：题目全是 Opus 的盲区，Opus 必然分最低，其他模型看起来更好，但那只是因为题不针对它们。

改成**投票校准**——保留 ≥2/3 模型都 fail 的 checkpoint。方法论在 v3 早期 4 公司小规模 set 上验证有效：σ 从单模型锚定的 14pp 降到 4pp，三个模型分数差距收敛到合理区间。

v4 当前态（7 家公司 / ~86 raw checkpoints / 6 层分层评分）：

| 模型 | Combined 总分 | 未校准 binary (regex 层) |
|------|---------------|--------------------------|
| Sonnet | 0.721 | 58.2% |
| Opus | 0.710 | 53.3% |
| DS | 0.675 | 45.9% |

未校准 binary 层 σ = 6.2pp，绝对分数 46-58% 区间已接近 Ofir Press 建议的 10-60% 上沿——区分度会随模型变强快速失效。v4 完整的 ~86 CP 投票校准是当前待做项（3 个模型的 fresh response 全部跑完后执行，产出 v4 calibrated subset）。当前 v4 headline 用 6 层 combined：regex 20% + citation 25% + computation 15% + depth 15% + timeliness 15% + unit 10%，depth judge 在 binary 之外提供连续分维度。

出题全流程还有一道**三阶段 QC gate**（Q1-Q21）：生成后查 ground truth 完整性 / P1-P8 覆盖 / 删除测试通过率 / 正则质量；Opus 测试后查未校准难度 / grading suspect 率；校准后查最终难度 / ticker 均衡。

---

## 六、生成器 scalable 吗

### Tier 1：数据陷阱 →全自动 ✅

`checkpoint_generator.py` 能从**任意** FactSheet 自动检测一批数据层陷阱：

- GPM 字段误标（算 gp/revenue，比对名叫 `*_total` 的字段是否对得上）
- segment 重叠（子项加和 ≠ total）
- forecast 边界（forecast 期缺 `E` 后缀）
- 不完整财年（某年只有 2-3 个季度，不能盲目加总成 FY）
- 增收不增利（收入和净利反向）
- 单位陷阱（多种单位并存）
- 还有 5 个模板分析检查（T1-T5：增收不增利成框、segment GPM 价差、forecast 纪律、利润主驱动、OPEX 去杠杆）

这些全部**由数据 pattern 参数化，不由公司参数化**。`scalable_benchmark.py` 把它串起来：给一个 ticker → 自动找 context 文件 → 抽 FactSheet → 生成 checkpoint → 组装 mega-task。新公司只要有足够的材料，几分钟出题。**这一层（仅 Tier 1 数据陷阱）**实测 7 家公司全部零人工干预出题。注意"零人工"仅指 Tier 1——Tier 2 分析陷阱和 Tier 3 taxonomy 维护仍需人工参与，详见下文。

### Tier 2：分析陷阱（hard core）→ 半自动 ⚠️

但**真正让 benchmark 难的不是数据陷阱**。回看 §四里若干硬核 F-code（如 F12 利润结构倒挂、F14 定义精度）——这些 checkpoint 要求读异构文档、识别 P1-P8 跨报告 pattern。这种东西 `checkpoint_generator.py` 生成不了。

实际做法是反过来的：不是人坐在白板前定 taxonomy 再给 agent 套用，而是 pattern 从真实 error log 里长出来。日常做投研 workflow 时把模型的失败 case 记下来——什么场景、什么原始数据、模型漏了什么、为什么错。攒到一定量后批量喂给 Opus，让它统一读取、归一化、做相似性聚类、抽象成命名 pattern，P1-P8 / F-code 就是这么从一堆真实失败里抽出来的，不是按某个先验框架设计的。Feedback loop 一直在跑，新失败模式不属于已有 pattern 就追加（H 类 catch-all 占 59%，就是这条 loop 的待消化库存）。

Pattern 一旦固化，per-ticker 出题就完全自动化：SKILL 2 spawn 一个 Opus trap-finding agent 读全部材料，按 P1-P8 在新素材里找对应实例 + evidence_span，直接成型 12 个 checkpoint，后面跟三阶段 QC gate、校准、feedback loop。全流程 ~30 min/ticker，7 家公司实测基本符合。

成本结构是一次性高、边际低：上游花在 error log 持续积累 + Opus 周期性抽象 taxonomy 这一段（人脑出真实 case，Opus 出 pattern，没有"坐着想 taxonomy"这一步），但攒到当前 P1-P8 粒度后，分摊到新公司近乎零。所以仍叫"半自动"——半在 pattern 出现的一次性环节，per-ticker 出题已经是 auto。

为什么最终 checkpoint ID 是 `C_C21` / `A_C09` 这种语义化命名而非 `checkpoint_generator.py` 产出的 `AUTO_*` 风格？因为正式 benchmark 跑的是 **trap-finding agent 路径**（覆盖 T1-T5 模板分析），不是纯数据 pattern 的全自动路径——后者只能覆盖 GPM 字段误标、segment 重叠这一档数据层陷阱，硬核分析陷阱 (P1-P8) 还得靠 trap-finding agent 找。

### Tier 3：grading 升级

v3 的 grading verification 是scaleable的真正的瓶颈——正则评分太脆，自由浮动的 `number_in_range` 让 memo 在无关上下文里提到 217 就能通过"FY25 亏损 217"这个 checkpoint，假阳性遍地。生成越多 checkpoint，噪声的绝对量越大。

v4 的 6 层分层评分把脆性压下来一大截，但没修到底。**已修**：T0/T1 hard verifier 占 55% 权重（citation + computation + timeliness 全 deterministic），regex 降到 20%，keyword stuffing 蒙不过大多数 checkpoint 了。**剩余可以做优化的**：

- **claim 三元组 evidence 提取（头号待办）** — `must_contain` 仍是关键词匹配。理想形态是升级成"找 (subject / metric / value) 三元组"，`FY25 / 亏损 / 217` 三个字段必须在同一上下文窗口内同时匹配，才是真正的 metric-anchored 提取。这是 v4 grading 最关键的待办项。
- **T2 depth judge 仍依赖 LLM**（Haiku 一致率 62%，当前用 Opus 成本高），现在用的是 prompt 带正反例 pair + source 数字对照，比开放式 LLM-as-judge 可复现得多，但不是全 deterministic。

### 诚实结论

> 生成器的**骨架**是 scalable 的——FactSheet → generator → mega-task 参数化，7 家公司实测跑通。三层人工口径要分清：Tier 1 数据陷阱全自动、Tier 2 分析陷阱 agent-assisted（per-ticker auto，但上游 error log + taxonomy 维护是人工）、Tier 3 grading 从 v3 regex-only 升级到 v4 六层分层但仍有迭代空间。

这跟 失败金矿 里讲的"归一化"是同一件事：把一条具体失败抽象成 pattern，再在新材料上重新实例化。数据陷阱的归一化做到了代码里（确定性参数化）；
分析陷阱的归一化做到了 P1-P8 taxonomy 里（描述性，靠 LLM agent 在框架下找实例）——后者上游一次性建好，下游 per-ticker 是 auto 的。

---

## 七、对比其他金融 benchmark

### 7.1 主流金融 QA benchmark 的共同结构

经典的金融 benchmark——FinQA、ConvFinQA、TAT-QA、FinanceBench、DocFinQA 这一族——各有侧重（FinQA 偏数值推理链、FinanceBench 偏大规模检索式 QA、TAT-QA 兼顾表格和文本），但在本文关心的维度上，它们**共享一个结构**：

- 任务是**孤立 Q&A**：一个明确问题 → 一个明确答案
- 素材多为**单份文档或单张表**（一份 10-K 的某节、一张财务表）
- 测的是**信息抽取 + 数值推理**：能不能在文档里找到/算出那个答案
- 评分靠**标准答案精确匹配**（数值题尤其干净），部分用 LLM-judge
- 素材是**公开 filing**，大概率已进训练集

我的理解（认知标签：判断）是，这一族 benchmark 解决的是"金融文档理解 + 数值推理"这个问题，而且解决得相当扎实——FinQA 类的数值推理题、FinanceBench 类的大规模检索式 QA，都是成熟、可复现、规模大的工作。FAGB 不试图取代它们，FAGB 测的是它们结构上**测不到**的另一块。

### 7.2 逐维对比

| 维度     | 主流金融 QA benchmark  | FAGB                                                                                  |
| ------ | ------------------ | ------------------------------------------------------------------------------------- |
| 任务格式   | 孤立 Q&A             | workflow 嵌入（写投资备忘录）                                                                   |
| 素材     | 多为单份文档/单表          | 多份异构、跨时间、互相冲突                                                                         |
| 测什么    | 信息抽取 + 数值推理        | 分析判断（没人指路时能否自主发现）                                                                     |
| 难度来源   | 题目本身（问题=难点+指针）     | 材料里的天然误导（陷阱在数据里）                                                                      |
| 评分     | 标准答案精确匹配（干净）       | 6 层分层评分（T0/T1 hard verifier 55% + T2 depth 15% + T3 regex 20% + unit 10%），正则脆性由分层架构缓解 |
| 数据泄漏   | 公开 filing，大概率已进训练集 | runtime leak-resistant（禁联网 + checkpoint 隐藏）；training contamination 未解决（见 §2 #5）       |
| prompt | 直接告诉你要找什么          | 通用 prompt，不给分析方向                                                                      |
| 规模     | 大（千~万级题量）          | 中等（7 公司 / ~86 CP）                                                                    |
| 生成     | 人工标注，静态            | 半自动生成，可在新材料上复现 pattern                                                                |

### 7.3 FAGB 的独特点

一句话：**FAGB 把"指针"拿掉了**（§一已详述）。典型的单题金融 QA 很难测到"自主发现"能力——题目本身已经给了方向，模型顺着执行即可。FAGB 用 workflow 任务 + 隐藏的 checkpoint，专门测这块——这正对应 §四那三大系统性弱点（不独立计算 / 不质疑权威 / 不追踪静默修订），它们全都是"没人指路"时才暴露的弱点。

### 7.4 FAGB 当前的主要短板

对比成熟 benchmark，FAGB 现阶段的短板分五条讲，对应 §九 的五条进化方向：

1. **测试集 L5 深度题密度太低** — depth 分数顶在天花板（详见 §4.4），题不够难导致区分不出模型深度差异。进化方向见 §9.1。
2. **Grading 还没完成 evidence 结构化** — v4 已把 regex 降到 20%、keyword stuffing 蒙不过去了，但 `must_contain` 仍是关键词匹配，claim 三元组提取（subject / metric / value）还没做。进化方向见 §9.2。
3. **Verifier 还没到 strong tier** — T0/T1 hard verifier 占 55%，但 computation 公式覆盖率只有 59%（26/44），depth judge 成本高。进化方向见 §9.3。
4. **环境不拟真** — 当前 task 给的是 pre-extract 过的纯文本 / JSON / MD，模型在禁联网状态下基于一沓清洁文件作答。这跟分析师真实工作场景至少差三层：(a) 真实场景里材料要自己 search / 拉 Wind / 调 CapIQ / 抓 IR 网站 PDF，FAGB 把"知道该去哪里找数据"这一步删了；(b) 真实输入是扫描件 PDF、半成功的 API、rate limit、跨语言素材，FAGB 为了方便跨模型对比，采用 B 方案，基本是已经清洁过的纯文本；(c) 真实工作是 PM 多轮反馈、需求漂移、跨 session 上下文，FAGB 是单 turn 给指令一次成稿。
5. **样本规模小、行业分布稀，缺人类 baseline** — 7 家公司里 3 家是汽车 / EV / 汽车诊断（占 43%，删 SOE/JV/长城后从 6/10 降下来，但仍是单一最大族），剩下 1 家医美 / 1 家物流 / 1 家美股科技 / 1 家工业（变压器），银行 / 保险 / SaaS / 医疗 / 大宗这些主流行业一个没有。汽车 skew 不再是首要短板，真正卡脖子的是总样本只有 7 家、每行业 1-3 家，跨行业统计意义几乎为零。另外没找分析师真跑过，"人比 AI 高多少"现在只是设计意图，不是测量结果。要分清：P1-P8 本身是行业无关的（沉默漂移、盲信管理层、跨源追踪这些 failure mode 在拨备 / ARR / 管线 / 库存语境里都存在），窄的是"这套 pattern 在某行业的具体实例化"还没实证。

---

## 八、与后训练的对接：FAGB → 训练数据 → 模型迭代

回到 失败金矿 的"三个去处"框架——error pattern 可以迭代 skill、做成 benchmark、反哺后训练。FAGB 占第二个，但闭环还没合上：把 FAGB 跑出来的 failure 翻译成训练数据，喂下游训练，再回 FAGB 验证模型在三大弱点上是不是真有进步。

### 8.1 三大弱点 → 三类训练数据

§4.3 跑出来的三大系统性弱点天然对应三种 SFT / preference data 需求：

| FAGB 弱点                   | 训练数据形态                                                                                                                             | 期待信号                      |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| **不独立计算**（~12% fail）      | Chain-of-computation SFT pair：input = 报告里 ICE 净利 + 集团净利分别披露；chosen = 模型自己做减法拆出 NEV 贡献并解释；rejected = 列两个数但没相减                       | §4.3 弱点一类 checkpoint 通过率↑ |
| **不质疑权威**（~16% fail）      | Claim-vs-data preference SFT pair：input = 管理层"220 亿核心净利 / 不予确认" + 财务数据；chosen = flag 不予确认 / 不当 base case；rejected = 直接当全年目标写入      | §4.3 弱点二类 checkpoint 通过率↑ |
| **不追踪静默修订**（~59% fail，主力） | Cross-report diff SFT：input = 两份报告（247M → 246M iPhone shipment + "unchanged" 标签）；chosen = 识别差异 + flag 标签误导；rejected = 抄"unchanged" | §4.3 弱点三类 checkpoint 通过率↑ |

每条 weakness 都不是抽象的"模型不够好"，是可以直接喂下游训练的具体能力 gap——这是 FAGB 一开始就埋好的下游接口。

### 8.2 训练路线假设（取决于 verifier 强度）

> **硬约束**：FAGB eval set 不能直接用于训练——必须划分 train / held-out split，held-out 最好是 OOD（新公司 / 新报告期）。以下是路线假设，从 verifier 到 production reward 还有 reward hacking、coverage、rollout 成本等工程问题待验证。

- FAGB 65% deterministic 层（citation 25% + computation 15% + timeliness 15% + unit 10%）可作 GRPO + RLVR reward prototype；
- T2 depth 15% 走 GRPO + RLAIF 或 fallback DPO；
- T3 regex 20% 虽 deterministic 但 keyword stuffing 易 hack，作 SFT 监督比作 RLVR reward 稳；
- Thesis quality 类只能 SFT / DPO，补完 T5 hard verifier 才能进 GRPO + RLVR

实际跑 RLVR 还要 SFT cold-start，否则 base model 直接 RL 有可能信号稀疏跑不起来

**Reward function 容易写漂移少稳定就 GRPO，写不出走 DPO**。GRPO 要 rollout + reward，但能探索超越 SFT 数据上限；DPO 在静态偏好对上用 preference loss 做梯度训练，不需要 rollout 不需要 reward function，简单稳定但被 chosen pair quality 锁死。RLVR 是 reward 形态（deterministic 算出）——可以套 GRPO，也可以套 PPO

#### FAGB 各类 checkpoint 的路由

| Checkpoint 类型           | Verifier 强度                             | 推荐路径                                                                                                                            |
| ----------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 数字溯源（citation 25%）      | T1 hard（grep 匹配）                        | **GRPO + RLVR**（reward 0/1；纯 grep 易 hack，需配 claim-span alignment + 单位 match + 罚多余数字）                                            |
| 公式类（computation 15%）    | T0 hard（执行公式）                           | **GRPO + RLVR**（reward = unit-aware tolerance + relative error decay，比 0/1 cliff 给 RL 更好的梯度）                                    |
| 时效性（timeliness 15%）     | T1 hard（时段标签匹配）                         | **GRPO + RLVR**（reward 0/1）                                                                                                     |
| 单位/币种（unit 10%）         | T1 deterministic（type check）            | **GRPO + RLVR**（reward 0/1）                                                                                                     |
| Regex（T3 20%）           | 弱 deterministic（keyword + topic_anchor） | **SFT / DPO 优先**——keyword stuffing hack 风险高，作 RLVR reward 不稳                                                                    |
| Depth judge（T2 15%）     | LLM judge + rubric                      | **GRPO + RLAIF**（reward = 0-4 离散；需 frozen judge + calibration set 防 drift）；judge 不稳就退 **DPO**（chosen = depth 满分，rejected = 0 分） |
| Thesis quality（未覆盖, 0%） | 无 verifier                              | 只能 **SFT / DPO**——等 §9.3 补 T5 才能 GRPO + RLVR                                                                                    |


完整判定原则见 A3 §四 13.4。

### 8.3 闭环 loop：benchmark ↔ 训练

形态：

```
FAGB v4 跑分 → 识别三大弱点 → 构造 SFT / preference data → 训练 →
FAGB v4+ 重测 → 看三大弱点 pass rate 有没有上升
   ├─ 没动 → 训练数据 hypothesis 错 → 回去重新构造
   └─ 动了 → 弱点可 train → 沉淀为 benchmark 一轮 update
```

两个 Goodhart 风险要 hold 住：

1. **不能只看 FAGB pass rate** — 训完模型可能在 FAGB 上分数飙升但实际能力没动（过拟合 FAGB 的具体表达 pattern）。必须留 held-out checkpoint，**最好是 OOD**（新公司 / 新报告期 / 新源格式 / 对抗性扰动），同 distribution held-out 也可能 leak。训练时不可见，最终验证用
2. **不能只看三大弱点** — H 类 catch-all 占 59% 待消化，还有大量未命名的失败模式。训完模型可能在三大弱点上进步，但在 H 类某些子 pattern 上退化。需要 per-pattern pass rate 跟踪，不只是 aggregate

### 8.4 现在到这一步还差什么

- **Per-checkpoint 训练 pair 自动生成** — 目前从 fail case 构造 SFT pair 是手工的，不 scalable。要做一个 SKILL 3 (training data generator)：input = FAGB fail trace，output = SFT / preference pair。配合 §9.2 claim 三元组 evidence 结构化，提取的 evidence span 直接就是训练数据的 chosen 部分
- **跑分 → 重训的频率定义** — benchmark 跑分多久喂一次给训练？每月？每季度？取决于训练数据积累速度和模型迭代节奏，目前没定

---

## 九、后续进化方向

FAGB 现在是 stage-2 强原型 + 一把还在打磨的尺子。要变成成熟 benchmark，并且把"能测"的链路再往前延伸到"能喂下游训练"，有五条平行的进化轴——和 §7.4 的五条短板一一对应。

### 9.1 测试集：增加 L5 深度题（头号 priority）

**这是下一版必做、收益最直接的一项。** §4.4 已经显示：三模型 depth 都在 0.850-0.875，DID_COMPUTE / COMPARE / CAUSE 全部 8-10/10 满分，只有 DID_CHALLENGE 有区分度——不是模型一样强，是题不够难。当前 checkpoint 以 L3/L4 "是否注意到"为主，L5 "主动做报告没做的分析"密度太低，depth 分数都顶在天花板。

下一版要把 L5 密度顶上去，重点考察四类**深度推断分析**能力：

- **主动计算 derived metric** — 报告披露 A 和 B，模型自己得算 A−B 才出结论（剔除合营贡献后的 NEV 板块真实盈利）
- **主动发现 silent revision** — 跨多份报告追踪同一指标，模型自己 flag 那些被"维持不变"掩盖的变动（247M → 246M iPhone 出货）
- **主动用数据反驳 management narrative** — 管理层说 X、数据说 not-X，模型必须自己拿数据反推（220 亿"未确认"被当成 base case）
- **主动做因果归因** — 不只列 "NI miss 45M"，还要拆出 S&M 超支 99M = 2.2x miss → "剔除额外一次性branding费用项core利润其实没有那么糟糕"

这四类才是区分"搬运"和"分析"的维度。

### 9.2 Grading：从 regex 到 evidence 结构化（v4 已部分完成）

v4 已完成第一步（见 §2 #4 分层设计）。剩余待做（按优先级）：

1. **claim 三元组 evidence 提取（头号待办）** — `must_contain` 从"找关键词"升级成"找 (subject / metric / value) 三元组"，换说法但语义对的写法也能匹配
2. **metric-anchored 覆盖扩展** — `derived_formula` 覆盖率 59%（26/44），补齐剩余 18 个 checkpoint 的公式
3. **depth judge 模型优化** — 目标是用 Sonnet（91% 一致率）替代 Opus 降成本，或 fine-tune 专用轻量 judge

### 9.3 Verifier 强度：从 weak 到 strong（v4 已部分完成）

FAGB v3 在 A3 §四 13.8 的分层表里属于 **T3 weak verifier**（regex + 同义词词表），单用容易被 keyword stuffing hack。**v4 把 T0/T1 hard check 占到了 55% 权重**，已从 T3 weak 推到 v2 和 v3 的中间位置。

剩余待做的 hard verifier：

| 升级项 | 做法 | 层级 | v4 状态 |
|--------|------|------|---------|
| 数字溯源 grep | 声称引用/披露的 source-stated 数字必须能在 source doc 里 exact match；derived 数字走 computation 层，不适用 grep | T0/T1 | **已完成**（citation 层） |
| Citation link 校验 | 每个数据声明必须 link 到具体文件 + 段落 / 行号 | T1 | **已完成**（source_file + evidence_span） |
| 单位 / 币种 type check | 亿 vs Bn vs Mn / CNY vs USD 混用直接扣分（§3 数值原子性的延伸） | T1 | **已完成**（unit/currency 层 10%） |
| As-of date 校验 | 引用时点数据必须带报告期，过时数据扣分 | T1 | **已完成**（timeliness 层 15%） |
| Computation 执行 | 有公式的 checkpoint 实际跑公式比对 | T0 | **部分完成**（覆盖率 59%） |

终态是分层 verifier 组合：T0/T1 hard verifier 60% 权重 + T2 rubric LLM-judge 20% + T5 narrative DPO 20%——R1 productized 在金融领域的对应物。

下游训练能上 GRPO + RLVR 还是只能 DPO，取决于 verifier 强度（判据见 §8.2，原始详见 A3 §四 13.4）。v4 当前 T0/T1 占 55%——citation / computation / timeliness 这几块够硬，可以上 GRPO + RLVR；thesis quality 判断还得靠 T2/T5 补完才行。

### 9.4 环境保真度：从禁联网静态 → 拟真动态

**这是 v3 最被低估的弱点，也是我做完这一版才真正意识到的。**

FAGB 当前的环境是个 **leak-resistant 但低保真**的简化：禁联网 + 给定 context_files + 单 turn memo。把分析师真实场景做了三层删减：

| 真实分析师场景 | FAGB 当前环境 | 删掉的是什么 |
|----------------|---------------|--------------|
| 自己 search / 拉 Wind / 调 CapIQ / 抓 IR 网站 PDF | 文件已经给齐，禁联网 | "知道该去哪里找数据"这一步 |
| PDF 扫描件、表格 OCR、半成功的 API、rate limit、跨语言素材 | 全是 pre-extract 过的 .txt / .md / JSON | "在 noisy 输入里 robust 拿数"的能力 |
| PM 多轮反馈、需求漂移、跨 session memory | 单 turn 给指令，一次成稿 | long-horizon trajectory |

这正好对应 A3 §十.12 那张表里"金融分析"那一行——FAGB 现在跑的是"干净 CSV / 单份研报"左列，不是"真实 PDF 扫描件、跨报告矛盾、管理层 Q&A vs 数据矛盾"右列。把禁联网当成核心约束是早期 leak-resistance 的代价。

未来可以做的升级：

1. **联网放开 + leak-resistance 由"时间窗"保证，不由"切断 web access"保证。
2. **真工具替 mock** — 允许调用 yfinance / AKShare / web_search / PDF reader 等真实工具，checkpoint 同步扩展：F-codes 多两个新陷阱，F15 = 该联网时没联网（错把陈旧 context 当 fact）/ F16 = 联网拿到错数没识别（被 web 上的噪声误导）。
3. **noisy 输入** — 扔进真实 PDF 扫描件（不预先做 OCR / table 提取）、半成功的 API 返回、跨语言素材。测的不再是"读完给定材料能不能推"，而是"在脏环境里能不能把信号拿出来"。
4. **multi-turn trajectory** — 从单 turn memo 扩到 "memo → PM 给 pushback → 改 → PM 再问"，trajectory 长度从 1 步走到 5-10 步。代价是中间 step 怎么打分（process reward 问题），但这条正好和 9.2/9.3 的 evidence 结构化重合，可以共建。

这条轴推下去 FAGB 就从静态 benchmark 变成了**带 trajectory 的 RL 训练环境**——直接接 A3 §七 RLVR 那条工业化版本，跟 §十.13 表里"高保真"列对齐。

### 9.5 覆盖维度 + 人类 baseline

最低成本、价值最直接的一条，但拖得最久：

- **行业扩展** — 7 家公司里 3 家汽车相关，加银行 / SaaS / 医药 / 大宗。重点不在"再多几家公司"，在验证 P1-P8 这套 pattern **跨行业可适配**（§七.4 #2）——pattern 抽象到这一层应该是行业无关的，但还没实证。
- **人类 baseline 实测** — 找两三个分析师真跑一遍，看人类 pass rate 是多少。出题时的设想是"称职分析师应过大多数"，但这只是设计意图，不是测量结果。在补完之前，v4 结果是"模型 vs 模型"的相对位置，不是"AI vs 人"的绝对差距。
- **历时跑分** — 固定一份 FAGB v4，定期把新模型（Opus 4.7 / Sonnet 4.7 / GPT-5.4 / Gemini 3）拉出来跑那 ~86 个 checkpoint，看在三大系统性弱点上是不是真的进步。这才是 benchmark 作为"尺子"的真正用途——不是测一次，是测很多次。

---

## 后记

这东西不是设计出来的，是 error log 长出来的。最早做的是考试题，前沿模型考 100 分——那个 100 分本身是第一条 finding：纯计算不是难点。难点在"没人给你问题"。从那以后整个方向就从"出题"转向了"造一个真实任务，把陷阱埋进材料里"。

做下来最大的体感：**benchmark 的难点不在出题，在评分。** P1-P8 一旦定好，新公司 30 分钟内就能出完一套 checkpoint（Tier 1 数据陷阱全自动，Tier 2 分析陷阱 agent-assisted）。难的是造一把**不会自己骗自己的尺子**——v4 把 T0/T1 hard verifier 撑到 55%，可信度上了一个台阶，剩余短板见 §九。

写到这里回头看，FAGB 也不是孤立的项目，是这一阵几篇笔记串起来的一个落点。
跟 失败金矿 那篇的链路最直接——那篇讲 AI 在真实任务里犯错 → error log → error pattern → 三个去处（迭代 skill / 做成 benchmark / 反哺后训练），FAGB 就是第二个去处的落地，P1-P8 本身就是一份从一轮轮失败里归纳出来的 error pattern taxonomy。
跟 Guide/Hook/Eval 那篇 §9 的观察 "Eval ≈ Benchmark" 一脉相承——Guide/Hook/Eval 在 harness 层（工作流外面加 gate），FAGB 在 model 层（把外壳拿掉测模型裸的弱点），同一条 error pattern 往两个方向走。
跟 data-validator 那篇是同一种思路换了对象——data-validator 把"这条数据可不可信"拆成 tier / as_of / alignment 三维，FAGB 把"这篇分析对不对"拆成 F-codes / P1-P8 / 删除测试 / 六层 grading，都不依赖单点判断，每维独立约束，组合裁决。

并起来就是一条习惯：高 stakes 的 yes/no 判断先问"是不是真的一维"，不是就拆维度。agent 行为、数据信任、模型能力评估都这么处理。FAGB 整件事就是为"金融分析判断力"这个 sub-layer 造这么一把尺子，v4 比 v3 可信得多，但还没到能交给 AI 自己迭代的程度。

还有很长的路（§九列了五条平行的进化轴）。但方向是清楚的——只要前沿模型在当前样本中仍反复犯"不独立计算 / 不质疑权威 / 不追踪静默修订"这三类静默错误，这把尺子就有量的东西。

---

*Last updated: 2026-05-20*
