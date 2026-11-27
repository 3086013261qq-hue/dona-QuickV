# 全新安装资源核查 / 2026-11-27

**当前：资源未齐，全新安装阻塞。不能将增量升级通过视为只有 SillyDroid 的手机已可完整安装。**

用户提供的正式发布地址：[https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/sillydroid/install-0.6.5.cjs](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/sillydroid/install-0.6.5.cjs)。从开发环境使用普通 HTTPS GET，不带 Cookie、不伪装来源，返回 HTTP 403/连接错误。这是本次开发端检查结果，不断言所有手机网络均不可访问。未绕过访问限制，也未执行任何原始安装器或下载内容。

## 必需资源与获取方式

需要原作者恢复以下正式下载资源，或提供对应相同 SHA-256 的正式备用渠道。只有文本安装器不足以提供 Python 环境。

| 资源 | 总字节数 | 固定 SHA-256 |
|---|---:|---|
| vertex-local.apk（6 段合并） | 74884755 | `cfa6c63d8f9d70927b4697f3427f4650ac10b731ec276a6c19968f2bc8b6c24f` |
| Quick V codeBundle（3 段合并） | 30430784 | `a92345bdb267eb0a0a02bccbfa3184bd27445d5f3e2abef0533acc902d3b2d9c` |

实际缺失文件及原作者地址（每段还须独立核验）：

| 文件/用途 | 字节数 | SHA-256 | 本次结果 |
|---|---:|---|---|
| [install-0.6.5.cjs](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/sillydroid/install-0.6.5.cjs) · author-installer | 876527 | `95f944ba5483e8953bab59a8962cc04d5517fddee6f5913a1054d16db6137db5` | HTTP 403 |
| [vertex-cfa6c63d8f9d-01.bin](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/assets/vertex-cfa6c63d8f9d-01.bin) · runtime-apk-part | 13631488 | `423fad348112549278f8ef2968ab697ce5cc58d188b1f0782b5738b03da19b18` | HTTP 403 |
| [vertex-cfa6c63d8f9d-02.bin](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/assets/vertex-cfa6c63d8f9d-02.bin) · runtime-apk-part | 13631488 | `c619085589e373ac5a13068dbdabc9232997a449368a75e3ca2ee05f618cfe8f` | HTTP 403 |
| [vertex-cfa6c63d8f9d-03.bin](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/assets/vertex-cfa6c63d8f9d-03.bin) · runtime-apk-part | 13631488 | `0818a63c13d9cf45b5419f24bffbc1c36b2434144085a979ec6dd1147ed5936f` | HTTP 403 |
| [vertex-cfa6c63d8f9d-04.bin](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/assets/vertex-cfa6c63d8f9d-04.bin) · runtime-apk-part | 13631488 | `514a3c9f7844bb76df3b631ad24e7aee7546744a495f8a51a8b37e289f89d549` | HTTP 403 |
| [vertex-cfa6c63d8f9d-05.bin](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/assets/vertex-cfa6c63d8f9d-05.bin) · runtime-apk-part | 13631488 | `9c9d381db21ccac1f460bdc7ae1ac072e3768dc4289fd18aba884de73cc0f47e` | HTTP 403 |
| [vertex-cfa6c63d8f9d-06.bin](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/assets/vertex-cfa6c63d8f9d-06.bin) · runtime-apk-part | 6727315 | `0a8134d4d2fcfecda3840909c0c97c1c029cc454d73ba12d871c3dc2c8c5dfd7` | HTTP 403 |
| [quick-v-code-0.6.1-a92345bdb267-01.bin](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/assets/quick-v-code-0.6.1-a92345bdb267-01.bin) · code-bundle-part | 12582912 | `2c45ccd1d2e6818b68d205943fe13093ba0822197e259ddbbe6a6d0e324e683a` | HTTP 403 |
| [quick-v-code-0.6.1-a92345bdb267-02.bin](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/assets/quick-v-code-0.6.1-a92345bdb267-02.bin) · code-bundle-part | 12582912 | `22910e574e12f35624871c2b98e1c31d94f2a3a38f99b59aa931e6350be6f9f9` | unavailable |
| [quick-v-code-0.6.1-a92345bdb267-03.bin](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/assets/quick-v-code-0.6.1-a92345bdb267-03.bin) · code-bundle-part | 5264960 | `6656c6aa1c64b392493ecd81355dea2e6afe2b37c860f7fa3fae8bd5998f30c2` | HTTP 403 |
| [runtime-source-1.8.zip](https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/sillydroid/runtime-source-1.8.zip) · runtime-source | 2095223 | `d091764778daa7af2aac9be79aadc4474c14dd17b14134ece246d36e0f4ce49c` | HTTP 403 |

`runtime-source-1.8.zip` 是原版清单列出的复现/源码资源，不是全新安装时必需执行的安装脚本；当前也未取得。原始 CJS 仅从用户已提供的本地副本静态核验，不重新公开上传。

## APK 内必须存在的组件

运行 APK 包含 Python 3.12 的 ARM64 rootfs、原生 proot/loader/共享库、旧 app-v1.8 及其 manifest；新 codeBundle 提供 code-v2/app 和 site 依赖，再叠加已验证内嵌 appOverlay。原始清单对 APK 内组件也逐项规定大小和摘要：

| APK 内部路径 | 字节数 | SHA-256 |
|---|---:|---|
| `assets/runtime/rootfs.tar.gz` | 74476025 | `9ead0ca95180174fc7bca24c78fa72d608110af5b6f6815f9f37050d32a30010` |
| `assets/app-code/app.tar.gz` | 154320 | `db644d32bd23f8e7c014fef4ccf3d80c420cd05a0e1683839c2a780397b623e8` |
| `assets/app-code/manifest.json` | 5867 | `853db19eea6bf5206ec39b0007283edbb1ba50c6367acff89f9b4282fd26d83a` |
| `assets/native/arm64-v8a/libandroid-shmem.so` | 14432 | `84475798e07c8174dbbfaec70a827fdb02f19ffa69a589380c13e7507fd0e731` |
| `assets/native/arm64-v8a/libtalloc.so.2` | 33592 | `742b438c4d09e276985a61d44164c9de207b6d8cc268f3018cb3001961bcb309` |
| `assets/native/arm64-v8a/loader` | 18136 | `cbdef0e652c2b78af25d867e1719fdebbb0915e25aae2dd35b3b5c1835f6b551` |
| `assets/native/arm64-v8a/loader32` | 6244 | `c429996fee730e1a4fe12625b22dab5a5bc2847a4cae274d36fd4a19cd8299a8` |
| `assets/native/arm64-v8a/proot` | 247488 | `1545b85b312505db6eb6908ff8b2ded0a77a3bd689c50ae85aa7c1d8445dd717` |

## 正式备用来源与兼容性核查

- [PC 上游](https://github.com/bad-woman/vertex2openai) 当前没有 GitHub Releases；已检查 README 与仓库树，没有核实到该 Quick V ARM64 Python 运行包。
- [SillyDroid 官方仓库](https://github.com/jialmaster/SillyDroid) 的 Release 是酒馆宿主/Node 环境，不是上述 Quick V 专用 Python 包；不能不经摘要和启动兼容审查就替换。
- 原版原生组件声明提供 Termux 正式包 URL 和许可证，但零散 deb 不能替代已固定的 Python rootfs、代码 site 和安装布局；本次不重建或重新分发这些第三方文件。
- 原作者手机二改身份未从仓库署名核实，不按域名用户名推测其他下载站。未找到可证明由手机原作者提供、且满足这些固定摘要的备用渠道。

获取后应运行 `python tools/check_resources.py --download`，核对全部段、合并总包及内层资源，再做安卓 ARM64 真机全新安装。大小不符、SHA 不符、未知镜像、登录页响应都拒绝。不能通过删除校验或伪造环境标记让测试通过。资源和实际安装兼容性未验证前，freshInstallReady 始终为 false。

本测试版包含完整原安装流程入口和升级/恢复工具，但**不包含这些第三方运行资源，不是离线完整运行包，当前不构成已验收的全新安装交付**。
