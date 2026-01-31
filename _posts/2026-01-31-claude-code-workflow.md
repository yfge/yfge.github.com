---
layout: post
title: Claude Code 开发工作流：一套可复用的实战框架
tags: [AI, vibe-coding, Claude Code, 工作流]
---

# Claude Code 开发工作流：一套可复用的实战框架

先说结论：**Claude Code 的工作流核心不是提示词，而是"可控交付"——每一步都能验收、每一步都能回退。**

我用 Claude Code 做了几个完整项目（包括开源的 [Orion 通知网关](https://github.com/yfge/orion)、[ZhiForge 自动化工具](https://github.com/yfge/zhiforge)），总结了一套经过验证的工作流程。

这篇是九阳神功系列的"速查版"——如果你没时间看完整系列，照这篇做就够用。

---

## 核心理念：AI 是施工队，你是总工+质检员

Claude Code 写代码很快，但最大的坑不是"不会写"，而是：

- 写得太快
- 改得太多
- 炸了没后路
- 炸完你不知道它到底改了哪些文件

所以工作流的第一要务是：**给自己装刹车系统**。

---

## 第一步：Git 刹车系统（必备）

> 详见：[vibe-coding 九阳神功之夯：Git 基础操作](/2026/01/27/git/)

每次让 Claude Code 动手前，先确保这套流程：

### 1）AI 改完先看它改了什么

```bash
git status
git diff
```

关键是看两件事：
- 它改了哪些文件（有没有越界）
- 改动范围是否合理

### 2）小步提交，多打存档

```bash
git add .
git commit -m "feat: xxx"
```

### 3）大改之前先开分支

```bash
git switch -c feature/xxx
```

写崩了？回主线 + 删分支：

```bash
git switch main
git branch -D feature/xxx
```

主线干干净净，心态也干干净净。

---

## 第二步：项目规矩文件（让 AI 有章可循）

Claude Code 会读取项目根目录的规矩文件。我建议至少准备：

**CLAUDE.md**（或 .CLAUDE.md）

```markdown
# 项目说明

## 技术栈
- 后端：FastAPI + SQLAlchemy
- 前端：Next.js
- 部署：Docker Compose

## 目录结构
- backend/：后端代码
- frontend/：前端代码
- docker/：Docker 配置

## 开发规范
- 提交前必须 git diff 检查
- 每个功能开分支开发
- 接口变更必须更新文档
```

这不是形式主义，是给 AI 画边界。

---

## 第三步：任务清单驱动（tasks.md）

不要让 Claude Code 自由发挥。给它一个 `tasks.md`：

```markdown
## TODO

- [ ] 实现 /api/users 接口
- [ ] 添加用户注册表单
- [ ] 配置 Docker Compose

## 完成

- [x] 初始化项目结构
- [x] 配置数据库连接
```

每次对话开始，让它先看 tasks.md，按清单推进。

---

## 第四步：可审计协作（agents_chat/）

> 详见：[AI 辅助完成的开源工程范本——Orion 项目背后的 vibe coding 实践](/2025/09/27/orion-vibe-coding-detailed/)

这是我从 Orion 项目总结的经验：**把每次协作过程记录下来**。

目录结构：

```
agents_chat/
└── 2026/
    └── 01/
        └── 31/
            └── 2026-01-31T14-30-00Z-add-user-api.md
```

每条记录包含：

```markdown
---
date: 2026-01-31
models: [claude-opus-4-5]
tags: [backend, api]
---

## 需求
实现用户注册接口

## 做了什么
- 新增 backend/api/users.py
- 更新 backend/main.py 路由

## 验收
curl -X POST http://localhost:8080/api/users -d '{"name":"test"}'

## TODO
- 添加参数校验
```

这样做的好处：过程可追溯、可学习、可复盘。

---

## 第五步：验收驱动（最关键）

**AI 说"应该可以"不算，必须给命令/证据。**

每次让 Claude Code 做完一个功能，立刻验收：

```bash
# 验收后端
curl http://localhost:8080/api/hello

# 验收前端
# 浏览器打开 http://localhost:8080

# 验收数据库
docker compose exec db mysql -u root -p

# 验收容器状态
docker compose ps
```

养成习惯：**不验收，不提交；不提交，不下一步**。

---

## 我的标准工作流（每天都用）

```
1. 打开项目，git status 看状态
2. 看 tasks.md，确定今天要做什么
3. 开分支：git switch -c feature/xxx
4. 让 Claude Code 开始干活
5. 每改一块：git diff → 确认 → git commit
6. 完成后验收（curl/浏览器/日志）
7. 验收通过：合并回 main，更新 tasks.md
8. 写 agents_chat 日志（可选但推荐）
```

---

## 进阶：多模型交叉验证

Claude Code 可能会幻觉。我的做法是：

- 让 Claude 先写
- 用 GPT-4 或 Gemini 审一遍
- 特别是涉及安全、性能的代码

专治"AI 自信满满但其实错了"的情况。

---

## 工具推荐

- **Git**：刹车系统，必装
- **Docker Desktop**：一键起环境
- **Chrome MCP**：自动化测试（让 Claude Code 操作浏览器验收）

技术栈选择：

- 后端推荐 FastAPI（简单、文档好）
- 前端推荐 Next.js（生态成熟）
- 部署推荐 Docker Compose（一键启动）

---

## 相关文章

这篇是"速查版"，完整内容见九阳神功系列：

- [夯：Git 基础操作，AI 时代的刹车系统](/2026/01/27/git/)
- [抄：直接拿优秀项目当蓝本，抄出你的初始系统](/2026/01/28/抄/)
- [学：先问架构拿术语，再用术语组装新项目](/2026/01/30/学/)

---

## 总结

Claude Code 工作流的核心就三句话：

1. **先装刹车（Git）**：随时能看改动、随时能回退
2. **画好边界（规矩文件）**：让 AI 知道能干什么、不能干什么
3. **验收驱动**：不是"能跑"就行，是"能证明跑对了"才行

有了这套工作流，Claude Code 就从"不定时炸弹"变成"可控的效率倍增器"。

---

{%- include about.md -%}
