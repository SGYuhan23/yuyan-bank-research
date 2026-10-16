# 渝研原版受控交互演示（源码保留）

本目录不再作为 Pages 发布产物。当前公开研究页、报告与模拟数据见 [research-showcase](../research-showcase/README.md)。下文描述原版功能与历史调用，不是当前展示案例。

React / TypeScript / Vite / Ant Design，使用 HashRouter 适配 GitHub Pages。Landing 先解释产品，再进入四个完整业务问题。Demo 不开放自由文本输入；选择问题、确认参数与 follow-up 都是受控交互。

## 运行

从仓库根目录执行：

```sh
python -S agent-ops/research/build_data.py
python -S scripts/export_static_demo_data.py
cd site
pnpm install --frozen-lockfile
pnpm test
pnpm build
pnpm preview
```

开发模式先执行一次 build 以准备静态资源，然后运行 `pnpm dev`。生产构建只发布 dist。Python、测试预期结果、模型密钥与本地配置不进入 Pages。

## 分工

- `src/pages/`：Landing、Demo 选择、Agent 演示、真实截图与说明。
- `src/demo/scenarios.ts`：完整业务问题与预设输入，不存最终计算答案。
- `src/demo/runtime.js`：展示适配器，调用既有引擎；每轮确认后重新计算。
- `src/components/`：参数卡、结果、现金曲线、可观察执行轨迹与合同依据。
- `js/fuling-engine.js`：分组背包与行业资源约束。
- `js/supplier-engine.js`：整数分金额、逐日现金流与延期情景。
- `js/contract-engine.js`：验收→开票→预计回款，保留固定日期和状态边界。
- `js/ledger-engine.js`：事务副本核对、失败回滚、版本和幂等校验。
- `js/scenario-state.js`：确认参数快照、请求与版本绑定，追加问题使旧结果失效。
- `tests/`：Python 动态预期对照，以及受控展示适配器的确认、回滚和结果绑定回归。

现有引擎、有限规则解析器及历史 trace 回放模块保留源码；新公开入口不提供任意文本解析。演示状态保存在内存中，重新进入案例即重置。不支持真实交易、部分核销或授信。

## 真实性边界

四个场景的参数由 Scenario fixture 提供。执行动画仅展示可观察的步骤，绝不展示或编造模型隐藏思维。结果调用当前浏览器引擎，不能读取测试预期作为答案。

C1 / 14 天场景附有一条对应当前完整业务问题的真实 Qwen 脱敏调用记录。模型根据该问题提出 C1、延期 14 天，以及折扣、额外费用和追加预付款均为 0 的结构化参数；本次提案字段完整，程序未修改模型参数。程序随后检查必填字段、业务边界和当前账本版本，经确认后再调用确定性工具。GitHub Pages 只回放这次调用记录，并在浏览器端重新计算关键金额和现金流，不会在页面中再次在线调用模型。ALL / 30 天追加问题与其他场景均标为演示轨迹。最终解释由工具输出和受控文案生成，没有在线 LLM。

金额、日期、动作和现金流均调用既有引擎。结果可查看参数快照与版本；余额失败时显示实际前后事件、版本、历史差异。25% 是资源分散研究假设，非监管或授信要求。
