# 渝研｜产业经营研究

先理解生意，再安排金融服务。以公开资料建立产业背景，用模拟客户与收付计划研究银行服务顺序和企业现金时点。

**[打开交互研究页](https://sgyuhan23.github.io/yuyan-bank-research/)** · [三分钟演示](DEMO.md) · [下载研究报告](research-showcase/dist/渝研_产业经营研究报告.pdf) · [复算说明](REPRODUCIBILITY.md)

## 当前两个案例

**涪陵榨菜客户经营**：合作社、加工企业、经销商三个客户原型，比较付款紧迫性、核查材料、工时和停止条件。本周18小时先安排经销商6小时、合作社8小时，留4小时补件；新证据可以改变排序。不计算未经校准的银行收益排名。

**汽车供应商资金周转**：比较现金、持票到期、次日贴现成功和现金晚14天。四种情景峰值缺口均为56万元，负余额期分别为94、185、95和108天；贴现成本为6,627.95元。这些都是模拟输入下的研究结果，不是实际企业表现或银行报价。

页面无自由输入、无实时模型调用。经营情景是预设分析路径；汽车情景经参数确认后展示对应的确定性结果，不把预设文字包装成模型推理。公开来源、适用范围与模拟数据边界保留在“研究报告与依据”中。

当前页面、报告、数据及复算源码位于 [research-showcase](research-showcase/README.md)。Pages 仅部署该目录的 dist，不混合旧版案例或报告。原后端、Agent、计算引擎和历史研究材料继续保留，属于原项目技术实现，不代表当前三个客户原型与56万元案例。

## 保留的原项目源码

这是完整源码作品仓库。保留 agent-ops / agent-platform 目录结构，不为展示重排 imports；依赖、运行账号与密钥由使用者在本地配置。

| 路径 | 作用 |
|---|---|
| [agent-ops/examples/fuling.py](agent-ops/examples/fuling.py) | 合成客群、按业务驱动估值的候选动作、工时与行业约束优化；保留明确的历史兼容代码 |
| [supplier_ledger.py](agent-ops/research/supplier_ledger.py) | 合同支付依赖、事件状态、现金曲线、原子收付核对及只读情景计算 |
| [ledger_store.py](agent-ops/research/ledger_store.py) | PostgreSQL 持久化、账户隔离、幂等、版本控制、确认快照存储 |
| [scenario_request.py](agent-ops/research/scenario_request.py) | 绑定请求、客户、参数、确认状态与账本版本 |
| [trace_guard.py](agent-ops/research/trace_guard.py) | 从成功工具结果生成受控回答，防止自由文本改写金额或状态 |
| [research frontend page](agent-platform/frontend/src/app/workspace/research/page.tsx) | 两个案例的真实交互界面；读取 Python 结果并调用账本接口 |
| [research_plugin.py](agent-ops/research_plugin.py) / [research_policy.py](agent-ops/research_policy.py) | 本项目 Agent 工具、API 扩展及回答边界 |
| [agent-ops/test_*.py](agent-ops/) | 确定性模型、合同依赖、账本、语义、发布边界与集成测试 |
| [build_data.py](agent-ops/research/build_data.py) / [build_reports.py](agent-ops/research/build_reports.py) | 标准库数据构建与报告生成 |
| [portfolio_verify.py](scripts/portfolio_verify.py) | 公开仓库发布快照的文件哈希核对 |
| [agent-platform/frontend](agent-platform/frontend) / [backend](agent-platform/backend) | 完整前后端、Agent 运行环境与本项目业务扩展源码 |

完整目录见 [Repository Structure](docs/PUBLIC_REPO_TREE.md)。

[原版浏览器 Demo 实现与一致性测试（历史案例，不是当前展示）](site/README.md)

## 本地运行

[复算与本地运行说明](REPRODUCIBILITY.md) 提供数据构建、测试、报告生成与完整平台启动步骤。独立复算不需要模型密钥或数据库；完整交互平台在本地运行。当前研究页展示预先由 Python 生成的情景结果，不提供后端服务。

## 技术栈

Python 负责确定性业务计算与接口，PostgreSQL 保存账本状态，Next.js / React 提供完整本地交互；Qwen 用于自然语言理解与解释，Agent workflow 负责问题理解、参数确认、工具调用和结果组织。原版浏览器 Demo 的 React / TypeScript / Vite / Ant Design 与独立 JavaScript 计算引擎继续保留；当前公开入口使用 research-showcase/dist 中的静态研究页。

[架构与责任划分](ARCHITECTURE.md) · [第三方说明](third_party/ATTRIBUTION.md) · [DeerFlow 许可证](agent-platform/LICENSE)
