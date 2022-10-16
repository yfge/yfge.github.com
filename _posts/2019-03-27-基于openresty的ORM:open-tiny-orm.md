---
title: 基于openresty的ORM：open-tiny-orm
tags: open-tiny-orm openresty lua
---

# 序

去年开始接触openresty,手里接过来的项目使用了lor,但是没有用orm,一切全部是手撸sql,各种拼接的语句充斥在业务代码中，让我非常的不能忍。因为之前有过框架开发的经验，所以有了写一个简单的orm的冲动。

那么,在互联网行当中，一个良好的orm应该有哪些特质呢？
1. 它应该是参数化生成查询语句的
2. 支持基本的分页操作
3. 应该是主从分离的
4. 应该是轻Model的
5. 方便调试输出
本着这几个出发点，于是有了这套小巧的框架，一共几百行，十个文件
但是加入这个到你的项目中，相信会让你的开发事半功半

# 安装
```bash
opm install yfge/open-tiny-orm
```
当然,也可以直接git clone 
```bash 
git clone https://github.com/yfge/open-tiny-orm.git
```

# model定义

* 推荐使用配置文件，配置文件应该为 `config/mysql` 即可以通过`require('config.mysql')`引入,里面应该是类似的结构： 
```lua
return {
    tiny = {
     	timeout = 3000,
            pool = {
                maxIdleTime = 120000,
                size = 800,
            },
            clusters = {
                master = {"127.0.0.1", "3306"},
                slave = {
                    {"127.0.0.1", "3306"},
                }
            },
            database = "tiny",
            user = "test",
            password = "123456",
            charset = "utf8",
            maxPacketSize = 1024*1024,
    }
}

```

这样在定义Model时只需要将 'tiny' 这个数据源传入即可
```lua
    local model = require('tiny.orm.mysql.model')
    local m = model:new (
        'table_test', -- 表名
        {
            'id',
            'name',
            'short',
            'remark',
            'date'
        },          -- 列的定义
        'tiny',     -- 使用 config/mysql 中的 tiny 配置字段作为连接配置
        'id', --自增 id
    )
```

* 当然从其他的地方加入配置文件
```lua
local model = require('tiny.orm.mysql.model')
local config = {
 	timeout = 3000,
        pool = {
            maxIdleTime = 120000,
            size = 800,
        },
        clusters = {
            master = {"127.0.0.1", "3306"},
            slave = {
                {"127.0.0.1", "3306"},
            }
        },
        database = "tiny",
        user = "test",
        password = "123456",
        charset = "utf8",
        maxPacketSize = 1024*1024,
}
local m = model:new(
    'tiny_user',
    {
        'id',
        'name',
        'passwd'
    },
    config,
    'id'
)
```
# 增删改查
我们推荐进行3层以上的上的分层,即将MVC中的M(model)层分为model和data两层，这样mode只负责数据的定义,而data则封装了数据的操作。
在lua中，这尤其重要，因为function是不能被序列化的


* 引入 model 和data 
```lua
    --- 增删改查
     local model = require('tiny.orm.mysql.model')
    local m = model:new (
        'table_test', -- 表名
        {
            'id',
            'name',
            'short',
            'remark',
            'date'
        },          -- 列的定义
        'tiny',     -- 使用 config/mysql 中的 tiny 配置字段作为连接配置
        'id', --自增 id
    )
    local mysql_fac = require('tiny.orm.mysql.factory')
    local fac = mysql_fac:new (m) -- m 为上文的
```
* 新建--> 用new_item() 生成一个新model实例，create进行创建
```lua
    local item = fac:new_item()
    item.name = 'hello world'
    item.show = 'hw'
    fac:create(item)
```
* 查询，修改，删除
```
    --- item.id 已经被赋值
    --- 按 id 查询
    local id = 1
    local item2 = fac:get_by_id(id)
    if (item2~=nil) then
        item2.name = 'new world '
        fac:save(item2) ---- 保存
    end
    --- 删除
    if item2 ~= nil then
        fac：delete(item2)
    end

```
# 查询与分页
可以用fac:get_query 返回一个查询实例    
然后就可以像其他语言的orm一样进行链式调用了
```lua
     cal items = nil
     local query = fac:get_query()
     --- select ... from  .. where id = 1
     items = query:where('id',1)
                  :first()
     query = fac:get_query()
     --- select .. from .. where name = 'hello ' limit 10,off 10 ;
     local items2 = query:where('name','hello')
                         :skip(0)
                         :take(10)
                         :get()
     query = fac:get_query()
     --- select  ... from where name = 'hello ' and id in (1,2,3,4)
     local items3 = query:where (name ,'hello')
                         :where_in('id',{1,2,3,4})
                         :get()
     query = fac:get_query()
     --- select .. from .. where .. order by ..
     local items4 = query:order_by('id','asc')
                         :order_by('name')
                         :get()


```

# 事务
我们封装了事务的操作，在多数据源下，事务是跨连接的，即在提交时会在不同的数据源（如果该数据源上有操作）创建连接，做到同时提交,同时回滚

```lua
    local trans = require('tiny.orm.mysql.transaction')
    local t = trans:new()
    t:start()
    --- 各种操作
    t:submit()
    --  提交
    t:rollback()
-- 回滚
```
# 日志操作
封装了一个简单的日志操作，可以通过`local log = require('tiny.log.helper')` 进行引入,之后可以在你的调试中通过`log.trace,log.debug,log.info,log.error,log.warn,log.fatal` 等进行日志记录。

这些日志最终可以通过 `log.get_log()`得到一个table,当调用为`warn,err,fatal`时，会有相应的文件名和代数输出。

# 最后
git 的地址为： 
https://github.com/yfge/open-tiny-orm
欢迎start ,follow ,and join !
