# Repository Structure

项目保留前后端、Agent 扩展、业务模型、测试和构建脚本的原目录结构。静态展示页位于 `site/`，本地运行说明见仓库根目录。

```text
渝研/
├── README.md                       # 30 秒业务入口
├── DEMO.md                         # 3 分钟原生 GitHub 演示
├── ARCHITECTURE.md                  # AI / 程序 / 人工职责
├── REPRODUCIBILITY.md               # 独立复算与完整本地运行
├── DISCLAIMER.md
├── PUBLIC_RELEASE_INVENTORY.json    # 全文件大小与 SHA-256（不自引用）
├── site/                          # 六部分静态展示 HTML / CSS
├── .github/workflows/pages.yml     # 静态 GitHub Pages 发布
├── .gitignore
├── third_party/ATTRIBUTION.md
├── docs/
│   ├── screenshots/                # 11 张真实截图与清单
│   ├── media/                      # 3 段 MP4、12 秒 GIF、录屏脚本说明
│   ├── reports/                    # 三份研究报告
│   ├── FROZEN_CORE_SHA256.json
│   └── SECRET_SCAN_REPORT.md
├── scripts/
│   ├── record_portfolio.cjs
│   ├── export_media.py
│   └── portfolio_verify.py
├── agent-ops/                      # 完整本项目扩展、模型、测试、构建
│   ├── examples/fuling.py
│   ├── research/                   # ledger / ScenarioRequest / build / 报告
│   ├── research_plugin.py
│   ├── research_policy.py
│   ├── test_*.py
│   ├── .env.example
│   └── ...
├── agent-platform/                 # 完整 DeerFlow 前后端与本地适配
│   ├── LICENSE
│   ├── frontend/                   # 含锁文件与 research 页面
│   ├── backend/                    # app / harness / extension-api / tests
│   ├── skills/
│   └── ...

```

排除：本地数据库、依赖安装目录、缓存、旧交付 ZIP、原始会话/私有上下文、账号与真实凭据；保留无秘密 `.env.example`。私人运行记录不公开，不影响功能源码完整性；以根目录复算指南与公开文件清单为准。


当前事实来源快照保留在 `agent-ops/research/evidence-v2/sources/`，供 build_facts.py 使用；同级过期运行结果不属于当前技术证据，不随公开版本提供。
