---
layout: post
title: 从**DALL-E 3**接入ChatGPT说起
tags: DAL—E-3 大模型 提示工程 全栈 ChatGPT 
---

# 从DAL-E-3接入ChatGPT说起

## 缘起

上一个周五，我知道了ChatGPT接入了openai最新的文生图模型**DALL-E 3**，想了一下，不就是**Functional Calling**么，于是试了一下，结果发现，没那么简单……


## 小试一下

我先登录**ChatGPT**的网页版，选择了GPT4模型，在官方列表里选择了**DALL-E 3**：

![img](/assets/png/20231012/Screenshot%202023-10-14%20at%2016.31.53.png)

之后我让它画个清明上河图,回复是这个样子:

![img](/assets/png/20231012/Screenshot%202023-10-14%20at%2016.35.18.png)

这个效果有点好啊，我点开了一个图片，看到了这：

![img](/assets/png/20231012/Screenshot%202023-10-14%20at%2016.36.01.png)


我又点开了下一张，看到了这：

![img](/assets/png/20231012/Screenshot%202023-10-14%20at%2016.36.15.png)


所以，DALL-E 3 不是简单的以Functional Calling的形式的接入GPT，在调用之前，会让GPT对用户的**提示词** (即**Prompts**)做一下优化，这种用**文生文模型去生成文生图模型的提示词**，真的把**提示工程**灵活运用的不要不要的。直接打开了新世界！

小试结果有点好，于是我想……

## 为难一下

清明上河图，是个AI就懂吧，没难度，直接应用到工作里试一下，**为难一下GPT**，于是我还是**启用GPT4 的DALL-E 3的插件**，向GPT提问：

> 设计一个聊天软件的UI，运行在I OS上

GPT给我的回复是这个样子：

![img](/assets/png/20231012/Screenshot%202023-10-14%20at%2016.37.08.png)






>为了为您设计一个iOS上的聊天软件UI，我将首先描述四种不同的聊天界面设计方案。然后，我会为您生成这些设计的可视化图像。
>
>1. **经典泡泡风格**:
>界面采用了经典的泡泡风格对话框，用户的消息显示为蓝色泡泡，而其他用户的消息显示为灰色泡泡。底部有一个输入框，旁边是一个发送按钮。顶部是联系人的名称和头像，以及一个视频通话图标。
>
>2. **扁平化风格**:
>界面采用扁平化设计，无阴影和3D效果。消息呈线性排列，带有用户头像和时间戳。底部有一个带有附加功能图标（如图片、语音、表情等）的输入框。
>3. **暗黑模式**:
>聊天界面采用深色背景，配以淡色文字。消息泡泡采用半透明效果，为用户提供舒适的夜间阅读体验。输入框和功能图标均采用亮色突出显示。
>4. **极简风格**:
>界面尽量简洁，移除所有多余的图标和按钮。消息直接呈线性排列，只显示文本，无头像和时间戳。底部输入框简洁，只有一个发送按钮。
>
>现在，我会为您生成上述描述的聊天软件UI设计的可视化图像。


>这是四种不同风格的iOS聊天软件UI设计。您可以根据您的需求和喜好选择其中的一个或提供进一步的反馈。如果您有任何其他要求或建议，请告诉我！


生成的图片：

![img](/assets/png/20231012/Screenshot%202023-10-14%20at%2016.37.34.png)


我点了开一张效果图，还是一样，提示词是优化过了的：

![img](/assets/png/20231012/Screenshot%202023-10-14%20at%2016.44.48.png)

所以我接着为难一下GPT，你不是文生图，还能图生文么，咱们刚刚试了文生图，你再试一下图生文吧。

于是，我接着向GPT提问：

> 针对第一个图给出SwiftUI 的代码



GPT给我的回复是这个样子:

![img](/assets/png/20231012/Screenshot%202023-10-14%20at%2016.37.47.png)



> 为了创建一个类似于第一张图的iOS聊天界面，您可以使用以下的基本SwiftUI代码作为起点。请注意，这只是一个简化的示例，您可能需要根据您的实际需求进行适当的调整。
>
> ```swift
>import SwiftUI
> 
> struct ChatView: View {
>     @State private var messageText: String = ""
>     
>     var body: some View {
>         VStack {
>             // Contact Info at the top
>             HStack {
>                 Image("contact_avatar") // Replace with your image name
>                     .resizable()
>                     .scaledToFit()
>                     .frame(width: 50, height: 50)
>                     .clipShape(Circle())
>                 
>                 Text("Contact Name")
>                     .font(.title)
>                 
>                 Spacer()
>                 
>                 Image(systemName: "video")
>                     .resizable()
>                     .scaledToFit()
>                     .frame(width: 30, height: 30)
>             }
>             .padding()
>             
>             // Messages List
>             ScrollView {
>                 VStack(spacing: 15) {
>                     ForEach(0..<10, id: \.self) { _ in
>                         MessageBubble(isSender: Bool.random()) // Randomly picking sender for demonstration
>                     }
>                 }
>             }
>             
>             // Input Field at the bottom
>             HStack {
>                 TextField("Type a message...", text: $messageText)
>                     .padding()
>                     .background(Color.gray.opacity(0.1))
>                     .cornerRadius(20)
>                 
>                 Button(action: {
>                     // Send the message
>                 }) {
>                     Image(systemName: "arrow.right.circle.fill")
>                         .resizable()
>                         .scaledToFit()
>                         .frame(width: 30, height: 30)
>                 }
>             }
>             .padding()
>         }
>     }
> }
> 
> struct MessageBubble: View {
>     var isSender: Bool
>     
>     var body: some View {
>         HStack {
>             if isSender {
>                 Spacer()
>                 Text("Sender Message")
>                     .padding()
>                     .background(Color.blue)
>                     .foregroundColor(.white)
>                     .cornerRadius(20)
>             } else {
>                 Text("Receiver Message")
>                     .padding()
>                     .background(Color.gray)
>                     .foregroundColor(.white)
>                     .cornerRadius(20)
>                 Spacer()
>             }
>         }
>         .padding(.horizontal)
>     }
> }
> 
> struct ChatView_Previews: PreviewProvider {
>     static var previews: some View {
>         ChatView()
>     }
> }
> 
> 


本着**抬杠到底**的态度，我新建了一个iOS工程，直接建立一个**Swift UI**的文件，然后把GPT给我的代码**原封不动**的贴了过去:

结果，我看到了这个预览界面:


 ![img](/assets/png/20231012/Screenshot%202023-10-14%20at%2016.46.32.png)



我的第一反应是:
有了这个界面(或是说，这一套方法)以后，再结合**Github Copilot**和**ChatGPT**，**我应该可以自己写一个iOS的App，虽然，我并不会Swift !!!**



我给自己点了一杯咖啡，又定了一箱啤酒，**又C又A**的让自己**静静**



于是我……


## 思考一下

脑子里有两个问题:

1. 为什么可以达到这种效果？
2. 是不是所有人使用GPT都可以达到这样的效果？


针对第个问题，我们知道，GPT-4V本身是一个图生文的模型，但是在加入DALL-E 3 的基础上，可以实现文生图-图生文的一系列转换，在这些链路通了的基础上，ChatGPT便展现出了更令人惊叹的能力。



针对第二个问题，本拐有更深的一层感悟，作为一个程序员，我的技术栈是比较杂的，并不像一些行业内的专家，在一个领域深耕很多年，从工作到现在，光编程语言就使用过`C#`,`Java`,`PHP`,`Golang`,`Openresty(Lua)`,`Node.js(JavaScripts)` 等一大堆，可以说**样样通**，**样样松**，这些复杂的经历一度让我感觉很困惑，因为在找工作时的确遇到过一些麻烦，但是，在**ChatGPT**出现以后，一切都变了，因为这种复杂的知识系统借助AI的能力让我处理每一件工作都得以应手，我也不再为自己一是一个东北乱炖一样的程序员的感到自卑，在AI时代,对AI应用的能力取决于自己的判断力，即：

```python
生产效率提升 = 使用者判断力/使用者生产力
能力发挥 = min(模型能力, 使用者判断力)
```

这个公式并不是本拐的原创，而是**孙志岗**老师提出的，作为一位在教育领域深耕多年的计算机专家，他对AI有着深刻的思考和洞见，但他始终认为自己本职还是一名Coder，在**ChatGPT**出现以后，更是打造出了**ChatALL**这种全网火爆的开源产品，而在最近，他又重拾本行，教起了**大模型全栈工程师**课程，作为这个课程的第一期学员，本拐也从中深受其益，因为这门课不过讲了编程和AI，更是讲了整体互联网行业内各个职能体系的思维方式及方法论，课程的结构是这个样子：

![img](/assets/jpeg/1697273276791.jpg)


可以看出，这门课程涵盖了实践，能力扩展，思维方式，提效工具的各个方面，目前课程已经进行到了第三期，而本拐当然是第一期的学员之一，在此，本拐郑重向各位安利。喜欢的朋友可以点击【原文连接】查看课程介绍。


 {%- include about.md -%}

