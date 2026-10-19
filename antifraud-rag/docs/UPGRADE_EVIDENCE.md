# 能力—证据映射

| 能力 | 代码 | 实际运行/验证 | 局限 |
|---|---|---|---|
| 版本、证据归属、原子审核 | upgrade/contracts.py, store.py | tests-actual.txt；browser/case-export.json | 单用户SQLite；本地名字不是认证 |
| 条件工具与依赖调度 | upgrade/agent.py, tools.py | tool-track/image-22201878577546c9a7f262c63bab170d.json；email-ced1d61357bb4bd38d71b6929b4e82a8.json | 规划和生成可失败；已修调度顺序；不是语义保证 |
| 真实OCR及位置 | upgrade/ocr.py, ocr.swift | ocr-actual.json, ocr-tool-actual.json | 仅macOS Vision；截图内容不证明到账 |
| 检索与强基线 | retrieval.py, evaluate_upgrade.py | development-reviewed.json；heldout-v1 | 自动兜底仅零命中；部分命中漏相关来源仍可能失败 |
| 安全链接与资料比较 | upgrade/tools.py | link-actual.json；邮件工具trace | 外部信誉未配置；未访问目标；比较输入不验证账户 |
| 培训事实隔离与复盘 | upgrade/training.py | training-actual.json；隐藏事实与反事实单测 | 确定性模拟覆盖有限；同模型复盘仍可能误评 |
| 图实验与模型调用 | upgrade/graph_lab.py | graph/report.json、structural-heldout-report.json；浏览器图接口 | 纯合成；固定邻域表示非GNN；未见结构收益不可靠 |
| 真实页面操作 | server.py, upgrade/api.py, web/upgrade.* | browser/result.json、截图、case-export.json | 本地原型；未部署；仅文本与PNG/JPEG上传 |
| 来源复核与驳回 | upgrade/store.py | 两份 *-author-review.json | 作者/Codex审阅，不是独立银行专家 |
| 公平比较与失败保留 | eval/upgrade/PROTOCOL.md, evaluate_upgrade.py, grade_upgrade.py | heldout-v1全部36项；盲评与非盲作者抽查分开 | 6个自编故事；不能证明总体优势 |

所有运行路径相对 `antifraud-rag/eval/upgrade/`。历史 `runs/` 不作新工具能力证据；本轮固定流程基线另外生成6个新ID，原历史未修改。

已实现且运行：上述本地模块、Qwen、embedding、原生OCR、模型训练与评分、HTTP浏览器链路。仅mock验证：外部信誉超时、部分网络失败注入。外部阻塞：未配置信誉服务真实查询、没有独立银行评审/真实业务数据。尚未实现：PDF、跨平台OCR、企业身份认证、训练式GNN、任意开放域客户模拟；本轮不假装具备这些能力。

验收结论：工程主链路已连通，实验和失败已交付；正常反例与部分生成追问未通过来源复核。因此保留原名，不写“升级全部验收通过”，不以增加模型或架构组件掩盖这一缺口。
