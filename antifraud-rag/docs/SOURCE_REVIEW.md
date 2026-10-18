# 来源核对表

核对者为Codex作者，尚未获得人类/银行人员独立审核。生产检索只读取`data/units.json`；`eval/cases.json`及反例绝不进入生产索引。

|单元|来源/类型|选择范围|保留的限制|
|---|---|---|---|
|bec-guidance|Westpac公开安全指引|Signs this may be a scam与Tips to minimise the risk完整章节，合为一个账户变更核验单元|独立取得号码，口头核实；付款未收到才检查付款历史；PayID及双重审批以可用为条件；非内部规程|
|bec-case|Scamwatch官方公开案例|John完整故事、隐私声明、损失后联系银行建议|根据一个或多个真实举报编写，姓名已处理；不是本项目真实客户，不推客户损失|
|receipt-guidance|Westpac公开安全指引|April 2023 – PayID Scam完整小节|网上售货场景，查看自己的网银到账，不信截图；章节日期为2023年4月，不能假称近期新规|
|investment-check|ASIC MoneySmart官方指引|CHECK: Is the company/person real and licensed or authorised完整章节及核验表|注册、许可、ASIC认可、投资安全四者不能混同；适用澳大利亚|
|national-statistics|Scamwatch官方统计|2025信息图总量、历史总量及2025/2024前五损失表|全国多机构合并举报，不是Westpac样本；不同精度总额不能重算报告精确同比|

原始HTTP抓取与工具保存章节均在`data/raw`；失败403记录在`data/acquisition-failures.jsonl`。西太银行正文由原始HTML提取；Scamwatch及ASIC原网址通过web工具读取，保存工具输出及章节。该类file_sha256是保存章节文件的哈希，不冒称源站原始HTML哈希。未知发布时间为null，章节中注明的时间另列。每条元数据在`source-index.json`和分类JSON中可检查。

`data/research/boundaries.json`为项目解释建议，不与官方事实合并；生成的培训情境另存`data/training/`，标为项目编写、待人工审核，不建立到官方检索索引。官方案例与自编情境可共同用于培训，但必须分开标识。

发现的首轮回答问题：见`docs/first-run-output.json`。同模型检查通过，但Codex作者发现“未收到款”前提在步骤中丢失，以及“实则接入诈骗者线路”过度确定。已增加定向条件检查和最多一次修订；不能宣称该检查覆盖全部遗漏与夸大。
