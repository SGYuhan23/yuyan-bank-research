import { Steps, Tabs, Tag, Tooltip, Collapse } from "antd";
import { money } from "./ToolResult";
export default function AgentTrace({
  session,
  step,
  busy,
  output,
  trace,
  recorded,
}: {
  session: any;
  step: number;
  busy: boolean;
  output: any;
  trace: any;
  recorded: boolean;
}) {
  const titles = [
    "识别业务场景",
    "提取业务参数",
    "检查计算条件",
    "运行确定性工具",
    "校验结果与版本",
    "生成受控解释",
  ];
  const req = session.binding.request,
    descriptions = [
      recorded
        ? "参考已有 C1 / 14 天模型提案"
        : "参数由当前 Scenario fixture 提供",
      step >= 1 ? "已整理客户、时间与成本字段" : "等待提取",
      step >= 2
        ? session.binding.confirmed
          ? "参数已确认"
          : "等待你逐项确认"
        : "等待检查",
      step >= 3 ? "按确认快照在浏览器重新计算" : "确认后才运行",
      step >= 4 ? "核对参数快照、账本版本与工具返回" : "等待计算",
      step >= 5 ? "解释来自本次工具输出" : "等待结果",
    ];
  const result = output?.value;
  const compact = result
    ? session.id === "allocation"
      ? {
          任务数: result.selected.length,
          工时: result.hours,
          假设净贡献元: money(result.benefit_fen),
        }
      : session.id === "cashflow"
        ? {
            峰值缺口元: money(result.scenario.peak_gap_fen),
            负余额天数: result.scenario.negative_days,
            账本版本: output.snapshot.base_version,
          }
        : session.id === "customer"
          ? result.customers.map((c) => ({
              建议: c.best.action_type,
              净贡献元: money(c.best.benefit_fen),
            }))
          : {
              核对一致: result.ok,
              计算余额元: money(result.computed),
              版本变化: [result.before.version, result.after.version],
              历史增量:
                result.after.history.length - result.before.history.length,
            }
    : null;
  return (
    <aside className="trace-panel">
      <div className="trace-heading">
        <span className="eyebrow">可观察的执行过程</span>
        <h2>Agent 执行轨迹</h2>
        {recorded ? (
          <Tooltip title="此步骤来自已有的脱敏模型调用记录；关键金额由当前浏览器重新计算。不是本次在线模型调用。">
            <Tag color="cyan">已记录模型调用</Tag>
          </Tooltip>
        ) : (
          <Tag>演示执行轨迹</Tag>
        )}
      </div>
      <Tabs
        defaultActiveKey="trace"
        items={[
          {
            key: "trace",
            label: "执行轨迹",
            children: (
              <>
                <Steps
                  direction="vertical"
                  size="small"
                  current={step}
                  status={step === 5 ? "finish" : "process"}
                  items={titles.map((title, i) => ({
                    title,
                    description: descriptions[i],
                    status:
                      i < step || step === 5
                        ? "finish"
                        : i === step
                          ? "process"
                          : "wait",
                  }))}
                />
                <div className="trace-note" aria-live="polite">
                  {busy
                    ? "执行中 · 步骤按约 450ms 展开"
                    : step === 2
                      ? "等待参数确认，尚未计算"
                      : step === 5
                        ? "本轮执行已完成"
                        : "按步骤显示可观察操作"}
                </div>
                {recorded && trace && (
                  <div className="record-note">
                    <strong>这条记录实际证明了什么？</strong>
                    <p>
                      原提示已指定 C1 / 14
                      天。模型提案留空了折扣、费用、预付，由验收程序依原问题补为
                      0。
                    </p>
                    <p>
                      上方业务问题是本次演示的完整表述，与历史提示并非同一句话。没有新的在线
                      Qwen 调用。
                    </p>
                    <Collapse
                      size="small"
                      items={[
                        {
                          key: "record",
                          label: "核对原始提示与模型提案",
                          children: (
                            <>
                              <p>{trace.actual_user_prompt}</p>
                              <pre>
                                {JSON.stringify(
                                  trace.original_model_proposal.request,
                                  null,
                                  2,
                                )}
                              </pre>
                              <p>{trace.correction_summary}</p>
                              <p>{trace.system_policy_summary}</p>
                            </>
                          ),
                        },
                      ]}
                    />
                  </div>
                )}
                <p className="small muted">
                  展示的是场景、参数、工具及结果，不是模型隐藏思维。动画仅控制步骤呈现。
                </p>
              </>
            ),
          },
          {
            key: "result",
            label: "结果详情",
            disabled: !output,
            children: (
              <>
                <p>本次实际工具返回摘要</p>
                <pre>{JSON.stringify(compact, null, 2)}</pre>
                <p className="small muted">
                  完整返回包含日序列或任务明细；主对话展示业务解释。
                </p>
              </>
            ),
          },
          {
            key: "basis",
            label: "计算依据",
            children: (
              <>
                <p>
                  参数来源：
                  {recorded
                    ? "场景预设 + 对应的脱敏历史提案"
                    : "当前 Scenario fixture"}
                </p>
                <p>工具仅消费已确认快照。金额按整数分计算。</p>
                <pre>{JSON.stringify(output?.snapshot || req, null, 2)}</pre>
                <p>
                  确认状态：{session.binding.confirmed ? "已确认" : "待确认"}
                </p>
                <p className="small muted">
                  所有单价、采用率和成本是研究假设。参数确认不代表真实合同已落实。
                </p>
              </>
            ),
          },
        ]}
      />
    </aside>
  );
}
