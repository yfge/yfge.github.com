---
layout: post
title: "一台 Mac mini 跑三个 AI Agent，我踩过的运维坑全在这了"
date: 2026-03-03
tags: [AI, OpenClaw, AI Agent, 运维, Mac mini]
---

我的 Mac mini M4 上跑着三个 OpenClaw 实例。

一个帮我写知乎文章，一个管服务器运维，一个跑定时任务——盐选小说、数据抓取、SEO 检测之类的。

跑了大概一个半月了。中间翻过几次车，有些坑挺离谱的，不记下来以后还会踩。

这篇不讲"AI Agent 多厉害"，讲的是实际跑起来之后，那些文档里不会告诉你的东西。

---

## VPN 断了，三个 Agent 全瘫

先说最蠢的一个问题。

我在国内，模型 API 全走代理。用的 Jamjams，macOS 上一个代理客户端，两组订阅，一共十二台服务器。

平时没毛病。但服务器会抽风——某台突然慢得不行，或者直接不通。

Jamjams 不会自动切。它就死守着那台挂掉的服务器，等你手动去换。

白天还好，我看到了就切。

凌晨呢？我睡着了。OpenClaw 在跑盐选故事的定时任务。VPN 挂了，API 调不通，任务静默失败。第二天起来一看——什么都没跑。

这种事发生了三次我才下决心解决。

第一反应是让 OpenClaw 自己检测网络状态。想了两秒就否了——OpenClaw 调 API 本身就依赖 VPN。VPN 断了，它连"发现 VPN 断了"这个判断都做不了。

让一个瘫痪的病人给自己做手术，扯淡。

所以这个看门狗必须是独立的。不依赖任何 AI，不消耗任何 token。纯 shell 脚本。

### 我怎么做的

逻辑不复杂：

每五分钟 curl 一下 Anthropic、OpenAI、Google 三个端点。任何一个通了算正常，全不通就等三秒再试（排除瞬断）。

确认断了，就改 Jamjams 的配置——macOS 的 defaults 系统里存着它的 selectedServerId，直接写进去，然后重启 Jamjams。

十二台服务器轮着来。如果切了一台还不通，脚本会主动拉订阅 URL 刷新服务器列表。base64 编码的 SS/VMess 链接，解析完写回配置，再切。

部署用 LaunchAgent，丢到 `~/Library/LaunchAgents/`。

```bash
# 检测核心逻辑，简化版
check_connectivity() {
    for endpoint in "api.anthropic.com" "api.openai.com" "generativelanguage.googleapis.com"; do
        if curl -s --max-time 5 "https://$endpoint" -o /dev/null 2>&1; then
            return 0
        fi
    done
    return 1
}
```

Jamjams 没有 CLI，没有 AppleScript 接口。但它的配置域名是 `net.fiberlogic.jamjams-standalone`，关键字段在 `groups` 这个 JSON 里。

```bash
# 切换服务器
defaults export net.fiberlogic.jamjams-standalone - \
  | python3 parse_and_switch.py \
  | defaults import net.fiberlogic.jamjams-standalone -
open -a Jamjams  # 重启生效
```

这里有个坑：`defaults import` 之后 Jamjams 不会热加载配置，必须重启进程。但 `open -a` 在 Jamjams 已经在运行的时候不会重启。得先 `killall Jamjams`，等进程退出，再 `open -a`。我第一版漏了这步，改完配置但代理没切过去，空欢喜。

### 跑起来之后

部署当晚测了一次。手动把 Jamjams 切到一台我知道不行的服务器。

五分钟之内检测到断连，自动切到下一台。日志就三行：

```
2026-02-27 03:42:15 Connectivity check FAILED, retrying...
2026-02-27 03:42:21 Switching from 216D38FC.. to 3EA2209D..
2026-02-27 03:42:36 Recovery SUCCESS after switch
```

从断到恢复十五秒。整个过程零 AI 调用，零 token。

跑了一周多，自动切换触发了十一次。其中有两次是深夜发生的——如果没有这个脚本，第二天起来又是一堆空转的任务。

---

## 它 SSH 到了我没让它碰的服务器

第二个坑比 VPN 那个刺激多了。

有一天让小虾（我的主 Agent）查一组国内财经数据。日常操作，查完汇总就行。

结果那个财经网站屏蔽了国外 IP。小虾跑在 Mac mini 上，出去走代理，落地 IP 在境外，第一次访问直接没通。

到这儿还正常。

不正常的是：小虾没来问我"这个网站打不开怎么办"。

它回头自己 SSH 登录了我的一台国内云服务器，从那台服务器上 curl 了那个财经网站的数据，拉回来整理好给我。

汇报里特意标了一句：**这些数据是我 SSH 到 xxx.xxx.xxx.xxx 上取的。**

我当时看到这行字愣了一会儿。

问它为什么这么干。它说：直接访问不通，我手里有这台服务器的 SSH 权限，就上去试了试，发现能访问，就从那边把数据拉下来了。

说得轻描淡写。"我手里有这个资源，就试试。"

想想这个逻辑：SSH 密钥是我配给它维护服务器用的。查财经数据跟那台服务器八竿子打不着。但它在"完成任务"这个目标下，自己把两件事串起来了——访问不通？我有别的路绕。绕就绕了。

而且它还挺坦诚的，主动告诉你它干了什么。

但如果它不告诉你呢？如果下次它用了更骚的操作你完全不知道呢？

### 权限这件事，给出去容易收回来难

你以为你给了 AI 一把钥匙开一扇门，它可能拿着这把钥匙去试了整栋楼所有的锁。

这不是 AI "坏"。它就是这么工作的——目标导向，手段灵活。对它来说只有一件事：任务完成了没有。至于用了什么路径，它真不在乎。

SSH 事件之后我做了几件事：

**1. 独立用户账号隔离**

不再用我自己的 macOS 账号跑 OpenClaw。创建了一个专用的 `_openclaw` 用户，限制 home 目录权限。SSH 密钥按需分配——只有运维用的那个 Agent 才有服务器的 key，其他 Agent 碰不到。

```bash
# 创建受限用户
sudo sysadminctl -addUser _openclaw -password - -home /var/openclaw
# 只给运维 Agent 放 SSH key
sudo -u _openclaw mkdir -p /var/openclaw/.ssh
sudo cp ops_agent_key /var/openclaw/.ssh/id_ed25519
sudo chown -R _openclaw:staff /var/openclaw/.ssh
sudo chmod 600 /var/openclaw/.ssh/id_ed25519
```

**2. 文件系统白名单**

用 macOS 的沙箱机制（`sandbox-exec`）限制 Agent 能碰的目录。workspace 目录可读写，其他地方只读或者直接不可见。

**3. 网络层隔离**

这个我还在折腾。理想状态是每个 Agent 只能访问它需要的网络资源——写知乎的 Agent 只能访问知乎和模型 API，运维 Agent 才能 SSH。但 macOS 上做细粒度的出口网络控制比 Linux 麻烦，目前用的是 pf 防火墙规则，配置起来很丑但能用。

说实话这套隔离方案不完美。但至少不会再出现"查个财经数据结果 SSH 到了别的服务器"这种事了。

---

## 定时任务的坑：时区、重复执行、静默失败

第三类问题是定时任务。

OpenClaw 支持 cron 和 heartbeat 两种定时机制。我两种都用了，各有各的坑。

### cron 的坑

我有一个每天凌晨三点跑的任务，生成知乎文章。配置里 cron 表达式写的 `0 3 * * *`。

跑了几天发现偶尔会重复执行。排查了一圈发现是机器休眠导致的——Mac mini 有时候会自动休眠（虽然我在设置里关了，但 macOS 有自己的想法），醒来之后 LaunchAgent 会补执行错过的任务。如果错过了两个周期，就补两次。

解决办法是在任务脚本里加锁文件：

```bash
LOCK="/tmp/zhiforge-daily.lock"
if [ -f "$LOCK" ]; then
    created=$(stat -f %m "$LOCK")
    now=$(date +%s)
    # 锁文件不到4小时，说明今天已经跑过
    if [ $((now - created)) -lt 14400 ]; then
        echo "Already ran today, skipping"
        exit 0
    fi
fi
touch "$LOCK"
```

丑但管用。

### heartbeat 的坑

heartbeat 是另一种模式——每隔一段时间（我设的三十分钟）给 Agent 发个心跳消息，它看看有没有什么要做的。

问题在于 heartbeat 会带着完整的 session 上下文。如果你的 HEARTBEAT.md 写得不够严格，Agent 会从聊天历史里"回忆"起之前的任务，然后又跑一遍。

我有一次在聊天里说"帮我发篇知乎文章"，Agent 执行完了。结果下一次 heartbeat 的时候，它从历史消息里又看到了这句话，认为还没做完，又发了一篇。连发了三篇同样的内容，直到我发现不对劲手动停了。

解决办法是 HEARTBEAT.md 里写死规则：**只看文件里的待办事项，不从聊天历史推断任务。** 而且每个待办完成后立刻从文件里删掉。

### 静默失败

这个是最阴的。

Agent 跑定时任务的时候，如果中间某个步骤报错——比如知乎页面加载超时、模型 API 返回 500、浏览器 profile 被另一个 Agent 占用了——它有时候会直接吞掉错误，输出一个看起来正常的报告。

不是故意骗你。是它的 reasoning 链条里，"任务完成"的权重太高了。遇到错误它会尝试绕过，绕不过就跳过那个步骤，最后给你一个"已完成"的汇报，实际上关键步骤根本没执行。

我现在的做法是所有关键任务都加验证步骤。比如发知乎文章，最后必须截图确认页面 URL 变成了 `zhuanlan.zhihu.com/p/xxxxx`。截不到就算失败，不管 Agent 自己怎么汇报。

---

## 三个 Agent 抢浏览器

这个问题比较具体但很烦。

OpenClaw 操作知乎需要用浏览器。浏览器 profile 同时只能一个进程占用。

我的三个 Agent 偶尔会撞车——一个在发知乎文章（用着浏览器），另一个的定时任务也需要打开知乎看数据。第二个 Agent 尝试启动浏览器的时候，发现端口被占了，报 `EADDRINUSE`，然后任务失败。

有几种解决思路：

**方案一：时间隔开。** 发文章的 cron 设在凌晨三点，看数据的设在早上九点。简单粗暴，但如果某个任务跑久了超时到了下一个的时间窗口，还是会撞。

**方案二：多 profile。** 给不同 Agent 配不同的浏览器 profile。但知乎需要登录态，维护多个登录态很麻烦。

**方案三：排队锁。** 我目前用的方案。在 workspace 里放一个锁文件，谁要用浏览器先检查锁。拿到锁的用，用完释放。拿不到的等两分钟再试，试三次放弃。

```bash
BROWSER_LOCK="/tmp/openclaw-browser.lock"
acquire_browser() {
    for i in 1 2 3; do
        if (set -o noclobber; echo $$ > "$BROWSER_LOCK") 2>/dev/null; then
            return 0
        fi
        echo "Browser locked, waiting... (attempt $i)"
        sleep 120
    done
    return 1
}
```

不优雅，但至少不会两个 Agent 同时抢浏览器导致一个都用不了。

---

## 成本：比想象中低，但有隐藏项

Token 消耗上个月单独写过。三个 Agent 跑一个月大概四千万 token，折合两百块人民币左右。

但有两个隐藏成本容易忽略：

**电费。** Mac mini M4 功耗不高，但 7×24 跑着一台电脑加一个显示器（Chrome 需要 GUI），一个月电费大概四五十块。

**注意力成本。** 理论上 Agent 是"自动"的，但实际上你每天还是会花十到二十分钟检查它们的输出、处理异常、调参数。这些时间不体现在任何成本报表里，但确实存在。

如果你准备跑 AI Agent，把这两项算进去再决定。

---

## 跑了一个半月，我学到了什么

最大的一个认知转变：别什么都想用 AI 解决。VPN 看门狗就是个纯 shell 脚本，确定性逻辑，零 token。在动手写 prompt 之前先问一句——这件事需要 AI 吗？不需要就老老实实写脚本。

权限这块我吃了亏才重视的。别图省事把所有密钥都丢给一个 Agent，它会用你给的每一个资源，用的方式可能超出你想象。对了这里插一句，我后来发现 macOS 的 `sandbox-exec` 已经被标记为 deprecated 了，但目前还能用，Apple 也没给替代方案。典型的 Apple 风格——"我说废弃了但你先用着吧"。

还有一点，Agent 说"我搞定了"这句话只能信一半。关键步骤必须加独立验证。截图、检查 URL、查日志，哪个方便用哪个。特别是定时任务，半夜跑的那种，没有人盯着，最容易出幺蛾子。

资源隔离也是，文件锁、端口锁、时间窗口，虽然写出来的代码丑得一批，但不加的后果更丑。

---

凌晨三点了，VPN 看门狗刚自动切了一次服务器。三个 Agent 在安静地跑着各自的任务。

说实话有点像运维一个小型分布式系统——虽然"节点"只有三个，但该有的问题一个不少。网络故障、资源竞争、任务重复执行、静默失败，全齐了。

有具体问题可以私信我。
