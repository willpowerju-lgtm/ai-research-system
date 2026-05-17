---
title: "如何指导 AI Agent 高效率产出 — Guide / Hook / Eval 三层架构"
date: 2026-05-13
type: personal
tags: ["personal", "Personal"]
日期: "2026-05-13"
content_type: "deep_analysis"
summary: "Skill 设计的三层架构：Guide 给方向（轻、可被模型演化绕开）、Hook 绝对护栏（必须遵从）、Eval 结果导向（最关键）。配套 Script-first 原则——能脚本化的数据搬运绝不交给 LLM。三表模型 / PPT JSON / IC Memo Outliner 三个 skill 的迭代实证这套架构。"
companies: []
themes: ["投研系统", "人工智能", "AI agent 工程", "Skill 设计"]
sector: []
key_points: ["设计哲学：LLM 能力快速演进，Guide 是临时脚手架，旧 helper 可能变成新 blocker——所以结果导向（Eval）比过程导向（Guide）更抗腐", "三层：Guide 轻量经验、Hook 硬规则、Eval 多层验收；Eval 是最难、最关键的一层", "Eval 必须跨上下文、跨模型——同 context LLM 有 sycophancy，同模型不同 context 有共性盲区，跨模型（Codex）更接近真正的 second opinion，主观感受是缺陷捕获大约 +30%", "Script-first：机械操作脚本化，LLM 只在需要判断时介入；准确度、速度、token 三方面都赢", "一个被低估的好处：eval log 跟 vendor benchmark 结构同构，error log 是 RLAIF/process reward 训练资产，verifier 可迁移性 > generator 可迁移性"]
---

# 如何指导 AI Agent 高效率产出 — Guide / Hook / Eval 三层架构

> 一份工程实践笔记。
> 写给自己对过去几个月 skill 设计经验的总结，以及任何在做"AI agent 怎么稳定产出"的人。

---

## 一、问题缘起：LLM 自由发挥的代价



最早写 skill 是 v1 风格——大段自然语言告诉 LLM "应该怎么做"，例如：

> 第一步，读取财报 PDF。
> 第二步，提取历史财务数据写入 Raw_Info sheet。
> 第三步，建 Assumptions sheet，列出所有 forecast driver。
> 第四步，根据 Assumptions 计算 IS……

LLM 会"按指示"执行——表面上。实际跑下来的问题清单：

- **漂移**：本来要把数据写成"引用源单元格"的链接公式，LLM 习惯性写了具体数字。模型从此失去可计算性，但表面上"完成"了。
- **隐性截断**：某一步生成的代码超出工具输出上限，被静默截断。前半段执行、后半段丢失，LLM 不知道，继续往下跑。最终结果不平。
- **同 session sycophancy**：让 LLM 自己审查刚才写的代码，它会找小修小补，不会承认"整体方向错了"。
- **跨 session 失忆**：context 压缩之后，LLM 忘了关键 mapping 是什么，重新猜一遍，猜错了。

每个问题都可以"打补丁"——但补丁会越积越多，guide 变成 30 页的天书，LLM 看完前 5 页就忘了后 25 页。

一句话：越想用 prose 把 LLM 行为锁死，guide 越长；guide 越长，LLM 越读不完；读不完就漂移；漂移又得打补丁。死循环。

## 二、正确的设计哲学：为什么是三层

先承认一个 skill 层面的缓解手段：**渐进式披露**（SKILL.md 主入口做路由 + `references/` 按 phase 按需加载）确实能显著提升指令遵循度——把 30 页天书拆成多份小文件，LLM 每个阶段只看到当前需要的规则，前 5 页忘后 25 页的问题被结构性缓解。但这只是把"一卷天书"改成"分卷出版的天书"——本质上还是在打补丁。真正的问题不是 guide 太长，而是**用 prose 锁 LLM 行为这件事本身就不可持续**。

打补丁打了1个月之后，意识到一件事：

> **LLM 能力在快速演进。Skill guide 本质上是 post-training 之后的额外脚手架。今天为了规避某个模型弱点写的 helper，下一代模型可能完全不需要——甚至会变成 blocker。**

Anthropic 自己的模型演进史也在反复印证这个方向：

- 早期 Claude 不擅长 parallel tool call，要在 prompt 里反复强调"批量调用"；Anthropic 官方文档现在定位 Claude 4 在默认并行 tool use 上更强——我观察到的是旧提示对新模型反而是干扰。
- 早期 context 短，要写"compact resume protocol"；1M context 之后我的大部分场景不需要了。

**Key thesis**：

> Guide 应该轻，因为它会过期。
> Hook 应该硬，因为它是绝对边界（覆写权限、破坏核心文件、违反业务铁律），跟模型能力无关。
> Eval 应该准，因为它是结果导向的——不管 LLM 怎么演化，最终交付物对不对，是可验证的客观事实。

三层架构的本质，就是把"易变的"和"恒定的"分开。Guide 可演化绕开，Hook 不可绕，Eval 看最终交付物。

- **Layer A · Guide / Workflow** — 轻 · 经验内化 · 模型演化可绕开
    - 作用：指方向，不限路径
- **Layer B · Hook 绝对护栏** — 硬 · 必做项 + 必不做项 · bash 前拦截
    - 作用：在 LLM 写代码前直接 exit 2
- **Layer C · Eval 多层验收** — 重 · 结果导向 · 跨上下文 + 跨模型
    - 作用：质量出口的最后一道闸
    - 配套 **Script-first** 孪生原则（机械操作脚本化，LLM 只在需判断时介入）

---

## 三、Layer A：Guide — 经验内化，但不锁死路径

### 3.1 Guide 的合理形态

Guide 是"人类知识经验的内化"——把人类做这件事时已经踩过的坑、形成的工作流，告诉 LLM。例如：

- 长任务拆 SESSION，每个 SESSION clean context
- 状态写到 `state.json` sidecar，不要靠 conversation 记忆
- Compact resume protocol：context 被压缩后，先读 disk 再继续
- 复杂任务用 `_model_log.md` checkpoint，下一阶段从 disk 读，不从 context 读

这些都是好建议——但**每一步具体怎么实现，留给 LLM**。

### 3.2 为什么 Guide 越薄越好

实测发现：**guide 写超过 ~500 行，LLM 的指令遵从度反而下降**。
原因：

- 长 guide 占 context，挤压 LLM 自己思考的空间
- 长 guide 里的次要规则容易被忽略
- 长 guide 容易自相矛盾（同一份文件写 3 个月，前后规则可能打架）


### 3.3 漂移可能是创新，也可能糟糕

这一层最反直觉的一点是：LLM 漂移不一定是错的。

人类设计的流程不是最短路径。一个例子：IC Memo skill 原本规定的顺序是"先列论点 → 再收集数据 → 最后拼 deck"。某次 LLM 漂了——收集数据时发现一条原以为关键的论点，数据其实根本不支持，于是它没按计划继续收，而是先回头调整论点结构再接着干。规定路径下，论点是写在前头锁死的，根本没有"用数据反向校验论点"这个环节；漂移反而把它补上了。

但漂移也可能糟糕。LLM 把"嫌麻烦"合理化成"优化路径"，比如建模最后跳过 BS 配平检查就交付。

Guide 区分不了这两种漂移。所以这一层不强行约束，把判断权交给 Eval。怎么走随便，最终交付前 Eval 会判断。

---

## 四、Layer B：Hook — 绝对护栏

### 4.1 两类规则

Hook 是 PreToolUse 钩子，在 LLM 真正调用 bash 之前拦截。两类规则：

| 类型       | 性质                 | 典型规则                                                                                     | 失败行为               |
| -------- | ------------------ | ---------------------------------------------------------------------------------------- | ------------------ |
| **必做项**  | 漏了下游 Eval 必拒，返工成本高 | 建模forecast revenue 写 cell 必须是 =`Formula` 字符串、单位必须先锁定、bash 命令前必须 spot-check state map     | bash 不允许执行，让 LLM 改 |
| **必不做项** | 任何情况都不允许           | 覆写核心 config 文件、push 时硬编码 `C:/Users/<name>/...`、跳过 git hook 签名、A 股调用 `yfinance.forwardPE` | exit 2 直接阻断        |

两类区别只是哲学上的——实现上都是 `exit 2` + 一段 explainer message。

### 4.2 触发方式

Hook 在 LLM 真正执行 bash 之前介入：扫一遍即将执行的命令字符串，命中违规模式就拦下，把"为什么拦"作为错误信息返回给 LLM——LLM 据此改写。规则本身怎么编码（regex、AST、还是别的）是工程问题，跟架构无关。

### 4.3 自门控（重要）

Hook 必须**自门控**——只在本 skill 上下文激活，不污染其他 skill。

实现：hook 内部先 regex 检测命令字符串里是否包含本 skill 的关键词（如 `Raw_Info` / `RAW_MAP` / `_State`），不命中则直接 exit 0 放行。

为什么重要：一个 vault 里有 60+ skill 共用同一套 hooks。如果某个 skill 的 hardcode guard 没有自门控，会拦下其他 skill 完全合法的 bash 命令——用户体验崩坏，且 LLM 会被错误信号误导。

### 4.4 几个高 ROI 的 hook 类型

- **硬编码守卫**：建模时把数字直接塞进 cell（而不是用公式引用）会让模型失去可计算性，hook 在写入前拦
- **数据源误用守卫**：某些 API 对特定市场返回错单位（典型例子是 yfinance 对 A 股 / 港股的 forward PE 不可用），写代码时直接拦
- **跨平台路径守卫**：push 之前扫 staged diff，发现绝对用户路径直接拒，避免协作时炸
- **大纲质量 gate**：写 outline 时强制几项硬阻断（数据底稿存在、每页数据点下限、关键章节齐全），低于阈值不让进下一阶段

### 4.5 Hook 的设计哲学

Hook 本质上是一道**安全护栏**——不教 LLM 怎么做，只告诉它什么绝对不能做。

这跟 Guide 形成对比：Guide 是"建议这么做"（可演化绕开），Hook 是"这么做必拒"（不可绕）。

Hook 的数量应该是稳定的——它编码的是业务铁律和工程边界，不是某个模型版本的弱点补丁。一个成熟 skill 的 hook 数应该在个位数。

---

## 五、Layer C：Eval — 最难也最关键的一层

### 5.1 为什么是最难的

Eval 是质量出口。LLM 可以靠任何手段 deliver 产物，但产物对不对、是不是"真的做完了"，LLM 自己说了不算。

设计 Eval 的难点在于找谁来当考官。这是整个架构里最微妙的部分。

### 5.2 为什么单一 Evaluator 不够

每种 evaluator 都有盲区：

| Evaluator 类型 | 优势 | 盲区 |
|---------------|------|------|
| **Python 机械检查** | 100% 客观，零成本，毫秒级 | 只能验证可形式化的事实（数字、公式、文件存在性），不懂语义 |
| **同 context LLM 自审** | 简单，无额外 token | **强 sycophancy**——被前面对话锚定，倾向认同自己的产物 |
| **独立 context 同模型 LLM** | 清零启动，无锚定 | 同模型家族有共性盲区——某些错误模式两次都会犯 |
| **跨模型 LLM**（如 OpenAI Codex 对 Claude） | 完全不同的 prior，抓得到同模型盲区 | 不熟悉本 skill 的具体约定，需要 prompt 把 context 喂进去 |
| **人类** | 终极裁判 | 慢、贵、易疲劳 |

**没有任何单层 Eval 能覆盖所有盲区**。所以最终方案是多层级 Eval，每层各司其职、相互补位。

### 5.3 三个 skill 的 Eval 架构

下面用三个具体 skill 印证这套思路。

#### A. 长跨期 Excel 建模 skill — 5 层 Eval

- **L0 机械层**：数值勾稽（BS 配平 / IS 重述 / CF 收口），脚本即时判定
- **L1 独立 context 同模型**：清零启动，做语义审 + spot check 抽查若干 PASS 项
- **L2 跨模型**：高危红线（论点-模型一致性 / 关键公式根因 / 跨表 integrity）交给不同 family 的模型审
- **L3 备用跨模型**：L2 不可用时降级到另一家
- **L4 合并裁决**：三方结论汇总，输出最终 verdict

L1 / L2 并行 dispatch、主线程不阻塞；但任何"完成"标记落盘前必须等所有 verdict 回齐再合并裁决——并行只省墙钟，不松绑 gate 顺序。三方都 PASS 才算交付，任一 BLOCKER 阻断。

**实际收益（主观观察，未做严谨统计）**：加上 L2（跨模型）这一层，我的样本里缺陷捕获大约多 30%。最典型的是这种盲区——表面机械勾稽全 PASS（合计、配平都对得上），但某个比率明显反常识。同模型 review 会接受"加总对了"这个数字，跨模型会 push back "ratio 不合理"——往往真的是底层有错位。

这个数字是体感，不是严格 N/baseline/CI 标定。方向上跟公开文献里跨模型 cross-examination / multi-agent debate 报告的收益一致，但具体幅度的可推广性留给读者打折扣。

#### B. PPT 渲染 skill — 多层机械 + 人审尾

PPT 的好处是视觉约束大部分可形式化——文本溢出、几何越界、形状重叠、配色合规、密度分布、已知渲染 bug——这些都能脚本化。所以前几层全部交给机械检查（写入时即时校验 + 编译后整体校验 + 渲染产物物理检查），LLM judge 反而用不上。

最后留一层给人——视觉一致性、节奏感、叙事流畅度。这部分 LLM 目前还判不准，所以不假装能自动化，老实写到清单里让自己最后看一遍。

#### C. IC Memo Outliner skill — Codex 跨模型语义 gate

Outliner 的产物是 thesis tree + slide outline。最早的设计是"LLM 自己 self-eval"——同模型同 context 跑一遍 6 项 check（论据覆盖、估值必要段、金字塔结构、连贯性等）。

实测：**完全没用**。同 context self-eval 永远 PASS——sycophancy 太重。

替换方案：**dispatch 跨模型 Codex agent 做 C1-C6 语义审**。Codex 看不到前面的对话历史，只看落盘的 `_thesis_tree.json` + `_outline.md`，针对 6 项 check 给 PASS/CONDITIONAL/FAIL verdict。

切换后第一次跑就抓到一条之前 self-eval 漏掉的硬伤——"Valuation section 写了三个倍数法，但没说为什么选这三个"。这种"看起来都写了，但论证链断了一截"的问题，同模型同 context 自审看不出来。

### 5.4 Eval 设计的几条原则

1. **机械层尽量厚**：能用 Python 判断的全部前置（成本零、速度毫秒级）
2. **LLM 层必须独立 context agent**：清零启动，不要在主对话里 self-eval
3. **关键产物必须跨模型**：高价值交付（最终模型、IC Memo、deck）至少跑一层 Codex 或其他外部模型
4. **多层并行不串行，但交付前必须 join**：L0/L1/L2 同时 fire，主线程不阻塞——但任何 commit / MODEL_COMPLETE 写入之前，必须等所有 verdict 回齐再合并裁决。并行只省墙钟，不松绑 gate 顺序。
5. **失败要可解释**：每个 verdict 必须带 evidence + fix_hint，不允许 "FAIL, please fix"

### 5.5 Eval 是结果导向，所以最抗腐

Eval 检查的是"做完了对不对"，这是客观事实，不随模型演化而变。所以是三层里最值得投资的。新模型上线，Guide 可能要重写一半，Hook 可能精简一些，Eval 主要做小修补（更新过时 case、调阈值），case 本身的结构不变。

Eval 也不是永恒的。SWE-bench 自己都在不断出新版本对抗 contamination，agent 学会针对 checklist 之后也会有过拟合风险。但相对于 Guide 可能面临的重构，Eval 的维护是边际成本，不是替换成本。

---

## 六、Script-first：Eval 的孪生原则

跟 Eval"判断结果对不对"的孪生原则是：**能不让 LLM 做的事，就别让 LLM 做。**

数据搬运、格式套用、单元格写入、JSON 读写、文件 hash……这些机械操作全部脚本化。LLM 只在"需要判断"的环节介入：选哪个 slide pattern？这条 catalyst 是不是 material？这段 thesis 的核心承诺数字是哪个？这家公司在情绪周期的哪个阶段？——这类才是 LLM 该做的事。

收益不是边际改善，是数量级差异：

| 维度 | LLM 做 | 脚本做 |
|------|--------|--------|
| **准确度** | 偶尔"约/大约/接近"，会 hallucinate 数字 | 对正确输入是确定性的 |
| **速度** | 1750 个 cell 写入 ≈ 30 分钟 | 200ms |
| **Token** | 35k token 一次 build | 0 |

更关键的是**确定性**：脚本对同一正确输入永远产出同一输出，LLM 不保证。脚本本身可能有 mapping bug / schema drift / 上游 input 坏掉——这些是 e2e 测试和 schema 校验的事——但消除了 LLM 采样方差这一层不确定性。

这条原则跟 §五 的"机械层尽量厚"其实是同一回事，只是站在两侧：

- **生成侧（§六）**：能脚本完成的，根本不让 LLM 写
- **验证侧（§五 L0）**：能脚本判断的，全部前置成 eval 的机械层

合起来一句话：**脚本能做的事，从生成到验证两端都让脚本做，LLM 只在中间"需要判断"的窄通道里出现**。这样 LLM 的错误 surface 缩到最小，Eval 也只需要审"真正需要判断的那 20%"。

---

## 七、三个 skill 印证这套架构

| 维度                  | 长跨期 Excel 建模 skill | PPT creator skill | IC Memo Outliner |
| ------------------- | --------------------- | ----------------- | --------------- |
| **Guide 大小**        | 中等主入口 + 十几份按需 reference | 略大主入口 + 三十份 reference | 中等主入口 + 十几份 reference |
| **Hook 数**          | 个位数（围绕硬编码 / 单位 / 颗粒度 / 数据源误用） | 个位数（品牌 / 图表数据 / 密度） | 个位数（围绕大纲质量硬阻断） |
| **Eval 层数**         | 5 层（机械 → 独立同模型 → 跨模型 → 备份跨模型 → 合并） | 多层机械 + 人审尾 | 1 层跨模型语义 gate |
| **Script-first 范围** | 状态 I/O / cell 写入 / anchor 对比 / 格式 / QC 套件 | 编译 / 图注入 / 修复 / 校验 | 论点树校验 / 数据底稿 / 源文档覆盖 |
| **迭代规律**            | Guide 越写越薄；Hook 数稳定；Eval 越长越深 | 同上 | 同上 |

**共同规律**：
- Guide 经历精简——早期试图用 prose 锁死，后期意识到不如让 hook + eval 兜底
- Hook 数稳定——业务铁律就那么几条
- Eval 持续加深——加 Codex 跨模型层之后再没回到单层

---

## 八、几个未必显然的经验

### 8.1 不要让 LLM 自己评判自己

同 context self-eval 几乎一定 PASS——sycophancy 在长 context 下尤其严重。
应对：所有 Eval 必须 dispatch 新 agent（清零 context）；高价值产物用跨模型 review

### 8.2 跨模型不等于"用另一个 Claude"

同家族模型（同样是 Claude / 同样是 GPT）会有共性盲区——某些错误两次都会犯。
真正的跨模型审查需要不同 family 的模型（Claude ↔ GPT/Codex ↔ DeepSeek/Gemini）。

### 8.3 Hook 必须自门控

否则会污染其他 skill 的执行流。逻辑很简单：先看本次 bash 命令是不是发生在本 skill 的上下文（命令字符串里有没有本 skill 的关键 token），无关就立即放行，不做后续检查。

### 8.4 State 出 context，落 disk

不要把状态写在对话里（"上一步我们做了 X"）。Context 压缩会丢，sub-agent 看不到。所有跨阶段状态写到 disk（state 文件 + 阶段 log），下次启动 / compact resume 从 disk 读，不从 context 读。

### 8.5 数据搬运绝对不用 LLM

哪怕是"把这个数搬到那个 cell"这种简单到不行的操作也不让 LLM 做。
理由：上千个这种操作累加起来，就是上千个潜在 hallucination 点。

### 8.6 漂移可能是创新，但创新也要过 Eval

不要在 Guide 层试图压制漂移——压不住，反而让 LLM 学会"伪装合规"。让漂移自由发生，用 Eval 拦截糟糕的漂移，保留好的漂移。

### 8.7 入口必须写明 compact 后的恢复路径

每个 skill 主入口都要强制写明"context compact 后第一件事"——读 state 文件、读运行日志、不要凭记忆继续。否则压缩后 LLM 会重新猜上下文，猜错了不自知。

---

## 九、一个被低估的好处：Eval log 是 vendor 级训练资产

写到这里回头看，这套架构还有一个之前没明确意识到的好处。跟"建一个能用的 skill"这个目标无关，但更有意思。

### 9.1 结构同构：Eval ≈ Benchmark

Vendor 评测前沿模型用的 benchmark（SWE-bench / τ-bench / AgentBench / GPQA）骨架是：**一个具体任务 + 独立的 evaluator + pass/fail verdict + diff**。

我们日常 skill eval 的骨架也一样：**一个具体的产出任务（一份模型 / 一篇 memo / 一份 deck）+ 多层 evaluator（脚本 + 独立 LLM + 跨模型审）+ 分级 verdict + fix_hint**。

完全同构。差别只在**规模**和 **ground truth 是从哪来的**，不在结构本身。

### 9.2 Error log 是 RLAIF / 过程奖励模型需要的数据

每跑一轮跨模型 review，会落下几份 verdict——机械层判定、同模型独立 review、跨模型审、最终合并裁决。把这些 verdict 跟 LLM 的**初版产出 + 修复后产出**配对，自然就形成一条 **preference pair 流**：同一个任务输入，"被拒绝的初版" vs "通过的改版"，附带"为什么被拒的批注"和"机械层 ground truth"。

从前沿模型团队的视角看，这种数据有四个稀缺特性：

- **真实分布**——来自实际生产任务，不是人工合成的 benchmark item
- **客观 verdict**——跨模型 + 脚本双重 ground truth，不依赖人工标注
- **失败模式多样**——硬编码裸数字（破坏可计算性）、字段错位（表面对齐但语义错）、verifier 过度认同 generator（sycophancy）、单位/口径不一致……都是 LLM 真正会犯的错，不是人工编出来的
- **天然 preference pair**——fail → fix 的 diff 就是现成的 pair，连标注都省了

这正是 RLAIF / Constitutional AI / o1-style process reward model 训练所需的输入格式。

### 9.3 三个 sharpening

**S1. 不只是复用 benchmark，是 dynamic benchmark generation**

传统 benchmark 静态发布，SWE-bench 一次冻结 N 个 task。我们的 eval log 是持续生成的：每次跨模型 review 抓到一个新失败模式，就是一个新 benchmark item。这比静态 benchmark 强的地方在于会随模型能力演进自动升级难度——模型越强，简单失败模式越少，eval log 自动聚焦到更难的 case。

**S2. Verifier 可迁移性 > Generator 可迁移性**

一个二阶推论，但很关键：

- Hook + 机械 eval + 跨模型 gate 都是**模型无关的**——换个 generator 模型，整套 eval 照常跑
- 也就是说，eval 投资跨模型版本是**复利**；guide 投资是**贴现**

这正好印证文章前面 "Eval > Guide for durability" 的核心论点——从 vendor 经济学角度的二次证明。前沿模型团队都在喊"我们不缺 reward model，我们缺 verifier"——恰好就是 verifier 比 generator 更稀缺、更值钱。

**S3. 跨模型 review 同时是数据干净度保障**

前面把跨模型 review 归因为"消除 sycophancy 和共性盲区"，其实还有一个更深的动机：如果 eval 的 LLM judge 也是 Claude，verdict 就被 Claude 的偏好污染了，拿来训练 Claude 是循环喂自己。

所以跨模型这一层不只是质量保障，也是训练数据干净度的保障。把 eval log 当训练资产用的话，verdict 跟 generator 同源等于让学生改自己的卷子。

### 9.4 Caveats（保持诚实）

- **隐私门槛**：error log 里有公司名 / 数据点 / thesis，vendor 要用必须 explicit opt-in + 脱敏管道
- **Verdict 噪声**：跨模型 review 自己有 false positive，作训练信号前需要校准
- **方向性洞察**：这是从 RLAIF / scalable oversight / process reward 几条线索推出的判断，没有 published paper 直接验证 "user skill eval = vendor benchmark gold"（虽然方向上跟 Constitutional AI / RLAIF / o1 process reward 都吻合）

打完这些折扣，方向不变：搭好 eval 不只是把自己 skill 做对，也是在帮 vendor 做下一代模型。这两件事的利益在结构上同向。

---

## 十、可复用 checklist — 写新 skill 时按这几条对照

**A. Guide 层（轻）**
- 主入口只放核心铁律 + 流程骨架，细节按 phase 拆 reference 文件按需加载
- 不试图用 prose 锁死 LLM 每一步行为

**B. Hook 层（硬）**
- 必做项：漏了下游 Eval 必拒的，写护栏在 bash 前拦截
- 必不做项：覆写核心 / 跳验证 / 硬编码路径，硬阻断
- 所有 hook 自门控——只在本 skill 上下文激活，不污染其他 skill
- 数量克制——它编码的是业务铁律，不是模型弱点补丁

**C. Eval 层（重）**
- 机械层尽量厚——可形式化的事实全部前置检查
- LLM 层必须独立 context——不在主对话 self-eval
- 高价值产物必须跨模型——避免同家族共性盲区
- 多层并行 dispatch，但任何"完成"落盘前等所有 verdict 回齐合并裁决
- 每个 verdict 带 evidence + fix_hint，不允许 "FAIL, please fix"

**D. Script-first 孪生原则**
- 数据搬运 / 格式套用 / 文件 I/O 全部脚本化
- LLM 只在需要判断时介入

---

## 后记

这套架构不是设计出来的，是踩坑踩出来的。最早 v1 是纯 prose guide，补丁越打越乱。意识到"模型会变、guide 是临时脚手架"之后，重心从"教 LLM 怎么做"转到"验证 LLM 做出来对不对"。

改动完善之后，发现一个好处：新模型上线（OPUS4.6 → 4.7）的迁移成本几乎为零。Hook 不动，Eval 不动，只有 Guide 要审一遍看哪些段落变冗余，而 Guide 本来就轻。

这是过去几个月最实际的体感：结果导向的检验跨模型版本最稳定。

---

*脱敏说明：本文涉及的具体公司 / ticker / 基金名已隐去，只保留架构与方法论。*
*Last updated: 2026-05-13*
