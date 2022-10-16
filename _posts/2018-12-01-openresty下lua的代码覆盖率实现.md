---
title: openresty下lua代码覆盖率实现
tags: openresty lua 自测 代码覆盖率
date: 2019-01-29
---

# 废话在前
## 什么是代码覆盖率
来自**百度百科**
>代码覆盖（Code coverage）是软件测试中的一种度量，描述程式中源代码被测试的比例和程度，所得比例称为代码覆盖率。

## 开发人员为何关注?

在我们的开发过程中，经常要用各种方式进行自测，或是各种 xUnit 系列，或是 postman，或是直接curl，在我们的代码交给 QA 同学之前，我们有必要知道自己的自测验过了多少内容，在这种情况，代码覆盖率就是一个重要的衡量指标。

# openresty 中的代码覆率解决方案

我们如果想得到每一次执行的代码覆率,需要搞定两件事情:

1. 可以**外在**的记录每一行的代码
2. 在记录的同时，可以知道这一行的代码上下文是什么
3. 更重要的是，我们需要尽可能的不动现有业务代码

对于第一点，lua的debug库中有一个非常神奇的钩子函数`sethook`,其官方文档如下:

>**debug.sethook ([thread,] hook, mask [, count])**
>
> Sets the given function as a hook. The string mask and the number count describe when the hook will be called. The string mask may have any combination of the following characters, with the given meaning:
>* 'c': the hook is called every time Lua calls a function;
>* 'r': the hook is called every time Lua returns from a function;
>* 'l': the hook is called every time Lua enters a new line of code.Moreover, with a count different from zero, the hook is called also after every count instructions.
>
>When called without arguments, debug.sethook turns off the hook.
>When the hook is called, its first argument is a string describing the event that has triggered its call: "call" (or "tail call"), "return", "line", and "count". For line events, the hook also gets the new line number as its second parameter. Inside a hook, you can call getinfo with level 2 to get more information about the running function (level 0 is the getinfo function, and level 1 is the hook function).

其中文翻译大体如下：

> 将给定的方法设定为钩子，参数`mask`和`count`决定了什么时候钩子方法被调用.参数`mask`可以是下列字符的组合:
>
>* 'c' 当lua**开始**执行一个方法时调用;
>* 'r' 当lua执行一个方法在**返回**时调用;
>* 'l' 当lua每执行到一行代码时调用.即lua从0开始执行一个方法的每一行时，这个钩子都会被调用.
>
>如果调用时不传任何参数,则会移除相应的钩子.当一个钩子方法被调用时,第一个参数表明了调用这个钩子的事件：`"call"`(或`"tail call"`),`"return"`,`"line"`和`"count"`.对于执行代码行的事件,新代码的行号会作为第二个参数传入钩子方法,可以用`debug.getinfo(2)`得到其他上下文信息.

在这个官方的说明里,lua已经贴心的告诉我们使用方式————配合debug.getinfo,那么debug.getinfo是什么？其实我们在之前讨论错误输出时已经使用过这个方法,其官方文档如下：

>**debug.getinfo ([thread,] f [, what])**
>
>Returns a table with information about a function. You can give the function directly or you can give a number as the value of f, which means the function running at level f of the call stack of the given thread: level 0 is the current function (getinfo itself); level 1 is the function that called getinfo (except for tail calls, which do not count on the stack); and so on. If f is a number larger than the number of active functions, then getinfo returns nil.
>
>The returned table can contain all the fields returned by lua_getinfo, with the string what describing which fields to fill in. The default for what is to get all information available, except the table of valid lines. If present, the option 'f' adds a field named func with the function itself. If present, the option 'L' adds a field named activelines with the table of valid lines.
>
>For instance, the expression debug.getinfo(1,"n").name returns a name for the current function, if a reasonable name can be found, and the expression debug.getinfo(print) returns a table with all available information about the print function.

这个API的说明中文含义大体如下:

>以table的形式返回一个函数的信息,可以直接调用这个方法或是传入一个表示调用堆栈深度的参数f，0表示当前方法(即**getinfo**本身),1表示调用**getinfo**的方法(除了最顶层的调用,即不在任何方法中),以此类推。如果传入的值比当前堆栈深度大,则返回nil.

>返回的table内字段包含由**lua_info**返回的所有字段。默认调用会除了代码行数信息的所有信息。当前版本下,传入`'f'`会增加一个`func`字段表示方法本身,传入`'L'`会增加一个`activelines`字段返回函数所有可用行数。

>例如如果当前方法是一个有意义的命名,`debug.getinfo(1,"n").name`可以得到当前的方法名,而`debug.getinfo(print)`可以得到**print**方法的所有信息。

OK,有了这两个方法,我们的思路就变得很清析了：

1. 在生命周期开始时注册钩子函数.
2. 将每一次调用情况记录汇总.

这里有一个新的问题，就是，我们的汇总是按调用累加还是只针对每一次调用计算，本着实用的立场，我们是需要进行累加的，那么，需要使用ngx.share_dict 来保存汇总信息.

基于以上考虑,封装一个libs/test/hook.lua文件,内容如下:

    local debug = load "debug"
    local cjson = load "cjson"
    local M = {}
    local mt = { __index = M }
    local sharekey = 'test_hook'
    local cachekey = 'test_hook'
    function M:new()
        local ins = {}
        local share = ngx.shared[sharekey]
        local info ,ret = share:get(cachekey)
        if info then
            info = cjson.decode(info)
        else
            info = {}
        end
        ins.info = info
        setmetatable(ins,mt)
        return ins
    end
    function M:sethook ()
        debug.sethook(function(event,line)
            local info = debug.getinfo(2)
            local s = info.short_src
            local f = info.name
            local startline = info.linedefined
            local endline = info.lastlinedefined
            if  string.find(s,"lualib") ~= nil then
                return
            end
            if self.info[s] == nil then
                self.info[s]={}
            end
            if f == nil then
                return 
            end
            if self.info[s][f] ==nil then
                self.info[s][f]={
                    start = startline,
                    endline=endline,
                    exec = {},
                    activelines = debug.getinfo(2,'L').activelines
                    }
            end
            self.info[s][f].exec[tostring(line)]=true
    
        end,'l')
    end
    function M:save()
         local share = ngx.shared[sharekey]
         local ret = share:set(cachekey,cjson.encode(self.info),120000)
    end
    function M:delete()
         local share = ngx.shared[sharekey]
         local ret = share:delete(cachekey)
         self.info = {}
    end
    function M:get_report()
        local res = {}
        for f,v in pairs(self.info) do
            item = {
                file=f,
                funcs={}
            }
            for m ,i in pairs(v) do
                    local cover = 0
                    local index = 0
                    for c,code in pairs(i.activelines) do
                        if i.activelines[c] then
                            index = index + 1
                        end
                        if i.exec[tostring(c)] or i.exec[c] then
                            cover = cover +1
                        end
                    end
                    item.funcs[#item.funcs+1] = { name = m ,coverage=   string.format("%.2f",cover / index*100 ) .."%"}
            end
            res[#res+1]=item
       end
       return res
    end
    return M

这样，我们**只需要**在content_by_lua的最开始加上:

    local hook = load "libs.test.hook"
    local test = hook:new()
    test:sethook()
    --other code ..
    
在最末加上:

    test:save()
    
即可统计代码覆盖率。

是的，没错，**我们至今只增加了4行业务代码**

但是统计了,应该怎么进行输出呢？

**加个接口好了:)**

因为现在lor用的多,所以,干脆加个lor的路由文件(libs/test/lorapi.lua):

    local hook = require 'libs.test.hook'
    local router =  lor:Router ()
    local M = {}
    router:get('/test/coverage/json-report',
    function(req,res,next)
        local t = hook:new()
        res:json(t:get_report())
    end)
    router:get('/test/coverage/txt-report',
    function(req,res,next)
        local t = hook:new()
        local msg = "Report"
        local rpt = t:get_report()
        for i ,v in pairs(rpt) do
            msg =msg.."\r\n"..v.file
            for j,f in pairs(v.funcs) do
                msg = msg .."\r\n\t function name:" .. f.name .."\tcoverage:"..f.coverage
            end
        end
        msg =msg .."\r\nEnd"
        res:send(msg)
    end)
    return router
    
这样，在我们的lor路由文件里加个requre,加个use,**两行改动,而且是增加！！**就达到我们的需求,检查代码的覆盖率.

