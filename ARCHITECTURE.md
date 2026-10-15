# 架构：把解释、计算和决策分开

两个案例先作为独立经营研究与产品原型成立，再通过 Agent 提升资料整理和解释效率。关闭模型、DeerFlow 或 LangGraph，仍可运行确定性数据构建与模型测试。

```mermaid
flowchart LR
    U[用户问题] --> L[LLM：理解 / 搜索 / 参数提议]
    L --> P[ScenarioRequest 提案与校验]
    P --> H[Human：逐项确认参数]
    H --> T[Deterministic Engine]
    T --> R[绑定参数快照与账本版本的结果]
    R --> E[解释 + 最终受控回答]
    E --> D[Human：经营判断 / 授信审批]
```

| 责任 | 承担的工作 | 不应该承担的工作 |
|---|---|---|
| LLM | 理解问题、搜索与整理资料、提出结构化参数、解释 | 自行计算金额或暗中补齐歧义；替人确认 |
| Deterministic Engine | 整数分金额、日期依赖、现金流、工时资源优化、校验、快照绑定 | 将合成输出宣称为银行业绩或信用决策 |
| Human | 确认测算参数、核验材料、经营判断、授信与风险审批 | 把参数确认当作真实合同已落实 |

## Fuling：不把所有动作都写成余额乘系数

`prototypes → candidate_actions → optimize_resources → v2.json → research page / PDFs`

结算由年交易笔数驱动，代发由员工数驱动，供应链由合格连接数驱动，维护由既有关系贡献与流失情景驱动；余额用于存款动作。动作有成本、工时和停止条件。单客户互斥、5 小时粒度与行业实际分配工时上限均由 Python 计算；前端选择已有情景，不另写金融公式。

## Supplier：状态、条件与事务

`research page / tool → research_plugin → ledger_store → supplier_ledger → PostgreSQL`

- 固定日与开票后支付分开；只有 PROJECTED 允许沿条件链重推日期。
- CONFIRMED 不等于现金；POSTED 不可覆盖。争议会使依赖预测不完整。
- 实际收付与余额核对在事务副本执行，匹配才整体提交；版本冲突与幂等键防止重复或过期写入。
- ScenarioRequest 明确提案、确认、版本与参数；工具不能用另一个情景冒充原请求。最终受控回答由 `trace_guard.py` 根据成功工具结果生成。

## 完整平台与本项目扩展边界

`agent-platform/` 是 [DeerFlow](https://github.com/bytedance/deer-flow) 的固定上游源码快照及本地适配，保留完整 Next.js 前端、Python 后端、LangGraph harness、工具与扩展机制。上游框架、认证/会话/沙箱/流式执行等基础设施不是本项目从零自研。

本项目主要新增：`agent-ops/` 中的经营模型、供应商账本、ScenarioRequest、扩展 API/工具、回答边界、数据与 PDF 构建、测试；`agent-platform/frontend/src/app/workspace/research/page.tsx` 的研究界面及导航、中文品牌适配。另有既有媒体/查证扩展和历史 examples，源码保留，但不扩充本次银行作品的业务范围。

准确上游提交与归属见 [ATTRIBUTION](third_party/ATTRIBUTION.md)。源码包无旧 `.git` 历史；保留 commit 标识用于归属核验，不是迁移原仓库历史。

## GitHub 展示与本地执行

GitHub Pages 浏览器 Agent Demo 与 GitHub 文档、真实截图和报告构成公开入口，不需要在线后端。录屏使用本地 Next.js + Gateway + PostgreSQL；登录账号和运行数据不公开。只有自行运行完整平台时才需要配置数据库与模型服务。

当前公开仓库包含完整功能源码与依赖锁文件，不含已安装依赖、私有运行状态或生产部署承诺。早期 `yuqi-core` 未被当前银行案例或平台 import，已从公开包移除；旧 dotenv 默认查找路径可通过显式环境变量或 YUQI_MODEL_ENV_FILE 覆盖，不需要该旧目录。

## 浏览器执行适配

`site/` 使用 React / TypeScript / Vite / Ant Design 和 HashRouter。四个受控完整问题由场景预设提供参数，不开放自由文本输入；确认后的参数与账本版本绑定，追加问题立即标记旧结果失效。Fuling 分组背包、Supplier 逐日现金流、合同依赖和原子核对在浏览器运行，通过动态 Python 对照验证，Python 仍为计算依据。当前引导演示状态仅保存在内存中，重新进入案例即重置。

历史 Qwen 脱敏记录独立展示为调用回放，不能冒充当前输入的新模型调用。Pages 不提供实时模型服务。构建与一致性测试在 GitHub Actions 执行，不向浏览器部署 Python 或测试答案。
