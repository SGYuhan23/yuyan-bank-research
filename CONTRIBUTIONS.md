# 本人实现与上游边界

“本人”指本个人作品的实现与集成工作，不代表从零实现全部依赖。项目以 DeerFlow 固定上游为基础；DeerFlow / LangGraph、认证、会话、沙箱及前后端通用基础不属于本人原创框架。原始许可证保留，见 [ATTRIBUTION](third_party/ATTRIBUTION.md)。

## 最值得 review 的 12 个文件

| 文件 | 归属与本人工作 | 建议检查 |
|---|---|---|
| [fuling.py](agent-ops/examples/fuling.py) | 本项目新增经营研究；合成客群、分动作业务驱动估值与工时优化；保留历史兼容函数 | 不是所有动作都按余额估值；约束、成本与停止条件 |
| [supplier_ledger.py](agent-ops/research/supplier_ledger.py) | 本项目新增合同与事件计算 | FIXED_DATE / AFTER_INVOICE、PROJECTED / CONFIRMED / POSTED、原子核对 |
| [ledger_store.py](agent-ops/research/ledger_store.py) | 本项目新增 PostgreSQL 业务持久化层，复用数据库与平台身份设施 | 幂等、版本冲突、账户隔离、事务回滚 |
| [scenario_request.py](agent-ops/research/scenario_request.py) | 本项目新增请求语义与确认快照 | 客户、参数、case/version 和确认状态绑定 |
| [trace_guard.py](agent-ops/research/trace_guard.py) | 本项目新增最终金融回答守卫 | 成功工具结果生成受控文本，防止金额/状态被自由改写 |
| [research_plugin.py](agent-ops/research_plugin.py) | 基于上游 extension API 新增银行研究工具/API | 提案与确认权限分离、工具调用边界 |
| [research_policy.py](agent-ops/research_policy.py) | 本项目扩展中间件，复用上游 Agent 生命周期 | 查证策略、模型输入与最终回答边界 |
| [research/page.tsx](agent-platform/frontend/src/app/workspace/research/page.tsx) | 在上游 Next.js / 认证 / 布局基础上新增研究页面 | 两案例交互、快照确认、输入变更使旧结果失效 |
| [test_fuling_v2.py](agent-ops/test_fuling_v2.py) | 本项目新增经营模型测试 | 同余额不同业务特征、行业约束改变任务选择 |
| [test_supplier_ledger.py](agent-ops/test_supplier_ledger.py) | 本项目新增账本确定性测试 | 合同依赖、状态不可混、余额不符整体回滚 |
| [test_scenario_semantics.py](agent-ops/test_scenario_semantics.py) | 本项目新增参数语义测试 | C1/14 与 ALL/30 不能冒充同一请求 |
| [build_v2.py](agent-ops/research/build_v2.py) | 本项目新增当前版本数据装配；前端与报告共享结果 | 公开事实、合成输入与模型输出的来源链 |

其他本项目源码包括报告生成、公开 trace 白名单、发布边界测试、既有媒体与查证扩展和本地启动脚本。根目录文档、采集脚本和公开打包规则属于 portfolio 整理工作，不是新的银行业务功能。

## 本人改造

在上游保留的组件上进行中文品牌、导航、研究入口、产物体验与既有交互策略适配。不会将完整 auth、sandbox、会话持久化、流式执行、工具体系或 UI 组件库标为本人从零实现。可结合固定上游提交 `5b2a1352cd67d5577ebf027b9f920e7ef1e360d4` 核对边界；公开包不携带旧 `.git` 历史。

## DeerFlow upstream

完整 `agent-platform/backend` 与 `frontend` 基础、harness、extension-api、skills、contracts、锁文件、上游 tests 与许可证按依赖保留。某些上游生成 fixtures 仍被源码和测试读取，因此不会仅为缩小体积删除。

## 早期 / 非当前主流程

`yuqi-core` 是未接入的早期独立实现，不在当前业务 import 链中，本次从公开包排除，原工作区历史未删除。runtime.py 的旧 dotenv 查找只是可选配置来源，显式环境变量或 YUQI_MODEL_ENV_FILE 可替代。历史 V1/V2 中间产物、过期测试汇总和开发计划已从 public export 排除，不作为当前经营结论。

既有 examples / 媒体工具保留其当前功能和源码，不与两项银行 Case 并列宣传。本次没有修改核心业务逻辑、Final numbers、截图或录屏。
