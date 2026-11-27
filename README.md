# dona-QuickV

Quick V 0.6.5 手机优先私有二改：沿用仓库现有明日方舟风格面板与独立酒馆助手播报，不重写原业务后端。

管理面板：「快速 V 0.6.5 · dona美化」，美化版本 `0.1.0`。独立脚本：「dona快V · 战术播报」。保留原作者声明与上游许可证。

将获授权的原始 `install-0.6.5.cjs` 放在根目录，然后：

```powershell
python tools/build_release.py install-0.6.5.cjs
python -m unittest discover -s tests -v
node --test tests/security.test.cjs
python tests/browser_qa.py
```

只静态解析安装器，生成文件位于 `.local/release/`；原安装器与含上游源码的产物不提交 Git。本次未运行安装器、未调用真实模型、未进行安卓真机测试。生成安装器沿用原版受校验的联网依赖下载，不是离线 APK。

- [安装、更新、卸载与回滚](docs/installation.md)
- [测试结果与真机待验证事项](docs/testing.md)
- [播报状态、统计与权限契约](docs/broadcast-spec.md)
- [上游版权与授权说明](docs/third-party-notices.md)

开发测试依赖为 Python 3.12+、Node.js 18+、固定版本 Playwright 与 Chromium；详见安装说明。
