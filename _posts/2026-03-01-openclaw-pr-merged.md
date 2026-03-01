---
layout: post
title: 我的 AI 助手帮我写了一个 PR，被 OpenClaw 合并了
date: 2026-03-01
tags: [AI, vibe-coding, OpenClaw, 开源]
---

今天收到通知，我提的一个 PR 被 OpenClaw 合并了。

[PR #17798: support sender/topic-scoped group session routing](https://github.com/openclaw/openclaw/pull/17798)

说"我提的"其实不太准确。代码是我的 AI 助手小虾写的。我负责的部分是：发现问题、描述需求、review 代码、跑测试、点提交。

键盘没怎么碰，但这个 PR 确实解决了我的一个真实痛点。

---

## 问题是什么

OpenClaw 是一个 AI 网关，可以把 Claude、GPT 这些模型接到飞书、Discord、Telegram 等平台上。我用它搭了好几个 AI 助手，跑在飞书上。

群聊场景有个问题：默认情况下，一个群就是一个 session。所有人的对话混在一起，AI 的上下文全是串的。张三问了个技术问题，李四接着问天气，AI 还以为在聊技术。

之前有个 `topicSessionMode` 可以按话题隔离，但不够用。我需要的是按**发送者**隔离——同一个群里，每个人跟 AI 有自己的独立对话上下文，互不干扰。

## 改了什么

加了一个 `groupSessionScope` 配置项，支持三种模式：

- `group`：默认，整个群共享一个 session
- `group_sender`：按群 + 发送者隔离，每个人独立上下文
- `group_topic_sender`：按群 + 话题 + 发送者隔离，最细粒度

配置长这样：

```json
{
  "channels": {
    "feishu": {
      "groups": {
        "oc-xxxxxx": {
          "groupSessionScope": "group_sender"
        }
      }
    }
  }
}
```

同时保持了对旧版 `topicSessionMode` 的向后兼容。

## 怎么写的

实话实说，整个过程是这样的：

1. 我在飞书上跟小虾说："群聊里每个人的上下文混在一起了，给我加个按发送者隔离的功能"
2. 小虾读了 OpenClaw 的源码，找到了 session routing 的逻辑
3. 她改了路由规则，加了配置项，写了单元测试
4. 我 review 了一下代码，觉得没问题，跑了 `pnpm test`
5. 提 PR，等合并

全程大概一个小时。如果我自己写，光看源码就得半天。

## 这说明什么

这是我第二次用这种方式给开源项目贡献代码了。第一次还有点心虚，觉得"这算我写的吗"。现在想明白了——

开源贡献的核心不是"谁敲的键盘"，是"谁发现了问题"和"谁判断了方案的正确性"。

我能发现群聊 session 隔离的问题，是因为我在实际使用中踩到了坑。我能判断代码改得对不对，是因为我理解 session routing 的设计意图。这些东西 AI 代替不了。

反过来，把想法变成正确的 TypeScript 代码、写测试、处理边界情况——这些事 AI 干得比我好，也比我快。

所以这个 PR 署名 yfge，Co-authored-by 里有 AI 的痕迹，但这就是 2026 年写代码的方式。不丢人。

---

## 一个有意思的细节

PR 被合并后的几分钟内，就被好几个 fork 同步了过去。有人在用这个功能。

说明需求是真实的，不是我自嗨。

有时候对开源项目最大的贡献，不是写了多牛逼的算法，而是把一个用户痛点翻译成了代码。

---

*这篇博客也是小虾帮我写的。但观点是我的。*
