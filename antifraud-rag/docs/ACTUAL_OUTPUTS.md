# 本轮实际输出（摘录）

## 当前收尾状态

最新展示改用[主演示4879327f7f344a79b7ccc1921b703345完整记录](../eval/final-closeout-v1/browser/main-run.json)：本人银行核对本次到账，凭证不替代到账，不混入供应商步骤。完整风险、建议、追问和边界均可见。原文“到账前不交货”尚需人工显式补明，不能把该输出当完美答案。新正常、投资及未收到款任务仍有不通过项，详见[逐条复核](../eval/final-closeout-v1/REPORT.md)。旧输出和错误不改写。以下为此前阶段展示，不作为当前全场景验收通过证据。

旧展示的供应商模板、宽泛暂停付款表述与跨场景追问存在错误；旧runs及中间复测记录未修改。本页改引新运行，只摘录用户任务、操作建议与其适用范围，完整输出和审核见各trace。金额修复继续保留。

作者按原文逐条复核对象与前提；不是银行人员独立签核，培训仍待人工审核。

## 卖方收款

[真实运行 f844e72e7022493a](../runs/f844e72e7022493a/run.json)

对方发来转账凭证，货可以给他了吗？

- 交货前必须本人登录网银或手机银行，核对本次货款是否已实际到账。
  - 对象：本次卖给买家的货物及对应货款
  - 条件：对方发来转账凭证，货可以给他了吗？
  - 来源：receipt-guidance
- 买家提供的付款截图、收据或转账凭证不能替代本人网银/手机银行的实际到账核对；未确认到账前不得交付本次货物。
  - 对象：本次卖给买家的货物及对应货款
  - 条件：对方发来转账凭证，货可以给他了吗？
  - 来源：receipt-guidance

## 供应商账户变更

[真实运行 0f17d9d932264f39](../runs/0f17d9d932264f39/run.json)

老合作方说换了卡号，让我们今天打钱，先做什么？

- 立即暂停按本次变更请求更改账户信息或支付货款，必须先独立取得电话口头核实。
  - 对象：本次供应商账户变更请求、变更账户及相关付款
  - 条件：独立口头核实本次变更前；不能默认供应商称此前款项未收到
  - 来源：bec-guidance
- 使用企业自己存档的电话号码，或公开渠道查得的号码（如官网、营业执照登记号对应号码），拨打供应商官方电话，直接向其财务或负责人确认本次账户变更请求是否真实。
  - 对象：本次供应商账户变更请求、变更账户及相关付款
  - 条件：独立口头核实本次变更前；不能默认供应商称此前款项未收到
  - 来源：bec-guidance

## 供应商称此前付款未收到

[真实运行 1cb97841db9f48b4](../runs/1cb97841db9f48b4/run.json)

供应商说上周的货款没收到，现在催我再付一次，该核实什么？

- 明确以供应商称上周该笔货款未收到为前提，暂停再次支付该笔款项。
  - 对象：上周的货款
  - 条件：供应商明确声称未收到此前付款
  - 来源：bec-guidance
- 核对上周该笔付款的历史记录与往来邮件，检查是否存在账户变更请求。
  - 对象：上周的货款
  - 条件：供应商明确声称未收到此前付款
  - 来源：bec-guidance

## 培训材料

[真实运行 692db6fe9cfe4413](../runs/692db6fe9cfe4413/run.json)

生成供应商收款账户变更的新员工培训材料。

培训情境（本项目编写，待人工审核）：企业A收到自称供应商B的邮件，称因财务系统升级需将收款账户变更为新银行账号，要求立即更新并支付下一笔50,000澳元货款。客服C在培训中学习如何响应。

- 新员工须知：收到供应商账户变更请求（如邮件、消息）时，必须独立取得电话号码并口头核实本次变更；不得使用请求中提供的联系方式。
  - 对象：本次供应商账户变更请求、变更账户及相关付款
  - 条件：独立口头核实本次变更前；不能默认供应商称此前款项未收到
  - 来源：bec-guidance

## 两个场景比较

[真实运行 1eab222befb5402b](../runs/1eab222befb5402b/run.json)

分别说明卖家核对买家到账，与企业核实供应商账户变更的区别。

- 卖家须亲自登录本人网银或手机银行，核对本次货款是否已实际到账；买家提供的付款截图或收据不能替代本人到账核实。
  - 对象：本次卖给买家的货物及对应货款
  - 条件：交货前核对自己的网银/手机银行实际到账，买家凭证不等于到账
  - 来源：receipt-guidance
- 企业付款方收到供应商账户变更请求后，必须使用自行掌握的、独立来源的电话号码（非邮件所附联系方式）进行口头核实；核实完成前不得更新本次账户信息，也不得按该请求支付本次货款。
  - 对象：本次供应商账户变更请求、变更账户及相关付款
  - 条件：独立口头核实本次变更前；不能默认供应商称此前款项未收到
  - 来源：bec-guidance

## 条件工具升级：新的真实运行（旧记录保留）

本轮新结果必须连同审核状态阅读，不能把 `pending_review` 当作内容正确或人工确认。

- 开发集卖方：`236e9c618f2240cca79b771749fe2e20`，BM25零命中→真实semantic→receipt-guidance。回答围绕本人网银/手机银行实际到账、不能依赖买方截图、未到账不交本次货物。
- 开发集账户变更：`09308b677b5d41e6a919e16e54631795`，BM25零命中→真实semantic→bec-guidance。限定本次请求与独立口头核实。
- 开发集此前未收款：`d4192aa782714864a19f8b3e94b31840`，BM25；保留供应商声称此前款未收到及同笔重复支付前提。
- 图片工具：`22201878577546c9a7f262c63bab170d`，真实Vision提取→公开指引，图片内容标为reported_claim，不能证明到账。
- 邮件工具：`ced1d61357bb4bd38d71b6929b4e82a8`，提取→比较/时间线/链接→检索，链接信誉服务不可用。**作者来源复核驳回**：追问混入付款历史，原模型审核漏检。
- 正常变更对照：`bf353905512244e2b33a56b6e06de689`。**作者来源复核驳回**：增添“唯一有效账户、盖章、密语”要求，不应作为合格演示答案。
- 交互培训会话：`1ed41b221e60496488163151c2b9194f`，确定性客户回复和实际Qwen复盘；复盘引用能定位学员原句，但语义评分仍需人审，不作客服绩效。

完整内容在 `eval/upgrade/`；失败及驳回记录没有手工改写为成功。保留集汇总见 `eval/upgrade/heldout-v1/REPORT.md`。John案例金额规则仍只覆盖“最初17,000澳元包含于估计总损失超过30,000澳元”；全国统计等其他金额并未获得通用语义校验能力。

## Latest integration follow-up (2026-10-20)

See [repair-v2 results](../eval/repair-v2/REPORT.md); old records and errors remain unchanged. New source-reviewed seller output `7edc8178cda3426986d59733dbd38d21` states:

> 交货前，必须亲自登录自己的网银或手机银行，核对本次货款是否已实际到账。
> 买家提供的转账截图或付款收据不能替代本人银行账户的实际到账确认；未确认到账前不得交付本次货物。

This excerpt is from the actual output in `followup-v2`, not a manual rewrite. Its scope is online selling and it cites receipt-guidance. Separated comparison run `9a2ef2ec26774a3faa6525bac1df3667` keeps seller receipt and company supplier-change steps distinct. Unsupported internal-policy run `c202abf2c86a483ab21cc7595d47b384` stops for insufficient evidence.

Normal, unpaid and investment follow-up outputs were rejected by project-source review for residual unsupported wording/omitted conditions; their pending-review runtime status must not be presented as semantic approval. No new training-generation success is claimed for this batch. The previous John amount correction and historical training trace remain the evidence for that separately tested behaviour.

## Trained GraphSAGE exercise

Actual local case run `17e0fbba194c4027b036779ccc582317` executed graph and score tools, selected4 of34 synthetic accounts under10% review budget, linked incident transaction IDs and project-authored questions, and persisted review/export. This is an internal analyst exercise, no real bank data, no LLM call. Full case and screenshots: `../eval/graphsage-v1/browser/final/`. The reviewer note does not approve a fraud finding; it preserves the need for contracts and business-purpose evidence. Training comparison and structure-generalisation failure are recorded separately in graphsage-v1 report; the shortlist is not an accuracy evaluation.
