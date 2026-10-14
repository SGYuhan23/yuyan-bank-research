# 确定性研究模块

当前两个案例为涪陵客户经营分析和供应商资金管理。公开事实、合成输入、研究假设和模型输出分开标注，不代表银行内部数据或实际经营业绩。

完整安装、本地平台启动、标准库数据构建、测试、报告生成及预期结果统一见 [REPRODUCIBILITY](../../REPRODUCIBILITY.md)。业务演示见 [DEMO](../../DEMO.md)，责任边界见 [DISCLAIMER](../../DISCLAIMER.md)。

当前 Supplier 逻辑为 supplier_ledger.py；models.py 的 supplier_case 是早期单订单回归参考，不代表当前结果。公开数据以 frontend/public/research/v2.json 为准。

本目录保留全部当前模型、测试支持、构建及报告源码。公开 trace 仅含真实用户提示、人工策略摘要、提案、修正、确认快照、工具参数/结果和受控回答，不公开完整内部上下文。

文件和冻结结果校验见 [portfolio_verify.py](../../scripts/portfolio_verify.py)。
