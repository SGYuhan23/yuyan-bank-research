# 已实现 / 未实现

## 当前收尾状态

当前分支codex/antifraud-tools-upgrade，已有训练型两层GraphSAGE。完整答案与来源展示、结果哈希、独立人工修订、18变体事实/初始信息一致性已实现；本轮80项回归通过。正常业务、投资条件及语义复盘仍有漏判，不宣称全场景可靠。详见[本轮实测与残留](../eval/final-closeout-v1/REPORT.md)。以下为历史阶段记录，后续记录优先，不代表当前仅两个入口或没有GNN。

## 已实现并有实际记录

- 在`codex/antifraud-rag`隔离新增模块，复用现有Qwen接入、LangGraph与引用检查思路，未修改产业研究结果、通用Agent、渝惠或线上部署。
- 官方原始网址资料采集和读取；直接HTTP失败保留403；工具取得章节时明确哈希口径，日期未知不补造。
- 银行公开指引、官方公开案例、官方统计、项目研究建议和项目编写培训情境分存。
- 5个完整检索单元，默认BM25无命中转真实embedding检索，保留两种显式模式；同一11题检索测试，不使用参考答案生产检索。
- 任务→检索→充分性/冲突→确定性计算→生成→引用与支持性检查的单LangGraph流程。
- 一项Decimal同比计算，输入来自已检索统计表；引用单元ID由程序附完整原文；失败保留草稿。
- 两个任务的真实模型输出；生成情境固定标识项目编写、待人工审核。
- 最小本地界面两个入口，显示正文、对应原文与可打开URL、待确认事项、培训审核状态；执行步骤来自真实运行。

## 未实现 / 无法验证

- 材料包10个来源已比对，生产覆盖仍仅5个完整单元；S9/S10获取失败，S1未下载原始PDF字节，不能确认包内哈希与全26条事实。
- 无银行内部操作规程，不能提供Westpac内部冻结、签字或时限政策。
- 尚无独立银行人员事实签核、盲评或客户试点。模型评审有已确认漏判，不能用作准确率宣传。
- 语义支持与适用条件保留不完备；针对“任何/所有付款”和收款账户已被控制的断言添加有日志的条件修复，但同模型评审仍会漏判。越权安全保证问题有时只拒绝、遗漏可提供的核实步骤，实际失败记录保留。生成内容需要人工审核，暂无人工审批后台，仅展示待审核状态并可导出。
- 没有通用统计计算器；仅支持已核验表格中的payment redirection 2025/2024同比。没有混合检索、重排或向量数据库，因为本次小样本未显示必要性。
- 生产RAG不在线自动爬取新网址；原始资料更新需要重新采集、审核并重建单元。直接获取受站点403限制的页面，需使用可用的网页读取工具重新获取，而非将失败当成功。
- 不提供交易拦截、风险评分、账户冻结或自动客服考核；无银行系统连接、账户权限或业务动作。
- 未部署公网、未合并分支、未覆盖GitHub Pages。页面需要本地模型服务，不把静态回放伪装为实时RAG。

## 运行记录说明

`runs/`保留实际检索、模型用量、充分性、计算、草稿、修复与失败。未保存模型隐藏思维链。评测调用发生在生产结果完成后，记录phase=evaluation_only_rubric_judge，不能混称生产步骤。最终全量复测每次运行保存pipeline-source.py及导入时源码哈希；早期迭代边运行边修改时的哈希仅表示创建记录时文件状态，不能用于精确重建当时内存版本。

## 两项收尾

默认网页/API/CLI统一auto检索，记录尝试、兜底原因及来源ID；语义失败直接失败，不能报告无资料。对bec-case特定金额关系增加确定性恢复及生成/审核提示，覆盖引用该案例且含17,000/30,000或1.7万/3万的步骤、风险线索；不覆盖任意数字表述、所有自由文本或其他案例，不是通用财务语义校验。详情与真实运行见CLOSEOUT.md。

## 场景范围修复

已删除“付款记录”触发的供应商整句模板及固定付款短语替换。新增轻量场景/对象/条件字段、用户原话依据、当前场景适用原文段落，以及逐条审核约束；比较任务可包含多个场景。核心场景之外仍无通用语义保证，同模型审核可能漏判，最终材料仍待人工审核。最新验收见SCOPE_CLOSEOUT.md。

## 独立工具升级分支（2026-10-19）

`upgrade/` 在保留原固定流程基础上新增版本化案件、受限条件工具、交互培训和独立合成交易实验。新界面是真实本地接口，历史页面仍在 `/legacy`。本轮实际运行、失败、外部依赖和未实现范围以 [UPGRADE_VALIDATION.md](UPGRADE_VALIDATION.md) 为准，不能把旧运行归为新工具成绩。

### 2026-10-20 integration follow-up

Implemented: Agent task-source coverage retry, exact source-span binding in focused output checks, bounded contract/answer repair, removal of unsupported optional material, frontend actual retrieval-path labels. Legacy zero-hit fallback and known-case loss rule retained. Verified: 64 offline tests, real embedding comparison, two historical-error substantive checks, fresh actual model outputs and browser workflow. See `../eval/repair-v2/REPORT.md` for IDs, first failures and residual source-review rejections. Not verified: general semantic correctness, superior accuracy/efficiency, bank use. Resume evidence is in RESUME_EVIDENCE.md; no personal background fields were changed.

### Learned graph follow-up

Now implemented and actually trained: two-layer mean GraphSAGE, three initialization seeds, validation-only checkpoint choice, neural no-neighbor-message ablation, group-disjoint split audit, JSON checkpoint export with Torch/numpy parity. Optional training dependency, existing numpy inference. Shared-case analyst exercise links raw synthetic transactions, graph/score tool results, top10% shortlist, incident-edge IDs, project-authored questions and persisted review/export. It is a deterministic exercise route within the existing Agent, not an extra LLM/multi-agent service. 75 local tests pass; actual browser and training reproduction in eval/graphsage-v1. Original synthetic-distribution gain does not survive structural challenge reliably; conservative default unchanged. Prior RAG semantic limitations, no actual bank integration/authentication and absent private transaction data remain unchanged.
