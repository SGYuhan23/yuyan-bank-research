# 银行反诈知识与培训辅助 Agent

两个任务：查询反诈知识、生成培训材料。实际流程是任务识别 → 检索 → 依据充分性/冲突检查 → 必要时程序计算 → 模型生成 → 原文引用与支持性检查。复用现有项目的Qwen接入和LangGraph；没有银行账户或交易操作权限。

## 启动

需要Python 3.12。在仓库根目录：

```bash
python3.12 -m venv antifraud-rag/.venv
antifraud-rag/.venv/bin/pip install -r antifraud-rag/requirements.txt
antifraud-rag/.venv/bin/python antifraud-rag/server.py --env /你的私有配置文件/.env
```

私有配置文件需包含 `QWEN_API_KEY`、`QWEN_ENDPOINT`（兼容接口根URL）、`QWEN_MODEL`。不把密钥放入网页或Git。可复用现有`client-research/.venv/bin/python`，先安装本模块requirements。打开 http://127.0.0.1:8770 。本地单用户，无公网部署认证。

命令行：

```bash
python antifraud-rag/pipeline.py '熟悉的供应商发邮件说更换收款账户，应该核实什么？' --env /私有文件/.env
python antifraud-rag/pipeline.py '为新入职客服生成一份收款账户变更场景的培训材料。' --task training --env /私有文件/.env
```

失败会保存`runs/<id>/run.json`及草稿，不返回预置成功答案。模型内部思维不保存。生成培训情境另存`data/training`，默认待人工审核；不回灌到官方知识库。

## 资料与检索

- `data/source-index.json`：官方原始来源索引，未知日期留null。
- `data/units.json`：5个完整章节/案例/统计表检索单元。
- `data/bank_public_guidance.json`、`official_guidance.json`、`official_public_case.json`、`official_statistics.json`分别保存类别。
- `data/research/`保存项目研究建议；`data/training/`保存自编培训内容，不作为官方事实检索。
- `docs/SOURCE_REVIEW.md`说明出处、范围及抓取失败。已核对后来提供的材料包索引；见`docs/PACKAGE_RECONCILIATION.md`，区分已获取、候选与未取得来源。

BM25基线采用中英文词及中文二元组，索引中包含作者标记的主题标签（不是参考答案）。语义检索实际调用`text-embedding-v4`并做内存余弦排序，向量本地缓存，无向量库。CLI `--retriever semantic`可选择语义检索。默认auto：先执行BM25，仅在无正分命中时调用现有embedding语义检索。默认网页与CLI一致；`--retriever bm25`和`--retriever semantic`可分别评测。服务失败显式报错，语义候选仍须经过充分性/冲突检查。未增加混合排序或重排。语义模式失败明确报错，不伪装成已执行。

引用采用检索单元ID，程序附完整原文章节；模型若仍提供引文则检查逐字匹配，不能拼接省略。另一次同模型调用检查支持性；该检查已在本次发现漏判，不能当作人工审核。

## 评测与检查

```bash
python -m unittest discover -s antifraud-rag -p 'test_*.py' -v
# eval脚本默认复用当前工作区相邻yuqi-core/.env；也可预先设置同名环境变量
python antifraud-rag/eval_retrieval.py
python antifraud-rag/evaluate.py
```

评测题和答案要点独立保存在`eval/cases.json`。恶意指令及冲突资料仅作为显式评测夹具注入，不进入生产索引。11题是开发用小样本，不是盲评集。结果、失败和修复分别保留。详见`docs/EVALUATION.md`。

## 边界

这是澳大利亚公开资料辅助原型，不是Westpac内部规程，不证明任何具体交易安全。无交易拦截、风险评分、账户冻结或自动客服考核。只内置一个有依据的同比计算工具；其他统计计算会要求补充支持，不宣称通用统计分析。尚无银行人员独立审核、真实客户试点、生产部署或效率提升证据。

## 审阅入口

- [实际生成的两类输出](docs/ACTUAL_OUTPUTS.md)（可继续打开对应run.json）。
- [评测与失败](docs/EVALUATION.md)、[材料包比对](docs/PACKAGE_RECONCILIATION.md)。
- [已实现与未实现](docs/IMPLEMENTATION_STATUS.md)、[来源核对](docs/SOURCE_REVIEW.md)。

本轮两项收尾的真实运行、mock故障测试及金额口径复核见[收尾验证](docs/CLOSEOUT.md)。

当前场景收尾：操作建议显式携带场景、对象、触发条件与来源，生成/审核只使用适用该场景的原文段落；删除原关键词整句模板。范围、真实复跑及已知局限见[场景收尾记录](docs/SCOPE_CLOSEOUT.md)。

## 独立升级分支：本地工具工作台

保留原知识与培训材料流程 `/legacy` 及历史运行。新入口 `/` 包含案例研判、交互培训和独立合成图实验。当前名称仍为“银行反诈知识与培训辅助 Agent”，不将探索验证包装成银行上线系统。

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r antifraud-rag/requirements-upgrade.txt
# 环境文件自行保存在仓库外，包含已有 QWEN_API_KEY / QWEN_ENDPOINT / QWEN_MODEL
OMP_NUM_THREADS=1 .venv/bin/python antifraud-rag/server.py --env /absolute/path/private.env --port 8782
# 默认 auto：BM25 无命中才转真实 embedding；显式 bm25/semantic/hybrid/all 可比较
.venv/bin/python antifraud-rag/upgrade_cli.py '对方发来转账凭证，货可以给他了吗？' --role 卖方收款 --env /absolute/path/private.env
# 训练本地合成实验模型；缺失模型时网页明确 unavailable，不返回伪分数
cd antifraud-rag
OMP_NUM_THREADS=1 ../.venv/bin/python -m upgrade.graph_lab
# 额外未见结构对照，使用训练得到的同一组模型，不调参
OMP_NUM_THREADS=1 ../.venv/bin/python -c 'from upgrade.graph_lab import structural_holdout; structural_holdout()'
```

案例、上传材料和模型文件在忽略的 `antifraud-rag/local/` 下；不提交私人材料。图片使用 macOS Vision（需 Swift 命令行工具），其他系统返回 OCR 不可用并允许人工转录。支持文本、PNG/JPEG；不宣称支持所有文档格式。链接默认只解析域名，不访问目标；可选 `SAFEBROWSING_API_KEY` 仅向固定服务查询脱敏后的来源域，未配置会明确显示 unavailable。

新代码：[数据契约与边界](docs/UPGRADE_CONTRACTS.md)、[参考源码审查](docs/UPGRADE_REFERENCES.md)、[三分钟演示](docs/UPGRADE_DEMO.md)、[升级验证](docs/UPGRADE_VALIDATION.md)。重排器没有进入默认路径；图表示不是 GraphSAGE/GPU 复现。人工审核为本地记录，不是企业认证或授信审批。

验证命令（仓库根目录）：
```bash
OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s antifraud-rag -p 'test_*.py' -v
.venv/bin/python -m compileall -q antifraud-rag
node --check antifraud-rag/web/upgrade.js
# 新批次目录；冻结文件不同则拒绝覆盖旧评测
.venv/bin/python antifraud-rag/evaluate_upgrade.py --env /absolute/path/private.env --batch my-new-run
.venv/bin/python antifraud-rag/grade_upgrade.py --env /absolute/path/private.env --batch my-new-run
```

浏览器脚本在 `eval/upgrade/browser/`，依赖Playwright及本机Chrome，默认连接端口8784，可用 BASE_URL 环境变量调整。它们会实际调用本地Qwen并产生案件/审核记录；并非无成本mock。能力证据与未通过项见 [UPGRADE_EVIDENCE.md](docs/UPGRADE_EVIDENCE.md)。冻结对照之后只修复独立材料工具试跑发现的依赖调度和网页故障，未根据保留题改生成规则；对照成绩对应冻结代码，不冒称最新代码已重新通过保留集。

## 最新融合与收尾证据（2026-10-20）

- [开源参考到实现的对应关系](docs/UPGRADE_REFERENCES.md)：选择相关设计，非复制完整系统或宣称全球最优。
- [简历与面试证据包](docs/RESUME_EVIDENCE.md)：可用表述、实际数据口径及技术取舍。
- [本轮真实结果](eval/repair-v2/REPORT.md)：新旧失败均保留，开发测试不冒充独立基准。

新版首页与 `upgrade_cli.py` 的 auto 流程在原有零命中兜底之外，检查已识别的三个核心任务是否取得相应来源；缺失时追加一次实际语义检索并重新判断充分性。显式 bm25/semantic 模式不被偷偷切换。原 `/legacy`、`pipeline.py` 仍保持原有零命中兜底，未新增覆盖补检。

新版建议与追问进入逐条来源审核：模型选择原文片段ID，程序绑定原文；无效格式/引用只允许一次重试，输出修订最多一次。可删除具体无依据的附加内容，但核心步骤仍需覆盖检查。该审核与生成使用同一供应商，不能代替独立人工审核。

## 训练型 GraphSAGE 与内部分析演练

当前新增真实的两层 mean GraphSAGE（学习自身与邻居权重），不是旧版固定均值实验改名。固定任务是“10%人工核查名额下的合成账户排序”。见 [协议与实际结果](eval/graphsage-v1/REPORT.md)。三个初始化种子、验证集选轮次、邻居消息消融、群组隔离和结构挑战均已实际运行。原测试集平均 AP0.915，结构挑战平均 AP0.496；不能概括为稳定领先。

**直接演示**：按上文启动本地服务器 → 交易图实验 → 选择“训练型两层 GraphSAGE” → 创建合成演练案件 → 执行图分析与核查排序 → 查看账户关联交易与项目编写的核实问题 → 保存人工判断并导出。仓库保存 JSON 权重，推理仅需现有 numpy，无需密钥或 PyTorch。节点统计树模型仍为保守默认，若本地模型缺失会明确停止，不伪造结果；可选择仓库自带的 GraphSAGE 实验权重。

**复现训练**（仓库根目录，使用新输出目录，已有目录会拒绝覆盖）：

```bash
python -m pip install -r antifraud-rag/requirements-graph-training.txt
PYTHONPATH=antifraud-rag OMP_NUM_THREADS=1 python -m upgrade.graph_sage --out /tmp/graphsage-new-run
```

完整预测、权重、每轮损失/验证AP、分组和哈希存于指定目录；这不会覆盖已发布实验或自动替换默认模型。独立演练走确定性工具流程，明确记录零LLM调用；它不需要让大模型猜测交易用途。普通知识问答没有银行交易数据访问能力，模拟角色也不构成实际身份认证。
