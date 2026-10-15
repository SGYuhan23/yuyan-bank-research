import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Alert, Button, Card, Descriptions, Spin, Tag } from "antd";
import { scenarios, asset } from "../demo/scenarios";
import { GuidedSession } from "../demo/runtime.js";
import {
  AgentLabel,
  UserMessage,
  ScenarioComposer,
} from "../components/AgentChat";
import AgentTrace from "../components/AgentTrace";
import ToolResult, { money } from "../components/ToolResult";
import ContractDetail from "../components/ContractDetail";
export default function AgentDemo() {
  const { id } = useParams(),
    s = scenarios.find((s) => s.id === id);
  const [session, setSession] = useState<any>(null),
    [trace, setTrace] = useState<any>(null),
    [step, setStep] = useState(0),
    [busy, setBusy] = useState(true),
    [output, setOutput] = useState<any>(null),
    [old, setOld] = useState<any>(null),
    [error, setError] = useState(""),
    [cycle, setCycle] = useState(0);
  const alive = useRef(true),
    lock = useRef(false),
    resultRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    alive.current = true;
    const abort = new AbortController();
    async function load() {
      try {
        const r = await fetch(asset("data/demo-data.json"), {
          signal: abort.signal,
        });
        if (!r.ok) throw Error("案例数据暂时无法加载");
        const d = await r.json();
        const t = await fetch(asset(d.trace_path), { signal: abort.signal });
        if (!t.ok) throw Error("调用记录暂时无法加载");
        const tr = await t.json();
        if (!s) return;
        const next = new GuidedSession(d, s.id);
        if (alive.current) {
          setTrace(tr);
          setSession(next);
        }
      } catch (e) {
        if (!abort.signal.aborted) {
          setError((e as Error).message);
          setBusy(false);
        }
      }
    }
    load();
    return () => {
      alive.current = false;
      abort.abort();
    };
  }, [id]);
  useEffect(() => {
    if (!session) return;
    setStep(0);
    setBusy(true);
    const a = setTimeout(() => setStep(1), 450),
      b = setTimeout(() => {
        setStep(2);
        setBusy(false);
      }, 900);
    return () => {
      clearTimeout(a);
      clearTimeout(b);
    };
  }, [session, cycle]);
  if (!s)
    return (
      <main className="page">
        <h1>请选择一个演示问题</h1>
        <Link to="/demo">返回案例</Link>
      </main>
    );
  const sleep = () => new Promise((r) => setTimeout(r, 450));
  async function confirm() {
    if (!session || busy || lock.current || output) return;
    lock.current = true;
    setError("");
    setBusy(true);
    try {
      session.confirm();
      setStep(3);
      await sleep();
      await sleep();
      if (!alive.current) return;
      const result = session.run();
      setOutput(result);
      setStep(4);
      await sleep();
      if (!alive.current) return;
      if (
        JSON.stringify(result.snapshot) !==
        JSON.stringify(session.binding.request)
      )
        throw Error("请求已变化，请重新确认");
      if (
        s!.id === "cashflow" &&
        result.value.scenario.base_version !== result.snapshot.base_version
      )
        throw Error("账本版本不一致");
      setStep(5);
      await sleep();
      setTimeout(
        () =>
          resultRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
          }),
        50,
      );
    } catch (e) {
      setOutput(null);
      setError((e as Error).message);
      setStep(2);
    } finally {
      lock.current = false;
      if (alive.current) setBusy(false);
    }
  }
  function followup() {
    if (!session || busy) return;
    setOld(output);
    setOutput(null);
    session.propose(true);
    setCycle((c) => c + 1);
  }
  const recorded =
    s.id === "cashflow" &&
    session &&
    !session.variant &&
    trace?.original_model_proposal?.request?.customer_id === "C1" &&
    trace.original_model_proposal.request.delay_days === 14;
  const p = session?.binding.request.parameters;
  const shownLedger = output?.value?.before || session?.ledger;
  const params = p
    ? s.id === "allocation"
      ? [
          ["可用新增经营工时", p.available_hours + " 小时"],
          [
            "行业资源分散约束",
            p.industry_limit ? "单一行业 ≤ 已选工时 25%" : "不启用",
          ],
          ["候选客户", "当前合成客户集合"],
          ["每户最大新增动作", "1 项"],
        ]
      : s.id === "customer"
        ? [
            ["固定变量", "余额 = " + money(p.deposit_fen) + " 元"],
            ["客户 A", "高交易频次"],
            ["客户 B", "高员工数量"],
            ["其他条件", "使用现有合成对照输入"],
          ]
        : s.id === "cashflow"
          ? [
              [
                "影响客户",
                p.customer_id === "ALL" ? "所有客户（ALL）" : "核心客户 C1",
              ],
              ["尾款延期", p.delay_days + " 天"],
              ["折扣 / 费用 / 追加预付", "0 / 0 元 / 0 元"],
              ["账本版本", String(session.ledger.version)],
            ]
          : [
              [
                "当前事实余额",
                money(
                  shownLedger.opening_fen +
                    shownLedger.events
                      .filter((e) => e.status === "POSTED")
                      .reduce((a, e) => a + e.amount_fen, 0),
                ) + " 元",
              ],
              [
                "实际支付",
                money(
                  session.ledger.events.find((e) => e.event_id === p.event_id)
                    .amount_fen,
                ) + " 元",
              ],
              ["观察余额", money(p.observed_balance_fen) + " 元"],
              ["付款 / 核对日期", p.posted_date + " / " + p.as_of],
            ]
    : [];
  const followText =
    s.id === "allocation"
      ? "如果我还希望避免经营资源过度集中在单一行业，会发生什么？"
      : s.id === "cashflow"
        ? "进一步压力测试：如果所有客户都晚 30 天呢？"
        : "再用正确观察余额核对";
  return (
    <div className="demo-shell">
      <header className="demo-header">
        <Link className="brand" to="/">
          <span className="brand-mark">研</span>渝研
        </Link>
        <span className="demo-title">{s.theme}</span>
        <Link to="/demo">← 返回案例</Link>
      </header>
      <div className="demo-grid">
        <main className="conversation">
          <div className="conversation-heading">
            <span className="eyebrow">DEMO {s.no} / GUIDED ANALYSIS</span>
            <h1>{s.title}</h1>
          </div>
          <UserMessage text={s.question} />
          <AgentLabel />
          <p className="agent-intro">{s.understanding}</p>
          {!session && !error && <Spin tip="正在读取合成案例" />}
          {error && <Alert type="error" showIcon message={error} />}
          {session && (
            <>
              {old && (
                <>
                  <div className="stale-output" data-testid="stale-result">
                    <strong>上一轮结果 · 参数已变化</strong>
                    <ToolResult id={s.id} output={old} />
                  </div>
                  <UserMessage text={followText} />
                  <Alert
                    type="warning"
                    showIcon
                    message="参数已变化，原结果失效。"
                    description={
                      s.id === "allocation"
                        ? "上一轮结果对应不启用行业约束，不能继续代表当前分析。"
                        : s.id === "cashflow"
                          ? "当前参数已经从 C1 / 14 天改为 ALL / 30 天，请重新确认。"
                          : "观察余额已变化，请重新确认核对范围。"
                    }
                  />
                </>
              )}
              <Card
                className="parameter-card"
                title="先确认这次分析范围"
                extra={
                  <Tag color={output ? "success" : "default"}>
                    {output ? "已确认" : "待确认"}
                  </Tag>
                }
              >
                <Descriptions
                  size="small"
                  column={1}
                  items={params.map(([label, children]) => ({
                    key: label,
                    label,
                    children,
                  }))}
                />
                <div className="confirm-row">
                  <Button
                    type="primary"
                    onClick={confirm}
                    disabled={busy || !!output}
                    loading={busy && step >= 3 && step < 5}
                  >
                    {output
                      ? "本轮已完成"
                      : s.id === "reconcile"
                        ? "确认并核对"
                        : "确认并计算"}
                  </Button>
                  <span className="small muted">
                    {busy && step < 3
                      ? "正在整理本次参数…"
                      : "确认分析参数，不代表实际合同或经营决策。"}
                  </span>
                </div>
              </Card>
              {step >= 3 && (
                <div className="tool-call" aria-live="polite">
                  <span className={busy ? "live-dot" : "done-dot"} />
                  <div>
                    <strong>{s.tool}</strong>
                    <p>
                      {busy
                        ? s.id === "cashflow"
                          ? `正在重新计算 ${session.ledger.orders.length} 笔订单的现金事件…`
                          : "正在按确认参数执行工具并核对结果…"
                        : "已使用确认快照执行 · 结果绑定本次请求与账本版本"}
                    </p>
                  </div>
                  <Tag>{busy ? "执行中" : "已完成"}</Tag>
                </div>
              )}
              {output && (
                <div
                  ref={resultRef}
                  className="result-area"
                  data-testid="tool-result"
                >
                  <Card title="本次工具结果">
                    <ToolResult id={s.id} output={output} />
                  </Card>
                  <div className="why">
                    <span className="eyebrow">这一步为什么重要？</span>
                    <p>{s.why}</p>
                  </div>
                  {!busy && !session.variant && s.id !== "customer" && (
                    <Button className="followup" onClick={followup}>
                      {followText} →
                    </Button>
                  )}
                  {s.id === "cashflow" && (
                    <ContractDetail
                      initial={session.data.supplier.initial_case}
                    />
                  )}
                </div>
              )}
              <ScenarioComposer />
            </>
          )}
        </main>
        {session && (
          <AgentTrace
            session={session}
            step={step}
            busy={busy}
            output={output}
            trace={trace}
            recorded={!!recorded}
          />
        )}
      </div>
    </div>
  );
}
