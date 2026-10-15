import { useEffect, useRef } from "react";
import { Tabs, Tag, Tooltip, Collapse } from "antd";
import { money } from "./ToolResult";
import { evaluate } from "../../js/supplier-engine.js";
import { scenarios } from "../demo/scenarios";
function Rows({ rows }: { rows: any[] }) {
  return (
    <dl className="trace-values">
      {rows.map(([k, v], i) => (
        <div key={i}>
          <dt>{k}</dt>
          <dd>{String(v)}</dd>
        </div>
      ))}
    </dl>
  );
}
export default function AgentTrace({
  session,
  step,
  busy,
  output,
  trace,
  recorded,
}: any) {
  const panelRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const panel = panelRef.current;
    const current = panel?.querySelectorAll<HTMLElement>(
      ".execution-workspace > li",
    )[step];
    if (panel && current && window.matchMedia("(min-width: 901px)").matches) {
      panel.scrollTo({
        top: Math.max(
          0,
          panel.scrollTop +
            current.getBoundingClientRect().top -
            panel.getBoundingClientRect().top -
            190,
        ),
        behavior: "smooth",
      });
    }
  }, [step]);
  const req = session.binding.request,
    p = req.parameters,
    id = session.id,
    r = output?.value,
    base = evaluate(r?.before || session.ledger),
    scene = scenarios.find((s) => s.id === id)!;
  const version = r?.before?.version ?? session.ledger.version;
  const parameterRows =
    id === "allocation"
      ? [
          ["新增经营工时", p.available_hours + " 小时"],
          [
            "行业分散约束",
            p.industry_limit ? "单一行业 ≤ 已选工时 25%" : "不启用",
          ],
          ["候选任务", "当前完整候选集"],
          ["每户最大动作", "1 项"],
        ]
      : id === "customer"
        ? [
            ["固定余额", money(p.deposit_fen) + " 元"],
            [
              "客户 A 年交易",
              session.data.fuling.comparisons[0].annual_transaction_count +
                " 笔",
            ],
            [
              "客户 B 员工",
              session.data.fuling.comparisons[1].payroll_employee_count + " 人",
            ],
          ]
        : id === "cashflow"
          ? [
              [
                "影响客户",
                p.customer_id === "C1" ? "C1 核心客户" : "ALL 所有客户",
              ],
              ["延期", p.delay_days + " 天"],
              ["折扣", p.discount],
              ["额外费用", money(p.fee_fen) + " 元"],
              ["追加预付", money(p.advance_fen) + " 元"],
            ]
          : [
              ["事实余额", money(base.actual_balance_fen) + " 元"],
              [
                "实际付款",
                money(
                  session.ledger.events.find((e) => e.event_id === p.event_id)
                    .amount_fen,
                ) + " 元",
              ],
              ["观察余额", money(p.observed_balance_fen) + " 元"],
            ];
  const resultRows = !r
    ? []
    : id === "allocation"
      ? [
          ["入选任务", r.selected.length + " 项"],
          ["使用工时", r.hours + " 小时"],
          ["假设净贡献", money(r.benefit_fen) + " 元"],
          ...(r.free
            ? [["机会成本", money(r.free.benefit_fen - r.benefit_fen) + " 元"]]
            : []),
        ]
      : id === "customer"
        ? r.customers.map((c, i) => [
            "客户 " + (i === 0 ? "A" : "B"),
            c.best.action_type,
          ])
        : id === "cashflow"
          ? [
              [
                "基准场景",
                money(r.baseline.peak_gap_fen) +
                  " 元 / " +
                  r.baseline.negative_days +
                  " 天",
              ],
              [
                "延期场景",
                money(r.scenario.peak_gap_fen) +
                  " 元 / " +
                  r.scenario.negative_days +
                  " 天",
              ],
            ]
          : [
              ["计算余额", money(r.computed) + " 元"],
              ["观察余额", money(r.observed) + " 元"],
              ["余额核对", r.ok ? "✓ 一致" : "✕ 不一致"],
              ["付款状态", r.ok ? "已入账" : "未写入"],
              ["账本版本", r.before.version + " → " + r.after.version],
              [
                "变更历史",
                "+" + (r.after.history.length - r.before.history.length),
              ],
            ];
  const conclusion = !r
    ? "等待工具结果"
    : id === "allocation"
      ? `在当前合成假设下，${r.selected.length} 项任务是 ${r.hours} 小时内优先验证的对象。${r.free ? "资源分散的机会成本为 " + money(r.free.benefit_fen - r.benefit_fen) + " 元。" : ""}入选不等于收益已实现。`
      : id === "customer"
        ? "余额一样，不代表经营机会一样。客户 A 的主要驱动是交易频次，客户 B 的主要驱动是员工数量。"
        : id === "cashflow"
          ? `最大缺口${r.scenario.peak_gap_fen === r.baseline.peak_gap_fen ? "没有增加" : "增加 " + money(r.scenario.peak_gap_fen - r.baseline.peak_gap_fen) + " 元"}；负余额持续时间 ${r.baseline.negative_days} → ${r.scenario.negative_days} 天。缺口规模与持续时间需要一起看。`
          : r.ok
            ? "核对一致后，这笔实际付款和新的账本状态一次性提交。"
            : "系统没有先写入再补救。付款、余额核对和账本版本必须一起通过，否则全部不提交。";
  const titles = [
    "理解业务问题",
    "整理分析参数",
    "检查计算条件",
    id === "allocation"
      ? "运行经营资源优化"
      : id === "customer"
        ? "比较五类经营动作"
        : id === "cashflow"
          ? "运行资金测算"
          : "执行付款与余额核对",
    "核对计算结果",
    "整理经营结论",
  ];
  const contents = [
    <>
      <Rows
        rows={[
          ["业务场景", scene.theme],
          [
            "分析目标",
            id === "allocation"
              ? "选择更值得优先验证的经营任务"
              : id === "customer"
                ? "固定余额，比较业务特征"
                : id === "cashflow"
                  ? "预计尾款延期"
                  : "付款与余额一起核对",
          ],
        ]}
      />
      <p className="small muted">
        {recorded
          ? "参考已有 C1 / 14 天模型提案"
          : "使用当前演示案例的完整业务问题"}
      </p>
    </>,
    <>
      <Rows rows={parameterRows} />
      <details>
        <summary>查看结构化参数</summary>
        <pre>{JSON.stringify(p, null, 2)}</pre>
      </details>
    </>,
    <>
      <ul className="trace-checks">
        {id === "allocation" ? (
          <>
            <li>✓ 候选任务集{session.variant ? "未变化" : "已加载"}</li>
            <li>✓ 可用新增经营工时已确定：{p.available_hours} 小时</li>
            <li>
              ✓ 行业资源分散约束：
              {p.industry_limit ? "单一行业 ≤ 已选工时 25%" : "不启用"}
            </li>
            <li>✓ 每户最多选择 1 项新增动作</li>
          </>
        ) : id === "customer" ? (
          <>
            <li>✓ 两个合成对照客户已加载</li>
            <li>✓ 两个客户余额均为 {money(p.deposit_fen)} 元</li>
            <li>✓ 客户 A 主要差异变量：交易频次</li>
            <li>✓ 客户 B 主要差异变量：员工数量</li>
            <li>✓ 其余对照字段按当前实验设定</li>
          </>
        ) : (
          <>
            <li>✓ 分析对象已确定</li>
            <li>✓ 时间与金额条件完整</li>
            <li>✓ 当前账本版本：{version}</li>
          </>
        )}
      </ul>
      <strong className="confirmation-wait">
        {session.binding.confirmed
          ? "✓ 已收到用户确认"
          : "等待用户确认 · 尚未计算"}
      </strong>
    </>,
    <>
      <code className="business-tool">{scene.tool}</code>
      {id === "allocation" ? (
        <Rows
          rows={[
            ["候选动作", session.data.fuling.actions.length + " 项"],
            ["可用工时", p.available_hours + " 小时"],
          ]}
        />
      ) : id === "cashflow" ? (
        <Rows
          rows={[
            ["读取订单", session.ledger.orders.length + " 笔"],
            [
              "读取现金事件",
              session.ledger.events.filter((e) =>
                [
                  "materials",
                  "production",
                  "shipment",
                  "receivable",
                  "prepayment",
                  "fee",
                  "quality_deduction",
                ].includes(e.event_type),
              ).length + " 条",
            ],
            [
              "基准场景",
              money(base.peak_gap_fen) + " 元 / " + base.negative_days + " 天",
            ],
          ]}
        />
      ) : id === "customer" ? (
        <p>分别重新计算：结算、存款关系、代发 / 支付、供应链连接、客户维护。</p>
      ) : (
        <Rows rows={parameterRows} />
      )}
      {r ? (
        <Rows rows={resultRows} />
      ) : (
        <p className="trace-running">正在计算…</p>
      )}
    </>,
    <>
      {r && (
        <ul className="trace-checks">
          {id === "allocation" ? (
            <>
              <li>✓ 结果对应当前工时条件</li>
              <li>✓ 结果对应当前行业约束</li>
              <li>✓ 没有复用上一轮参数</li>
              <li>✓ 入选任务总工时不超过可用工时</li>
            </>
          ) : id === "customer" ? (
            <>
              <li>✓ 两个客户使用同一套经营动作估值规则</li>
              <li>✓ 余额控制条件一致</li>
              <li>✓ 建议差异来自业务驱动变量</li>
              <li>✓ 结果不是按客户名称预设</li>
            </>
          ) : (
            <>
              <li>✓ 参数快照与本次问题一致</li>
              <li>✓ 结果对应本次分析请求</li>
              <li>✓ 没有复用上一轮参数</li>
              <li>
                ✓{" "}
                {id === "reconcile"
                  ? `账本版本 ${r.before.version} → ${r.after.version}`
                  : `当前账本版本仍为 ${session.ledger.version}`}
              </li>
            </>
          )}
          {id === "reconcile" && (
            <li>
              {r.ok ? "✓ 核对一致，一次性提交" : "✓ 余额不符，已确认全部回滚"}
            </li>
          )}
        </ul>
      )}
    </>,
    <p className="trace-conclusion">{conclusion}</p>,
  ];
  return (
    <aside ref={panelRef} className="trace-panel">
      <div className="trace-heading">
        <span className="eyebrow">可观察的执行过程</span>
        <h2>Agent 执行轨迹</h2>
        {recorded ? (
          <Tooltip title="该步骤来自此业务问题的一次真实脱敏模型调用记录；金额和现金流由当前浏览器重新计算，本页面不会再次在线调用模型。">
            <Tag color="cyan">已有模型调用</Tag>
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
                {session.variant && (
                  <p className="trace-note">
                    上一轮参数已失效，本轮重新确认与计算。
                  </p>
                )}
                <ol className="execution-workspace">
                  {titles.map((title, i) => (
                    <li
                      key={title}
                      className={
                        i > step
                          ? "future"
                          : i === step && step !== 5
                            ? "active"
                            : "complete"
                      }
                    >
                      <span className="trace-node">
                        {i < step || step === 5
                          ? "✓"
                          : String(i + 1).padStart(2, "0")}
                      </span>
                      <h3>{title}</h3>
                      {i <= step && (
                        <div className="trace-body">{contents[i]}</div>
                      )}
                    </li>
                  ))}
                </ol>
                {recorded && (
                  <div className="record-note">
                    <p>
                      模型提出结构化参数；程序检查必填字段和业务边界，确认后再调用确定性工具。
                    </p>
                    <p>{trace.validation_summary}</p>
                    <Collapse
                      size="small"
                      items={[
                        {
                          key: "record",
                          label: "查看此问题的真实调用记录",
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
                              <p>{trace.context_summary}</p>
                              <p>{trace.confirmation_summary}</p>
                              <pre>
                                {JSON.stringify(
                                  {
                                    confirmed_request: trace.confirmed_request,
                                    tool: trace.tool,
                                    arguments: trace.arguments,
                                    result: trace.result,
                                  },
                                  null,
                                  2,
                                )}
                              </pre>
                              <p>{trace.answer}</p>
                              <p>{trace.boundary}</p>
                            </>
                          ),
                        },
                      ]}
                    />
                  </div>
                )}
                <p className="small muted">
                  仅展示可观察操作，不展示模型隐藏思维。{busy ? "执行中。" : ""}
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
                <Rows rows={resultRows} />
                <p>{conclusion}</p>
              </>
            ),
          },
          {
            key: "basis",
            label: "计算依据",
            children: (
              <>
                <p>
                  参数来源：当前演示案例{recorded ? "与对应的历史模型提案" : ""}
                  。金额按整数分计算。
                </p>
                <details>
                  <summary>查看本次确认参数与请求标识</summary>
                  <pre>{JSON.stringify(output?.snapshot || req, null, 2)}</pre>
                </details>
                <p>
                  单价、采用率、成本均为研究假设。参数确认不代表合同已落实。
                </p>
              </>
            ),
          },
        ]}
      />
    </aside>
  );
}
