# 新增验证模块：银行反诈知识与培训辅助 Agent

本分支在保留产业研究成果的基础上新增两个RAG任务：知识问答与培训材料生成。

- [运行与启动](antifraud-rag/README.md)
- [官方来源索引](antifraud-rag/docs/SOURCES.md)
- [实际评测及失败样例](antifraud-rag/docs/EVALUATION.md)
- [已实现 / 未实现](antifraud-rag/docs/IMPLEMENTATION_STATUS.md)

未合并、未部署；公开指引不等于Westpac内部规程，培训材料待人工审核。

---

# 渝研｜重庆产业客户研究 Agent

面向银行对公客户经理的访前研究：**企业最近发生了什么，这些变化可能对应什么服务方向，哪些有证据、哪些必须见面核实？**

本分支把重点转向真实重庆制造企业的公开资料、经营判断与 AI 研究工具。完整旧成果继续保留，未覆盖 GitHub Pages 线上版本。

- [新版静态演示：固定研究流程与启动说明](client-research/docs/FIXED_WORKFLOW.md)
- [本地启动与任务流程](client-research/README.md)
- [已核对的来源事实表](client-research/docs/FACT_TABLE.md) · [来源索引](client-research/docs/SOURCES.md)
- [真实运行、评测及失败样本](client-research/docs/EVALUATION.md)
- [交付状态与简历事实清单](client-research/docs/DELIVERY.md)
- [历史模拟研究与旧版介绍](docs/LEGACY_README.md)

新研究工作台位于 `client-research`：单 LangGraph Agent 实际检索来源索引、读取公开资料、调用确定性计算、生成有引用的访前档案。支持人工确认/修改/撤回、Markdown 导出和新资料版本更新。索引范围与模型局限明确展示，不宣称任意企业全网研究或自动授信。

当前 Pages 仍为 [旧版模拟研究展示](https://sgyuhan23.github.io/yuyan-bank-research/)，不代表本分支的实时 Agent。本分支没有合并或部署。
