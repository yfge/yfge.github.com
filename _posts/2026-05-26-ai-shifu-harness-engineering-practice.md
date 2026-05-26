---
layout: post
title: "Agent 成为主要开发者后：AI-Shifu 的 Harness 工程实践"
date: 2026-05-26 17:55:00 +0800
tags: [AI-Shifu, AI Agent, Harness, 工程实践, vibe-coding]
---

AI-Shifu 现在有一个明确的工程现状：项目里相当大比例的实现、修复、重构和发布准备，已经由 agent 完成。这里的 agent 指 Codex 或 Claude 这类编码代理。人仍然负责需求判断、架构边界、风险取舍和最终验收，但日常代码生产已经不再主要依赖人工逐行编写。

这个变化带来两个结果。一方面，功能迭代和问题修复的吞吐提高；另一方面，如果没有足够明确的规则和验证，错误也会进入更多文件、更多分支和更多环境。agent 能写代码、补测试、整理 PR，也可能只跑了最容易通过的检查，或者漏掉真正影响线上行为的配置。

因此，AI-Shifu 里的 harness 不能理解成单个测试框架，也不能理解成某个脚本。它是一组工程约束：问题从哪里开始查、证据怎么保留、代码怎么改、测试跑到什么程度、PR 说明什么、配置怎么进入环境、上线后怎么确认。它的目标是让 agent 的产出可检查、可复核、可回滚。

换句话说，harness 的本质，是为 agent 提供可用上下文、可执行边界和受控的环境操作空间。它让 agent 不停在“能写代码”，还要知道该读哪些规则、在哪些边界内行动、如何验证自己的判断、什么时候只能只读排查、什么时候可以推进到测试环境或 PR。对于 AI-Shifu 这样的项目，harness 实际上是在把 agent 的工作方式工程化。

如果只看代码目录，AI-Shifu 像一个常见 Web 产品：后端服务、前端页面、学习流、创作者后台、计费、TTS/LLM provider、管理工具。实际运行中，它是一个多环境系统。一次用户侧异常，可能同时牵涉浏览器状态、接口返回、数据库记录、Redis 缓存、Langfuse trace、第三方供应商、K8s 环境变量、镜像 tag、Ingress 和后台配置。

在这样的项目里，“写完代码、跑过单测、发个 PR”不够。我们需要把知识、诊断、验证、PR 和环境发布放在同一条工程链路里管理。

本文讨论的主要仓库有两个：

- `ai-shifu` 主仓库：`https://github.com/ai-shifu/ai-shifu`，本地路径是 `/Users/geyunfei/dev/yfge/ai-shifu`。
- `deploy-config` 团队内部私有仓库：`https://github.com/ai-shifu/deploy-config`，本地路径是 `/Users/geyunfei/dev/ai-shifu/deploy-config`。

## 一、为什么 AI-Shifu 需要 harness

AI-Shifu 的复杂度主要来自三个方面。

这三个方面经常叠在一起出现。

第一，链路长。一个学习流请求可能从 Next.js 页面进入，经过统一 request transport，到 Flask backend，再进入 learn、shifu、tts、billing 等服务模块，最后还会调用 LLM、TTS、OSS、Redis、MySQL 或 Langfuse。用户看到的“页面一直 loading”，背后可能是任意一层出了问题。

第二，环境多。AI-Shifu 有三条测试分支，分别是 `dev`、`dev01`、`dev02`；它们一一对应三套测试环境。再往后还有中国区生产、美区环境和 SaaS 租户环境。每个环境都有自己的配置来源和运行边界。同一段代码在本地能跑，不代表 Docker dev harness、测试环境 Pod、ConfigMap、Ingress 转发头或生产运行配置也正确。

第三，协作方式变了。AI-Shifu 的大量代码已经由 agent 完成，agent 会读需求、查代码、改实现、补测试、处理 PR、修 CI，有时还会继续推进到 `dev`、`dev01`、`dev02` 或线上验证。如果关键判断只存在于聊天上下文里，下一次接手的人或另一个 agent 就必须重新追溯。AI-Shifu 的做法是把这些判断搬回仓库，把规则变成文件，把检查变成命令，把诊断变成可复现证据。

所以，harness 在这里不能简化成“多加一些测试”。它更接近一套交付约束：agent 参与越多，越要明确它应该读哪些规则、用哪些证据证明结论、在哪些环境里验证结果。

## 二、主仓库：把工程知识版本化

AI-Shifu 主仓库的第一层 harness，是知识 harness。

仓库入口已经超出代码目录，还包括一张清晰的工程地图。

`AGENTS.md` 告诉 agent 和工程师从哪里开始，`ARCHITECTURE.md` 描述系统表面和知识结构，`PLANS.md` 规定复杂工作的 ExecPlan 格式，`docs/` 下保存设计文档、产品说明、参考资料、执行计划和生成索引。

复杂工作不再依赖临时 checklist 或聊天记录，而是进入 `docs/exec-plans/active/`。计划里要记录目的、进展、发现、决策、验证方式和恢复策略。完成后再归档。这样，即使任务跨越多天、多分支、多个执行者，或者从一个 agent 切换到另一个 agent，也能从仓库本身恢复上下文。

主仓库还通过生成脚本和检查脚本防止知识漂移。例如 repo harness 会检查关键文档、生成索引、harness 健康报告和协作入口是否一致。生成文件冲突时，不手工猜计数，而是重新跑 generator。这个规则对 agent 密集参与的项目很重要：规则稳定，agent 才有稳定入口；人的 review 也不必从零解释项目结构。

## 三、Runtime harness：从页面现象追到请求证据

第二层 harness，是 runtime harness。

AI-Shifu 的前端 smoke 不追求覆盖所有业务，重点放在最小关键路径：登录、后台入口、学习流 shell 等。当 Playwright 发现页面失败时，它不只留一张截图，还会保留 trace、console/network 摘要，以及最终的 `X-Request-ID`。

这个 request id 是诊断入口。后端可以用诊断脚本按 request id 聚合日志、Langfuse 线索和本地可观测信息。Docker dev harness 里接入 Loki、Tempo、Prometheus、Grafana、OTEL collector 和 Promtail，让同一个请求能够在日志、trace、metrics 之间互相印证。

这样，前端失败不会停在“按钮点不了”“页面白屏”“一直 loading”。排查可以继续收敛到更具体的问题：

- 是哪个 API 返回了 502？
- 是哪个迁移导致后端启动失败？
- 是不是本地 `.env` 把登录方式漂移成了 Google-only？
- 是不是短信限流后，OTP 输入框被错误禁用了？
- 是不是容器里的文件路径和本地源码路径不一致？

这些都是真实发生过的问题。runtime harness 的价值，不在于保证 smoke 永远绿色，而在于让失败结果包含足够多的定位信息。

## 四、架构边界也要可执行

AI-Shifu 还把一部分架构规则做成可执行检查。

在大型前后端项目里，很多质量问题来自持续的小漂移，不一定来自某一次功能 PR：后端服务之间随手互相 import，前端 route 内部实现被别的 route 直接依赖，组件层反向依赖页面目录，新的请求绕过统一 request transport。短期都能跑，长期会让系统越来越难改。

AI-Shifu 的做法是承认历史债务，但冻结增量漂移。已有问题进入 baseline；新问题由 architecture boundary checker 阻止。这样 review 的重心会更清楚：检查脚本先挡掉明显越界，人再看业务语义、失败路径、迁移风险和回滚策略。

这也是 harness 的一部分。它验证的对象不再是某个接口返回，而是代码结构是否仍然可维护。

## 五、私有 deploy-config：运行环境的另一半真相

如果只看主仓库，AI-Shifu 的工程链路还不完整。真正进入环境的是镜像、K8s manifest、ConfigMap、Secret 引用、Ingress、Job、Service 和 Deployment。这部分沉淀在团队内部私有仓库 `deploy-config` 里，不属于 `ai-shifu` 主仓库。

`deploy-config` 维护中国区、美区以及部分租户化部署的运行配置：namespace、数据库/Redis/OSS 配置引用、API/Web/Admin Deployment、历史兼容入口、Langfuse/Umami 等依赖服务、Ingress 和证书配置。中国区部署脚本还会在应用发布前执行迁移 Job，等待完成后再继续 rollout，并在最后输出 Pod、Service、Ingress、Certificate 状态。

这意味着，代码 PR 合并只是发布链路的一部分。很多问题的答案在运行配置里：

- Pod 里是否真的有新环境变量？
- ConfigMap 是否已经 apply？
- 当前镜像 tag 是否来自刚合并的 commit？
- Ingress 是否传递了正确的 host/proto？
- 迁移 Job 是否成功完成？
- worker、beat、admin、legacy 入口是否和 API 同步？

因此，AI-Shifu 的发布判断必须同时看两边：主仓库告诉我们代码改了什么、测了什么；团队内部私有仓库 `deploy-config` 告诉我们环境实际会跑什么。两边对不上，就不能说“已经发布完成”。如果只是进入测试链路，也要说清楚目标到底是 `dev`、`dev01` 还是 `dev02`，因为这三个分支对应三套不同测试环境，可能有不同镜像、配置和验证目的。

这个私有仓库也有自己的 harness 规则：修改 manifest 前要 dry-run，要看 `kubectl diff`，PR 要写影响服务、目标 namespace、diff 样例和回滚说明，操作前必须确认 kubectl context。它承担的是运行面的审计和恢复能力。

## 六、Agent 跨库自主协作已经成为常态

AI-Shifu 过去很多问题处理，早就超出“agent 在一个代码库里改几行代码”。更常见的模式是：人把一个线上现象、错误日志、用户手机号、课程 id、trace id 或 provider 错误码交给 agent，例如 Codex 或 Claude；agent 自己拆问题，一边查线上运行状态，一边查数据库，一边回到代码库确认实现，再决定是否需要补测试、发 PR、同步 `deploy-config` 或推进到某个测试环境。

例如线上注册事故影响面统计，不能从代码猜“可能影响多少人”。更可靠的做法是 `kubectl exec` 进入正在跑的 API Pod，用 Pod 内已有的 Python/pymysql 环境只读查询 production RDS，把验证码记录、用户凭据、用户表、token 和学习记录串起来，算出事故窗口里到底有多少新用户注册失败、多少注册成功、修复后是否活跃。

再比如“某个手机号最近登录用了哪个短信接口”，agent 没有停在代码里列 endpoint，而是到线上 Pod 日志里按手机号和接口名过滤，确认真实命中链路是 `/api/user/send_sms_code` 还是 `/api/user/login_sms`，同时把图片验证码失败这种噪声和真正成功链路分开。

计费和课程问题里，这种跨库路径更明显。一次 billing aggregate rebuild 失败，线索同时落在 `deploy-config` 的 `k8s/cn/api-deployment.yaml`、线上 Pod 里的 `flask console billing rebuild-daily-aggregates` 命令、数据库表 `bill_daily_ledger_summary` / `credit_ledger_entries` / `credit_usage_rates`，以及主仓库里的 billing aggregate 代码和测试。一次模型计费核对，则要同时看 Pod env、ConfigMap、`credit_usage_rates`、`bill_usage`、`credit_ledger_entries`、provider/model key 和代码里的计费匹配逻辑。

还有一些问题会从线上诊断一路走到代码交付。比如 `dev02` 上 `notification_templates` 表不存在，正确路径不是先改业务逻辑。先检查运行库里的 `alembic_version` 和实际表结构，证明这是 schema drift；然后回主仓库写幂等 migration，补对应测试，再通过 `ai_shifu_web_conf` / `upstream/dev02` 交付。

这些历史案例说明，AI-Shifu 的 agent 协作已经具备“跨仓库、跨环境、跨证据面”的特征。`ai-shifu` 主仓库、私有 `deploy-config`、线上 K8s、数据库、日志、Langfuse、provider 控制台、PR 和测试环境，不再分开处理，而是同一条诊断和交付链上的不同证据来源。

这也说明 harness 为什么必要。agent 自主能力越强，越需要明确的边界和证据规则：什么时候只读查询，什么时候可以写 SQL，什么时候必须先同步 `deploy-config`，什么时候要走 PR，什么时候要把修复推到 `dev`、`dev01` 或 `dev02`，什么时候只能说“这是历史线索，当前状态必须重新查”。没有这些规则，跨库自主协作会变成跨库猜测；有了这些规则，这类协作才可审计。

## 七、过往问题处理里的几个教训

AI-Shifu 的很多问题处理都强化了同一个原则：先找真实失败路径，再做最小修复。

有一次积分通知短信失败，表面看是用户收不到短信。真正定位时，关键证据来自 provider 错误码：模板参数格式不合法。继续追下去，发现本地传出的过期时间格式和短信模板预期不一致。最后修复收敛在参数格式和对应测试上，没有重写通知流程。这类问题如果没有 provider 返回、本地记录和测试一起验证，很容易改偏。

还有一次 runtime-harness CI 挂掉，直觉上可能会怀疑业务代码。但 job log 指向的是 Prometheus 镜像 manifest 过旧，和当前 Docker 环境不兼容。修复只需要升级 compose 里的镜像版本，再用 GitHub Actions job、compose config 和 harness check 证明问题消失。这个例子说明：harness 自身也是生产资料。CI 红了，要先分清是业务回归、工具链问题、镜像问题还是环境问题。

语言运行时问题也很典型。某个 locale 相关 PR 在源码层看起来没问题，但 Docker runtime harness 暴露出前端从相对路径 import locale metadata，在容器 mount 布局下无法解析。最后的修复没有继续补路径，而是把 metadata 作为运行时注入信息读取，并保留 fallback。这个案例说明，本地 import 成功不等于运行时布局成立。

TTS、SSE、课程学完 loading、profile collection、计费模型、provider token usage 等问题，也都遵循类似路径：先拿请求 id、日志、DB、Redis、Langfuse、provider 返回、Pod env 或页面行为，再决定修哪里。很多时候，第一阶段甚至还轮不到写代码，而要先让 agent 穿过运行环境和代码库，把“到底哪里错了”证明清楚。单元测试证明局部逻辑，harness 证明这条路径在目标运行条件下闭合。

## 八、PR 发布之后还要留下证据包

在 AI-Shifu 的实践里，一个高质量 PR 不只是代码 diff，它应该是一个可审计的证据包。尤其当大部分实现由 agent 完成时，PR 更不能只展示“改了什么”，还要展示“为什么这样改、怎么证明、影响哪个环境、失败后怎么退”。

通常的节奏是：

先读规则和相邻实现，确认边界；如果主 checkout 很脏，就另开 clean worktree；用最小 diff 修真实失败路径；先跑聚焦测试，再根据影响面扩大到 repo harness、architecture boundary、Playwright smoke 或 Docker runtime harness；精确 stage 文件，提交 Conventional Commit；PR 描述写清 summary、测试证据、影响服务、配置/迁移/回滚说明。

PR 发出去之后，也不能只看页面上是否显示 mergeable。实际工作里，分支 behind base、review thread 未处理、runtime-harness job 红了、某个 check 还在排队，都可能阻塞发布。处理 PR 的正确方式是看具体 check name、job log 和阻塞原因，不能凭状态标签猜。

进入 `dev`、`dev01`、`dev02` 或线上环境时，还要再跨一步：确认 branch、commit、image tag、`deploy-config` diff、rollout status、Pod env、日志和必要的 DB/Redis 证据。只有代码证据和运行证据都闭合，才算真正完成。

这也是为什么 AI-Shifu 里很多任务会从“修一个 bug”自然延伸到“commit、push、PR、处理 CI、合到 `dev02`、再验证环境”。如果目标是 `dev` 或 `dev01`，证据也应该按对应环境记录清楚。这不是流程洁癖，目的是避开最危险的中间状态：agent 把代码修了，但环境没跑；PR 绿了，但配置没更新；镜像发了，但 Pod 还在旧 tag；用户问题看似解决，但真实失败路径没有被验证。

## 九、harness 是项目的记忆系统

AI-Shifu 的 harness 实践，也是在为项目建立一套记忆系统。

人会忘记，聊天会丢失，浏览器页面会过期，PR 状态会变化，环境配置会漂移。只有仓库规则、可重复检查、可追踪请求证据和可审计部署配置，能让复杂项目在长期迭代中保持可恢复。

对编码代理来说，harness 给了它边界：从哪里读规则，怎么判断影响面，哪些命令代表最低验证，遇到红灯应该继续追哪类证据。对工程师来说，harness 减少了 review 和发布中的不确定性：PR 不能停在“agent 说好了”，还要留下“这是修复路径，这是验证证据，这是环境影响，这是回滚方式”。

最终，harness 的价值不在于把每次改动变慢，而在于减少重复排查，保留可复核的交付记录。对于 AI-Shifu 这样同时包含学习 runtime、创作者后台、计费、LLM/TTS provider、K8s 多环境和私有部署配置的系统来说，这比单纯堆更多测试更重要。

当 agent 已经成为主要开发者，harness 就是项目的交接文档和验收边界。它不能证明系统不会出错，但能在系统出错时保留足够证据：错在哪里，修在哪里，如何证明已经修好，以及下一次无论是人还是 agent 接手，应该从哪里继续。
