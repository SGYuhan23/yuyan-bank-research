# 渝研｜银行经营分析与产品研究

一个围绕县域客户经营和制造业供应商资金管理的个人研究与产品项目。

我尝试回答两个问题：

- 客户经理时间有限时，哪些客户机会更值得先验证？
- 企业已经有订单，为什么过程中仍然会出现现金缺口？

**[查看项目展示](https://sgyuhan23.github.io/yuyan-bank-research/)** · **[查看完整案例](DEMO.md)**

| 县域客户经营：时间有限，先跟进谁？ | 供应商资金管理：有订单，为什么还缺钱？ |
|---|---|
| [![县域客户经营页面](docs/screenshots/01-fuling-overview.png)](DEMO.md#县域客户经营) | [![供应商资金管理页面](docs/screenshots/04-supplier-overview.png)](DEMO.md#供应商资金管理) |

## 两个案例

**县域客户经营**：交易频繁的客户可能适合结算服务，员工多的客户可能适合代发。项目把这些业务差异转成待验证的任务，再比较时间有限时先做哪些。合成实验中，150 小时下加入资源分散约束，假设净贡献从 45,027 元变为 44,205 元；822 元是模型中的取舍，不是实际业绩。

**供应商资金管理**：订单最终回款 96 万元，过程中却有 49 万元的峰值资金缺口。核心客户晚付款 14 天，峰值不变，负余额时间从 38 天延长到 52 天。资金风险不仅是差多少钱，也包括要撑多久。

[阅读研究报告](docs/reports/README.md) · [数据与使用边界](DISCLAIMER.md)

## 项目设计

公开事实用于理解地区与产业背景；客户和订单使用合成数据。AI 理解问题、整理资料和解释结果，程序计算金额、日期、现金流与资源安排，人负责确认输入和经营判断。

例如，用户问 C1 客户晚付款 14 天，不能拿所有客户晚 30 天的结果回答。系统先展示理解出的参数，确认后计算；修改输入后，旧结果失效。

## 界面预览

[完整图文案例](DEMO.md) 展示任务选择、合同条件和余额核对。截图来自真实本地页面，GitHub Pages 是静态介绍，无需账号。

可选：[概览录屏](docs/media/overview.mp4) · [客户经营录屏](docs/media/fuling.mp4) · [供应商与 AI 录屏](docs/media/supplier-ai.mp4)。录屏保留了当时的界面文字，业务计算与图文案例一致。

## 源码结构

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
| [portfolio_verify.py](scripts/portfolio_verify.py) | 当前完整公开仓库的文件与计算结果核对 |
| [agent-platform/frontend](agent-platform/frontend) / [backend](agent-platform/backend) | 完整前后端及 Agent framework 源码，不是只有页面截图 |

完整目录见 [Repository Structure](docs/PUBLIC_REPO_TREE.md)。

## 本地运行

[复算与本地运行说明](REPRODUCIBILITY.md) 提供数据构建、测试、报告生成与完整平台启动步骤。独立复算不需要模型密钥或数据库；完整交互平台在本地运行。线上仅提供静态展示页，不提供后端服务。

## 技术栈

Python 负责确定性计算与接口，PostgreSQL 保存账本，Next.js / React 提供本地交互界面。Agent 扩展基于 DeerFlow / LangGraph，可接入 Qwen。静态展示使用原生 HTML / CSS。

[架构与责任划分](ARCHITECTURE.md) · [第三方说明](third_party/ATTRIBUTION.md) · [DeerFlow 许可证](agent-platform/LICENSE)
