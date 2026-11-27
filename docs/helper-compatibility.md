# 酒馆助手导入格式核对

核对基线：[N0VI028/JS-Slash-Runner@39b13a5e797303cb0fc352553988b60be1208653](https://github.com/N0VI028/JS-Slash-Runner/tree/39b13a5e797303cb0fc352553988b60be1208653)。

- [ScriptTree 定义](https://github.com/N0VI028/JS-Slash-Runner/blob/39b13a5e797303cb0fc352553988b60be1208653/src/type/scripts.ts)：单个 script 对象，包含 type、enabled、name、id、content、info、button、data、export_with。生成文件采用该结构，不使用聊天卡、快速回复或虚构的 URL 导入协议。
- [文件导入实现](https://github.com/N0VI028/JS-Slash-Runner/blob/39b13a5e797303cb0fc352553988b60be1208653/src/panel/script/Toolbar.vue)：接受 .json 文件，JSON.parse 后以 ScriptTree 解析；分配新 UUID，强制 enabled=false。故手机步骤是下载 JSON→选择文件导入→手动启用，不能承诺任意版本支持直接粘 URL。
- [脚本库官方文档](https://n0vi028.github.io/JS-Slash-Runner-Doc/guide/基本用法/脚本库.html)：脚本关闭时的清理使用 pagehide。本体 IIFE 已在该生命周期卸载自己的 DOM/监听/计时器；云端加载中的请求也会中止。

JSON content 仅导入固定标签的云加载器；加载器校验核心播报源码摘要后通过 Blob ES module 执行。一轮启用只下载一次，没有更新轮询，不安装后端，不获取业务凭据。手机 WebView、实际助手版本对 CSP/Blob module 和同源父文档的支持仍需真机测试，不改变跨域或 CSP 规避限制。
