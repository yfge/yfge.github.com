---
layout: post
title: "我从不相信现成 SKILL，到整理出 Agent Harness Skills"
date: 2026-05-28 20:00:00 +0800
tags: [AI Agent, Harness, Skill, 工程实践, vibe-coding]
---

我一开始是不相信现成 SKILL 的。

更准确地说，我不是不相信 agent，也不是不相信 skill 这个形式。

我是不太相信各种开源 SKILL。

因为在我原来的理解里，SKILL 本质上是个人工作流程和经验沉淀。我的项目、我的环境、我的踩坑、我的命令习惯，写成 `SKILL.md` 当然有用。但那更像是给自己用的工作手册。

别人的开源 SKILL，我以前基本不 care。

不是傲慢，而是觉得“这东西离开原作者的上下文，很难真正可用”。真实项目不是 demo。agent 进仓库后，先遇到的是一堆事实：哪个文档可信，哪个目录不能乱 import，哪些检查有效，目标环境是哪套，日志和 trace 怎么查，PR 里应该写什么。

这些东西如果都靠 agent 临场猜，模型越强，错起来越快。

直到我看到 [obra/superpowers](https://github.com/obra/superpowers)。

Superpowers 让我改观的地方，不是它里面每个 skill 都“神”。真正有意思的是，它把靠谱工程师会反复提醒自己的动作，拆成了可组合的 skills：先问清楚要做什么，再写计划；调试时先追事实，不急着猜；实现时用小步验证；完成前必须拿新鲜证据证明。

这就不是“别人的 prompt 模板”了。它更像是在说：工程经验可以从个人习惯里拆出来，变成 agent 能调用、别人能阅读和修改的东西。

我又去看了它的 [issues](https://github.com/obra/superpowers/issues)。里面有两个问题给我印象很深：一个是在说 [Codex 是 skills-only，不是 slash commands](https://github.com/obra/superpowers/issues/1630)；另一个是早期有人遇到[文件在磁盘上，但 Codex 里没有可用 skills](https://github.com/obra/superpowers/issues/274)。

这两个问题表面看是安装和适配，实际上说明：如果 skill 要成为可分享的工程资产，它不能只是一个文件。它得被 runtime 发现，被正确路由，并能在真实仓库里指导下一步动作。

我也是从这个点开始，慢慢意识到：我自己在几个项目里积累的那些规则、边界、验证方式和交付习惯，也许不只是“个人工作流”，而是真的可以被沉淀和分享。

## 从项目实践到 Agent Harness Skills

前面我写过一篇 [AI-Shifu 的 Harness 工程实践](/2026/05/26/ai-shifu-harness-engineering-practice.html)。那篇文章讲的是一个具体项目：AI-Shifu 里 agent 写了很多代码之后，我们怎么把规则、验证、运行证据、PR 和环境确认串起来。

但 AI-Shifu 只是一个样本。Superpowers 已经把“agent 如何做软件开发”这件事讲得比较完整了，我想补的是另一个角度：真实仓库本身，要准备什么，agent 才不至于每次都从头猜。

后来的整理不是从某一个项目复制出来的，而是从多个真实项目的实践里整体沉淀出来的。项目形态差很多：Web 产品、视频生产链路、实验室系统、agent 工作台、内容自动化工具都有。但 agent 在里面犯的错很像。

它会读错入口，把 README 当成事实源，真正的 `AGENTS.md` 或架构文档反而没看。它会跑错验证，改一段文档去跑最重的端到端检查，改运行链路却停在单测通过。它会越过边界，前端随手 import 另一个 route 的内部实现，后端绕过统一入口。

更常见的是证据不够。页面失败，只说“看起来不对”；接口失败，没有 request id；外部供应商失败，被写成产品质量失败；PR 里只有“已修复”，没有验证路径。还有一种更麻烦：它会把某个私有项目里的路径、环境、账号、部署约定、内部 URL 原样搬出来。那些东西在原项目里是事实，放进公开 skill 里就是污染。

这些问题不是靠一句“你要小心”能解决的。它们要变成仓库里的规矩、入口和检查。

于是我整理出了 [yfge/agent-harness-skills](https://github.com/yfge/agent-harness-skills)。它不是要替代 Superpowers，而是一个工程上的补充：Superpowers 更像 agent 的工作方法，Agent Harness Skills 更关注仓库这一侧的工程条件。

## 它不是脚手架，也不是 test harness

Agent Harness Skills 不是业务脚手架。

它不会告诉你怎么创建一个 SaaS、一个后台、一个视频平台、一个实验室系统。

它也不是 test harness。测试当然重要，但在真实项目里，测试只是验证的一部分。你还要知道架构边界有没有被破坏，运行证据能不能查，配置有没有进环境，PR 记录能不能被人复核。

我给它起了一个比较工程化的说法：repo-side control layer。说白了，就是仓库外层的控制面。

它要回答的不是“这个业务怎么写”，而是“agent 进来以后该怎么工作”：先读哪里，信哪个文件，哪些边界不能越过，改完跑什么，失败时留什么证据。

这些东西过去通常在资深工程师脑子里，或者散在聊天记录、临时 runbook、CI job、README 里。人可以靠经验补全，agent 不行。它需要明确入口、边界和能跑的检查。

所以这组 skills 不是为了增加流程感，而是为了减少猜测。

## 这组 skills 到底管什么

现在这个仓库里有九个 skills。我没有把它们写成大而全的方法论，而是拆成几个具体问题。

比如 `repo-harness-assessment` 是先看这个仓库到底缺什么，不是一上来就大改。`agent-entrypoint-design` 解决入口问题：`AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、Cursor rules、GitHub instructions，谁是事实源，谁只是镜像，不能互相打架。

`design-doc-and-task-board` 管需求、设计、任务状态和 exec plan。`repo-contracts-and-boundaries` 管架构边界和历史债务：老问题可以进 baseline，新漂移不能继续放进来。

`validation-harness-design` 管验证分层：文档、边界、逻辑、运行链路改动，不应该都用同一把尺子。`runtime-evidence-and-tracing` 管运行证据：run id、request id、日志、trace、截图、artifact，要能串起来。

`agent-ledger-and-delivery` 管交付记录，避免最后只剩一句“done”。`quality-gardening` 管长期质量漂移，用指标和阈值一点点收敛。`atomic-commit-discipline` 管提交，避免 agent 把不相干的改动混到一起。

这些东西合起来，才像一个仓库给 agent 准备的工作台。

## 真正沉淀下来的几条判断

第一，先让 agent 找到事实源，再让它改代码。

这句话听起来很普通，但很重要。`AGENTS.md` 不应该写成项目百科全书。它更像一个指示牌：先去哪，看哪个文件，遇到不同目录按什么规则走。

第二，先冻结新漂移，再慢慢还历史债。

很多项目一开始加架构检查都会红，因为历史问题太多。不要幻想一次清零。更现实的做法是 baseline：老问题先承认，从今天开始不让新问题再进来。

第三，验证不是跑最多命令，而是跑能证明这次改动的命令。

改 Markdown 不需要启动整个 runtime；改请求链路，只跑静态检查肯定不够。跑不了完整验证，也要把原因写清楚，不能把降级验证说成完整验证。

第四，运行证据要连接起来。

真实事故不会按照单测的形状出现。用户看到的是页面 loading、短信收不到、视频没生成、账单不对。你要能从现象追到 request id、日志、trace、截图、provider 返回和相关 artifact。否则 agent 很容易在代码里猜一个看似合理的修复。

第五，task、commit、review 要能互相追。

agent 写完代码之后，不能只留下“已完成”。任务状态要跟完成它的 commit 对得上，PR 说明要写清楚验证命令和结果，review 的人要能复核。

第六，私有经验可以当原料，但不能原样进 public skill。

我可以从很多真实项目里总结经验，但写进 `agent-harness-skills` 时，只保留可复用的角色、artifact、检查方式和失败模式。私有路径、账号、host、客户数据、部署假设，都不能带进去。

## 未来的 agent-ready repository

很多人讨论 agent 编程，还是习惯把焦点放在模型能力上：哪个模型更会写代码，哪个模型上下文更长，哪个工具调用更强。

这些当然重要。

但我现在更关心的是另一件事：仓库本身是不是适合 agent 操作。

一个不适合 agent 的仓库，会让它反复猜事实源、边界、验证、环境和交付标准。模型越强，猜错时扩散越快。

一个 agent-ready repository，不是装一个更聪明的 agent 就够了。它要把入口、边界、验证、证据、任务状态和交付记录都整理出来，让 agent 能读，也让人能审。

这就是我从不相信现成 SKILL，到整理出 Agent Harness Skills 的过程。

我不是突然相信了某个 prompt 模板。我只是被真实项目反复教育之后，接受了一个更朴素的结论：如果 agent 要长期参与开发，仓库就不能只为人类记忆而设计。过去靠资深工程师口口相传的规则，要变成 agent 能读、能执行、也能被人审计的东西。

Skill 的价值就在这里。它不是魔法，它只是把工程约束写下来。约束足够清楚，agent 才不只是一个会写代码的工具，而是一个能在真实仓库里稳定工作的参与者。
