---
layout: post
title: 把你的 AI 对话，变成可复盘、可分享的生产力
tags: AI vibe-coding Talkreplay
---

# TalkReplay：把你的 AI 对话，变成可复盘、可分享的生产力  
作者：**老拐瘦**（本拐）

> 本拐每天和 Claude、Codex 反复拉扯：写代码、踩坑、复盘、再重来。可惜这些高价值的对话碎片，总是散落在历史记录里。  
> **TalkReplay** 的目标很简单：把你的 AI 会话**记录 → 回放 → 总结 → 分享**，让灵感不再逃走，让复盘成为默认动作。


## TalkReplay 是什么？

**一句话**：把你与 **Claude / Codex** 的聊天记录，变成可检索、可回放、可导出的「对话时间线」。开箱即用，Docker 一键跑。

- **技术栈**：Next.js 14（App Router）· React · TypeScript · Tailwind CSS · shadcn/ui · Zustand · React Query  
- **适配来源**：Claude（`~/.claude/projects`）、Codex（`~/.codex/sessions`），支持示例数据（fixtures）快速体验  
- **定位**：开源的 **vibe coding** 标准范本：一边干，一边记录，一边沉淀


## 三个关键词：Record · Replay · Share

- **Record（记录）**：导入 Claude/Codex 的本地会话目录（或直接用内置示例数据），统一成结构化时间线  
- **Replay（回放）**：左侧列表 + 右侧详情的双栏视图，按关键词、日期、星标快速定位，一键回到某次「关键回合」  
- **Share（分享）**：把长对话提炼成摘要/纪要，导出为 Markdown/HTML（持续增强），用于文章、Issue 或项目文档


## 5 分钟上手（零依赖、Docker 一键）

```bash
# 1) 克隆
git clone https://github.com/yfge/TalkReplay
cd TalkReplay

# 2) 立即体验：用内置示例数据（fixtures）
CLAUDE_LOGS_PATH=./fixtures/claude CODEX_LOGS_PATH=./fixtures/codex APP_PORT=3000 docker compose up --build
```

> 默认访问：http://localhost:3000  
> 挂载真实目录时，建议加 `:ro` 只读参数，保证安全。

**使用你本地的真实会话目录（只读挂载更安心）**：

```bash
CLAUDE_LOGS_PATH="$HOME/.claude/projects" CODEX_LOGS_PATH="$HOME/.codex/sessions" APP_PORT=3000 docker compose up --build
```

**可选：纯前端导入**  
不想挂载？也可以在浏览器里选择文件/文件夹，快速演示 UI 与筛选能力（适合 Demo）。


## 主要功能（v1.0）

- **多 Provider 适配**：Claude / Codex，计划扩展更多来源  
- **搜索 / 过滤 / 星标**：关键词、日期范围、Starred only  
- **时间线回放**：双栏浏览，清晰复盘「思考 → 尝试 → 修正」  
- **只读挂载**：以最低风险读取你的会话数据  
- **示例数据**：`fixtures/` 内置结构，clone 即可看到效果


## 为什么要做 TalkReplay？

- **vibe coding 正火**：以对话为中心、快速试错，重在复盘与分享  
- **把过程变资产**：会话里充满 prompt、推理、折返与决策；把它们沉淀下来，才是可复用的生产力  
- **团队共享的基础**（规划中）：从个人沉淀，到组织级知识库与最佳实践库


## 设计哲学：让复盘成为「默认动作」

- **以「回合」为单位**：工具调用、关键修改、失败→成功，天然构成「高光片段」  
- **对话先于代码**：先把故事讲清楚，再把代码沉淀到仓库  
- **工程化的 vibe**：仓库内置 `agents_chat/`、`tasks.md`、Husky 质量闸，项目本身就是一份可复播的实践样本


## 路线图（节选）

- **1.x**：标签与书签、对比视图（同题多模型）、更强导出（Markdown/HTML）、长列表虚拟化  
- **Team / SaaS（私测）**：组织/成员/空间、权限与审计、组织级检索与分享  
- **可选持久化**：个人版保持零依赖；团队版引入后端数据库与多租户


## 安全与隐私

- 默认 **本地运行**，不上传任何会话数据  
- 推荐 **只读挂载** 你的日志目录（`:ro`）  
- 纯前端导入适合演示，真实使用优先走本地挂载


## 开源与参与

- **GitHub**：<https://github.com/yfge/TalkReplay>（欢迎 Star / Issue / PR）  
- **官网**：<https://talkreplay.com>  
- **愿景**：让 AI 对话变成「可复盘、可验证、可传播」的团队资产，而不是一次性的灵感烟花

## 附：常用命令速查

**本地开发：**
```bash
pnpm install
pnpm dev -- --port 3002

# 质量闸门
pnpm lint
pnpm test
pnpm build
```

**Docker 运行：**
```bash
# 直接 build + run
docker build -t talk-replay .
docker run   -p 3000:3000   -e NEXT_PUBLIC_CLAUDE_ROOT=/app/data/claude   -e NEXT_PUBLIC_CODEX_ROOT=/app/data/codex    -e CLAUDE_ROOT=/app/data/claude   -e CODEX_ROOT=/app/data/codex   -v "$HOME/.claude/projects":/app/data/claude:ro   -v "$HOME/.codex/sessions":/app/data/codex:ro   talk-replay
```

**docker-compose（推荐）：**
```bash
CLAUDE_LOGS_PATH="$HOME/.claude/projects" CODEX_LOGS_PATH="$HOME/.codex/sessions" APP_PORT=3000 docker compose up --build
```


## 结语

写代码可以靠感觉，但**生产力必须靠复盘**。  
**Talk → Replay → Grow.** 我们在 **talkreplay.com** 见。
