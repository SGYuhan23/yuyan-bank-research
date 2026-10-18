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
