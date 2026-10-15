import { Alert, Collapse, Table, Tag } from "antd";
import CashCurve from "./CashCurve";
export const money = (fen: number) =>
  (fen / 100).toLocaleString("zh-CN", { maximumFractionDigits: 2 });
function Metrics({ items }: { items: [string, string][] }) {
  return (
    <div className="metrics">
      {items.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}
export default function ToolResult({
  id,
  output,
}: {
  id: string;
  output: any;
}) {
  const r = output.value;
  if (id === "allocation")
    return (
      <>
        <Metrics
          items={[
            ["入选任务", r.selected.length + " 项"],
            ["使用工时", r.hours + " 小时"],
            ["假设净贡献", money(r.benefit_fen) + " 元"],
          ]}
        />
        {r.free && (
          <Alert
            type="info"
            showIcon
            message={`资源分散的机会成本：${money(r.free.benefit_fen - r.benefit_fen)} 元`}
            description={`不设置约束：${money(r.free.benefit_fen)} 元 → 加入约束：${money(r.benefit_fen)} 元。差额是合成模型输出；25% 是研究中的资源分散假设，不是监管要求或授信限额。`}
          />
        )}
        <h3>优先验证的经营任务</h3>
        <Table
          size="small"
          pagination={false}
          rowKey="id"
          dataSource={r.actions.slice(0, 6)}
          columns={[
            {
              title: "合成客户 / 任务",
              dataIndex: "customer_id",
              render: (s, a: any) => (
                <>
                  <strong>{s.replace("SYN-V2-", "客户 ")}</strong>
                  <div>{a.action_type}</div>
                </>
              ),
            },
            {
              title: "工时",
              dataIndex: "service_hours",
              render: (h) => h + " h",
            },
            {
              title: "假设净贡献",
              dataIndex: "benefit_fen",
              render: (n) => money(n) + " 元",
            },
          ]}
        />
        <p className="muted small">
          从当前候选任务中选择组合，每户最多 1
          项新增动作。单价、采用率、成本及工时均为研究假设。
        </p>
        <Collapse
          items={[
            {
              key: "tasks",
              label: "查看入选任务的成本、材料与停止条件",
              children: (
                <div className="task-evidence">
                  {r.actions.map((a) => (
                    <section key={a.id}>
                      <h4>
                        {a.customer_id} · {a.action_type}
                      </h4>
                      <p>
                        {a.value_formula}；实施成本{" "}
                        {money(a.implementation_cost_fen)} 元。
                      </p>
                      <p>待验证：{a.evidence_requirement}</p>
                      <p>停止条件：{a.stop_condition}</p>
                    </section>
                  ))}
                </div>
              ),
            },
          ]}
        />
      </>
    );
  if (id === "customer")
    return (
      <>
        <div className="customer-results">
          {r.customers.map(({ customer: c, best: b }: any, i: number) => (
            <section key={i}>
              <Tag color="cyan">客户 {i === 0 ? "A" : "B"} · 合成对照</Tag>
              <p className="muted">余额 {money(c.deposit_fen)} 元</p>
              <h3>{b.action_type}</h3>
              <p className="driver">
                {i === 0
                  ? `年度交易 ${c.annual_transaction_count.toLocaleString()} 笔`
                  : `可授权员工 ${c.payroll_employee_count} 人`}
              </p>
              <p>{b.value_formula}</p>
              <dl>
                <dt>实施成本</dt>
                <dd>{money(b.implementation_cost_fen)} 元</dd>
                <dt>所需工时</dt>
                <dd>{b.service_hours} 小时</dd>
                <dt>假设净贡献</dt>
                <dd>{money(b.benefit_fen)} 元</dd>
              </dl>
              <p className="small">待验证：{b.evidence_requirement}</p>
              <p className="small">停止条件：{b.stop_condition}</p>
            </section>
          ))}
        </div>
        <p className="small muted">
          控制余额后的合成实验。单价、采用率与成本均为
          ASSUMPTION，不代表真实客户建议。
        </p>
      </>
    );
  if (id === "cashflow") {
    const b = r.baseline,
      s = r.scenario;
    return (
      <>
        <Metrics
          items={[
            ["峰值资金缺口", money(s.peak_gap_fen) + " 元"],
            ["负余额持续时间", s.negative_days + " 天"],
          ]}
        />
        <div className="comparison-strip">
          <span>
            基准：{money(b.peak_gap_fen)} 元 / {b.negative_days} 天
          </span>
          <strong>→</strong>
          <span>
            本次：{money(s.peak_gap_fen)} 元 / {s.negative_days} 天
          </span>
        </div>
        <CashCurve baseline={b} scenario={s} />
        <p className="result-explanation">
          {s.peak_gap_fen === b.peak_gap_fen
            ? "最大缺口没有继续扩大"
            : `最大缺口增加了 ${money(s.peak_gap_fen - b.peak_gap_fen)} 元`}
          ，但资金紧张的持续时间从 {b.negative_days} 天延长到 {s.negative_days}{" "}
          天。企业需要多承受 {s.negative_days - b.negative_days} 天的资金压力。
        </p>
        {!s.complete && (
          <Alert type="warning" message="存在逾期或争议，预测不完整" />
        )}
      </>
    );
  }
  const before = r.before,
    after = r.after,
    eid = output.snapshot.parameters.event_id,
    be = before.events.find((e) => e.event_id === eid),
    ae = after.events.find((e) => e.event_id === eid);
  return (
    <>
      <Alert
        type={r.ok ? "success" : "error"}
        showIcon
        message={
          r.ok ? "核对一致 · 实际支付已入账" : "余额不一致 · 本次操作全部撤销"
        }
        description={
          r.ok
            ? "实际付款与余额核对已一起保存。"
            : "计算余额与观察余额不一致，没有留下半完成记录。"
        }
      />
      <Metrics
        items={[
          ["计算余额", money(r.computed) + " 元"],
          ["观察余额", money(r.observed) + " 元"],
        ]}
      />
      <div className="ledger-diff">
        <div>
          <span>账本版本</span>
          <strong>
            {before.version} → {after.version}
          </strong>
        </div>
        <div>
          <span>事件</span>
          <strong>{r.ok ? "既有付款更新为已入账" : "未新增 / 未修改"}</strong>
        </div>
        <div>
          <span>变更历史</span>
          <strong>
            {after.history.length - before.history.length === 0
              ? "未新增"
              : "+" + (after.history.length - before.history.length)}
          </strong>
        </div>
        <div>
          <span>付款状态</span>
          <strong>
            {be.status} → {ae.status}
          </strong>
        </div>
      </div>
      <p className="small muted">
        登记的是既有采购付款，不重复新增现金事件。日期与余额核对在事务副本中执行，一致才提交。
      </p>
    </>
  );
}
