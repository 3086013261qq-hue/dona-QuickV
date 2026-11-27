# dona-QuickV

**v0.1.0-beta.1：全新安装资源阻塞，尚不能作为完整可用交付。** 2026-11-27 从开发环境以普通 GET 访问原作者正式地址及运行分片，返回 HTTP 403/连接错误。尚未找到可核实的正式备用源。只有 SillyDroid、还未装 Quick V 的用户，请先阅读[缺失资源与获取方式](docs/resources.md)。

## 1. 项目介绍与署名

在 Quick V 0.6.5 原功能上加入绒绒设计的明日方舟风格面板，以及可独立安装的「dona快V · 战术播报」。面板名称为「快速 V 0.6.5 · dona美化」，不修改认证、转发、重试和模型业务。美化核心版本 `0.1.0`，本次发布流程版本 `0.1.0-beta.1`。

PC 上游：[bad-woman/vertex2openai](https://github.com/bad-woman/vertex2openai)，MIT 署名 `Copyright (c) 2025 gzzhongqi`。手机版保留原版 `author: Quick V` 声明，不推测手机作者姓名。用户明确确认允许公开二改分发，授权由其留存；运行环境及第三方依赖不在本仓库重新分发。详见[版权与授权](docs/third-party-notices.md)。

## 2. 适用环境

安卓 ARM64 手机的 **SillyDroid → 设置 → 内置终端**，Node.js 18+，先正常启动过酒馆。Windows、Termux 和酒馆“ZIP 数据导入”不是安装入口。安卓真机验收尚未完成。

## 3. 快速 V 本体安装

[测试 Release](https://github.com/3086013261qq-hue/dona-QuickV/releases/tag/v0.1.0-beta.1)

**只有 SillyDroid：**命令支持进入完整安装流程，但必须取得原作者 Python 运行包和代码依赖包。当前开发环境未取得这些资源，不能保证现在能完成全新安装；不会拿覆盖安装冒充成功。资源不足时核对[缺失清单](docs/resources.md)，不要关闭校验或使用不明镜像。

**已装原版 0.6.5：**先在快速 V 面板停止服务，再运行同一命令。通过原版和运行环境校验后，只替换美化及状态适配文件，保留已有环境、凭据、配置和聊天。发现额外修改会停止。

在内置终端复制执行整条命令，无需电脑传文件：

```sh
{{INSTALL_COMMAND}}
```

命令先在私有临时目录下载固定入口、核对独立写死的 SHA-256，通过后才执行 Node；入口继续验证安装资源。完成后重启酒馆，在扩展设置打开快速 V。原版完整流程的环境、锁、空间、分片及总摘要、归档和回滚校验保留。

## 4. 酒馆助手播报导入

手机点击下载[脚本导入 JSON](https://github.com/3086013261qq-hue/dona-QuickV/releases/download/v0.1.0-beta.1/dona-broadcast.tavern-helper.json)，进入 **酒馆助手 → 脚本库 → 全局脚本 → 导入**，选择下载的 JSON，再手动启用「dona快V · 战术播报」。官方导入器是文件选择器，不承诺粘贴网址即可导入。

固定版本 CDN：[导入 JSON](https://cdn.jsdelivr.net/gh/3086013261qq-hue/dona-QuickV@v0.1.0-beta.1/frontend/broadcast/imports/v0.1.0-beta.1.json)。若浏览器显示 JSON，先下载/保存再导入。加载器使用 GitHub + jsDelivr 固定标签，启用时只下载一次并核验播报源码，不轮询更新，不含本体安装逻辑。本体未安装时不会伪造状态或 Token。

## 5. 更新与版本检查

再次执行第 3 节 install 命令会检查文件指纹；同版本无需重复安装或下载运行环境。未来版本使用其 Release 中的新固定命令，不跟随 main/latest 自动执行。

只检查当前状态：

```sh
{{STATUS_COMMAND}}
```

播报更新：关闭旧项，下载新测试版 JSON 并导入启用，确认后删除旧项。每版固定源码，不静默切换。

## 6. 卸载与回滚

**只卸载播报：**在酒馆助手中关闭/删除脚本，必要时刷新酒馆。它会移除自身浮窗、样式、监听和计时器，原版提示和操作一直保留。

**恢复原版 Quick V 0.6.5：**先在原面板停止服务，再运行：

```sh
{{RESTORE_COMMAND}}
```

只恢复本测试版修改的静态文件并移除新增 dona 模块，不卸载 Quick V、不删除整个酒馆目录、不修改凭据和配置。完成后重启酒馆，按需关闭播报。可捕获的替换错误会恢复本次更改前的文件；断电/系统强杀恢复仍待真机验证。

## 7. 常见错误

- **HTTP 403/资源失败：**GitHub 与原作者运行资源是不同来源。全新安装需要作者恢复正式资源或提供对应固定摘要的正式备用地址，不能用皮肤覆盖解决；见[资源清单](docs/resources.md)。
- **环境不符：**先启动酒馆，从 SillyDroid 设置打开内置终端，不要使用 Termux/电脑。
- **仍在运行：**在原快速 V 面板停止，等待退出，不要删除运行锁。
- **SHA-256 不符：**停止并核对版本与下载完整性，不修改期望摘要强行运行。
- **存在本机修改：**为保留修改已停止。保存自己的修改，按已核验原版方式修复后再测试。
- **播报不出现：**确认脚本启用、同源父页面和本体存在真实请求。空闲默认隐藏，播报不能代替本体安装。

## 测试与开发

[自动化结果与安卓待验证](docs/testing.md)。全新安装当前为**资源阻塞**，未验收通过；分支不合并 main。开发构建 `python tools/prepare_beta.py`；检查 `python tools/audit_release.py`；发布预览 `python tools/publish_release.py --preview`。原始安装器及解包文件不提交 Git，获授权二改产物只上传 Releases。

另见[详细安装/更新/卸载](docs/installation.md)、[资源状态](docs/resource-status.json)、[播报契约](docs/broadcast-spec.md)。
