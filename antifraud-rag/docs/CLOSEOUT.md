# 本轮两项收尾验证

基线1358d53，开始前已pull --ff-only确认分支无更新。未改项目名称、框架或供应商，未部署。

## 默认检索

网页/API及默认CLI使用auto：BM25有正分命中直接返回；无命中才调用现有embedding语义检索，k=3保持不变。显式bm25不会兜底，semantic直接调用语义检索，两者可独立评测。每次尝试记录method、unit_ids、source_ids；兜底记录bm25_no_positive_score。页面显示真实方法与返回单元。语义服务失败记录retrieval_failed并终止，不能等价为资料缺失。候选继续经过原有充分性和冲突检查。

## 真实运行（非mock）

已有私有配置可用，未打印/提交凭据。使用现有text-embedding-v4；文档向量可复用现有缓存，每个语义查询实际调用embedding接口。

|输入|真实检索路径|对应单元|
|---|---|---|
|老合作方说换了卡号，让我们今天打钱，先做什么？|BM25无命中→semantic|bec-guidance第一位|
|对方发来转账凭证，货可以给他了吗？|BM25无命中→semantic|receipt-guidance第一位|
|熟人来信说收钱的卡换了，催着赶紧汇过去，要怎么确认？|BM25无命中→semantic|bec-guidance第一位|
|买家把汇款截屏给我了，我现在就发货行吗？|BM25命中，无兜底|receipt-guidance|

[真实检索明细](../eval/closeout/real-retrieval.json)，[五项默认流程运行](../eval/closeout/real-pipeline.json)。两条口语、正常供应商问答及培训均实际生成；无关“火星种土豆温度”虽获得语义候选，充分性为false，steps和risks为空，未编造种植答案。此为小样本功能验证，不是回答准确率或普遍无幻觉证明。

## 损失关系

原文：In the weeks to come, with the initial loss of $17,000, the delay in supply flowing from missed orders and broken contractual obligations, John’s company estimated their loss to be over $30,000.

参考口径：企业估计总损失超过30,000澳元，包含最初17,000澳元及供货延误、合同义务等影响。不能把30,000作为额外损失，也不把估计值写成确定金额。

生成/审核提示要求保留包含、合计、额外、估计关系；另有bec-case特定规则，记录case_amount_scope_applied及修正前后文本，仅作用于引用此案例且包含已知金额表达的steps/risks。源文关键关系改变时拒绝套用。不是通用财务语义校验；自由文本仍需人工复核。

新培训运行 **4b48fa8dbff54fc4**，金额关系逐条按原文复核，含估计、总损失、包含初始损失、非额外损失；详见[复核记录](../eval/closeout/amount-review.json)。这是Codex作者核对，非原模型自评分，也非银行人员独立签核。培训整体仍待人工审核。

ACTUAL_OUTPUTS.md改为引用新运行，并注明旧表述错误；training.png/mobile.png更新为新结果。历史runs及旧评测草稿均保留，不改写模型当时的输出。

## 检查与边界

- 现有8项测试加7项直接相关回归，共15项通过。新增网络mock明确只测试兜底分支、显式模式、故障与日志；金额回归使用上述固定参考关系断言，不依赖模型自评。
- [故障模拟](../eval/closeout/mock-unavailable.json)：mock embed异常，真实执行状态图失败，未进入充分性检查。不是实际供应商故障。
- Python编译及前端语法检查通过；[浏览器检查](../eval/closeout/browser-results.json)使用真实本地HTTP/API提交，验证实际兜底状态、来源ID和新培训金额展示。
- 未进行银行人员独立审核、生产部署或大样本效果评测；未声明准确率100%、消除幻觉或效率提升。本轮所需模型/embedding均实际运行，无因缺凭据而未运行项。
