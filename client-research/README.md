# 对话式 Agent 入口

新首页提供明确研究主题、完整 Prompt、逐步工具事件与最终档案。本地启动后访问 `/agent/` 可执行真实模型任务；GitHub Pages 静态目录播放历史真实记录。见 [固定流程与启动](docs/FIXED_WORKFLOW.md)。它使用真实资料和预设研究规则，不调用在线模型。以下为保留的本地 Agent 实验入口。

# 渝研｜重庆产业客户研究 Agent

面向银行对公客户经理的访前研究：这家重庆企业发生了什么、可能值得了解什么服务、有哪些反证、见面需要核实什么。

此目录是独立审阅版本。旧版模拟研究及 Pages 部署原样保留，当前线上页面没有切换。这里的模型会实际选择检索/读取/计算工具；页面不把预置报告包装成在线推理。

## 启动

Python 3.12+；需要自己配置可用的 OpenAI-compatible Qwen 服务。无密钥可浏览保存的真实运行，发起研究会明确失败。

```bash
cd client-research
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.lock
cp .env.example .env
# 编辑 .env，不提交密钥
.venv/bin/python server.py --env .env
```

打开 http://127.0.0.1:8765 。服务仅监听本机，无公网认证和多用户隔离，未部署后端。

1. 输入样本企业或其简称，填写问题，选择资料范围。
2. 选择保存原文模式（重新调用真实模型）或在线抓取模式（重新请求索引中的原文）。两者均不是全网搜索。
3. 查看工具执行、事实、阶段、计算、假设、反证与问题。失败保留记录，不回退假报告。
4. 复核假设时填写复核人、修改内容与依据。记录绑定证据版本，原始模型运行不被覆盖。
5. 导出 Markdown 访前档案，包含引用与复核记录。
6. 勾选新增来源，或导入重庆政府/巨潮/上交所 HTTPS 原文，点击“以此档案更新”。旧确认不继承，新事实/被替代事件/撤回假设单列。

五个首批主体：重庆日发、秦安股份、秦安铸造、隆鑫通用、重庆紫硕。索引之外的企业当前明确停止，不伪造企业档案。导入资料只支持已有主体，任意企业自动发现尚未实现。

## 复现与检查

```bash
.venv/bin/python prepare_sources.py       # 下载原始来源并提取所选页/表；失败写入记录
.venv/bin/python build_reference.py       # 作者逐原文核对的事实表与人工研究底稿
.venv/bin/python engine.py --company rifa --env .env --mode live
.venv/bin/python evaluate.py --env .env  # 5样本 × Agent/单轮基线；有真实模型费用；已有结果不覆盖
.venv/bin/python -m unittest discover -s tests -v
```

来源快照见 `data/sources.json`，含原始 URL、发布/检索时间、期间、页码/段落、摘录、原文件 SHA-256；完整下载文件保留本地 `data/raw`（不提交全文）。`data/reference-facts.json` 是作者核对标签，**运行管线不读取它**。该表尚未经过使用者或银行人员独立签核。

`runs/` 仅包含本轮真实运行、原始失败及同条件单轮输出。每次新运行写 `local/runs/`；人工记录在 `local/reviews/`，导入来源在 `local/imported-sources.json`。删除 local 会丢失本机记录，请自行备份。导入元数据为用户提供，模型仍须核实。

## 实现边界

- 单 LangGraph 循环、一个模型、3 个只读工具，无子Agent、向量库或微服务。
- 检索核验来源索引，实际读取原文摘录或请求原始网页/PDF；没有搜索引擎集成。不能宣称全网自主研究。
- 确定性计算校验输入数字是否在资料中；期间/主体/单位的语义仍需人工复核，不能把数值存在当成语义正确。
- Schema、逐字摘录、引用来源、官方项目编号与计算 ID 校验；**不是自动事实真伪证明**。首屏摘要、假设、问题仍可能包含不当推断，必须复核。
- 模型响应只保存结构化任务、工具参数、结果、用量和简短依据；不读取或保存 `reasoning_content`。
- 12轮主循环上限，最终证据复核最多3次结构修复；模型失败、抓取失败和校验失败均显式保存。历史运行的代码缺陷与修复见交付报告。
- 新证据后先由模型提出修订，强产品断言另经明确标识的保守规则撤回/标不足，最后需使用者人工复核；旧 Review 不自动迁移。事件的 supersedes 指当前阶段被替代，历史事件不删除。
- 没有贷款额度建议、自动授信、信用评分、商机概率、预期银行收入，也没有真实客户经营收益指标。

入口材料：[来源事实表](docs/FACT_TABLE.md) · [复用判断](docs/REUSE.md) · [交付检查](docs/DELIVERY.md) · [评测](docs/EVALUATION.md)。

作者源文修订与规则复核均另存运行并明确标识，不把它们计作新模型调用。浏览器测试需 `npm install`，在仓库根目录运行 `node client-research/tests/browser.cjs`，或在此目录 `npm run test:browser`；需本机Chrome及已启动服务。
