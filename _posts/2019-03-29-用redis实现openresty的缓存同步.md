---
title: 用redis实现openresty的缓存同步
tags: open-tiny-orm openresty redis 缓存 并发 lua
date: 2019-03-29
---
# 引 
**"一切单机缓存都是魔鬼,与其被消灭，不如与其共舞"**
# 来由
之前接到我们uAuth的一个bug,具体原因为,当一个用户改密后，原token理应失效，但是线上时常会有原token访问的正常的情况。
可是在测试环境上，确无论如何也复现不出来。

后来仔细分析了源码,是由于token的存储用了openresty的缓存，当token失效后，只在线上的n台服务器中的一台做了失效处理，而其他的n-1台的缓存仍然有效。 

# 思路

**缓存不一致** ———— 这确实是好多场景容易碰到的问题，那么怎么办？解决方式有二：
1. 干掉openresty的缓存,将存储设计由openresty缓存/redis/mysql 改为redis/mysql 两层结构。 
2. 设计openresty的缓存同步机制，从根儿上解决这个问题。

方式1，确实是简单直接有效的方式，but:   

**使用openresty，不让我用缓存，那和一条咸鱼有什么区别？**

于是，我选择了第2种方式，那么问题来了，如何设计这个同步机制 ？
经典的同步肯定是发布/订阅来搞定，第一时间自然想到了kafka，可是查了一圈发现openresty中官方的resty.kafka只支持生产,并且大多数场景都是用来日志记录。到时redis,有一个经典的subscribe例子,那么好，就这么干。 

## 撸码
### 封装发布/订阅操作
既然同步，那咱就整到位。 
第一步,封装一个redis_message.lua
```lua
local redis_c = require "resty.redis"
local cjson = require 'cjson.safe'
local M = {}
local mt = {__index = M}
function M:new(cfg)
    local ins = {
        timeout = cfg.timeout or 60000,
        pool = cfg.pool or {maxIdleTime = 120000,size = 200},
        database = cfg.database or 0,
        host = cfg .host,
        port = cfg. port,
        password = cfg .password or ""
    }
    setmetatable(ins,mt)
    return ins
end
local function get_con(cfg)
    local red = redis_c:new()
    red:set_timeout(cfg.timeout)
    local ok,err = red:connect(cfg.host,cfg.port)
    if not ok then
        return nil
    end
    local count ,err = red:get_reused_times()
    if 0 == count then
        ok ,err = red:auth(cfg.password)
    elseif err then
        return nil
    end

    red:select(cfg.database)
    return red
end

local function keep_alive(red,cfg)
    local ok,err = red:set_keepalive(cfg.pool.maxIdleTime,cfg.pool.size)
    if not ok then
        red:close()
    end
    return true
end

function M:subscribe(key,func)
    local co = coroutine.create(function()
        local red = get_con(self)
        local ok,err = red:subscribe(key)
        if not ok then
            return err
        end
        local flag = true
        while flag do
            local res,err = red:read_reply()
            if err then
                ;
            else
                if res[1] == "message" then
                    local obj = cjson.decode(res[3])
                    flag = func(obj.msg)
                end
            end
            red:set_keepalive(100,100)
       end
   end)
   coroutine.resume(co)

end
function M:publish(key,msg)
    local red = get_con(self)
    local obj = {}
    obj.type = type(msg)
    obj.msg = msg
    local  ok,err = red:publish(key,cjson.encode(obj))
    if not ok then
        return false
    else
        return true
    end
    keep_alive(red,self)
end

return M
```
这个messagel.lua里，有几个点可以关注一下：
1. redis的的subscribe操作是subcribe CHANNEL
2. 当subscribe收到相应的信息后,是一个数组，依次为[事件,通道,数据],因此我们只从简单考虑事件的情况,即`message`这种情况。
3. 我们对外封装是subcribe后传入一个函数的，如果这个函数返回false就停止订阅。

## 设计消息格式
为了保证缓存操作的通用性,我们设计消息格式为：
```lua
local msg = {key = key ,cache = cache_name,op=op,data=data,timeout=timeout}
```
在这其中：  
1. cache表示我们要同步的缓存名称。
2. key表明了要同步的缓存key值
3. op设置了三种,分别是set,expire,del
4. 根据op的不同,可以选择性的传入data,timeout(设置超时使用)

## 加入配置
加入一个配置，我这里保存的是app/config/cacheSync
```lua
return {
    redis = {
        host="10.10.10.111",
        port=6379,
        database = 3,
        password = "Pa88word"
    },
    queueName='lua:tiny:cache:sync',
}
```

## 封装业务层的发布操作
在封装好底层库,设计好消息格式后,我们就可以封装业务层的操作了。即:
```lua
local cfg = require('app.config.cacheSync') --同步的配置，包括服务器
local redis_message = require('libs.redis.redis_message') --上文封装的message
local function async_cache(cache_name,key,op,data,timeout)
     local rm = redis_message:new(cfg.redis)
     local message = {key = key ,cache = cache_name,op=op}
     if data then
        message .data = data
     end
     if timeout then
        message.timeout = timeout
     end
     rm:publish(cfg.queueName,message)
end
```
## 封装订阅操作
我们的订阅操作放在init_by_lua_file的生命周期中，话不多说代码如下:
```lua
local cfg = require('app.config.cacheSync') --同步的配置，包括服务器
local redis_message = require('libs.redis.redis_message') --上文封装的message
local cjson = require('cjson.safe')
local function handler(msg)
    local key = msg.key
    local shared = ngx.shared[msg.cache]
    if shared ~= nil and shared ~= ngx.null then
          if msg.op == 'del' then
              shared:delete(key)
          elseif msg.op == 'set' then
              local data = cjson.encode(msg.data)
              if data == nil or data == ngx.null then
                 data = msg.data
              end
              local res ,msg = shared:set(key,data)
              if msg then
                ngx.log(ngx.ERR,msg)
              end
          elseif msg.op =='expire' then
              shared:set(key,cjson.encode(msg.data),msg.timeout)
          end
    end
    return true
end
local req_id = ngx.worker.id()
if req_id == 0 then
   ngx.timer.at(0,function()
        local message = redis_message:new(cb_cfg.redis)
        message:subscribe(cfg.queueName,handler)
   end)
end
```
OK,至此为止，我们成功的实现了openresty的缓存同步，并且初步有了一套可复用的组件，当然这里还有几个tips:
1. 需要在conf文件中设置` lua_socket_log_errors off;` 否则nginx的error文件会一直报timeout错误。
2. 没有考虑redis的可靠性问题。

