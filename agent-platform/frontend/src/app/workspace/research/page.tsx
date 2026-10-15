"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { fetch as authFetch } from "@/core/api/fetcher";

const displayCustomerId = (id: string) => id.replace(/^SYN-V2-(\d+).*$/, "合成客户 $1");

type Event = {
  event_id: string;
  order_id: string;
  event_type: string;
  status: string;
  amount_fen: number;
  planned_date: string;
  confirmed_date: string | null;
  posted_date: string | null;
  evidence: string;
  source: string;
  prediction_confidence?: string;
};
type Case = {
  version: number;
  as_of: string;
  opening_date: string;
  events: Event[];
  history: unknown[];
  orders: {
    order_id: string;
    customer_id: string;
    name: string;
    payment_terms?: {
      type: string;
      payment_after_invoice_days?: number;
      invoice_after_acceptance_days?: number;
    };
  }[];
};
type Calc = {
  actual_balance_fen: number;
  peak_gap_fen: number;
  minimum_date: string;
  minimum_drivers: string[];
  negative_days: number;
  closing_fen: number;
  series: { date: string; balance_fen: number }[];
  complete: boolean;
  overdue_unresolved: string[];
  disputed_events: string[];
  evidence_completeness: { supported: number; required: number };
  concentration: { top1: string; top3: string };
  discount_cost_fen?: number;
  fee_fen?: number;
};
type ScenarioSnapshot = {
  request_id: string;
  case_id: string;
  base_version: number;
  customer_id: string | null;
  delay_days: number | null;
  discount: string | null;
  fee_fen: number | null;
  advance_fen: number | null;
  confirmation_status: string;
};
type ScenarioProposal = {
  request: ScenarioSnapshot;
  parameter_hash: string;
  missing_fields: string[];
};
type Stored = { case_id: string; case: Case; calculation: Calc };
type Action = {
  id: string;
  customer_id: string;
  sector: string;
  action_type: string;
  service_hours: number;
  expected_benefit_fen: number;
  implementation_cost_fen: number;
  benefit_fen: number;
  evidence_requirement: string;
  value_formula: string;
  business_drivers: string;
  stop_condition: string;
  source_fact_ids: string;
  risk_confidence: string;
  reason?: string;
};
type Allocation = {
  name: string;
  constraint: string;
  capacity_hours: number;
  hours: number;
  benefit_fen: number;
  selected: string[];
  sector_hours: Record<string, number>;
  reason: string;
  rejected: Action[];
  max_sector_share: string;
};
type Fact = {
  fact_id: string;
  metric: string;
  value: string;
  period: string;
  source: string;
  model_usage: string;
  verification_status: string;
  limitation: string;
};
type Bundle = {
  version: string;
  fuling: {
    disclosure: string;
    facts: Fact[];
    actions: Action[];
    allocations: Allocation[];
    sensitivity: (Allocation & { realization_rate: string })[];
  };
  supplier: { base: Calc };
  deposit: { base: { contribution_fen: number; break_even_rate: string } };
  roles: { role: string; work: string }[];
};
const money = (v: number) =>
  (v / 100).toLocaleString("zh-CN", { maximumFractionDigits: 2 }) + "元";
const card = "rounded-xl border bg-card p-5 md:p-7";
const button =
  "rounded-lg border px-4 py-2 text-sm hover:bg-muted disabled:opacity-40";
const input = "w-full rounded-md border bg-background px-3 py-2";
const labels: Record<string, string> = {
  PROJECTED: "预测安排",
  CONFIRMED: "已确认安排",
  POSTED: "已入账事实",
  DISPUTED: "争议待核对",
  CANCELLED: "已取消",
  purchase_order: "采购订单",
  materials: "原料采购",
  production: "生产支出",
  shipment: "发货/物流",
  acceptance: "收货验收",
  invoice: "开票",
  receivable: "回款",
  prepayment: "预付款",
  fee: "费用",
  quality_deduction: "质量扣款",
};
async function api<T>(action: string, payload: unknown): Promise<T> {
  const r = await authFetch("/api/plugins/yuyan.research/actions/" + action, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const problem = (await r.json().catch(() => ({ detail: "" }))) as {
      detail?: string;
    };
    throw Error(
      typeof problem.detail === "string" && problem.detail
        ? problem.detail
        : `服务暂不可用（${r.status}），可重试；研究资料仍可查看。`,
    );
  }
  const result = (await r.json()) as T & {
    error?: { message: string; difference_fen?: number };
    committed?: boolean;
  };
  if (result.error) throw Error(result.error.message);
  return result;
}
function Curve({ result }: { result: Calc }) {
  const values = result.series.map((x) => x.balance_fen);
  const low = Math.min(0, ...values),
    high = Math.max(1, ...values);
  const y = (n: number) => 170 - ((n - low) / (high - low)) * 140;
  return (
    <figure className="my-5">
      <svg
        viewBox="0 0 640 205"
        className="w-full"
        role="img"
        aria-label="预测日终现金曲线"
      >
        <line
          x1="25"
          x2="620"
          y1={y(0)}
          y2={y(0)}
          stroke="#9ca3af"
          strokeDasharray="4"
        />
        <polyline
          fill="none"
          stroke="#16745a"
          strokeWidth="3"
          points={values
            .map(
              (n, i) =>
                `${25 + (i / Math.max(1, values.length - 1)) * 595},${y(n)}`,
            )
            .join(" ")}
        />
        <text x="25" y="198" fontSize="12">
          {result.series[0]?.date}
        </text>
        <text x="515" y="198" fontSize="12">
          {result.series.at(-1)?.date}
        </text>
      </svg>
      <figcaption className="text-muted-foreground text-xs">
        MODEL OUTPUT · 包含未落实预测；虚线为零余额，日终曲线不保证日内支付。
      </figcaption>
    </figure>
  );
}
function Metrics({ r }: { r: Calc }) {
  return (
    <dl className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {[
        ["账本事实余额", money(r.actual_balance_fen)],
        ["预测峰值缺口", money(r.peak_gap_fen)],
        ["最低点日期", r.minimum_date],
        ["负余额天数", r.negative_days + "天"],
      ].map(([k, v]) => (
        <div key={k}>
          <dt className="text-muted-foreground text-xs">{k}</dt>
          <dd className="mt-2 text-lg font-semibold">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
export default function Research() {
  const [data, setData] = useState<Bundle>();
  const [trace, setTrace] = useState<{
    answer: string;
    recorded_at: string;
    boundary: string;
    actual_user_prompt: string;
    system_policy_summary: string;
    parameters_prespecified: boolean;
  }>();
  const [tab, setTab] = useState("home");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [allocation, setAllocation] = useState(0);
  const [stored, setStored] = useState<Stored>();
  const [caseList, setCaseList] = useState<
    { case_id: string; version: number }[]
  >([]);
  const [scenario, setScenario] = useState<Calc>();
  const [proposal, setProposal] = useState<ScenarioProposal>();
  const [proposals, setProposals] = useState<ScenarioProposal[]>([]);
  const [reconcileDate, setReconcileDate] = useState("2027-02-16");
  const [observedBalance, setObservedBalance] = useState(200000);
  function invalidateScenario() {
    setScenario(undefined);
    if (proposal)
      void api("invalidate_scenario", {
        request_id: proposal.request.request_id,
      }).catch((err) => setError(String(err)));
    setProposal(undefined);
  }
  useEffect(() => {
    setScenario(undefined);
    setProposal(undefined);
    setProposals([]);
  }, [stored]);
  const [delay, setDelay] = useState(14);
  const [customer, setCustomer] = useState("C1");
  const [discount, setDiscount] = useState("0");
  const [fee, setFee] = useState(0);
  const [advance, setAdvance] = useState(0);
  const [newKind, setNewKind] = useState("quality_deduction");
  const [newOrder, setNewOrder] = useState("O1");
  const [eventId, setEventId] = useState("O1-receivable");
  const [operation, setOperation] = useState("confirm");
  const [date, setDate] = useState("2027-01-01");
  const [reason, setReason] = useState("");
  const [evidence, setEvidence] = useState("");
  const [amount, setAmount] = useState(480000);
  const [pending, setPending] = useState<Record<string, unknown>>();
  useEffect(() => {
    void globalThis
      .fetch("/research/trace.json")
      .then((r) => (r.ok ? r.json() : undefined))
      .then(setTrace)
      .catch(() => undefined);
    void globalThis
      .fetch("/research/v2.json")
      .then((r) => {
        if (!r.ok) throw Error("研究数据加载失败");
        return r.json() as Promise<Bundle>;
      })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);
  useEffect(() => {
    setPending(undefined);
  }, [
    operation,
    eventId,
    date,
    amount,
    reason,
    evidence,
    newKind,
    newOrder,
    reconcileDate,
    observedBalance,
  ]);
  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  async function loadCases() {
    setScenario(undefined);
    setPending(undefined);
    const x = await api<{ cases: { case_id: string; version: number }[] }>(
      "list",
      {},
    );
    setCaseList(x.cases);
    if (x.cases[0])
      setStored(
        await api<Stored>("get", {
          case_id: stored?.case_id ?? x.cases[0].case_id,
        }),
      );
  }
  function choose(t: string) {
    setTab(t);
    setPending(undefined);
    if (t === "supplier") void run(loadCases);
  }
  const a = data?.fuling.allocations[allocation];
  const e = stored?.case.events.find((x) => x.event_id === eventId);
  function draft() {
    if (!stored) return;
    const command: Record<string, unknown> = {
      operation,
      event_id: eventId,
      reason,
    };
    if (operation === "add")
      Object.assign(command, {
        event_id: crypto.randomUUID(),
        order_id: newOrder,
        event_type: newKind,
        planned_date: date,
        amount_fen: Math.round(amount * 100),
        source: evidence,
      });
    if (operation === "confirm")
      Object.assign(command, { confirmed_date: date, evidence });
    if (operation === "record_actuals_and_reconcile")
      Object.assign(command, {
        as_of: reconcileDate,
        observed_balance_fen: Math.round(observedBalance * 100),
        postings: [{ event_id: eventId, posted_date: date, evidence }],
      });
    if (operation === "reschedule") command.planned_date = date;
    if (operation === "amend") command.amount_fen = Math.round(amount * 100);
    if (operation === "dispute") command.evidence = evidence;
    if (operation === "reconcile")
      Object.assign(command, {
        as_of: date,
        observed_balance_fen: Math.round(amount * 100),
      });
    setPending({
      case_id: stored.case_id,
      version: stored.case.version,
      key: crypto.randomUUID(),
      command,
    });
  }
  return (
    <main id="research-scroll" className="h-full overflow-y-auto">
      <div className="mx-auto max-w-6xl space-y-7 px-5 py-8 md:px-10">
        <SidebarTrigger aria-label="打开导航" />
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-muted-foreground text-xs tracking-widest">
              渝研｜银行经营分析
            </p>
            <h1 className="mt-3 text-3xl font-semibold">
              {tab === "fuling"
                ? "涪陵县域经营分析"
                : tab === "supplier"
                  ? "汽摩供应商资金管理"
                  : tab === "deposit"
                    ? "扩展研究：存款边际价值"
                    : "先理解业务，再讨论决策"}
            </h1>
            <p className="text-muted-foreground mt-3 max-w-3xl text-sm leading-7">
              独立作品。公开区域事实与合成经营实验分开；不代表银行客户、内部参数或真实经营成果。
            </p>
          </div>
          <Link className={button} href="/workspace/chats/new">
            研究助手
          </Link>
        </header>
        <nav className="flex flex-wrap gap-2">
          {[
            ["home", "研究总览"],
            ["fuling", "Case A · 涪陵"],
            ["supplier", "Case B · 供应商"],
            ["deposit", "扩展研究"],
          ].map(([id, title]) => (
            <button
              className={button + (tab === id ? " bg-muted" : "")}
              key={id}
              onClick={() => choose(id!)}
            >
              {title}
            </button>
          ))}
        </nav>
        {error && (
          <div
            role="alert"
            className="rounded-lg border border-amber-600 p-4 text-sm"
          >
            {error}
            <button
              className="ml-4 underline"
              onClick={() => location.reload()}
            >
              重新载入
            </button>
          </div>
        )}
        {!data && <p>正在载入来源与确定性结果…</p>}
        {data && tab === "home" && (
          <>
            <section className="grid gap-5 md:grid-cols-2">
              {[
                [
                  "fuling",
                  "A / 经营分析",
                  "有限资源下，银行应优先验证什么机会？",
                  "从涪陵产业事实出发，在正常与受限工时下比较任务选择和行业约束。",
                ],
                [
                  "supplier",
                  "B / 产品设计",
                  "订单最终回款覆盖列示支出，为什么过程中仍可能出现现金缺口？",
                  "查看资金事件、调整未落实条款、比较方案，并核对确认与到账状态。",
                ],
              ].map(([id, tag, title, description]) => (
                <button
                  key={id}
                  onClick={() => choose(id!)}
                  className={
                    card + " text-left transition hover:border-emerald-700"
                  }
                >
                  <p className="text-xs text-emerald-700">{tag}</p>
                  <h2 className="my-4 text-xl font-semibold">{title}</h2>
                  <p className="text-muted-foreground text-sm leading-7">
                    {description}
                  </p>
                  <p className="mt-5 text-sm">进入研究与操作 →</p>
                </button>
              ))}
            </section>
            <section className={card}>
              <h2 className="font-semibold">三个角色，三种责任</h2>
              <div className="mt-5 grid gap-4 md:grid-cols-3">
                {data.roles.map((r) => (
                  <div className="bg-muted rounded-lg p-4" key={r.role}>
                    <h3>{r.role}</h3>
                    <p className="mt-3 text-sm leading-7">{r.work}</p>
                  </div>
                ))}
              </div>
            </section>
            <section className={card}>
              <h2 className="font-semibold">一条真实研究助手调用</h2>
              <p className="my-3 text-sm leading-7">
                业务问题摘要：核心客户尾款延期14天，需要多少额外流动资金？完整真实提示及预先指定条件见下。
                <br />
                参数提案 → 人工核对 → 已确认快照计算 → 受控回答。
              </p>
              {trace ? (
                <>
                  <p className="text-muted-foreground text-xs">
                    Qwen Plus · 真实调用 · {trace.recorded_at}
                  </p>
                  <pre className="my-4 text-sm leading-7 whitespace-pre-wrap">
                    {trace.answer}
                  </pre>
                  <p className="text-muted-foreground text-sm">
                    {trace.boundary}
                  </p>
                  <a
                    className="mt-4 inline-block underline"
                    href="/research/trace.json"
                  >
                    查看脱敏工具参数与结果
                  </a>
                </>
              ) : (
                <p>调用记录暂不可用；不以示例数据冒充真实运行。</p>
              )}
            </section>
            <p className="text-muted-foreground text-sm">
              FACT 公开事实 → ASSUMPTION 明示假设 → MODEL OUTPUT 确定性结果 →
              DECISION 人工研究建议。存款研究作为附录，不参与两项主案例排序。
            </p>
          </>
        )}
        {data && tab === "fuling" && (
          <>
            <section className={card}>
              <h2 className="text-xl font-semibold">
                01 / 涪陵有哪些值得验证的机会？
              </h2>
              <p className="mt-3 text-sm leading-7">
                先进材料与新能源链可先核对结算、回款和上下游连接需求；食品榨菜链关注采购季节与验收；商贸物流关注资金时点。这些是待验证研究问题，不是已确认客户需求。
              </p>
              <div className="mt-5 grid gap-4 md:grid-cols-3">
                {data.fuling.facts.map((f) => (
                  <article key={f.fact_id} className="rounded-lg border p-4">
                    <p className="text-xs text-emerald-700">
                      FACT · {f.period}
                    </p>
                    <h3 className="mt-2 font-medium">{f.metric}</h3>
                    <p className="my-2 text-sm">{f.value}</p>
                    <p className="text-muted-foreground text-xs leading-6">
                      用途：{f.model_usage}。{f.limitation}
                    </p>
                    <details className="mt-2 text-xs">
                      <summary>核验状态与来源</summary>
                      <p className="my-2">{f.verification_status}</p>
                      <a
                        className="underline"
                        href={f.source}
                        target="_blank"
                        rel="noreferrer"
                      >
                        官方来源 ↗
                      </a>
                    </details>
                  </article>
                ))}
              </div>
            </section>
            <section className={card}>
              <h2 className="text-xl font-semibold">
                02 / 有限资源，先做哪些任务？
              </h2>
              <p className="my-3 text-sm leading-7">
                {data.fuling.disclosure.replace(
                  "重庆农商行或涪陵",
                  "任何银行或地区",
                )}
              </p>
              <label className="block text-sm">
                资源与集中度情景
                <select
                  className={input + " mt-2"}
                  value={allocation}
                  onChange={(ev) => setAllocation(Number(ev.target.value))}
                >
                  {data.fuling.allocations.map((x, i) => (
                    <option key={i} value={i}>
                      {x.name} · {x.constraint}
                    </option>
                  ))}
                </select>
              </label>
              {a && (
                <>
                  <p className="my-4 text-sm">
                    ASSUMPTION · {a.reason}
                    。每户最多一个增量动作；存量必要维护不在候选动作之间竞争。
                  </p>
                  <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                    {[
                      ["已分配/预算", `${a.hours}/${a.capacity_hours}小时`],
                      ["增量净贡献", money(a.benefit_fen)],
                      ["选中任务", `${a.selected.length}项`],
                      [
                        "最高行业工时占比",
                        `${(Number(a.max_sector_share) * 100).toFixed(1)}%`,
                      ],
                    ].map(([k, v]) => (
                      <div key={k}>
                        <p className="text-muted-foreground text-xs">{k}</p>
                        <p className="mt-2 font-semibold">{v}</p>
                      </div>
                    ))}
                  </div>
                  <p className="text-muted-foreground my-4 text-xs">
                    MODEL OUTPUT · 净贡献 = 假设毛收益 −
                    实施成本；未实证收益。风险/信心为待核验说明，不是概率或信用分数。
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[650px] text-left text-sm">
                      <thead>
                        <tr>
                          {[
                            "任务/客户",
                            "行业",
                            "工时",
                            "净贡献",
                            "验证条件",
                          ].map((h) => (
                            <th className="border-b p-2" key={h}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.fuling.actions
                          .filter((x) => a.selected.includes(x.id))
                          .map((x) => (
                            <tr key={x.id}>
                              <td className="border-b p-2">
                                {x.action_type}
                                <small className="block">{displayCustomerId(x.customer_id)}</small>
                              </td>
                              <td className="p-2">{x.sector}</td>
                              <td className="p-2">{x.service_hours}</td>
                              <td className="p-2">{money(x.benefit_fen)}</td>
                              <td className="p-2">
                                <p>{x.business_drivers}</p>
                                <p>
                                  产业原型来源：{x.source_fact_ids}
                                  （不校准金融参数）
                                </p>
                                <p>{x.value_formula}</p>
                                <p>待验证：{x.evidence_requirement}</p>
                                <p>停止：{x.stop_condition}</p>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                  <details className="mt-5">
                    <summary>未选动作及原因（{a.rejected.length}项）</summary>
                    <div className="mt-3 max-h-80 overflow-auto text-sm">
                      {a.rejected.map((x) => (
                        <p className="border-b py-3" key={x.id}>
                          {displayCustomerId(x.id)} · {x.action_type} · {money(x.benefit_fen)} ·{" "}
                          {x.reason}
                        </p>
                      ))}
                    </div>
                  </details>
                </>
              )}
            </section>
            <section className={card}>
              <h2 className="font-semibold">03 / 约束到底改变了什么？</h2>
              <div className="mt-4 space-y-3 text-sm">
                {data.fuling.allocations.map((x, i) => (
                  <p key={i}>
                    {x.name} / {x.constraint}：{x.hours}小时，
                    {x.selected.length}项，净贡献{money(x.benefit_fen)}。
                  </p>
                ))}
              </div>
              <p className="mt-4 text-sm leading-7">
                DECISION ·
                先验证选中任务的流水、服务成本和客户意愿；约束造成的贡献损失是研究中的分散化代价，不等于银行应接受的真实代价。若金融参数失真，排序也会改变。
              </p>
            </section>
            <section className={card}>
              <h2 className="font-semibold">
                04 / 收益没有完全实现，还值得做吗？
              </h2>
              <p className="my-3 text-sm">
                固定150小时与25%行业工时上限，收益按实现比例折减，成本照常支付。比例是压力假设，不是估计成功率。
              </p>
              {data.fuling.sensitivity.map((x) => (
                <p className="my-2 text-sm" key={x.realization_rate}>
                  收益实现{Number(x.realization_rate) * 100}%：
                  {x.selected.length}项 / {x.hours}小时 / 净贡献
                  {money(x.benefit_fen)}
                </p>
              ))}
            </section>
          </>
        )}
        {data && tab === "supplier" && (
          <>
            <section className={card}>
              <h2 className="text-xl font-semibold">
                01 / 打开自己的合成订单账本
              </h2>
              <p className="my-3 text-sm">
                事件与历史保存在服务端
                账本，按账户隔离。此处“事实”指合成案例内已录入凭证，不是真实企业流水。
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  className={button}
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      const created = await api<Stored>("create", {
                        key: crypto.randomUUID(),
                      });
                      setStored(created);
                      setCaseList((old) => [
                        {
                          case_id: created.case_id,
                          version: created.case.version,
                        },
                        ...old,
                      ]);
                      setScenario(undefined);
                      setPending(undefined);
                    })
                  }
                >
                  创建独立合成案例
                </button>
                <button
                  className={button}
                  disabled={busy}
                  onClick={() => void run(loadCases)}
                >
                  刷新已有案例
                </button>
                {caseList.length > 0 && (
                  <select
                    aria-label="已有案例"
                    className={button}
                    value={stored?.case_id ?? ""}
                    onChange={(ev) =>
                      void run(async () => {
                        setStored(
                          await api<Stored>("get", {
                            case_id: ev.target.value,
                          }),
                        );
                        setScenario(undefined);
                        setPending(undefined);
                      })
                    }
                  >
                    {caseList.map((c) => (
                      <option key={c.case_id} value={c.case_id}>
                        {c.case_id.slice(0, 8)} · 账本 {c.version}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              {!stored && (
                <p className="text-muted-foreground mt-4 text-sm">
                  尚未打开案例；先创建或选择已有案例。
                </p>
              )}
            </section>
            {stored && (
              <>
                <section className={card}>
                  <p className="mb-4 text-xs">
                    案例 {stored.case_id} · 版本 {stored.case.version} ·
                    核对边界 {stored.case.as_of} 00:00（不包含）
                  </p>
                  <Metrics r={stored.calculation} />
                  {!stored.calculation.complete && (
                    <p role="status" className="mt-4 text-amber-700">
                      存在逾期未解决或争议事件，不能据此得出整体资金安全结论。
                    </p>
                  )}
                  <Curve result={scenario ?? stored.calculation} />
                  <p className="text-sm">
                    最低点当日触发事件：
                    {(scenario ?? stored.calculation).minimum_drivers.join(
                      "、",
                    ) || "期初/核对余额"}
                    。此前累计支出同样影响缺口。
                  </p>
                  <p className="mt-3 text-sm">
                    关键材料核对：
                    {stored.calculation.evidence_completeness.supported}/
                    {stored.calculation.evidence_completeness.required}{" "}
                    项有确认说明。不是信用评分，也不验证文件真伪。
                  </p>
                  <p className="mt-3 text-sm">
                    合成订单客户集中度：Top 1{" "}
                    {(
                      Number(stored.calculation.concentration.top1) * 100
                    ).toFixed(1)}
                    %，Top 3{" "}
                    {(
                      Number(stored.calculation.concentration.top3) * 100
                    ).toFixed(1)}
                    %。
                  </p>
                </section>
                <section className={card}>
                  <h2 className="text-xl font-semibold">02 / 比较未落实条款</h2>
                  <p className="my-3 text-sm">
                    合同支付条件：
                    {stored.case.orders
                      .map(
                        (o) =>
                          `${o.order_id}：${o.payment_terms?.type === "AFTER_INVOICE" ? `验收后${o.payment_terms.invoice_after_acceptance_days}天预计开票，开票后${o.payment_terms.payment_after_invoice_days}天预计回款` : "固定日期（旧案例默认）"}`,
                      )
                      .join("；")}
                    。依赖变化只推导预测日期，确认或入账不会自动变更。
                  </p>
                  <div className="my-5 grid grid-cols-2 gap-4 md:grid-cols-5">
                    <label>
                      延期天数
                      <input
                        className={input}
                        type="number"
                        min="0"
                        max="90"
                        value={delay}
                        disabled={busy}
                        onChange={(ev) => {
                          invalidateScenario();
                          setDelay(Number(ev.target.value));
                        }}
                      />
                    </label>
                    <label>
                      影响客户
                      <select
                        className={input}
                        value={customer}
                        disabled={busy}
                        onChange={(ev) => {
                          invalidateScenario();
                          setCustomer(ev.target.value);
                        }}
                      >
                        {stored.case.orders.map((o) => (
                          <option key={o.order_id} value={o.customer_id}>
                            {o.name}
                          </option>
                        ))}
                        <option value="ALL">所有客户同时延期</option>
                      </select>
                    </label>
                    <label>
                      尾款折扣
                      <select
                        className={input}
                        value={discount}
                        disabled={busy}
                        onChange={(ev) => {
                          invalidateScenario();
                          setDiscount(ev.target.value);
                        }}
                      >
                        {["0", ".01", ".02", ".05"].map((v) => (
                          <option key={v} value={v}>
                            {Number(v) * 100}%
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      费用/元
                      <input
                        className={input}
                        type="number"
                        min="0"
                        value={fee}
                        disabled={busy}
                        onChange={(ev) => {
                          invalidateScenario();
                          setFee(Number(ev.target.value));
                        }}
                      />
                    </label>
                    <label>
                      每单追加预付/元
                      <input
                        className={input}
                        type="number"
                        min="0"
                        max="100000"
                        value={advance}
                        disabled={busy}
                        onChange={(ev) => {
                          invalidateScenario();
                          setAdvance(Number(ev.target.value));
                        }}
                      />
                    </label>
                  </div>
                  <button
                    className={button}
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        setScenario(undefined);
                        const x = await api<ScenarioProposal>(
                          "propose_scenario",
                          {
                            request_id: crypto.randomUUID(),
                            case_id: stored.case_id,
                            base_version: stored.case.version,
                            delay_days: delay,
                            customer_id: customer,
                            discount,
                            fee_fen: Math.round(fee * 100),
                            advance_fen: Math.round(advance * 100),
                          },
                        );
                        setProposal(x);
                      })
                    }
                  >
                    校验并回显情景参数
                  </button>
                  <button
                    className={button + " ml-2"}
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        const x = await api<{ requests: ScenarioProposal[] }>(
                          "scenario_requests",
                          { case_id: stored.case_id },
                        );
                        setProposals(
                          x.requests.filter(
                            (p) =>
                              p.request.confirmation_status === "PROPOSED" &&
                              p.request.base_version === stored.case.version,
                          ),
                        );
                      })
                    }
                  >
                    载入助手参数提案
                  </button>
                  {proposals.map((p) => (
                    <button
                      className={button + " m-2"}
                      key={p.request.request_id}
                      disabled={busy}
                      onClick={() => {
                        invalidateScenario();
                        setCustomer(p.request.customer_id ?? "");
                        setDelay(p.request.delay_days ?? 0);
                        setDiscount(p.request.discount ?? "");
                        setFee((p.request.fee_fen ?? 0) / 100);
                        setAdvance((p.request.advance_fen ?? 0) / 100);
                        setProposal(p);
                      }}
                    >
                      查看提案 {p.request.request_id}
                    </button>
                  ))}
                  {proposal && (
                    <div className="my-4 rounded-lg border p-4">
                      <p>请逐项确认；确认测算参数不代表合同已落实。</p>
                      <p>
                        请求 {proposal.request.request_id} · 账本版本{" "}
                        {proposal.request.base_version}
                      </p>
                      <p>
                        客户 {proposal.request.customer_id ?? "待确认"} / 延期{" "}
                        {proposal.request.delay_days ?? "待确认"} 天 / 折扣{" "}
                        {proposal.request.discount ?? "待确认"} / 费用{" "}
                        {proposal.request.fee_fen === null
                          ? "待确认"
                          : money(proposal.request.fee_fen)}{" "}
                        / 每单预付{" "}
                        {proposal.request.advance_fen === null
                          ? "待确认"
                          : money(proposal.request.advance_fen)}
                      </p>
                      {proposal.missing_fields.length > 0 ? (
                        <p className="text-amber-700">
                          参数有歧义或缺失，请修改输入并重新校验；不能直接计算。
                        </p>
                      ) : (
                        <button
                          className={button + " mt-3"}
                          disabled={
                            busy ||
                            proposal.request.confirmation_status !== "PROPOSED"
                          }
                          onClick={() =>
                            void run(async () => {
                              const confirmed = await api<ScenarioProposal>(
                                "confirm_scenario",
                                {
                                  request_id: proposal.request.request_id,
                                  snapshot: proposal.request,
                                },
                              );
                              setProposal(confirmed);
                              const result = await api<{
                                scenario: Calc;
                                request: ScenarioSnapshot;
                                parameter_hash: string;
                              }>("simulate", {
                                request_id: confirmed.request.request_id,
                              });
                              if (
                                result.parameter_hash !==
                                  confirmed.parameter_hash ||
                                result.request.base_version !==
                                  stored.case.version
                              )
                                throw Error("结果快照不匹配，拒绝展示");
                              setScenario(result.scenario);
                            })
                          }
                        >
                          确认参数并计算
                        </button>
                      )}
                    </div>
                  )}
                  {scenario && (
                    <div className="mt-5 space-y-3 text-sm">
                      {!scenario.complete && (
                        <p className="text-amber-700">
                          此情景仍有争议或逾期未解决，不足以判断整体资金安全。
                        </p>
                      )}
                      <p>
                        基线 → 情景缺口：
                        {money(stored.calculation.peak_gap_fen)} →{" "}
                        {money(scenario.peak_gap_fen)}；负余额：
                        {stored.calculation.negative_days} →{" "}
                        {scenario.negative_days}天。
                      </p>
                      <p>
                        条款代价：折扣{money(scenario.discount_cost_fen ?? 0)} +
                        费用{money(scenario.fee_fen ?? 0)}
                        。追加预付从尾款移至核对日假设发生，未计作实际到账。
                      </p>
                      <p>ASSUMPTION · 方案只用于比较，未保存为已确认安排。</p>
                    </div>
                  )}
                  <p className="mt-5 font-medium">
                    资金缺口 ≠
                    授信额度。需要进一步进行用途、还款来源与授信风险审核。
                  </p>
                </section>
                <section className={card}>
                  <h2 className="text-xl font-semibold">03 / 核对事件与变更</h2>
                  <div className="mt-5 overflow-x-auto">
                    <table className="w-full min-w-[680px] text-left text-sm">
                      <thead>
                        <tr>
                          {[
                            "订单/事件",
                            "金额",
                            "计划日期",
                            "状态",
                            "证据",
                          ].map((x) => (
                            <th className="border-b p-2" key={x}>
                              {x}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {stored.case.events.map((x) => (
                          <tr key={x.event_id}>
                            <td className="border-b p-2">
                              {x.order_id} / {labels[x.event_type]}
                            </td>
                            <td className="p-2">{money(x.amount_fen)}</td>
                            <td className="p-2">
                              {x.planned_date}
                              {x.prediction_confidence && (
                                <p>条件可信状态：{x.prediction_confidence}</p>
                              )}
                              {x.posted_date && (
                                <small className="block">
                                  到账 {x.posted_date}
                                </small>
                              )}
                            </td>
                            <td className="p-2">{labels[x.status]}</td>
                            <td className="max-w-48 p-2 text-xs">
                              {x.evidence || "尚未确认：不能视为可用现金"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-5 grid gap-4 md:grid-cols-3">
                    <label>
                      变更事件
                      <select
                        className={input}
                        value={eventId}
                        onChange={(ev) => setEventId(ev.target.value)}
                      >
                        {stored.case.events.map((x) => (
                          <option key={x.event_id}>{x.event_id}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      操作
                      <select
                        className={input}
                        aria-label="操作"
                        value={operation}
                        onChange={(ev) => setOperation(ev.target.value)}
                      >
                        {[
                          ["add", "新增资金/流程事件"],
                          ["confirm", "确认安排"],
                          [
                            "record_actuals_and_reconcile",
                            "实际收付与余额一次核对",
                          ],
                          ["reschedule", "重新协商日期"],
                          ["amend", "重新协商金额"],
                          ["dispute", "标记质量/验收争议"],
                          ["cancel", "取消未入账计划"],
                          ["reconcile", "核对边界与余额"],
                        ].map(([v, t]) => (
                          <option key={v} value={v}>
                            {t}
                          </option>
                        ))}
                      </select>
                    </label>
                    {operation === "record_actuals_and_reconcile" && (
                      <>
                        <label>
                          新核对边界（当天00:00，不含）
                          <input
                            className={input}
                            type="date"
                            value={reconcileDate}
                            onChange={(ev) => setReconcileDate(ev.target.value)}
                          />
                        </label>
                        <label>
                          观察到的实际余额/元
                          <input
                            className={input}
                            type="number"
                            value={observedBalance}
                            onChange={(ev) =>
                              setObservedBalance(Number(ev.target.value))
                            }
                          />
                        </label>
                      </>
                    )}
                    {operation === "add" && (
                      <>
                        <label>
                          订单
                          <select
                            className={input}
                            value={newOrder}
                            onChange={(ev) => setNewOrder(ev.target.value)}
                          >
                            {stored.case.orders.map((o) => (
                              <option key={o.order_id} value={o.order_id}>
                                {o.name}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>
                          事件类别
                          <select
                            className={input}
                            value={newKind}
                            onChange={(ev) => setNewKind(ev.target.value)}
                          >
                            {[
                              "quality_deduction",
                              "fee",
                              "materials",
                              "production",
                              "shipment",
                              "acceptance",
                              "invoice",
                              "receivable",
                            ].map((k) => (
                              <option key={k} value={k}>
                                {labels[k]}
                              </option>
                            ))}
                          </select>
                        </label>
                      </>
                    )}
                    <label>
                      日期
                      <input
                        className={input}
                        type="date"
                        value={date}
                        onChange={(ev) => setDate(ev.target.value)}
                      />
                    </label>
                    <label>
                      金额/元（支出填负数，流程节点填0）
                      <input
                        className={input}
                        type="number"
                        value={amount}
                        onChange={(ev) => setAmount(Number(ev.target.value))}
                      />
                    </label>
                    <label>
                      原因
                      <input
                        className={input}
                        value={reason}
                        onChange={(ev) => setReason(ev.target.value)}
                        placeholder="必填：为什么变更"
                      />
                    </label>
                    <label>
                      凭证/来源说明
                      <input
                        className={input}
                        value={evidence}
                        onChange={(ev) => setEvidence(ev.target.value)}
                        placeholder="确认或入账必填；演示注明合成"
                      />
                    </label>
                  </div>
                  <p className="text-muted-foreground my-4 text-xs leading-6">
                    已入账记录不可覆盖。改期/改金额会撤销原确认，回到待协商。选择已确认的完整收付事件，一次填写实际日期、凭据、新核对边界和观察余额；系统先在副本入账，再核对余额，一致才整体保存，不一致全部回滚并返回差额。不支持部分核销。边界前其他未落实记录会明确列为逾期。新增质量扣款与原尾款分别记录，勿再将同一扣款从尾款扣除。
                  </p>
                  <button
                    disabled={busy || !reason.trim()}
                    className={button}
                    onClick={draft}
                  >
                    预览变更
                  </button>
                  {pending && (
                    <div className="mt-4 rounded-lg border border-amber-600 p-4">
                      <h3 className="font-semibold">
                        提交前确认 · 基于版本 {stored.case.version}
                      </h3>
                      <p className="my-3 text-sm">
                        当前：{e?.event_id} / {labels[e?.status ?? ""]} /{" "}
                        {e?.planned_date} / {money(e?.amount_fen ?? 0)}
                        。确认仅改变安排状态；只有入账操作影响事实现金。
                      </p>
                      <dl className="space-y-2 text-sm">
                        {Object.entries(
                          pending.command as Record<string, unknown>,
                        )
                          .filter(
                            ([k]) => !["event_id", "operation"].includes(k),
                          )
                          .map(([k, v]) => (
                            <div key={k}>
                              <dt className="text-muted-foreground inline">
                                {{
                                  reason: "变更原因",
                                  planned_date: "新计划日期",
                                  confirmed_date: "确认日期",
                                  posted_date: "实际收付日期",
                                  postings: "本次实际收付",
                                  evidence: "凭证说明",
                                  amount_fen: "新金额",
                                  as_of: "新核对边界",
                                  observed_balance_fen: "核对余额",
                                  source: "来源",
                                  order_id: "订单",
                                  event_type: "事件类型",
                                }[k] ?? k}
                                ：
                              </dt>
                              <dd className="inline">
                                {k.endsWith("_fen")
                                  ? money(Number(v))
                                  : (labels[String(v)] ?? String(v))}
                              </dd>
                            </div>
                          ))}
                      </dl>
                      <button
                        className={button + " mt-4"}
                        disabled={busy}
                        onClick={() =>
                          void run(async () => {
                            setStored(await api<Stored>("change", pending));
                            setPending(undefined);
                            setScenario(undefined);
                          })
                        }
                      >
                        明确确认并提交
                      </button>
                    </div>
                  )}
                  <details className="mt-6">
                    <summary>
                      来源与变更历史（{stored.case.history.length}条）
                    </summary>
                    <pre className="mt-3 max-h-96 overflow-auto text-xs">
                      {JSON.stringify(stored.case.history, null, 2)}
                    </pre>
                  </details>
                </section>
              </>
            )}
          </>
        )}
        {tab === "deposit" && (
          <section className={card}>
            <h2 className="text-xl font-semibold">
              Experimental Research / 扩展研究
            </h2>
            <p className="my-4 leading-8">
              简化计算为：年平均存款余额 ×（有效资金系数 × 假设 FTP −
              存款利率）− 服务成本。FTP
              仅作用于折算有效资金，利息按全部平均余额计提；没有已承诺资产资金缺口，因此不再额外扣替代资金成本。
            </p>
            <p className="my-4">
              1000万元 ×（80% × 2% − 1.5%）− 2万元 =
              {data ? money(data.deposit.base.contribution_fen) : "加载中"}
              ；盈亏平衡存款利率为
              {data
                ? (Number(data.deposit.base.break_even_rate) * 100).toFixed(1)
                : "—"}
              %。这是模型假设，不代表任何银行内部 FTP，不用于客户定价或真实ALM。
            </p>
          </section>
        )}
        {tab !== "home" && (
          <footer className="flex flex-wrap gap-4 pb-10 text-sm">
            <a className={button} href={`/research/${tab}-research.pdf`}>
              下载研究 PDF
            </a>
            <a className={button} href="/research/sources.json">
              下载来源登记表
            </a>
            <a className={button} href="/research/fuling_public_facts.json">
              公开事实登记表
            </a>
          </footer>
        )}
        {busy && <p role="status">正在校验并执行，请稍候…</p>}
      </div>
    </main>
  );
}
