# 浏览器银行经营分析 Demo

默认入口是 `index.html` 的聊天界面，`project.html` 保留案例介绍。无需账号、运行服务器、模型密钥或数据库。GitHub Pages 的构建阶段使用 Python，访客浏览器仅运行 JavaScript。

## 模型与计算的真实边界

自由文本由有限的浏览器规则识别，不是实时 LLM。超出范围时不生成答案。供应商参数先回显并经用户确认；输入变化即撤销确认、标记旧结果失效。结果保存同一请求参数快照与账本版本。

已有 `qwen-plus` 调用通过严格字段清单从仓库脱敏 trace 导出。回放展示原始提案、缺失字段、验收程序修正、确认、工具与受控回答；完整原问题在技术详情保留，未用更简单问题替代真实模型提示。本轮没有新生成模型记录。回放只适用于保存的案例，其他输入明确采用浏览器规则；同时用原始案例重新执行记录参数并比对结果。

## 计算文件

| 文件 | 作用 |
|---|---|
| [fuling-engine.js](js/fuling-engine.js) | 与 Python 相同的分组背包与行业工时合并；每客户最多一个动作；按实际选中工时计算行业占比 |
| [supplier-engine.js](js/supplier-engine.js) | 整数分逐日现金累计、延期、折扣、费用与每单追加预付 |
| [contract-engine.js](js/contract-engine.js) | 验收→开票→预计回款；只推导预计状态，传播争议，固定日期保持不动 |
| [ledger-engine.js](js/ledger-engine.js) | 合成付款确认、事务副本核对、失败回滚、版本和幂等校验 |
| [scenario-state.js](js/scenario-state.js) | 请求、确认、参数变更与结果失效 |
| [trace-replay.js](js/trace-replay.js) | 真实已记录调用的自然语言回放及原始参数详情 |

演示状态仅存在 `sessionStorage`，同一标签页刷新可恢复；重置清除。不是银行流水系统，不支持部分核销、实际放款或真实授信。

## 复算和一致性测试

从仓库根目录执行：

```sh
python -S agent-ops/research/build_data.py
python -S scripts/export_static_demo_data.py
node --test site/tests/*.test.mjs
```

导出程序读取业务数据和 Python 源码，生成浏览器输入，以及独立的 Python 动态预期结果。预期结果放在 tests，不被产品代码读取，也不部署到 Pages。测试比较 50/150/220/600 小时、启用及不启用行业约束的完整选中任务 ID、工时、净贡献与行业工时；比较 C1/0、C1/14、ALL/30、C1/7、C2/12、ALL/15 的逐日现金序列。另验证同余额五类动作估值、条件链、争议、确认/入账日期保护、余额不符的状态/版本/历史不变，以及幂等和版本冲突。

Python 核心模型未为适配浏览器而修改。浏览器 UI 的工时范围为 50–600 小时，延期范围为 0–90 天。合同演示使用案例真实初始日期，示意日期不替换数据。

Pages 工作流每次先执行数据构建、Python 回归与 Node 一致性测试，通过后才发布浏览器代码、合成输入、脱敏 trace、截图和报告。Python、测试预期结果和本地配置不在发布产物中。
