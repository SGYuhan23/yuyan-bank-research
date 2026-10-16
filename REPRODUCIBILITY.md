# 复算与本地运行

从本仓库根目录执行。完整源码保留；GitHub 展示不依赖在线服务。

先在干净检出中验证提交的发布快照，再在独立工作副本中执行下方数据重建与测试：

```sh
python scripts/portfolio_verify.py
```

此检查验证提交文件的字节哈希，不是重建后的业务结果校验。导出的一致性测试预期含运行时间戳，重建后字节可能变化；用既有回归与 Python / 浏览器对照验证计算结果，不以重建文件重置发布清单或冻结核心哈希。

## 当前公开研究页

新版展示从 `research-showcase/dist/` 发布。按 [新版复算说明](research-showcase/README.md) 运行10项模型检查与页面交互检查；页面、PDF、data.json 均以该目录为准。以下步骤仅用于保留的原版后端、Agent 与计算引擎，不用于解释新版三个客户原型或56万元案例。

## 1. 原版最小确定性复算

Python 3.12+；数据构建仅用标准库，不需要模型、数据库或 DeerFlow 运行时。

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r agent-ops/research/review-requirements.txt
python -S agent-ops/research/build_data.py
python -m pytest agent-ops/test_fuling_v2.py agent-ops/test_supplier_ledger.py agent-ops/test_research_models.py agent-ops/test_v2_evidence.py agent-ops/test_scenario_semantics.py agent-ops/test_public_release.py -q
```

默认生成案例数据，输出 `agent-platform/frontend/public/research/v2.json` 与当前 CSV。语义测试用 LangChain 消息容器，无真实模型调用。校验脚本检查核心文件、数据与 PDF 哈希以及完整公开清单。若主动重新生成媒体或 PDF，清单应随新产物重建，不可伪称字节不变。

## 2. 必要预期结果

| 检查 | 预期 |
|---|---|
| Fuling：600h，无约束 / 25% 行业资源上限 | 均为 138,451.20 元 |
| Fuling：150h，无约束 / 25% 上限 | 45,027 / 44,205 元；差 822 元 |
| Supplier：基线 | 峰值缺口 49 万元，负余额 38 天 |
| Supplier：C1 / 14 天 | 峰值缺口 49 万元，负余额 52 天 |
| Supplier：ALL / 30 天 | 峰值缺口 53 万元，负余额 68 天；不是同一个请求 |
| 状态与事务 | 预测不自动升级，POSTED 不可覆盖，余额不符全部回滚 |

这些都是合成 / ASSUMPTION 下的研究输出，不是实际经营成果。

**Legacy Note：** `models.py::supplier_case` 及对应 `test_research_models.py` Supplier assertions 是早期单订单确定性回归参考；展示中的 Supplier Case 以 `supplier_ledger.py`、`test_supplier_ledger.py` 与 `v2.json` 为准。26万元不是展示案例 结果。

## 3. 报告构建

```sh
python -m pip install -r agent-ops/research/render-requirements.txt
# 非 macOS 请设置一个合法可用的中文 TTF 字体绝对路径：
# export RESEARCH_CJK_FONT=/your/font.ttf
python agent-ops/research/build_reports.py
```

输出在 `output/pdf/`，展示 PDF 同步到 `agent-platform/frontend/public/research/`。仓库 `docs/reports/` 是展示 PDF 副本；正常复算不必重新渲染报告。预期页数为 9 / 8 / 4，重建后应检查所有页面，字体和 PDF 元数据可能导致二进制哈希变化。

## 4. 完整本地平台（可选）

需要 Python 3.12、Node 22+、pnpm 10.26.2、uv、Docker / PostgreSQL。以下仅监听本机，不是公网部署步骤。

```sh
cp agent-ops/.env.example agent-ops/.env
# 本地填写 QWEN_API_KEY、POSTGRES_PASSWORD 和 AGENT_DATABASE_URL；切勿提交。
# URL 的密码需 URL 编码，并与 PostgreSQL 配置一致。
set -a
. agent-ops/.env
set +a
docker compose --env-file agent-ops/.env -f agent-ops/compose.yaml up -d --wait
(cd agent-platform/backend && uv sync --locked --python 3.12 --extra postgres)
(cd agent-platform/frontend && npx --yes pnpm@10.26.2 install --frozen-lockfile)
agent-platform/backend/.venv/bin/python agent-ops/gateway.py
```

另开终端运行：

```sh
cd agent-platform/frontend
node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port 3000
```

浏览器访问 `http://127.0.0.1:3000/workspace/research`，按首次初始化流程创建自己的账号。请自行创建本地账号。模型使用外部服务并可能收费；独立复算不需要密钥。需要 Agent 沙箱文件工具时，按 `agent-ops/README.md` 准备既有沙箱镜像。上游依赖完整安装和首次初始化因本机条件而异，本次验证的是现有本地环境，不宣称新机器一键生产启动。

```sh
# 完整 workspace 测试；AGENT_DATABASE_URL 显式提供真实测试数据库
agent-platform/backend/.venv/bin/python -m pytest agent-ops/test_*.py -q
# 不提供 URL 时两项真实 PG 测试明确 skip，不能计为 passed。
```

## 5. 校验与秘密扫描

```sh
# 在尚未执行数据重建的干净检出中验证发布快照
python scripts/portfolio_verify.py
# 自行安装 Gitleaks 8.24.3 或兼容版本；报告中隐藏匹配值
mkdir -p tmp
gitleaks dir . --redact --ignore-gitleaks-allow --report-format json --report-path tmp/secret-scan.json
```

上游安全测试故意含虚构密钥样例，会触发扫描；必须核查告警，不按文件夹整体豁免。已执行结果见 [扫描报告](docs/SECRET_SCAN_REPORT.md)。本仓库为新建公开仓库，不包含旧开发仓库 Git 历史；未部署在线后端服务。GitHub Pages 的 Agent Demo 在浏览器计算，使用规则识别参数并回放已记录模型调用；无实时模型或在线业务接口。

## 浏览器 Agent Demo

```sh
python -S scripts/export_static_demo_data.py
node --test site/tests/*.test.mjs
```

导出程序从业务数据生成合成输入，并动态运行 Python 生成一致性测试预期。浏览器规则负责识别参数，已记录 Qwen 调用标明回放。详见 [Demo 技术说明](site/README.md)。
