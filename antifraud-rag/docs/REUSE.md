# 仓库核查与复用

在现有审阅clone新建 `codex/antifraud-rag`，基于 `ffdcb08`，保留产业研究及线上版本。工作区根的通用DeerFlow恢复记录表明原入口和工具仍在，不能因此推断反诈RAG已经存在。

实际复用：`client-research/engine.py:ResearchRun.model`的Qwen HTTP接入、temperature=0、JSON模式、enable_thinking=false、用量及错误记录；现有LangGraph依赖；Pydantic与本地HTTP服务模式。新增独立反诈状态图，避免污染产业研究公司/事件模型。没有新增多Agent、向量库或微服务。

已有的原文substring引用检查只能证明引文存在，不能证明推论成立；新流程在精确引文校验后增加同模型另一调用的支持性检查，仍不等于独立人类审查。保留失败草稿，不伪装成功。

初期未找到材料包，先独立查找原始来源；用户随后提供zip路径，已比对10个来源。详见PACKAGE_RECONCILIATION.md；未将包内建议、场景卡或自报PASS当作官方事实或本项目验证结果。
