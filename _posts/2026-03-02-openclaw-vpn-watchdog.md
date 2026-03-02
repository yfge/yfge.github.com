---
layout: post
title: "OpenClaw 断网自愈：我给 AI 助手写了个 VPN 看门狗"
tags: [OpenClaw, VPN, 自动化, Mac mini]
---

我的 Mac mini 上跑着三个 OpenClaw 实例。

它们帮我写知乎、管服务器、跑定时任务。

但有个致命的问题：VPN 一断，它们全瘫。

API 调不通，模型连不上，定时任务空转。

而 VPN 断连这件事，几乎每天都会发生。

---

## 问题到底有多烦

我用的是 Jamjams，一个 macOS 上的代理工具。

两组订阅，一共12台服务器。

正常情况下没毛病。

但服务器会抽风。有时候某台突然慢得不行，有时候直接不通。

Jamjams 自己不会切。它就死守着那台挂掉的服务器，等你手动去换。

白天还好，我看到了就切。

凌晨呢？我睡着了，OpenClaw 在跑盐选故事的定时任务，VPN 挂了，任务静默失败。第二天起来一看，什么都没跑。

这种事发生了不止一次。

---

## 为什么不用 OpenClaw 自己来检测

这是第一个直觉。

但想了两秒就否了。

OpenClaw 本身就依赖 VPN 才能调 API。VPN 断了，OpenClaw 也瘫了。

让一个瘫痪的病人给自己做手术，不现实。

所以这个看门狗必须是独立的。不依赖任何 AI，不消耗任何 token。

纯 shell 脚本，跑 macOS 的 LaunchAgent。

---

## 我怎么做的

整体逻辑很简单，三步：

**第一步：检测。**

每5分钟 curl 一下 Anthropic、OpenAI、Google 三个端点。任何一个通了，就算正常。

全不通，等3秒再试一次。排除瞬断。

**第二步：切换。**

确认断了，就改 Jamjams 的配置文件（macOS defaults），把 selectedServerId 换成下一台。

然后重启 Jamjams。

12台服务器轮着来。

**第三步：刷新。**

如果切了一台还不通，说明可能不是单台问题。

这时候脚本会主动拉订阅 URL，拿最新的服务器列表。

拉回来的是 base64 编码的 SS/VMess 链接。解析完写回配置，再切一台。

正常情况下，每小时自动刷新一次服务器列表。出故障时立即刷新。

---

## 技术细节（给想抄的人）

Jamjams 没有 CLI，没有 AppleScript 接口。

但它的配置存在 macOS 的 defaults 系统里，域名是 `net.fiberlogic.jamjams-standalone`。

关键字段：
- `groups` → JSON，里面有 `selectedServerId` 和 `subscriptions`
- `subscriptions` 里有每个订阅的 URL 和服务器列表

改法：
```bash
defaults export net.fiberlogic.jamjams-standalone - | python3 解析修改 | defaults import
```

改完之后 `open -a Jamjams` 重启生效。

部署用 LaunchAgent，丢到 `~/Library/LaunchAgents/`，每300秒跑一次。

日志写 `/tmp/vpn-watchdog.log`。

完事。

---

## 跑了之后的效果

部署当晚测了一次。

手动把 Jamjams 切到一台我知道不太行的服务器。

5分钟之内，脚本检测到断连，自动切到下一台，恢复。

日志里就三行：

```
Connectivity check FAILED, retrying...
Switching from 216D38FC.. to 3EA2209D..
Recovery SUCCESS after switch
```

从断到恢复，大概15秒。

而且整个过程零 AI 调用，零 token。

---

## 一个更大的认知

这件事让我重新想了一下"AI 自动化"这个概念。

很多人（包括我）一上来就想用 AI 解决所有问题。

但有些问题根本不需要 AI。

VPN 断了切服务器，这是一个确定性问题。输入确定，输出确定，中间没有任何需要"理解"或"判断"的环节。

用 AI 来做这件事，是浪费。

用 shell 脚本来做，更快、更稳、更省钱。

**AI 应该用在需要判断力的地方。不需要判断力的地方，写死逻辑就行。**

我现在给自己定了一个规矩：

> 在动手写 prompt 之前，先问一句：这件事需要 AI 吗？

如果答案是不需要，就老老实实写脚本。

---

脚本开源在我的 workspace 里。如果你也用 Jamjams 或者类似的代理工具，可以直接改 server ID 列表拿去用。

有问题评论区聊。
