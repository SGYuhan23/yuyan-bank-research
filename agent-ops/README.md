# 渝研 Agent 运行装配

当前主产品是中文通用 Agent；安装和启动见 [根 README](../README.md)。默认工具为网页检索与读取、文件读写、沙箱代码执行、图片生成/编辑和图形生成。

`delivery_guard.py`：明确文件请求的交付核验和有界续跑。
`research_policy.py`：普通事实查证策略。
`extensions.json`：通过框架的配置中间件机制加载上述策略。
`config.qwen.yaml`：默认不加载银行业务插件，模型与预算显式配置。
`start.py`：启动数据库、Gateway和原Next.js工作台；`scripts/start_general_agent.py` 负责加载私有本地设置。

研究和业务案例源码保留，不是默认任务入口。实际验证结果见 [验收记录](../docs/AGENT_ACCEPTANCE.md)。
