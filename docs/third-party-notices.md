# 上游版权与授权说明

管理面板名称为「快速 V 0.6.5 · dona美化」，美化版本独立为 `0.1.0`；独立脚本称「dona快V · 战术播报」。dona 仅为本项目视觉与状态展示适配署名，不冒称原后端作者。

PC 兼容性参考：[bad-woman/vertex2openai](https://github.com/bad-woman/vertex2openai)。本次沿用手机安装器固定的上游提交 `6bb56f90acc40a0f3762c24ccc010d77c3b6970a`，没有把 PC main 的新功能移植到手机版。该提交的 [MIT LICENSE](https://github.com/bad-woman/vertex2openai/blob/6bb56f90acc40a0f3762c24ccc010d77c3b6970a/LICENSE) 标明 `Copyright (c) 2025 gzzhongqi`。这里引用的是许可证署名，不据此推测手机二改作者身份。

手机 Quick V 0.6.5 由用户提供原版安装器。2026-11-27 仓库所有者明确确认允许将完整二改 CJS 及包含其的 ZIP 公开发布，授权由其留存，记录于 release-policy.json。二改内所需升级/恢复静态源码作为同一授权交付的一部分；不据此扩大第三方运行时二进制的分发权。原始安装器不公开上传。

构建保留全部原版嵌入文件和上游应用代码，只有 `build-report.json` 中列明的面板资源及状态观察适配发生变动。`app/UPSTREAM-LICENSE`、`app/UPSTREAM_COMMIT` 与原版署名文件原样保留，交付目录另附同一份完整 `UPSTREAM-LICENSE`。运行时、原生工具及第三方 Python 依赖仍由原版固定包提供，继续保留其自身声明，不能把本说明当作所有第三方组件的重新授权。

原版安装器和本地解包物不进入 Git，获授权的二改安装器与维护文件只通过 Releases 提供。仓库提交自研安装/发布/云加载脚本、适配规则、测试与文档。原版依赖仍从原作者资源地址取得；当前资源未齐，不用 SillyDroid 宿主 APK 或零散 Termux 包冒充等价运行环境。上游原生与 Python 依赖的许可证、源码提供要求依然适用。

发布审计发现固定原版 `app/cookie_auth.py` 的 BATCH_GRAPHQL_URL 含 Google 控制台前端静态客户端标识。它随原版代码存在，不是用户或本机提供的 Key/Cookie；保留原业务，不改动或试用该标识。扫描仅对该未修改模块的精确文件 SHA-256 记录这一个例外，不放宽其他文件、位置或凭据匹配。未读取、使用或发布本机真实业务凭据。
