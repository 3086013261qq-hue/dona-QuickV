# dona快V 功能设计 / v0.3

本版取代 v0.2 的 iframe 样式覆盖方案。管理面板随二改插件安装，酒馆助手仅负责可选悬浮播报。

| 模块 | 交付物 | 验收 |
|---|---|---|
| F01 管理面板 | replacement index.html + style.css，复用 app.js | 原控件和功能无损，手机竖屏/横屏/软键盘可用 |
| F02 原插件安装 | 现有安装架构下的面板资源替换 | 安装清单与资源摘要正确，更新回滚不破坏原配置；不运行未经审核脚本 |
| F03 悬浮播报 | 独立酒馆助手脚本 | 只读取原版状态，空闲隐藏，支持关闭与卸载 |
| F04 等待与重试展示 | 读取 #quick-v-chat-wait、#quick-v-failure-notice 等原 DOM | 实际时间、实际状态；失败时原操作仍可用；不新增重试逻辑 |
| F05 视觉统一 | 战术黄、冷白、工业灰、切角、低动效 | 320/390/430px、不遮挡聊天、支持减少动效 |
| F06 兼容性 | 原版运行与无美化情况下均正常 | 不改认证、转发、凭据、请求或进程；不改变安全边界 |

原版状态证据：extension/wait.js 创建 #quick-v-chat-wait；extension/failure-notice.js 创建 #quick-v-failure-notice，并设置 data-phase；extension/failure-client.js 维护状态和既有重试行为。酒馆助手只展示，不负责触发这些行为。原管理面板文件为 plugin/public/index.html、style.css、app.js。

## 命名与署名规范
管理面板保留上游正式名称及真实版本号，例如「快速 V 0.6.5 · dona美化」，美化版本独立编号，不以 dona快V 替代原项目名称或冒称后端作者。仓库名 dona-QuickV 保持不变；独立酒馆助手悬浮播报脚本可称「dona快V · 战术播报」。保留原作者署名与许可声明，不推测未核实的作者名称。
