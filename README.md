# 渝研 Agent

一个可以查资料、处理文件、执行代码、制作图片，并交付可继续修改成果的中文 Agent 工作台。基于 DeerFlow 改造，使用 Qwen 与真实工具；默认单 Agent。

输入任务或上传文件后，可以查看工具执行过程，在对话旁预览成果，下载文件，并继续要求修改。会话和执行状态保存在 PostgreSQL，文件按用户和会话隔离。

## 主要能力

| 能力 | 实现 |
|---|---|
| 联网查证 | Qwen 原生搜索、网页读取、来源链接及读取状态 |
| 文件分析 | 上传文件，读取 CSV / 文本，在 Docker 沙箱执行 Python / bash |
| 成果交付 | JSON、Markdown、HTML 等文件预览下载；明确文件生成请求有交付检查与有界重试 |
| 图片与图形 | Qwen 图片生成/编辑、SVG 与可编辑 Draw.io 流程图 |
| 多轮任务 | 保留会话、文件和检查点，继续修改；取消运行与重复提交幂等 |
| 自定义助手 | 用户级模型、工具组与提示配置；默认关闭子 Agent 与第三方 MCP |

交付检查验证文件存在、非空、属于当前会话并已展示，不代替事实核验或内容正确性评测。支持的明确文件生成表达与限制见 [验收说明](docs/AGENT_ACCEPTANCE.md)。

## 本地安装与启动

要求：Python 3.12、uv、Node.js 22+、pnpm 10.26.2、Docker。默认端口 3000 / 8001 / 55433，仅监听本机。

```bash
git clone https://github.com/SGYuhan23/yuyan-bank-research.git
cd yuyan-bank-research
uv sync --project agent-platform/backend --locked --extra postgres
cd agent-platform/frontend
corepack pnpm install --frozen-lockfile
cd ../..
cp agent-ops/.env.example agent-ops/.env.local
```

编辑 `agent-ops/.env.local`：设置自己的 `QWEN_API_KEY`、`POSTGRES_PASSWORD`、`AGENT_DATABASE_URL`。数据库 URL 格式为 `postgresql://agent_platform:<URL编码后的密码>@127.0.0.1:55433/agent_platform`，与 POSTGRES_PASSWORD 一致。模型与端点可以显式配置，不会静默切换模型。不要提交此文件。

```bash
docker pull enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:1.11.0
agent-platform/backend/.venv/bin/python scripts/start_general_agent.py
```

打开 **http://127.0.0.1:3000/**，首次创建管理员，随后新建对话。macOS 可双击 `启动原版Agent.command`。Docker 数据卷、`.deer-flow` 和密钥文件应一起妥善备份。Windows 使用虚拟环境实际的 Python 可执行文件路径。

尝试这些任务：

- 上传 CSV：“读取文件，用 Python 汇总每项金额，生成 result.json 和 report.html 并展示。”
- “保留原版，把第二项数量改为 5，重新计算并生成新版本。”
- “查阅 Python 官方文档，比较 CSV 和 JSON，引用实际读取的来源。”
- “画一张水彩风格的窗边橘猫图片。”
- “画一个包含判断分支的流程图，交付 SVG 和 Draw.io 文件。”

## 实现与验证

- [架构与责任边界](ARCHITECTURE.md)
- [Agent 验收结果与已知限制](docs/AGENT_ACCEPTANCE.md)
- [开源参考与实际落实情况](docs/AGENT_REFERENCES.md)
- [复现步骤](REPRODUCIBILITY.md)

核心代码位于 `agent-platform/`，本项目工具、运行配置和验收位于 `agent-ops/`。DeerFlow 提供基础框架；本项目负责模型装配、联网/媒体工具、交付检查、中文交互和验证，不宣称从零自研框架或超过全部参考项目。

旧银行研究、静态展示与案例源码保留为历史材料，不是当前主产品入口。GitHub Pages 已退出本项目的交付方式；本仓库交付真实可运行的 Agent 源码，不提供公共模型服务。

[第三方归属](third_party/ATTRIBUTION.md) · [DeerFlow MIT 许可证](agent-platform/LICENSE)
