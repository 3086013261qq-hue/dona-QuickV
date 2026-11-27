# dona快V · 战术播报 / 开发版

- frontend/tools/build_panel.py：输入用户授权的原始 install-0.6.5.cjs，按固定 SHA-256 校验，仅静态提取并生成 index.html 与 style.css，保留原 app.js，不执行安装器，不重新打包后端。
- frontend/broadcast/dona-broadcast.js：酒馆助手脚本原型，使用宿主 DOM 观察原版等待与故障提示。不读凭据、不请求网络、不触发重试、不遮盖原版操作。脚本在 pagehide 清理。
- 原版故障提示首次延迟 6 秒，DOM 模式可能错过短重试；现有 DOM 无法提供重试总上限及本轮 Token 用量。等待计时为整轮生成用时，不能声称首字延迟。
- 可选的 dona-qv:status 同源 DOM 自定义事件采用 version:1、runId、seq、type（start/retry/connecting/streaming/complete/failed/cancelled）与脱敏数字字段。事件桥未实现；若启用桥，所有后续请求均须发布 start/终态。不得以 mock 数据作为线上数据。
- 尚未完成完整安装包和真机验证；私有仓库不能匿名 CDN 导入。开发测试可复制脚本源码到酒馆助手脚本库。
