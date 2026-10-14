# 第三方归属与本项目边界

## DeerFlow upstream

- 上游：[bytedance/deer-flow](https://github.com/bytedance/deer-flow)
- 本地固定基线：`5b2a1352cd67d5577ebf027b9f920e7ef1e360d4`
- 位置：[`agent-platform/`](../agent-platform/)
- 许可证：[MIT 原文](../agent-platform/LICENSE)，保留原版权声明：Bytedance Ltd. and/or its affiliates；DeerFlow Authors。

DeerFlow 提供完整 Agent framework 与前后端基础，包括 LangGraph harness、模型/工具编排、会话与流式执行、认证和扩展机制。**本项目没有从零自研整个 Agent framework。** 本次公开 snapshot 不迁移旧 `.git` 历史；保留代码中的上游版权、许可证及依赖声明。

## 本项目实现与适配

- `agent-ops/`：Fuling 经营分析、Supplier 条件与事件账本、ScenarioRequest、业务 API/工具扩展、确定性回答守卫、构建/报告/测试与本地集成脚本。
- `agent-platform/frontend/src/app/workspace/research/page.tsx`：研究展示及账本交互；另有既有 examples 页面、中文品牌、导航与产物体验的本地适配。
- 既有框架侧交互策略适配保留在完整源码中，不改称自主研发框架。
- 根文档、`docs/` 与 `scripts/`：本次 GitHub portfolio 整理与真实页面采集支持，不增加业务模型。
- 早期 `yuqi-core`：未接入主平台，本次不再放入公开包；原工作区历史保留，不计为当前作品。

## 其他组件与资料

LangGraph / LangChain、Next.js / React、PostgreSQL、Playwright、ReportLab 等依赖归各自作者所有，具体版本与许可证以仓库锁文件、依赖清单和相应上游声明为准。Qwen 是外部模型服务，代码包不包含模型权重或服务密钥。录屏转换使用 FFmpeg（通过 imageio-ffmpeg 或本机安装获得），只发布实际操作生成的媒体，不捆绑第三方可执行文件。

政府网站事实与引文用于来源核验，来源登记见 [`sources.json`](../agent-platform/frontend/public/research/sources.json) 和 [`fuling_public_facts.json`](../agent-platform/frontend/public/research/fuling_public_facts.json)。来源资料不因随仓库附带就成为本项目原创或由本项目重新授权。

保留所有上游许可证；未为整个混合仓库擅自添加统一的新许可证。使用或再分发代码时应核对相应目录的许可条件。
