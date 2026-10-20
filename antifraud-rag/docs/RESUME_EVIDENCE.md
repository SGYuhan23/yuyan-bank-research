# 简历与面试证据包（本轮收尾版）

项目：银行反诈知识与培训辅助 Agent。个人职责、日期、学校及合作背景由本人确认；以下条目描述项目已实现成果，不补造身份或银行合作。

## 总行管培版（3条）

- 围绕卖方到账核对、供应商账户变更与此前款项未收到三类业务，构建公开依据驱动的反诈辅助原型，将建议的对象、前提与来源关联，打通材料输入、完整答案审核、档案导出及案件变更后的旧结果失效流程。
- 设计3类业务、18个分层自编培训变体，加入正常业务对照，区分初始已知、对话释放与待核实信息；以“不能将账户变更直接判为诈骗”为边界，保留错误建议、模型漏判和人工修订记录。
- 围绕有限人工核查名额开展合成交易研究：比较四类模型，在447账户测试集、45个核查名额下，GraphSAGE三个初始化均找回186个异常标签中的45个；同时报告结构挑战退化，将模型定位为待核查线索排序工具。

## 金融科技版（3条）

- 基于LangGraph与Qwen实现受约束的工具规划，接入7类工具，结合BM25无命中语义兜底、来源覆盖补检、逐项语义复核与SQLite版本管理，完成真实材料提取到审核导出的可追溯流程。
- 将引用真实性与建议适用性分开验证：程序绑定原文片段、校验案件证据与版本，模型检查角色、对象和条件；补齐完整答案审核、正常培训事实一致性及否定句回归，本轮80项本地测试通过，并保留在线失败。
- 实现两层mean GraphSAGE，与节点统计树、固定邻域均值树及去邻居消息网络消融比较；同一合成测试集三个初始化平均AP0.915，固定邻域树AP0.882，既有结构挑战AP降至约0.496，保留树模型作为保守默认。

## 逐条证据对应

| 条目 | 代码 | 实验或演示记录 |
|---|---|---|
| 管培1 | upgrade/agent.py、store.py、web/upgrade.js | eval/final-closeout-v1/browser/main-run.json，运行4879327f7f344a79b7ccc1921b703345；main-export.json、stale-export.json、assertions.json |
| 管培2 | upgrade/training.py | eval/final-closeout-v1/training-final/all18.json；正常33b6a86d82634484b42f7a5bc772a102；否定34c854a742e74889a88219bd7f9b716a |
| 管培3 | upgrade/graph_sage.py、graph_exercise.py | eval/graphsage-v1/actual/report.json、REPORT.md；本轮图工具运行ca2478b1a0094fae9b769b467a94fe58 |
| 科技1 | upgrade/agent.py、tools.py、retrieval.py、store.py | eval/final-closeout-v1/retrieval-final.json、browser/main-run.json |
| 科技2 | pipeline.py、upgrade/grounding.py、training.py、test_final_closeout.py | eval/final-closeout-v1/tests.txt、REPORT.md、online/；80测试包含网络mock，不是80次在线问答 |
| 科技3 | upgrade/graph_sage.py、graph_lab.py | eval/graphsage-v1/actual/权重、预测及report.json；reproduction.json记录此前复现，本轮未扩大训练 |

上述路径相对于antifraud-rag。AP是average precision，不是准确率；三个初始化使用同一数据。结构挑战此前已经观察过，不是新盲测。18个变体均为项目编写，不能写成18个真实客户。浏览器自动点击确认验证的是流程，不是业务专家签核。

## 七类工具如何解释

| 工具 | 解决的问题 | 能力边界 |
|---|---|---|
| guidance | 找公开指引、返回出处；BM25无命中调用现有embedding | 召回候选不等于证据充分；服务失败单独记录 |
| extract | 提取文本或图片文字，生成可追溯材料陈述 | OCR不能证明凭证真实、资金到账；本轮主流程为文本提取，未重跑真实OCR |
| links | 提取链接并检查格式/可用信誉服务 | 不凭专业网址判安全；外部信誉服务未验证不能称已查询 |
| compare | 确定性比较用户提供的新旧金额、币种、账户字段 | 相同或不同只是字段观察，不验证账户归属 |
| timeline | 将材料中的事件日期整理为时间线 | 未知日期不补造，时间线不是交易真实性证明 |
| graph | 分析合成转账连接、环路与关联交易 | 合法结算也能成环，不识别违法目的 |
| score | 对合成账户执行显式选定模型的排序 | 分数不是欺诈概率；图演练固定调用graph与score，不声称LLM规划 |

## 当前表述边界

已经训练GNN，不是GraphRAG。小型知识库不需要额外向量数据库。项目有真实工具执行与合成模型实验，但没有整体优于通用模型、效率收益或银行业务落地证据。正常业务措辞、投资网址条件和培训语义复盘仍有漏判；主展示限定为卖方到账核对及合成图附录，详见本轮报告。不要将源于澳大利亚的公开建议写成中国银行内部规程。

[90秒介绍、5分钟演示与五个追问](INTERVIEW_DEMO.md)
