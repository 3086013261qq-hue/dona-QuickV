# dona快V · 战术播报 0.1.0 / 私有本地测试

- frontend/tools/build_panel.py：输入用户授权的原始 install-0.6.5.cjs，按固定 SHA-256 校验，静态生成 index.html 与 style.css，保留原 app.js。tools/build_release.py 调用该函数并完成私有安装包构建，不执行安装器。
- frontend/broadcast/dona-broadcast.js：酒馆助手脚本原型，使用宿主 DOM 观察原版等待与故障提示。不读凭据、不请求网络、不触发重试、不遮盖原版操作。脚本在 pagehide 清理。
- 原版故障提示首次延迟 6 秒，DOM 模式可能错过短重试；现有 DOM 无法提供重试总上限及本轮 Token 用量。等待计时为整轮生成用时，不能声称首字延迟。
- 已实现的 dona-qv:status 同源 DOM 自定义事件采用 version:1、runId、seq、type（start/waiting/retry/connecting/streaming/complete/failed/cancelled/reset）与脱敏数字字段。由原扩展发布既有受保护接口的状态，不新增网络轮询。所有示例数字只在 tests/ 中，生产无 mock 数据。
- 本轮统计只来自提供方原始 usage 字段；缺失字段省略。成功传输耗时采用原版成功尝试的 gen_time，语义见 docs/broadcast-spec.md。
- 普通请求可展示实际已开始的额外重试数/预算；PVP 使用总尝试数，避免把并发候选误称串行重试。全局尝试数含首次请求和某些协议回退。
- 完整二改 CJS 安装包在 .local/release/，仍需原版联网运行依赖。私有仓库不能匿名 CDN 导入；复制本文件完整源码到酒馆助手脚本库进行本地测试。
- reinjection 会清理上一实例；普通 pagehide 或调用宿主 window.__donaQvBroadcastV1?.() 会卸载。BFCache 暂停并在恢复后重新观察；跨域父文档不可访问时不挂载，不放宽权限。
- 已完成桌面 Chromium 模拟，安卓安装、宿主权限、触控和后台恢复仍待真机验证。
