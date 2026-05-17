# 从 Cowork 到 Claude Code：一个买方研究员的工作站迁移实录

## 前言

清明潜水回来以后，我把设计了个把月的 Cowork 工作流整体搬到了 Claude Code native。我是真真切切的摸到了那堵挡在我前面的墙，他是一个架构的问题不是设计的问题。感觉现在自己已经从一个Financial profession 变成了Engineering profession... 算是回归以前学校里的本职专业了...这个世界真的是个魔幻的循环

## 一、 Cowork的墙

### 1.1 单线程卡脖子

Cowork 的执行模型是单线程的。简单任务没问题，但我每天早上要跑全球宏观早报，美国、中国、港股、加密货币四路数据同时拉。Cowork 里这四路只能排队，一路卡住全部等。一份早报跑完经常要15-20分钟，大部分时间花在等上。 ^kp1-一份早报跑完

更痛的是 deep research：先批量向 NotebookLM 提问9个模块，再做2轮深度追问，最后合成 report 初稿。三个阶段全串行，一个 initiating coverage 跑下来要3-4小时。中间还不能断，Cowork 没有断点续传，session 一断前面的中间结果就没了。虽然也写了很多断点续传机制，但是限于架构原因执行力看运气。 ^kp2-三个阶段全串行

### 1.2 没有跨 session 记忆

Cowork 每次打开都是一张白纸，他不记得我其他session做了什么，哪怕是我在skills 里面写入了session log逻辑，他也不会每次启动自动读取，需要我手动提醒他去读取，没有每次固定加载的claude.md 作为trigger, user preference 又不是很稳定。



### 1.3 Chrome 自动化不稳定

工作流有几条线因为反爬虫，API额外费用原因重度依赖浏览器自动化：Gemini Deep Research 跑行业报告、诸多反扒网站无法代码接入。Cowork sandbox 环境只能调用 Chrome MCP —连接断开、页面渲染不全、反爬绕不过去，sandbox下载绕路，每次出问题都要手动介入，谈不上自动化。切换code 以后可以本地调用CDP模式，稳定性好了不少。

### 1.4 Skill 管理是体力活

Cowork 的 skill 修改后要重启 save 才能生效。我当时已经有38个 skill，改一个 prompt 就要退出重进、重新加载 context，改一个词浪费两分钟。

Skill 之间的调度更麻烦。earnings review 要先调 data fetcher 拉数据，再调 transcript parser 解析电话会，再调 memo writer 出稿。这种串联在 Cowork 里只能手动一个一个触发，没有编排层。



## 二、Claude Code 的进化

### Orchestra + Sub-Agent Framework

迁移的首要动机便是code真正支持orchestra + sub agent架构 也支持python background runing，还可以无限多开（只要token足够... 好羡慕身边提供无限claude opus token的机构的朋友 ... ）

Claude Code 支持三种 sub-agent 模式 ：

* Fork——独立并行，共享 prompt cache，成本接近零。早报四路数据同时出发，谁先回来谁先落盘。

* Teammate——多阶段工作流，阶段间通过文件 mailbox 传递。deep research 的 NLM 批量问询（Haiku）到深度追问（Sonnet）再到合成初稿（Opus）走的就是这个模式。

* Worktree——隔离沙箱。爬虫、批量写入这类可能失败的任务放 worktree 里跑，炸了不影响主 agent。

实测早报端到端从15-20分钟降到5-8分钟。deep research 从"必须一口气跑完"变成按阶段 checkpoint，可以跨 session 续传。

### 2.2 三层持久化 Memory

Claude Code 的 memory 分三层。

MEMORY.md 是轻量索引，常驻 context，每条不超过150字，放系统配置这类高频信息。

memory/topic/ 按主题归档详细记录，按需拉取，hooks 配置、路径速查表、repo 分工原则都在这一层。

session-log/ 是跨 session 工作台账，每次 earnings review 做到哪一步、上次 visiting memo 用了什么模板、哪个 API 出过什么坑，全部落盘，下次 session 自动恢复上下文。

最下面一层还有每次具体任务的错误日志，做到每一次都可以追溯，中断都可以恢复，快速检索。

有一条硬约束：memory 是 hint，不是 truth。从 memory 读出来的信息，做决策前必须回原始文件或实时数据源验证。

### 2.3 Hooks 系统

Hooks 在工具调用前后自动触发脚本，不占 context window，不需要 AI 自己记住该做什么。

几个在跑的例子。PreToolUse 阶段：输出 PPTX/DOCX 前自动跑 data-validator 做来源分级和交叉校验；CDP 操作前检查连接；git push 前自动从云端读取 token。PostToolUse 阶段：Write/Edit 完成后自动检测研究产物的文件名模式，更新 workflow state，比如写完 outline_draft.md 就自动标记阶段完成。Stop 阶段：session 结束时归档工作日志。

Cowork 时代 data-validator 是手动触发的，经常忘。PPT 里的数据分级标记也是交付前才想起来清理。现在全自动。

### 2.4 模型分级调度

每个环节可以指定模型。Cowork 时期这套分级只是设想，没有工程支撑。现在 SKILL.md 里直接声明 model: haiku，sub-agent 调度时自动匹配。

举个实际的例子：某消费医疗标的的用户研究，原来 Phase 2 的 NLP 分析全部 Sonnet 处理，包括逐帖打标签（情感、品牌提及、竞品、风险关键词）。迁移后在 Phase 1 和 Phase 2 之间插了 Phase 1.5，由火山方舟豆包做批量打标，Sonnet 只管上层分析，token 用量降了60%+。

### 2.5 跨平台可移植

迁移过程中被迫建了一套跨平台规范，因为 repo 同时被 Windows 主机和 Mac 笔记本 clone。

规则就一条：git 跟踪的代码文件里不许出现硬编码路径。机器相关路径放 .env（云端同步）和 config/local.json（.gitignore 排除），Python 统一走配置模块读取。

加了一个 pre-push hook，提交内容里出现硬编码本机路径直接拒绝 push。前两周拦住了五次无意识的硬编码。

### 2.6 数据获取分级

web-access skill 在 Chrome DevTools Protocol 之上加了一层代理，解决了浏览器自动化不稳定的问题。数据获取按 T0-T4 五级：

T0 是 web-access skill，默认联网入口，CDP 模式带 Chrome 登录态。T1 是专用 API（FRED、AKShare、yfinance），一手数据。T2 是已知 URL 直取（WebFetch + Jina）。T3 是 CDP 浏览器自动化，用在小红书、微博这类反爬场景。T4 才是 WebSearch，作为最后手段。

核心思路：数值不走搜索引擎。股价用 yfinance，美国宏观用 FRED API，A股共识预期用 AKShare。有确定性 API 的东西不应该让 AI 去搜索引擎搜一个可能过时的数字。



## 三、新模块与核心升级

搬到 Code 以后不只是底层架构换了，上面跑的 skill 也借机做了一轮重构。有些是 Cowork 时期根本做不了的新东西，有些是原来就有但一直受限于架构跑不顺的。 ^kp3-限于架构原因

### 3.1 Workflow State — 长流程终于跑得住了

Cowork 时期最怕的事就是 deep research 跑到一半 session 断了。现在每个多阶段 skill 都接了 workflow state 状态机：每个 phase 结束写 checkpoint，session 断了下次从上次的 checkpoint 恢复，结束时写 retrospective 归档到 GitHub。deep research 四个阶段（问题清单 → 数据登记 → 工作底稿 → 报告初稿）现在可以分三四个 session 跑完，中间该睡觉睡觉，第二天打开自动接上。

这个是 Cowork 时期怎么设计都绕不过去的问题——没有持久化层，你在 skill prompt 里写再多断点逻辑也只是 context 里的文字，session 一关就没了。

### 3.2 Data Validator — 数据血缘追踪 + 强制 QC

Cowork 时期 data-validator 是一个独立 skill，每次要手动触发。实际效果是：赶 deadline 的时候一定会忘。出过一次事故——IC deck 里一个 market size 数字来源是 web search 的二手引用，开会时被 challenge 来源，当场答不上来。

现在 data-validator 做了两件事。第一件是数据血缘登记：每个进入 deck 或模型的数字都要标注来源层级（A级是公司官方财报、Bloomberg 原始数据；B级是卖方报告、web search），标注时间戳和地域口径，记录下游依赖关系。第二件是通过 hooks 绑成 PreToolUse 自动触发——只要检测到在输出 PPTX 或 DOCX，自动跑一遍来源分级、时效性检查（数据是不是过期了）、数学交叉校验（revenue × margin 是不是等于 profit，各子项加总是不是等于 total）。跑完不通过的字段会被标红，强制你在交付前处理。

不需要我记得去跑，也不需要 AI 记得去跑。系统层面强制执行，漏不了。

### 3.3 LLM Sub-Agent — 火山方舟接入

这个 Cowork 里完全没有。原来所有中文任务都走 Claude，从轻量搬运（格式化、翻译、摘要）到重活（NLP打标、研报解读）全用同一个模型。

现在通过 llm-subagent skill 接了火山方舟三条线：豆包做轻量中文搬运（替代 Haiku 的中文短板），Kimi 做长文档（256K context，吃研报和财报），ASR 模式做调研录音转写。录音转写这条线改动最大——以前要先上传 NLM 再提问再导出，现在火山方舟 TOS 上传 + bigasr 直接出 transcript，5分钟搞定30分钟录音，transcript 直接喂给 Sonnet 主线程做结构化。visiting memo 的端到端时间砍了一半不止。

### 3.4 Morning Brief — 从串行排队到四路并行

Cowork 版的早报是我最早写的 skill 之一，也是最先撞墙的。四个 data fetcher（美国宏观、中国宏观、港股、加密货币）排队跑，一路 API 超时全部卡住。

迁移后改成四路 Haiku fork 并行拉数据，谁先回来谁先写入本地 JSON，最后 Sonnet 统一读取合成交易决策报告。早报从15-20分钟压到5-8分钟，最大的改善不是快了，是稳定了——一路失败不影响其他三路，失败的那路单独重试就行。

### 3.5 IC Memo — 拆成规划层 + 渲染层

Cowork 时期 IC memo 是一个大 skill 从头到尾，prompt 越写越长，改一个地方不知道会影响哪里。

现在拆成两个独立 skill：ic-memo-outliner 负责规划（研究、模式选择、storyline、逐页 slide 规划、数据底稿），输出 outline.md + data.xlsx；ic-pptx 负责渲染（读取 outline，按品牌母版规范生成 PPTX）。两层解耦以后，outline 可以反复改到满意再渲染，渲染层换模板也不影响规划层。

### 3.6 Earnings Review — 全链路编排

Cowork 里 earnings review 的三步（data fetch → transcript parse → memo write）需要我手动触发每一步。现在是一个 orchestrator 串起来：Haiku 子 agent 拉数据，Sonnet 解析 transcript，Sonnet 写 memo，phase 之间自动交接。我只需要在开头说"跑一下 XX 的财报点评"，中间出去泡杯咖啡，回来看成品。

### 3.7 社媒爬虫 — 从零开始

Cowork 时期完全没碰过社媒数据采集，sandbox 环境也跑不了。现在 mediacrawler-router 可以调度小红书、微博、B站、贴吧四个平台的爬虫，Cookie 复用，JSONL 输出，跑在 worktree 沙箱里不影响主 agent。配合消费医疗标的的用户舆情研究，从"拍脑袋判断用户情绪"变成了有数据支撑的分析。

### 3.8 Obsidian 知识沉淀 — NLM 管检索，Obsidian 管记忆

NLM（NotebookLM）在我的工作流里一直承担交叉语义检索的角色——上传十几份研报和财报，问一个跨文档的问题，它能从不同来源里把相关段落拎出来做交叉验证，这个能力很强。但 NLM 有一个根本性的短板：它不沉淀。每次查完就查完了，知识不会留下来，下次还是从零开始问。

Obsidian 补的就是这块。通过 onenote-obsidian-sync，调研笔记、专家访谈摘要、行业判断、公司跟踪的关键结论都会沉淀到 Obsidian vault 里，用双向链接串成网络。Claude 通过本地文件系统直接读取 vault 内容，不需要上传、不需要 API，天然就在 context 可达范围内。

实际效果是：NLM 负责"这份研报第几页说了什么"这类即时检索，Obsidian 负责"我们三个月前对这个行业的判断是什么、后来验证了没有"这类长期记忆。两层配合以后，Claude 对我的研究脉络的理解比 Cowork 时期深了一个量级——它不只是知道我现在在做什么，还知道我之前做过什么、为什么做、结论是什么。这是一个 AI 自己维护的知识库，用得越久越懂你。

## 四、迁移的代价

迁移不是免费的。

CLAUDE.md 写了一周。执行原则、数值原子性、编码规范、数据分级、skill 路由表、同步规范，从零到稳定迭代了十来个版本。写好了是长期资产，但前期投入不小。

12个 workflow orchestrator 重写，每个 skill 的 dispatch 逻辑要根据 Code 的 sub-agent 模型重新设计，不是复制粘贴，是架构层面重新想过。然后就是无休止的测试，debug，token 压力很大，只能在工作中遇到了再去跑迭代。

跨平台是持续成本。每次写新 skill 都要想 Mac 上能不能跑。pre-push hook 拦得住硬编码，但根源上是思维习惯要改。

## 结语

Cowork 更像一个聪明的实习生，你说什么他做什么，但你得一步步盯着。Code 更像一个 onboard 两周后的同事，知道你覆盖什么、上次做到哪、数据该从哪拉、出了错怎么降级、交付前跑哪些 QC。

77个 skill，38个日常在跑。三层 memory，hooks 自动化，sub-agent 并行，workflow state 断点续传。不是一开始规划好的东西，是每天干活时一个坑一个坑填出来的。CLAUDE.md 里每条规则背后都有一次具体的事故——GBK 崩溃、数字搬运出错的 IC deck、session 断开导致3小时 deep research 从头跑。事故变成规则，规则写进系统，系统自动执行。就这样。
