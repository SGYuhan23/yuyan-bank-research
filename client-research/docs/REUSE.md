# 仓库检查与复用决定 · 2026-10-18

基线：985e862f15061d7176aebf4387bf9d25034fb04c；分支 codex/chongqing-client-research。
原工作区是无远程、未跟踪文件的工作区；本次从指定 GitHub 地址独立 clone，未改原文件。
读取 agent-platform/AGENTS.md，遵循 extension-first，不改 DeerFlow 核心。

| 现有成果 | 判断 |
|---|---|
| research-showcase | 当前 Pages 的模拟客户和资金情景；原样保留，不作为真实企业事实 |
| agent-ops/research/sources.json、fuling_public_facts.json | 行业背景；与本次企业主体不匹配，不迁入事实表 |
| agent-ops/research_policy.py | 复用其实际读取才可引用、预算停止、不猜不存在的策略 |
| agent-ops/research/trace_guard.py | 保留原模块，迁移其“工具结果拥有数值和状态”的控制原则；原函数与账本耦合，不能直接用于企业研究 |
| agent-ops/research_plugin.py | 提供 DeerFlow extension 接入范式；新研究模块独立运行、使用已有 LangGraph 栈，不启用子 Agent |
| 本地 yuqi-core | GitHub 基线没有该目录；借用本机 Qwen 环境变量进行实际验证，不把其源码或密钥复制进仓库 |

新模块 client-research 是单进程、单有界 LangGraph 图；一个模型、只读工具、JSON 文件版本持久化。无向量库、微服务或授信评分。
Pages workflow 和 research-showcase/dist 均不修改。独立页面仅本地预览；静态导出显式标识历史运行。
