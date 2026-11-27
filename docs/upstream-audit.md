# 原版功能总审核 / 2026-11-27

## 证据与范围
- PC: [README](https://github.com/bad-woman/vertex2openai/blob/main/README.md), [main.py](https://github.com/bad-woman/vertex2openai/blob/main/app/main.py), [model_capabilities.py](https://github.com/bad-woman/vertex2openai/blob/main/app/model_capabilities.py), [resumable.py](https://github.com/bad-woman/vertex2openai/blob/main/app/resumable.py), [LICENSE](https://github.com/bad-woman/vertex2openai/blob/main/LICENSE)。本轮读取 main 分支 README、LICENSE 及后三个 Python 文件开头；并非完整桌面源码差异审计。PC 的功能表述以 README 声明为准，真实运行未验证。
- Mobile: install-0.6.5.cjs SHA256 95f944ba5483e8953bab59a8962cc04d5517fddee6f5913a1054d16db6137db5；RELEASE.files 32 项全部校验通过；appOverlay 241159 bytes，SHA256 ba03dfdfb075675b16f558252a10374417de57b79d24594143bd8c0ddc886a77，静态解包成功。移动端基线 6bb56f90acc40a0f3762c24ccc010d77c3b6970a。外置 codeBundle 30430784 bytes 未获取，Android runtime 未实测。未运行安装器。
- MIT 上游署名 Copyright (c) 2025 gzzhongqi；手机作者授权范围须留存。当前不复制未确认许可的手机源码到 GitHub。

## 功能清单
| 模块 | PC 现行文档/源码 | 手机 0.6.5 证据 | dona 决策 |
|---|---|---|---|
| OpenAI 兼容 API | chat/completions, models | overlay/app/routes/chat_api.py, models_api.py | 保留官方 API 接入及授权校验 |
| 模型能力 | 模型独立思考、采样、生图尺寸、输出上限 | overlay/app/model_capabilities.py, plugin/lib/thinking-settings.cjs | 能力驱动 UI；按实际可用模型显示 |
| 流式、非流式、保活 | README 明示 | chat_api.py, resumable.py | 保留；测试停止、错误和去重 |
| 续传 | README / resumable.py | chat_api.py 含缓冲查询；failure-client.js 管理失败状态 | 前端端到端续传尚需验证，不把故障重试等同续传 |
| 工具调用、消息格式 | README 明示函数调用和预填充兼容 | overlay/app/message_processing.py, schema_validation.py, signature_store.py | 回归合法消息、签名及工具；不改内容安全规则 |
| 日志、用量 | README 声明日志、Token 统计 | overlay/app/logger.py, diagnostics.py | 显示真实指标、脱敏；缺指标明确不可用 |
| 等待与故障 | README 描述异常分类 | plugin/lib/wait-settings.cjs, failure-status.cjs; extension/wait.js, failure-client.js, failure-notice.js | 保留计时和状态提示，前端视觉统一 |
| 服务生命周期 | Docker | plugin/lib/supervisor.cjs, launch.cjs, runtime/runtime-v1/watchdog.py | 保留安卓专有守护逻辑，验证进程退出 |
| 酒馆集成 | 独立控制台 | extension/index.js, connect.js | 前端适配原控件；不重新实现凭据管理 |
| 设备上下文 | PC 文档未显示 | extension/device-context.js | 仅展示必要的本地状态，不上传设备信息 |
| 安装维护 | Docker/持久化目录 | install 脚本下载、归档验证、安装事务、运行时复用 | 保留校验及回滚；增量更新待实测 |
| 凭据 | PC 文档另列认证模式 | plugin setup/cookie-setup | 现有安装独立管理原配置；美化层不读写凭据、不新增认证或转发机制 |

## 非首发任务：历史优化候选
以下仅为记录，不是美化项目必做事项。首发不改后端，只有实测缺陷或明确需求才重新评估。
1. 缓冲容量：mobile resumable.py append 与 store _evict_locked 分离；检查单任务与全局内存硬限制、清理时机。默认 TTL 1800 秒、200 streams。先写长文本压力测试，再调整。不得丢已确认正文而显示成功。
2. 轮询：extension/failure-client.js POLL_MS=750；panel app.js 常规状态轮询 10s、操作忙碌 2.5s，visibilitychange 已停止若干轮询。因此不重复实现已有功能；测试聊天失败轮询后台行为，按状态退避并清理计时器。
3. 生命周期：区分主动取消、短时断网、页面隐藏、服务进程被杀；安卓进程被杀后不保证原生成任务可恢复。
4. UI：对现有 ID、iframe/同源边界做兼容测试；只覆盖 CSS 与展示逻辑；明确主题卸载及恢复。
5. 安全：本地服务监听限制、强认证、CSRF、日志脱敏、版本完整性；前端不存储凭据。遵守官方 API 的授权、配额和错误语义。

## 非结论
未获得完整移动依赖包，未运行安卓、未逐行对照 PC main 与 pinned commit；模型列表是项目声明而非官方可用性证明。内存、功耗、速度改善需有实测数据。
