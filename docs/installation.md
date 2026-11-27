# 快速 V 0.6.5 · dona美化 v0.1.0-beta.2 安装说明

全新安装是首要验收项，但目前**被原作者外部运行资源获取阻塞**，不能视为完整可用交付。只有 SillyDroid 的手机仍须取得 Quick V 的 Python 运行包和代码依赖包，SillyDroid 自身运行环境不能直接替代。详见 `resources.md`、`resource-status.json`。

## 手机安装

打开仓库开发分支 README，复制固定版本整条命令，粘贴到 **SillyDroid → 设置 → 内置终端**。无需电脑传文件。命令在私有临时目录下载 `install-dona.cjs`，核对独立写死的 SHA-256 后才运行。对应命令在同包 `commands.json`：install 安装/更新，status 查看，restore 恢复原版。

适用：安卓 ARM64、Node.js 18+、已正常启动过酒馆的 SillyDroid 内置终端。不是 APK 重打包；ZIP 不是酒馆数据导入包。不要在 Windows、Termux 或“ZIP 数据导入”中执行。

### 全新安装：只有 SillyDroid

检测到未安装 Quick V 时，入口下载并校验完整二改 CJS，再进入原版完整流程，包含 Python rootfs、原生工具、应用和依赖安装。保留原版环境、目录、空间、资源分片与总摘要、归档边界、运行锁和失败回滚。没有要求用户预装 Quick V。

然而，当前开发环境普通 GET 作者正式安装器及运行资源返回 HTTP 403/连接错误，尚未获得必要运行包。手机可能有不同的访问结果，但资源未齐、未完成真机安装前不能宣称通过。若同样 403，应向原作者取得恢复后的正式资源或正式备用地址，不使用访问绕过、Cookie 或不明镜像。

### 原版 0.6.5 与同核心 dona 更新

先在原快速 V 面板停止服务。入口逐文件检查原版或 dona 静态指纹，复用原 `preflight`、`reusableRuntime` 和运行锁，精确匹配后才执行小范围事务。业务 app.js、依赖 site、运行二进制及凭据不改动或重新下载。

已是当前指纹时不替换、不下载完整安装器。发现额外本机修改时停止。其他原版版本走原完整流程，仍需要外部资源。成功后重启酒馆，从扩展设置打开「快速 V 0.6.5 · dona美化」。

## 酒馆助手单独导入

手机下载 Release 的 `dona-broadcast.tavern-helper.json`，到 **酒馆助手 → 脚本库 → 全局脚本 → 导入**选择文件，再启用。已核对官方 `N0VI028/JS-Slash-Runner@39b13a5e797303cb0fc352553988b60be1208653` 的 ScriptTree 和文件导入器；它重新分配 ID，默认关闭导入脚本。不能承诺往普通导入窗口粘贴 URL 即可工作。

JSON 只含固定版本云入口、说明和空变量/按钮。云加载器一次获取 jsDelivr 固定标签源码、校验 SHA-256 后加载，不轮询更新。播报仍展示原受保护状态，不保存业务数据，不承担本体安装或管理。

需要同源父文档、宿主允许 Blob ES module。不放宽跨域/CSP。实际安卓 WebView、特定酒馆助手版本的导入、启停待真机验收。单独完整 JS 同时提供，供审查与受控测试。

## 更新与卸载

- 本体更新：运行目标测试版的固定 install 命令。同版跳过；未来版本显式更新标签和摘要，不追踪 main/latest。
- 播报更新：关闭旧项，导入新测试版 JSON，启用确认后删除旧项。
- 播报卸载：关闭后删除；pagehide 清理自身，必要时刷新。原版提示与按钮一直保留。
- 恢复原版 0.6.5：停止服务，执行本版 commands.json 中 restore 命令。只恢复本次修改的静态源码并删除三个新增 dona 模块，不删除 `quick-v-state`、聊天或配置。重启后按需关闭播报。
- 可捕获的文件替换错误自动回滚。系统强杀/断电恢复尚未验证；混合指纹会停止，应使用已核验的完整原版方式修复。
- 整个 Quick V 的卸载继续使用上游审核方式。本项目不提供递归删除业务数据命令。

## 开发与发布

```powershell
python tools/prepare_beta.py
python -m unittest discover -s tests -v
node --test tests/security.test.cjs tests/installer.test.cjs
python tests/browser_qa.py
python tests/cloud_qa.py
python tools/audit_release.py
python tools/publish_release.py --preview
```

原始安装器由获授权开发者放在工程根目录。固定 SHA-256 为 `95f944ba5483e8953bab59a8962cc04d5517fddee6f5913a1054d16db6137db5`。构建只静态读取，不执行原始或二改原业务安装器。产物在 `.local/beta/`，原包/解包文件不提交 Git。

`python tools/check_resources.py --download` 只从原作者固定 HTTPS 地址下载并验证，退出码 2 表示全新安装资源未齐备。未找到可确认正式备用源前不修改基址。发布工具要求源码先提交并推送开发分支，使用现有 GitHub 授权创建草稿、上传并核对摘要后发布 Pre-release；不合并 main，不重新分发运行时二进制。
