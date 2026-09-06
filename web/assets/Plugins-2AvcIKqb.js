import{q as p,m,c as e,a as n,p as i,F as g,g as f,d as _,s as a,o as s,t as d,n as b}from"./index-CRDCzMSX.js";const y={class:"card"},v={key:0,class:"loading"},x={key:1,class:"table"},h=["onClick"],k={key:0},w={__name:"Plugins",setup(P){const o=p();m(()=>{r()});function r(){o.fetchPlugins()}async function c(u){await o.reloadPlugin(u)}return(u,l)=>(s(),e("div",null,[n("div",{class:"topbar"},[l[0]||(l[0]=n("h2",null,"插件管理",-1)),n("div",{class:"topbar-actions"},[n("button",{class:"btn btn-outline btn-sm",onClick:r},"刷新")])]),n("div",y,[l[3]||(l[3]=n("div",{class:"card-title"},"已加载插件",-1)),i(o).loading?(s(),e("div",v,"加载中...")):(s(),e("table",x,[l[2]||(l[2]=n("thead",null,[n("tr",null,[n("th",null,"插件名称"),n("th",null,"处理器数"),n("th",null,"有实例"),n("th",null,"操作")])],-1)),n("tbody",null,[(s(!0),e(g,null,f(i(o).plugins,t=>(s(),e("tr",{key:t.name},[n("td",null,[n("strong",null,d(t.name),1)]),n("td",null,d(t.handlers),1),n("td",null,[n("span",{class:b(["badge",t.has_instance?"badge-success":"badge-warning"])},d(t.has_instance?"是":"否"),3)]),n("td",null,[n("button",{class:"btn btn-outline btn-sm",onClick:C=>c(t.name)},"重载",8,h)])]))),128)),i(o).plugins.length?_("",!0):(s(),e("tr",k,[...l[1]||(l[1]=[n("td",{colspan:"4",class:"empty-state"},[n("div",{class:"empty-state"},[n("div",{class:"icon"},"🧩"),n("p",null,"暂无插件"),n("p",{style:{"font-size":"12px","margin-top":"8px"}},"将插件放置在 plugins/ 目录下即可自动加载")])],-1)])]))])]))]),l[4]||(l[4]=n("div",{class:"card"},[n("div",{class:"card-title"},"插件开发指南"),n("div",{style:{"font-size":"14px","line-height":"1.8",color:"#475569"}},[n("p",null,[a("创建插件文件 "),n("code",null,"plugins/my_plugin.py"),a("：")]),n("pre",{style:{background:"#F1F5F9",padding:"16px","border-radius":"8px",margin:"12px 0","overflow-x":"auto"}},[a(""),n("code",null,`from core.plugin.decorators import on_command, on_message
from core.plugin.context import PluginContext

class MyPlugin:
    _skbook_handlers = [
        {"type": "command", "name": "hello", "aliases": ["你好"]},
    ]

    def __init__(self):
        self.ctx: PluginContext = None

    async def on_load(self):
        self.ctx.log.info("插件已加载")

    async def hello(self, event):
        await event.reply(f"你好！你的用户ID是 {event.sender_id}")`),a(`
        `)]),n("p",null,[a("更多文档请参考 "),n("code",null,"docs/plugin-development.md")])])],-1))]))}};export{w as default};
