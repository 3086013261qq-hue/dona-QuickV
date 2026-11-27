# dona快V 视觉层

## 管理面板
theme/panel.css 为现有皮肤初稿。最终交付独立替换版 plugin/public/index.html 与 style.css；保留原 app.js 及其 ID/属性契约。可在构建阶段合并原 CSS 与覆盖层。不需要酒馆助手跨 iframe 注入管理面板。

## 悬浮播报
theme/extension.css 为前期风格参考，后续独立酒馆助手脚本采用专属命名空间；只观察原版等待与故障提示状态，不承担管理面板功能，不改变请求行为。不得隐藏必要的原版操作。原版扩展继续运行。卸载时清理自己创建的 DOM、样式、监听与观察器。

现已实现私有本地构建与状态桥：`python tools/build_release.py install-0.6.5.cjs`。构建会调用 `frontend/tools/build_panel.py` 的面板生成函数，将现有皮肤与原 CSS 合并，再静态回填原安装清单并重算摘要。业务 `app.js` 保持逐字节一致。

`integration/` 包含自研的脱敏字段采集与事件桥；`tools/build_release.py` 对固定 SHA-256 原版应用精确插入观察钩子，不复制原手机源码到 Git。受保护的原版 failure-status 接口附加本轮数字字段，复用原扩展既有轮询，播报脚本不发网络请求。

已执行桌面 Chromium 手机视口和生命周期模拟；尚未验证安卓安装、真实服务商请求和具体酒馆助手版本权限。参见 `docs/testing.md`。

## 命名与署名规范
管理面板保留上游正式名称及真实版本号，例如「快速 V 0.6.5 · dona美化」，美化版本独立编号，不以 dona快V 替代原项目名称或冒称后端作者。仓库名 dona-QuickV 保持不变；独立酒馆助手悬浮播报脚本可称「dona快V · 战术播报」。保留原作者署名与许可声明，不推测未核实的作者名称。
