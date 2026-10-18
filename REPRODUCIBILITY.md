# 本地复现

按照根 README 的锁文件安装和配置步骤启动。运行环境使用 Python 3.12、Node 22+、pnpm 10.26.2、PostgreSQL 17 和 Docker AIO 1.11.0。

## 离线回归

```bash
agent-platform/backend/.venv/bin/python -m pytest agent-ops/test_delivery_guard.py agent-ops/test_configuration.py agent-ops/test_research_policy.py agent-ops/test_media.py agent-ops/test_diagram.py agent-ops/test_web_fetch.py agent-ops/test_web_research.py agent-ops/test_local_interaction_policy.py -q
cd agent-platform/frontend
pnpm typecheck
pnpm exec next build --webpack
```

离线测试含显式测试替身；不是模型质量成绩。

## 真实运行验收

启动服务后执行 `agent-ops/live_acceptance.py`，检查登录、上传、模型调用、两轮计算和文件交付。脚本使用既有本地验收账号；干净实例会初始化专用本地测试管理员，凭据只保存到被忽略的 `.deer-flow/acceptance/account.json`。已有管理员但没有该文件时，请先配置专用测试账号，不在聊天或日志暴露凭据。

其他验收脚本：`security_acceptance.py`、`run_control_acceptance.py`、`diagram_acceptance.py`、`media_acceptance.py`、`research_acceptance.py`。图形自定义助手验收需要先导入 `yuyan.agent.json`；图片与联网验收会消耗已配置模型额度。不得将脚本退出成功等同输出质量通过，必须同时检查文件和工具记录。

`recovery_check.py before` / `after` 用于完成任务的Gateway重启持久化核查，不等于运行中强杀恢复或跨机器恢复演练。

旧研究业务的复算代码保留于 `agent-ops/research/`，其历史报告和发布清单不作为当前通用Agent的质量证明。
