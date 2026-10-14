# 渝研：本项目扩展与本地运行

当前业务与作品入口以 [根 README](../README.md)、[DEMO](../DEMO.md) 和 [复算说明](../REPRODUCIBILITY.md) 为准。历史 V1/V2 内部开发结论不随公开包导出。

完整本地安装、环境变量、数据库、模型服务与复算步骤见 [REPRODUCIBILITY](../REPRODUCIBILITY.md)。必须显式配置 AGENT_DATABASE_URL；模型参数可通过进程环境或 YUQI_MODEL_ENV_FILE 指定的本地 dotenv 文件提供。runtime.py 仍保留可选旧路径查找，但旧 yuqi-core 源码不是运行依赖。账号文件只放在被忽略的 .deer-flow/acceptance 中。

当前 Agent 扩展及既有媒体/查证工具全部保留；既有文件工具使用 Docker AIO 沙箱镜像 `enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:1.11.0`，需用户自行获取。Agent 框架来自 DeerFlow，并非本项目从零自研。贡献边界见 [CONTRIBUTIONS](../CONTRIBUTIONS.md)。

当前完整源码可以本地配置运行，未部署公网。业务已冻结，不增加 Agent、RAG 或模型。
