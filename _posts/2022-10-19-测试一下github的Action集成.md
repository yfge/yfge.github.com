---
layout: post
title:  pages博客的配置以及标签的自动化
tags: GitHub 自动化 标签 博客
---
{% raw %}
# github pages博客的配置以及标签的自动化

## 引子

> 没有github的程序员，不是好程序员！

**BUT**

> 如果有一个`*.github.io`的blog,会不会更酷?

基于以上原因，本拐也折腾了一下自己的github,并且做了**标签**的集成功能，以下为一些最佳实践。

## 启用github pages

### 建立存储库

对于开发者个人而言，建立github pages第一步就是建立一个`YOURNAME.github.io` 的存储库。

其中：`YOURNAME` 是你的github用户名。

> 如果是早期的情况，仓库名为 `YOURNAME.github.com`


## 配置Jekyll

基本存储库建立好以后，只能看到一个很丑的原生页面，为了让站点美观，我们需要配置`Jekyll`

> **关于Jekyll**
> Jekyll 是一个静态站点生成器，内置 GitHub Pages 支持和简化的构建过程。 Jekyll 使用 Markdown 和 HTML 文件，并根据您选择的布局创建完整静态网站。 Jekyll 支持 Markdown 和 Lick，这是一种可在网站上加载动态内容的模板语言。 有关详细信息，请参阅 Jekyll。

### 安装Jekyll
MacOS下安装Jeky脚本如下：

```bash
# 需要ruby
brew install ruby 
# 安装jekyll
sudo gem install bundler jekyll minima
bundle install
```
### 初始化站点结构

将存储库clone到本地后，进入到存储库目录下，执行：

```bash
jekyll new --skip-bundle ./
```
这时jekyll会初始化相应的目录结构，如下：

```bash
.
├── 404.html
├── Gemfile
├── Gemfile.lock
├── _config.yml
├── _posts
│   └── 2022-10-19-welcome-to-jekyll.markdown
├── about.markdown
└── index.markdown
```
到这里，一个基本的配置已经完成了。
只要按照`mmm-yy-dd-title.md`的形式往`_posts`目录下增加文档，在推送后就会进行相应的更新。

也可以在本地运行`bundle exec jekyll serve`来看站点的生成形式。


## 加入标签支持

### 在博客内容中加入标签

现在的博客内容，大多都愿意以标签形式进行组织，而`Jekyll`原生并没有提供相应的支持，为了让博客更cool，我们需要加入对标签的支持。

首先，我们要在博客的内容中加入tag,即在你的markdown文档开始部分加入tags说明，比如，本文档最开始是这样的：

```bash
---
layout: post
title:  pages博客的配置以及标签的自动化
tags: GitHub 自动化 标签 博客
---

# github pages博客的配置以及标签的自动化
```
### 配置标签页和组件

我们要将标签聚合配置一个默认模板，在`_layouts`目录下，创建`tagpage.html`

内容如下：

```liquid
---
layout: default
---

<div class="post">
<h1>Tag: {{ page.tag }}</h1>
<ul>
{% for post in site.tags[page.tag] %}
  <li><a href="{{ post.url }}">{{ post.title }}</a> ({{ post.date |     date_to_string }})<br>
    {{ post.description }}
  </li>
{% endfor %}
</ul>
</div>
<hr>

{% include archives.html %}

```

同时，为我们标签加入一个页面的组件，在`_includes`下创建`archives.html`

内容如下：

```html
<h2>标签</h2>
{% capture temptags %}
  {% for tag in site.tags %}
    {{ tag[1].size | plus: 1000 }}#{{ tag[0] }}#{{ tag[1].size }}
  {% endfor %}
{% endcapture %}
{% assign sortedtemptags = temptags | split:' ' | sort | reverse %}
{% for temptag in sortedtemptags %}
  {% assign tagitems = temptag | split: '#' %}
  {% capture tagname %}{{ tagitems[1] }}{% endcapture %}
  <a href="/tag/{{ tagname }}"><code class="highligher-rouge"><nobr>{{ tagname    }}</nobr></code></a>
{% endfor %}
```

### 生成标签索引页

因为`Jeykll`整体内容组织是基于目录的，所需要按目录生成对应的tags,具体方式为，建立一个文件`make-tag.py`

```python
import glob
import os

post_dir = '_posts/'
tag_dir = 'tag/'

filenames = glob.glob(post_dir + '*md')

total_tags = []
for filename in filenames:
    f = open(filename, 'r', encoding='utf8')
    crawl = False
    for line in f:
        if crawl:
            current_tags = line.strip().split()
            if len(current_tags)>0  and   current_tags[0] == 'tags:':
                total_tags.extend(current_tags[1:])
                crawl = False
                break
        if line.strip() == '---':
            if not crawl:
                crawl = True
            else:
                crawl = False
                break
    f.close()
total_tags = set(total_tags)

old_tags = glob.glob(tag_dir + '*.md')
for tag in old_tags:
    os.remove(tag)
    
if not os.path.exists(tag_dir):
    os.makedirs(tag_dir)

for tag in total_tags:
    tag_filename = tag_dir + tag + '.md'
    f = open(tag_filename, 'a')
    write_str = '---\nlayout: tagpage\ntitle: \"Tag: ' + tag + '\"\ntag: ' + tag + '\nrobots: noindex\n---\n'
    f.write(write_str)
    f.close()
print("Tags generated, count", total_tags.__len__())

```

可以简单看出，这个脚本的作用，就是遍历博客文档，生成`./tag/TAG.md`的文档。

这样，可以在每次博客写完后，运行一下相应的脚本，即可。

```python
python make-tag.py
```

### 让标签不在导航中显示

我们现在对标签的配置已经完成了，但是有一个问题，就是所有的标签都会展示在页面的导航中，非常别扭，因此，需要改一下导航的生成。

先将默认的模板copy到项目下：

```bash
sudo mv   /Library/Ruby/Gems/2.6.0/gems/minima-2.5.1/_includes/header.html ./_includes  
```
打开`header.html`，找到下面内容（应该在19-26行)：

```liquid
<div class="trigger">
  {%- for path in page_paths -%}
    {%- assign my_page = site.pages | where: "path", path | first -%}
    {%- if my_page.title -%}
    <a class="page-link" href="{{ my_page.url | relative_url }}">{{ my_page.title | escape }}</a>
    {%- endif -%}
  {%- endfor -%}
</div>
```

改为：

```liquid
        <div class="trigger">
          {%- for path in page_paths -%}
            {%- assign my_page = site.pages | where: "path", path | first -%}
            {%- if my_page.title  -%}
            {%- unless my_page.title contains "Tag" -%}
            <a class="page-link" href="{{ my_page.url | relative_url }}">{{ my_page.title | escape }}</a>
            {%- endunless -%}
            {%- endif -%}
          {%- endfor -%}
        </div>
```

这回再刷新，已经看不到多余的内容了。

## 集成到 GitHub Action中
我们现在已经完成了标签的配置以及生成，但还是很别扭，因为：

1. 每次都要运行一下对应的脚本 `python make-tag.py`；
2. 在 `tag`目录下生成很多冗余文件。

对于有强迫症的你，肯定是接受不了的，那么，我们可以把标签生成的工作交给`GitHub 的Action`来完成。

具体方式：
1. 先直接把tag目录干掉&commit
2. 进入项目的`Action` 页面，选择`New Workflow`
![image](/assets/jpeg/871666167187_.pic.jpg)
3. 进入页面后，搜索`pages`
![image](/assets/jpeg/881666167204_.pic.jpg)
4. 选择`GitHub Pages Jeykll` 下的`Configure`
![image](/assets/jpeg/891666167275_.pic.jpg)
5. 这时会跳转到如下页面：
![image](/assets/jpeg/901666167311_.pic.jpg)
6. 更改这个代码，在第29行后加入：
```yaml
      - name: Setup Python
        uses: actions/setup-python@v3
      - name: Generate Tags
        run:  python make-tag.py
```
![image](/assets/jpeg/911666167592_.pic.jpg)
然后保存并提交

7. 进入项目的 GitHub配置页面，在`Pages`标签下，把`Build And Deployment`下的`Source`选项从`Branch`改成`GitHub Actions`。
![image](/assets/jpeg/921666168419_.pic.jpg)

在这时，如果再有提交，就会运行我们新配置的action进行部署了。

到此为止，算是大功告成。

## 参考

1. GitHub 官方文档 [https://docs.github.com/cn/pages](https://docs.github.com/cn/pages)

2. Jekyll官方文档 [https://jekyllrb.com/](https://jekyllrb.com/)

3. Long Qian : Jekyll Tags on Github Pages [https://longqian.me/2017/02/09/github-jekyll-tag/](https://longqian.me/2017/02/09/github-jekyll-tag/)

4. Jekyll的liquid脚本文档 [https://shopify.github.io/liquid/](https://shopify.github.io/liquid/)

5. 转义，解决花括号在 Jekyll 被识别成 Liquid 代码的问题 [https://blog.walterlv.com/post/jekyll/raw-in-jekyll.html](https://blog.walterlv.com/post/jekyll/raw-in-jekyll.html)

6. GitHub Actions [https://docs.github.com/cn/actions](https://docs.github.com/cn/actions)



{% endraw %}


 {%- include about.md -%}


